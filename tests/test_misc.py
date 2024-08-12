""" Test of pyHMI.Misc. """

from pyHMI.Misc import swap_bytes, swap_words


def test_swap():
    assert swap_bytes(b'\x01\x02\x03\x04') == b'\x02\x01\x04\x03'
    assert swap_words(b'\x01\x02\x03\x04') == b'\x03\x04\x01\x02'
