from collections import defaultdict
import threading
import time
from .Tag import DS
from pyModbusTCP.client import ModbusClient
from pyModbusTCP.utils import word_list_to_long, decode_ieee, encode_ieee, get_2comp


class _LockedClient:
    """Allow thread safe access to modbus client."""

    def __init__(self, client, thread_lock):
        self._client = client
        self._thread_lock = thread_lock

    def __enter__(self):
        self._thread_lock.acquire()
        return self._client

    def __exit__(self, *args):
        self._thread_lock.release()


class ModbusTCPDevice(DS):
    def __init__(self, host='localhost', port=502, unit_id=1, timeout=5.0, refresh=1.0, debug=False,
                 client_adv_args=None):
        super().__init__()
        # public vars
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.refresh = refresh
        self.debug = debug
        # client advanced parameters (like 'debug' = True)
        if client_adv_args is None:
            self.client_adv_args = dict()
        else:
            self.client_adv_args = client_adv_args
        # privates vars
        self._rdb_bits = defaultdict(dict)
        self._rdb_words = defaultdict(dict)
        self._rdb_longs = defaultdict(dict)
        self._rdb_floats = defaultdict(dict)
        self._wdb_bits = defaultdict(dict)
        self._wdb_words = defaultdict(dict)
        self._wdb_floats = defaultdict(dict)
        self._connected = False
        self._poll_cycle = 0
        self._thread_lock = threading.Lock()
        self._wait_evt = threading.Event()
        self._w_scheduled_l = []
        self._r_scheduled_l = []
        self._c = ModbusClient(host=self.host, port=self.port, unit_id=self.unit_id,
                               timeout=self.timeout, auto_open=True, **self.client_adv_args)
        # allow thread safe access to modbus client (allow direct blocking IO on modbus socket)
        self.locked_client = _LockedClient(self._c, self._thread_lock)
        # start thread
        self._th = threading.Thread(target=self.polling_thread)
        self._th.daemon = True
        self._th.start()

    def __repr__(self):
        return 'ModbusTCPDevice(host=%s, port=%i, unit_id=%i, timeout=%.1f, refresh=%.1f,  client_adv_args=%s)' \
               % (self.host, self.port, self.unit_id, self.timeout, self.refresh, self.client_adv_args)

    @property
    def connected(self):
        with self._thread_lock:
            return self._connected

    @property
    def poll_cycle(self):
        with self._thread_lock:
            return self._poll_cycle

    # tag_add, get, err and set are mandatory function to be a valid tag source
    def tag_add(self, tag):
        # check a table already reference the tag, raise ValueError if not
        with self._thread_lock:
            if tag.ref['type'] == 'bit':
                if tag.ref['addr'] not in self._rdb_bits:
                    raise ValueError('Tag address %d have no bits table define on modbus host %s'
                                     % (tag.ref['addr'], self.host))
            elif tag.ref['type'] == 'word':
                if tag.ref['addr'] not in self._rdb_words:
                    raise ValueError('Tag address %d have no words table define on modbus host %s'
                                     % (tag.ref['addr'], self.host))
            elif tag.ref['type'] == 'long':
                if tag.ref['addr'] not in self._rdb_longs:
                    raise ValueError('Tag address %d have no longs table define on modbus host %s'
                                     % (tag.ref['addr'], self.host))
            elif tag.ref['type'] == 'float':
                if tag.ref['addr'] not in self._rdb_floats:
                    raise ValueError('Tag address %d have no floats table define on modbus host %s'
                                     % (tag.ref['addr'], self.host))
            elif tag.ref['type'] == 'w_bit':
                pass
            elif tag.ref['type'] == 'w_word':
                pass
            elif tag.ref['type'] == 'w_float':
                pass
            else:
                raise ValueError('Wrong tag type %s for modbus host %s' % (tag.ref['type'], self.host))

    def get(self, ref):
        try:
            with self._thread_lock:
                if ref['type'] == 'bit':
                    b = bool(self._rdb_bits[ref['addr']]['bit'])
                    return not b if ref.get('not', False) else b
                elif ref['type'] == 'word':
                    word = int(self._rdb_words[ref['addr']]['word'])
                    if ref.get('signed', False):
                        word = get_2comp(word, val_size=16)
                    return word * ref.get('span', 1) + ref.get('offset', 0)
                elif ref['type'] == 'long':
                    long = int(self._rdb_longs[ref['addr']]['long'])
                    if ref.get('signed', False):
                        long = get_2comp(long, val_size=32)
                    return long * ref.get('span', 1) + ref.get('offset', 0)
                elif ref['type'] == 'float':
                    flt = float(self._rdb_floats[ref['addr']]['float'])
                    return flt * ref.get('span', 1.0) + ref.get('offset', 0.0)
                elif ref['type'] == 'w_bit':
                    return self._wdb_bits[ref['addr']]['w_value']
                elif ref['type'] == 'w_word':
                    return self._wdb_words[ref['addr']]['w_value']
                elif ref['type'] == 'w_float':
                    return self._wdb_floats[ref['addr']]['w_value']
                else:
                    return
        except KeyError:
            return

    def err(self, ref):
        try:
            with self._thread_lock:
                if ref['type'] == 'bit':
                    return self._rdb_bits[ref['addr']]['err']
                elif ref['type'] == 'word':
                    return self._rdb_words[ref['addr']]['err']
                elif ref['type'] == 'long':
                    return self._rdb_longs[ref['addr']]['err']
                elif ref['type'] == 'float':
                    return self._rdb_floats[ref['addr']]['err']
                elif ref['type'] == 'w_bit':
                    return self._wdb_bits[ref['addr']]['err']
                elif ref['type'] == 'w_word':
                    return self._wdb_words[ref['addr']]['err']
                elif ref['type'] == 'w_float':
                    return self._wdb_floats[ref['addr']]['err']
                else:
                    return
        except KeyError:
            return

    def set(self, ref, value):
        if ref['type'] == 'w_bit':
            self.write_bit(ref['addr'], value)
            return True
        elif ref['type'] == 'w_word':
            value = value * ref.get('span', 1) + ref.get('offset', 0)
            if ref.get('signed', False) and value < 0:
                value += 0x10000
            self.write_word(ref['addr'], value)
            return True
        elif ref['type'] == 'w_float':
            value = value * ref.get('span', 1) + ref.get('offset', 0)
            self.write_float(ref['addr'], value, swap_word=ref.get('swap_word', False))
            return True
        else:
            return False

    def polling_thread(self):
        # polling cycle
        while True:
            # do thread safe copy of read/write buffer for this cycle
            with self._thread_lock:
                copy_w_scheduled_l = list(self._w_scheduled_l)
                copy_r_scheduled_l = list(self._r_scheduled_l)
                self._w_scheduled_l = []
            # do modbus write on socket
            for w_sched in copy_w_scheduled_l:
                # TODO improve debug system (move from com thread to main)
                str_now = time.strftime('%Y-%m-%d %H:%M:%S')
                if w_sched['type'] == 'bit':
                    if self.debug:
                        print('%s: write single coil @%d=%d' % (str_now, w_sched['addr'], w_sched['value']))
                    write_ok = self._c.write_single_coil(w_sched['addr'], w_sched['value'])
                    # update write DB with status
                    with self._thread_lock:
                        self._wdb_bits[w_sched['addr']]['w_value'] = w_sched['value']
                        self._wdb_bits[w_sched['addr']]['err'] = not write_ok
                elif w_sched['type'] == 'word':
                    if self.debug:
                        print('%s: write single register @%d=%d' % (str_now, w_sched['addr'], w_sched['value']))
                    write_ok = self._c.write_single_register(w_sched['addr'], w_sched['value'])
                    # update write DB with status
                    with self._thread_lock:
                        self._wdb_words[w_sched['addr']]['w_value'] = w_sched['value']
                        self._wdb_words[w_sched['addr']]['err'] = not write_ok
                elif w_sched['type'] == 'float':
                    if self.debug:
                        print('%s: write float register @%d=%.2f' % (str_now, w_sched['addr'], w_sched['value']))
                    i32 = encode_ieee(w_sched['value'])
                    (msb, lsb) = [(i32 & 0xFFFF0000) >> 16, i32 & 0xFFFF]
                    write_ok = self._c.write_multiple_registers(
                        w_sched['addr'], [lsb, msb] if w_sched['swap_word'] else [msb, lsb])
                    # update write DB with status
                    with self._thread_lock:
                        self._wdb_floats[w_sched['addr']]['w_value'] = w_sched['value']
                        self._wdb_floats[w_sched['addr']]['err'] = not write_ok
            # do modbus reading on socket
            for r in copy_r_scheduled_l:
                if r['type'] == 'bit':
                    addr = r['addr']
                    size = r['size']
                    if r['use_f2']:
                        reg_list = self._c.read_discrete_inputs(addr, size)
                    else:
                        reg_list = self._c.read_coils(addr, size)
                    # if read is ok, store result in dict (with thread _lock synchronization)
                    if reg_list:
                        with self._thread_lock:
                            for reg in reg_list:
                                self._rdb_bits[addr]['bit'] = reg
                                self._rdb_bits[addr]['err'] = False
                                addr += 1
                    else:
                        with self._thread_lock:
                            for _addr in range(addr, addr + size):
                                self._rdb_bits[_addr]['err'] = True
                elif r['type'] == 'word':
                    addr = r['addr']
                    size = r['size']
                    if r['use_f4']:
                        reg_list = self._c.read_input_registers(addr, size)
                    else:
                        reg_list = self._c.read_holding_registers(addr, size)
                    # if read is ok, store result in dict (with thread _lock synchronization)
                    if reg_list:
                        with self._thread_lock:
                            for reg in reg_list:
                                self._rdb_words[addr]['word'] = reg
                                self._rdb_words[addr]['err'] = False
                                addr += 1
                    else:
                        with self._thread_lock:
                            for _addr in range(addr, addr + size):
                                self._rdb_words[_addr]['err'] = True
                elif r['type'] == 'long':
                    addr = r['addr']
                    size = r['size']
                    if r['use_f4']:
                        reg_list = self._c.read_input_registers(addr, size * 2)
                    else:
                        reg_list = self._c.read_holding_registers(addr, size * 2)
                    # if read is ok, store result in dict (with thread _lock synchronization)
                    if reg_list:
                        with self._thread_lock:
                            for off in range(0, size):
                                if r['swap_word']:
                                    w_list = [reg_list[off * 2 + 1], reg_list[off * 2]]
                                else:
                                    w_list = [reg_list[off * 2], reg_list[off * 2 + 1]]
                                long = word_list_to_long(w_list)[0]
                                self._rdb_longs[addr + off * 2]['long'] = long
                                self._rdb_longs[addr + off * 2]['err'] = False
                    else:
                        with self._thread_lock:
                            for off in range(0, size):
                                self._rdb_longs[addr + off * 2]['err'] = True
                elif r['type'] == 'float':
                    addr = r['addr']
                    size = r['size']
                    if r['use_f4']:
                        reg_list = self._c.read_input_registers(addr, size * 2)
                    else:
                        reg_list = self._c.read_holding_registers(addr, size * 2)
                    # if read is ok, store result in dict (with thread _lock synchronization)
                    if reg_list:
                        with self._thread_lock:
                            for off in range(0, size):
                                if r['swap_word']:
                                    w_list = [reg_list[off * 2 + 1], reg_list[off * 2]]
                                else:
                                    w_list = [reg_list[off * 2], reg_list[off * 2 + 1]]
                                flt = decode_ieee(word_list_to_long(w_list)[0])
                                self._rdb_floats[addr + off * 2]['float'] = flt
                                self._rdb_floats[addr + off * 2]['err'] = False
                    else:
                        with self._thread_lock:
                            for off in range(0, size):
                                self._rdb_floats[addr + off * 2]['err'] = True
            # do stat stuff
            with self._thread_lock:
                self._connected = self._c.is_open
                self._poll_cycle += 1
            # wait before next polling (or not if a write trig the wait event)
            if self._wait_evt.wait(self.refresh):
                self._wait_evt.clear()

    def write_bit(self, addr, value):
        with self._thread_lock:
            # schedules the write operation
            self._w_scheduled_l.append({'type': 'bit', 'addr': addr, 'value': value})
        # immediate refresh of polling thread
        self._wait_evt.set()

    def write_word(self, addr, value):
        with self._thread_lock:
            # schedules the write operation
            self._w_scheduled_l.append({'type': 'word', 'addr': addr, 'value': value})
        # immediate refresh of polling thread
        self._wait_evt.set()

    def write_float(self, addr, value, swap_word=False):
        with self._thread_lock:
            # schedules the write operation
            self._w_scheduled_l.append({'type': 'float', 'addr': addr, 'value': value, 'swap_word': swap_word})
        # immediate refresh of polling thread
        self._wait_evt.set()

    def add_bits_table(self, addr, size=1, use_f2=False):
        with self._thread_lock:
            # init bits table with default value
            for a in range(addr, addr + size):
                self._rdb_bits[a] = {'bit': False, 'err': True}
            # add bit table to read buffer
            self._r_scheduled_l.append({'type': 'bit', 'addr': addr, 'size': size, 'use_f2': use_f2})
        # immediate modbus refresh
        self._wait_evt.set()

    def add_words_table(self, addr, size=1, use_f4=False):
        with self._thread_lock:
            # init words table with default value
            for a in range(addr, addr + size):
                self._rdb_words[a] = {'word': 0, 'err': True}
            # add word table to read buffer
            self._r_scheduled_l.append({'type': 'word', 'addr': addr, 'size': size, 'use_f4': use_f4})
        # immediate modbus refresh
        self._wait_evt.set()

    def add_longs_table(self, addr, size=1, use_f4=False, swap_word=False):
        with self._thread_lock:
            # init longs table with default value
            for offset in range(0, size):
                self._rdb_longs[addr + offset * 2] = {'long': 0, 'err': True}
            # add long table to read buffer
            self._r_scheduled_l.append({'type': 'long', 'addr': addr, 'size': size,
                                        'use_f4': use_f4, 'swap_word': swap_word})
        # immediate modbus refresh
        self._wait_evt.set()

    def add_floats_table(self, addr, size=1, use_f4=False, swap_word=False):
        with self._thread_lock:
            # init words table with default value
            for offset in range(0, size):
                self._rdb_floats[addr + offset * 2] = {'float': 0.0, 'err': True}
            # add float table to read buffer
            self._r_scheduled_l.append({'type': 'float', 'addr': addr, 'size': size,
                                        'use_f4': use_f4, 'swap_word': swap_word})
        # immediate modbus refresh
        self._wait_evt.set()
