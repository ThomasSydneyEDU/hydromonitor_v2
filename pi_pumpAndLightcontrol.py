import tkinter as tk
import threading
from datetime import datetime
from gui_helpers import (
    create_switch,
    create_reset_button,
    update_clock,
    update_connection_status,
)
from arduino_helpers import connect_to_arduino, send_command_to_arduino


class HydroponicsGUI:
    def __init__(self, root, arduino):
        self.root = root
        self.arduino = arduino
        self.root.title("Hydroponics System Control")
        self.root.geometry("800x480")
        self.root.attributes("-fullscreen", False)

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

        # Initialize connection status check
        update_connection_status(self)

        # Main frame for manual controls
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Left frame for switches
        self.left_frame = tk.Frame(self.main_frame, width=400, padx=20, pady=20)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Right frame for sensor data
        self.right_frame = tk.Frame(self.main_frame, width=400, padx=20, pady=20)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Temperature and Humidity Display
        self.sensor_label = tk.Label(
            self.right_frame, text="Temp: -- °C | Hum: -- %", font=("Helvetica", 20)
        )
        self.sensor_label.pack(pady=20, anchor="center")

        # Manual controls
        self.states = {
            "lights_top": {"state": False, "device_code": "LT"},
            "lights_bottom": {"state": False, "device_code": "LB"},
            "pump_top": {"state": False, "device_code": "PT"},
            "pump_bottom": {"state": False, "device_code": "PB"},
        }
        create_switch(self, "Lights (Top)", 0, "lights_top", "LT")
        create_switch(self, "Lights (Bottom)", 1, "lights_bottom", "LB")
        create_switch(self, "Pump (Top)", 2, "pump_top", "PT")
        create_switch(self, "Pump (Bottom)", 3, "pump_bottom", "PB")

        # Reset button
        create_reset_button(self)

        # Start clock
        update_clock(self)

        # Send time to Arduino
        self.set_time_on_arduino()

        # Start listening for relay state updates
        self.start_relay_state_listener()

    def start_relay_state_listener(self):
        """ Continuously listen for state updates from the Arduino. """
        def listen_for_state():
            while True:
                try:
                    if self.arduino and self.arduino.in_waiting > 0:
                        response = self.arduino.readline().decode().strip()
                        if response.startswith("STATE:"):
                            self.update_relay_states(response)
                except Exception as e:
                    print(f"Error reading state update: {e}")
                    break

        threading.Thread(target=listen_for_state, daemon=True).start()

    def update_relay_states(self, response):
        """ Parse the Arduino relay state message and update GUI indicators. """
        try:
            print(f"Received from Arduino: {response}")  # Debugging output

            if not response.startswith("STATE:"):
                print(f"Warning: Unexpected message format: {response}")
                return

            # Split response: STATE + SENSOR DATA
            parts = response.split(" | ")
            state_values = parts[0].split(":")[1].split(",")  # Extract relay states

            if len(state_values) != 4:
                print(f"Warning: Unexpected number of values in state update: {state_values}")
                return

            # Update GUI indicators for relays
            light_top, light_bottom, pump_top, pump_bottom = map(int, state_values)
            self.set_gui_state("lights_top", light_top)
            self.set_gui_state("lights_bottom", light_bottom)
            self.set_gui_state("pump_top", pump_top)
            self.set_gui_state("pump_bottom", pump_bottom)

            # Extract and update sensor data if present
            temp, hum = "--", "--"  # Default values
            for part in parts[1:]:
                if "TEMP:" in part:
                    temp = part.split(":")[1].strip()
                if "HUM:" in part:
                    hum = part.split(":")[1].strip()

            # Update GUI with sensor readings
            self.sensor_label.config(text=f"Temp: {temp}°C | Hum: {hum}%")

        except Exception as e:
            print(f"Error parsing relay state: {e}")

    def set_gui_state(self, key, state):
        """ Update button text and indicator color based on relay state. """
        info = self.states[key]
        button = info.get("button")
        light = info.get("light")

        if state == 1:
            info["state"] = True
            button.config(text="ON", bg="darkgreen")
            light.delete("all")
            light.create_oval(2, 2, 18, 18, fill="green")
        else:
            info["state"] = False
            button.config(text="OFF", bg="darkgrey")
            light.delete("all")
            light.create_oval(2, 2, 18, 18, fill="red")

    def reset_to_arduino_schedule(self):
        """Reset all devices to follow Arduino’s schedule."""
        print("Resetting to Arduino schedule...")
        send_command_to_arduino(self.arduino, "RESET_SCHEDULE\n")

    def set_time_on_arduino(self):
        """Send the current system time to the Arduino."""
        if self.arduino:
            try:
                current_time = datetime.now().strftime("%H:%M:%S")
                print(f"Sending time to Arduino: {current_time}")
                send_command_to_arduino(self.arduino, f"SET_TIME:{current_time}\n")
            except Exception as e:
                print(f"Error sending time to Arduino: {e}")


def main():
    arduino = connect_to_arduino()
    root = tk.Tk()
    app = HydroponicsGUI(root, arduino)
    root.mainloop()
    if arduino:
        arduino.close()


if __name__ == "__main__":
    main()