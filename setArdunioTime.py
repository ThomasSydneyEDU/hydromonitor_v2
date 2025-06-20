import serial
import time
from datetime import datetime

def connect_to_arduino():
    """Scan available ports and attempt to connect to the Arduino."""
    POSSIBLE_PORTS = ["/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/tty.usbmodem1101"]
    
    for port in POSSIBLE_PORTS:
        try:
            arduino = serial.Serial(port, 9600, timeout=2)
            time.sleep(2)  # Allow Arduino to reboot and settle
            print(f"✅ Connected to Arduino on {port}")
            return arduino
        except Exception:
            continue

    print("⚠ No Arduino found.")
    return None

def send_time_and_confirm():
    now = datetime.now()
    formatted_time = now.strftime('%H:%M:%S')
    command = f'SET_TIME:{formatted_time}\n'
    print(f'📤 Sending: {command.strip()}')

    arduino = connect_to_arduino()
    if not arduino:
        return

    try:
        arduino.reset_input_buffer()  # Clear stale data
        arduino.write(command.encode())
        timeout = time.time() + 5  # Wait up to 5 seconds for response

        while time.time() < timeout:
            if arduino.in_waiting > 0:
                response = arduino.readline().decode().strip()
                print(f"📩 Received: {response}")
                if response.startswith("TIME:"):
                    print("✅ Time confirmed by Arduino.")
                    break
        else:
            print("⏰ Timeout: No TIME confirmation received from Arduino.")

    except Exception as e:
        print(f"❌ Error communicating with Arduino: {e}")
    finally:
        arduino.close()

if __name__ == "__main__":
    send_time_and_confirm()