#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Modbus/TCP server

from pyModbusTCP.server import ModbusServer

if __name__ == '__main__':
    server = ModbusServer(host='0.0.0.0', port=502)
    server.start()

