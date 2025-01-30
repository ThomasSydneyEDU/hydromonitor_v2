import tkinter as tk
import threading
import time
from datetime import datetime
from gui_helpers import (
    create_switch,
    create_reset_button,
    update_clock,
    update_connection_status,
)
from arduino_helpers import connect_to_arduino, send_command_to_arduino, check_arduino_connection

class HydroponicsGUI:
    def __init__(self, root):
        self.root = root
        self.arduino = None  # Initially, no connection
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

        # Main frame for manual controls
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Left frame for switches
        self.left_frame = tk.Frame(self.main_frame, width=400, padx=20, pady=20)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

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

        # Start monitoring and reconnecting Arduino
        self.monitor_arduino_connection()

        # Start listening for relay state updates
        self.start_relay_state_listener()

    def monitor_arduino_connection(self):
        """ Periodically checks the connection and attempts reconnection if lost. """
        def monitor_connection():
            while True:
                if not check_arduino_connection(self.arduino):
                    print("🔴 Arduino disconnected! Attempting to reconnect...")
                    self.arduino = connect_to_arduino()  # Try to reconnect

                    if self.arduino:
                        print("✅ Arduino reconnected!")
                        self.set_time_on_arduino()  # Resync time
                time.sleep(5)  # Check connection every 5 seconds

        threading.Thread(target=monitor_connection, daemon=True).start()

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
                    self.arduino = None  # Mark as disconnected
                    break  # Stop listening until a reconnection is made

        threading.Thread(target=listen_for_state, daemon=True).start()

    def update_relay_states(self, response):
        """ Parse the Arduino relay state message and update GUI indicators. """
        try:
            print(f"📩 Received from Arduino: {response}")  # Debugging output

            if not response.startswith("STATE:"):
                print(f"⚠ Unexpected message format: {response}")
                return

            state_values = response.split(":")[1].split(",")

            if len(state_values) != 4:
                print(f"⚠ Unexpected number of values in state update: {state_values}")
                return

            light_top, light_bottom, pump_top, pump_bottom = map(int, state_values)
            self.set_gui_state("lights_top", light_top)
            self.set_gui_state("lights_bottom", light_bottom)
            self.set_gui_state("pump_top", pump_top)
            self.set_gui_state("pump_bottom", pump_bottom)

        except Exception as e:
            print(f"⚠ Error parsing relay state: {e}")

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
        print("🔄 Resetting to Arduino schedule...")
        send_command_to_arduino(self.arduino, "RESET_SCHEDULE\n")

    def set_time_on_arduino(self):
        """Send the current system time to the Arduino."""
        if self.arduino:
            try:
                current_time = datetime.now().strftime("%H:%M:%S")
                print(f"⏰ Sending time to Arduino: {current_time}")
                send_command_to_arduino(self.arduino, f"SET_TIME:{current_time}\n")
            except Exception as e:
                print(f"⚠ Error sending time to Arduino: {e}")


def main():
    root = tk.Tk()
    app = HydroponicsGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()