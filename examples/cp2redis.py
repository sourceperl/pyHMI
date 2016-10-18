#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# retrieve modbus data from CP4900 device and store it to a redis DB
# CP redis keys begin with 'cp4900:'

from pyHMI.DS_ModbusTCP import ModbusTCPDevice
from pyHMI.Tag import Tag
import redis
import time


class Devices(object):
    # init datasource
    # CP-4900
    cp = ModbusTCPDevice('localhost', port=502, timeout=2.0, refresh=1.0)
    # init modbus tables
    cp.add_floats_table(1, 7)
    cp.add_words_table(17, 1)
    cp.add_longs_table(20, 2)


class Tags(object):
    # tags list
    # from CP
    THT = Tag(0, src=Devices.cp, ref={'type': 'float', 'addr': 1})
    RT = Tag(0, src=Devices.cp, ref={'type': 'float', 'addr': 3})
    SURFACE = Tag(0, src=Devices.cp, ref={'type': 'float', 'addr': 5})
    PRES_V2 = Tag(0, src=Devices.cp, ref={'type': 'float', 'addr': 7})
    DEBIT_CHROM = Tag(0, src=Devices.cp, ref={'type': 'float', 'addr': 13})
    ETAT_GC = Tag(0, src=Devices.cp, ref={'type': 'word', 'addr': 17})
    DEF_ANALYSE = Tag(0, src=Devices.cp, ref={'type': 'long', 'addr': 20})
    DEF_CAPTEUR = Tag(0, src=Devices.cp, ref={'type': 'long', 'addr': 22})
    # virtual
    LOOP_COUNT = Tag(0)

    @classmethod
    def update_tags(cls):
        # update tags
        cls.LOOP_COUNT.val += 1


class Job(object):
    def __init__(self, do_cmd, every_ms=500):
        self.cmd = do_cmd
        self.every_s = every_ms / 1000.0
        self.last_do = 0.0


class MainApp(object):
    def __init__(self):
        # jobs
        self.jobs = []
        # redis
        self.redis = redis.Redis('localhost')
        # periodic update tags
        self.do_every(Tags.update_tags, every_ms=500)
        self.do_every(self.update_redis, every_ms=500)

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
        
    def update_redis(self):
        # status keys
        self.redis.set('cp4900:cp2redis:loop_count', Tags.LOOP_COUNT.val)
        self.redis.set('cp4900:cp2redis:com_ok', Devices.cp.connected)
        # data keys
        self.redis.set('cp4900:tht', Tags.THT.val)
        self.redis.set('cp4900:retention_time', Tags.RT.val)
        self.redis.set('cp4900:peak_area', Tags.SURFACE.val)
        self.redis.set('cp4900:pressure_gas', Tags.PRES_V2.val)
        self.redis.set('cp4900:flow_gas', Tags.DEBIT_CHROM.val)
        self.redis.set('cp4900:analysis_fault', Tags.DEF_ANALYSE.val)
        self.redis.set('cp4900:sensor_fault', Tags.DEF_CAPTEUR.val)
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
        self.redis.set('cp4900:state', cp_status.get(Tags.ETAT_GC.val, 'état inconnu'))


if __name__ == '__main__':
    # main App
    main_app = MainApp()
    main_app.mainloop()
