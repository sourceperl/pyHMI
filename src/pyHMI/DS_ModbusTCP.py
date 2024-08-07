from collections import defaultdict
from queue import Queue, Full
import threading
import time
from typing import Any, Dict, List, Optional, Union
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
#   - holding registers (0x03)
#       Read Multiple Holding Registers 3
#       Write Single Holding Register 6
#       Write Multiple Holding Registers 16
#
#   - input registers (0x04) read-only
#       Read Input Registers 4


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


class _TableGroup:
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

    def have_table(self, at_address: int) -> bool:
        return at_address in self._address_d


class ModbusReadCoils(DataSource):
    def __init__(self, device: "ModbusTCPDevice", address: int) -> None:
        # args
        self.device = device
        self.address = address
        # check table exist at device level
        with self.device.r_coils_tables as t:
            if not t.have_table(at_address=address):
                raise ValueError(f'@{self.address} have no table define on {self.device}')

    def __repr__(self):
        return f'{self.__class__.__name__}(device={self.device!r}, address={self.address!r})'

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if type(tag.first_value) is not bool:
            logger.warning(msg=f'first_value type should be bool in {tag}')

    def get(self) -> Optional[bool]:
        with self.device.r_coils_tables as tg:
            return tg.address_d[self.address].value

    def set(self, _value: bool) -> None:
        raise ValueError(f'cannot write read-only {self!r}')

    def error(self) -> bool:
        with self.device.r_coils_tables as tg:
            return tg.address_d[self.address].error


class ModbusWriteCoils(DataSource):
    def __init__(self, device: "ModbusTCPDevice", address: int) -> None:
        # args
        self.device = device
        self.address = address
        # check table exist at device level
        with self.device.w_coils_tables as t:
            if not t.have_table(at_address=address):
                raise ValueError(f'@{self.address} have no table define on {self.device}')

    def __repr__(self):
        return f'{self.__class__.__name__}(device={self.device!r}, address={self.address!r})'

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if type(tag.first_value) is not bool:
            logger.warning(msg=f'first_value type should be bool in {tag}')

    def get(self) -> Optional[bool]:
        with self.device.w_coils_tables as tg:
            return tg.address_d[self.address].value

    def set(self, value: bool) -> None:
        with self.device.w_coils_tables as tg:
            tg.address_d[self.address].value = value

    def error(self) -> bool:
        with self.device.w_coils_tables as tg:
            return tg.address_d[self.address].error


class ModbusReadDiscreteInputs(DataSource):
    def __init__(self, device: "ModbusTCPDevice", address: int) -> None:
        # args
        self.device = device
        self.address = address
        # check table exist at device level
        with self.device.r_d_inps_tables as t:
            if not t.have_table(at_address=address):
                raise ValueError(f'@{self.address} have no table define on {self.device}')

    def __repr__(self):
        return f'{self.__class__.__name__}(device={self.device!r}, address={self.address!r})'

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if type(tag.first_value) is not bool:
            logger.warning(msg=f'first_value type should be bool in {tag}')

    def get(self) -> Optional[bool]:
        with self.device.r_d_inps_tables as tg:
            return tg.address_d[self.address].value

    def set(self, _value: bool) -> None:
        raise ValueError(f'cannot write read-only {self!r}')

    def error(self) -> bool:
        with self.device.r_d_inps_tables as tg:
            return tg.address_d[self.address].error


class ModbusReadHoldingRegs(DataSource):
    def __init__(self, device: "ModbusTCPDevice", address: int) -> None:
        # args
        self.device = device
        self.address = address
        # check table exist at device level
        with self.device.r_h_regs_tables as tg:
            if not tg.have_table(at_address=address):
                raise ValueError(f'@{self.address} have no table define on {self.device}')

    def __repr__(self):
        return f'{self.__class__.__name__}(device={self.device!r}, address={self.address!r})'

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if type(tag.first_value) is not int:
            logger.warning(msg=f'first_value type should be int in {tag}')

    def get(self) -> Optional[bool]:
        with self.device.r_h_regs_tables as tg:
            return tg.address_d[self.address].value

    def set(self, _value: bool) -> None:
        raise ValueError(f'cannot write read-only {self!r}')

    def error(self) -> bool:
        with self.device.r_h_regs_tables as tg:
            return tg.address_d[self.address].error


class ModbusWriteHoldingRegs(DataSource):
    def __init__(self, device: "ModbusTCPDevice", address: int) -> None:
        # args
        self.device = device
        self.address = address
        # check table exist at device level
        with self.device.w_h_regs_tables as tg:
            if not tg.have_table(at_address=address):
                raise ValueError(f'@{self.address} have no table define on {self.device}')

    def __repr__(self):
        return f'{self.__class__.__name__}(device={self.device!r}, address={self.address!r})'

    def add_tag(self, tag: Tag) -> None:
        # warn user of type mismatch between initial tag value and this datasource
        if type(tag.first_value) is not int:
            logger.warning(msg=f'first_value type should be int in {tag}')

    def get(self) -> Optional[bool]:
        with self.device.w_h_regs_tables as tg:
            return tg.address_d[self.address].value

    def set(self, value: int) -> None:
        with self.device.w_h_regs_tables as tg:
            tg.address_d[self.address].value = value

    def error(self) -> bool:
        with self.device.w_h_regs_tables as tg:
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
        self.r_coils_tables = SafeObject(_TableGroup())
        self.r_d_inps_tables = SafeObject(_TableGroup())
        self.r_h_regs_tables = SafeObject(_TableGroup())

        self.w_coils_tables = SafeObject(_TableGroup())
        self.w_h_regs_tables = SafeObject(_TableGroup())
        # privates vars
        self._one_shot_q = Queue(maxsize=5)

        self._r_words_d = defaultdict(dict)
        self._r_longs_d = defaultdict(dict)
        self._r_floats_d = defaultdict(dict)
        self._read_requests_l = SafeObject(list())
        self._write_requests_l = SafeObject(list())

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

    def add_read_coils_table(self, address: int, size: int = 1):
        table = _Table(address=address, size=size, default_value=False)
        with self.r_coils_tables as tg:
            tg.schedule(table)
        return table

    def add_write_coils_table(self, address: int, size: int = 1, default_value=False):
        table = _Table(address=address, size=size, default_value=default_value)
        with self.w_coils_tables as tg:
            tg.schedule(table)
        return table

    def add_read_h_regs_table(self, address: int, size: int = 1):
        table = _Table(address=address, size=size, default_value=0)
        with self.r_h_regs_tables as tg:
            tg.schedule(table)
        return table

    def add_write_h_regs_table(self, address: int, size: int = 1, default_value=0):
        table = _Table(address=address, size=size, default_value=default_value)
        with self.w_h_regs_tables as tg:
            tg.schedule(table)
        return table

    def add_longs_table(self, addr: int, size: int = 1, use_f4: bool = False, swap_word: bool = False):
        # init longs table with default value
        # with self._thread_lock:
        for offset in range(0, size):
            self._r_longs_d[addr + offset * 2] = {'long': 0, 'err': True}
        # add long table to read buffer
        with self._read_requests_l as l:
            l.append({'type': 'long', 'addr': addr, 'size': size, 'use_f4': use_f4, 'swap_word': swap_word})

    def add_floats_table(self, addr: int, size: int = 1, use_f4: bool = False, swap_word: bool = False):
        # init words table with default value
        # with self._thread_lock:
        for offset in range(0, size):
            self._r_floats_d[addr + offset * 2] = {'float': 0.0, 'err': True}
        # add float table to read buffer
        with self._read_requests_l as l:
            l.append({'type': 'float', 'addr': addr, 'size': size, 'use_f4': use_f4, 'swap_word': swap_word})

    def write_coils(self, address: int, value: bool) -> bool:
        # schedules the write operation
        try:
            self._one_shot_q.put(_OneShotWriteRequest(where='coils', address=address, value=value), block=False)
            return True
        except Full:
            return False

    def write_word(self, address: int, value: int):
        # schedules the write operation
        try:
            self._one_shot_q.put(_OneShotWriteRequest(where='h_registers', address=address, value=value), block=False)
            return True
        except Full:
            return False

    def write_float(self, address: int, value: float, swap_word: bool = False):
        # schedules the write operation
        try:
            self._one_shot_q.put(_OneShotWriteRequest(where='float', address=address, value=value), block=False)
            return True
        except Full:
            return False
