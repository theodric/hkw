# HKW PC - Funkuhr Python Client

This is a modern Python 3 refactoring of the original C program for accessing the HKW PC - Funkuhr radio clock receiver.

## Overview

The HKW PC - Funkuhr is a radio clock receiver that can be accessed via serial communication. This Python version provides the same functionality as the original C program but with modern Python 3 features and better error handling.

## Features

- Serial communication with HKW PC - Funkuhr receiver
- Time and date parsing from radio clock signals
- Validation of received data
- Support for both UTC and MET time formats
- Battery status monitoring
- Signal quality validation

## Requirements

- Python 3.6 or higher
- pyserial library
- Access to a serial port (typically `/dev/ttyUSB0` on Linux/macOS)

## Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure your HKW PC - Funkuhr receiver is connected to a USB port and recognized as a serial device.

## Usage

### Basic Usage

```bash
python hkw.py
```

This will attempt to connect to `/dev/ttyUSB0` and retrieve the current time from the radio clock.

### Programmatic Usage

```python
from hkw import HKWClock

# Create clock instance
clock = HKWClock(device="/dev/ttyUSB0", baudrate=300)

# Get time
result = clock.get_time()
if result == 0:
    print("Successfully retrieved time")
else:
    print("Failed to retrieve time")
```

### Custom Device

If your receiver is connected to a different port:

```python
clock = HKWClock(device="/dev/ttyUSB1")  # Different USB port
```

## Output Format

The program outputs time information in the following format:

```
Time: HH:MM:SS
Date: Weekday YYYY-MM-DD
Time format: UTC|MET
Low Battery: yes|no
Valid-Bit  : information is valid|invalid
Check-ok   : information looks ok|bad
```

## Error Handling

The program includes comprehensive error handling for:
- Serial port connection failures
- Timeout conditions (3-second timeout)
- Invalid data format
- Communication errors

## Differences from Original C Version

1. **Object-oriented design**: Uses a class-based approach for better organization
2. **Type hints**: Includes Python type annotations for better code clarity
3. **Better error handling**: More robust exception handling
4. **Fixed typos**: Corrected weekday names ("Wednesday", "Thursday", added "Friday")
5. **Modern Python features**: Uses f-strings, context managers, and other Python 3 features
6. **Cross-platform**: Works on Linux, macOS, and Windows (with appropriate serial port names)

## Troubleshooting

### Permission Issues

If you get permission errors accessing the serial port:

```bash
sudo chmod 666 /dev/ttyUSB0
```

Or add your user to the dialout group:

```bash
sudo usermod -a -G dialout $USER
```

### Device Not Found

If the device is not found, check:
1. The device is properly connected
2. The correct device path is being used
3. The device has proper permissions

### Timeout Issues

If the program times out, it may indicate:
1. The receiver is not receiving a signal
2. The serial connection is not properly configured
3. The device is not responding

## License

This refactored version maintains the original GPL license from the 1996 C program by St. Traby.
