#!/usr/bin/env python2

# install pymodbus : sudo apt-get install pymodbus

from pymodbus.server.async import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
import logging

# setup logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# build 2 datastore for bits and words spaces, populate with 0
bits = ModbusSequentialDataBlock(0x00, [0] * 0xffff)
words = ModbusSequentialDataBlock(0x00, [0] * 0xffff)

# setup server
store = ModbusSlaveContext(di=bits, co=bits, hr=words, ir=words)
context = ModbusServerContext(slaves=store, single=True)

# start server
StartTcpServer(context, address=('0.0.0.0', 502))

