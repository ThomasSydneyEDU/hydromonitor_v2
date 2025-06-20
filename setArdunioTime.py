import serial
import time
from datetime import datetime

# Update this with your actual serial port
SERIAL_PORT = '/dev/tty.usbmodem1101'  # Mac
# SERIAL_PORT = 'COM4'  # Windows
BAUD_RATE = 9600

# Wait for Arduino to reboot after upload
time.sleep(2)

# Get current time
now = datetime.now()
formatted_time = now.strftime('%H:%M:%S')
command = f'SET_TIME:{formatted_time}\n'

print(f'Sending: {command.strip()}')

# Send to Arduino
with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as ser:
    ser.write(command.encode())
    time.sleep(0.5)
    response = ser.read_all().decode()
    print("Response from Arduino:", response)