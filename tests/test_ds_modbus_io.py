""" Test of every DS_ModbusTCP DataSource subclass """

import itertools
import random

import pytest
from pyModbusTCP.server import ModbusServer

from pyHMI.DS_ModbusTCP import (ModbusBool, ModbusBoolRegister, ModbusFloat,
                                ModbusInt, ModbusRequest, ModbusTCPDevice)

from .utils import (bool_list_to_16b_list, build_bool_data_l,
                    build_float_data_l, build_int_data_l, cut_bytes,
                    double_float_to_int, int_to_double_float,
                    int_to_single_float, regs_to_bytes, single_float_to_int,
                    to_16b_list, to_byte_length, to_reg_length)


@pytest.fixture
def modbus_srv():
    # setup code
    srv = ModbusServer(port=5020, no_block=True)
    srv.start()
    # pass to test functions
    yield srv
    # teardown code
    srv.stop()


def run_and_wait_ok(request: ModbusRequest):
    """ Run request and wait for a valid result """
    if not request.run():
        raise RuntimeError('unable to run request')
    if not request.run_done_evt.wait(timeout=5.0):
        raise RuntimeError('request not processed')
    if request.error:
        raise RuntimeError('request processing error')


def test_read_modbus_bool_src(modbus_srv):
    """ Test ModbusBool reading operations (ModbusServer -> DataSource) """
    for d_inputs in [False, True]:
        # build a dataset
        addr = random.randint(0, 0x1000)
        size = random.randint(1, 2000)
        srv_bool_l = build_bool_data_l(size)
        # init server
        if d_inputs:
            modbus_srv.data_bank.set_discrete_inputs(addr, srv_bool_l)
        else:
            modbus_srv.data_bank.set_coils(addr, srv_bool_l)
        # init client
        request = ModbusTCPDevice(port=5020).add_read_bits_request(addr, size, d_inputs=d_inputs)
        src_l = [ModbusBool(request, address=addr+i) for i in range(size)]
        # run request
        run_and_wait_ok(request)
        # read dataset
        ds_bool_l = [src.get() for src in src_l]
        # check data match
        assert srv_bool_l == ds_bool_l


def test_read_modbus_bool_register_src(modbus_srv):
    """ Test ModbusBoolRegister reading operations (ModbusServer -> DataSource) """
    for i_regs in [False, True]:
        # build a dataset
        addr = random.randint(0, 0x1000)
        size = random.randint(1, 2000)
        srv_bool_l = build_bool_data_l(size)
        # init server
        if i_regs:
            modbus_srv.data_bank.set_input_registers(addr, bool_list_to_16b_list(srv_bool_l))
        else:
            modbus_srv.data_bank.set_holding_registers(addr, bool_list_to_16b_list(srv_bool_l))
        # init client
        request = ModbusTCPDevice(port=5020).add_read_regs_request(addr, to_reg_length(size), i_regs=i_regs)
        src_l = [ModbusBoolRegister(request, address=addr + i//16, bit=i % 16) for i in range(len(srv_bool_l))]
        # run request
        run_and_wait_ok(request)
        # read dataset
        ds_bool_l = [src.get() for src in src_l]
        # check data match
        assert srv_bool_l == ds_bool_l


def test_read_modbus_int_src(modbus_srv):
    """ Test ModbusInt reading operations (ModbusServer -> DataSource) """
    # test all common options
    for i_regs, bit_length, signed in itertools.product([False, True], [16, 32, 64, 128], [False, True]):
        addr = random.randint(0, 0xffff - 125 + 1)
        size = random.randint(1, 125//to_reg_length(bit_length))
        srv_int_l = build_int_data_l(size=size, bit_length=bit_length, signed=signed)
        # init server
        if i_regs:
            modbus_srv.data_bank.set_input_registers(addr, to_16b_list(srv_int_l, bit_length))
        else:
            modbus_srv.data_bank.set_holding_registers(addr, to_16b_list(srv_int_l, bit_length))
        # init datasource
        nb_reg = len(srv_int_l) * to_reg_length(bit_length)
        request = ModbusTCPDevice(port=5020).add_read_regs_request(addr, nb_reg, i_regs=i_regs)
        ds_args = {'bit_length': bit_length, 'signed': signed}
        src_l = [ModbusInt(request, addr+off, **ds_args) for off in range(0, nb_reg, to_reg_length(bit_length))]
        # run request
        run_and_wait_ok(request)
        # read dataset
        ds_int_l = [src.get() for src in src_l]
        # check data match
        assert srv_int_l == ds_int_l


def test_read_modbus_float_src(modbus_srv):
    """ Test ModbusFloat reading operations (ModbusServer -> DataSource) """
    for i_regs, bit_length, in itertools.product([False, True], [32, 64]):
        addr = random.randint(0, 0xffff - 125 + 1)
        size = random.randint(1, 125//to_reg_length(bit_length))
        # build a list of float
        srv_float_l = build_float_data_l(size=size, bit_length=bit_length)
        # encode float to IEEE format
        ieee_l = []
        for value in srv_float_l:
            ieee_l.append(single_float_to_int(value) if bit_length == 32 else double_float_to_int(value))
        # init server
        if i_regs:
            modbus_srv.data_bank.set_input_registers(addr, to_16b_list(ieee_l, bit_length))
        else:
            modbus_srv.data_bank.set_holding_registers(addr, to_16b_list(ieee_l, bit_length))
        # init datasource
        device = ModbusTCPDevice(port=5020)
        request = device.add_read_regs_request(addr, size * to_reg_length(bit_length), i_regs=i_regs)
        src_l = []
        for off in range(0, size * to_reg_length(bit_length), to_reg_length(bit_length)):
            src_l.append(ModbusFloat(request, addr+off, bit_length=bit_length))
        # run request
        run_and_wait_ok(request)
        # read dataset
        ds_float_l = [src.get() for src in src_l]
        # check data match
        assert srv_float_l == pytest.approx(ds_float_l, abs=1e-6, nan_ok=True)


def test_write_modbus_bool_src(modbus_srv):
    """ Test ModbusBool writing operations (DataSource -> ModbusServer) """
    # build a dataset
    addr = random.randint(0, 0x1000)
    size = random.randint(1, 1968)
    ds_bool_l = build_bool_data_l(size)
    # init datasource
    mb_device = ModbusTCPDevice(port=5020)
    request = mb_device.add_write_bits_request(addr, size)
    # write on ds
    for offset, value in enumerate(ds_bool_l):
        ModbusBool(request, address=addr+offset).set(value)
    # run request
    run_and_wait_ok(request)
    # init server
    srv_bool_l = modbus_srv.data_bank.get_coils(addr, size)
    # check data match
    assert ds_bool_l == srv_bool_l


def test_write_modbus_int_src(modbus_srv):
    """ Test ModbusInt writing operations (DataSource -> ModbusServer) """
    # test all common options
    for bit_length, signed in itertools.product([16, 32, 64, 128], [False, True]):
        addr = random.randint(0, 0xffff - 123 + 1)
        size = random.randint(1, 123//to_reg_length(bit_length))
        ds_int_l = build_int_data_l(size=size, bit_length=bit_length, signed=signed)
        # init datasource
        request = ModbusTCPDevice(port=5020).add_write_regs_request(addr, size * to_reg_length(bit_length))
        for offset, value in enumerate(ds_int_l):
            offset *= to_reg_length(bit_length)
            ModbusInt(request, addr+offset, bit_length=bit_length, signed=signed).set(value)
        # run request
        run_and_wait_ok(request)
        # init server
        srv_16b_l = modbus_srv.data_bank.get_holding_registers(addr, size * to_reg_length(bit_length))
        # [list of 16 bits regs] -> raw_bytes
        raw_b = regs_to_bytes(srv_16b_l)
        # convert raw_bytes to list of well encoded integer
        srv_int_l = []
        for block in cut_bytes(raw_b, block_size=to_byte_length(bit_length)):
            srv_int_l.append(int.from_bytes(block, byteorder='big', signed=signed))
        # check data match
        assert ds_int_l == srv_int_l


def test_write_modbus_float_src(modbus_srv):
    """ Test ModbusFloat writing operations (DataSource -> ModbusServer) """
    # test all common options
    for bit_length in [32, 64]:
        addr = random.randint(0, 0xffff - 123 + 1)
        size = random.randint(1, 123//to_reg_length(bit_length))
        ds_float_l = build_float_data_l(size=size, bit_length=bit_length)
        # write with datasource
        request = ModbusTCPDevice(port=5020).add_write_regs_request(addr, size * to_reg_length(bit_length))
        for i, value in enumerate(ds_float_l):
            ModbusFloat(request, addr+i*to_reg_length(bit_length), bit_length=bit_length).set(value)
        # run request
        run_and_wait_ok(request)
        # read with server
        srv_16b_l = modbus_srv.data_bank.get_holding_registers(addr, size * to_reg_length(bit_length))
        # list of regs (16 bits) -> raw_bytes
        raw_b = regs_to_bytes(srv_16b_l)
        # raw_bytes -> list of well encoded float
        srv_float_l = []
        for block in cut_bytes(raw_b, block_size=to_byte_length(bit_length)):
            if bit_length == 32:
                srv_float_l.append(int_to_single_float(int.from_bytes(block, byteorder='big')))
            else:
                srv_float_l.append(int_to_double_float(int.from_bytes(block, byteorder='big')))
        # check data match
        assert ds_float_l == pytest.approx(srv_float_l, abs=1e-6, nan_ok=True)
