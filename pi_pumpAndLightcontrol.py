import tkinter as tk
import tkinter.ttk as ttk
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
        self.clock_label = tk.Label(self.top_frame, text="", font=("Helvetica", 18))
        self.clock_label.pack(side=tk.LEFT, padx=20)

        # Arduino connection indicator with label
        connection_frame = tk.Frame(self.top_frame)
        connection_frame.pack(side=tk.RIGHT, padx=20)
        connection_label = tk.Label(connection_frame, text="Arduino Connected", font=("Helvetica", 12))
        connection_label.grid(row=0, column=0, padx=(0, 10))
        self.connection_indicator = tk.Canvas(connection_frame, width=20, height=20, highlightthickness=0)
        self.connection_indicator.grid(row=0, column=1)

        # Initialize connection status check
        update_connection_status(self)

        # Main frame for manual controls and sensor data
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Center frame for switches
        self.center_frame = tk.Frame(self.main_frame, padx=20, pady=20)
        self.center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Switches frame holds both relay columns
        self.switches_frame = tk.Frame(self.root)
        # Add relay columns to switches_frame
        self.relay_column_1 = tk.Frame(self.switches_frame)
        self.relay_column_1.pack(side=tk.LEFT, expand=True, padx=10)

        self.relay_column_2 = tk.Frame(self.switches_frame)
        self.relay_column_2.pack(side=tk.RIGHT, expand=True, padx=10)

        # --- Group buttons into labeled frames in relay columns ---
        self.lights_frame = tk.LabelFrame(self.relay_column_1, text="Lights", font=("Helvetica", 12, "bold"))
        self.lights_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.pumps_frame = tk.LabelFrame(self.relay_column_1, text="Pumps", font=("Helvetica", 12, "bold"))
        self.pumps_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Reset to Schedule button
        self.reset_frame = tk.Frame(self.relay_column_1)
        self.reset_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.reset_button = tk.Button(self.reset_frame,
                                      text="Reset to Schedule",
                                      font=("Helvetica", 12, "bold"),
                                      width=18,
                                      height=2,
                                      bg="blue",
                                      fg="white",
                                      command=self.reset_to_arduino_schedule)
        self.reset_button.pack(pady=4)

        self.fans_frame = tk.LabelFrame(self.relay_column_2, text="Fans", font=("Helvetica", 12, "bold"))
        self.fans_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.misc_frame = tk.LabelFrame(self.relay_column_2, text="EC/pH Acquisition", font=("Helvetica", 12, "bold"))
        self.misc_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Pack switches_frame inside center_frame
        self.switches_frame.pack(in_=self.center_frame, fill=tk.BOTH, expand=True)

        # Right frame for sensor data (leave untouched)
        self.right_frame = tk.Frame(self.main_frame, width=400, padx=20, pady=20)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Temperature and Humidity Display
        self.temp_frame = tk.Frame(self.right_frame)
        self.temp_frame.pack(pady=10)

        self.temperature_label_title = tk.Label(self.temp_frame, text="Temperature", font=("Helvetica", 14, "bold"))
        self.temperature_label_title.pack()

        self.temperature_label = tk.Label(self.temp_frame, text="-- °C", font=("Helvetica", 14))
        self.temperature_label.pack()

        self.humid_frame = tk.Frame(self.right_frame)
        self.humid_frame.pack(pady=10)

        self.humidity_label_title = tk.Label(self.humid_frame, text="Humidity", font=("Helvetica", 14, "bold"))
        self.humidity_label_title.pack()

        self.humidity_label = tk.Label(self.humid_frame, text="-- %", font=("Helvetica", 14))
        self.humidity_label.pack()

        # Water Temperature Display
        self.water_temp_frame = tk.Frame(self.right_frame)
        self.water_temp_frame.pack(pady=10)

        self.water_temp_label_title = tk.Label(self.water_temp_frame, text="Water Temperatures", font=("Helvetica", 14, "bold"))
        self.water_temp_label_title.pack()

        self.water_temp1_label = tk.Label(self.water_temp_frame, text="Sensor 1: -- °C", font=("Helvetica", 12))
        self.water_temp1_label.pack()

        self.water_temp2_label = tk.Label(self.water_temp_frame, text="Sensor 2: -- °C", font=("Helvetica", 12))
        self.water_temp2_label.pack()

        # Float Sensor Display
        self.float_frame = tk.Frame(self.right_frame)
        self.float_frame.pack(pady=10)

        self.float_label_title = tk.Label(self.float_frame, text="Float Sensors", font=("Helvetica", 14, "bold"))
        self.float_label_title.pack()

        self.float_top_label = tk.Label(self.float_frame, text="Top: --", font=("Helvetica", 12))
        self.float_top_label.pack()

        self.float_bottom_label = tk.Label(self.float_frame, text="Bottom: --", font=("Helvetica", 12))
        self.float_bottom_label.pack()

        # Manual controls with custom style for switches
        style = ttk.Style(self.root)
        style.configure("Switch.TCheckbutton",
                        font=("Helvetica", 12),
                        padding=6,
                        foreground="#333",
                        background="#eee")

        relay_definitions = [
            ("Lights (Top)", "lights_top", "LT", self.lights_frame),
            ("Lights (Bottom)", "lights_bottom", "LB", self.lights_frame),
            ("Pump (Top)", "pump_top", "PT", self.pumps_frame),
            ("Pump (Bottom)", "pump_bottom", "PB", self.pumps_frame),
            ("Fan (Vent)", "fan_vent", "FV", self.fans_frame),
            ("Fan (Circ)", "fan_circ", "FC", self.fans_frame),
            ("Sensor Pump (Top)", "sensor_pump_top", "SPT", self.misc_frame),
            ("Sensor Pump (Bottom)", "sensor_pump_bottom", "SPB", self.misc_frame),
            ("Drain Actuator", "drain_actuator", "DA", self.misc_frame),
        ]
        self.states = {}
        for label, key, code, parent in relay_definitions:
            self.states[key] = {"state": False, "device_code": code}
            button = tk.Button(parent,
                               text=f"{label}\nTurn ON",
                               font=("Helvetica", 12),
                               width=18,
                               height=3,
                               bg="red",
                               activebackground="darkred",
                               fg="white",
                               command=lambda k=key: self.toggle_switch(k))
            button.pack(pady=4)
            self.states[key]["button"] = button

        # Start clock
        update_clock(self)

        # Send time to Arduino
        self.set_time_on_arduino()

        # Start listening for relay state updates
        self.start_relay_state_listener()

    def toggle_switch(self, state_key):
        """Toggle a device state manually and send the command to the Arduino."""
        if state_key not in self.states:
            print(f"⚠ Error: {state_key} not found in self.states")
            return

        new_state = not self.states[state_key]["state"]
        self.states[state_key]["state"] = new_state

        button = self.states[state_key]["button"]
        label = button.cget('text').splitlines()[0]
        if new_state:
            button.config(
                text=f"{label}\nTurn OFF",
                bg="green",
                activebackground="darkgreen",
                fg="white"
            )
            send_command_to_arduino(self.arduino, f"{self.states[state_key]['device_code']}:ON\n")
        else:
            button.config(
                text=f"{label}\nTurn ON",
                bg="red",
                activebackground="darkred",
                fg="white"
            )
            send_command_to_arduino(self.arduino, f"{self.states[state_key]['device_code']}:OFF\n")

        print(f"🔄 Toggled {state_key} to {'ON' if new_state else 'OFF'}")

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
        """ Parse the Arduino state message and update GUI indicators. """
        try:
            print(f"📩 Received from Arduino: {response}")  # Debugging output

            if not response.startswith("STATE:"):
                print(f"⚠ Warning: Unexpected message format: {response}")
                return

            # Split and extract values (relay states + sensor data)
            state_values = response.split(":")[1].split(",")

            if len(state_values) != 12:
                print(f"⚠ Warning: Unexpected number of values in state update: {state_values}")
                return

            # Parse relay states and sensor data
            light_top, light_bottom, pump_top, pump_bottom, fan_vent, fan_circ = map(int, state_values[:6])
            temperature, humidity = map(int, state_values[6:8])
            water_temp1, water_temp2 = map(float, state_values[8:10])
            float_top, float_bottom = map(int, state_values[10:12])

            # Update GUI switch indicators
            self.set_gui_state("lights_top", light_top)
            self.set_gui_state("lights_bottom", light_bottom)
            self.set_gui_state("pump_top", pump_top)
            self.set_gui_state("pump_bottom", pump_bottom)
            self.set_gui_state("fan_vent", fan_vent)
            self.set_gui_state("fan_circ", fan_circ)

            # Placeholder for sensor pump and drain actuator states if included in Arduino message
            # For now, no state updates from Arduino for these devices

            # ✅ Update the connection indicator to green (since valid data was received)
            self.connection_indicator.delete("all")
            self.connection_indicator.create_oval(2, 2, 18, 18, fill="green")

            # ✅ Update the temperature and humidity display
            self.temperature_label.config(text=f"{temperature} °C")
            self.humidity_label.config(text=f"{humidity} %")

            # Update water temperature display
            self.water_temp1_label.config(text=f"Top reservoir: {water_temp1:.1f} °C")
            self.water_temp2_label.config(text=f"Bottom reservoir: {water_temp2:.1f} °C")

            self.float_top_label.config(text=f"Top: {'Okay' if float_top else 'Low'}")
            self.float_bottom_label.config(text=f"Bottom: {'Okay' if float_bottom else 'Low'}")

        except Exception as e:
            print(f"⚠ Error parsing relay state: {e}")

    def set_gui_state(self, key, state):
        """ Update BooleanVar based on relay state. """
        self.states[key]["state"] = True if state == 1 else False
        btn = self.states[key]["button"]
        label = btn.cget("text").splitlines()[0]
        if state == 1:
            btn.config(
                text=f"{label}\nTurn OFF",
                bg="green",
                activebackground="darkgreen",
                fg="white"
            )
        else:
            btn.config(
                text=f"{label}\nTurn ON",
                bg="red",
                activebackground="darkred",
                fg="white"
            )


    def set_time_on_arduino(self):
        """Send the current system time to the Arduino."""
        if self.arduino:
            try:
                current_time = datetime.now().strftime("%H:%M:%S")
                print(f"Sending time to Arduino: {current_time}")
                send_command_to_arduino(self.arduino, f"SET_TIME:{current_time}\n")
            except Exception as e:
                print(f"Error sending time to Arduino: {e}")

    def reset_to_arduino_schedule(self):
        """Send a reset command to the Arduino to resume scheduled operation."""
        try:
            print("🔄 Sending reset to schedule command to Arduino")
            send_command_to_arduino(self.arduino, "RESET_SCHEDULE\n")
        except Exception as e:
            print(f"⚠ Error sending reset command: {e}")


def main():
    arduino = connect_to_arduino()
    root = tk.Tk()
    app = HydroponicsGUI(root, arduino)
    root.mainloop()
    if arduino:
        arduino.close()


if __name__ == "__main__":
    main()