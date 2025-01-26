import tkinter as tk
import serial
import time
import threading
from datetime import datetime

# Define serial port and baud rate
SERIAL_PORT = "/dev/ttyACM0"  # Adjust if needed
BAUD_RATE = 9600

class HydroponicsGUI:
    def __init__(self, root, arduino):
        self.root = root
        self.arduino = arduino
        self.root.title("Hydroponics System Control")
        self.root.geometry("800x480")  # Set resolution to match Raspberry Pi touchscreen
        self.root.attributes("-fullscreen", True)  # Enable fullscreen mode

        # Main frame to organize layout
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Left frame for manual controls (switches and lights)
        self.left_frame = tk.Frame(self.main_frame, width=400, padx=20, pady=20)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right frame for time, schedule toggle, and temperature
        self.right_frame = tk.Frame(self.main_frame, width=400, padx=20, pady=20)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Temperature display
        self.temperature_label = tk.Label(
            self.right_frame, text="Temperature: -- °C | -- °F", font=("Helvetica", 20)
        )
        self.temperature_label.pack(pady=20, anchor="center")

        # Start temperature updates
        self.update_temperature()

    def update_temperature(self):
        """Request and update the temperature every 30 seconds."""
        def fetch_temperature():
            try:
                self.arduino.write(b"GET_TEMP\n")
                print("Sent command: GET_TEMP")
                time.sleep(2)  # Wait for Arduino to respond
                if self.arduino.in_waiting > 0:
                    response = self.arduino.readline()
                    try:
                        response = response.decode('utf-8', errors='replace').strip()
                        print(f"Arduino response: {response}")  # Debugging output
                        if response.startswith("Temperature: "):
                            temp_data = response.replace("Temperature: ", "").split(" | ")
                            if len(temp_data) == 2:  # Ensure valid response format
                                self.temperature_label.config(text=f"Temperature: {temp_data[0]} | {temp_data[1]}")
                    except Exception as decode_error:
                        print(f"Decode error: {decode_error}")
            except Exception as e:
                print(f"Error fetching temperature: {e}")

        threading.Thread(target=fetch_temperature, daemon=True).start()
        self.root.after(30000, self.update_temperature)  # Schedule next update in 30 seconds


def main():
    try:
        arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        time.sleep(2)  # Wait for Arduino to initialize
        print("Connected to Arduino.")
    except Exception as e:
        print(f"Error connecting to Arduino: {e}")
        return

    root = tk.Tk()
    app = HydroponicsGUI(root, arduino)
    root.mainloop()
    arduino.close()


if __name__ == "__main__":
    main()
