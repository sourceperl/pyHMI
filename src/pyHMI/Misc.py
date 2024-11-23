"""Misc resources."""

import math
import threading
import time
from typing import List, Optional, Union


def auto_repr(self: object, export_t: Optional[tuple] = None) -> str:
    """Auto build obj.__repr__ str"""
    args_str = ''
    for k, v in self.__dict__.items():
        if (export_t and k in export_t) or not export_t:
            if args_str:
                args_str += ', '
            args_str += f'{k}={repr(v)}'
    return f'{self.__class__.__name__}({args_str})'


def swap_bytes(value: Union[bytes, bytearray]) -> bytearray:
    """Swapped bytes in the input bytearray (b'1234' -> b'2143')"""
    sw_value = bytearray(len(value))
    for i in range(0, len(value), 2):
        sw_value[i] = value[i+1]
        sw_value[i+1] = value[i]
    return sw_value


def swap_words(value: Union[bytes, bytearray]) -> bytearray:
    """Swapped words in the input bytearray (b'1234' -> b'3412')"""
    sw_value = bytearray(len(value))
    for i in range(0, len(value), 4):
        sw_value[i:i+2] = value[i+2:i+4]
        sw_value[i+2:i+4] = value[i:i+2]
    return sw_value


def cut_bytes(value: Union[bytes, bytearray], block_size: int) -> Union[List[bytes], List[bytearray]]:
    """Cut a bytes/bytearray as blocks of block_size byte length"""
    return [value[i:i+block_size] for i in range(0, len(value), block_size)]


def cut_bytes_to_regs(value: Union[bytes, bytearray]) -> List[int]:
    """Convert a bytes/bytearray to a list of modbus registers (16-bit big-endian int)"""
    return [int.from_bytes(x, byteorder='big') for x in cut_bytes(value, block_size=2)]


def c_coef(p_bara: float, t_deg_c: float, z: float = 1.0,
           p_bara_b: float = 1.01325, t_deg_c_b: float = 0.0, z_b: float = 1.0) -> float:
    """Compute the value of the conversion coefficient from current measurement values.

    default reference conditions are 1 ATM for pressure (1013.25 hPa), 0 °C for temperature and 1 for Zb.
    """
    return (p_bara/p_bara_b) * (celsius_to_kelvin(t_deg_c_b)/celsius_to_kelvin(t_deg_c)) * (z_b/z)


def speed_ms(flow_m3h: float, dn_mm: float) -> float:
    """Compute gas speed (m/s) from meter gas flow (raw m3/h) and a specific pipe DN (mm)"""
    radius_m = (dn_mm/1_000)/2
    section = math.pi * radius_m**2
    speed_mh = flow_m3h/section
    return speed_mh/3_600


def water_volume_m3(lenght_m: int, dn_mm: int) -> float:
    """Compute water volume (m3) for a specific pipe DN (mm) and length (m)"""
    radius_m = (dn_mm/1_000)/2
    return math.pi * radius_m**2 * lenght_m


def celsius_to_kelvin(deg_c: float) -> float:
    """Conversion from degree Celsius to Kelvin"""
    return deg_c + 273.15


def is_subsonic(p_up_bara: float, p_down_bara: float) -> bool:
    """Obtain subsonic state for current pressures"""
    return p_down_bara > p_up_bara / 2


def valve_flow(cv: float, p1_bara: float, p2_bara: float, t_deg_c: float = 6.0, sg: float = 0.554) -> float:
    """Compute flow rate (nm3/h) in a valve from it's Cv"""
    # check args value
    if p1_bara < 0.00:
        raise ValueError('arg p1_bara must be positive')
    if p2_bara < 0.00:
        raise ValueError('arg p2_bara must be positive')
    # formats args for calculation
    t_k = celsius_to_kelvin(t_deg_c)
    sign = 1 if p1_bara - p2_bara >= 0 else -1
    p_up = max(p1_bara, p2_bara)
    p_down = min(p1_bara, p2_bara)
    dp = p_up - p_down
    # circulation below or over critical point
    if is_subsonic(p_up, p_down):
        return sign * 417 * cv * p_up * (1 - ((2 * dp) / (3 * p_up))) * math.sqrt(dp / (p_up * sg * t_k))
    else:
        return sign * 0.471 * 417 * cv * p_up * math.sqrt(1 / (sg * t_k))


def limit(value, v_min, v_max):
    """
    limit a float or int python var

    :param value: value to limit
    :param v_min: minimum value
    :param v_max: maximum value
    :return: limited value
    """
    try:
        return min(max(value, v_min), v_max)
    except TypeError:
        return None


class Relay:
    def __init__(self):
        self._value = False
        self._last_value = False

    def update(self, state):
        """Set the current relay state."""
        self._last_value = self._value
        self._value = state

    @property
    def state(self):
        """Get the current relay state."""
        return self._value

    def trigger_pos(self):
        """True on positive edge."""
        return self._value and not self._last_value

    def trigger_neg(self):
        """True on negative edge."""
        return self._last_value and not self._value

    def toggle(self):
        """Toggle relay state."""
        self.update(not self._value)


class SafeObject:
    """ Allow thread safe access to object. 

    Usage:
        safe_dict = SafeObject(dict())

        with safe_dict as d:
            d['foo'] += 1
    """

    def __init__(self, obj):
        self._obj = obj
        self._lock = threading.Lock()

    def __enter__(self):
        self._lock.acquire()
        return self._obj

    def __exit__(self, *args):
        self._lock.release()


class TTL:
    def __init__(self, value: float, reset: bool = True) -> None:
        # args
        self.value = value
        # private
        self._expire_at = time.monotonic() + self.value if reset else 0.0

    @property
    def is_expired(self) -> bool:
        return time.monotonic() > self._expire_at

    @property
    def is_not_expired(self) -> bool:
        return not self.is_expired

    def reset(self):
        self._expire_at = time.monotonic() + self.value
