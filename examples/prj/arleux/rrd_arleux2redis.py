#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyHMI.DS_ModbusTCP import ModbusTCPDevice
from pyHMI.Tag import Tag
from pyRRD_Redis import RRD_redis, StepAddFunc
from redis import StrictRedis
import time


# devices
tbx_reg1 = ModbusTCPDevice('163.111.184.147', port=502, unit_id=1, timeout=2.0, refresh=1.0)
# Reg. modbus tables
tbx_reg1.add_floats_table(20700, size=32)
# tags dict
tags = {'L1_C_WOBBE_ACT': Tag(0.0, src=tbx_reg1, ref={'type': 'float', 'addr': 20700}),
        'L1_C_WOBBE_CSR': Tag(0.0, src=tbx_reg1, ref={'type': 'float', 'addr': 20702}),
        'L1_C_PCS_ACT': Tag(0.0, src=tbx_reg1, ref={'type': 'float', 'addr': 20704}),
        'L1_C_PCS_CSR': Tag(0.0, src=tbx_reg1, ref={'type': 'float', 'addr': 20706}),
        'L1_C_DEBIT_ACT': Tag(0.0, src=tbx_reg1, ref={'type': 'float', 'addr': 20708}),
        'L1_C_DEBIT_CSR': Tag(0.0, src=tbx_reg1, ref={'type': 'float', 'addr': 20710}),
        'L1_M_WOBBE': Tag(0.0, src=tbx_reg1, ref={'type': 'float', 'addr': 20712}),
        'L1_M_PCS': Tag(0.0, src=tbx_reg1, ref={'type': 'float', 'addr': 20714}),
        'L1_M_DEBIT': Tag(0.0, src=tbx_reg1, ref={'type': 'float', 'addr': 20716}),
        'L1_OUT_REG': Tag(0.0, src=tbx_reg1, ref={'type': 'float', 'addr': 20718}),
        'L1_OUT_PID_WOBBE': Tag(0.0, src=tbx_reg1, ref={'type': 'float', 'addr': 20720}),
        'L1_OUT_PID_PCS': Tag(0.0, src=tbx_reg1, ref={'type': 'float', 'addr': 20722}),
        'L1_OUT_PID_DEBIT': Tag(0.0, src=tbx_reg1, ref={'type': 'float', 'addr': 20724})}
# populate an RRDs dict
redis_cli = StrictRedis()
rrds = {}
for key in tags:
    rrds[key] = RRD_redis('rrd:' + key, client=redis_cli, size=8640, step=10.0, add_func=StepAddFunc.last)
# wait 1s for modbus thread start
time.sleep(1.0)
# main loop
while True:
    now = time.time()
    for key in tags:
        rrds[key].add(tags[key].val, at_time=now)
    time.sleep(10.0)
