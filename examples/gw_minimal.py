#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyHMI.DS_ModbusTCP import ModbusTCPDevice
from pyHMI.Tag import Tag
import time


# Device PLC
plc = ModbusTCPDevice('localhost', port=502, timeout=2.0, refresh=1.0)
plc.add_read_bits_table(0, 4)
# Tags
BIT_0 = Tag(False, src=plc, ref={'type': 'bit', 'addr': 0})
BIT_1 = Tag(False, src=plc, ref={'type': 'bit', 'addr': 1})
BIT_2 = Tag(False, src=plc, ref={'type': 'bit', 'addr': 2})
BIT_3 = Tag(False, src=plc, ref={'type': 'bit', 'addr': 3})
W_BIT_0 = Tag(False, src=plc, ref={'type': 'w_bit', 'addr': 0})
W_BIT_1 = Tag(False, src=plc, ref={'type': 'w_bit', 'addr': 1})
W_BIT_2 = Tag(False, src=plc, ref={'type': 'w_bit', 'addr': 2})
W_BIT_3 = Tag(False, src=plc, ref={'type': 'w_bit', 'addr': 3})

# Main loop
while True:
    W_BIT_0.val = BIT_2.val ^ BIT_3.val
    time.sleep(1.0)

