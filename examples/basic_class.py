#!/usr/bin/env python3

# All stuff is in tags.update().

from pyHMI.DS_ModbusTCP import ModbusTCPDevice, ModbusBool
from pyHMI.Tag import Tag
import time


class Devices:
    # list all datasource here
    md = ModbusTCPDevice('localhost', port=502, timeout=2.0, read_refresh=1.0, write_refresh=1.0)
    md.add_write_bits_request(0)
    md.add_read_bits_request(1, 2)


class Tags:
    # list all tags here
    W_BIT_0 = Tag(False, src=ModbusBool(Devices.md, address=0, write=True))
    R_BIT_1 = Tag(False, src=ModbusBool(Devices.md, address=1))
    R_BIT_2 = Tag(False, src=ModbusBool(Devices.md, address=2))

    @classmethod
    def update_tags(cls):
        cls.W_BIT_0.val = cls.R_BIT_1.val and cls.R_BIT_2.val


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
