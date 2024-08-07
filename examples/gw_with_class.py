#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# All stuff is in tags.update().

from pyHMI.DS_ModbusTCP import ModbusTCPDevice
from pyHMI.Tag import Tag
import time


class Devices(object):
    # init datasource
    # PLC TBox
    plc = ModbusTCPDevice('localhost', port=502, timeout=2.0, refresh=1.0)
    # init modbus tables
    plc.add_read_coils_table(0, 4)


class Tags(object):
    # tags list
    # from PLC
    BIT_0 = Tag(False, src=Devices.plc, ref={'type': 'bit', 'addr': 0})
    BIT_1 = Tag(False, src=Devices.plc, ref={'type': 'bit', 'addr': 1})
    BIT_2 = Tag(False, src=Devices.plc, ref={'type': 'bit', 'addr': 2})
    BIT_3 = Tag(False, src=Devices.plc, ref={'type': 'bit', 'addr': 3})
    # to PLC
    W_BIT_0 = Tag(False, src=Devices.plc, ref={'type': 'w_bit', 'addr': 0})
    W_BIT_1 = Tag(False, src=Devices.plc, ref={'type': 'w_bit', 'addr': 1})
    W_BIT_2 = Tag(False, src=Devices.plc, ref={'type': 'w_bit', 'addr': 2})
    W_BIT_3 = Tag(False, src=Devices.plc, ref={'type': 'w_bit', 'addr': 3})

    @classmethod
    def update_tags(cls):
        # update tags
        cls.W_BIT_0.val = cls.BIT_2.val and cls.BIT_3.val
        cls.W_BIT_1.val = cls.BIT_2.val ^ cls.BIT_3.val


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
