import serial
from typing import List
import binascii


def read_serial_to_empty(ser: serial.Serial) -> List[bytes]:
    result = []
    while True:
        r_line = ser.readline()
        if r_line:
            result.append(r_line)
        else:
            break

    return result


def parse_help(com_result: List[bytes]) -> bool:
    if not com_result:
        print('No response from serial device!')
        raise AssertionError('No response from serial device!')

    last_line: str = com_result[-1].decode(errors='ignore')
    if last_line != 'CFE> ':
        print('Did not detect CFE environment!')
        print(f'Got {last_line}')
        raise AssertionError('Did not detect CFE environment!')

    for byte_line in com_result:
        response: str = byte_line.decode(errors='ignore')
        if response.startswith('dn') and 'Dump NAND contents along with spare area' in response:
            return True
    else:
        print('Did not find the expected dn command!')
        return False


def parse_dn(com_result: List[bytes]) -> bytearray:
    is_valid_block = False
    prev_address = None
    bytes_result = bytearray()
    for com_line in com_result:
        line = com_line.decode(errors='ignore').rstrip('\r\n')
        if line.isspace() or not line:
            continue
        if not is_valid_block:
            if '------------------ block: ' in line:
                is_valid_block = True
                print(line)
                continue
        else:
            if '----------- spare area for ' in line:
                is_valid_block = False
                continue
            else:
                line = line.strip('\n')
                address, data = line.split(':', 1)

                if not len(address) == 8:
                    print("Invalid Address!")
                    print(line)
                    exit(0)

                curr_address = binascii.unhexlify(address)
                if prev_address is not None:
                    if int.from_bytes(prev_address, byteorder='big') + 16 \
                          != int.from_bytes(curr_address, byteorder='big'):
                        print()
                        print("Data parse error: Skipped one or more segments!")
                        print(f"Previous segment: {binascii.hexlify(prev_address)}, "
                              f"Current segment: {binascii.hexlify(curr_address)}")
                        print()
                        print(line)
                        return bytearray()
                    else:
                        prev_address = curr_address
                else:
                    prev_address = curr_address

                data_parser = data.split('    ', 1)

                if len(data_parser) != 2:
                    print()
                    print("Data parse error: Could not split data between hex and ASCII representations!")
                    print()
                    print(line)
                    return bytearray()

                if len(data_parser[1]) != 16:
                    print()
                    print("Data parse error: Invalid Number of ASCII interpreted characters!")
                    print(f"Expected 16, got {len(data_parser[1])}")
                    print()
                    print(line)
                    return bytearray()

                hex_data = data_parser[0].split(' ')
                if len(hex_data) != 5:
                    print()
                    print("Data parse error: Could not split hex data correctly!")
                    print(f"Expected 5 segments (empty first segment is valid), got {len(hex_data)}")
                    print()
                    print(hex_data)
                    print(line)
                    return bytearray()

                if hex_data[0] != '':
                    print()
                    print("Data parse error: Could not split hex data correctly!")
                    print(f"Expected empty first segment, got {str(hex_data[0])}")
                    print()
                    print(line)
                    return bytearray()

                for index, hex_segment in enumerate(hex_data[1:5]):
                    if len(hex_segment) != 8:
                        print()
                        print("Data parse error: Invalid hex segment!")
                        print(f"Expected 8 hex chars, got {len(hex_segment)}")
                        print()
                        print(line)
                        print(hex_segment)
                        return bytearray()

                    ascii_value = ''
                    hex_chars = [hex_segment[i:i+2] for i in range(0, len(hex_segment), 2)]
                    for hex_char in hex_chars:
                        char_byte = bytearray.fromhex(hex_char)
                        if 32 <= char_byte[0] <= 126:
                            ascii_value = ascii_value + str(char_byte, 'ascii')
                        else:
                            ascii_value = ascii_value + '.'
                    str_start_index = index * 4
                    str_end_index = str_start_index + 4
                    if ascii_value != data_parser[1][str_start_index:str_end_index]:
                        print()
                        print("Data parse error: ASCII and hex notations do not match!")
                        print(f"Expected {ascii_value}, got {data_parser[1][str_start_index:str_end_index]}")
                        print()
                        print(line)
                        print(hex_segment)
                        return bytearray()

                    bytes_result.extend(binascii.unhexlify(hex_segment))
    return bytes_result


if __name__ == "__main__":
    ser = serial.Serial('COM3', 115200, timeout=0.1)
    ser.write(b'\r\nhelp\r\n')
    ser.flush()

    if not parse_help(read_serial_to_empty(ser)):
        exit(-1)
    print('Found the dn command in CFE, proceeding to dump NAND contents')
    curr_address = 0
    page_step = 16
    end_of_nand = False

    while not end_of_nand:
        first_run = True

        if first_run:
            print(f'Retrieving {hex(curr_address)}')
            ser.write(f'dn {hex(curr_address)} {page_step}\r\n'.encode())
            ser.flush()
            dn_result = read_serial_to_empty(ser)
            if 'Attempt to read block number(' in dn_result[2].decode(errors='ignore'):
                print('Reached end of NAND')
                end_of_nand = True
                continue
            initial_result = parse_dn(dn_result)
            if initial_result:
                first_run = False
            else:
                print('Retrieval failed, will retry')

        if not first_run:
            print(f'Verifying {hex(curr_address)}')
            ser.write(f'dn {hex(curr_address)} {page_step}r\n'.encode())
            ser.flush()
            dn_result = read_serial_to_empty(ser)
            verify_result = parse_dn(dn_result)
            if verify_result != initial_result:
                print('Verification Failed, will retry.')
                first_run = True
                continue
            with open('full.dmp', 'ab+') as f:
                f.write(verify_result)
            first_addr = dn_result[2].decode().split(':')[0]
            second_addr = dn_result[3].decode().split(':')[0]
            last_addr = dn_result[-10].decode().split(':')[0]
            addr_difference = int(second_addr, 16) - int(first_addr, 16)
            curr_address = int(last_addr, 16) + addr_difference
            first_run = True

