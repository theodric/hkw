#!/usr/bin/env python3
import serial
import time

def check_valid(t):
    if (t[0] in '012' and
        t[1].isdigit() and
        t[2] in '012345' and
        t[3].isdigit() and
        t[4] in '012345' and
        t[5].isdigit() and
        t[6] in '1234567' and
        t[7] in '0123' and
        t[8].isdigit() and
        t[9] in '01' and
        t[10].isdigit() and
        t[11].isdigit() and
        t[12].isdigit() and
        True and  # CHECK_UTC always true
        (ord(t[14]) & 1) and
        t[15] == '\r'):
        return True
    return False

def parse_response(t):
    weekdays = ["Monday", "Tuesday", "Wednestay", "Thurstay", "Saturday", "Sunday"]
    try:
        hour = t[0:2]
        minute = t[2:4]
        second = t[4:6]
        weekday = weekdays[int(t[6]) - 1] if t[6] in '1234567' else "unknown"
        day = t[7:9]
        month = t[9:11]
        year = "20" + t[11:13]
        time_format = "UTC" if (ord(t[13]) & 0x4) else "MET"
        low_batt = "yes" if (ord(t[14]) & 0x8) else "no"
        valid_bit = (ord(t[15]) & 1)

        return {
            "time": f"{hour}:{minute}:{second}",
            "date": f"{year}-{month}-{day}",
            "weekday": weekday,
            "time_format": time_format,
            "low_battery": low_batt,
            "valid": valid_bit
        }
    except Exception as e:
        return {"error": str(e)}

def main():
    ser = serial.Serial('/dev/ttyS1', baudrate=300, bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_TWO, timeout=1)

    ser.write(b'o\r')
    time.sleep(0.1)
    response = ser.read(16).decode('ascii', errors='ignore')

    if len(response) != 16:
        print(f"expected 16 bytes, got {len(response)}")
        return

    if check_valid(response):
        parsed = parse_response(response)
        for k,v in parsed.items():
            print(f"{k}: {v}")
    else:
        print("invalid response")

if __name__ == "__main__":
    main()
