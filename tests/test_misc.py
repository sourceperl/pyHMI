""" Test of Misc """

from pyHMI.Misc import swap_bytes, swap_words


def test_swap():
    assert swap_bytes(b'1234') == b'2143'
    assert swap_words(b'1234') == b'3412'
