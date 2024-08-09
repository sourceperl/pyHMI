#!/usr/bin/env python3

""" Simulate gas pipe for PID test purpose. """

from pyHMI.DS_ModbusTCP import ModbusTCPDevice
from pyHMI.Tag import Tag
from pyRRD_Redis import RRD_redis, StepAddFunc
import threading
import time
import math


class Devices(object):
    # init datasource
    # PLC TBox
    tbx = ModbusTCPDevice('192.168.0.100', port=502, timeout=2.0, refresh=1.0)
    # init modbus tables
    tbx.add_floats_table(20612, size=9)


class Tags(object):
    # tags list
    # from PLC
    CMD_POS_VL = Tag(0.0, src=Devices.tbx, ref={'type': 'float', 'addr': 20612})
    P_AMT_VL = Tag(65.0, src=Devices.tbx, ref={'type': 'float', 'addr': 20614})
    SET_POINT = Tag(0.0, src=Devices.tbx, ref={'type': 'float', 'addr': 20616})
    # to PLC
    P_AVL_VL = Tag(50.0, src=Devices.tbx, ref={'type': 'w_float', 'addr': 20806, 'swap_word': False})

    @classmethod
    def update_tags(cls):
        pass


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
    def add_flow(self):
        with self._th_lock:
            return self._add_flow

    @add_flow.setter
    def add_flow(self, value):
        with self._th_lock:
            self._add_flow = value

    @property
    def sub_flow(self):
        with self._th_lock:
            return self._sub_flow

    @sub_flow.setter
    def sub_flow(self, value):
        with self._th_lock:
            self._sub_flow = value

    @property
    def avg_p(self):
        with self._th_lock:
            return self._stock_vol / self._water_vol

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


def m3_water_volume(d_mm, l_km):
    d_m = d_mm / 1000.0
    l_m = l_km * 1000.0
    return math.pi * (d_m/2)**2 * l_m


class SimJob(object):
    MAX_FLOW = 250000
    NEED_FLOW = 80000
    pipe = GasPipe(init_volume=500000, water_volume=10000)
    # init RRD db
    rrd_pid_out = RRD_redis('rrd:pid_out', size=32768, step=1.0, add_func=StepAddFunc.avg)
    rrd_set_point = RRD_redis('rrd:set_point', size=32768, step=1.0, add_func=StepAddFunc.avg)
    rrd_proc_value = RRD_redis('rrd:proc_value', size=32768, step=1.0, add_func=StepAddFunc.avg)

    @classmethod
    def sim(cls):
        # fix P aval
        Tags.P_AVL_VL.val = SimJob.pipe.avg_p
        # compute delta P VL
        delta_p = abs(Tags.P_AMT_VL.val - Tags.P_AVL_VL.val)
        # coef_dp = 1 for deltaP=15b and more, coef_dp=0 for deltaP=0b
        coef_dp = 2.0 * delta_p / (delta_p + 15.0)
        coef_dp = min(1.0, coef_dp)
        # flow in valve (ideal valve)
        flow = Tags.CMD_POS_VL.val/100.0 * cls.MAX_FLOW * coef_dp
        # debug
        print('p_aval=%.2f' % Tags.P_AVL_VL.val)
        print('delta_p=%.2f' % delta_p)
        print('coef=%.2f' % coef_dp)
        print('flow=%.2f' % flow)
        print('')
        # set sim pipe params
        SimJob.pipe.add_flow = flow
        SimJob.pipe.sub_flow = cls.NEED_FLOW
        # fill database
        SimJob.rrd_pid_out.add_step(Tags.CMD_POS_VL.val)
        SimJob.rrd_set_point.add_step(Tags.SET_POINT.val)
        SimJob.rrd_proc_value.add_step(Tags.P_AVL_VL.val)


class Job(object):
    def __init__(self, do_cmd, every_ms=500):
        self.cmd = do_cmd
        self.every_s = every_ms / 1000.0
        self.last_do = 0.0


class MainApp(object):
    def __init__(self):
        # jobs
        self.jobs = []
        # periodic update tags
        self.do_every(Tags.update_tags, every_ms=500)
        self.do_every(SimJob.sim, every_ms=1000)

    def mainloop(self):
        # basic scheduler (replace tk after)
        while True:
            for job in self.jobs:
                if job.every_s <= job.last_do:
                    job.cmd()
                    job.last_do = 0.0
                job.last_do += 0.1
            time.sleep(.1)

    def do_every(self, do_cmd, every_ms=1000):
        # store jobs
        self.jobs.append(Job(do_cmd=do_cmd, every_ms=every_ms))
        # first launch
        do_cmd()


if __name__ == '__main__':
    # main App
    main_app = MainApp()
    main_app.mainloop()
