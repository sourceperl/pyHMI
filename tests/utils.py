import random
import string
import struct
from typing import List, Optional


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


def int_to_single_float(value: int) -> float:
    """ Convert an integer value to its single float representation. """
    return struct.unpack('f', struct.pack('I', value))[0]


def single_float_to_int(value: float) -> int:
    """ Convert a single float to its int representation. """
    return struct.unpack('I', struct.pack('f', value))[0]


def int_to_double_float(value: int) -> float:
    """ Convert an integer value to its double float representation. """
    return struct.unpack('d', struct.pack('Q', value))[0]


def double_float_to_int(value: float) -> int:
    """ Convert a double float to its int representation. """
    return struct.unpack('Q', struct.pack('d', value))[0]


def regs_to_bytes(regs_l: list) -> bytes:
    """ Convert a list of 16 bits registers to its bytes representation. """
    return struct.pack('>' + 'H' * len(regs_l), *regs_l)


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


def cut_bytes(value: bytes, block_size: int) -> list:
    """ Cut a bytes as blocks of block_size byte length. """
    return [value[i:i+block_size] for i in range(0, len(value), block_size)]


def build_random_str(length: Optional[int] = None) -> str:
    """ Build a random string. """
    length = random.randint(1, 255) if length is None else length
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def build_bool_data_l(size: int) -> List[bool]:
    """ Build a random list of bool. """
    return [random.choice([False, True]) for _ in range(size)]


def build_int_data_l(size: int, bit_length: int, signed: bool = False) -> List[int]:
    """ Build a random list of int. """
    rand_func = getrandbits_signed if signed else random.getrandbits
    return [rand_func(bit_length) for _ in range(size)]


def build_float_data_l(size: int, bit_length: int) -> List[float]:
    """ Build a random list of int. """
    # check bit_length arg
    assert bit_length in [32, 64]
    # rand func() returns a 32 or 64 bit wide random integer converted to a float
    if bit_length == 32:
        def rand_func(): return int_to_single_float(random.getrandbits(32))
    else:
        def rand_func(): return int_to_double_float(random.getrandbits(64))
    # build list
    return [rand_func() for _ in range(size)]
