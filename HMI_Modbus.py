import threading
from pyModbusTCP.client import ModbusClient
from pyModbusTCP.utils import word_list_to_long, decode_ieee
import time


class ModbusDevice(object):
    def __init__(self, host='localhost', port=502, unit_id=1, timeout=5.0):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.bits = {}
        self.words = {}
        self.floats = {}
        self.connected = False
        self.poll_cycle = 0
        # privates vars
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
                str_now = time.strftime('%Y-%m-%d %H:%M:%S %z')
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
                                self.bits[addr] = reg
                                addr += 1
                    else:
                        with self._lock:
                            for _addr in range(addr, addr + size):
                                self.bits[_addr] = None
                elif r['type'] is 'word':
                    addr = r['addr']
                    size = r['size']
                    reg_list = self._c.read_holding_registers(addr, size)
                    # if read is ok, store result in dict (with thread _lock synchronization)
                    if reg_list:
                        with self._lock:
                            for reg in reg_list:
                                self.words[addr] = reg
                                addr += 1
                    else:
                        with self._lock:
                            for _addr in range(addr, addr + size):
                                self.bits[_addr] = None
                elif r['type'] is 'float':
                    addr = r['addr']
                    size = r['size']
                    reg_list = self._c.read_holding_registers(addr, size*2)
                    # if read is ok, store result in dict (with thread _lock synchronization)
                    if reg_list:
                        with self._lock:
                            for off in range(0, size):
                                self.floats[addr+off*2] = decode_ieee(word_list_to_long([reg_list[off*2],
                                                                                         reg_list[off*2+1]])[0])
                    else:
                        with self._lock:
                            for off in range(0, size):
                                self.floats[addr+off*2] = None
            # do stat stuff
            with self._lock:
                self.connected = self._c.is_open()
                self.poll_cycle += 1
            # 1s before next polling (or not if a write trig wait event)
            if self._wait_evt.wait(1.0):
                self._wait_evt.clear()

    def get(self, get_type, ref):
        if get_type == 'val':
            if ref['type'] == 'bit':
                with self._lock:
                    return self.bits[ref['addr']] if ref.get('not', False) == False else not self.bits[ref['addr']]
            elif ref['type'] == 'word':
                with self._lock:
                    return self.words[ref['addr']]
            elif ref['type'] == 'float':
                with self._lock:
                    return self.floats[ref['addr']]
        elif get_type == 'err':
            if ref['type'] == 'bit':
                with self._lock:
                    return self.bits[ref['addr']] is None
            elif ref['type'] == 'word':
                with self._lock:
                    return self.words[ref['addr']] is None
            elif ref['type'] == 'float':
                with self._lock:
                    return self.floats[ref['addr']] is None

    def set(self, value, ref):
        if ref['type'] == 'w_bit':
            return self.write_bit(ref['addr'], value)
        elif ref['type'] == 'word':
            return self.write_word(ref['addr'], value)

    def write_bit(self, addr, value):
        with self._lock:
            # don't allow write request when device is not in sync
            if self.connected:
                self._w_buffer.append({'type': 'bit', 'addr': addr, 'value': value})
                # immediate modbus refresh
                self._wait_evt.set()
                return True
            else:
                return None

    def write_bits(self, addr, value):
        _addr = addr
        for _value in value:
            self.write_bit(_addr, _value)
            _addr += 1

    def write_word(self, addr, value):
        with self._lock:
            # don't allow write request when device is not in sync
            if self.connected:
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
                self.bits[a] = False
        # immediate modbus refresh
        self._wait_evt.set()

    def add_words_table(self, addr, size=1):
        with self._lock:
            # add bit table to read buffer
            self._r_buffer.append({'type': 'word', 'addr': addr, 'size': size})
            # init words table with default value
            for a in range(addr, addr + size):
                self.words[a] = 0
        # immediate modbus refresh
        self._wait_evt.set()

    def add_floats_table(self, addr, size=1):
        with self._lock:
            # add bit table to read buffer
            self._r_buffer.append({'type': 'float', 'addr': addr, 'size': size})
            # init words table with default value
            for offset in range(0, size):
                self.floats[addr+offset*2] = 0.0
        # immediate modbus refresh
        self._wait_evt.set()
