import tkinter as tk
import serial
import time
import threading
from datetime import datetime

# Define serial port and baud rate
SERIAL_PORT = "/dev/ttyACM0"  # Arduino port
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

        # Manual controls on the left
        self.states = {
            "lights_top": False,
            "lights_bottom": False,
            "pump_top": False,
            "pump_bottom": False,
        }
        self.create_switch("Lights (Top)", 0, "lights_top", "LT")
        self.create_switch("Lights (Bottom)", 1, "lights_bottom", "LB")
        self.create_switch("Pump (Top)", 2, "pump_top", "PT")
        self.create_switch("Pump (Bottom)", 3, "pump_bottom", "PB")

        # Reset button
        self.create_reset_button()

        # Time display on the right
        self.clock_label = tk.Label(self.right_frame, text="", font=("Helvetica", 24))
        self.clock_label.pack(pady=20, anchor="center")

        # Temperature display
        self.temperature_label = tk.Label(
            self.right_frame, text="Temperature: -- °C | -- °F", font=("Helvetica", 20)
        )
        self.temperature_label.pack(pady=20, anchor="center")

        # Start clock and temperature updates
        self.update_clock()
        self.update_temperature()

        # Ensure all switches are OFF at startup
        self.initialize_switches()

    def create_switch(self, label_text, row, state_key, device_code):
        """Create a switch with a light indicator."""
        label = tk.Label(self.left_frame, text=label_text, font=("Helvetica", 18))
        label.grid(row=row, column=0, padx=10, pady=10, sticky="w")
        button = tk.Button(
            self.left_frame,
            text="OFF",
            font=("Helvetica", 18),
            bg="darkgrey",
            fg="white",
            width=10,
            command=lambda: self.toggle_state(state_key, button, light, device_code),
        )
        button.grid(row=row, column=1, padx=10, pady=10)
        light = tk.Canvas(self.left_frame, width=30, height=30, bg="red", highlightthickness=0)
        light.grid(row=row, column=2, padx=10, pady=10)
        self.states[state_key] = {"state": False, "button": button, "light": light, "device_code": device_code}

    def create_reset_button(self):
        """Create a reset button to turn off all switches."""
        reset_button = tk.Button(
            self.left_frame,
            text="Reset All",
            font=("Helvetica", 18),
            bg="red",
            fg="white",
            width=15,
            command=self.reset_all_switches,
        )
        reset_button.grid(row=4, column=0, columnspan=3, pady=20)

    def toggle_state(self, state_key, button, light, device_code):
        """Toggle the state, update the button and light, and send a command to the Arduino."""
        current_state = not self.states[state_key]["state"]
        self.states[state_key]["state"] = current_state
        if current_state:
            button.config(text="ON", bg="darkgreen")
            light.config(bg="green")
            self.send_command(device_code, "ON")
        else:
            button.config(text="OFF", bg="darkgrey")
            light.config(bg="red")
            self.send_command(device_code, "OFF")

    def send_command(self, device_code, state):
        """Send a command to the Arduino via serial."""
        command = f"{device_code}:{state}\n"
        print(f"Sending command: {command.strip()}")
        try:
            self.arduino.write(command.encode())
        except Exception as e:
            print(f"Error sending command to Arduino: {e}")

    def initialize_switches(self):
        """Ensure all switches are OFF at startup."""
        print("Initializing all switches to OFF...")
        for state_key, info in self.states.items():
            info["state"] = False
            info["button"].config(text="OFF", bg="darkgrey")
            info["light"].config(bg="red")
            self.send_command(info["device_code"], "OFF")

    def reset_all_switches(self):
        """Turn all switches off."""
        print("Resetting all switches to OFF...")
        self.initialize_switches()

    def update_clock(self):
        """Update the clock every second."""
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.clock_label.config(text=f"Current Time: {current_time}")
        self.root.after(1000, self.update_clock)

    def update_temperature(self):
        """Request and update the temperature every 30 seconds."""
        def fetch_temperature():
            try:
                self.arduino.write(b"GET_TEMP\n")
                time.sleep(1)  # Wait for Arduino to respond
                if self.arduino.in_waiting > 0:
                    response = self.arduino.readline().decode().strip()
                    if response.startswith("Temperature: "):
                        temp_data = response.replace("Temperature: ", "").split(" | ")
                        self.temperature_label.config(text=f"Temperature: {temp_data[0]} | {temp_data[1]}")
            except Exception as e:
                print(f"Error fetching temperature: {e}")

        threading.Thread(target=fetch_temperature, daemon=True).start()
        self.root.after(30000, self.update_temperature)  # Schedule next update in 30 seconds


def main():
    # Connect to Arduino
    try:
        arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)  # Wait for the Arduino to initialize
        print("Connected to Arduino.")
    except Exception as e:
        print(f"Error connecting to Arduino: {e}")
        return

    # Initialize GUI
    root = tk.Tk()
    app = HydroponicsGUI(root, arduino)
    root.mainloop()

    # Close the serial connection
    arduino.close()


if __name__ == "__main__":
    main()
