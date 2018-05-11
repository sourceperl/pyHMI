#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Upload redis tags to dweet IoT platform

from MyPrivateConstants import Redis2Dweet
from pyHMI.DS_Redis import RedisDevice
from pyHMI.Tag import Tag
import logging
import traceback
import socket
import time
import json
import urllib.parse
import urllib.request
import urllib.error


class Devices(object):
    # init datasource
    # PLC TBox
    redis = RedisDevice()


class Tags(object):
    # tags list
    # from PLC
    CP_LOOP_COUNT = Tag(0, src=Devices.redis, ref={'type': 'int', 'key': 'cp4900:cp2redis:loop_count'})
    CP_COM_FAULT = Tag(0, src=Devices.redis, ref={'type': 'bool', 'key': 'cp4900:cp2redis:com_fault'})
    CP_THT = Tag(0, src=Devices.redis, ref={'type': 'float', 'key': 'cp4900:tht'})
    CP_AGE = Tag(0, src=Devices.redis, ref={'type': 'float', 'key': 'cp4900:age'})
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


class Dweet(object):
    HEADS = {'Content-type': 'application/json'}
    UPDATE_URL = 'https://dweet.io/dweet/for/'

    def __init__(self, dweet_id):
        self.dweet_id = str(dweet_id)

    def update(self, fields):
        # do update request
        try:
            request = urllib.request.Request(Dweet.UPDATE_URL + self.dweet_id, headers=Dweet.HEADS,
                                             data=json.dumps(fields).encode('utf-8'))
            urllib.request.urlopen(request, timeout=10)
            return True
        except Exception as e:
            logging.error(traceback.format_exc())
            return False


class IotJobs(object):
    # define a dweet data source
    dweet1 = Dweet(dweet_id=Redis2Dweet.DWEET_ID)

    @classmethod
    def dweet(cls):
        # add Tags with no error to update fields dict
        fields = {}
        fields['CP_LOOP_COUNT'] = Tags.CP_LOOP_COUNT.val
        fields['CP_COM_FAULT'] = Tags.CP_COM_FAULT.val
        fields['CP_THT'] = round(Tags.CP_THT.val, 2)
        fields['CP_AGE'] = round(Tags.CP_AGE.val, 2)
        fields['CP_STATE'] = Tags.CP_STATE.val
        fields['CP_RETENTION_TIME'] = round(Tags.CP_RETENTION_TIME.val, 2)
        fields['CP_PEAK_AREA'] = round(Tags.CP_PEAK_AREA.val, 2)
        fields['CP_PRESSURE_GAS'] = round(Tags.CP_PRESSURE_GAS.val, 2)
        fields['CP_FLOW_GAS'] = round(Tags.CP_FLOW_GAS.val, 2)
        fields['CP_ANALYSIS_FAULT'] = Tags.CP_ANALYSIS_FAULT.val
        fields['CP_SENSOR_FAULT'] = Tags.CP_SENSOR_FAULT.val
        fields['RPI_SIGFOX_SINCE_TX'] = Tags.RPI_SIGFOX_SINCE_TX.val
        # refresh actoboard data source
        cls.dweet1.update(fields)


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
        self.do_every(IotJobs.dweet, every_ms=30000, do_now=False)

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
