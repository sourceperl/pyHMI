from enum import Enum, unique
import queue
import struct
import threading
import time
from typing import Any, Dict, List, Literal, Optional, get_args
from pyModbusTCP.client import ModbusClient
from pyHMI.Tag import Tag
from . import logger
from .Tag import DataSource, Device
from .Misc import SafeObject, swap_bytes, swap_words, bytes2word_list


# some consts
@unique
class _RequestType(Enum):
    READ_COILS = 1
    READ_D_INPUTS = 2
    READ_H_REGS = 3
    READ_I_REGS = 4
    WRITE_COILS = 5
    WRITE_H_REGS = 6


_READ_REQUESTS = (_RequestType.READ_COILS, _RequestType.READ_D_INPUTS,
                  _RequestType.READ_H_REGS, _RequestType.READ_I_REGS)
_WRITE_REQUESTS = (_RequestType.WRITE_COILS, _RequestType.WRITE_H_REGS)


# some functions
def _auto_repr(self: object, export_t: Optional[tuple] = None) -> str:
    args_str = ''
    for k, v in self.__dict__.items():
        if (export_t and k in export_t) or not export_t:
            if args_str:
                args_str += ', '
            args_str += f'{k}={repr(v)}'
    return f'{self.__class__.__name__}({args_str})'


# some class
class _DataSpace:
    class Data:
        def __init__(self, value: Any, error: bool) -> None:
            # args
            self.value = value
            self.error = error

        def __repr__(self) -> str:
            return _auto_repr(self)

    def __init__(self, address: int, size: int, default_value: Any) -> None:
        # private
        self._lock = threading.Lock()
        self._data_d: Dict[int, _DataSpace.Data] = dict()
        # populate data dict
        for iter_addr in range(address, address + size):
            self._data_d[iter_addr] = _DataSpace.Data(value=default_value, error=True)

    def __repr__(self) -> str:
        return _auto_repr(self, export_t=('_data_d', ))

    def __enter__(self):
        self._lock.acquire()
        return self._data_d

    def __exit__(self, *args):
        self._lock.release()

    def is_init(self, at_address: int, size: int = 1) -> bool:
        with self._lock:
            for offset in range(size):
                if not at_address + offset in self._data_d:
                    return False
        return True


class _Request:
    def __init__(self, device: "ModbusTCPDevice", type: _RequestType, address: int, size: int,
                 default_value: Any, scheduled: bool, single_func: bool = False) -> None:
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
        self.scheduled = scheduled
        self.single_func = single_func
        # public
        self.data_space = _DataSpace(address=address, size=size, default_value=self.default_value)
        # reference request at device level
        self.device.requests_l.append(self)

    def __repr__(self) -> str:
        return _auto_repr(self, export_t=('type', 'address', 'size'))

    def schedule_now(self) -> bool:
        try:
            self.device.one_shot_q.put_nowait(self)
            return True
        except queue.Full:
            logger.warning('unable to add request to one-shot run queue ({self!r})')
            return False


class _RequestsList:
    def __init__(self) -> None:
        # private
        self._lock = threading.Lock()
        self._requests_l: List[_Request] = list()

    def __len__(self) -> int:
        with self._lock:
            return len(self._requests_l)

    def copy(self) -> List[_Request]:
        with self._lock:
            return self._requests_l.copy()

    def append(self, request: _Request) -> None:
        with self._lock:
            self._requests_l.append(request)


class ModbusTCPDevice(Device):
    def __init__(self, host='localhost', port=502, unit_id=1, timeout=5.0, refresh=1.0,
                 client_adv_args: Optional[dict] = None):
        # args
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.refresh = refresh
        self.client_adv_args = client_adv_args
        # public
        self.requests_l = _RequestsList()
        self.one_shot_q: queue.Queue[_Request] = queue.Queue(maxsize=5)
        # allow thread safe access to modbus client (allow direct blocking IO on modbus socket)
        args_d = {} if self.client_adv_args is None else self.client_adv_args
        self.safe_cli = SafeObject(ModbusClient(host=self.host, port=self.port, unit_id=self.unit_id,
                                                timeout=self.timeout, auto_open=True, **args_d))
        # privates
        self._schedule_once_th = threading.Thread(target=self._schedule_once_thread, daemon=True)
        self._schedule_th = threading.Thread(target=self._schedule_thread, daemon=True)
        # start threads
        self._schedule_once_th.start()
        self._schedule_th.start()

    def __repr__(self):
        return f'{self.__class__.__name__}(host={self.host!r}, port={self.port}, unit_id={self.unit_id}, ' \
               f'timeout={self.timeout:.1f}, refresh={self.refresh:.1f}, client_adv_args={self.client_adv_args!r})'

    @property
    def connected(self):
        with self.safe_cli as cli:
            return cli.is_open

    def _process_read_request(self, request: _Request) -> None:
        # ignore other requests
        if request.type not in _READ_REQUESTS:
            return
        # do request
        if request.type is _RequestType.READ_COILS:
            with self.safe_cli as cli:
                reg_list = cli.read_coils(request.address, request.size)
        elif request.type == _RequestType.READ_D_INPUTS:
            with self.safe_cli as cli:
                reg_list = cli.read_discrete_inputs(request.address, request.size)
        elif request.type == _RequestType.READ_H_REGS:
            with self.safe_cli as cli:
                reg_list = cli.read_holding_registers(request.address, request.size)
        elif request.type == _RequestType.READ_I_REGS:
            with self.safe_cli as cli:
                reg_list = cli.read_input_registers(request.address, request.size)
        # process result
        if reg_list:
            # on success
            with request.data_space as ds:
                for offset, reg in enumerate(reg_list):
                    ds[request.address+offset].value = reg
                    ds[request.address+offset].error = False
        else:
            # on error
            with request.data_space as ds:
                for iter_addr in range(request.address, request.address + request.size):
                    ds[iter_addr].error = True

    def _process_write_request(self, request: _Request) -> None:
        # ignore other requests
        if request.type not in _WRITE_REQUESTS:
            return
        # get values for write(s)
        values_l = []
        with request.data_space as ds:
            for iter_addr in range(request.address, request.address + request.size):
                values_l.append(ds[iter_addr].value)
        # do request
        if request.type is _RequestType.WRITE_COILS:
            with self.safe_cli as cli:
                if request.single_func:
                    write_ok = cli.write_single_coil(request.address, values_l[0])
                else:
                    write_ok = cli.write_multiple_coils(request.address, values_l)
        elif request.type is _RequestType.WRITE_H_REGS:
            with self.safe_cli as cli:
                if request.single_func:
                    write_ok = cli.write_single_register(request.address, values_l[0])
                else:
                    write_ok = cli.write_multiple_registers(request.address, values_l)
        # process result
        with request.data_space as ds:
            # update error flag
            for iter_addr in range(request.address, request.address + request.size):
                ds[iter_addr].error = not write_ok

    def _schedule_once_thread(self):
        """ Process one-shot request. """
        while True:
            # wait next request from queue
            request = self.one_shot_q.get()
            # log it
            logger.debug(f'{threading.current_thread().name} receive {request}')
            # process it
            try:
                self._process_read_request(request)
                self._process_write_request(request)
            except Exception as e:
                msg = f'except {type(e).__name__} in {threading.current_thread().name} ' \
                      f'({request.__class__.__name__}): {e}'
                logger.warning(msg)
            # mark queue task as done
            self.one_shot_q.task_done()

    def _schedule_thread(self):
        """ Process every scheduled request. """
        while True:
            # iterate over all requests
            for request in self.requests_l.copy():
                try:
                    if request.scheduled:
                        self._process_read_request(request)
                        self._process_write_request(request)
                except Exception as e:
                    msg = f'except {type(e).__name__} in {threading.current_thread().name} ' \
                          f'({request.__class__.__name__}): {e}'
                    logger.warning(msg)
            # wait before next refresh
            time.sleep(self.refresh)

    def add_read_bits_request(self, address: int, size: int = 1, scheduled: bool = False, d_inputs: bool = False):
        req_type = _RequestType.READ_D_INPUTS if d_inputs else _RequestType.READ_COILS
        return _Request(self, type=req_type, address=address, size=size, default_value=None, scheduled=scheduled)

    def add_write_bits_request(self, address: int, size: int = 1, scheduled: bool = False,
                               default_value: bool = False, single_func: bool = False):
        return _Request(self, type=_RequestType.WRITE_COILS, address=address, size=size,
                        default_value=default_value, scheduled=scheduled, single_func=single_func)

    def add_read_regs_request(self, address: int, size: int = 1, scheduled: bool = False, i_regs: bool = False):
        req_type = _RequestType.READ_I_REGS if i_regs else _RequestType.READ_H_REGS
        return _Request(self, type=req_type, address=address, size=size, default_value=None, scheduled=scheduled)

    def add_write_regs_request(self, address: int, size: int = 1, scheduled: bool = False, default_value: int = 0,
                               single_func: bool = False):
        return _Request(self, type=_RequestType.WRITE_H_REGS, address=address, size=size,
                        default_value=default_value, scheduled=scheduled, single_func=single_func)


class ModbusBool(DataSource):
    def __init__(self, request: _Request, address: int, sched_on_write: bool = False) -> None:
        # args
        self.request = request
        self.address = address
        self.sched_on_write = sched_on_write
        # some check on request
        if request.type not in (_RequestType.READ_COILS, _RequestType.READ_D_INPUTS, _RequestType.WRITE_COILS):
            raise TypeError(f'bad request type {request.type.name} for {self.__class__.__name__}')
        if not request.data_space.is_init(at_address=self.address):
            raise ValueError(f'@{self.address} is not available in the data space of this request')

    def __repr__(self) -> str:
        return _auto_repr(self)

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if type(tag.first_value) is not bool:
            raise TypeError('first_value must be a bool')

    def get(self) -> Optional[bool]:
        # read from request data space
        with self.request.data_space as ds:
            return ds[self.address].value

    def set(self, value: bool) -> None:
        # check write status
        if self.request.type is not _RequestType.WRITE_COILS:
            raise TypeError(f'cannot write to this data source (bad request type {self.request.type.name})')
        # check value type
        if not isinstance(value, bool):
            raise TypeError(f'unsupported type for value (not a bool)')
        # apply value to request data space
        with self.request.data_space as ds:
            ds[self.address].value = value
        # request executed immediately if value is written
        if self.sched_on_write:
            self.request.schedule_now()

    def error(self) -> bool:
        with self.request.data_space as ds:
            return ds[self.address].error


class ModbusInt(DataSource):
    BYTE_ORDER_TYPE = Literal['little', 'big']

    def __init__(self, request: _Request, address: int, sched_on_write: bool = False,
                 bit_length: int = 16, byte_order: BYTE_ORDER_TYPE = 'big',
                 signed: bool = False, swap_bytes: bool = False, swap_word: bool = False) -> None:
        # used by property
        self._byte_order: ModbusInt.BYTE_ORDER_TYPE = 'big'
        # args
        self.request = request
        self.address = address
        self.sched_on_write = sched_on_write
        self.bit_length = bit_length
        self.byte_order = byte_order
        self.signed = signed
        self.swap_bytes = swap_bytes
        self.swap_word = swap_word
        # some check on request
        if request.type not in (_RequestType.READ_H_REGS, _RequestType.READ_I_REGS, _RequestType.WRITE_H_REGS):
            raise TypeError(f'bad request type {request.type.name} for {self.__class__.__name__}')
        if not request.data_space.is_init(at_address=self.address, size=self.reg_nb):
            raise ValueError(f'@{self.address} is not available in the data space of this request')

    def __repr__(self) -> str:
        return _auto_repr(self)

    @property
    def reg_nb(self):
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
        regs_l: List[int] = []
        with self.request.data_space as ds:
            for offest in range(self.reg_nb):
                regs_l.append(ds[self.address + offest].value)
        # skip decoding for uninitialized variables (usually at startup)
        if None in regs_l:
            return
        # list of regs (int) -> bytes
        value_as_b = bytes()
        for reg in regs_l:
            value_as_b += reg.to_bytes(2, byteorder='big')
        # apply swaps
        if self.swap_bytes:
            value_as_b = swap_bytes(value_as_b)
        if self.swap_word:
            value_as_b = swap_words(value_as_b)
        # format raw
        return int.from_bytes(value_as_b, byteorder=self._byte_order, signed=self.signed)

    def set(self, value: int) -> None:
        # check write status
        if self.request.type is not _RequestType.WRITE_H_REGS:
            raise TypeError(f'cannot write to this data source (bad request type {self.request.type.name})')
        # check value type
        if not isinstance(value, int):
            raise TypeError(f'unsupported type for value (not an int)')
        # convert to bytes:
        # - check strange value status (negative for an unsigned, ...)
        # - apply 2's complement if requested
        try:
            value_b = value.to_bytes(2*self.reg_nb, byteorder=self.byte_order, signed=self.signed)
        except OverflowError as e:
            raise ValueError(f'cannot set this int ({e})')
        # apply swaps
        if self.swap_bytes:
            value_b = swap_bytes(value_b)
        if self.swap_word:
            value_b = swap_words(value_b)
        # build a list of register values
        regs_l = bytes2word_list(value_b)
        # apply it to request address space
        for offset, reg_value in enumerate(regs_l):
            with self.request.data_space as ds:
                ds[self.address + offset].value = reg_value
        # request executed immediately if value is written
        if self.sched_on_write:
            self.request.schedule_now()

    def error(self) -> bool:
        with self.request.data_space as ds:
            return ds[self.address].error


class ModbusFloat(DataSource):
    BYTE_ORDER_TYPE = Literal['little', 'big']

    def __init__(self, request: _Request, address: int, sched_on_write: bool = False,
                 bit_length: int = 32, byte_order: BYTE_ORDER_TYPE = 'big',
                 swap_bytes: bool = False, swap_word: bool = False) -> None:
        # used by property
        self._bit_length = 32
        self._byte_order: ModbusFloat.BYTE_ORDER_TYPE = 'big'
        # args
        self.request = request
        self.address = address
        self.sched_on_write = sched_on_write
        self.bit_length = bit_length
        self.byte_order = byte_order
        self.swap_bytes = swap_bytes
        self.swap_word = swap_word
        # some check on request
        if request.type not in (_RequestType.READ_H_REGS, _RequestType.READ_I_REGS, _RequestType.WRITE_H_REGS):
            raise TypeError(f'bad request type {request.type.name} for {self.__class__.__name__}')
        if not request.data_space.is_init(at_address=self.address, size=self.reg_nb):
            raise ValueError(f'@{self.address} is not available in the data space of this request')

    def __repr__(self) -> str:
        return _auto_repr(self)

    @property
    def reg_nb(self):
        return self.bit_length//16 + (1 if self.bit_length % 16 else 0)

    @property
    def bit_length(self) -> int:
        return self._bit_length

    @bit_length.setter
    def bit_length(self, value: int):
        # runtime literal check
        if value not in [32, 64]:
            raise ValueError(f'bit_length must be either 32 or 64')
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
        regs_l: List[int] = []
        with self.request.data_space as ds:
            for offest in range(self.reg_nb):
                regs_l.append(ds[self.address + offest].value)
        # skip decoding for uninitialized variables (usually at startup)
        if None in regs_l:
            return
        # list of regs (int) -> bytes
        value_as_b = bytes()
        for reg in regs_l:
            value_as_b += reg.to_bytes(2, byteorder='big')
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
        if not isinstance(value, float):
            raise TypeError(f'unsupported type for value (not a float)')
        # convert to bytes:
        # - check strange value status (negative for an unsigned, ...)
        # - apply 2's complement if requested
        try:
            fmt = '>' if self.byte_order == 'big' else '<'
            fmt += 'f' if self.bit_length == 32 else 'd'
            value_b = struct.pack(fmt, value)
        except (struct.error, OverflowError) as e:
            raise ValueError(f'cannot set this float ({e})')
        # apply swaps
        if self.swap_bytes:
            value_b = swap_bytes(value_b)
        if self.swap_word:
            value_b = swap_words(value_b)
        # build a list of register values
        regs_l = bytes2word_list(value_b)
        # apply it to write address space
        with self.request.data_space as ds:
            for offset, reg_value in enumerate(regs_l):
                ds[self.address + offset].value = reg_value
        # request executed immediately if value is written
        if self.sched_on_write:
            self.request.schedule_now()

    def error(self) -> bool:
        with self.request.data_space as ds:
            return ds[self.address].error
