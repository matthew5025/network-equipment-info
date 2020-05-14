import binascii

with open('full.dmp', 'r') as f, open('full', 'wb+') as bf:
    is_valid_block = False
    prev_address = None
    for line in f:
        if line.isspace():
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
                        exit(0)
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
                    exit(0)

                if len(data_parser[1]) != 16:
                    print()
                    print("Data parse error: Invalid Number of ASCII interpreted characters!")
                    print(f"Expected 16, got {len(data_parser[1])}")
                    print()
                    print(line)
                    exit(0)

                hex_data = data_parser[0].split(' ')
                if len(hex_data) != 5:
                    print()
                    print("Data parse error: Could not split hex data correctly!")
                    print(f"Expected 5 segments (empty first segment is valid), got {len(hex_data)}")
                    print()
                    print(hex_data)
                    print(line)
                    exit(0)

                if hex_data[0] != '':
                    print()
                    print("Data parse error: Could not split hex data correctly!")
                    print(f"Expected empty first segment, got {str(hex_data[0])}")
                    print()
                    print(line)
                    exit(0)

                for index, hex_segment in enumerate(hex_data[1:5]):
                    if len(hex_segment) != 8:
                        print()
                        print("Data parse error: Invalid hex segment!")
                        print(f"Expected 8 hex chars, got {len(hex_segment)}")
                        print()
                        print(line)
                        print(hex_segment)
                        exit(0)

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
                        exit(0)

                    to_file = binascii.unhexlify(hex_segment)
                    bf.write(to_file)
