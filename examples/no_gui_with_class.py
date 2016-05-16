#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# All stuff is in tags.update().

from pyHMI.DS_ModbusTCP import ModbusTCPDevice
from pyHMI.Tag import Tag
import time


class Devices(object):
    def __init__(self):
        # init datasource
        # PLC TBox
        self.plc = ModbusTCPDevice('localhost', port=502, timeout=2.0, refresh=1.0)
        # init modbus tables
        self.plc.add_bits_table(0, 4)


class Tags(object):
    def __init__(self, app, update_ms=500):
        self.app = app
        self.update_ms = update_ms
        # Devices
        self.d = self.app.d
        # tags list
        # from PLC
        self.BIT_0 = Tag(False, src=self.d.plc, ref={'type': 'bit', 'addr': 0})
        self.BIT_1 = Tag(False, src=self.d.plc, ref={'type': 'bit', 'addr': 1})
        self.BIT_2 = Tag(False, src=self.d.plc, ref={'type': 'bit', 'addr': 2})
        self.BIT_3 = Tag(False, src=self.d.plc, ref={'type': 'bit', 'addr': 3})
        # to PLC
        self.W_BIT_0 = Tag(False, src=self.d.plc, ref={'type': 'w_bit', 'addr': 0})
        self.W_BIT_1 = Tag(False, src=self.d.plc, ref={'type': 'w_bit', 'addr': 1})
        self.W_BIT_2 = Tag(False, src=self.d.plc, ref={'type': 'w_bit', 'addr': 2})
        self.W_BIT_3 = Tag(False, src=self.d.plc, ref={'type': 'w_bit', 'addr': 3})
        # launch update loop
        self.app.do_every(self.update_tags, every_ms=self.update_ms)

    def update_tags(self):
        # update tags
        self.W_BIT_0.val = self.BIT_2.val and self.BIT_3.val
        self.W_BIT_1.val = self.BIT_2.val ^ self.BIT_3.val


class MainApp(object):
    def __init__(self):
        # jobs
        self.jobs = {}
        # create devices
        self.d = Devices()
        # create tags
        self.t = Tags(self, update_ms=500)

    def mainloop(self):
        # basic scheduler (replace tk after)
        while True:
            for job in self.jobs:
                if self.jobs[job]['every_s'] <= self.jobs[job]['last_do']:
                    job()
                    self.jobs[job]['last_do'] = 0.0
                self.jobs[job]['last_do'] += 0.1
            time.sleep(.1)

    def do_every(self, do_cmd, every_ms=1000):
        # store jobs
        self.jobs[do_cmd] = {'every_s': every_ms/1000.0, 'last_do': 0.0}
        # first launch
        do_cmd()


if __name__ == '__main__':
    # main App
    main_app = MainApp()
    main_app.mainloop()
