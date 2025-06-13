#!/usr/bin/env python3
"""
This program shows how to access the HKW PC - Funkuhr.
The receiver is also supported by xntpd.
(c) 1996 by St. Traby, GPL
Refactored to Python 3
"""

import serial
import time
import signal
import sys
from typing import Optional


class HKWClock:
    """Class to handle communication with HKW PC - Funkuhr radio clock receiver."""
    
    def __init__(self, device: str = "/dev/ttyUSB0", baudrate: int = 300):
        """
        Initialize the HKW clock connection.
        
        Args:
            device: Serial device path (default: /dev/ttyUSB0)
            baudrate: Baud rate for serial communication (default: 300)
        """
        self.device = device
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None
        
        # Weekday names (note: original had typos, corrected here)
        self.weekdays = [
            "Monday",
            "Tuesday", 
            "Wednesday",  # Fixed typo from "Wednestay"
            "Thursday",   # Fixed typo from "Thurstay"
            "Friday",     # Added missing Friday
            "Saturday",
            "Sunday"
        ]
        
        # Set up signal handler for timeout
        signal.signal(signal.SIGALRM, self._signal_handler)
    
    def _signal_handler(self, signum: int, frame) -> None:
        """Handle timeout signal."""
        print(f"signal exit, signum={signum}", file=sys.stderr)
        sys.exit(1)
    
    def _sleep_10ms(self) -> None:
        """Sleep for 10 milliseconds."""
        time.sleep(0.01)
    
    def open_clock(self) -> bool:
        """
        Open serial connection to the clock.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.serial_conn = serial.Serial(
                port=self.device,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_TWO,
                timeout=1,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            return True
        except serial.SerialException as e:
            print(f'open of "{self.device}" failed: {e}', file=sys.stderr)
            return False
    
    def write_clock(self, message: str) -> int:
        """
        Write a message to the clock.
        
        Args:
            message: Message to send
            
        Returns:
            Number of characters written
        """
        if not self.serial_conn:
            return 0
            
        written = 0
        for char in message:
            try:
                self.serial_conn.write(char.encode('ascii'))
                # Read one character back (echo)
                self.serial_conn.read(1)
                self._sleep_10ms()
                written += 1
            except serial.SerialException:
                break
        return written
    
    def read_clock(self) -> str:
        """
        Read response from the clock until carriage return.
        
        Returns:
            Response string
        """
        if not self.serial_conn:
            return ""
            
        response = ""
        while True:
            try:
                char = self.serial_conn.read(1).decode('ascii')
                if not char:
                    break
                response += char
                if char == '\r':
                    break
            except serial.SerialException:
                break
        return response
    
    def check_valid(self, time_data: str) -> bool:
        """
        Validate the time data format.
        
        Args:
            time_data: Time data string from clock
            
        Returns:
            True if valid, False otherwise
        """
        if len(time_data) < 16:
            return False
            
        # Check each character position according to original validation
        checks = [
            lambda x: '0' <= x <= '2',      # t[0] - hour tens
            lambda x: '0' <= x <= '9',      # t[1] - hour ones
            lambda x: '0' <= x <= '5',      # t[2] - minute tens
            lambda x: '0' <= x <= '9',      # t[3] - minute ones
            lambda x: '0' <= x <= '5',      # t[4] - second tens
            lambda x: '0' <= x <= '9',      # t[5] - second ones
            lambda x: '1' <= x <= '7',      # t[6] - weekday
            lambda x: '0' <= x <= '3',      # t[7] - day tens
            lambda x: '0' <= x <= '9',      # t[8] - day ones
            lambda x: '0' <= x <= '1',      # t[9] - month tens
            lambda x: '0' <= x <= '9',      # t[10] - month ones
            lambda x: '0' <= x <= '9',      # t[11] - year tens
            lambda x: '0' <= x <= '9',      # t[12] - year ones
            lambda x: True,                 # t[13] - UTC flag (always valid)
            lambda x: bool(ord(x) & 1),     # t[14] - status
            lambda x: x == '\r'             # t[15] - carriage return
        ]
        
        for i, check in enumerate(checks):
            if i >= len(time_data) or not check(time_data[i]):
                return False
        return True
    
    def display_result(self, time_data: str) -> int:
        """
        Display the parsed time data.
        
        Args:
            time_data: Time data string from clock
            
        Returns:
            0 if valid, 1 if invalid
        """
        if len(time_data) < 16:
            print("Invalid time data length", file=sys.stderr)
            return 1
        
        # Extract time components
        time_str = f"{time_data[0]}{time_data[1]}:{time_data[2]}{time_data[3]}:{time_data[4]}{time_data[5]}"
        
        # Extract date components
        weekday_idx = ord(time_data[6]) - ord('0') - 1
        weekday = self.weekdays[weekday_idx] if 0 <= weekday_idx < len(self.weekdays) else "unknown"
        date_str = f"20{time_data[11]}{time_data[12]}-{time_data[9]}{time_data[10]}-{time_data[7]}{time_data[8]}"
        
        # Extract flags
        time_format = "UTC" if ord(time_data[13]) & 0x4 else "MET"
        low_battery = "yes" if ord(time_data[14]) & 0x8 else "no"
        valid_bit = "" if ord(time_data[15]) & 1 else "in"
        
        # Display results
        print(f"Time: {time_str}")
        print(f"Date: {weekday} {date_str}")
        print(f"Time format: {time_format}")
        print(f"Low Battery: {low_battery}")
        print(f"Valid-Bit  : information is {valid_bit}valid", file=sys.stderr)
        
        # Check validity
        is_valid = self.check_valid(time_data)
        print(f"Check-ok   : information looks {'ok' if is_valid else 'bad'}", file=sys.stderr)
        
        return 0 if is_valid else 1
    
    def close(self) -> None:
        """Close the serial connection."""
        if self.serial_conn:
            self.serial_conn.close()
    
    def get_time(self) -> int:
        """
        Get time from the clock.
        
        Returns:
            0 if successful, 1 if failed
        """
        if not self.open_clock():
            return 1
        
        try:
            # Set 3-second timeout
            signal.alarm(3)
            
            # Send command to get time
            written = self.write_clock("o\r")
            if written != 2:
                print(f"Failed to write command, wrote {written} bytes", file=sys.stderr)
                return 1
            
            # Read response
            response = self.read_clock()
            
            # Cancel timeout
            signal.alarm(0)
            
            if len(response) != 16:
                print(f"expected 16 bytes, got {len(response)}", file=sys.stderr)
                return 1
            
            return self.display_result(response)
            
        finally:
            self.close()


def main() -> int:
    """Main function."""
    clock = HKWClock()
    return clock.get_time()


if __name__ == "__main__":
    sys.exit(main()) 