import random
import time
import unittest
from pyModbusTCP.server import ModbusServer
from pyHMI.DS_ModbusTCP import ModbusTCPDevice, ModbusBool, ModbusInt, ModbusFloat


class DS_ModbusTCP_Test(unittest.TestCase):
    """ """

    def setUp(self) -> None:
        self.srv = ModbusServer(port=5020, no_block=True)
        self.srv.start()

    def tearDown(self) -> None:
        self.srv.stop()

    def test_bool_src(self):
        # build a dataset
        from_addr = random.randint(0, 0x1000)
        size = random.randint(1, 2000)
        srv_l = [random.choice([False, True]) for _ in range(size)]
        # init server side
        self.srv.data_bank.set_coils(from_addr, srv_l)
        # init client side
        mb_device = ModbusTCPDevice(port=5020)
        my_request = mb_device.add_read_bits_request(from_addr, size)
        my_request.run_now()
        src_l = []
        for i in range(size):
            src_l.append(ModbusBool(my_request, address=from_addr+i))
        # allows time for receive the dataset
        time.sleep(0.1)
        # read dataset
        cli_l = []
        for src in src_l:
            cli_l.append(src.get())
        # check data match
        self.assertEqual(srv_l, cli_l)

    def test_int_src(self):
        # build a dataset
        from_addr = random.randint(0, 0xf000)
        size = random.randint(1, 125)
        srv_l = [random.randint(0, 0xffff) for _ in range(size)]
        # init server side
        self.srv.data_bank.set_holding_registers(from_addr, srv_l)
        # init client side
        my_request = ModbusTCPDevice(port=5020).add_read_regs_request(from_addr, size)
        my_request.run_now()
        src_l = []
        for i in range(size):
            src_l.append(ModbusInt(my_request, address=from_addr+i))
        # allows time for receive the dataset
        time.sleep(0.1)
        # read dataset
        cli_l = []
        for src in src_l:
            cli_l.append(src.get())
        # check data match
        self.assertEqual(srv_l, cli_l)