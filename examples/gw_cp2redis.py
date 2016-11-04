#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# retrieve modbus data from CP4900 device and store it to a redis DB
# CP redis keys begin with 'cp4900:'

from pyHMI.DS_ModbusTCP import ModbusTCPDevice
from pyHMI.DS_Redis import RedisDevice
from pyHMI.Tag import Tag
from pyHMI.Misc import limit
import time


class Devices(object):
    # init datasource
    # CP-4900
    cp = ModbusTCPDevice('163.111.182.171', port=502, timeout=2.0, refresh=1.0)
    # init modbus tables
    cp.add_bits_table(1, 3, use_f1=True)
    cp.add_floats_table(1, 7, use_f4=True)
    cp.add_words_table(17, 1, use_f4=True)
    cp.add_longs_table(20, 2, use_f4=True)
    # Redis on localhost
    rd = RedisDevice()


class Tags(object):
    # tags list
    # from CP-4900
    NEW_DATA_PC1 = Tag(False, src=Devices.cp, ref={'type': 'bit', 'addr': 1})
    CALIB = Tag(False, src=Devices.cp, ref={'type': 'bit', 'addr': 2})
    NEW_DATA_PC2 = Tag(False, src=Devices.cp, ref={'type': 'bit', 'addr': 3})
    THT = Tag(0.0, src=Devices.cp, ref={'type': 'float', 'addr': 1})
    RT = Tag(0.0, src=Devices.cp, ref={'type': 'float', 'addr': 3})
    SURFACE = Tag(0.0, src=Devices.cp, ref={'type': 'float', 'addr': 5})
    PRES_V2 = Tag(0.0, src=Devices.cp, ref={'type': 'float', 'addr': 7})
    DEBIT_CHROM = Tag(0.0, src=Devices.cp, ref={'type': 'float', 'addr': 13})
    ETAT_GC = Tag(0, src=Devices.cp, ref={'type': 'word', 'addr': 17})
    DEF_ANALYSE = Tag(0, src=Devices.cp, ref={'type': 'long', 'addr': 20})
    DEF_CAPTEUR = Tag(0, src=Devices.cp, ref={'type': 'long', 'addr': 22})
    # to Redis
    RD_CP_NEW_DATA_PC1 = Tag(False, src=Devices.rd, ref={'type': 'bool', 'key': 'cp4900:new_data_flag_1', 'ttl': 10})
    RD_CP_NEW_DATA_PC2 = Tag(False, src=Devices.rd, ref={'type': 'bool', 'key': 'cp4900:new_data_flag_2', 'ttl': 10})
    RD_CP_CALIB = Tag(False, src=Devices.rd, ref={'type': 'bool', 'key': 'cp4900:calibration', 'ttl': 10})
    RD_CP_LOOP_COUNT = Tag(0, src=Devices.rd, ref={'type': 'int', 'key': 'cp4900:cp2redis:loop_count', 'ttl': 10})
    RD_CP_COM_FAULT = Tag(False, src=Devices.rd, ref={'type': 'bool', 'key': 'cp4900:cp2redis:com_fault', 'ttl': 10})
    RD_CP_THT = Tag(0.0, src=Devices.rd, ref={'type': 'float', 'key': 'cp4900:tht', 'ttl': 10})
    RD_CP_AGE = Tag(0, src=Devices.rd, ref={'type': 'float', 'key': 'cp4900:age', 'ttl': 10})
    RD_CP_RETENTION_TIME = Tag(0.0, src=Devices.rd, ref={'type': 'float', 'key': 'cp4900:retention_time', 'ttl': 10})
    RD_CP_PEAK_AREA = Tag(0.0, src=Devices.rd, ref={'type': 'float', 'key': 'cp4900:peak_area', 'ttl': 10})
    RD_CP_PRESSURE_GAS = Tag(0.0, src=Devices.rd, ref={'type': 'float', 'key': 'cp4900:pressure_gas', 'ttl': 10})
    RD_CP_FLOW_GAS = Tag(0.0, src=Devices.rd, ref={'type': 'float', 'key': 'cp4900:flow_gas', 'ttl': 10})
    RD_CP_ANALYSIS_FAULT = Tag(0, src=Devices.rd, ref={'type': 'int', 'key': 'cp4900:analysis_fault', 'ttl': 10})
    RD_CP_SENSOR_FAULT = Tag(0, src=Devices.rd, ref={'type': 'int', 'key': 'cp4900:sensor_fault', 'ttl': 10})
    RD_CP_STATE = Tag('', src=Devices.rd, ref={'type': 'str', 'key': 'cp4900:state', 'ttl': 10})
    # virtual
    LOOP_COUNT = Tag(0)
    CP_REFRESH = Tag(time.time())

    @classmethod
    def update_tags(cls):
        # update tags
        Tags.LOOP_COUNT.val += 1
        # status keys
        Tags.RD_CP_LOOP_COUNT.val = Tags.LOOP_COUNT.val
        Tags.RD_CP_COM_FAULT.val = not Devices.cp.connected
        # CP-4900 age
        Tags.RD_CP_AGE.val = (time.time() - Tags.CP_REFRESH.val) / 60
        # store refresh date when new data flag is set
        if Tags.NEW_DATA_PC1.val:
            Tags.CP_REFRESH.val = time.time()
        # data keys
        Tags.RD_CP_NEW_DATA_PC1.val = Tags.NEW_DATA_PC1.e_val
        Tags.RD_CP_NEW_DATA_PC2.val = Tags.NEW_DATA_PC2.e_val
        Tags.RD_CP_CALIB.val = Tags.CALIB.e_val
        Tags.RD_CP_THT.val = limit(Tags.THT.e_val, 0.0, 250.0)
        Tags.RD_CP_RETENTION_TIME.val = limit(Tags.RT.e_val, 0.0, 1000.0)
        Tags.RD_CP_PEAK_AREA.val = limit(Tags.SURFACE.e_val, 0.0, 1000.0)
        Tags.RD_CP_PRESSURE_GAS.val = limit(Tags.PRES_V2.e_val, 0.0, 10000.0)
        Tags.RD_CP_FLOW_GAS.val = limit(Tags.DEBIT_CHROM.e_val, 0.0, 100.0)
        Tags.RD_CP_ANALYSIS_FAULT.val = Tags.DEF_ANALYSE.e_val
        Tags.RD_CP_SENSOR_FAULT.val = Tags.DEF_CAPTEUR.e_val

        # cp state
        cp_status = {
            0: 'initialisation',
            1: 'purge',
            2: 'analyse en cours',
            3: 'stabilisation',
            4: 'prêt',
            5: 'erreur',
            6: 'erreur temporaire',
            7: 'défectueux',
            8: 'pas prêt'
        }
        Tags.RD_CP_STATE.val = cp_status.get(Tags.ETAT_GC.val, 'état inconnu').encode('utf-8')


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
