from enum import Enum
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


class _Space:
    class Data:
        def __init__(self, value: Any, error: bool) -> None:
            # args
            self.value = value
            self.error = error

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._data_d: Dict[int, _Space.Data] = dict()

    def __enter__(self):
        self._lock.acquire()
        return self._data_d

    def __exit__(self, *args):
        self._lock.release()

    def have_table(self, at_address: int, size: int = 1) -> bool:
        with self._lock:
            for offset in range(size):
                if not at_address + offset in self._data_d:
                    return False
        return True


class _Table:
    def __init__(self, space: _Space, address: int, size: int,  schedule: bool, default_value: Any) -> None:
        # args
        self.space = space
        self.address = address
        self.size = size
        self.schedule = schedule
        self.default_value = default_value
        # init address space for this table
        with self.space as sp:
            for iter_addr in range(self.address, self.address + self.size):
                sp[iter_addr] = _Space.Data(value=self.default_value, error=True)


class _ScheduleList:
    def __init__(self) -> None:
        # private
        self._lock = threading.Lock()
        self._tables_l: List[_Table] = list()

    def __enter__(self):
        self._lock.acquire()
        return self._tables_l

    def __exit__(self, *args):
        self._lock.release()

    # def add_table(self, modbus_table: _Table):
    #     with self._lo
    #     self._tables_l.append(modbus_table)
    #     for iter_addr in range(modbus_table.address, modbus_table.address + modbus_table.size):
    #         self._data_d[iter_addr] = _Table.Data(value=modbus_table.default_value, error=True)

    # def remove_table(self, modbus_table: _Table):
    #     # keep _address_d unchanged since tag and io thread can still access it
    #     try:
    #         self._tables_l.remove(modbus_table)
    #     except ValueError:
    #         pass

    def as_list(self) -> List[_Table]:
        with self._lock:
            return self._tables_l.copy()


class ModbusBool(DataSource):
    def __init__(self, device: "ModbusTCPDevice", address: int, d_inputs: bool = False, write: bool = False) -> None:
        # args
        self.device = device
        self.address = address
        self.write = write
        self.d_inputs = d_inputs
        # check no write set if input registers space is select
        if self.d_inputs and self.write:
            raise ValueError(f'unable to set write and d_inputs at same time (discrete inputs are read-only)')
        # private
        if self.write:
            self.space = self.device.write_coils_space
        elif self.d_inputs:
            self.space = self.device.read_d_inps_space
        else:
            self.space = self.device.read_coils_space
        # check table exist at device level
        if not self.space.have_table(at_address=address):
            raise ValueError(f'@{self.address} has no table defined (or it is undersized)')

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if type(tag.first_value) is not bool:
            logger.warning(msg=f'first_value type should be bool in {tag!r}')

    def get(self) -> Optional[bool]:
        with self.space as sp:
            return sp[self.address].value

    def set(self, value: bool) -> None:
        if self.write:
            with self.space as sp:
                sp[self.address].value = value
        else:
            raise ValueError(f'cannot write read-only {self!r}')

    def error(self) -> bool:
        with self.space as sp:
            return sp[self.address].error


class ModbusInt(DataSource):
    BIT_LENGTH_TYPE = Literal[16, 32, 64, 128]
    BYTE_ORDER_TYPE = Literal['little', 'big']

    def __init__(self, device: "ModbusTCPDevice", address: int, i_regs: bool = False,
                 bit_length: BIT_LENGTH_TYPE = 16, byte_order: BYTE_ORDER_TYPE = 'big',
                 signed: bool = False, swap_word: bool = False, write: bool = False) -> None:
        # used by property
        self._bit_length: ModbusInt.BIT_LENGTH_TYPE = 16
        self._byte_order: ModbusInt.BYTE_ORDER_TYPE = 'big'
        # args
        self.device = device
        self.address = address
        self.i_regs = i_regs
        self.bit_length = bit_length
        self.byte_order = byte_order
        self.signed = signed
        self.swap_word = swap_word
        self.write = write
        # check no write set if input registers space is select
        if self.i_regs and self.write:
            raise ValueError(f'unable to set write and i_regs at same time (input registers are read-only)')
        # private
        if self.write:
            self.space = self.device.write_h_regs_space
        elif self.i_regs:
            self.space = self.device.read_i_regs_space
        else:
            self.space = self.device.read_h_regs_space
        # check table exist at device level
        if not self.space.have_table(at_address=address, size=self.reg_nb):
            raise ValueError(f'@{self.address} has no table defined (or it is undersized)')

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
            logger.warning(msg=f'first_value type should be int in {tag!r}')

    def get(self) -> Optional[int]:
        # read register(s) into table
        regs_l: List[int] = []
        with self.space as sp:
            for offest in range(self.reg_nb):
                regs_l.append(sp[self.address + offest].value)
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
        if not self.write:
            raise ValueError(f'cannot write read-only {self!r}')
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
        # apply it to write address space
        for offset, reg_value in enumerate(regs_l):
            with self.space as sp:
                sp[self.address + offset].value = reg_value

    def error(self) -> bool:
        with self.space as sp:
            return sp[self.address].error


class ModbusFloat(DataSource):
    BIT_LENGTH_TYPE = Literal[32, 64]
    BYTE_ORDER_TYPE = Literal['little', 'big']

    def __init__(self, device: "ModbusTCPDevice", address: int, i_regs: bool = False, bit_length: BIT_LENGTH_TYPE = 32,
                 byte_order: BYTE_ORDER_TYPE = 'big', swap_word: bool = False, write: bool = False) -> None:
        # used by property
        self._bit_length: ModbusFloat.BIT_LENGTH_TYPE = 32
        self._byte_order: ModbusFloat.BYTE_ORDER_TYPE = 'big'
        # args
        self.device = device
        self.address = address
        self.i_regs = i_regs
        self.bit_length = bit_length
        self.byte_order = byte_order
        self.swap_word = swap_word
        self.write = write
        # check no write set if input registers space is select
        if self.i_regs and self.write:
            raise ValueError(f'unable to set write and i_regs at same time (input registers are read-only)')
        # private
        if self.write:
            self.space = self.device.write_h_regs_space
        elif self.i_regs:
            self.space = self.device.read_i_regs_space
        else:
            self.space = self.device.read_h_regs_space
        # check table exist at device level
        if not self.space.have_table(at_address=address, size=self.reg_nb):
            raise ValueError(f'@{self.address} has no table defined (or it is undersized)')

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
            logger.warning(msg=f'first_value type should be float in {tag!r}')

    def get(self) -> Optional[float]:
        # read register(s) into table
        regs_l: List[int] = []
        with self.space as sp:
            for offest in range(self.reg_nb):
                regs_l.append(sp[self.address + offest].value)
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
        if not self.write:
            raise ValueError(f'cannot write read-only {self!r}')
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
        with self.space as sp:
            for offset, reg_value in enumerate(regs_l):
                sp[self.address + offset].value = reg_value

    def error(self) -> bool:
        with self.space as sp:
            return sp[self.address].error


class ModbusTCPDevice(Device):
    def __init__(self, host='localhost', port=502, unit_id=1, timeout=5.0, read_refresh=1.0, write_refresh=1.0,
                 client_adv_args: Optional[dict] = None):
        # args
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.read_refresh = read_refresh
        self.write_refresh = write_refresh
        self.client_adv_args = client_adv_args
        # public vars
        self.read_coils_space = _Space()
        self.read_d_inps_space = _Space()
        self.read_h_regs_space = _Space()
        self.read_i_regs_space = _Space()
        self.write_coils_space = _Space()
        self.write_h_regs_space = _Space()
        self.read_io_sched_l = _ScheduleList()
        self.write_io_sched_l = _ScheduleList()
        # privates vars
        self._os_table_io_q: queue.Queue[_Table] = queue.Queue(maxsize=5)
        # allow thread safe access to modbus client (allow direct blocking IO on modbus socket)
        args_d = {} if self.client_adv_args is None else self.client_adv_args
        self.safe_cli = SafeObject(ModbusClient(host=self.host, port=self.port, unit_id=self.unit_id,
                                                timeout=self.timeout, auto_open=True, **args_d))
        # start threads
        self._one_shot_io_th = threading.Thread(target=self._one_shot_io_thread, daemon=True)
        self._read_io_th = threading.Thread(target=self._read_io_thread, daemon=True)
        self._write_io_th = threading.Thread(target=self._write_io_thread, daemon=True)
        self._one_shot_io_th.start()
        self._read_io_th.start()
        self._write_io_th.start()

    def __repr__(self):
        return f'ModbusTCPDevice(host={self.host!r}, port={self.port}, unit_id={self.unit_id}, ' \
               f'timeout={self.timeout:.1f}, read_refresh={self.read_refresh:.1f}, ' \
               f'write_refresh={self.write_refresh:.1f}, client_adv_args={self.client_adv_args!r})'

    @property
    def connected(self):
        with self.safe_cli as cli:
            return cli.is_open

    def _one_shot_io_thread(self):
        """ Process every write I/O. """
        while True:
            table = self._os_table_io_q.get()
            logger.warning(f'_one_shot_io_thread receive {table}')
            self._process_read_table(table)
            self._process_write_table(table)
            self._os_table_io_q.task_done()

    def _process_read_table(self, table: _Table):
        # do request
        if table.space == self.read_coils_space:
            with self.safe_cli as cli:
                reg_list = cli.read_coils(table.address, table.size)
        elif table.space == self.read_d_inps_space:
            with self.safe_cli as cli:
                reg_list = cli.read_discrete_inputs(table.address, table.size)
        elif table.space == self.read_h_regs_space:
            with self.safe_cli as cli:
                reg_list = cli.read_holding_registers(table.address, table.size)
        # process result
        if reg_list:
            # on success
            with table.space as sp:
                for offset, reg in enumerate(reg_list):
                    sp[table.address+offset].value = reg
                    sp[table.address+offset].error = False
        else:
            # on error
            with table.space as sp:
                for iter_addr in range(table.address, table.address + table.size):
                    sp[iter_addr].error = True

    def _process_write_table(self, table: _Table):
        # format values to write
        values_l = []
        with table.space as sp:
            for iter_addr in range(table.address, table.address + table.size):
                values_l.append(sp[iter_addr].value)
        # modbus request
        try:
            if table.space == self.write_coils_space:
                with self.safe_cli as cli:
                    if len(values_l) == 1:
                        write_ok = cli.write_single_coil(table.address, values_l[0])
                    else:
                        write_ok = cli.write_multiple_coils(table.address, values_l)
            elif table.space == self.write_h_regs_space:
                with self.safe_cli as cli:
                    if len(values_l) == 1:
                        write_ok = cli.write_single_register(table.address, values_l[0])
                    else:
                        write_ok = cli.write_multiple_registers(table.address, values_l)
            # process result
            with table.space as sp:
                # update error flag
                for iter_addr in range(table.address, table.address + table.size):
                    sp[iter_addr].error = not write_ok
        except ValueError as e:
            logger.warning(f'error in write_io_thread ({table.__class__.__name__}): {e}')

    def _read_io_thread(self):
        """ Process every read I/O. """
        while True:
            # iterate over all tables in schedule list
            for table in self.read_io_sched_l.as_list():
                try:
                    # process table marked as scheduled
                    if table.schedule:
                        self._process_read_table(table)
                except ValueError as e:
                    logger.warning(f'error in {threading.current_thread().name} ({table.__class__.__name__}): {e}')
            # wait before next polling
            time.sleep(self.read_refresh)

    def _write_io_thread(self):
        """ Process every write I/O. """
        while True:
            for table in self.write_io_sched_l.as_list():
                try:
                    # process table marked as scheduled
                    if table.schedule:
                        self._process_write_table(table)
                except ValueError as e:
                    logger.warning(f'error in {threading.current_thread().name} ({table.__class__.__name__}): {e}')
            # wait before next polling
            time.sleep(self.write_refresh)

    def add_read_bits_table(self, address: int, size: int = 1, schedule: bool = True, d_inputs: bool = False):
        # select tables group
        space = self.read_d_inps_space if d_inputs else self.read_coils_space
        # init table
        table = _Table(space, address, size, schedule=schedule, default_value=None)
        # schedule it
        with self.read_io_sched_l as l:
            l.append(table)
        return table

    def add_write_bits_table(self, address: int, size: int = 1, schedule: bool = True, default_value: bool = False):
        table = _Table(self.write_h_regs_space, address, size, schedule=schedule, default_value=default_value)
        with self.write_io_sched_l as l:
            l.append(table)
        return table

    def add_read_regs_table(self, address: int, size: int = 1, schedule: bool = True, i_regs: bool = False):
        # select tables group
        space = self.read_i_regs_space if i_regs else self.read_h_regs_space
        # init table
        table = _Table(space, address, size, schedule=schedule, default_value=None)
        # schedule it
        with self.read_io_sched_l as l:
            l.append(table)
        return table

    def add_write_regs_table(self, address: int, size: int = 1, schedule: bool = True, default_value: int = 0):
        table = _Table(self.write_h_regs_space, address, size, schedule=schedule, default_value=default_value)
        with self.write_io_sched_l as l:
            l.append(table)
        return table
