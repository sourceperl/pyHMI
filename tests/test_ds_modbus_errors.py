""" Test of every DS_ModbusTCP DataSource subclass """

import pytest
from pyHMI.DS_ModbusTCP import ModbusTCPDevice, ModbusBool, ModbusInt, ModbusFloat


class FakeConf:
    md = ModbusTCPDevice(port=5020)
    r_bits_req = md.add_read_bits_request(0, size=16)
    r_regs_req = md.add_read_regs_request(0, size=16)
    w_bits_req = md.add_write_bits_request(0, size=16)
    w_regs_req = md.add_write_regs_request(0, size=16)


def test_errors_requests():
    """ Test requests errors """
    # === should raise exception ===
    # for over-sized request
    # read bits
    for d_inputs in [False, True]:
        with pytest.raises(ValueError):
            FakeConf.md.add_read_bits_request(0x10000, size=1, d_inputs=d_inputs)
        with pytest.raises(ValueError):
            FakeConf.md.add_read_bits_request(0xffff, size=2, d_inputs=d_inputs)
        with pytest.raises(ValueError):
            FakeConf.md.add_read_bits_request(0, size=2001, d_inputs=d_inputs)
    # read regs
    for i_regs in [False, True]:
        with pytest.raises(ValueError):
            FakeConf.md.add_read_regs_request(0x10000, size=1, i_regs=i_regs)
        with pytest.raises(ValueError):
            FakeConf.md.add_read_regs_request(0xffff, size=2, i_regs=i_regs)
        with pytest.raises(ValueError):
            FakeConf.md.add_read_regs_request(0, size=126, i_regs=i_regs)
    # write bits
    with pytest.raises(ValueError):
        FakeConf.md.add_write_bits_request(0x10000, size=1)
    with pytest.raises(ValueError):
        FakeConf.md.add_write_bits_request(0xffff, size=2)
    with pytest.raises(ValueError):
        FakeConf.md.add_write_bits_request(0, size=1969)
    # write regs
    with pytest.raises(ValueError):
        FakeConf.md.add_write_regs_request(0x10000, size=1)
    with pytest.raises(ValueError):
        FakeConf.md.add_write_regs_request(0xffff, size=2)
    with pytest.raises(ValueError):
        FakeConf.md.add_write_regs_request(0, size=124)


def test_errors_modbus_bool():
    """ Test ModbusBool errors """
    # === shouldn't raise exception ===
    # for good request type
    for req in [FakeConf.r_bits_req, FakeConf.w_bits_req]:
        ModbusBool(req, 0)
    # for writing a well-typed value
    ModbusBool(FakeConf.w_bits_req, 0).set(False)
    ModbusBool(FakeConf.w_bits_req, 0).set(True)

    # === should raise exception ===
    # for bad request type
    for req in [FakeConf.r_regs_req, FakeConf.w_regs_req]:
        with pytest.raises(TypeError):
            ModbusBool(req, 0)
    # for writing on read-only
    with pytest.raises(TypeError):
        ModbusBool(FakeConf.r_bits_req, 0).set(False)
    # for write an unsupported value type
    with pytest.raises(TypeError):
        ModbusBool(FakeConf.w_bits_req, 0).set('oops')  # type: ignore


def test_errors_modbus_int():
    """ Test ModbusInt errors """
    # === shouldn't raise exception ===
    # for good request type
    for req in [FakeConf.r_regs_req, FakeConf.w_regs_req]:
        ModbusInt(req, 0)
    # for write a well-typed value with a valid range
    for bit_length in [16, 32, 64, 128]:
        ModbusInt(FakeConf.w_regs_req, 0, bit_length=bit_length, signed=True).set(-1)
        ModbusInt(FakeConf.w_regs_req, 0, bit_length=bit_length, signed=False).set(2**bit_length-1)
        ModbusInt(FakeConf.w_regs_req, 0, bit_length=bit_length, signed=False).set(2**bit_length-1)
        ModbusInt(FakeConf.w_regs_req, 0, bit_length=bit_length, signed=False).set(2**bit_length-1)

    # === should raise exception ===
    # for bad request type
    for req in [FakeConf.r_bits_req, FakeConf.w_bits_req]:
        with pytest.raises(TypeError):
            ModbusInt(req, 0)
    # for writing on read-only
    with pytest.raises(TypeError):
        ModbusInt(FakeConf.r_regs_req, 0).set(False)
    # for write an unsupported value type
    with pytest.raises(TypeError):
        ModbusInt(FakeConf.w_regs_req, 0, bit_length=bit_length, signed=True).set('oops')  # type: ignore
    # for writing an overrange value
    for bit_length in [16, 32, 64, 128]:
        with pytest.raises(ValueError):
            ModbusInt(FakeConf.w_regs_req, 0, bit_length=bit_length, signed=True).set(2**bit_length//2)
        with pytest.raises(ValueError):
            ModbusInt(FakeConf.w_regs_req, 0, bit_length=bit_length, signed=False).set(2**bit_length)
        with pytest.raises(ValueError):
            ModbusInt(FakeConf.w_regs_req, 0, bit_length=bit_length, signed=False).set(2**bit_length)
        with pytest.raises(ValueError):
            ModbusInt(FakeConf.w_regs_req, 0, bit_length=bit_length, signed=False).set(2**bit_length)
    # for unsupported option value: bit_length
    with pytest.raises(ValueError):
        ModbusFloat(FakeConf.w_regs_req, 0, byte_order='bug')  # type: ignore


def test_errors_modbus_float():
    """ Test ModbusFloat errors """
    # === shouldn't raise exception ===
    # for good request type
    for req in [FakeConf.r_regs_req, FakeConf.w_regs_req]:
        ModbusFloat(req, 0)
    # for write a well-typed value
    ModbusFloat(FakeConf.w_regs_req, 0).set(0.0)

    # === should raise exception ===
    # for bad request type
    for req in [FakeConf.r_bits_req, FakeConf.w_bits_req]:
        with pytest.raises(TypeError):
            ModbusInt(req, 0)
    # for writing on read-only
    with pytest.raises(TypeError):
        ModbusFloat(FakeConf.r_regs_req, 0).set(0.0)
    # for write an unsupported value type
    with pytest.raises(TypeError):
        ModbusFloat(FakeConf.w_regs_req, 0).set('oops')  # type: ignore
    # for writing an overrange value
    with pytest.raises(ValueError):
        ModbusFloat(FakeConf.w_regs_req, 0, bit_length=32).set(999.9e99)
    # for unsupported option value: bit_length
    with pytest.raises(ValueError):
        ModbusFloat(FakeConf.w_regs_req, 0, bit_length=128)
