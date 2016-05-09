import threading
from pyModbusTCP.client import ModbusClient


class ModbusDevice(object):
    def __init__(self, host='localhost', port=502, unit_id=1, timeout=5.0):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.lock = threading.Lock()
        self.bits = {}
        self.words = {}
        self.connected = False
        self.poll_cycle = 0
        # privates vars
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
            with self.lock:
                tmp_w_buffer = list(self._w_buffer)
                tmp_r_buffer = list(self._r_buffer)
                self._w_buffer = []
            # do modbus write on socket
            for w in tmp_w_buffer:
                if w['type'] is 'bit':
                    self._c.write_single_coil(w['addr'], w['value'])
            # do modbus reading on socket
            for r in tmp_r_buffer:
                if r['type'] is 'bit':
                    addr = r['addr']
                    size = r['size']
                    reg_list = self._c.read_discrete_inputs(addr, size)
                    # if read is ok, store result in dict (with thread lock synchronization)
                    if reg_list:
                        with self.lock:
                            for reg in reg_list:
                                self.bits[addr] = reg
                                addr += 1
                    else:
                        with self.lock:
                            for _addr in range(addr, addr+size):
                                self.bits[_addr] = None
                elif r['type'] is 'word':
                    addr = r['addr']
                    size = r['size']
                    reg_list = self._c.read_holding_registers(addr, size)
                    # if read is ok, store result in dict (with thread lock synchronization)
                    if reg_list:
                        with self.lock:
                            for reg in reg_list:
                                self.words[addr] = reg
                                addr += 1
                    else:
                        with self.lock:
                            for _addr in range(addr, addr+size):
                                self.bits[_addr] = None
            # do stat stuff
            with self.lock:
                self.connected = self._c.is_open()
                self.poll_cycle += 1
            # 1s before next polling (or not if a write trig wait event)
            if self._wait_evt.wait(1.0):
                self._wait_evt.clear()

    def get(self, get_type, ref):
        if get_type == 'val':
            if ref['type'] == 'bit':
                return self.bits[ref['addr']]
            elif ref['type'] == 'word':
                return self.words[ref['addr']]
        elif get_type == 'err':
            if ref['type'] == 'bit':
                return self.bits[ref['addr']] is None

    def w_bit(self, addr, value):
        with self.lock:
            # don't allow write request when device is not in sync
            if self.connected:
                self._w_buffer.append({'type': 'bit', 'addr': addr, 'value': value})
                # immediate modbus refresh
                self._wait_evt.set()

    def w_bits(self, addr, value):
        _addr = addr
        for _value in value:
            self.w_bit(_addr, _value)
            _addr += 1

    def r_bits(self, addr, size=1):
        with self.lock:
            # add bit table to read buffer
            self._r_buffer.append({'type': 'bit', 'addr': addr, 'size': size})
            # init bits table with default value
            for a in range(addr, addr + size):
                self.bits[a] = False
        # immediate modbus refresh
        self._wait_evt.set()

    def r_words(self, addr, size=1):
        with self.lock:
            # add bit table to read buffer
            self._r_buffer.append({'type': 'word', 'addr': addr, 'size': size})
            # init words table with default value
            for a in range(addr, addr + size):
                self.words[a] = 0
        # immediate modbus refresh
        self._wait_evt.set()
