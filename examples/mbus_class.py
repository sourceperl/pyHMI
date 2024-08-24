#!/usr/bin/env python3

# All stuff is in tags.update()

from pyHMI.DS_ModbusTCP import ModbusTCPDevice, ModbusBool
from pyHMI.Tag import Tag
import time


class Devices:
    def __init__(self) -> None:
        # list here everything related to the devices
        class LocalModbus:
            def __init__(self) -> None:
                self.device = ModbusTCPDevice('localhost', port=502, timeout=2.0, refresh=1.0)
                self.read_req = self.device.add_read_bits_request(1, 2, run_cyclic=True)
                self.write_req = self.device.add_write_bits_request(0, run_cyclic=True)
        self.local_modbus = LocalModbus()


class Tags:
    def __init__(self, devices: Devices) -> None:
        # list all tags here
        self.W_BIT_0 = Tag(False, src=ModbusBool(devices.local_modbus.write_req, address=0))
        self.R_BIT_1 = Tag(False, src=ModbusBool(devices.local_modbus.read_req, address=1))
        self.R_BIT_2 = Tag(False, src=ModbusBool(devices.local_modbus.read_req, address=2))

    def update(self):
        self.W_BIT_0.value = self.R_BIT_1.value and self.R_BIT_2.value


devices = Devices()
tags = Tags(devices)


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
        self.do_every(tags.update, every_ms=500)

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
