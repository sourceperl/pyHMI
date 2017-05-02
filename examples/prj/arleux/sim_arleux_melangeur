#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# simulate valve open/close
# stuff in tags.update(): check valve command and set FDC after delay
from pyHMI.DS_ModbusTCP import ModbusTCPDevice
from pyHMI.Tag import Tag
from pyHMI.SimGas import GasPipe, FlowValve
import math
import time
import random as rd


class Devices(object):
    # init datasource
    # PLC TBox
    tbx_api = ModbusTCPDevice('163.111.184.144', port=502, unit_id=2, timeout=2.0, refresh=1.0)
    # init modbus tables
    tbx_api.add_bits_table(20800, 96)
    #tbx_api.add_floats_table(20900, 32)
    # Reg. L1
    tbx_reg1 = ModbusTCPDevice('163.111.184.147', port=502, unit_id=1, timeout=2.0, refresh=1.0)
    # init modbus tables
    tbx_reg1.add_floats_table(768, size=8)
    tbx_reg1.add_floats_table(1280, size=4)


class Tags(object):
    # tags list
    # virtual
    P_MINE = Tag(0.0)
    P_AVAL_MEL = Tag(0.0)
    # from API
    # read
    API_POSTE_MARCHE = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 20803})
    API_L1_MARCHE = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 20804})
    API_L2_MARCHE = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 20805})
    # write
    API_POS_VL1 = Tag(0.0, src=Devices.tbx_api, ref={'type': 'w_float', 'addr': 2058})
    API_POS_VL2 = Tag(0.0, src=Devices.tbx_api, ref={'type': 'w_float', 'addr': 2060})
    API_Q_MINE = Tag(0.0, src=Devices.tbx_api, ref={'type': 'w_float', 'addr': 2062})
    API_P_MINE = Tag(0.0, src=Devices.tbx_api, ref={'type': 'w_float', 'addr': 2304})
    API_P_AO1 = Tag(0.0, src=Devices.tbx_api, ref={'type': 'w_float', 'addr': 2306})
    API_P_AO2 = Tag(0.0, src=Devices.tbx_api, ref={'type': 'w_float', 'addr': 2308})
    # from tbox Reg. L1
    # read
    REG_OUT_VL1 = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'float', 'addr': 1280})
    # write
    REG_M_WOBBE = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'w_float', 'addr': 768})
    REG_M_PCS = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'w_float', 'addr': 770})
    REG_M_DEBIT = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'w_float', 'addr': 772})

    @classmethod
    def update_tags(cls):
        pass


class SimJob(object):
    pipe_mine = GasPipe(init_volume=212 * 50, water_volume=212)
    pipe_aval = GasPipe(init_volume=20000 * 50, water_volume=20000)
    vl1 = FlowValve(q_max=25000.0, up_w_stock=212)
    vl2 = FlowValve(q_max=25000.0, up_w_stock=212)

    @classmethod
    def sim(cls):
        # some vars with random noise
        q_ao = 100000 + rd.randint(-100, 100)
        wbe_ae = 12900 + rd.randint(-5, 5)
        pcs_ae = 10350 + rd.randint(-5, 5)
        wbe_mine = 6000
        pcs_mine = 4900
        # fix P amont/aval
        Tags.P_MINE.val = SimJob.pipe_mine.avg_p
        Tags.P_AVAL_MEL.val = SimJob.pipe_aval.avg_p
        # fix avion flow (limit at 67.7b PMS)
        avion_flow = 10000 * 16 * math.log(67.7 - Tags.P_MINE.val) / 67.7
        # VLs
        cls.vl1.up_flow = avion_flow
        cls.vl1.up_pres = Tags.P_MINE.val
        cls.vl1.down_pres = Tags.P_AVAL_MEL.val
        cls.vl1.pos = Tags.REG_OUT_VL1.val
        cls.vl2.up_flow = avion_flow
        cls.vl2.up_pres = Tags.P_MINE.val
        cls.vl2.down_pres = Tags.P_AVAL_MEL.val
        cls.vl2.pos = 0.0
        # update tags
        Tags.REG_M_DEBIT.val = ((cls.vl1.get_flow() * Tags.API_L1_MARCHE.val) +
                                (cls.vl2.get_flow() * Tags.API_L2_MARCHE.val)) * Tags.API_POSTE_MARCHE.val
        ratio_mine = Tags.REG_M_DEBIT.val / q_ao
        Tags.REG_M_WOBBE.val = ratio_mine * wbe_mine + (1 - ratio_mine) * wbe_ae
        Tags.REG_M_PCS.val = ratio_mine * pcs_mine + (1 - ratio_mine) * pcs_ae
        # set sim pipe params
        SimJob.pipe_mine.in_flow = avion_flow
        SimJob.pipe_mine.out_flow = Tags.REG_M_DEBIT.val
        SimJob.pipe_aval.in_flow = Tags.REG_M_DEBIT.val
        # update EANA API
        Tags.API_POS_VL1.val = cls.vl1.pos * 1.03
        Tags.API_Q_MINE.val = SimJob.pipe_aval.in_flow
        Tags.API_P_MINE.val = Tags.P_MINE.val
        Tags.API_P_AO1.val = Tags.P_AVAL_MEL.val
        Tags.API_P_AO2.val = Tags.P_AVAL_MEL.val


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
