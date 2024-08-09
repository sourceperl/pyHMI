#!/usr/bin/env python3

from pyHMI.DS_ModbusTCP import ModbusTCPDevice, ModbusBool
from pyHMI.Tag import Tag
import time


# Device PLC
md = ModbusTCPDevice('localhost', port=502)
md.add_write_bits_table(0)
md.add_read_bits_table(1, 2)
# Tags
W_BIT_0 = Tag(False, src=ModbusBool(md, address=0, write=True))
R_BIT_1 = Tag(False, src=ModbusBool(md, address=1))
R_BIT_2 = Tag(False, src=ModbusBool(md, address=2))


# Main loop
while True:
    W_BIT_0.val = R_BIT_1.val or R_BIT_2.val
    time.sleep(1.0)
