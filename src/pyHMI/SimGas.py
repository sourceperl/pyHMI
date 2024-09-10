import math
import threading
import time


# some functions
def celsius_to_kelvin(deg_c: float) -> float:
    """Conversion from degree Celsius to Kelvin"""
    return deg_c + 273.15


def is_subsonic(p_up_bara: float, p_down_bara: float) -> bool:
    """Obtain subsonic state for current pressures"""
    return p_down_bara > p_up_bara / 2


def pipe_water_volume_m3(d_mm: float, l_km: float) -> float:
    """Compute water volume of gas pipeline from current DN (mm) and length (km)"""
    d_m = d_mm / 1_000.0
    l_m = l_km * 1_000.0
    return math.pi * (d_m / 2) ** 2 * l_m


def valve_flow(cv: float, p1_bara: float, p2_bara: float, t_deg_c: float = 6.0, sg: float = 0.554) -> float:
    """Compute flow rate (nm3/h) in a valve from it's Cv.

    The default density of 0.554 is for methane.
    """
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


def valve_cv(q_nm3: float, p1_bara: float, p2_bara: float, t_deg_c: float = 6.0, sg: float = 0.554) -> float:
    """Compute Cv of a valve from it's flow rate (nm3/h).

    The default density of 0.554 is for methane.
    """
    # check args value
    if q_nm3 < 0.00:
        raise ValueError('arg q_nm3 must be positive')
    if p1_bara < 0.00:
        raise ValueError('arg p1_bara must be positive')
    if p2_bara < 0.00:
        raise ValueError('arg p2_bara must be positive')
    # formats args for calculation
    t_k = celsius_to_kelvin(t_deg_c)
    p_up = max(p1_bara, p2_bara)
    p_down = min(p1_bara, p2_bara)
    dp = p_up - p_down
    # circulation below or over critical point
    if is_subsonic(p_up, p_down):
        return q_nm3 / (417 * p_up * (1 - ((2 * dp) / (3 * p_up))) * math.sqrt(dp / (p_up * sg * t_k)))
    else:
        return q_nm3 / (0.471 * 417 * p_up * math.sqrt(1 / (sg * t_k)))


# some class
class SimPipe:
    """ Basic simulation of a gas pipeline :

                             p_bara
                                ^
    +/- process_nm3h <-> [water_vol_m3] <-> +/- network_nm3h
    """

    def __init__(self, init_p_bara: float = 50.0, water_vol_m3: int = 10_000, update_s: float = 0.1):
        # private
        self._stock_vol_m3 = water_vol_m3 * init_p_bara
        self._water_vol_m3 = water_vol_m3
        self._update_s = update_s
        self._process_nm3h = 0
        self._network_nm3h = 0
        self._th_lock = threading.Lock()
        # start update thread
        self._update_th = threading.Thread(target=self._update_th_run, daemon=True)
        self._update_th.start()

    @property
    def process_nm3h(self):
        with self._th_lock:
            return self._process_nm3h

    @process_nm3h.setter
    def process_nm3h(self, value):
        with self._th_lock:
            self._process_nm3h = value

    @property
    def network_nm3h(self):
        with self._th_lock:
            return self._network_nm3h

    @network_nm3h.setter
    def network_nm3h(self, value):
        with self._th_lock:
            self._network_nm3h = value

    @property
    def p_bara(self):
        with self._th_lock:
            return self._stock_vol_m3 / self._water_vol_m3

    @p_bara.setter
    def p_bara(self, value):
        with self._th_lock:
            self._stock_vol_m3 = self._water_vol_m3 * value

    @property
    def water_vol_m3(self):
        with self._th_lock:
            return self._water_vol_m3

    @property
    def stock_vol_m3(self):
        with self._th_lock:
            return self._stock_vol_m3

    def _update_th_run(self):
        while True:
            with self._th_lock:
                # update stock with process and network smoothed flows
                time_ratio = self._update_s/3600
                self._stock_vol_m3 += self._process_nm3h * time_ratio
                self._stock_vol_m3 += self._network_nm3h * time_ratio
                # limit stock volume to 0
                self._stock_vol_m3 = max(0.0, self._stock_vol_m3)
            time.sleep(self._update_s)
