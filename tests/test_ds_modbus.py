import itertools
import random
import time
import unittest
from pyModbusTCP.server import ModbusServer
from pyModbusTCP.utils import encode_ieee
from pyHMI.DS_ModbusTCP import ModbusTCPDevice, ModbusBool, ModbusInt, ModbusFloat
from .utils import to_byte_length, to_reg_length, to_16b_list, build_bool_data_l, build_int_data_l


class DS_ModbusTCP_IO(unittest.TestCase):
    """ Test of every DS_ModbusTCP DataSource subclass """

    def assert_list_almost_equal(self, l1: list, l2: list, places: int = 7):
        self.assertEqual(len(l1), len(l2))
        for a, b in zip(l1, l2):
            self.assertAlmostEqual(a, b, places=places)

    def setUp(self) -> None:
        self.srv = ModbusServer(port=5020, no_block=True)
        self.srv.start()

    def tearDown(self) -> None:
        self.srv.stop()

    def test_read_modbus_bool_src(self):
        """ Test ModbusBool reading operations (ModbusServer -> DataSource) """
        for d_inputs in [False, True]:
            # build a dataset
            addr = random.randint(0, 0x1000)
            size = random.randint(1, 2000)
            srv_l = build_bool_data_l(size)
            # init server
            if d_inputs:
                self.srv.data_bank.set_discrete_inputs(addr, srv_l)
            else:
                self.srv.data_bank.set_coils(addr, srv_l)
            # init client
            mb_device = ModbusTCPDevice(port=5020)
            request = mb_device.add_read_bits_request(addr, size, d_inputs=d_inputs)
            request.run_now()
            src_l = [ModbusBool(request, address=addr+i) for i in range(size)]
            # allows time for receive the dataset
            time.sleep(0.1)
            # read dataset
            ds_l = [src.get() for src in src_l]
            # check data match
            self.assertEqual(srv_l, ds_l)

    def test_read_modbus_int_src(self):
        """ Test ModbusInt reading operations (ModbusServer -> DataSource) """
        # test all common options
        for i_regs, bit_length, signed in itertools.product([False, True], [16, 32, 64, 128], [False, True]):
            addr = random.randint(0, 0xffff - 125 + 1)
            size = random.randint(1, 125//to_reg_length(bit_length))
            srv_l = build_int_data_l(size=size, bit_length=bit_length, signed=signed)
            data_as_16b_l = to_16b_list(srv_l, bit_length)
            # init server
            if i_regs:
                self.srv.data_bank.set_input_registers(addr, data_as_16b_l)
            else:
                self.srv.data_bank.set_holding_registers(addr, data_as_16b_l)
            # init datasource
            nb_reg = len(srv_l) * to_reg_length(bit_length)
            request = ModbusTCPDevice(port=5020).add_read_regs_request(addr, nb_reg, i_regs=i_regs)
            request.run_now()
            ds_args = {'bit_length': bit_length, 'signed': signed}
            src_l = [ModbusInt(request, addr+off, **ds_args) for off in range(0, nb_reg, to_reg_length(bit_length))]
            # allows time for receive the dataset
            time.sleep(0.1)
            # read dataset
            ds_l = [src.get() for src in src_l]
            # check data match
            self.assertEqual(srv_l, ds_l)

    def test_read_modbus_float_src(self):
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
                self.srv.data_bank.set_input_registers(addr, regs_l)
            else:
                self.srv.data_bank.set_holding_registers(addr, regs_l)
            # init datasource
            request = ModbusTCPDevice(port=5020).add_read_regs_request(addr, len(regs_l), i_regs=i_regs)
            request.run_now()
            src_l = []
            for off in range(0, len(regs_l), to_reg_length(bit_length)):
                src_l.append(ModbusFloat(request, addr+off, bit_length=32 if bit_length == 32 else 64))
            # allows time for receive the dataset
            time.sleep(0.1)
            # read dataset
            ds_l = [src.get() for src in src_l]
            # check data match
            self.assert_list_almost_equal(srv_l, ds_l, places=7 if bit_length == 32 else 14)

    def test_write_modbus_bool_src(self):
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
        request.run_now()
        # allows time for receive the dataset
        time.sleep(0.1)
        # init server
        srv_l = self.srv.data_bank.get_coils(addr, len(ds_l))
        # check data match
        self.assertEqual(ds_l, srv_l)

    def test_write_modbus_int_src(self):
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
            request.run_now()
            # allows time for receive the dataset
            time.sleep(0.1)
            # init server
            srv_16b_l = self.srv.data_bank.get_holding_registers(addr, size * to_reg_length(bit_length))
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
            self.assertEqual(ds_l, srv_l)


class DS_ModbusTCP_Excepts(unittest.TestCase):
    """ Test of every DS_ModbusTCP DataSource subclass. """

    def test_modbus_int(self):
        """ Test ModbusInt errors """
        # a fake query that is never scheduled (default for all write requests)
        a_request = ModbusTCPDevice(port=5020).add_write_regs_request(0, size=8)

        # should raise exception
        with self.assertRaises(ValueError):
            ModbusInt(a_request, 0, bit_length=16, signed=False).set(-1)
        with self.assertRaises(ValueError):
            ModbusInt(a_request, 0, bit_length=16, signed=False).set(2**16)
        with self.assertRaises(ValueError):
            ModbusInt(a_request, 0, bit_length=16, signed=True).set(2**15)

        # shouldn't raise exception
        try:
            ModbusInt(a_request, 0, bit_length=16, signed=True).set(-1)
            ModbusInt(a_request, 0, bit_length=16, signed=False).set(2**16-1)
            ModbusInt(a_request, 0, bit_length=32, signed=False).set(2**32-1)
            ModbusInt(a_request, 0, bit_length=64, signed=False).set(2**64-1)
        except Exception as e:
            self.fail(f'Exception {e!r} raised unexpectedly')
