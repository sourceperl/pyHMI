import random
import time
import unittest
from pyModbusTCP.server import ModbusServer
from pyModbusTCP.utils import long_list_to_word
from pyHMI.DS_ModbusTCP import ModbusTCPDevice, ModbusBool, ModbusInt, ModbusFloat


# some functions
def to_reg_length(bit_length: int) -> int:
    """ Return the minimal number of 16 bits registers to contain a bit_length value. """
    return bit_length//16 + (1 if bit_length % 16 else 0)


def getrandbits_signed(bit_length: int, signed: bool = True) -> int:
    value = random.getrandbits(bit_length)
    if signed:
        value -= (2**bit_length-1)//2
    return value


def to_16bit_chunks(int_l: list, int_bit_lenght: int) -> list:
    result_l = []
    for _int in int_l:
        _16b_l = []
        for _ in range(0, int_bit_lenght, 16):
            _16b_l.append(_int & 0xffff)
            _int >>= 16
        _16b_l.reverse()
        result_l.extend(_16b_l)
    return result_l


class DS_ModbusTCP_Test(unittest.TestCase):
    """ """

    def setUp(self) -> None:
        self.srv = ModbusServer(port=5020, no_block=True)
        self.srv.start()

    def tearDown(self) -> None:
        self.srv.stop()

    def test_read_modbus_bool_src(self):
        """ """
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

    def test_read_modbus_int_src(self):
        """ """
        # build a dataset
        from_addr = random.randint(0, 0xffff - 125 + 1)
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

    def test_read_modbus_signed_int_src(self):
        """ Test ModbusInt on the input registers space with a signed or not int at each standard bit length. """
        # build a dataset
        for bit_len in [16, 32, 64, 128]:
            for signed in [False, True]:
                nb_min_reg = to_reg_length(bit_length=bit_len)
                from_addr = random.randint(0, 0xffff - 125 + 1)
                nb_int = random.randint(1, 125//nb_min_reg)
                nb_16b_regs = nb_int * nb_min_reg
                srv_l = [getrandbits_signed(bit_length=bit_len, signed=signed) for _ in range(nb_int)]
                # 32 to 16 bits
                srv_l_16b = to_16bit_chunks(srv_l, int_bit_lenght=bit_len)
                # init server side
                self.srv.data_bank.set_input_registers(from_addr, srv_l_16b)
                # init client side
                my_request = ModbusTCPDevice(port=5020).add_read_regs_request(from_addr, size=nb_16b_regs, i_regs=True)
                my_request.run_now()
                src_l = []
                for offset in range(0, nb_16b_regs, nb_min_reg):
                    src_l.append(ModbusInt(my_request, address=from_addr+offset, bit_length=bit_len, signed=signed))
                # allows time for receive the dataset
                time.sleep(0.1)
                # read dataset
                cli_l = []
                for src in src_l:
                    cli_l.append(src.get())
                # check data match
                self.assertEqual(srv_l, cli_l)
