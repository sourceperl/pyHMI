from enum import Enum, auto
import queue
import struct
import threading
import time
from typing import Any, Dict, List, Literal, Optional, get_args
from pyModbusTCP.client import ModbusClient
from pyHMI.Tag import Tag
from . import logger
from .Tag import DataSource, Device
from .Misc import SafeObject, auto_repr, swap_bytes, swap_words, cut_bytes_to_regs


# some class
class _RequestType(Enum):
    READ_COILS = auto()
    READ_D_INPUTS = auto()
    READ_H_REGS = auto()
    READ_I_REGS = auto()
    WRITE_COILS = auto()
    WRITE_H_REGS = auto()


class _RequestGroup:
    READ = [_RequestType.READ_COILS, _RequestType.READ_D_INPUTS,
            _RequestType.READ_H_REGS, _RequestType.READ_I_REGS]
    WRITE = [_RequestType.WRITE_COILS, _RequestType.WRITE_H_REGS]


class _Data:
    def __init__(self, address: int, size: int, default_value: Any) -> None:
        # private
        self._lock = threading.Lock()
        self._data_d: Dict[int, Any] = dict()
        # populate data dict
        for iter_addr in range(address, address + size):
            self._data_d[iter_addr] = default_value

    def __repr__(self) -> str:
        return auto_repr(self, export_t=('_data_d', ))

    def __enter__(self):
        self._lock.acquire()
        return self._data_d

    def __exit__(self, *args):
        self._lock.release()


class ModbusRequest:
    def __init__(self, device: "ModbusTCPDevice", type: _RequestType, address: int, size: int,
                 default_value: Any, run_cyclic: bool, run_on_set: bool = False, single_func: bool = False) -> None:
        # check single queries
        if single_func and size != 1:
            raise ValueError('single modbus function requires size=1')
        # check limits
        if not 0 <= address <= 0xffff:
            raise ValueError('address out of range (valid from 0 to 65535)')
        if address + size > 0x10000:
            raise ValueError('request after end of address space')
        if type in (_RequestType.READ_COILS, _RequestType.READ_D_INPUTS):
            if not 1 <= size <= 2000:
                raise ValueError('size out of range (valid from 1 to 2000)')
        elif type in (_RequestType.READ_H_REGS, _RequestType.READ_I_REGS):
            if not 1 <= size <= 125:
                raise ValueError('size out of range (valid from 1 to 125)')
        elif type is _RequestType.WRITE_COILS:
            if not 1 <= size <= 1968:
                raise ValueError('size out of range (valid from 1 to 1968)')
        elif type is _RequestType.WRITE_H_REGS:
            if not 1 <= size <= 123:
                raise ValueError('size out of range (valid from 1 to 123)')
        # args
        self.device = device
        self.type = type
        self.address = address
        self.size = size
        self.default_value = default_value
        self.run_cyclic = run_cyclic
        self.run_on_set = run_on_set
        self.single_func = single_func
        # public
        self.error = True
        self.run_done_evt = threading.Event()
        # private
        self._data = _Data(address=address, size=size, default_value=self.default_value)
        self._single_run_expire = 0.0
        # reference request at device level
        self.device.requests_l.append(self)

    def __repr__(self) -> str:
        return auto_repr(self, export_t=('type', 'address', 'size'))

    @property
    def _single_run_expired(self) -> bool:
        return time.monotonic() > self._single_run_expire

    @property
    def single_run_ready(self) -> bool:
        # single-run thread process fresh modbus request exclusively
        return not self._single_run_expired

    def _get_data(self, address: int, size: int = 1) -> list:
        registers_l = []
        with self._data as data:
            for i in range(size):
                registers_l.append(data[address + i])
        return registers_l

    def _set_data(self, address: int, registers_l: list, by_thread: bool = False):
        # apply it to write address space
        with self._data as data:
            for i, value in enumerate(registers_l):
                data[address + i] = value
        # skip others process if call by a thread
        if by_thread:
            return
        # request executed on set
        if self.run_on_set:
            self.run()

    def is_valid(self, at_address: int, for_size: int = 1) -> bool:
        """ Indicate request validity for this address and size. """
        with self._data as data:
            for offset in range(for_size):
                if not at_address + offset in data:
                    return False
        return True

    def run(self) -> bool:
        """ Attempt immediate execution of the request using the single run thread.

        Any pending execution will be canceled after the delay specified at device level in
        run_cancel_delay (defaults to 5.0 seconds).

        Return True if the request is queued.
        """
        # accept this request when device is actually connected or if the single-run queue is empty
        if self.device.connected or (self.device.single_run_req_q.qsize() == 0):
            # set an expiration stamp (avoid single-run thread process outdated request)
            self._single_run_expire = time.monotonic() + self.device.run_cancel_delay
            try:
                self.device.single_run_req_q.put_nowait(self)
                self.run_done_evt.clear()
                return True
            except queue.Full:
                logger.warning(f'single-run queue full, drop {self.type.name} at @{self.address}')
        # error reporting
        return False


class _RequestsList:
    def __init__(self) -> None:
        # private
        self._lock = threading.Lock()
        self._requests_l: List[ModbusRequest] = list()

    def __len__(self) -> int:
        with self._lock:
            return len(self._requests_l)

    def copy(self) -> List[ModbusRequest]:
        with self._lock:
            return self._requests_l.copy()

    def append(self, request: ModbusRequest) -> None:
        with self._lock:
            self._requests_l.append(request)


class ModbusTCPDevice(Device):
    def __init__(self, host='localhost', port=502, unit_id=1, timeout=5.0, refresh=1.0, run_cancel_delay=5.0,
                 client_args: Optional[dict] = None):
        # args
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.refresh = refresh
        self.client_args = client_args
        # public
        self.connected = False
        self.run_cancel_delay = run_cancel_delay
        self.requests_l = _RequestsList()
        self.single_run_req_q: queue.Queue[ModbusRequest] = queue.Queue(maxsize=255)
        # allow thread safe access to modbus client (allow direct blocking IO on modbus socket)
        args_d = {} if self.client_args is None else self.client_args
        self.safe_cli = SafeObject(ModbusClient(host=self.host, port=self.port, unit_id=self.unit_id,
                                                timeout=self.timeout, auto_open=True, **args_d))
        # privates
        self._single_run_th = threading.Thread(target=self._single_run_thread, daemon=True)
        self._cyclic_th = threading.Thread(target=self._cyclic_thread, daemon=True)
        # start threads
        self._single_run_th.start()
        self._cyclic_th.start()

    def __repr__(self):
        return f'{self.__class__.__name__}(host={self.host!r}, port={self.port}, unit_id={self.unit_id}, ' \
               f'timeout={self.timeout:.1f}, refresh={self.refresh:.1f}, client_adv_args={self.client_args!r})'

    def _process_read_request(self, request: ModbusRequest) -> None:
        # do request
        if request.type is _RequestType.READ_COILS:
            with self.safe_cli as cli:
                registers_l = cli.read_coils(request.address, request.size)
        elif request.type == _RequestType.READ_D_INPUTS:
            with self.safe_cli as cli:
                registers_l = cli.read_discrete_inputs(request.address, request.size)
        elif request.type == _RequestType.READ_H_REGS:
            with self.safe_cli as cli:
                registers_l = cli.read_holding_registers(request.address, request.size)
        elif request.type == _RequestType.READ_I_REGS:
            with self.safe_cli as cli:
                registers_l = cli.read_input_registers(request.address, request.size)
        else:
            # ignore other requests
            return
        # process result
        if registers_l:
            # on success
            request._set_data(address=request.address, registers_l=registers_l, by_thread=True)
            request.error = False
        else:
            # on error
            request.error = True
        # mark request run as done
        request.run_done_evt.set()

    def _process_write_request(self, request: ModbusRequest) -> None:
        # do request
        if request.type is _RequestType.WRITE_COILS:
            registers_l = request._get_data(address=request.address, size=request.size)
            with self.safe_cli as cli:
                if request.single_func:
                    write_ok = cli.write_single_coil(request.address, registers_l[0])
                else:
                    write_ok = cli.write_multiple_coils(request.address, registers_l)
        elif request.type is _RequestType.WRITE_H_REGS:
            registers_l = request._get_data(address=request.address, size=request.size)
            with self.safe_cli as cli:
                if request.single_func:
                    write_ok = cli.write_single_register(request.address, registers_l[0])
                else:
                    write_ok = cli.write_multiple_registers(request.address, registers_l)
        else:
            # ignore other requests
            return
        # result
        request.error = not write_ok
        # mark request run as done
        request.run_done_evt.set()

    def _update_device_status(self):
        # update connected flag
        with self.safe_cli as cli:
            self.connected = cli.is_open

    def _single_run_thread(self):
        """ This thread executes all requests put to the single-run queue. """
        while True:
            # wait next request from queue
            request = self.single_run_req_q.get()
            # log it
            logger.debug(f'{threading.current_thread().name} receive {request}')
            # process it
            try:
                if request.single_run_ready:
                    self._process_read_request(request)
                    self._process_write_request(request)
                    self._update_device_status()
            except Exception as e:
                msg = f'except {type(e).__name__} in {threading.current_thread().name} ' \
                      f'({request.__class__.__name__}): {e}'
                logger.warning(msg)
            # mark queue task as done
            self.single_run_req_q.task_done()

    def _cyclic_thread(self):
        """ This thread executes cyclic requests. """
        while True:
            # iterate over all requests
            for request in self.requests_l.copy():
                try:
                    if request.run_cyclic:
                        self._process_read_request(request)
                        self._process_write_request(request)
                        self._update_device_status()
                except Exception as e:
                    msg = f'except {type(e).__name__} in {threading.current_thread().name} ' \
                          f'({request.__class__.__name__}): {e}'
                    logger.warning(msg)
            # wait before next refresh
            time.sleep(self.refresh)

    def add_read_bits_request(self, address: int, size: int = 1, run_cyclic: bool = False, d_inputs: bool = False):
        req_type = _RequestType.READ_D_INPUTS if d_inputs else _RequestType.READ_COILS
        return ModbusRequest(self, type=req_type, address=address, size=size, default_value=None, run_cyclic=run_cyclic)

    def add_write_bits_request(self, address: int, size: int = 1, run_cyclic: bool = False, run_on_set: bool = False,
                               default_value: bool = False, single_func: bool = False):
        return ModbusRequest(self, type=_RequestType.WRITE_COILS, address=address, size=size, default_value=default_value,
                             run_cyclic=run_cyclic, run_on_set=run_on_set, single_func=single_func)

    def add_read_regs_request(self, address: int, size: int = 1, run_cyclic: bool = False, i_regs: bool = False):
        req_type = _RequestType.READ_I_REGS if i_regs else _RequestType.READ_H_REGS
        return ModbusRequest(self, type=req_type, address=address, size=size, default_value=None, run_cyclic=run_cyclic)

    def add_write_regs_request(self, address: int, size: int = 1, run_cyclic: bool = False, run_on_set: bool = False,
                               default_value: int = 0, single_func: bool = False):
        return ModbusRequest(self, type=_RequestType.WRITE_H_REGS, address=address, size=size, default_value=default_value,
                             run_cyclic=run_cyclic, run_on_set=run_on_set, single_func=single_func)


class ModbusBool(DataSource):
    def __init__(self, request: ModbusRequest, address: int) -> None:
        # args
        self.request = request
        self.address = address
        # some check on request
        if request.type not in (_RequestType.READ_COILS, _RequestType.READ_D_INPUTS, _RequestType.WRITE_COILS):
            raise TypeError(f'bad request type {request.type.name} for {self.__class__.__name__}')
        if not request.is_valid(at_address=self.address):
            raise ValueError(f'@{self.address} is not available in the data space of this request')

    def __repr__(self) -> str:
        return auto_repr(self)

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if type(tag.first_value) is not bool:
            raise TypeError('first_value must be a bool')

    def get(self) -> Optional[bool]:
        return self.request._get_data(address=self.address)[0]

    def set(self, value: bool) -> None:
        # check write status
        if self.request.type is not _RequestType.WRITE_COILS:
            raise TypeError(f'cannot write to this data source (bad request type {self.request.type.name})')
        # check value type
        if not isinstance(value, bool):
            raise TypeError('unsupported type for value (not a bool)')
        # apply value to request data space
        self.request._set_data(address=self.address, registers_l=[value])

    def error(self) -> bool:
        return self.request.error


class ModbusInt(DataSource):
    BYTE_ORDER_TYPE = Literal['little', 'big']

    def __init__(self, request: ModbusRequest, address: int, bit_length: int = 16, byte_order: BYTE_ORDER_TYPE = 'big',
                 signed: bool = False, swap_bytes: bool = False, swap_word: bool = False) -> None:
        # used by property
        self._byte_order: ModbusInt.BYTE_ORDER_TYPE = 'big'
        # args
        self.request = request
        self.address = address
        self.bit_length = bit_length
        self.byte_order = byte_order
        self.signed = signed
        self.swap_bytes = swap_bytes
        self.swap_word = swap_word
        # some check on request
        if request.type not in (_RequestType.READ_H_REGS, _RequestType.READ_I_REGS, _RequestType.WRITE_H_REGS):
            raise TypeError(f'bad request type {request.type.name} for {self.__class__.__name__}')
        if not request.is_valid(at_address=self.address, for_size=self.reg_length):
            raise ValueError(f'@{self.address} is not available in the data space of this request')

    def __repr__(self) -> str:
        return auto_repr(self)

    @property
    def reg_length(self):
        return self.bit_length//16 + (1 if self.bit_length % 16 else 0)

    @property
    def byte_order(self) -> BYTE_ORDER_TYPE:
        return self._byte_order

    @byte_order.setter
    def byte_order(self, value: BYTE_ORDER_TYPE):
        # runtime literal check
        if value not in get_args(ModbusInt.BYTE_ORDER_TYPE):
            raise ValueError(f'byte_order must be in {get_args(ModbusInt.BYTE_ORDER_TYPE)}')
        self._byte_order = value

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if type(tag.first_value) is not int:
            raise TypeError('first_value must be an int')

    def get(self) -> Optional[int]:
        # read register(s)
        registers_l = self.request._get_data(address=self.address, size=self.reg_length)
        # skip decoding for uninitialized variables (usually at startup)
        if None in registers_l:
            return
        # list of registers (int) -> bytes
        value_as_b = bytes()
        for register in registers_l:
            value_as_b += register.to_bytes(2, byteorder='big')
        # apply swaps
        if self.swap_bytes:
            value_as_b = swap_bytes(value_as_b)
        if self.swap_word:
            value_as_b = swap_words(value_as_b)
        # format raw
        return int.from_bytes(value_as_b, byteorder=self.byte_order, signed=self.signed)

    def set(self, value: int) -> None:
        # check write status
        if self.request.type is not _RequestType.WRITE_H_REGS:
            raise TypeError(f'cannot write to this data source (bad request type {self.request.type.name})')
        # check value type
        if not isinstance(value, int):
            raise TypeError('unsupported type for value (not an int)')
        # convert to bytes:
        # - check strange value status (negative for an unsigned, ...)
        # - apply 2's complement if requested
        try:
            value_as_b = value.to_bytes(2*self.reg_length, byteorder=self.byte_order, signed=self.signed)
        except OverflowError as e:
            raise ValueError(f'cannot set this int ({e})')
        # apply swaps
        if self.swap_bytes:
            value_as_b = swap_bytes(value_as_b)
        if self.swap_word:
            value_as_b = swap_words(value_as_b)
        # apply value to request data space
        self.request._set_data(address=self.address, registers_l=cut_bytes_to_regs(value_as_b))

    def error(self) -> bool:
        return self.request.error


class ModbusFloat(DataSource):
    BYTE_ORDER_TYPE = Literal['little', 'big']

    def __init__(self, request: ModbusRequest, address: int, bit_length: int = 32, byte_order: BYTE_ORDER_TYPE = 'big',
                 swap_bytes: bool = False, swap_word: bool = False) -> None:
        # used by property
        self._bit_length = 32
        self._byte_order: ModbusFloat.BYTE_ORDER_TYPE = 'big'
        # args
        self.request = request
        self.address = address
        self.bit_length = bit_length
        self.byte_order = byte_order
        self.swap_bytes = swap_bytes
        self.swap_word = swap_word
        # some check on request
        if request.type not in (_RequestType.READ_H_REGS, _RequestType.READ_I_REGS, _RequestType.WRITE_H_REGS):
            raise TypeError(f'bad request type {request.type.name} for {self.__class__.__name__}')
        if not request.is_valid(at_address=self.address, for_size=self.reg_length):
            raise ValueError(f'@{self.address} is not available in the data space of this request')

    def __repr__(self) -> str:
        return auto_repr(self)

    @property
    def reg_length(self):
        return self.bit_length//16 + (1 if self.bit_length % 16 else 0)

    @property
    def bit_length(self) -> int:
        return self._bit_length

    @bit_length.setter
    def bit_length(self, value: int):
        # runtime literal check
        if value not in [32, 64]:
            raise ValueError('bit_length must be either 32 or 64')
        self._bit_length = value

    @property
    def byte_order(self) -> BYTE_ORDER_TYPE:
        return self._byte_order

    @byte_order.setter
    def byte_order(self, value: BYTE_ORDER_TYPE):
        # runtime literal check
        if value not in get_args(ModbusFloat.BYTE_ORDER_TYPE):
            raise ValueError(f'byte_order must be in {get_args(ModbusFloat.BYTE_ORDER_TYPE)}')
        self._byte_order = value

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if type(tag.first_value) is not float:
            raise TypeError('first_value must be a float')

    def get(self) -> Optional[float]:
        # read register(s)
        registers_l = self.request._get_data(address=self.address, size=self.reg_length)
        # skip decoding for uninitialized variables (usually at startup)
        if None in registers_l:
            return
        # list of registers (int) -> bytes
        value_as_b = bytes()
        for register in registers_l:
            value_as_b += register.to_bytes(2, byteorder='big')
        # apply swaps
        if self.swap_bytes:
            value_as_b = swap_bytes(value_as_b)
        if self.swap_word:
            value_as_b = swap_words(value_as_b)
        # convert bytes to float and return it
        fmt = '>' if self.byte_order == 'big' else '<'
        fmt += 'f' if self.bit_length == 32 else 'd'
        return struct.unpack(fmt, value_as_b)[0]

    def set(self, value: float) -> None:
        # check write status
        if self.request.type is not _RequestType.WRITE_H_REGS:
            raise TypeError(f'cannot write to this data source (bad request type {self.request.type.name})')
        # check value type
        if not isinstance(value, (int, float)):
            raise TypeError('unsupported type for value (not an int or a float)')
        # convert to bytes:
        # - check strange value status (negative for an unsigned, ...)
        # - apply 2's complement if requested
        try:
            fmt = '>' if self.byte_order == 'big' else '<'
            fmt += 'f' if self.bit_length == 32 else 'd'
            value_as_b = struct.pack(fmt, value)
        except (struct.error, OverflowError) as e:
            raise ValueError(f'cannot set this float ({e})')
        # apply swaps
        if self.swap_bytes:
            value_as_b = swap_bytes(value_as_b)
        if self.swap_word:
            value_as_b = swap_words(value_as_b)
        # apply value to request data space
        self.request._set_data(address=self.address, registers_l=cut_bytes_to_regs(value_as_b))

    def error(self) -> bool:
        return self.request.error


class ModbusTboxStr(DataSource):
    def __init__(self, request: ModbusRequest, address: int, str_length: int, encoding: str = 'iso-8859-1') -> None:
        # args
        self.request = request
        self.address = address
        self.str_length = str_length
        self.encoding = encoding
        # some check on request
        if request.type not in (_RequestType.READ_H_REGS, _RequestType.READ_I_REGS, _RequestType.WRITE_H_REGS):
            raise TypeError(f'bad request type {request.type.name} for {self.__class__.__name__}')
        if not request.is_valid(at_address=self.address, for_size=self.reg_length):
            raise ValueError(f'@{self.address} is not available in the data space of this request')

    def __repr__(self) -> str:
        return auto_repr(self)

    @property
    def reg_length(self):
        return self.str_length//2 + (1 if self.str_length % 2 else 0)

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if type(tag.first_value) is not str:
            raise TypeError('first_value must be a str')

    def get(self) -> Optional[str]:
        # read register(s)
        registers_l = self.request._get_data(address=self.address, size=self.reg_length)
        # skip decoding for uninitialized variables (usually at startup)
        if None in registers_l:
            return
        # list of registers (int) -> bytes
        value_as_b = bytes()
        for register in registers_l:
            value_as_b += register.to_bytes(2, byteorder='big')
        # remove the final padding
        value_as_b = value_as_b.rstrip(b'\x00')
        # format raw
        try:
            return value_as_b.decode(self.encoding)
        except UnicodeDecodeError as e:
            logger.warning(f'unable to decode this str ({e})')
            return None

    def set(self, value: str) -> None:
        # check write status
        if self.request.type is not _RequestType.WRITE_H_REGS:
            raise TypeError(f'cannot write to this data source (bad request type {self.request.type.name})')
        # check value type
        if not isinstance(value, str):
            raise TypeError('unsupported type for value (not a str)')
        # ckeck string length
        if len(value) > self.str_length:
            raise ValueError(f'cannot set this str (too long: declared size is {self.str_length} char(s))')
        # convert to bytes:
        # - check strange value status (negative for an unsigned, ...)
        # - apply 2's complement if requested
        try:
            value_as_b = value.encode(self.encoding)
        except UnicodeEncodeError as e:
            raise ValueError(f'cannot set this str ({e})')
        # finalize with b'\x00' padding
        value_as_b = value_as_b.ljust(self.reg_length, b'\x00')
        # apply value to request data space
        self.request._set_data(address=self.address, registers_l=cut_bytes_to_regs(value_as_b))

    def error(self) -> bool:
        return self.request.error
