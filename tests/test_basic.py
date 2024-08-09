import unittest
from pyModbusTCP.server import ModbusServer
from pyHMI.Misc import swap_bytes, swap_word


class MiscTest(unittest.TestCase):
    """ Test of pyHMI.Misc. """

    def test_swap(self):
        self.assertEqual(swap_bytes(b'\x01\x02\x03\x04'), b'\x02\x01\x04\x03')
        self.assertEqual(swap_word(b'\x01\x02\x03\x04'), b'\x03\x04\x01\x02')


class MyTest(unittest.TestCase):
    """ """

    def setUp(self) -> None:
        self.srv = ModbusServer(port=5020, no_block=True)
        self.srv.start()

    def tearDown(self) -> None:
        self.srv.stop()

    def test_misc(self):
        pass
