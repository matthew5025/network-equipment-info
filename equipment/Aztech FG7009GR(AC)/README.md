# Aztech FG7009GR(AC)
## General Information
CPU: BCM63139  
NAND: Spansion S34ML01G (131072KB)  
RAM: 256MB  
Firmware Version: 339.6.2-011  
Software Version: V4.16L.02A  
Bootloader (CFE) Version: 1.0.38-116.174  
This is a SingTel specific SKU. The generic version is known as the Aztech FG7008GR(AC)

## Board Photo
![Photo of the PCB](board_photo.jpg)

## UART Information
![Photo of UART Pins](uart_pinout.jpg)
Look for the jumper headers labeled J7.  
Starting from the pin closest to the J7 label and moving right  
1. Ground
2. Rx
3. Tx
4. 3.3v

The serial connenection has a baud rate of 115200bps.  
A login is required to access the serial console.  
Username: admin  
Password: last 4 digits of the S/N + last 4 char of the MAC Address  
Example:  
- Serial Number: 1234567891011
- MAC Address: 0a:0b:0c:0d:0e
- Password: 10110D0E

## SingTel Login Page
You may visit http://192.168.1.254/singtel for a more comprehensive settings page.  
Username: admin  
Password: H3ll0t3ch