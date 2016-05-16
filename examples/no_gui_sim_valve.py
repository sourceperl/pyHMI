#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# simulate valve open/close
# stuff in tags.update(): check valve command and set FDC after delay

from pyHMI.DS_ModbusTCP import ModbusTCPDevice
from pyHMI.Tag import Tag
from pyHMI.Misc import Relay
import time
from threading import Timer


class Devices(object):
    def __init__(self):
        # init datasource
        # PLC TBox
        self.tbx = ModbusTCPDevice('163.111.181.85', port=502, timeout=2.0, refresh=1.0)
        # init modbus tables
        self.tbx.add_bits_table(3050, 55)
        self.tbx.add_bits_table(1536, 8)
        self.tbx.add_words_table(4000, 5)
        self.tbx.add_floats_table(5030, 8)


class Tags(object):
    def __init__(self, app, update_ms=500):
        self.app = app
        self.update_ms = update_ms
        # Devices
        self.d = self.app.d
        # tags list
        # from PLC
        self.V1130_EV_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3066})
        self.V1130_EV_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3067})
        self.V1135_EV_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3068})
        self.V1135_EV_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3069})
        self.V1136_EV_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3070})
        self.V1136_EV_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3071})
        self.MV2_EV_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3072})
        self.V1130_FDC_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3074})
        self.V1130_FDC_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3075})
        self.V1133_FDC_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3076})
        self.V1133_FDC_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3077})
        self.V1134_FDC_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3078})
        self.V1134_FDC_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3079})
        self.V1135_FDC_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3080})
        self.V1135_FDC_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3081})
        self.V1136_FDC_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3082})
        self.V1136_FDC_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3083})
        self.V1137_FDC_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3084})
        self.V1137_FDC_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3085})
        self.V1138_FDC_OUV = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3086})
        self.V1138_FDC_FER = Tag(False, src=self.d.tbx, ref={'type': 'bit', 'addr': 3087})
        # relay
        self.r1 = Relay()
        self.r2 = Relay()
        self.r3 = Relay()
        self.r4 = Relay()
        self.r5 = Relay()
        self.r6 = Relay()
        # launch update loop
        self.app.do_every(self.update_tags, every_ms=self.update_ms)

    def update_tags(self):
        self.r1.state = self.V1130_EV_OUV.val
        self.r2.state = self.V1130_EV_FER.val
        self.r3.state = self.V1135_EV_OUV.val
        self.r4.state = self.V1135_EV_FER.val
        self.r5.state = self.V1136_EV_OUV.val
        self.r6.state = self.V1136_EV_FER.val
        # V1130
        if self.r1.trigger_pos():
            self.d.tbx.write_bit(525, False)
            Timer(15, lambda: self.d.tbx.write_bit(524, True)).start()
        if self.r2.trigger_pos():
            self.d.tbx.write_bit(524, False)
            Timer(15, lambda: self.d.tbx.write_bit(525, True)).start()
        # V1135
        if self.r3.trigger_pos():
            self.d.tbx.write_bit(531, False)
            Timer(5, lambda: self.d.tbx.write_bit(530, True)).start()
        if self.r4.trigger_pos():
            self.d.tbx.write_bit(530, False)
            Timer(5, lambda: self.d.tbx.write_bit(531, True)).start()
        # V1136
        if self.r5.trigger_pos():
            self.d.tbx.write_bit(533, False)
            Timer(5, lambda: self.d.tbx.write_bit(532, True)).start()
        if self.r6.trigger_pos():
            self.d.tbx.write_bit(532, False)
            Timer(5, lambda: self.d.tbx.write_bit(533, True)).start()


class App(object):
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
    app = App()
    app.mainloop()
