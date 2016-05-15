# -*- coding: utf-8 -*-

import threading
from pyModbusTCP.client import ModbusClient
from pyModbusTCP.utils import word_list_to_long, decode_ieee
import time


class ModbusTCPDevice(object):
    def __init__(self, host='localhost', port=502, unit_id=1, timeout=5.0, refresh=1.0):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.refresh = refresh
        # privates vars
        self._bits = {}
        self._words = {}
        self._floats = {}
        self._connected = False
        self._poll_cycle = 0
        self._lock = threading.Lock()
        self._wait_evt = threading.Event()
        self._w_buffer = []
        self._r_buffer = []
        self._c = ModbusClient(host=self.host, port=self.port, unit_id=self.unit_id,
                               timeout=self.timeout, auto_open=True)
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
        # modbus read value start with tag error flag set
        if any(tag.ref['type'] in s for s in ('bit', 'word', 'float')):
            tag.err = True
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
            elif tag.ref['type'] == 'float':
                if tag.ref['addr'] not in self._floats:
                    raise ValueError(
                        'Tag address %d have no floats table define on modbus host %s' % (tag.ref['addr'], self.host))

    def get(self, ref):
        if ref['type'] == 'bit':
            with self._lock:
                b = bool(self._bits[ref['addr']]['bit'])
                return not b if ref.get('not', False) else b
        elif ref['type'] == 'word':
            with self._lock:
                word = int(self._words[ref['addr']]['word'])
                return word * ref.get('span', 1) + ref.get('offset', 0)
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
        elif ref['type'] == 'float':
            with self._lock:
                return self._floats[ref['addr']]['err']

    def set(self, value, ref):
        if ref['type'] == 'w_bit':
            return self.write_bit(ref['addr'], value)
        elif ref['type'] == 'w_word':
            return self.write_word(ref['addr'] * ref.get('span', 1) + ref.get('offset', 0), value)
            # elif ref['type'] == 'w_float':
            #     return self.write_float(ref['addr'] * ref.get('span', 1) + ref.get('offset', 0), value)

    def polling_thread(self):
        # polling cycle
        while True:
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
                    print('%s: write single coil @%d=%d' % (str_now, w['addr'], w['value']))
                    self._c.write_single_coil(w['addr'], w['value'])
                elif w['type'] is 'word':
                    print('%s: write single register @%d=%d' % (str_now, w['addr'], w['value']))
                    self._c.write_single_register(w['addr'], w['value'])
            # do modbus reading on socket
            for r in tmp_r_buffer:
                if r['type'] is 'bit':
                    addr = r['addr']
                    size = r['size']
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
                elif r['type'] is 'float':
                    addr = r['addr']
                    size = r['size']
                    reg_list = self._c.read_holding_registers(addr, size * 2)
                    # if read is ok, store result in dict (with thread _lock synchronization)
                    if reg_list:
                        with self._lock:
                            for off in range(0, size):
                                flt = decode_ieee(word_list_to_long([reg_list[off * 2], reg_list[off * 2 + 1]])[0])
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
            # 1s before next polling (or not if a write trig wait event)
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

    def add_bits_table(self, addr, size=1):
        with self._lock:
            # add bit table to read buffer
            self._r_buffer.append({'type': 'bit', 'addr': addr, 'size': size})
            # init bits table with default value
            for a in range(addr, addr + size):
                self._bits[a] = {'bit': False, 'err': True}
        # immediate modbus refresh
        self._wait_evt.set()

    def add_words_table(self, addr, size=1):
        with self._lock:
            # add bit table to read buffer
            self._r_buffer.append({'type': 'word', 'addr': addr, 'size': size})
            # init words table with default value
            for a in range(addr, addr + size):
                self._words[a] = {'word': 0, 'err': True}
        # immediate modbus refresh
        self._wait_evt.set()

    def add_floats_table(self, addr, size=1):
        with self._lock:
            # add bit table to read buffer
            self._r_buffer.append({'type': 'float', 'addr': addr, 'size': size})
            # init words table with default value
            for offset in range(0, size):
                self._floats[addr + offset * 2] = {'float': 0.0, 'err': True}
        # immediate modbus refresh
        self._wait_evt.set()
