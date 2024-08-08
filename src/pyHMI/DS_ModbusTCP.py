from queue import Queue, Full
import threading
import time
from token import OP
from typing import Any, Dict, List, Literal, Optional, Union
from pyModbusTCP.client import ModbusClient
from pyModbusTCP.utils import decode_ieee, encode_ieee, get_2comp
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

    def __init__(self, address: int, size: int, default_value: Any) -> None:
        # args
        self.address = address
        self.size = size
        self.default_value = default_value


class _TablesGroup:
    def __init__(self) -> None:
        # private
        # list of all tables to be shedule by io thread loop
        self._schedule_l: List[_Table] = list()
        # global address dict = concatenation of all subset tables address dict
        self._address_d: Dict[int, _Table.Data] = dict()

    def __len__(self):
        return len(self._address_d)

    @property
    def address_d(self):
        return self._address_d

    def schedule(self, modbus_table: _Table):
        self._schedule_l.append(modbus_table)
        for iter_addr in range(modbus_table.address, modbus_table.address + modbus_table.size):
            self._address_d[iter_addr] = _Table.Data(value=modbus_table.default_value, error=True)

    def unschedule(self, modbus_table: _Table):
        # this unschedule current mobdus_table from io thread loop
        # keep _address_d unchanged since tag and io thread can still access it
        try:
            self._schedule_l.remove(modbus_table)
        except ValueError:
            pass

    def as_list(self) -> List[_Table]:
        return self._schedule_l.copy()

    def have_table(self, at_address: int, size: int = 1) -> bool:
        for offset in range(size):
            if not at_address + offset in self._address_d:
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

    def __repr__(self):
        return f'{self.__class__.__name__}(device={self.device!r}, address={self.address!r}, ' \
               f'd_inputs={self.d_inputs!r}, write={self.write!r})'

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if type(tag.first_value) is not bool:
            logger.warning(msg=f'first_value type should be bool in {tag}')

    def get(self) -> Optional[bool]:
        with self._tables_group as tg:
            return tg.address_d[self.address].value

    def set(self, value: bool) -> None:
        if self.write:
            with self._tables_group as tg:
                tg.address_d[self.address].value = value
        else:
            raise ValueError(f'cannot write read-only {self!r}')

    def error(self) -> bool:
        with self._tables_group as tg:
            return tg.address_d[self.address].error


class ModbusInt(DataSource):
    def __init__(self, device: "ModbusTCPDevice", address: int, i_regs: bool = False,
                 bit_length: Literal[16, 32, 64, 128] = 16, signed: bool = False, swap_word: bool = False,
                 write: bool = False) -> None:
        # args
        self.device = device
        self.address = address
        self.i_regs = i_regs
        self.bit_length = bit_length
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

    def __repr__(self):
        return f'{self.__class__.__name__}(device={self.device!r}, address={self.address!r}, write={self.write!r}, ' \
               f'i_regs={self.i_regs!r})'

    @property
    def reg_nb(self):
        return self.bit_length//16 + (1 if self.bit_length % 16 else 0)

    def _apply_signed(self, value: Optional[int]) -> Optional[int]:
        if value is not None:
            return get_2comp(value, val_size=self.bit_length) if self.signed else value
        else:
            return

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if type(tag.first_value) is not int:
            logger.warning(msg=f'first_value type should be int in {tag}')

    def get(self) -> Optional[int]:
        # read register(s) into table
        regs_l: List[int] = []
        with self._tables_group as tg:
            for offest in range(self.reg_nb):
                regs_l.append(tg.address_d[self.address + offest].value)
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
        return int.from_bytes(value_as_b, byteorder='big', signed=self.signed)

    def set(self, value: int) -> None:
        # check write status
        if not self.write:
            raise ValueError(f'cannot write read-only {self!r}')
        # convert to bytearray:
        # - check strange value status (negative for unsigned, ...)
        # - apply 2's complement if requested
        try:
            value_b = bytearray(value.to_bytes(2*self.reg_nb, byteorder='big', signed=self.signed))
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
                tg.address_d[self.address + offset].value = reg_value

    def error(self) -> bool:
        with self._tables_group as tg:
            return tg.address_d[self.address].error


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

            # read coils space
            with self.r_coils_tables as tg:
                cp_coils_tables_l = tg.as_list()
            #  iterate over a safe list of tables
            for coils_table in cp_coils_tables_l:
                # modbus request
                try:
                    with self.safe_cli as cli:
                        reg_list = cli.read_coils(coils_table.address, coils_table.size)
                    # process result
                    with self.r_coils_tables as tg:
                        if reg_list:
                            # on success
                            for offset, reg in enumerate(reg_list):
                                tg.address_d[coils_table.address+offset].value = reg
                                tg.address_d[coils_table.address+offset].error = False
                        else:
                            # on error
                            for iter_addr in range(coils_table.address, coils_table.address + coils_table.size):
                                tg.address_d[iter_addr].error = True
                except ValueError as e:
                    logger.warning(f'error in read_io_thread (coils): {e}')

            # read discrete inputs
            with self.r_d_inps_tables as tg:
                cp_d_inputs_tables_l = tg.as_list()
            # iterate over a safe list of tables
            for d_input_table in cp_d_inputs_tables_l:
                # modbus request
                try:
                    with self.safe_cli as cli:
                        reg_list = cli.read_discrete_inputs(d_input_table.address, d_input_table.size)
                    # process result
                    with self.r_d_inps_tables as tg:
                        if reg_list:
                            # on success
                            for offset, reg in enumerate(reg_list):
                                tg.address_d[d_input_table.address+offset].value = reg
                                tg.address_d[d_input_table.address+offset].error = False
                        else:
                            # on error
                            for iter_addr in range(d_input_table.address, d_input_table.address + d_input_table.size):
                                tg.address_d[iter_addr].error = True
                except ValueError as e:
                    logger.warning(f'error in read_io_thread (discrete_inputs): {e}')

            # read discrete inputs
            with self.r_h_regs_tables as tg:
                cp_h_registers_tables_l = tg.as_list()
            # iterate over a safe list of tables
            for h_regs_table in cp_h_registers_tables_l:
                # modbus request
                try:
                    with self.safe_cli as cli:
                        reg_list = cli.read_holding_registers(h_regs_table.address, h_regs_table.size)
                    # process result
                    with self.r_h_regs_tables as tg:
                        if reg_list:
                            # on success
                            for offset, reg in enumerate(reg_list):
                                tg.address_d[h_regs_table.address+offset].value = reg
                                tg.address_d[h_regs_table.address+offset].error = False
                        else:
                            # on error
                            for iter_addr in range(h_regs_table.address, h_regs_table.address + h_regs_table.size):
                                tg.address_d[iter_addr].error = True
                except ValueError as e:
                    logger.warning(f'error in read_io_thread (holding_registers): {e}')

            # wait before next polling
            time.sleep(self.read_refresh)

    def _write_io_thread(self):
        """ Process every write I/O. """
        while True:

            # write coils space
            with self.w_coils_tables as tg:
                cp_coils_tables_l = tg.as_list()
            # iterate over a safe list of tables
            for table in cp_coils_tables_l:
                # format values to write
                values_l = []
                with self.w_coils_tables as tg:
                    for iter_addr in range(table.address, table.address + table.size):
                        values_l.append(tg.address_d[iter_addr].value)
                # modbus request
                try:
                    with self.safe_cli as cli:
                        if len(values_l) == 1:
                            write_ok = cli.write_single_coil(table.address, values_l[0])
                        else:
                            write_ok = cli.write_multiple_coils(table.address, values_l)
                    # process result
                    with self.w_coils_tables as tg:
                        # update error flag
                        for iter_addr in range(table.address, table.address + table.size):
                            tg.address_d[iter_addr].error = not write_ok
                except ValueError as e:
                    logger.warning(f'error in write_io_thread (coils): {e}')

            # write holding registers
            with self.w_h_regs_tables as tg:
                cp_h_regs_tables_l = tg.as_list()
            # iterate over a safe list of tables
            for table in cp_h_regs_tables_l:
                # format values to write
                values_l = []
                with self.w_h_regs_tables as tg:
                    for iter_addr in range(table.address, table.address + table.size):
                        values_l.append(tg.address_d[iter_addr].value)
                # modbus request
                try:
                    with self.safe_cli as cli:
                        if len(values_l) == 1:
                            write_ok = cli.write_single_register(table.address, values_l[0])
                        else:
                            write_ok = cli.write_multiple_registers(table.address, values_l)
                    # process result
                    with self.w_h_regs_tables as tg:
                        # update error flag
                        for iter_addr in range(table.address, table.address + table.size):
                            tg.address_d[iter_addr].error = not write_ok
                except ValueError as e:
                    logger.warning(f'error in write_io_thread (holding_registers): {e}')

            # wait before next polling
            time.sleep(self.write_refresh)

    def add_read_bits_table(self, address: int, size: int = 1, d_inputs: bool = False):
        # select tables group
        if d_inputs:
            tables_group = self.r_d_inps_tables
        else:
            tables_group = self.r_coils_tables
        # init table
        table = _Table(address=address, size=size, default_value=None)
        # link it to table group
        with tables_group as tg:
            tg.schedule(table)
        return table

    def add_write_bits_table(self, address: int, size: int = 1, default_value: bool = False):
        # init table
        table = _Table(address=address, size=size, default_value=default_value)
        # link it to table group
        with self.w_coils_tables as tg:
            tg.schedule(table)
        return table

    def add_read_regs_table(self, address: int, size: int = 1, i_regs: bool = False):
        # select tables group
        if i_regs:
            tables_group = self.r_i_regs_tables
        else:
            tables_group = self.r_h_regs_tables
        # init table
        table = _Table(address=address, size=size, default_value=None)
        # link it to table group
        with tables_group as tg:
            tg.schedule(table)
        return table

    def add_write_regs_table(self, address: int, size: int = 1, default_value: int = 0):
        # init table
        table = _Table(address=address, size=size, default_value=default_value)
        # link it to table group
        with self.w_h_regs_tables as tg:
            tg.schedule(table)
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
