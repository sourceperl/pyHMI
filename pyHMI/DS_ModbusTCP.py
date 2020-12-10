# -*- coding: utf-8 -*-

import threading
from pyModbusTCP.client import ModbusClient
from pyModbusTCP.utils import word_list_to_long, decode_ieee, encode_ieee, get_2comp
import time


class ModbusTCPDevice(object):
    def __init__(self, host='localhost', port=502, unit_id=1, timeout=5.0, refresh=1.0, client_adv_args=None):
        # public vars
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.refresh = refresh
        # client advenced parameters (like 'debug' = True)
        if client_adv_args is None:
            self.client_adv_args = dict()
        else:
            self.client_adv_args = client_adv_args
        # privates vars
        self._bits = {}
        self._words = {}
        self._longs = {}
        self._floats = {}
        self._connected = False
        self._poll_cycle = 0
        self._lock = threading.Lock()
        self._wait_evt = threading.Event()
        self._w_buffer = []
        self._r_buffer = []
        self._c = ModbusClient(host=self.host, port=self.port, unit_id=self.unit_id,
                               timeout=self.timeout, **self.client_adv_args)
        # start thread
        self._th = threading.Thread(target=self.polling_thread)
        self._th.daemon = True
        self._th.start()

    @property
    def connected(self):
        with self._lock:
            return self._connected

    @property
    def poll_cycle(self):
        with self._lock:
            return self._poll_cycle

    # tag_add, get, err and set are mandatory function to be a valid tag source
    def tag_add(self, tag):
        # check a table already reference the tag, raise ValueError if not
        with self._lock:
            if tag.ref['type'] == 'bit':
                if tag.ref['addr'] not in self._bits:
                    raise ValueError(
                        'Tag address %d have no bits table define on modbus host %s' % (tag.ref['addr'], self.host))
            elif tag.ref['type'] == 'word':
                if tag.ref['addr'] not in self._words:
                    raise ValueError(
                        'Tag address %d have no words table define on modbus host %s' % (tag.ref['addr'], self.host))
            elif tag.ref['type'] == 'long':
                if tag.ref['addr'] not in self._longs:
                    raise ValueError(
                        'Tag address %d have no longs table define on modbus host %s' % (tag.ref['addr'], self.host))
            elif tag.ref['type'] == 'float':
                if tag.ref['addr'] not in self._floats:
                    raise ValueError(
                        'Tag address %d have no floats table define on modbus host %s' % (tag.ref['addr'], self.host))
            elif tag.ref['type'] == 'w_bit':
                pass
            elif tag.ref['type'] == 'w_word':
                pass
            elif tag.ref['type'] == 'w_float':
                pass
            else:
                raise ValueError(
                    'Wrong tag type %s for modbus host %s' % (tag.ref['type'], self.host))

    def get(self, ref):
        if ref['type'] == 'bit':
            with self._lock:
                b = bool(self._bits[ref['addr']]['bit'])
                return not b if ref.get('not', False) else b
        elif ref['type'] == 'word':
            with self._lock:
                word = int(self._words[ref['addr']]['word'])
                if ref.get('signed', False):
                    word = get_2comp(word, val_size=16)
                return word * ref.get('span', 1) + ref.get('offset', 0)
        elif ref['type'] == 'long':
            with self._lock:
                long = int(self._longs[ref['addr']]['long'])
                if ref.get('signed', False):
                    long = get_2comp(long, val_size=32)
                return long * ref.get('span', 1) + ref.get('offset', 0)
        elif ref['type'] == 'float':
            with self._lock:
                flt = float(self._floats[ref['addr']]['float'])
                return flt * ref.get('span', 1.0) + ref.get('offset', 0.0)

    def err(self, ref):
        if ref['type'] == 'bit':
            with self._lock:
                return self._bits[ref['addr']]['err']
        elif ref['type'] == 'word':
            with self._lock:
                return self._words[ref['addr']]['err']
        elif ref['type'] == 'long':
            with self._lock:
                return self._longs[ref['addr']]['err']
        elif ref['type'] == 'float':
            with self._lock:
                return self._floats[ref['addr']]['err']

    def set(self, value, ref):
        if ref['type'] == 'w_bit':
            return self.write_bit(ref['addr'], value)
        elif ref['type'] == 'w_word':
            value = value * ref.get('span', 1) + ref.get('offset', 0)
            if ref.get('signed', False) and value < 0:
                value += 0x10000
            return self.write_word(ref['addr'], value)
        elif ref['type'] == 'w_float':
            value = value * ref.get('span', 1) + ref.get('offset', 0)
            return self.write_float(ref['addr'], value, swap_word=ref.get('swap_word', False))

    def polling_thread(self):
        # polling cycle
        while True:
            # keep socket open
            if not self._c.is_open():
                self._c.open()
            # do thread safe copy of read/write buffer for this cycle
            with self._lock:
                tmp_w_buffer = list(self._w_buffer)
                tmp_r_buffer = list(self._r_buffer)
                self._w_buffer = []
            # do modbus write on socket
            for w in tmp_w_buffer:
                # TODO improve debug system (move from com thread to main)
                str_now = time.strftime('%Y-%m-%d %H:%M:%S')
                if w['type'] is 'bit':
                    if self.debug:
                        print('%s: write single coil @%d=%d' % (str_now, w['addr'], w['value']))
                    self._c.write_single_coil(w['addr'], w['value'])
                elif w['type'] is 'word':
                    if self.debug:
                        print('%s: write single register @%d=%d' % (str_now, w['addr'], w['value']))
                    self._c.write_single_register(w['addr'], w['value'])
                elif w['type'] is 'float':
                    if self.debug:
                        print('%s: write float register @%d=%.2f' % (str_now, w['addr'], w['value']))
                    i32 = encode_ieee(w['value'])
                    (msb, lsb) = [(i32 & 0xFFFF0000) >> 16, i32 & 0xFFFF]
                    self._c.write_multiple_registers(w['addr'], [lsb, msb] if w['swap_word'] else [msb, lsb])
            # do modbus reading on socket
            for r in tmp_r_buffer:
                if r['type'] is 'bit':
                    addr = r['addr']
                    size = r['size']
                    if r['use_f1']:
                        reg_list = self._c.read_coils(addr, size)
                    else:
                        reg_list = self._c.read_discrete_inputs(addr, size)
                    # if read is ok, store result in dict (with thread _lock synchronization)
                    if reg_list:
                        with self._lock:
                            for reg in reg_list:
                                self._bits[addr]['bit'] = reg
                                self._bits[addr]['err'] = False
                                addr += 1
                    else:
                        with self._lock:
                            for _addr in range(addr, addr + size):
                                self._bits[_addr]['err'] = True
                elif r['type'] is 'word':
                    addr = r['addr']
                    size = r['size']
                    if r['use_f4']:
                        reg_list = self._c.read_input_registers(addr, size)
                    else:
                        reg_list = self._c.read_holding_registers(addr, size)
                    # if read is ok, store result in dict (with thread _lock synchronization)
                    if reg_list:
                        with self._lock:
                            for reg in reg_list:
                                self._words[addr]['word'] = reg
                                self._words[addr]['err'] = False
                                addr += 1
                    else:
                        with self._lock:
                            for _addr in range(addr, addr + size):
                                self._words[_addr]['err'] = True
                elif r['type'] is 'long':
                    addr = r['addr']
                    size = r['size']
                    if r['use_f4']:
                        reg_list = self._c.read_input_registers(addr, size * 2)
                    else:
                        reg_list = self._c.read_holding_registers(addr, size * 2)
                    # if read is ok, store result in dict (with thread _lock synchronization)
                    if reg_list:
                        with self._lock:
                            for off in range(0, size):
                                if r['swap_word']:
                                    w_list = [reg_list[off * 2 + 1], reg_list[off * 2]]
                                else:
                                    w_list = [reg_list[off * 2], reg_list[off * 2 + 1]]
                                long = word_list_to_long(w_list)[0]
                                self._longs[addr + off * 2]['long'] = long
                                self._longs[addr + off * 2]['err'] = False
                    else:
                        with self._lock:
                            for off in range(0, size):
                                self._longs[addr + off * 2]['err'] = True
                elif r['type'] is 'float':
                    addr = r['addr']
                    size = r['size']
                    if r['use_f4']:
                        reg_list = self._c.read_input_registers(addr, size * 2)
                    else:
                        reg_list = self._c.read_holding_registers(addr, size * 2)
                    # if read is ok, store result in dict (with thread _lock synchronization)
                    if reg_list:
                        with self._lock:
                            for off in range(0, size):
                                if r['swap_word']:
                                    w_list = [reg_list[off * 2 + 1], reg_list[off * 2]]
                                else:
                                    w_list = [reg_list[off * 2], reg_list[off * 2 + 1]]
                                flt = decode_ieee(word_list_to_long(w_list)[0])
                                self._floats[addr + off * 2]['float'] = flt
                                self._floats[addr + off * 2]['err'] = False
                    else:
                        with self._lock:
                            for off in range(0, size):
                                self._floats[addr + off * 2]['err'] = True
            # do stat stuff
            with self._lock:
                self._connected = self._c.is_open()
                self._poll_cycle += 1
            # wait before next polling (or not if a write trig wait event)
            if self._wait_evt.wait(self.refresh):
                self._wait_evt.clear()

    def write_bit(self, addr, value):
        with self._lock:
            # don't allow write request when device is not in sync
            if self._connected:
                self._w_buffer.append({'type': 'bit', 'addr': addr, 'value': value})
                # immediate modbus refresh
                self._wait_evt.set()
                return True
            else:
                return None

    def write_bits(self, addr, value):
        with self._lock:
            # don't allow write request when device is not in sync
            if self._connected:
                _addr = addr
                for _value in value:
                    self._w_buffer.append({'type': 'bit', 'addr': _addr, 'value': _value})
                    _addr += 1
                # immediate modbus refresh
                self._wait_evt.set()
                return True
            else:
                return None

    def write_word(self, addr, value):
        with self._lock:
            # don't allow write request when device is not in sync
            if self._connected:
                self._w_buffer.append({'type': 'word', 'addr': addr, 'value': value})
                # immediate modbus refresh
                self._wait_evt.set()
                return True
            else:
                return None

    def write_float(self, addr, value, swap_word=False):
        with self._lock:
            # don't allow write request when device is not in sync
            if self._connected:
                self._w_buffer.append({'type': 'float', 'addr': addr, 'value': value, 'swap_word': swap_word})
                # immediate modbus refresh
                self._wait_evt.set()
                return True
            else:
                return None

    def add_bits_table(self, addr, size=1, use_f1=False):
        with self._lock:
            # add bit table to read buffer
            self._r_buffer.append({'type': 'bit', 'addr': addr, 'size': size, 'use_f1': use_f1})
            # init bits table with default value
            for a in range(addr, addr + size):
                self._bits[a] = {'bit': False, 'err': True}
        # immediate modbus refresh
        self._wait_evt.set()

    def add_words_table(self, addr, size=1, use_f4=False):
        with self._lock:
            # add word table to read buffer
            self._r_buffer.append({'type': 'word', 'addr': addr, 'size': size, 'use_f4': use_f4})
            # init words table with default value
            for a in range(addr, addr + size):
                self._words[a] = {'word': 0, 'err': True}
        # immediate modbus refresh
        self._wait_evt.set()

    def add_longs_table(self, addr, size=1, use_f4=False, swap_word=False):
        with self._lock:
            # add long table to read buffer
            self._r_buffer.append({'type': 'long', 'addr': addr, 'size': size,
                                   'use_f4': use_f4, 'swap_word': swap_word})
            # init longs table with default value
            for offset in range(0, size):
                self._longs[addr + offset * 2] = {'long': 0, 'err': True}
        # immediate modbus refresh
        self._wait_evt.set()

    def add_floats_table(self, addr, size=1, use_f4=False, swap_word=False):
        with self._lock:
            # add float table to read buffer
            self._r_buffer.append({'type': 'float', 'addr': addr, 'size': size,
                                   'use_f4': use_f4, 'swap_word': swap_word})
            # init words table with default value
            for offset in range(0, size):
                self._floats[addr + offset * 2] = {'float': 0.0, 'err': True}
        # immediate modbus refresh
        self._wait_evt.set()
