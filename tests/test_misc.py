import unittest
from pyHMI.Misc import swap_bytes, swap_words


class MiscTest(unittest.TestCase):
    """ Test of pyHMI.Misc. """

    def test_swap(self):
        self.assertEqual(swap_bytes(b'\x01\x02\x03\x04'), b'\x02\x01\x04\x03')
        self.assertEqual(swap_words(b'\x01\x02\x03\x04'), b'\x03\x04\x01\x02')
