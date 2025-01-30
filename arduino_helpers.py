import serial
import time
import glob

def find_arduino(baud_rate=9600, timeout=2):
    """ Scan available ports and attempt to connect to an Arduino. """
    ports = glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')
    for port in ports:
        try:
            arduino = serial.Serial(port, baud_rate, timeout=timeout)
            time.sleep(2)  # Allow initialization
            print(f"Connected to Arduino on {port}")
            return arduino
        except Exception as e:
            print(f"Failed to connect on {port}: {e}")
    return None

def send_command_to_arduino(arduino, command):
    """ Send a command to the Arduino via serial connection. """
    if arduino and arduino.is_open:
        try:
            arduino.write(command.encode())
            print(f"Sent command: {command.strip()}")
        except Exception as e:
            print(f"Error sending command: {e}")
    else:
        print(f"Arduino not connected. Command not sent: {command.strip()}")