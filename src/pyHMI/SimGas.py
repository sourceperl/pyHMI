import math
import threading
import time


class SimPipe:
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
                self._stock_vol_m3 = max(0, self._stock_vol_m3)
            time.sleep(self._update_s)


class GasPipe:
    def __init__(self, init_volume=50000, water_volume=10000):
        # private
        self._add_flow = 0
        self._sub_flow = 0
        self._stock_vol = init_volume
        self._water_vol = water_volume
        self._th_lock = threading.Lock()
        # start update thread
        self._th = threading.Thread(target=self._updater)
        self._th.daemon = True
        self._th.start()

    @property
    def in_flow(self):
        with self._th_lock:
            return self._add_flow

    @in_flow.setter
    def in_flow(self, value):
        with self._th_lock:
            self._add_flow = value

    @property
    def out_flow(self):
        with self._th_lock:
            return self._sub_flow

    @out_flow.setter
    def out_flow(self, value):
        with self._th_lock:
            self._sub_flow = value

    @property
    def avg_p(self):
        with self._th_lock:
            return self._stock_vol / self._water_vol

    @property
    def water_vol(self):
        with self._th_lock:
            return self._water_vol

    @property
    def current_vol(self):
        with self._th_lock:
            return self._stock_vol

    def _updater(self):
        while True:
            with self._th_lock:
                # add volume
                self._stock_vol += self._add_flow / 3600
                # sub volume
                self._stock_vol -= self._sub_flow / 3600
                # min val
                self._stock_vol = max(0, self._stock_vol)
            time.sleep(1.0)


class FlowValve:
    def __init__(self, q_max, up_pres=0.0, up_flow=0.0, up_w_stock=0.0, down_pres=0.0, pos=0.0):
        self.q_max = q_max
        self.up_pres = up_pres
        self.up_flow = up_flow
        self.up_w_stock = up_w_stock
        self.down_pres = down_pres
        self.pos = pos

    @property
    def delta_p(self):
        return self.up_pres - self.down_pres

    def get_flow(self):
        # VL max flow at current pos
        max_flow = (self.pos / 100.0) * self.q_max
        return min((self.up_w_stock * self.delta_p + self.up_flow) * self.pos / 100.0, max_flow)


def get_water_volume(d_mm, l_km):
    d_m = d_mm / 1000.0
    l_m = l_km * 1000.0
    return math.pi * (d_m / 2) ** 2 * l_m
