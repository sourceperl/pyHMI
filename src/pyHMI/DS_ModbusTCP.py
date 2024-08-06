from collections import defaultdict
import threading
import time
from typing import Any, Optional, Union
from pyModbusTCP.client import ModbusClient
from pyModbusTCP.utils import word_list_to_long, decode_ieee, encode_ieee, get_2comp
from pyHMI.Tag import Tag
from . import logger
from .Tag import DataSource, Device
from .Misc import SafeObject

# 4 address spaces :
#   - coils (0x01)
#       Read Coils 1
#       Write Single Coil 5	
#       Write Multiple Coils 15
#
#   - discrete inputs (0x2) read-only
#       Read Input Registers 4
#
#   - input registers (0x03)
#       Read Multiple Holding Registers 3	
#       Write Single Holding Register 6	
#       Write Multiple Holding Registers 16
#
#   - holding registers (0x04) read-only
#       Read Input Registers 4


class ModbusCoils(DataSource):
    def __init__(self, device: "ModbusTCPDevice", address: int, write: bool = False) -> None:
        # args
        self.device = device
        self.address = address
        self.write = write
        # check table at device level
        with self.device._r_coils_d as d:
            if self.address not in d:
                raise ValueError(f'bits @{self.address} have no table define on {self.device}')

    def __repr__(self):
        return f'ModbusBit(device={self.device!r}, address={self.address}, write={self.write})'

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if type(tag.first_value) is not bool:
            logger.warning(msg=f'first_value type should be bool in {tag}')

    def get(self) -> Optional[bool]:
        # check write-only
        if self.write:
            raise ValueError(f'cannot read write-only {self!r}')
        #
        with self.device._r_coils_d as d:
            return bool(d[self.address]['bit'])

    def set(self, value: bool) -> None:
        # check read-only
        if not self.write:
            raise ValueError(f'cannot write read-only {self!r}')
        #
        self.device.write_bit(self.address, value)

    def error(self) -> bool:
        """ Method call by Tag class to retrieve error status from datasource. """
        with self.device._r_coils_d as d:
            return bool(d[self.address]['err'])

        # read
        # try:
        #         elif self.type == 'word':
        #             word = int(self._rdb_words[ref['addr']]['word'])
        #             if ref.get('signed'):
        #                 word = get_2comp(word, val_size=16)
        #             return word
        #         elif self.type == 'long':
        #             long = int(self._rdb_longs[ref['addr']]['long'])
        #             if ref.get('signed'):
        #                 long = get_2comp(long, val_size=32)
        #             return long
        #         elif self.type == 'float':
        #             flt = float(self._rdb_floats[ref['addr']]['float'])
        #             return flt
        #         elif self.type == 'w_bit':
        #             return self._wdb_bits[ref['addr']]['w_value']
        #         elif self.type == 'w_word':
        #             return self._wdb_words[ref['addr']]['w_value']
        #         elif self.type == 'w_float':
        #             return self._wdb_floats[ref['addr']]['w_value']
        #         else:
        #             return
        # except KeyError:
        #     return

        # write
        # elif ref['type'] == 'w_word':
        #     if ref.get('signed', False) and value < 0:
        #         value += 0x10000
        #     self.write_word(ref['addr'], value)

        # elif ref['type'] == 'w_float':
        #     self.write_float(ref['addr'], value, swap_word=ref.get('swap_word', False))

        #         elif ref['type'] == 'word':
        #             return self._rdb_words[ref['addr']]['err']

        #         elif ref['type'] == 'long':
        #             return self._rdb_longs[ref['addr']]['err']

        #         elif ref['type'] == 'float':
        #             return self._rdb_floats[ref['addr']]['err']

        #         elif ref['type'] == 'w_bit':
        #             return self._wdb_bits[ref['addr']]['err']

        #         elif ref['type'] == 'w_word':
        #             return self._wdb_words[ref['addr']]['err']

        #         elif ref['type'] == 'w_float':
        #             return self._wdb_floats[ref['addr']]['err']


class ModbusTCPDevice(Device):
    def __init__(self, host='localhost', port=502, unit_id=1, timeout=5.0, refresh=1.0,
                 client_adv_args: Optional[dict] = None):
        super().__init__()
        # public vars
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.refresh = refresh
        self.client_adv_args = client_adv_args
        # privates vars
        self._r_coils_d = SafeObject(defaultdict(dict))
        self._r_words_d = defaultdict(dict)
        self._r_longs_d = defaultdict(dict)
        self._r_floats_d = defaultdict(dict)
        self._w_bits_d = defaultdict(dict)
        self._w_words_d = defaultdict(dict)
        self._w_floats_d = defaultdict(dict)
        self._read_requests_l = SafeObject(list())
        self._write_requests_l = SafeObject(list())
        self._thread_lock = threading.Lock()
        self._write_io_evt = threading.Event()
        # allow thread safe access to modbus client (allow direct blocking IO on modbus socket)
        args_d = {} if self.client_adv_args is None else self.client_adv_args
        self.safe_cli = SafeObject(ModbusClient(host=self.host, port=self.port, unit_id=self.unit_id,
                                                timeout=self.timeout, auto_open=True, **args_d))
        # start threads
        self._read_io_th = threading.Thread(target=self._read_io_thread, daemon=True)
        self._write_io_th = threading.Thread(target=self._write_io_thread, daemon=True)
        self._read_io_th.start()
        self._write_io_th.start()

    def __repr__(self):
        return f'ModbusTCPDevice(host={self.host!r}, port={self.port}, unit_id={self.unit_id}, '\
               f'timeout={self.timeout:.1f}, refresh={self.refresh:.1f}, client_adv_args={self.client_adv_args!r})'

    @property
    def connected(self):
        with self.safe_cli as cli:
            return cli.is_open

    def _read_io_thread(self):
        """ Process every read I/O. """
        while True:
            # do thread safe copy of read/write buffer for this cycle
            with self._read_requests_l as l:
                copy_read_table_l = l.copy()
            # read
            for r_table_d in copy_read_table_l:
                if r_table_d['type'] == 'bit':
                    addr = r_table_d['addr']
                    size = r_table_d['size']
                    if r_table_d['use_f2']:
                        with self.safe_cli as cli:
                            reg_list = cli.read_discrete_inputs(addr, size)
                    else:
                        with self.safe_cli as cli:
                            reg_list = cli.read_coils(addr, size)
                    # if read is ok, store result in dict (with thread _lock synchronization)
                    if reg_list:
                        for offset, reg in enumerate(reg_list):
                            with self._r_coils_d as d:
                                d[addr+offset]['bit'] = reg
                                d[addr+offset]['err'] = False
                    else:
                        with self._r_coils_d as d:
                            for iter_addr in range(addr, addr + size):
                                d[iter_addr]['err'] = True
                elif r_table_d['type'] == 'word':
                    addr = r_table_d['addr']
                    size = r_table_d['size']
                    if r_table_d['use_f4']:
                        with self.safe_cli as cli:
                            reg_list = cli.read_input_registers(addr, size)
                    else:
                        with self.safe_cli as cli:
                            reg_list = cli.read_holding_registers(addr, size)
                    # if read is ok, store result in dict (with thread _lock synchronization)
                    if reg_list:
                        with self._thread_lock:
                            for reg in reg_list:
                                self._r_words_d[addr]['word'] = reg
                                self._r_words_d[addr]['err'] = False
                                addr += 1
                    else:
                        with self._thread_lock:
                            for _addr in range(addr, addr + size):
                                self._r_words_d[_addr]['err'] = True
                elif r_table_d['type'] == 'long':
                    addr = r_table_d['addr']
                    size = r_table_d['size']
                    if r_table_d['use_f4']:
                        with self.safe_cli as cli:
                            reg_list = cli.read_input_registers(addr, size * 2)
                    else:
                        with self.safe_cli as cli:
                            reg_list = cli.read_holding_registers(addr, size * 2)
                    # if read is ok, store result in dict (with thread _lock synchronization)
                    if reg_list:
                        with self._thread_lock:
                            for off in range(0, size):
                                if r_table_d['swap_word']:
                                    w_list = [reg_list[off * 2 + 1], reg_list[off * 2]]
                                else:
                                    w_list = [reg_list[off * 2], reg_list[off * 2 + 1]]
                                long = word_list_to_long(w_list)[0]
                                self._r_longs_d[addr + off * 2]['long'] = long
                                self._r_longs_d[addr + off * 2]['err'] = False
                    else:
                        with self._thread_lock:
                            for off in range(0, size):
                                self._r_longs_d[addr + off * 2]['err'] = True
                elif r_table_d['type'] == 'float':
                    addr = r_table_d['addr']
                    size = r_table_d['size']
                    if r_table_d['use_f4']:
                        with self.safe_cli as cli:
                            reg_list = cli.read_input_registers(addr, size * 2)
                    else:
                        with self.safe_cli as cli:
                            reg_list = cli.read_holding_registers(addr, size * 2)
                    # if read is ok, store result in dict (with thread _lock synchronization)
                    if reg_list:
                        with self._thread_lock:
                            for off in range(0, size):
                                if r_table_d['swap_word']:
                                    w_list = [reg_list[off * 2 + 1], reg_list[off * 2]]
                                else:
                                    w_list = [reg_list[off * 2], reg_list[off * 2 + 1]]
                                flt = decode_ieee(word_list_to_long(w_list)[0])
                                self._r_floats_d[addr + off * 2]['float'] = flt
                                self._r_floats_d[addr + off * 2]['err'] = False
                    else:
                        with self._thread_lock:
                            for off in range(0, size):
                                self._r_floats_d[addr + off * 2]['err'] = True
            # wait before next polling
            time.sleep(self.refresh)

    def _write_io_thread(self):
        """ Process every write I/O. """
        while True:
            # do thread safe copy of read/write buffer for this cycle
            with self._write_requests_l as l:
                copy_write_requests_l = l.copy()
                l.clear()
            # write
            for req_d in copy_write_requests_l:
                if req_d['type'] == 'bit':
                    logger.debug(f"write single coil @{req_d['addr']}={req_d['value']}")
                    with self.safe_cli as cli:
                        write_ok = cli.write_single_coil(req_d['addr'], req_d['value'])
                    # update write DB with status
                    with self._thread_lock:
                        self._w_bits_d[req_d['addr']]['w_value'] = req_d['value']
                        self._w_bits_d[req_d['addr']]['err'] = not write_ok
                elif req_d['type'] == 'word':
                    logger.debug(f"write single register @{req_d['addr']}={req_d['value']}")
                    with self.safe_cli as cli:
                        write_ok = cli.write_single_register(req_d['addr'], req_d['value'])
                    # update write DB with status
                    with self._thread_lock:
                        self._w_words_d[req_d['addr']]['w_value'] = req_d['value']
                        self._w_words_d[req_d['addr']]['err'] = not write_ok
                elif req_d['type'] == 'float':
                    logger.debug(f"write float register @{req_d['addr']}={req_d['value']}")
                    i32 = encode_ieee(req_d['value'])
                    (msb, lsb) = [(i32 & 0xFFFF0000) >> 16, i32 & 0xFFFF]
                    with self.safe_cli as cli:
                        write_ok = cli.write_multiple_registers(
                            req_d['addr'], [lsb, msb] if req_d['swap_word'] else [msb, lsb])
                    # update write DB with status
                    with self._thread_lock:
                        self._w_floats_d[req_d['addr']]['w_value'] = req_d['value']
                        self._w_floats_d[req_d['addr']]['err'] = not write_ok
            # wait before next polling (or not if a write trig the wait event)
            if self._write_io_evt.wait(timeout=self.refresh):
                self._write_io_evt.clear()

    def write_bit(self, addr: int, value: bool):
        # schedules the write operation
        with self._write_requests_l as l:
            l.append({'type': 'bit', 'addr': addr, 'value': value})
        # immediate refresh of polling thread
        self._write_io_evt.set()

    def write_word(self, addr: int, value: int):
        # schedules the write operation
        with self._write_requests_l as l:
            l.append({'type': 'word', 'addr': addr, 'value': value})
        # immediate refresh of polling thread
        self._write_io_evt.set()

    def write_float(self, addr: int, value: float, swap_word: bool = False):
        # schedules the write operation
        with self._write_requests_l as l:
            l.append({'type': 'float', 'addr': addr, 'value': value, 'swap_word': swap_word})
        # immediate refresh of polling thread
        self._write_io_evt.set()

    def add_bits_table(self, addr: int, size: int = 1, use_f2: bool = False):
        # init bits table with default value
        with self._r_coils_d as d:
            for iter_addr in range(addr, addr + size):
                d[iter_addr] = {'bit': False, 'err': True}
        with self._read_requests_l as l:
            # add bit table to read buffer
            l.append({'type': 'bit', 'addr': addr, 'size': size, 'use_f2': use_f2})
        # immediate modbus refresh
        self._write_io_evt.set()

    def add_words_table(self, addr: int, size: int = 1, use_f4: bool = False):
        # init words table with default value
        with self._thread_lock:
            for a in range(addr, addr + size):
                self._r_words_d[a] = {'word': 0, 'err': True}
        # add word table to read buffer
        with self._read_requests_l as l:
            l.append({'type': 'word', 'addr': addr, 'size': size, 'use_f4': use_f4})
        # immediate modbus refresh
        self._write_io_evt.set()

    def add_longs_table(self, addr: int, size: int = 1, use_f4: bool = False, swap_word: bool = False):
        # init longs table with default value
        with self._thread_lock:
            for offset in range(0, size):
                self._r_longs_d[addr + offset * 2] = {'long': 0, 'err': True}
        # add long table to read buffer
        with self._read_requests_l as l:
            l.append({'type': 'long', 'addr': addr, 'size': size, 'use_f4': use_f4, 'swap_word': swap_word})
        # immediate modbus refresh
        self._write_io_evt.set()

    def add_floats_table(self, addr: int, size: int = 1, use_f4: bool = False, swap_word: bool = False):
        # init words table with default value
        with self._thread_lock:
            for offset in range(0, size):
                self._r_floats_d[addr + offset * 2] = {'float': 0.0, 'err': True}
        # add float table to read buffer
        with self._read_requests_l as l:
            l.append({'type': 'float', 'addr': addr, 'size': size, 'use_f4': use_f4, 'swap_word': swap_word})
        # immediate modbus refresh
        self._write_io_evt.set()
