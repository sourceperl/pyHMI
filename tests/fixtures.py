import pytest
from pyModbusTCP.server import ModbusServer


@pytest.fixture
def modbus_srv():
    # setup code
    srv = ModbusServer(port=5020, no_block=True)
    srv.start()
    # pass to test functions
    yield srv
    # teardown code
    srv.stop()
