#!/usr/bin/env python3

import time

from pyHMI.DS_ModbusTCP import ModbusBool, ModbusTCPDevice
from pyHMI.Tag import Tag

# Device PLC
md = ModbusTCPDevice('localhost', port=502, refresh=0.5)
md_read_req = md.add_read_bits_request(1, 2, cyclic=True)
md_write_req = md.add_write_bits_request(0, cyclic=True)
# Tags
W_BIT_0 = Tag(False, src=ModbusBool(md_write_req, address=0))
R_BIT_1 = Tag(False, src=ModbusBool(md_read_req, address=1))
R_BIT_2 = Tag(False, src=ModbusBool(md_read_req, address=2))


# Main loop
while True:
    W_BIT_0.value = R_BIT_1.value or R_BIT_2.value
    time.sleep(1.0)
