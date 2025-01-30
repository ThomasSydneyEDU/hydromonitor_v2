import serial
import serial.tools.list_ports
import time

def find_arduino_port():
    """Automatically detects the correct Arduino port by scanning available serial ports."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "Arduino" in port.description or "ttyACM" in port.device:
            return port.device
    return None  # No Arduino found

def connect_to_arduino():
    """Attempts to connect to the Arduino, retrying every 5 seconds if necessary."""
    while True:
        arduino_port = find_arduino_port()
        if arduino_port:
            try:
                arduino = serial.Serial(arduino_port, 9600, timeout=2)
                time.sleep(2)  # Allow time for Arduino to initialize
                print(f"✅ Connected to Arduino on {arduino_port}")
                return arduino
            except serial.SerialException:
                print(f"⚠ Error connecting to {arduino_port}. Retrying...")
        else:
            print("🔍 No Arduino found. Retrying in 5 seconds...")
        
        time.sleep(5)  # Retry after 5 seconds

def send_command_to_arduino(arduino, command):
    """Send a command to the Arduino via serial connection."""
    if arduino and arduino.is_open:
        try:
            arduino.write(command.encode())
            print(f"📤 Sent command to Arduino: {command.strip()}")
        except Exception as e:
            print(f"⚠ Error sending command to Arduino: {e}")
    else:
        print(f"❌ Arduino not connected. Command not sent: {command.strip()}")

def check_arduino_connection(arduino):
    """Returns True if the Arduino is connected, False otherwise."""
    try:
        if arduino and arduino.is_open:
            arduino.write(b"PING\n")
            time.sleep(0.1)  # Allow response time
            if arduino.in_waiting > 0:
                response = arduino.readline().decode().strip()
                return response == "PING_OK"
    except Exception:
        return False
    return False