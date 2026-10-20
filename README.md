**Embedded Systems Engineering Toolkit**  
Video Demo : [https://youtu.be/ubifp5qjpJc](https://youtu.be/ubifp5qjpJc "https://youtu.be/ubifp5qjpJc")  
**Description**  
Embedded Systems Engineering Toolkit is a Python command-line  
   
 application created as a CS50P final project.  
The project provides several practical tools related to embedded systems  
   
 engineering and serial communication.  
The program can analyze Intel HEX firmware files, validate serial  
   
 communication frames using CRC16 Modbus, calculate USART baud-rate  
   
 settings, export serial analysis results to CSV, and generate a PDF  
   
 engineering report.  
**Features**  
**1. Intel HEX Firmware Analyzer**  
The firmware analyzer reads an Intel HEX file and checks:  
- Total number of lines  
- Valid HEX records  
- Firmware size in bytes  
- Maximum memory address reached  
- Whether the firmware exceeds the configured Flash memory limit  
The default Flash memory limit is 512 KB.  
**2. Serial Protocol and CRC16 Analyzer**  
The serial analyzer processes communication frames from serial.log.  
Each frame contains:  
- Timestamp  
- Device ID  
- Payload  
- Expected CRC  
The program calculates a CRC16 Modbus checksum for the payload and  
   
 compares it with the expected CRC.  
The analyzer reports:  
- Total packets  
- Valid packets  
- Corrupted packets  
- Packet loss rate  
- System health score  
Detailed serial analysis results can also be exported to:  
serial_analysis.csv  
**3. USART Baud Rate Calculator**  
The baud-rate calculator determines USART register values from:  
- System clock frequency  
- Target baud rate  
It calculates:  
- USART divider  
- Mantissa  
- Fraction  
- Actual baud rate  
- Percentage error  
Invalid input values are handled without crashing the program.  
**4. PDF Engineering Report**  
The program can generate a summary engineering report in PDF format.  
The generated report is:  
Embedded_Toolkit_Report.pdf  
The report contains summaries of:  
- Firmware analysis  
- Serial communication health  
- Baud-rate configuration  
**How to Run**  
Create a virtual environment:  
python3 -m venv venv  
   
Activate the virtual environment:  
source venv/bin/activate  
   
Install the required packages:  
pip install -r requirements.txt  
   
Run the program:  
python3 project.py  
   
**Program Menu**  
When the program starts, it provides five options:  
1. Parse Intel HEX Firmware & Check Memory Bounds  
2. Analyze Serial Hardware Logs & CRC16 Modbus  
3. Calculate Hardware Baud Rate Register Values  
4. Generate Full PDF & CSV Engineering Report  
5. Exit  
**Testing**  
The project includes automated tests in test_project.py.  
Run the tests with:  
pytest -q  
   
The tests cover important parts of the application, including:  
- Intel HEX parsing  
- HEX checksum validation  
- CRC16 Modbus calculation  
- Serial frame validation  
- Invalid serial frame handling  
- USART baud-rate calculation  
- Invalid baud-rate input handling  
**Example**  
For a system clock of 16 MHz and a target baud rate of 9600, the program  
   
 produces:  
Mantissa: 104  
 Fraction: 3  
 Actual Baud: 9598.08  
 Error: 0.02%  
   
**Output Files**  
The program can create the following files:  
- serial_analysis.csv - Detailed serial communication analysis  
- Embedded_Toolkit_Report.pdf - Engineering summary report  
The project also uses:  
- firmware.hex - Intel HEX firmware input  
- serial.log - Serial communication log input  
- config.json - Project configuration file  
**Project Structure**  
final_project/  
 ├── project.py  
 ├── test_project.py  
 ├── requirements.txt  
 ├── config.json  
 ├── firmware.hex  
 ├── serial.log  
 ├── serial_analysis.csv  
 └── Embedded_Toolkit_Report.pdf  
   
**Dependencies**  
The project uses Python and the following packages:  
- pytest - automated testing  
- reportlab - PDF report generation  
**Author**  
CS50P Final Project  
