#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Upload redis tags to thingspeak IoT platform

from MyPrivateConstants import Redis2Thingspeak
from pyHMI.DS_Redis import RedisDevice
from pyHMI.Tag import Tag
import time
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


class Thingspeak(object):
    HEADS = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain'}
    UPDATE_URL = 'https://api.thingspeak.com/update'

    def __init__(self, api_key):
        self.api_key = str(api_key)

    def update(self, fields):
        # format update params (key, field1, field2...)
        d_params = {'key': self.api_key}
        d_params.update(fields)
        params = urllib.parse.urlencode(d_params).encode('utf-8')
        # do update request
        try:
            request = urllib.request.Request(Thingspeak.UPDATE_URL, headers=Thingspeak.HEADS, data=params)
            urllib.request.urlopen(request)
            return True
        except urllib.error.URLError:
            return False


class IotJobs(object):
    # "Test" thingspeak channel
    tspeak1 = Thingspeak(api_key=Redis2Thingspeak.API_KEY)

    @classmethod
    def thingspeak(cls):
        # add Tags with no error to update fields dict
        fields = {}
        if not Tags.CP_THT.err:
            fields['field1'] = Tags.CP_THT.val
        if not Tags.CP_AGE.err:
            fields['field2'] = Tags.CP_AGE.val
        # refresh thingspeak
        cls.tspeak1.update(fields)


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
        self.do_every(IotJobs.thingspeak, every_ms=15000)

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
