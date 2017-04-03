#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# simulate valve open/close
# stuff in tags.update(): check valve command and set FDC after delay
from pyHMI.DS_ModbusTCP import ModbusTCPDevice
from pyHMI.Tag import Tag
import math
import time
import random as rd
import sys
sys.path.append('../pyHMI/')
from SimGas import GasPipe, FlowValve


class Devices(object):
    # init datasource
    # Reg. L1
    tbx_reg = ModbusTCPDevice('163.111.184.147', port=502, unit_id=1, timeout=2.0, refresh=1.0)
    # init modbus tables
    tbx_reg.add_floats_table(768, size=8)
    tbx_reg.add_floats_table(1280, size=4)


class Tags(object):
    # tags list
    # virtual
    P_MINE = Tag(0.0)
    P_AVAL_MEL = Tag(0.0)
    # from tbox Reg. L1
    # read
    REG_CMD_VL = Tag(0.0, src=Devices.tbx_reg, ref={'type': 'float', 'addr': 1280})
    # write
    REG_M_WOBBE = Tag(0.0, src=Devices.tbx_reg, ref={'type': 'w_float', 'addr': 768})
    REG_M_PCS = Tag(0.0, src=Devices.tbx_reg, ref={'type': 'w_float', 'addr': 770})
    REG_M_DEBIT = Tag(0.0, src=Devices.tbx_reg, ref={'type': 'w_float', 'addr': 772})

    @classmethod
    def update_tags(cls):
        pass
        # print('%.2f' % Tags.REG_CMD_VL.val)


class SimJob(object):
    pipe_mine = GasPipe(init_volume=212 * 50, water_volume=212)
    pipe_aval = GasPipe(init_volume=20000 * 50, water_volume=20000)
    flow_valve = FlowValve(q_max=25000.0, up_w_stock=212)

    @classmethod
    def sim(cls):
        # some vars with random noise
        q_ao = 100000 + rd.randint(-100, 100)
        wbe_ae = 12900 + rd.randint(-5, 5)
        pcs_ae = 10350 + rd.randint(-5, 5)
        wbe_mine = 6000 + rd.randint(-5, 5)
        pcs_mine = 4900 + rd.randint(-5, 5)
        # fix P aval
        Tags.P_MINE.val = SimJob.pipe_mine.avg_p
        Tags.P_AVAL_MEL.val = SimJob.pipe_aval.avg_p
        # fix avion flow
        avion_flow = 10000 * 16 * math.log(67.7 - Tags.P_MINE.val) / 67.7
        # define flow valve infos
        cls.flow_valve.up_flow = avion_flow
        cls.flow_valve.up_pres = Tags.P_MINE.val
        cls.flow_valve.down_pres = Tags.P_AVAL_MEL.val
        cls.flow_valve.pos = Tags.REG_CMD_VL.val
        # update tags
        Tags.REG_M_DEBIT.val = cls.flow_valve.get_flow()
        ratio_mine = Tags.REG_M_DEBIT.val / q_ao
        Tags.REG_M_WOBBE.val = ratio_mine * wbe_mine + (1 - ratio_mine) * wbe_ae
        Tags.REG_M_PCS.val = ratio_mine * pcs_mine + (1 - ratio_mine) * pcs_ae
        # set sim pipe params
        SimJob.pipe_mine.in_flow = avion_flow
        SimJob.pipe_mine.out_flow = Tags.REG_M_DEBIT.val
        SimJob.pipe_aval.in_flow = Tags.REG_M_DEBIT.val
        # DEBUG
        print('p_amont=%.2f' % Tags.P_MINE.val)
        print('p_aval=%.2f' % Tags.P_AVAL_MEL.val)
        print('vl_delta_p=%.2f' % cls.flow_valve.delta_p)
        print('vl_pos=%.2f' % cls.flow_valve.pos)
        print('vl_flow=%.2f' % SimJob.pipe_aval.in_flow)
        print('')


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
