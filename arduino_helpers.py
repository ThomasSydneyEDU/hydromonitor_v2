import serial
import time

def connect_to_arduino(port, baud_rate):
    """Attempt to connect to the Arduino on the specified port and baud rate."""
    try:
        arduino = serial.Serial(port, baud_rate, timeout=2)
        time.sleep(2)  # Wait for the Arduino to initialize
        print("Connected to Arduino.")
        return arduino
    except Exception as e:
        print(f"Error connecting to Arduino: {e}")
        return None

def send_command_to_arduino(arduino, command):
    """Send a command to the Arduino via serial connection."""
    if arduino:
        try:
            arduino.write(command.encode())
            print(f"Sent command to Arduino: {command.strip()}")
        except Exception as e:
            print(f"Error sending command to Arduino: {e}")
    else:
        print(f"Arduino not connected. Command not sent: {command.strip()}")