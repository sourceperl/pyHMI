#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# simulate valve open/close
# stuff in tags.update(): check valve command and set FDC after delay

from pyHMI.DS_ModbusTCP import ModbusTCPDevice
from pyHMI.Tag import Tag
from pyHMI.Misc import Relay
import time
import math
from threading import Timer

# some const (see http://www.idealvalve.com/pdf/Flow-Calculation-for-Gases.pdf)
SG = 0.554
T_DEG_C = 8.0
VALVE_CV = 0.1


class Devices(object):
    # init datasource
    # PLC TBox
    tbx = ModbusTCPDevice('163.111.181.85', port=502, timeout=2.0, refresh=1.0)
    # init modbus tables
    tbx.add_bits_table(3050, 55)
    tbx.add_floats_table(5030, 16)


class Tags(object):
    # tags list
    # from PLC
    # bit
    V1130_EV_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3066})
    V1130_EV_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3067})
    V1135_EV_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3068})
    V1135_EV_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3069})
    V1136_EV_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3070})
    V1136_EV_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3071})
    MV2_EV_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3072})
    V1130_FDC_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3074})
    V1130_FDC_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3075})
    V1133_FDC_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3076})
    V1133_FDC_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3077})
    V1134_FDC_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3078})
    V1134_FDC_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3079})
    V1135_FDC_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3080})
    V1135_FDC_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3081})
    V1136_FDC_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3082})
    V1136_FDC_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3083})
    V1137_FDC_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3084})
    V1137_FDC_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3085})
    V1138_FDC_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3086})
    V1138_FDC_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3087})
    # float
    P_AM_VL = Tag(0.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5046})
    P_AV_VL = Tag(0.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5048})
    REG_SORTIE = Tag(0.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5060})
    # virtual
    DELTA_P_VL = Tag(0.0, get_cmd=lambda: Tags.P_AM_VL.e_val - Tags.P_AV_VL.e_val)
    # relay
    r1 = Relay()
    r2 = Relay()
    r3 = Relay()
    r4 = Relay()
    r5 = Relay()
    r6 = Relay()

    @classmethod
    def init_tags(cls):
        # init config for neutral (need I/O sym active on tbx)
        # V1130 open
        Devices.tbx.write_bit(524, True)
        # V1133 open
        Devices.tbx.write_bit(526, True)
        # V1134 open
        Devices.tbx.write_bit(528, True)
        # V1135 close
        Devices.tbx.write_bit(530, False)
        Devices.tbx.write_bit(531, True)
        # V1136 open
        Devices.tbx.write_bit(532, False)
        Devices.tbx.write_bit(533, True)
        # V1137 open
        Devices.tbx.write_bit(534, True)
        # V1138 open
        Devices.tbx.write_bit(536, True)
        # set pressure and flow
        Devices.tbx.write_float(1280, 59.2)
        Devices.tbx.write_float(1282, 59.1)
        Devices.tbx.write_float(1284, 59.2)
        # Devices.tbx.write_float(1286, 10000)
        Devices.tbx.write_float(1288, 4.5)
        Devices.tbx.write_float(1290, 0.0)
        Devices.tbx.write_float(1292, 59.0)
        Devices.tbx.write_float(1294, 48.0)

    @classmethod
    def update_tags(cls):
        # update relay state
        cls.r1.update(cls.V1130_EV_OUV.val)
        cls.r2.update(cls.V1130_EV_FER.val)
        cls.r3.update(cls.V1135_EV_OUV.val)
        cls.r4.update(cls.V1135_EV_FER.val)
        cls.r5.update(cls.V1136_EV_OUV.val)
        cls.r6.update(cls.V1136_EV_FER.val)
        # V1130
        if cls.r1.trigger_pos():
            Devices.tbx.write_bit(525, False)
            Timer(15, lambda: Devices.tbx.write_bit(524, True)).start()
        if cls.r2.trigger_pos():
            Devices.tbx.write_bit(524, False)
            Timer(15, lambda: Devices.tbx.write_bit(525, True)).start()
        # V1135
        if cls.r3.trigger_pos():
            Devices.tbx.write_bit(531, False)
            Timer(5, lambda: Devices.tbx.write_bit(530, True)).start()
        if cls.r4.trigger_pos():
            Devices.tbx.write_bit(530, False)
            Timer(5, lambda: Devices.tbx.write_bit(531, True)).start()
        # V1136
        if cls.r5.trigger_pos():
            Devices.tbx.write_bit(533, False)
            Timer(5, lambda: Devices.tbx.write_bit(532, True)).start()
        if cls.r6.trigger_pos():
            Devices.tbx.write_bit(532, False)
            Timer(5, lambda: Devices.tbx.write_bit(533, True)).start()
        # compute flow in process valve
        deg_r = T_DEG_C * 1.8 + 32 + 459.67
        try:
            z_qi = (962 * VALVE_CV * cls.REG_SORTIE.val) / \
                   math.sqrt((SG * deg_r) / (cls.P_AM_VL.val ** 2 - cls.P_AV_VL.val ** 2))
        except ZeroDivisionError:
            z_qi = 0.0
        # write flow
        Devices.tbx.write_float(1286, z_qi)


class Job(object):
    def __init__(self, do_cmd, every_ms=500):
        self.cmd = do_cmd
        self.every_s = every_ms / 1000.0
        self.last_do = 0.0


class MainApp(object):
    def __init__(self):
        # jobs
        self.jobs = []
        # wait modbus thread start
        time.sleep(1.0)
        # init tags
        Tags.init_tags()
        # periodic update tags
        self.do_every(Tags.update_tags, every_ms=500)

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
