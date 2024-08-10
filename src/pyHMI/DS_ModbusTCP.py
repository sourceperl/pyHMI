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
from .Misc import SafeObject, swap_word, bytes2word_list


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
def _auto_repr(self) -> str:
    return f"{self.__class__.__name__}({', '.join(f'{k}={repr(v)}' for k, v in self.__dict__.items())})"


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
        return _auto_repr(self)

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
                 default_value: Any, is_schedule: bool, single_func: bool = False) -> None:
        # no single query for more than one coil/register requested
        if single_func and size != 1:
            raise ValueError('cannot use single modbus function (single_func arg) if size is not set to 1')
        # args
        self.device = device
        self.type = type
        self.address = address
        self.size = size
        self.default_value = default_value
        self.is_schedule = is_schedule
        self.single_func = single_func
        # public
        self.data_space = _DataSpace(address=address, size=size, default_value=self.default_value)
        # reference request at device level
        self.device.requests_l.append(self)

        self.device._request_io_q.put_nowait(self)

    def __repr__(self) -> str:
        return _auto_repr(self)


class _RequestsList:
    def __init__(self) -> None:
        # private
        self._lock = threading.Lock()
        self._requests_l: List[_Request] = list()

    def __repr__(self) -> str:
        return _auto_repr(self)

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
        # allow thread safe access to modbus client (allow direct blocking IO on modbus socket)
        args_d = {} if self.client_adv_args is None else self.client_adv_args
        self.safe_cli = SafeObject(ModbusClient(host=self.host, port=self.port, unit_id=self.unit_id,
                                                timeout=self.timeout, auto_open=True, **args_d))
        # privates
        self._request_io_q: queue.Queue[_Request] = queue.Queue(maxsize=5)
        self._one_shot_req_th = threading.Thread(target=self._one_shot_req_thread, daemon=True)
        self._sched_req_th = threading.Thread(target=self._schedule_req_thread, daemon=True)
        # start threads
        self._one_shot_req_th.start()
        self._sched_req_th.start()

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

    def _one_shot_req_thread(self):
        """ Process every write I/O. """
        while True:
            # wait next request from queue
            request = self._request_io_q.get()
            # log it
            logger.debug(f'{threading.current_thread().name} receive {request}')
            # process it
            try:
                self._process_read_request(request)
                self._process_write_request(request)
            except ValueError as e:
                logger.warning(f'error in {threading.current_thread().name} ({request.__class__.__name__}): {e}')
            # mark queue task as done
            self._request_io_q.task_done()

    def _schedule_req_thread(self):
        """ Process every read I/O. """
        while True:
            # iterate over all requests in schedule list
            for request in self.requests_l.copy():
                try:
                    if request.is_schedule:
                        self._process_read_request(request)
                        self._process_write_request(request)
                except ValueError as e:
                    logger.warning(f'error in {threading.current_thread().name} ({request.__class__.__name__}): {e}')
            # wait before next refresh
            time.sleep(self.refresh)

    def add_read_bits_request(self, address: int, size: int = 1, schedule: bool = True, d_inputs: bool = False):
        req_type = _RequestType.READ_D_INPUTS if d_inputs else _RequestType.READ_COILS
        return _Request(self, type=req_type, address=address, size=size, default_value=None, is_schedule=schedule)

    def add_write_bits_request(self, address: int, size: int = 1, schedule: bool = True,
                               default_value: bool = False, single_func: bool = False):
        return _Request(self, type=_RequestType.WRITE_COILS, address=address, size=size,
                        default_value=default_value, is_schedule=schedule, single_func=single_func)

    def add_read_regs_request(self, address: int, size: int = 1, schedule: bool = True, i_regs: bool = False):
        req_type = _RequestType.READ_I_REGS if i_regs else _RequestType.READ_H_REGS
        return _Request(self, type=req_type, address=address, size=size, default_value=None, is_schedule=schedule)

    def add_write_regs_request(self, address: int, size: int = 1, is_schedule: bool = True, default_value: int = 0,
                               single_func: bool = False):
        return _Request(self, type=_RequestType.WRITE_H_REGS, address=address, size=size,
                        default_value=default_value, is_schedule=is_schedule, single_func=single_func)


class ModbusBool(DataSource):
    def __init__(self, request: _Request, address: int) -> None:
        # args
        self.request = request
        self.address = address
        # some check on request
        if request.type not in (_RequestType.READ_COILS, _RequestType.READ_D_INPUTS, _RequestType.WRITE_COILS):
            raise ValueError(f'bad request type {request.type.name} for {self.__class__.__name__}')
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
            raise ValueError(f'cannot write to this data source (bad request type {self.request.type.name})')
        # apply value to request data space
        with self.request.data_space as ds:
            ds[self.address].value = value

    def error(self) -> bool:
        with self.request.data_space as ds:
            return ds[self.address].error


class ModbusInt(DataSource):
    BIT_LENGTH_TYPE = Literal[16, 32, 64, 128]
    BYTE_ORDER_TYPE = Literal['little', 'big']

    def __init__(self, request: _Request, address: int,
                 bit_length: BIT_LENGTH_TYPE = 16, byte_order: BYTE_ORDER_TYPE = 'big',
                 signed: bool = False, swap_word: bool = False) -> None:
        # used by property
        self._bit_length: ModbusInt.BIT_LENGTH_TYPE = 16
        self._byte_order: ModbusInt.BYTE_ORDER_TYPE = 'big'
        # args
        self.request = request
        self.address = address
        self.bit_length = bit_length
        self.byte_order = byte_order
        self.signed = signed
        self.swap_word = swap_word
        # some check on request
        if request.type not in (_RequestType.READ_H_REGS, _RequestType.READ_I_REGS, _RequestType.WRITE_H_REGS):
            raise ValueError(f'bad request type {request.type.name} for {self.__class__.__name__}')
        if not request.data_space.is_init(at_address=self.address):
            raise ValueError(f'@{self.address} is not available in the data space of this request')

    def __repr__(self) -> str:
        return _auto_repr(self)

    @property
    def reg_nb(self):
        return self.bit_length//16 + (1 if self.bit_length % 16 else 0)

    @property
    def bit_length(self) -> BIT_LENGTH_TYPE:
        return self._bit_length

    @bit_length.setter
    def bit_length(self, value: BIT_LENGTH_TYPE):
        # runtime literal check
        if value not in get_args(ModbusInt.BIT_LENGTH_TYPE):
            raise ValueError(f'bit_length must be in {get_args(ModbusInt.BIT_LENGTH_TYPE)}')
        self._bit_length = value

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
        # apply swap word if requested
        if self.swap_word:
            value_as_b = swap_word(value_as_b)
        # format raw
        return int.from_bytes(value_as_b, byteorder=self._byte_order, signed=self.signed)

    def set(self, value: int) -> None:
        # check write status
        if self.request.type is not _RequestType.WRITE_H_REGS:
            raise ValueError(f'cannot write to this data source (bad request type {self.request.type.name})')
        # convert to bytes:
        # - check strange value status (negative for an unsigned, ...)
        # - apply 2's complement if requested
        try:
            value_b = value.to_bytes(2*self.reg_nb, byteorder=self.byte_order, signed=self.signed)
        except OverflowError as e:
            raise ValueError(f'cannot set this int ({e})')
        # apply swap word if requested
        if self.swap_word:
            value_b = swap_word(value_b)
        # build a list of register values
        regs_l = bytes2word_list(value_b)
        # apply it to address space
        for offset, reg_value in enumerate(regs_l):
            with self.request.data_space as ds:
                ds[self.address + offset].value = reg_value

    def error(self) -> bool:
        with self.request.data_space as ds:
            return ds[self.address].error


class ModbusFloat(DataSource):
    BIT_LENGTH_TYPE = Literal[32, 64]
    BYTE_ORDER_TYPE = Literal['little', 'big']

    def __init__(self, request: _Request, address: int,
                 bit_length: BIT_LENGTH_TYPE = 32, byte_order: BYTE_ORDER_TYPE = 'big',
                 swap_word: bool = False) -> None:
        # used by property
        self._bit_length: ModbusFloat.BIT_LENGTH_TYPE = 32
        self._byte_order: ModbusFloat.BYTE_ORDER_TYPE = 'big'
        # args
        self.request = request
        self.address = address
        self.bit_length = bit_length
        self.byte_order = byte_order
        self.swap_word = swap_word
        # some check on request
        if request.type not in (_RequestType.READ_H_REGS, _RequestType.READ_I_REGS, _RequestType.WRITE_H_REGS):
            raise ValueError(f'bad request type {request.type.name} for {self.__class__.__name__}')
        if not request.data_space.is_init(at_address=self.address):
            raise ValueError(f'@{self.address} is not available in the data space of this request')

    def __repr__(self) -> str:
        return _auto_repr(self)

    @property
    def reg_nb(self):
        return self.bit_length//16 + (1 if self.bit_length % 16 else 0)

    @property
    def bit_length(self) -> BIT_LENGTH_TYPE:
        return self._bit_length

    @bit_length.setter
    def bit_length(self, value: BIT_LENGTH_TYPE):
        # runtime literal check
        if value not in get_args(ModbusFloat.BIT_LENGTH_TYPE):
            raise ValueError(f'bit_length must be in {get_args(ModbusFloat.BIT_LENGTH_TYPE)}')
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
        # apply swap word if requested
        if self.swap_word:
            value_as_b = swap_word(value_as_b)
        # convert bytes to float and return it
        fmt = '>' if self.byte_order == 'big' else '<'
        fmt += 'f' if self.bit_length == 32 else 'd'
        return struct.unpack(fmt, value_as_b)[0]

    def set(self, value: float) -> None:
        # check write status
        if self.request.type is not _RequestType.WRITE_H_REGS:
            raise ValueError(f'cannot write to this data source (bad request type {self.request.type.name})')
        # convert to bytes:
        # - check strange value status (negative for an unsigned, ...)
        # - apply 2's complement if requested
        try:
            fmt = '>' if self.byte_order == 'big' else '<'
            fmt += 'f' if self.bit_length == 32 else 'd'
            value_b = struct.pack(fmt, value)
        except struct.error as e:
            raise ValueError(f'cannot set this float ({e})')
        # apply swap word if requested
        if self.swap_word:
            value_b = swap_word(value_b)
        # build a list of register values
        regs_l = bytes2word_list(value_b)
        # apply it to write address space
        with self.request.data_space as ds:
            for offset, reg_value in enumerate(regs_l):
                ds[self.address + offset].value = reg_value

    def error(self) -> bool:
        with self.request.data_space as ds:
            return ds[self.address].error
