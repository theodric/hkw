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
import logging
from typing import Optional


class HKWClock:
    """Class to handle communication with HKW PC - Funkuhr radio clock receiver."""
    
    def __init__(self, device: str = "/dev/ttyUSB0", baudrate: int = 300, verbose: bool = True):
        """
        Initialize the HKW clock connection.
        
        Args:
            device: Serial device path (default: /dev/ttyUSB0)
            baudrate: Baud rate for serial communication (default: 300)
            verbose: Enable verbose logging (default: True)
        """
        self.device = device
        self.baudrate = baudrate
        self.verbose = verbose
        self.serial_conn: Optional[serial.Serial] = None
        
        # Set up logging
        if self.verbose:
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(sys.stderr)
                ]
            )
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.WARNING)
        
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
        
        self.logger.info(f"Initializing HKWClock with device={device}, baudrate={baudrate}")
        
        # Set up signal handler for timeout
        self.logger.debug("Setting up signal handler for SIGALRM")
        signal.signal(signal.SIGALRM, self._signal_handler)
        self.logger.debug("Signal handler registered successfully")
    
    def _signal_handler(self, signum: int, frame) -> None:
        """Handle timeout signal."""
        self.logger.error(f"TIMEOUT SIGNAL RECEIVED: signum={signum}")
        self.logger.error(f"Signal frame: {frame}")
        self.logger.error("This usually means the serial communication timed out")
        if self.serial_conn:
            self.logger.error(f"Serial connection status: {self.serial_conn.is_open}")
            self.logger.error(f"Serial port: {self.serial_conn.port}")
        print(f"signal exit, signum={signum}", file=sys.stderr)
        sys.exit(1)
    
    def _sleep_10ms(self) -> None:
        """Sleep for 10 milliseconds."""
        self.logger.debug("Sleeping for 10ms")
        time.sleep(0.01)
    
    def open_clock(self) -> bool:
        """
        Open serial connection to the clock.
        
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Attempting to open serial connection to {self.device}")
        self.logger.debug(f"Serial parameters: baudrate={self.baudrate}, 8N2, timeout=1s")
        
        try:
            self.logger.debug("Creating serial.Serial object")
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
            
            self.logger.info(f"Serial connection opened successfully")
            self.logger.debug(f"Serial port details: {self.serial_conn}")
            self.logger.debug(f"Port open: {self.serial_conn.is_open}")
            self.logger.debug(f"Port name: {self.serial_conn.name}")
            self.logger.debug(f"Baudrate: {self.serial_conn.baudrate}")
            self.logger.debug(f"Timeout: {self.serial_conn.timeout}")
            
            return True
            
        except serial.SerialException as e:
            self.logger.error(f'Failed to open "{self.device}": {e}')
            self.logger.error(f"Error type: {type(e).__name__}")
            self.logger.error(f"Error details: {str(e)}")
            print(f'open of "{self.device}" failed: {e}', file=sys.stderr)
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error opening serial port: {e}")
            self.logger.error(f"Error type: {type(e).__name__}")
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
            self.logger.error("Cannot write: no serial connection")
            return 0
        
        self.logger.info(f"Writing message to clock: {repr(message)}")
        self.logger.debug(f"Message length: {len(message)} characters")
        
        written = 0
        for i, char in enumerate(message):
            try:
                self.logger.debug(f"Writing character {i+1}/{len(message)}: {repr(char)}")
                bytes_written = self.serial_conn.write(char.encode('ascii'))
                self.logger.debug(f"Bytes written: {bytes_written}")
                
                # Read one character back (echo)
                self.logger.debug("Reading echo character")
                echo = self.serial_conn.read(1)
                self.logger.debug(f"Echo received: {repr(echo)}")
                
                self._sleep_10ms()
                written += 1
                self.logger.debug(f"Character {i+1} written successfully")
                
            except serial.SerialException as e:
                self.logger.error(f"Serial error writing character {i+1}: {e}")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error writing character {i+1}: {e}")
                break
        
        self.logger.info(f"Write operation completed: {written}/{len(message)} characters written")
        return written
    
    def read_clock(self) -> str:
        """
        Read response from the clock until carriage return.
        
        Returns:
            Response string
        """
        if not self.serial_conn:
            self.logger.error("Cannot read: no serial connection")
            return ""
        
        self.logger.info("Starting to read response from clock")
        response = ""
        char_count = 0
        
        while True:
            try:
                self.logger.debug(f"Reading character {char_count + 1}")
                char = self.serial_conn.read(1)
                
                if not char:
                    self.logger.warning("No character received (timeout or empty)")
                    break
                
                char_str = char.decode('ascii')
                self.logger.debug(f"Character {char_count + 1} received: {repr(char_str)}")
                response += char_str
                char_count += 1
                
                if char_str == '\r':
                    self.logger.info("Carriage return received, stopping read")
                    break
                    
            except serial.SerialException as e:
                self.logger.error(f"Serial error reading character {char_count + 1}: {e}")
                break
            except UnicodeDecodeError as e:
                self.logger.error(f"Unicode decode error reading character {char_count + 1}: {e}")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error reading character {char_count + 1}: {e}")
                break
        
        self.logger.info(f"Read operation completed: {len(response)} characters received")
        self.logger.debug(f"Full response: {repr(response)}")
        return response
    
    def check_valid(self, time_data: str) -> bool:
        """
        Validate the time data format.
        
        Args:
            time_data: Time data string from clock
            
        Returns:
            True if valid, False otherwise
        """
        self.logger.info(f"Validating time data: {repr(time_data)}")
        self.logger.debug(f"Time data length: {len(time_data)}")
        
        if len(time_data) < 16:
            self.logger.error(f"Time data too short: expected 16, got {len(time_data)}")
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
        
        field_names = [
            "hour_tens", "hour_ones", "minute_tens", "minute_ones",
            "second_tens", "second_ones", "weekday", "day_tens",
            "day_ones", "month_tens", "month_ones", "year_tens",
            "year_ones", "utc_flag", "status", "carriage_return"
        ]
        
        for i, (check, field_name) in enumerate(zip(checks, field_names)):
            if i >= len(time_data):
                self.logger.error(f"Field {i} ({field_name}): index out of range")
                return False
            
            char = time_data[i]
            is_valid = check(char)
            self.logger.debug(f"Field {i} ({field_name}): char={repr(char)}, valid={is_valid}")
            
            if not is_valid:
                self.logger.error(f"Field {i} ({field_name}): validation failed for char {repr(char)}")
                return False
        
        self.logger.info("Time data validation passed")
        return True
    
    def display_result(self, time_data: str) -> int:
        """
        Display the parsed time data.
        
        Args:
            time_data: Time data string from clock
            
        Returns:
            0 if valid, 1 if invalid
        """
        self.logger.info("Displaying time data results")
        
        if len(time_data) < 16:
            self.logger.error(f"Invalid time data length: {len(time_data)}")
            print("Invalid time data length", file=sys.stderr)
            return 1
        
        # Extract time components
        time_str = f"{time_data[0]}{time_data[1]}:{time_data[2]}{time_data[3]}:{time_data[4]}{time_data[5]}"
        self.logger.debug(f"Extracted time: {time_str}")
        
        # Extract date components
        weekday_idx = ord(time_data[6]) - ord('0') - 1
        weekday = self.weekdays[weekday_idx] if 0 <= weekday_idx < len(self.weekdays) else "unknown"
        date_str = f"20{time_data[11]}{time_data[12]}-{time_data[9]}{time_data[10]}-{time_data[7]}{time_data[8]}"
        self.logger.debug(f"Extracted date: {weekday} {date_str}")
        self.logger.debug(f"Weekday index: {weekday_idx}, weekday name: {weekday}")
        
        # Extract flags
        utc_flag_value = ord(time_data[13])
        time_format = "UTC" if utc_flag_value & 0x4 else "MET"
        self.logger.debug(f"UTC flag value: {utc_flag_value} (0x{utc_flag_value:02x}), time format: {time_format}")
        
        status_value = ord(time_data[14])
        low_battery = "yes" if status_value & 0x8 else "no"
        self.logger.debug(f"Status value: {status_value} (0x{status_value:02x}), low battery: {low_battery}")
        
        valid_bit_value = ord(time_data[15])
        valid_bit = "" if valid_bit_value & 1 else "in"
        self.logger.debug(f"Valid bit value: {valid_bit_value} (0x{valid_bit_value:02x}), valid: {valid_bit == ''}")
        
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
            self.logger.info("Closing serial connection")
            try:
                self.serial_conn.close()
                self.logger.debug("Serial connection closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing serial connection: {e}")
        else:
            self.logger.debug("No serial connection to close")
    
    def get_time(self) -> int:
        """
        Get time from the clock.
        
        Returns:
            0 if successful, 1 if failed
        """
        self.logger.info("Starting get_time operation")
        
        if not self.open_clock():
            self.logger.error("Failed to open clock connection")
            return 1
        
        try:
            # Set 3-second timeout
            self.logger.info("Setting 3-second alarm timeout")
            signal.alarm(3)
            
            # Send command to get time
            self.logger.info("Sending 'o\\r' command to clock")
            written = self.write_clock("o\r")
            
            if written != 2:
                self.logger.error(f"Failed to write command: expected 2 bytes, wrote {written}")
                print(f"Failed to write command, wrote {written} bytes", file=sys.stderr)
                return 1
            
            # Read response
            self.logger.info("Reading response from clock")
            response = self.read_clock()
            
            # Cancel timeout
            self.logger.info("Cancelling alarm timeout")
            signal.alarm(0)
            
            if len(response) != 16:
                self.logger.error(f"Invalid response length: expected 16 bytes, got {len(response)}")
                print(f"expected 16 bytes, got {len(response)}", file=sys.stderr)
                return 1
            
            self.logger.info("Processing time data")
            return self.display_result(response)
            
        except Exception as e:
            self.logger.error(f"Unexpected error in get_time: {e}")
            self.logger.error(f"Error type: {type(e).__name__}")
            return 1
        finally:
            self.logger.info("Cleaning up resources")
            self.close()


def main() -> int:
    """Main function."""
    print("HKW PC - Funkuhr Python Client", file=sys.stderr)
    print("Verbose mode enabled - showing all operations", file=sys.stderr)
    print("-" * 50, file=sys.stderr)
    
    clock = HKWClock(verbose=True)
    result = clock.get_time()
    
    print("-" * 50, file=sys.stderr)
    print(f"Program completed with exit code: {result}", file=sys.stderr)
    
    return result


if __name__ == "__main__":
    sys.exit(main()) 