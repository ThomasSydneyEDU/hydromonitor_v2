import tkinter as tk
import serial
import time
import threading
from datetime import datetime, timedelta

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

        # Top frame for clock and Arduino connection indicator
        self.top_frame = tk.Frame(self.root, padx=20, pady=10)
        self.top_frame.pack(fill=tk.X, side=tk.TOP)

        # Clock display
        self.clock_label = tk.Label(self.top_frame, text="", font=("Helvetica", 24))
        self.clock_label.pack(side=tk.LEFT, padx=20)

        # Arduino connection indicator with label
        connection_frame = tk.Frame(self.top_frame)
        connection_frame.pack(side=tk.RIGHT, padx=20)
        connection_label = tk.Label(connection_frame, text="Arduino Connected", font=("Helvetica", 16))
        connection_label.grid(row=0, column=0, padx=(0, 10))
        self.connection_indicator = tk.Canvas(connection_frame, width=20, height=20, highlightthickness=0)
        self.connection_indicator.grid(row=0, column=1)
        self.update_connection_status()

        # Main frame to organize layout
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Left frame for manual controls (switches and lights)
        self.left_frame = tk.Frame(self.main_frame, width=400, padx=20, pady=20)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right frame for temperature and other indicators
        self.right_frame = tk.Frame(self.main_frame, width=400, padx=20, pady=20)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Manual controls on the left
        self.states = {
            "lights_top": {"state": False, "schedule": "", "description_label": None},
            "lights_bottom": {"state": False, "schedule": "", "description_label": None},
            "pump_top": {"state": False, "schedule": "", "description_label": None},
            "pump_bottom": {"state": False, "schedule": "", "description_label": None},
        }
        self.create_switch("Lights (Top)", 0, "lights_top", "LT")
        self.create_switch("Lights (Bottom)", 1, "lights_bottom", "LB")
        self.create_switch("Pump (Top)", 2, "pump_top", "PT")
        self.create_switch("Pump (Bottom)", 3, "pump_bottom", "PB")

        # Reset button
        self.create_reset_button()

        # Schedule toggle
        self.schedule_enabled = tk.BooleanVar(value=True)
        schedule_toggle = tk.Checkbutton(
            self.left_frame,
            text="Schedule On",
            font=("Helvetica", 16),
            variable=self.schedule_enabled,
            pady=10,
            command=self.update_schedule_visibility,
        )
        schedule_toggle.grid(row=5, column=0, columnspan=3)

        # Temperature display
        self.temperature_label = tk.Label(
            self.right_frame, text="Temperature: -- °C | -- °F", font=("Helvetica", 20)
        )
        self.temperature_label.pack(pady=20, anchor="center")

        # Start clock and temperature updates
        self.update_clock()
        self.update_temperature()

        # Load and apply the schedule
        self.load_schedule()

        # Ensure all switches are OFF at startup
        self.initialize_switches()

    def create_switch(self, label_text, row, state_key, device_code):
        """Create a switch with a light indicator and schedule description."""
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
        light = tk.Canvas(self.left_frame, width=20, height=20, highlightthickness=0)
        light.grid(row=row, column=2, padx=10, pady=10)
        light.create_oval(2, 2, 18, 18, fill="red")

        description_label = tk.Label(self.left_frame, text="", font=("Helvetica", 12), fg="gray")
        description_label.grid(row=row + 1, column=0, columnspan=3, sticky="w")
        self.states[state_key] = {
            "state": False,
            "button": button,
            "light": light,
            "device_code": device_code,
            "description_label": description_label,
        }

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
        reset_button.grid(row=9, column=0, columnspan=3, pady=20)

    def toggle_state(self, state_key, button, light, device_code):
        """Toggle the state, update the button and light, and send a command to the Arduino."""
        current_state = not self.states[state_key]["state"]
        self.states[state_key]["state"] = current_state
        if current_state:
            button.config(text="ON", bg="darkgreen")
            light.delete("all")
            light.create_oval(2, 2, 18, 18, fill="green")
            self.send_command(device_code, "ON")
        else:
            button.config(text="OFF", bg="darkgrey")
            light.delete("all")
            light.create_oval(2, 2, 18, 18, fill="red")
            self.send_command(device_code, "OFF")

    def send_command(self, device_code, state):
        """Send a command to the Arduino via serial."""
        if self.arduino:
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
            info["light"].delete("all")
            info["light"].create_oval(2, 2, 18, 18, fill="red")
            self.send_command(info["device_code"], "OFF")

    def reset_all_switches(self):
        """Turn all switches off."""
        print("Resetting all switches to OFF...")
        self.initialize_switches()

    def update_clock(self):
        """Update the clock every second."""
        current_time = time.strftime("%b %d %H:%M")
        self.clock_label.config(text=current_time)
        self.root.after(1000, self.update_clock)

    def update_temperature(self):
        """Request and update the temperature every 30 seconds."""
        def fetch_temperature():
            if self.arduino:
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

    def update_connection_status(self):
        """Update the connection indicator every second."""
        if self.arduino:
            try:
                self.arduino.write(b"PING\n")
                time.sleep(0.1)  # Allow time for Arduino to respond
                if self.arduino.in_waiting > 0:
                    self.connection_indicator.delete("all")
                    self.connection_indicator.create_oval(2, 2, 18, 18, fill="green")
                else:
                    self.connection_indicator.delete("all")
                    self.connection_indicator.create_oval(2, 2, 18, 18, fill="red")
            except Exception:
                self.connection_indicator.delete("all")
                self.connection_indicator.create_oval(2, 2, 18, 18, fill="red")
        else:
            self.connection_indicator.delete("all")
            self.connection_indicator.create_oval(2, 2, 18, 18, fill="red")
        self.root.after(1000, self.update_connection_status)

    def load_schedule(self):
        """Load schedule from file and update switch descriptions."""
        try:
            with open("schedule.txt", "r") as file:
                for line in file:
                    if line.strip() and not line.startswith("#"):
                        device, start_time, duration = line.split()
                        if device in ["LT", "LB"]:
                            description = "On from 9:00 AM to 9:00 PM."
                        elif device in ["PT", "PB"]:
                            description = "On for 15 minutes every 4 hours starting at midnight."

                        # Update the corresponding switch
                        for state_key, info in self.states.items():
                            if info["device_code"] == device:
                                info["schedule"] = description
                                if self.schedule_enabled.get():
                                    info["description_label"].config(text=description)
        except Exception as e:
            print(f"Error loading schedule: {e}")

    def update_schedule_visibility(self):
        """Show or hide schedule descriptions based on the toggle."""
        for state_key, info in self.states.items():
            if self.schedule_enabled.get():
                info["description_label"].config(text=info["schedule"])
            else:
                info["description_label"].config(text="")


def main():
    try:
        arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        time.sleep(2)  # Wait for Arduino to initialize
        print("Connected to Arduino.")
    except Exception as e:
        print(f"Error connecting to Arduino: {e}")
        arduino = None

    root = tk.Tk()
    app = HydroponicsGUI(root, arduino)
    root.mainloop()
    if arduino:
        arduino.close()


if __name__ == "__main__":
    main()
