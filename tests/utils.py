import random
from typing import List


# some functions
def to_byte_length(bit_length: int) -> int:
    """ Return the minimal number of bytes to contain a bit_length value. """
    return bit_length//8 + (1 if bit_length % 8 else 0)


def to_reg_length(bit_length: int) -> int:
    """ Return the minimal number of 16 bits registers to contain a bit_length value. """
    return bit_length//16 + (1 if bit_length % 16 else 0)


def getrandbits_signed(bit_length: int) -> int:
    """ Signed version of random.getrandbits. """
    return random.getrandbits(bit_length) - (2**bit_length-1)//2


def to_16b_list(int_l: list, bit_length: int) -> List[int]:
    """ Transform an int list of bit_length size into a 16 bits chunks list. """
    _16b_l = []
    for _int in int_l:
        int_as_blocks = []
        for _ in range(0, bit_length, 16):
            int_as_blocks.append(_int & 0xffff)
            _int >>= 16
        _16b_l.extend(reversed(int_as_blocks))
    return _16b_l


def build_bool_data_l(size: int) -> List[bool]:
    """ Build a random list of bool. """
    return [random.choice([False, True]) for _ in range(size)]


def build_int_data_l(size: int, bit_length: int, signed: bool = False) -> List[int]:
    """ Build a random list of int. """
    rand_func = getrandbits_signed if signed else random.getrandbits
    return [rand_func(bit_length) for _ in range(size)]
