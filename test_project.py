import pytest
from project import (
    parse_hex_line,
    calculate_crc16_modbus,
    validate_serial_frame,
    calculate_usart_baud_setting,
)


def test_parse_hex_line():
    
    valid_line = ":1000000021000000000000000000000000000000CF"
    result = parse_hex_line(valid_line)

    assert result["valid"] is True
    assert result["byte_count"] == 16
    assert result["address"] == 0
    assert result["record_type"] == 0

    invalid_checksum = ":1000000021000000000000000000000000000000FF"
    result = parse_hex_line(invalid_checksum)

    assert result["valid"] is False

    invalid_format = "1000000021000000000000000000000000000000CF"
    result = parse_hex_line(invalid_format)

    assert result["valid"] is False
    assert result["error"] == "NOT_A_HEX_LINE"
    result = parse_hex_line("")

    assert result["valid"] is False


def test_calculate_crc16_modbus():
    result = calculate_crc16_modbus("Temp:25C")

    assert isinstance(result, str)
    assert result.startswith("0x")
    assert result.upper() == "0XC302"
    
    different_result = calculate_crc16_modbus("Temp:26C")

    assert different_result != result


def test_validate_serial_frame():
    valid_frame = "12:00:01, DEV01, Temp:25C, 0xC302"
    result = validate_serial_frame(valid_frame)

    assert result["valid"] is True
    assert result["timestamp"] == "12:00:01"
    assert result["device_id"] == "DEV01"
    assert result["payload"] == "Temp:25C"

    
    invalid_crc = "12:00:01, DEV01, Temp:25C, 0x0000"
    result = validate_serial_frame(invalid_crc)

    assert result["valid"] is False
    assert result["calculated_crc"] == "0xC302"

    
    incomplete_frame = "12:00:01, DEV01, Temp:25C"
    result = validate_serial_frame(incomplete_frame)

    assert result["valid"] is False
    assert result["reason"] == "INVALID_FRAME_FORMAT"

    
    result = validate_serial_frame("")

    assert result["valid"] is False
    assert result["reason"] == "EMPTY"


def test_calculate_usart_baud_setting():
    result = calculate_usart_baud_setting(16e6, 9600)

    assert result["target_baud"] == 9600
    assert result["system_clock_mhz"] == 16
    assert result["mantissa"] == 104
    assert result["fraction"] == 3
    assert result["actual_baud"] == 9598.08
    assert result["error_percentage"] < 0.5

    result = calculate_usart_baud_setting(-1, 9600)

    assert "error" in result
    assert result["error"] == "INVALID_INPUT"

    result = calculate_usart_baud_setting(16e6, 0)

    assert "error" in result
    assert result["error"] == "INVALID_INPUT"

    result = calculate_usart_baud_setting(0, 0)

    assert "error" in result
