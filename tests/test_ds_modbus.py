""" Test of every DS_ModbusTCP DataSource subclass """

import pytest
import itertools
import random
import time
from pyModbusTCP.utils import encode_ieee
from pyHMI.DS_ModbusTCP import ModbusTCPDevice, ModbusBool, ModbusInt, ModbusFloat
from .fixtures import modbus_srv
from .utils import to_byte_length, to_reg_length, to_16b_list, build_bool_data_l, build_int_data_l


class FakeConf:
    md = ModbusTCPDevice(port=5020)
    r_bits_req = md.add_read_bits_request(0, size=16)
    r_regs_req = md.add_read_regs_request(0, size=16)
    w_bits_req = md.add_write_bits_request(0, size=16)
    w_regs_req = md.add_write_regs_request(0, size=16)


def test_errors_modbus_bool():
    """ Test ModbusBool errors """
    # === shouldn't raise exception ===
    # for good request type
    for req in [FakeConf.r_bits_req, FakeConf.w_bits_req]:
        ModbusBool(req, 0)
    # for writing a well-typed value
    ModbusBool(req, 0).set(False)
    ModbusBool(req, 0).set(True)

    # === should raise exception ===
    # for bad request type
    for req in [FakeConf.r_regs_req, FakeConf.w_regs_req]:
        with pytest.raises(TypeError):
            ModbusBool(req, 0)
    # for writing on read-only
    with pytest.raises(TypeError):
        ModbusBool(FakeConf.r_bits_req, 0).set(False)
    # for write an unsupported value type
    with pytest.raises(TypeError):
        ModbusBool(FakeConf.w_bits_req, 0).set('oops')  # type: ignore        


def test_errors_modbus_int():
    """ Test ModbusInt errors """
    # === shouldn't raise exception ===
    # for good request type
    for req in [FakeConf.r_regs_req, FakeConf.w_regs_req]:
        ModbusInt(req, 0)
    # for write a well-typed value with a valid range
    for bit_length in [16, 32, 64, 128]:
        ModbusInt(FakeConf.w_regs_req, 0, bit_length=bit_length, signed=True).set(-1)
        ModbusInt(FakeConf.w_regs_req, 0, bit_length=bit_length, signed=False).set(2**bit_length-1)
        ModbusInt(FakeConf.w_regs_req, 0, bit_length=bit_length, signed=False).set(2**bit_length-1)
        ModbusInt(FakeConf.w_regs_req, 0, bit_length=bit_length, signed=False).set(2**bit_length-1)

    # === should raise exception ===
    # for bad request type
    for req in [FakeConf.r_bits_req, FakeConf.w_bits_req]:
        with pytest.raises(TypeError):
            ModbusInt(req, 0)
    # for writing on read-only
    with pytest.raises(TypeError):
        ModbusInt(FakeConf.r_regs_req, 0).set(False)
    # for write an unsupported value type
    with pytest.raises(TypeError):
        ModbusInt(FakeConf.w_regs_req, 0, bit_length=bit_length, signed=True).set('oops')  # type: ignore
    # for writing an overrange value
    for bit_length in [16, 32, 64, 128]:
        with pytest.raises(ValueError):
            ModbusInt(FakeConf.w_regs_req, 0, bit_length=bit_length, signed=True).set(2**bit_length//2)
        with pytest.raises(ValueError):
            ModbusInt(FakeConf.w_regs_req, 0, bit_length=bit_length, signed=False).set(2**bit_length)
        with pytest.raises(ValueError):
            ModbusInt(FakeConf.w_regs_req, 0, bit_length=bit_length, signed=False).set(2**bit_length)
        with pytest.raises(ValueError):
            ModbusInt(FakeConf.w_regs_req, 0, bit_length=bit_length, signed=False).set(2**bit_length)
    # for unsupported option value: bit_length
    with pytest.raises(ValueError):
        ModbusFloat(FakeConf.w_regs_req, 0, byte_order='bug')  # type: ignore

def test_errors_modbus_float():
    """ Test ModbusFloat errors """
    # === shouldn't raise exception ===
    # for good request type
    for req in [FakeConf.r_regs_req, FakeConf.w_regs_req]:
        ModbusFloat(req, 0)
    # for write a well-typed value
    ModbusFloat(FakeConf.w_regs_req, 0).set(0.0)

    # === should raise exception ===
    # for bad request type
    for req in [FakeConf.r_bits_req, FakeConf.w_bits_req]:
        with pytest.raises(TypeError):
            ModbusInt(req, 0)
    # for writing on read-only
    with pytest.raises(TypeError):
        ModbusFloat(FakeConf.r_regs_req, 0).set(0.0)
    # for write an unsupported value type
    with pytest.raises(TypeError):
        ModbusFloat(FakeConf.w_regs_req, 0).set('oops')  # type: ignore
    # for writing an overrange value
    with pytest.raises(ValueError):
        ModbusFloat(FakeConf.w_regs_req, 0, bit_length=32).set(999.9e99)
    # for unsupported option value: bit_length
    with pytest.raises(ValueError):
        ModbusFloat(FakeConf.w_regs_req, 0, bit_length=128)


def test_read_modbus_bool_src(modbus_srv):
    """ Test ModbusBool reading operations (ModbusServer -> DataSource) """
    for d_inputs in [False, True]:
        # build a dataset
        addr = random.randint(0, 0x1000)
        size = random.randint(1, 2000)
        srv_l = build_bool_data_l(size)
        # init server
        if d_inputs:
            modbus_srv.data_bank.set_discrete_inputs(addr, srv_l)
        else:
            modbus_srv.data_bank.set_coils(addr, srv_l)
        # init client
        mb_device = ModbusTCPDevice(port=5020)
        request = mb_device.add_read_bits_request(addr, size, d_inputs=d_inputs)
        request.schedule_now()
        src_l = [ModbusBool(request, address=addr+i) for i in range(size)]
        # allows time for receive the dataset
        time.sleep(0.1)
        # read dataset
        ds_l = [src.get() for src in src_l]
        # check data match
        assert srv_l == ds_l


def test_read_modbus_int_src(modbus_srv):
    """ Test ModbusInt reading operations (ModbusServer -> DataSource) """
    # test all common options
    for i_regs, bit_length, signed in itertools.product([False, True], [16, 32, 64, 128], [False, True]):
        addr = random.randint(0, 0xffff - 125 + 1)
        size = random.randint(1, 125//to_reg_length(bit_length))
        srv_l = build_int_data_l(size=size, bit_length=bit_length, signed=signed)
        data_as_16b_l = to_16b_list(srv_l, bit_length)
        # init server
        if i_regs:
            modbus_srv.data_bank.set_input_registers(addr, data_as_16b_l)
        else:
            modbus_srv.data_bank.set_holding_registers(addr, data_as_16b_l)
        # init datasource
        nb_reg = len(srv_l) * to_reg_length(bit_length)
        request = ModbusTCPDevice(port=5020).add_read_regs_request(addr, nb_reg, i_regs=i_regs)
        request.schedule_now()
        ds_args = {'bit_length': bit_length, 'signed': signed}
        src_l = [ModbusInt(request, addr+off, **ds_args) for off in range(0, nb_reg, to_reg_length(bit_length))]
        # allows time for receive the dataset
        time.sleep(0.1)
        # read dataset
        ds_l = [src.get() for src in src_l]
        # check data match
        assert srv_l == ds_l


def test_read_modbus_float_src(modbus_srv):
    """ Test ModbusFloat reading operations (ModbusServer -> DataSource) """
    for i_regs, bit_length, in itertools.product([False, True], [32, 64]):
        addr = random.randint(0, 0xffff - 125 + 1)
        size = random.randint(1, 125//to_reg_length(bit_length))
        # build a list of float
        srv_l = [random.random() for _ in range(size)]
        # init server
        encoded_l = [encode_ieee(x, double=bit_length == 64) for x in srv_l]
        regs_l = to_16b_list(encoded_l, bit_length=bit_length)
        if i_regs:
            modbus_srv.data_bank.set_input_registers(addr, regs_l)
        else:
            modbus_srv.data_bank.set_holding_registers(addr, regs_l)
        # init datasource
        request = ModbusTCPDevice(port=5020).add_read_regs_request(addr, len(regs_l), i_regs=i_regs)
        request.schedule_now()
        src_l = []
        for off in range(0, len(regs_l), to_reg_length(bit_length)):
            src_l.append(ModbusFloat(request, addr+off, bit_length=bit_length))
        # allows time for receive the dataset
        time.sleep(0.1)
        # read dataset
        ds_l = [src.get() for src in src_l]
        ds_l[-1] += 0.000_000_1
        # check data match
        assert srv_l == pytest.approx(ds_l, abs=1e-6)


def test_write_modbus_bool_src(modbus_srv):
    """ Test ModbusBool writing operations (DataSource -> ModbusServer) """
    # build a dataset
    addr = random.randint(0, 0x1000)
    size = random.randint(1, 2000)
    ds_l = build_bool_data_l(size)
    # init datasource
    mb_device = ModbusTCPDevice(port=5020)
    request = mb_device.add_write_bits_request(addr, size)
    # write on ds
    for offset, value in enumerate(ds_l):
        ModbusBool(request, address=addr+offset).set(value)
    request.schedule_now()
    # allows time for receive the dataset
    time.sleep(0.1)
    # init server
    srv_l = modbus_srv.data_bank.get_coils(addr, len(ds_l))
    # check data match
    assert ds_l == srv_l


def test_write_modbus_int_src(modbus_srv):
    """ Test ModbusInt writing operations (DataSource -> ModbusServer) """
    # test all common options
    for bit_length, signed in itertools.product([16, 32, 64, 128], [False, True]):
        addr = random.randint(0, 0xffff - 123 + 1)
        size = random.randint(1, 123//to_reg_length(bit_length))
        ds_l = build_int_data_l(size=size, bit_length=bit_length, signed=signed)
        # init datasource
        request = ModbusTCPDevice(port=5020).add_write_regs_request(addr, size * to_reg_length(bit_length))
        for offset, value in enumerate(ds_l):
            offset *= to_reg_length(bit_length)
            ModbusInt(request, addr+offset, bit_length=bit_length, signed=signed).set(value)
        request.schedule_now()
        # allows time for receive the dataset
        time.sleep(0.1)
        # init server
        srv_16b_l = modbus_srv.data_bank.get_holding_registers(addr, size * to_reg_length(bit_length))
        # [list of 16 bits regs] -> raw_bytes
        raw_b = bytes()
        if srv_16b_l:
            for srv_16b in srv_16b_l:
                raw_b += srv_16b.to_bytes(2, byteorder='big')
        # convert raw_bytes to list of well encoded integer
        srv_l = []
        byte_step = to_byte_length(bit_length)
        for i in range(0, len(raw_b), byte_step):
            srv_l.append(int.from_bytes(raw_b[i:i+byte_step], signed=signed))
        # check data match
        assert ds_l == srv_l


def test_write_modbus_float_src(modbus_srv):
    """ Test ModbusInt writing operations (DataSource -> ModbusServer) """
    
    # TODO implement this
    
    return
    # test all common options
    for bit_length in [32, 64]:
        addr = random.randint(0, 0xffff - 123 + 1)
        size = random.randint(1, 123//to_reg_length(bit_length))
        ds_l = build_int_data_l(size=size, bit_length=bit_length)
        # init datasource
        request = ModbusTCPDevice(port=5020).add_write_regs_request(addr, size * to_reg_length(bit_length))
        for offset, value in enumerate(ds_l):
            offset *= to_reg_length(bit_length)
            ModbusFloat(request, addr+offset, bit_length=bit_length).set(value)
        request.schedule_now()
        # allows time for receive the dataset
        time.sleep(0.1)
        # init server
        srv_16b_l = modbus_srv.data_bank.get_holding_registers(addr, size * to_reg_length(bit_length))
        # [list of 16 bits regs] -> raw_bytes
        raw_b = bytes()
        if srv_16b_l:
            for srv_16b in srv_16b_l:
                raw_b += srv_16b.to_bytes(2, byteorder='big')
        # convert raw_bytes to list of well encoded integer
        srv_l = []
        byte_step = to_byte_length(bit_length)
        for i in range(0, len(raw_b), byte_step):
            srv_l.append(int.from_bytes(raw_b[i:i+byte_step]))
        # check data match
        assert ds_l == srv_l
