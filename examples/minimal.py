#!/usr/bin/env python3

from pyHMI.DS_ModbusTCP import ModbusTCPDevice, ModbusBool
from pyHMI.Tag import Tag
import time


# Device PLC
md = ModbusTCPDevice('localhost')
md_r_req = md.add_read_bits_request(1, 2, run_cyclic=True)
md_w_req = md.add_write_bits_request(0, 1, run_cyclic=True)

# Tags
W_BIT_0 = Tag(False, src=ModbusBool(md_w_req, 0))
R_BIT_1 = Tag(False, src=ModbusBool(md_r_req, 1))
R_BIT_2 = Tag(False, src=ModbusBool(md_r_req, 2))


# Main loop
while True:
    W_BIT_0.val = R_BIT_1.val or R_BIT_2.val
    time.sleep(1.0)
