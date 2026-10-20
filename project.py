import sys
import os
import csv
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def parse_hex_line(line_str):
    """Parse a single line from an Intel HEX file and validate standard checksum."""
    line = line_str.strip()
    if not line.startswith(":"):
        return {"valid": False, "error": "NOT_A_HEX_LINE"}

    try:
        byte_count = int(line[1:3], 16)
        address = int(line[3:7], 16)
        record_type = int(line[7:9], 16)
        data_hex = line[9:9 + (byte_count * 2)]
        checksum = int(line[9 + (byte_count * 2):11 + (byte_count * 2)], 16)

        sum_bytes = byte_count + (address >> 8) + (address & 0xFF) + record_type
        for i in range(0, len(data_hex), 2):
            sum_bytes += int(data_hex[i:i+2], 16)

        calc_checksum = (-sum_bytes) & 0xFF
        is_valid = (calc_checksum == checksum)

        return {
            "valid": is_valid,
            "byte_count": byte_count,
            "address": address,
            "record_type": record_type,
            "data": data_hex,
            "checksum": checksum
        }
    except Exception:
        return {"valid": False, "error": "PARSE_ERROR"}


def analyze_hex_firmware(hex_filepath, max_flash_kb=512):
    """Analyze full Intel HEX file footprint and check target Flash bounds."""
    if not os.path.exists(hex_filepath):
        return {"error": "FILE_NOT_FOUND"}

    total_bytes = 0
    lines_count = 0
    valid_lines = 0
    max_address = 0

    with open(hex_filepath, "r") as f:
        for line in f:
            lines_count += 1
            res = parse_hex_line(line)
            if res.get("valid"):
                valid_lines += 1
                if res["record_type"] == 0:  # Data record
                    total_bytes += res["byte_count"]
                    current_end = res["address"] + res["byte_count"]
                    if current_end > max_address:
                        max_address = current_end

    max_flash_bytes = max_flash_kb * 1024
    overflow = max_address > max_flash_bytes

    return {
        "total_lines": lines_count,
        "valid_lines": valid_lines,
        "firmware_size_bytes": total_bytes,
        "max_address_reached": hex(max_address),
        "flash_limit_kb": max_flash_kb,
        "memory_overflow": overflow
    }


def calculate_crc16_modbus(payload_str):
    """Compute standard CRC16 Modbus checksum."""
    crc = 0xFFFF
    for char in payload_str:
        crc ^= ord(char)
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    swapped = ((crc & 0xFF) << 8) | ((crc >> 8) & 0xFF)
    return f"0x{swapped:04X}"


def validate_serial_frame(raw_line, delimiter=","):
    """Validate incoming raw serial log frames and verify checksum."""
    if not raw_line or not isinstance(raw_line, str):
        return {"valid": False, "reason": "EMPTY"}

    parts = [p.strip() for p in raw_line.strip().split(delimiter)]
    if len(parts) < 4:
        return {"valid": False, "reason": "INVALID_FRAME_FORMAT", "raw": raw_line.strip()}

    timestamp, device_id, payload, expected_crc = parts[0], parts[1], parts[2], parts[3]
    calc_crc = calculate_crc16_modbus(payload)

    
    is_pass = (calc_crc.upper() == expected_crc.upper())

    return {
        "valid": is_pass,
        "timestamp": timestamp,
        "device_id": device_id,
        "payload": payload,
        "expected_crc": expected_crc,
        "calculated_crc": calc_crc
    }


def process_serial_log_stream(log_filepath):
    """Process serial log file and evaluate link health metrics."""
    if not os.path.exists(log_filepath):
        return {}

    history = []
    with open(log_filepath, "r") as f:
        for line in f:
            if line.strip():
                history.append(validate_serial_frame(line))

    total = len(history)
    if total == 0:
        return {"total": 0, "valid_count": 0, "loss_rate": 0.0, "health_score": 100.0}

    valid_cnt = sum(1 for item in history if item.get("valid"))
    corrupted_cnt = total - valid_cnt

    return {
        "total": total,
        "valid_count": valid_cnt,
        "corrupted_count": corrupted_cnt,
        "loss_rate": round((corrupted_cnt / total) * 100, 2),
        "health_score": round((valid_cnt / total) * 100, 2),
        "details": history
    }


def calculate_usart_baud_setting(sys_clock_hz, target_baud):
    """Calculate hardware USART divider register settings and percentage error."""
    if sys_clock_hz <= 0 or target_baud <= 0:
        return {"error": "INVALID_INPUT"}

    usart_div = sys_clock_hz / (16 * target_baud)
    mantissa = int(usart_div)
    fraction = round((usart_div - mantissa) * 16)

    if fraction == 16:
        mantissa += 1
        fraction = 0

    actual_baud = sys_clock_hz / (16 * (mantissa + (fraction / 16)))
    error_percentage = abs((actual_baud - target_baud) / target_baud) * 100

    return {
        "target_baud": target_baud,
        "system_clock_mhz": sys_clock_hz / 1e6,
        "usart_div": round(usart_div, 4),
        "mantissa": mantissa,
        "fraction": fraction,
        "actual_baud": round(actual_baud, 2),
        "error_percentage": round(error_percentage, 3)
    }


def export_to_csv(data_list, output_filename="report.csv"):
    """Export dataset to structured CSV file."""
    if not data_list:
        return False
    keys = data_list[0].keys()
    with open(output_filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data_list)
    return True


def generate_pdf_report(summary_dict, output_filename="Embedded_Toolkit_Report.pdf"):
    """Generate formal engineering PDF summary report."""
    c = canvas.Canvas(output_filename, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Embedded Engineering Toolkit - Summary Report")

    c.setFont("Helvetica", 10)
    c.drawString(100, 735, "Generated automatically by CS50P Final Project Tool")
    c.line(100, 725, 500, 725)

    y = 690
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y, "1. Firmware Analysis (Intel HEX):")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(120, y, f"Total Lines Processed: {summary_dict.get('hex_total_lines', 'N/A')}")
    y -= 15
    c.drawString(120, y, f"Firmware Size: {summary_dict.get('hex_size_bytes', 'N/A')} Bytes")
    y -= 15
    c.drawString(120, y, f"Memory Overflow Warning: {summary_dict.get('hex_overflow', 'N/A')}")

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y, "2. Serial Communication Health:")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(120, y, f"Total Packets Checked: {summary_dict.get('serial_total', 'N/A')}")
    y -= 15
    c.drawString(120, y, f"Packet Loss Rate: {summary_dict.get('serial_loss_rate', 'N/A')}%")
    y -= 15
    c.drawString(120, y, f"System Health Score: {summary_dict.get('serial_health_score', 'N/A')}%")

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y, "3. Hardware Baud Rate Config:")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(120, y, f"Target Baud: {summary_dict.get('baud_target', 'N/A')}")
    y -= 15
    c.drawString(120, y, f"Calculated Error: {summary_dict.get('baud_error', 'N/A')}%")

    c.save()
    return True


def show_menu():
    print("\n==================================================")
    print("      EMBEDDED SYSTEMS ENGINEERING TOOLKIT       ")
    print("==================================================")
    print("1. Parse Intel HEX Firmware & Check Memory Bounds")
    print("2. Analyze Serial Hardware Logs & CRC16 Modbus")
    print("3. Calculate Hardware Baud Rate Register Values")
    print("4. Generate Full PDF & CSV Engineering Report")
    print("5. Exit")
    print("==================================================")


def main():
    report_summary = {}

    
    if not os.path.exists("firmware.hex"):
        with open("firmware.hex", "w") as f:
            f.write(":1000000021000000000000000000000000000000CF\n")
            f.write(":1000100000080020170000081B0000081D00000851\n")
            f.write(":00000001FF\n")

    
    if not os.path.exists("serial.log"):
        with open("serial.log", "w") as f:
            f.write("12:00:01, DEV01, Temp:25C, 0xC302\n")
            f.write("12:00:02, DEV01, Temp:26C, 0xC3F2\n")
            f.write("12:00:03, DEV01, Temp:27C, 0xC262\n")

    while True:
        show_menu()
        try:
            choice = input("Select an option (1-5): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting. Goodbye!")
            break

        if choice == "1":
            print("\n--- [Intel HEX Firmware Analyzer] ---")
            res = analyze_hex_firmware("firmware.hex", max_flash_kb=512)
            print(f"Total Lines: {res['total_lines']}")
            print(f"Firmware Size: {res['firmware_size_bytes']} Bytes")
            print(f"Max Address: {res['max_address_reached']}")
            print(f"Memory Overflow: {res['memory_overflow']}")

            report_summary["hex_total_lines"] = res["total_lines"]
            report_summary["hex_size_bytes"] = res["firmware_size_bytes"]
            report_summary["hex_overflow"] = res["memory_overflow"]

        elif choice == "2":
            print("\n--- [Serial Protocol & CRC16 Analyzer] ---")
            res = process_serial_log_stream("serial.log")
            print(f"Total Packets: {res['total']}")
            print(f"Valid Packets: {res['valid_count']}")
            print(f"Packet Loss Rate: {res['loss_rate']}%")
            print(f"Health Score: {res['health_score']}%")

            report_summary["serial_total"] = res["total"]
            report_summary["serial_loss_rate"] = res["loss_rate"]
            report_summary["serial_health_score"] = res["health_score"]

            if res.get("details"):
                export_to_csv(res["details"], "serial_analysis.csv")
                print("Exported detailed serial log to 'serial_analysis.csv'")

        elif choice == "3":
            print("\n--- [Baud Rate Register Calculator] ---")
            try:
                clk_input = input("Enter System Clock Frequency in MHz (e.g. 16, 72): ")
                baud_input = input("Enter Target Baud Rate (e.g. 9600, 115200): ")
                clk = float(clk_input) * 1e6
                baud = int(baud_input)
                
                calc = calculate_usart_baud_setting(clk, baud)
                
                if "error" in calc:
                     print(f"Error: {calc['error']}")
                else:
                     print(f"Mantissa: {calc['mantissa']} | Fraction: {calc['fraction']}")
                     print(f"Actual Baud: {calc['actual_baud']} | Error: {calc['error_percentage']}%")

                     report_summary["baud_target"] = baud
                     report_summary["baud_error"] = calc["error_percentage"]
            except (ValueError, EOFError, KeyboardInterrupt):
                print("Invalid input numbers!")

        elif choice == "4":
            print("\n--- [Generating Reports] ---")
            if generate_pdf_report(report_summary, "Embedded_Toolkit_Report.pdf"):
                print("PDF Engineering Report generated: 'Embedded_Toolkit_Report.pdf'")
            else:
                print("Failed to generate PDF report.")

        elif choice == "5":
            print("\nExiting Embedded Toolkit. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid option! Please select 1-5.")


if __name__ == "__main__":
    main()
