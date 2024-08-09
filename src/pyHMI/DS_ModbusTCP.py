from queue import Queue, Full
import struct
import threading
import time
from typing import Any, Dict, List, Literal, Optional, Union, get_args
from pyModbusTCP.client import ModbusClient
from pyHMI.Tag import Tag
from . import logger
from .Tag import DataSource, Device
from .Misc import SafeObject, swap_word, bytes2word_list


class _OneShotWriteRequest:
    def __init__(self, where: str, address: int, value: Union[bool, int, float, list]) -> None:
        # args
        self.where = where
        self.address = address
        self.value = value

    def __repr__(self) -> str:
        return f'_OneShotWriteRequest(where={self.where!r}, address={self.address!r}, value={self.value!r})'


class _Table:
    class Data:
        def __init__(self, value: Any, error: bool) -> None:
            # args
            self.value = value
            self.error = error

    def __init__(self, address: int, size: int, schedule: bool, default_value: Any) -> None:
        # args
        self.address = address
        self.size = size
        self.schedule = schedule
        self.default_value = default_value


class _TablesGroup:
    def __init__(self) -> None:
        # private
        # list of all tables to be shedule by io thread loop
        self._tables_l: List[_Table] = list()
        # global address dict = concatenation of all subset tables address dict
        self._data_d: Dict[int, _Table.Data] = dict()

    def __len__(self):
        return len(self._data_d)

    @property
    def data_d(self):
        return self._data_d

    def add_table(self, modbus_table: _Table):
        self._tables_l.append(modbus_table)
        for iter_addr in range(modbus_table.address, modbus_table.address + modbus_table.size):
            self._data_d[iter_addr] = _Table.Data(value=modbus_table.default_value, error=True)

    def remove_table(self, modbus_table: _Table):
        # keep _address_d unchanged since tag and io thread can still access it
        try:
            self._tables_l.remove(modbus_table)
        except ValueError:
            pass

    def as_list(self) -> List[_Table]:
        return self._tables_l.copy()

    def have_table(self, at_address: int, size: int = 1) -> bool:
        for offset in range(size):
            if not at_address + offset in self._data_d:
                return False
        return True


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
            self._tables_group = self.device.w_coils_tables
        elif self.d_inputs:
            self._tables_group = self.device.r_d_inps_tables
        else:
            self._tables_group = self.device.r_coils_tables
        # check table exist at device level
        with self._tables_group as tg:
            if not tg.have_table(at_address=address):
                raise ValueError(f'@{self.address} has no table defined (or it is undersized)')

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if type(tag.first_value) is not bool:
            logger.warning(msg=f'first_value type should be bool in {tag!r}')

    def get(self) -> Optional[bool]:
        with self._tables_group as tg:
            return tg.data_d[self.address].value

    def set(self, value: bool) -> None:
        if self.write:
            with self._tables_group as tg:
                tg.data_d[self.address].value = value
        else:
            raise ValueError(f'cannot write read-only {self!r}')

    def error(self) -> bool:
        with self._tables_group as tg:
            return tg.data_d[self.address].error


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
            self._tables_group = self.device.w_h_regs_tables
        elif self.i_regs:
            self._tables_group = self.device.r_i_regs_tables
        else:
            self._tables_group = self.device.r_h_regs_tables
        # check table exist at device level
        with self._tables_group as tg:
            if not tg.have_table(at_address=address, size=self.reg_nb):
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
        with self._tables_group as tg:
            for offest in range(self.reg_nb):
                regs_l.append(tg.data_d[self.address + offest].value)
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
        with self._tables_group as tg:
            for offset, reg_value in enumerate(regs_l):
                tg.data_d[self.address + offset].value = reg_value

    def error(self) -> bool:
        with self._tables_group as tg:
            return tg.data_d[self.address].error


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
            self._tables_group = self.device.w_h_regs_tables
        elif self.i_regs:
            self._tables_group = self.device.r_i_regs_tables
        else:
            self._tables_group = self.device.r_h_regs_tables
        # check table exist at device level
        with self._tables_group as tg:
            if not tg.have_table(at_address=address, size=self.reg_nb):
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
        with self._tables_group as tg:
            for offest in range(self.reg_nb):
                regs_l.append(tg.data_d[self.address + offest].value)
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
        with self._tables_group as tg:
            for offset, reg_value in enumerate(regs_l):
                tg.data_d[self.address + offset].value = reg_value

    def error(self) -> bool:
        with self._tables_group as tg:
            return tg.data_d[self.address].error


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
        self.r_coils_tables = SafeObject(_TablesGroup())
        self.r_d_inps_tables = SafeObject(_TablesGroup())
        self.r_h_regs_tables = SafeObject(_TablesGroup())
        self.r_i_regs_tables = SafeObject(_TablesGroup())
        self.w_coils_tables = SafeObject(_TablesGroup())
        self.w_h_regs_tables = SafeObject(_TablesGroup())
        # privates vars
        self._one_shot_q = Queue(maxsize=5)
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
            a_task_to_do = self._one_shot_q.get()
            logger.warning(f'_one_shot_io_thread receive {a_task_to_do}')
            self._one_shot_q.task_done()

    def _read_io_thread(self):
        """ Process every read I/O. """
        while True:
            for tables_group in (self.r_coils_tables, self.r_d_inps_tables,
                                 self.r_h_regs_tables, self.r_i_regs_tables):
                # read coils space
                with tables_group as tg:
                    cp_tables_l = tg.as_list()
                # iterate over all tables of tg_group
                for table in cp_tables_l:
                    # process table marked as scheduled
                    if table.schedule:
                        # modbus request
                        try:
                            if tables_group == self.r_coils_tables:
                                with self.safe_cli as cli:
                                    reg_list = cli.read_coils(table.address, table.size)
                            elif tables_group == self.r_d_inps_tables:
                                with self.safe_cli as cli:
                                    reg_list = cli.read_discrete_inputs(table.address, table.size)
                            elif tables_group == self.r_h_regs_tables:
                                with self.safe_cli as cli:
                                    reg_list = cli.read_holding_registers(table.address, table.size)
                            # process result
                            with tables_group as tg:
                                if reg_list:
                                    # on success
                                    for offset, reg in enumerate(reg_list):
                                        tg.data_d[table.address+offset].value = reg
                                        tg.data_d[table.address+offset].error = False
                                else:
                                    # on error
                                    for iter_addr in range(table.address, table.address + table.size):
                                        tg.data_d[iter_addr].error = True
                        except ValueError as e:
                            logger.warning(f'error in read_io_thread ({table.__class__.__name__}): {e}')
            # wait before next polling
            time.sleep(self.read_refresh)

    def _write_io_thread(self):
        """ Process every write I/O. """
        while True:
            for tables_group in (self.w_coils_tables, self.w_h_regs_tables):
                # write coils space
                with tables_group as tg:
                    cp_tables_l = tg.as_list()
                # iterate over a safe list of tables
                for table in cp_tables_l:
                    # process table marked as scheduled
                    if table.schedule:
                        # format values to write
                        values_l = []
                        with tables_group as tg:
                            for iter_addr in range(table.address, table.address + table.size):
                                values_l.append(tg.data_d[iter_addr].value)
                        # modbus request
                        try:
                            if tables_group == self.w_coils_tables:
                                with self.safe_cli as cli:
                                    if len(values_l) == 1:
                                        write_ok = cli.write_single_coil(table.address, values_l[0])
                                    else:
                                        write_ok = cli.write_multiple_coils(table.address, values_l)
                            elif tables_group == self.w_h_regs_tables:
                                with self.safe_cli as cli:
                                    if len(values_l) == 1:
                                        write_ok = cli.write_single_register(table.address, values_l[0])
                                    else:
                                        write_ok = cli.write_multiple_registers(table.address, values_l)
                            # process result
                            with tables_group as tg:
                                # update error flag
                                for iter_addr in range(table.address, table.address + table.size):
                                    tg.data_d[iter_addr].error = not write_ok
                        except ValueError as e:
                            logger.warning(f'error in write_io_thread ({table.__class__.__name__}): {e}')
            # wait before next polling
            time.sleep(self.write_refresh)

    def add_read_bits_table(self, address: int, size: int = 1, schedule: bool = True, d_inputs: bool = False):
        # select tables group
        if d_inputs:
            tables_group = self.r_d_inps_tables
        else:
            tables_group = self.r_coils_tables
        # init table
        table = _Table(address=address, size=size, schedule=schedule, default_value=None)
        # link it to table group
        with tables_group as tg:
            tg.add_table(table)
        return table

    def add_write_bits_table(self, address: int, size: int = 1, schedule: bool = True, default_value: bool = False):
        # init table
        table = _Table(address=address, size=size, schedule=schedule, default_value=default_value)
        # link it to table group
        with self.w_coils_tables as tg:
            tg.add_table(table)
        return table

    def add_read_regs_table(self, address: int, size: int = 1, schedule: bool = True, i_regs: bool = False):
        # select tables group
        if i_regs:
            tables_group = self.r_i_regs_tables
        else:
            tables_group = self.r_h_regs_tables
        # init table
        table = _Table(address=address, size=size, schedule=schedule, default_value=None)
        # link it to table group
        with tables_group as tg:
            tg.add_table(table)
        return table

    def add_write_regs_table(self, address: int, size: int = 1, schedule: bool = True, default_value: int = 0):
        # init table
        table = _Table(address=address, size=size, schedule=schedule, default_value=default_value)
        # link it to table group
        with self.w_h_regs_tables as tg:
            tg.add_table(table)
        return table

    def write_coils(self, address: int, value: bool) -> bool:
        # schedules the write operation
        try:
            self._one_shot_q.put(_OneShotWriteRequest(where='coils', address=address, value=value), block=False)
            return True
        except Full:
            return False

    # def write_word(self, address: int, value: int):
    #     # schedules the write operation
    #     try:
    #         self._one_shot_q.put(_OneShotWriteRequest(where='h_registers', address=address, value=value), block=False)
    #         return True
    #     except Full:
    #         return False

    # def write_float(self, address: int, value: float, swap_word: bool = False):
    #     # schedules the write operation
    #     try:
    #         self._one_shot_q.put(_OneShotWriteRequest(where='float', address=address, value=value), block=False)
    #         return True
    #     except Full:
    #         return False
