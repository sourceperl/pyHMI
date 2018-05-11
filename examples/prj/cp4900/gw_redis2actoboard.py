#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Upload redis tags to actoboard IoT platform

from MyPrivateConstants import Redis2Actoboard
from pyHMI.DS_Redis import RedisDevice
from pyHMI.Tag import Tag
import base64
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


class Actoboard(object):
    HEADS = {'Content-type': 'application/json'}

    def __init__(self, push_url, api_key):
        self.push_url = str(push_url)
        self.api_key = str(api_key)

    def update(self, fields):
        # format headers
        auth_str = base64.b64encode(('%s:x' % self.api_key).encode('utf-8')).decode('utf-8')
        auth_str = 'Basic ' + auth_str
        acto_head = Actoboard.HEADS
        acto_head.update({'Authorization': auth_str})
        # do update request
        try:
            request = urllib.request.Request(self.push_url, headers=acto_head, data=json.dumps(fields).encode('utf-8'))
            urllib.request.urlopen(request)
            return True
        except:
            return False


class IotJobs(object):
    # define an actoboard push data source
    actob1 = Actoboard(api_key=Redis2Actoboard.API_KEY,
                       push_url=Redis2Actoboard.PUSH_URL)

    @classmethod
    def actoboard(cls):
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
        cls.actob1.update(fields)


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
        self.do_every(IotJobs.actoboard, every_ms=30000)

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
    # main App
    main_app = MainApp()
    main_app.mainloop()
