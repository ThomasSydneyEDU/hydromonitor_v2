import serial
import time
from datetime import datetime

def connect_to_arduino():
    """Scan available ports and attempt to connect to the Arduino."""
    POSSIBLE_PORTS = ["/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyUSB0", "/dev/ttyUSB1"]
    
    for port in POSSIBLE_PORTS:
        try:
            arduino = serial.Serial(port, 9600, timeout=2)
            time.sleep(2)  # Allow time for initialization
            print(f"✅ Connected to Arduino on {port}")
            return arduino
        except Exception:
            continue  # Try the next port

    print("⚠ No Arduino found.")
    return None

def send_command_to_arduino(arduino, command):
    """Send a command to the Arduino via serial connection."""
    if arduino:
        try:
            arduino.write(command.encode())
            print(f"📤 Sent command: {command.strip()}")
        except Exception as e:
            print(f"⚠ Error sending command: {e}")

def check_arduino_connection(arduino):
    """Check if the Arduino is still responding."""
    if not arduino:
        return False
    try:
        arduino.write(b"PING\n")
        time.sleep(0.1)
        if arduino.in_waiting > 0:
            response = arduino.readline().decode().strip()
            return response == "PING_OK"
    except Exception:
        return False
    return False

def set_time_on_arduino(arduino):
    """Send the current system time to the Arduino."""
    if arduino:
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            send_command_to_arduino(arduino, f"SET_TIME:{current_time}\n")
        except Exception as e:
            print(f"⚠ Error sending time to Arduino: {e}")

def reset_to_arduino_schedule(arduino):
    """Reset all devices to follow Arduino’s schedule."""
    if not arduino:
        print("⚠ Arduino is not connected. Cannot reset schedule.")
        return False
    print("🔄 Resetting to Arduino schedule...")
    send_command_to_arduino(arduino, "RESET_SCHEDULE\n")
    time.sleep(1)
    send_command_to_arduino(arduino, "GET_STATE\n")
    return True
