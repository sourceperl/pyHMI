#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Start a modbus/TCP server and populate it with CP nano IHM values

from pyHMI.DS_Redis import RedisDevice
from pyHMI.Tag import Tag
import logging
import traceback
import socket
import time
from pyModbusTCP.server import ModbusServer, DataBank
from pyModbusTCP import utils


class Devices(object):
    # init datasource
    redis = RedisDevice()


class Tags(object):
    # tags list
    CP_LOOP_COUNT = Tag(0, src=Devices.redis, ref={'type': 'int', 'key': 'cp4900:cp2redis:loop_count'})
    CP_COM_FAULT = Tag(0, src=Devices.redis, ref={'type': 'bool', 'key': 'cp4900:cp2redis:com_fault'})
    CP_THT = Tag(0, src=Devices.redis, ref={'type': 'float', 'key': 'cp4900:tht'})
    CP_AGE = Tag(0, src=Devices.redis, ref={'type': 'float', 'key': 'cp4900:age'})
    CP_STATE_INT = Tag(0, src=Devices.redis, ref={'type': 'int', 'key': 'cp4900:state_int'})
    CP_STATE = Tag(0, src=Devices.redis, ref={'type': 'str', 'key': 'cp4900:state'})
    CP_RETENTION_TIME = Tag(0, src=Devices.redis, ref={'type': 'float', 'key': 'cp4900:retention_time'})
    CP_PEAK_AREA = Tag(0, src=Devices.redis, ref={'type': 'float', 'key': 'cp4900:peak_area'})
    CP_PRESSURE_GAS = Tag(0, src=Devices.redis, ref={'type': 'float', 'key': 'cp4900:pressure_gas'})
    CP_FLOW_GAS = Tag(0, src=Devices.redis, ref={'type': 'float', 'key': 'cp4900:flow_gas'})
    CP_ANALYSIS_FAULT = Tag(0, src=Devices.redis, ref={'type': 'int', 'key': 'cp4900:analysis_fault'})
    CP_SENSOR_FAULT = Tag(0, src=Devices.redis, ref={'type': 'int', 'key': 'cp4900:sensor_fault'})
    RPI_SIGFOX_SINCE_TX = Tag(0, src=Devices.redis, ref={'type': 'int', 'key': 'rpi_sigfox:since_tx'})

    @classmethod
    def update_tags(cls):
        # update tags
        pass


class ModbusServer(object):
    # init modbus server and start it
    srv = ModbusServer(host='0.0.0.0', port=502, no_block=True)
    srv.start()
    
    @classmethod
    def float2word(cls, floats_list):
        b32_l = [utils.encode_ieee(f) for f in floats_list]
        b16_l = utils.long_list_to_word(b32_l)
        return b16_l

    @classmethod
    def update_items(cls):
        # bit items
        DataBank.set_bits(0, [Tags.CP_COM_FAULT.val])
        # word items
        # life word and other items
        DataBank.set_words(0, [int(time.time()) % 3600])
        DataBank.set_words(1, [Tags.CP_ANALYSIS_FAULT.val])
        DataBank.set_words(2, [Tags.CP_SENSOR_FAULT.val])
        DataBank.set_words(3, [Tags.CP_STATE_INT.val])
        # float items
        DataBank.set_words(100, cls.float2word([Tags.CP_THT.val]))
        DataBank.set_words(102, cls.float2word([Tags.CP_AGE.val]))
        DataBank.set_words(104, cls.float2word([Tags.CP_PRESSURE_GAS.val]))
        DataBank.set_words(106, cls.float2word([Tags.CP_FLOW_GAS.val]))
        DataBank.set_words(108, cls.float2word([Tags.CP_PEAK_AREA.val]))
        DataBank.set_words(110, cls.float2word([Tags.CP_RETENTION_TIME.val]))
        

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
        self.do_every(ModbusServer.update_items, every_ms=1000, do_now=True)

    def mainloop(self):
        # basic scheduler (replace tk after)
        while True:
            for job in self.jobs:
                if job.every_s <= job.last_do:
                    job.cmd()
                    job.last_do = 0.0
                job.last_do += 0.1
            time.sleep(.1)

    def do_every(self, do_cmd, every_ms=1000, do_now=True):
        # store jobs
        self.jobs.append(Job(do_cmd=do_cmd, every_ms=every_ms))
        # first call (now or after every_ms)
        if do_now:
            do_cmd()


if __name__ == '__main__':
    # logging setup
    logging.basicConfig(format='%(asctime)s %(message)s')
    # main App
    main_app = MainApp()
    main_app.mainloop()
