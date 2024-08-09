"""Misc resources."""

from typing import List, Union
import math
import threading


def swap_bytes(value: Union[bytes, bytearray]) -> bytearray:
    """Swapped bytes in the input bytearray (b'\x01\x02\x03\x04' -> b'\x02\x01\x04\x03')"""
    sw_value = bytearray(len(value))
    for i in range(0, len(value), 2):
        sw_value[i] = value[i+1]
        sw_value[i+1] = value[i]
    return sw_value


def swap_word(value: Union[bytes, bytearray]) -> bytearray:
    """Swapped words in the input bytearray (b'\xde\xad\xbe\xef' -> b'\xbe\xef\xde\xad')"""
    sw_value = bytearray(len(value))
    for i in range(0, len(value), 4):
        sw_value[i:i+2] = value[i+2:i+4]
        sw_value[i+2:i+4] = value[i:i+2]
    return sw_value


def bytes2word_list(value: Union[bytes, bytearray]) -> List[int]:
    """Convert a bytearray to a list of word value"""
    ret_l = []
    for i in range(0, len(value), 2):
        ret_l.append(int.from_bytes(value[i:i+2], byteorder='big'))
    return ret_l


def speed_ms(flow_nm3h: float, p_bara: float, dn_mm: int) -> float:
    """Compute gas speed (m/s) from gas flow (nm3/h), pressure (bara) and a specific pipe DN (mm)"""
    radius_m = (dn_mm/1000)/2
    section = math.pi * radius_m**2
    speed_mh = flow_nm3h/(p_bara * section)
    return speed_mh/3600


def water_volume_m3(lenght_m: int, dn_mm: int) -> float:
    """Compute water volume (m3) for a specific pipe DN (mm) and length (m)"""
    radius_m = (dn_mm/1000)/2
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
