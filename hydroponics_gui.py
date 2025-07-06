import tkinter as tk
import threading
from datetime import datetime
import json
import os
import json
import csv
from gui_helpers import (
    update_connection_status,
)
from arduino_helpers import connect_to_arduino, send_command_to_arduino


class HydroponicsGUI:
    RELAY_STATE_LENGTH = 7
    SENSOR_STATE_LENGTH = 6
    def schedule_periodic_time_sync(self):
        """Resend current time to Arduino every 10 minutes."""
        self.set_time_on_arduino()
        self.root.after(10 * 60 * 1000, self.schedule_periodic_time_sync)

    def __init__(self, root, arduino):
        self.root = root
        default_bg = "#eeeeee"
        self.arduino = arduino
        self.root.title("Hydroponics System Control")
        self.root.geometry("800x480")
        self.root.attributes("-fullscreen", False)
        self.root.configure(bg=default_bg)

        # Track Arduino time and when it was received for clock display
        self.last_arduino_time = None
        self.last_time_received_timestamp = None

        # Top frame for clock and Arduino connection indicator
        self.top_frame = tk.Frame(self.root, padx=20, pady=10, bg=default_bg)
        self.top_frame.pack(fill=tk.X, side=tk.TOP)

        # Arduino connection indicator with label
        connection_frame = tk.Frame(self.top_frame, bg=default_bg)
        connection_frame.pack(side=tk.RIGHT, padx=20)
        connection_label = tk.Label(connection_frame, text="Arduino Connected", font=("Helvetica", 12), bg=default_bg, fg="black")
        connection_label.grid(row=0, column=0, padx=(0, 5))
        self.connection_indicator = tk.Canvas(connection_frame, width=20, height=20, highlightthickness=0, bg=default_bg)
        self.connection_indicator.grid(row=0, column=1)
        # Clock display moved to the right side of the top frame, inside connection_frame
        self.clock_label = tk.Label(connection_frame, text="", font=("Helvetica", 14), bg=default_bg, fg="black")
        self.clock_label.grid(row=0, column=2, padx=(10, 0))

        # Initialize connection status check
        update_connection_status(self)

        # Main frame for manual controls and sensor data
        self.main_frame = tk.Frame(self.root, bg=default_bg)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Center frame for switches
        self.center_frame = tk.Frame(self.main_frame, padx=20, pady=20, bg=default_bg)
        self.center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Switches frame holds both relay columns
        self.switches_frame = tk.Frame(self.root, bg=default_bg)
        # Add relay columns to switches_frame
        self.relay_column_1 = tk.Frame(self.switches_frame, bg=default_bg)
        self.relay_column_1.pack(side=tk.LEFT, expand=True, padx=10, anchor="n")

        self.relay_column_2 = tk.Frame(self.switches_frame, bg=default_bg)
        self.relay_column_2.pack(side=tk.RIGHT, expand=True, padx=10, anchor="n")

        # --- Group buttons into labeled frames in relay columns ---
        self.lights_frame = tk.LabelFrame(self.relay_column_1, text="Lights", font=("Helvetica", 12, "bold"), bg=default_bg, fg="black")
        self.lights_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.pumps_frame = tk.LabelFrame(self.relay_column_1, text="Pumps", font=("Helvetica", 12, "bold"), bg=default_bg, fg="black")
        self.pumps_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.fans_frame = tk.LabelFrame(self.relay_column_2, text="Fans", font=("Helvetica", 12, "bold"), bg=default_bg, fg="black")
        self.fans_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Heater button (moved from relay_column_1 to relay_column_2, below fans_frame)
        self.heater_frame = tk.LabelFrame(self.relay_column_2, text="Heater", font=("Helvetica", 12, "bold"), bg=default_bg, fg="black")
        self.heater_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.misc_frame = tk.LabelFrame(self.relay_column_2, text="EC/pH Acquisition", font=("Helvetica", 12, "bold"), bg=default_bg, fg="black")
        self.misc_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Pack switches_frame inside center_frame
        self.switches_frame.pack(in_=self.center_frame, fill=tk.BOTH, expand=True)

        # Right frame for sensor data (leave untouched)
        self.right_frame = tk.Frame(self.main_frame, width=400, padx=20, pady=20, bg=default_bg)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Temperature and Humidity Display
        self.temp_frame = tk.Frame(self.right_frame, bg=default_bg)
        self.temp_frame.pack(pady=10)

        self.temperature_label_title = tk.Label(self.temp_frame, text="Air Temperature (Inside / Outside)", font=("Helvetica", 14, "bold"), bg=default_bg, fg="black")
        self.temperature_label_title.pack()

        self.temperature_label = tk.Label(self.temp_frame, text="-- °C", font=("Helvetica", 14), bg=default_bg, fg="black")
        self.temperature_label.pack()

        self.humid_frame = tk.Frame(self.right_frame, bg=default_bg)
        self.humid_frame.pack(pady=10)

        self.humidity_label_title = tk.Label(self.humid_frame, text="Air Humidity (Inside / Outside)", font=("Helvetica", 14, "bold"), bg=default_bg, fg="black")
        self.humidity_label_title.pack()

        self.humidity_label = tk.Label(self.humid_frame, text="-- %", font=("Helvetica", 14), bg=default_bg, fg="black")
        self.humidity_label.pack()

        # Water Temperature Display
        self.water_temp_frame = tk.Frame(self.right_frame, bg=default_bg)
        self.water_temp_frame.pack(pady=10)

        self.water_temp_label_title = tk.Label(self.water_temp_frame, text="Water Temperatures", font=("Helvetica", 14, "bold"), bg=default_bg, fg="black")
        self.water_temp_label_title.pack()

        self.water_temp1_label = tk.Label(self.water_temp_frame, text="Top reservoir: -- °C", font=("Helvetica", 12), bg=default_bg, fg="black")
        self.water_temp1_label.pack()

        self.water_temp2_label = tk.Label(self.water_temp_frame, text="Bottom reservoir: -- °C", font=("Helvetica", 12), bg=default_bg, fg="black")
        self.water_temp2_label.pack()

        # Float Sensor Display
        self.float_frame = tk.Frame(self.right_frame, bg=default_bg)
        self.float_frame.pack(pady=10)

        self.float_label_title = tk.Label(self.float_frame, text="Float Sensors", font=("Helvetica", 14, "bold"), bg=default_bg, fg="black")
        self.float_label_title.pack()

        self.float_top_label = tk.Label(self.float_frame, text="Top: --", font=("Helvetica", 12), bg=default_bg, fg="black")
        self.float_top_label.pack()

        self.float_bottom_label = tk.Label(self.float_frame, text="Bottom: --", font=("Helvetica", 12), bg=default_bg, fg="black")
        self.float_bottom_label.pack()

        # Manual controls with custom style for switches

        relay_definitions = [
            ("Lights (Top)", "lights_top", "LT", self.lights_frame),
            ("Lights (Bottom)", "lights_bottom", "LB", self.lights_frame),
            ("Pump (Top)", "pump_top", "PT", self.pumps_frame),
            ("Pump (Bottom)", "pump_bottom", "PB", self.pumps_frame),
            ("Fan (Vent)", "fan_vent", "FV", self.fans_frame),
            ("Fan (Circ)", "fan_circ", "FC", self.fans_frame),
            ("Heater", "heater", "HE", self.heater_frame),
        ]
        self.states = {}
        for label, key, code, parent in relay_definitions:
            self.states[key] = {"state": False, "device_code": code}
            container = tk.Frame(parent, bg=default_bg)
            container.pack(pady=4)

            button = tk.Button(
                container,
                text=label,
                width=18,
                height=2,
                relief="raised",
                bg="gray",
                fg="black",
                command=lambda k=key: self.toggle_switch(k)
            )
            button.pack(side=tk.LEFT, padx=4, pady=2)
            self.states[key]["button"] = button

        # Start clock
        self.update_clock()

        # Send time to Arduino after 2 seconds
        self.root.after(2000, self.set_time_on_arduino)
        # Schedule periodic time sync every 10 minutes
        self.root.after(10 * 60 * 1000, self.schedule_periodic_time_sync)

        # Request relay state from Arduino
        send_command_to_arduino(self.arduino, "GET_STATE\n")

        # Start listening for relay state updates
        self.start_relay_state_listener()

        # Schedule periodic status write
        self.schedule_status_write()



    def schedule_status_write(self):
        self.write_status_to_file()
        self.root.after(60000, self.schedule_status_write)

    def write_status_to_file(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, "hydro_dashboard", "status.json")

        # Split temperature and humidity into indoor/outdoor for dashboard
        temp_text = self.temperature_label.cget("text")
        humid_text = self.humidity_label.cget("text")
        status = {
            "Air Temp (Indoor)": temp_text.split("/")[0].strip().replace("°C", ""),
            "Air Temp (Outdoor)": temp_text.split("/")[1].strip().replace("°C", "") if "/" in temp_text else "",
            "Humidity (Indoor)": humid_text.split("/")[0].strip().replace("%", ""),
            "Humidity (Outdoor)": humid_text.split("/")[1].strip().replace("%", "") if "/" in humid_text else "",
            "Water Temp Top": self.water_temp1_label.cget("text").split(":")[-1].strip().replace("°C", ""),
            "Water Temp Bottom": self.water_temp2_label.cget("text").split(":")[-1].strip().replace("°C", ""),
            "Top Float": self.float_top_label.cget("text").split(":")[-1].strip(),
            "Bottom Float": self.float_bottom_label.cget("text").split(":")[-1].strip(),
            "timestamp": datetime.now().isoformat()
        }

        # Add relay statuses
        for key, info in self.states.items():
            status[f"Relay {key.replace('_', ' ').title()}"] = "ON" if info["state"] else "OFF"

        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(status, f)
            print(f"[INFO] ✅ Status written to {output_path}")
        except Exception as e:
            print(f"[ERROR] ❌ Failed to write status: {e}")

    def toggle_switch(self, state_key):
        """Toggle a device state manually and send the command to the Arduino."""
        if state_key not in self.states:
            print(f"⚠ Error: {state_key} not found in self.states")
            return

        new_state = not self.states[state_key]["state"]
        self.states[state_key]["state"] = new_state
        new_color = "green" if new_state else "red"
        self.states[state_key]["button"].config(bg=new_color)
        if new_state:
            send_command_to_arduino(self.arduino, f"{self.states[state_key]['device_code']}:ON\n")
        else:
            send_command_to_arduino(self.arduino, f"{self.states[state_key]['device_code']}:OFF\n")

        print(f"🔄 Toggled {state_key} to {'ON' if new_state else 'OFF'}")
        self.write_status_to_file()

    def start_relay_state_listener(self):
        """ Continuously listen for state updates from the Arduino. """
        def listen_for_state():
            while True:
                # Check for serial disconnection
                if not self.arduino:
                    print("⚠ Arduino not connected.")
                    break
                try:
                    if self.arduino and self.arduino.in_waiting > 0:
                        response = self.arduino.readline().decode().strip()
                        if not response:
                            continue  # Skip empty lines
                        print(f"[ARDUINO] {response}")
                        # Log every Arduino message to arduino_log.txt
                        with open("arduino_log.txt", "a") as log_file:
                            log_file.write(f"{datetime.now().isoformat()} - {response}\n")
                        if response.startswith("RSTATE:"):
                            self.update_relay_states(response)
                        elif response.startswith("SSTATE:"):
                            self.update_sensor_states(response)
                        elif response.startswith("TIME:"):
                            # Use system time for logging and display
                            now = datetime.now()
                            self.last_arduino_time = now
                            self.last_time_received_timestamp = now
                            self.clock_label.config(text=now.strftime("%H:%M:%S"), fg="black")

                            # Also record the reported Arduino time for diagnostics
                            arduino_time_str = response.split(":", 1)[1].strip()
                            with open("arduino_log.txt", "a") as log_file:
                                log_file.write(f"{now.isoformat()} - ARDUINO_TIME: {arduino_time_str}\n")
                except Exception as e:
                    print(f"Error reading state update: {e}")
                    break

        threading.Thread(target=listen_for_state, daemon=True).start()

    def update_clock(self):
        """Update the GUI clock based on Arduino or fallback."""
        now = datetime.now()
        if self.last_arduino_time and self.last_time_received_timestamp:
            seconds_since_last = (now - self.last_time_received_timestamp).total_seconds()
            if seconds_since_last > 15:
                # If no recent Arduino time message, show system time in gray
                self.clock_label.config(text=now.strftime("%H:%M:%S"), fg="gray")
        self.root.after(1000, self.update_clock)

    def update_relay_states(self, response):
        """ Parse the Arduino relay state message and update GUI relay indicators. """
        try:
            print(f"📩 Received from Arduino: {response}")  # Debugging output

            if ":" not in response:
                print(f"⚠ Incomplete or malformed message: {response}")
                return

            if not response.startswith("RSTATE:"):
                print(f"⚠ Warning: Unexpected message format: {response}")
                return

            # Split and extract relay state values as key-value pairs
            state_values = response.split(":", 1)[1].split(",")

            relay_map = {
                'LT': 'lights_top',
                'LB': 'lights_bottom',
                'PT': 'pump_top',
                'PB': 'pump_bottom',
                'FV': 'fan_vent',
                'FC': 'fan_circ',
                'HE': 'heater',
            }

            relay_states = {}
            for item in state_values:
                if "=" in item:
                    code, val = item.split("=")
                    relay_states[code.strip()] = int(val.strip())

            for code, key in relay_map.items():
                if code in relay_states:
                    try:
                        self.set_gui_state(key, relay_states[code])
                    except Exception as e:
                        print(f"⚠ GUI update error: {e}")

            # Ensure GUI updates immediately after relay state change
            try:
                self.root.update_idletasks()
            except Exception as e:
                print(f"⚠ GUI update error: {e}")

            # ✅ Update the connection indicator to green (since valid data was received)
            try:
                self.connection_indicator.delete("all")
                self.connection_indicator.create_oval(2, 2, 18, 18, fill="green")
            except Exception as e:
                print(f"⚠ GUI update error: {e}")

            self.write_status_to_file()
            # Log relay state update to arduino_log.txt
            with open("arduino_log.txt", "a") as log_file:
                log_file.write(f"{datetime.now().isoformat()} - RELAY: {response}\n")

            # Log relay state to CSV
            relay_log_path = os.path.join("hydro_dashboard", "relay_log.csv")
            relay_headers = [
                "timestamp",
                "top_lights", "bottom_lights",
                "pump_top", "pump_bottom",
                "fan_vent", "fan_circ",
                "heater"
            ]
            relay_row = [datetime.now().isoformat()]
            for code in ['LT', 'LB', 'PT', 'PB', 'FV', 'FC', 'HE']:
                relay_row.append(relay_states.get(code, ""))
            file_exists = os.path.exists(relay_log_path)
            os.makedirs(os.path.dirname(relay_log_path), exist_ok=True)
            with open(relay_log_path, "a", newline="") as f:
                writer = csv.writer(f)
                if not file_exists or os.path.getsize(relay_log_path) == 0:
                    writer.writerow(relay_headers)
                writer.writerow(relay_row)

        except Exception as e:
            print(f"⚠ Error parsing relay state: {e}")

    def update_sensor_states(self, response):
        """
        Parse the Arduino sensor state message and update sensor displays.
        The first temperature/humidity pair is from the *indoor* DHT sensor,
        the second pair is from the *outdoor* DHT sensor.
        """
        try:
            if ":" not in response:
                print(f"⚠ Incomplete or malformed message: {response}")
                return

            sensor_values = response.split(":")[1].split(",")

            if len(sensor_values) != 8:
                print(f"⚠ Warning: Unexpected number of values in sensor update: {sensor_values}")
                return

            # Indoor DHT sensor
            temp_indoor = int(sensor_values[0])
            humid_indoor = int(sensor_values[1])
            # Outdoor DHT sensor
            temp_outdoor = int(sensor_values[2])
            humid_outdoor = int(sensor_values[3])
            water_temp1 = float(sensor_values[4])
            water_temp2 = float(sensor_values[5])
            float_top = int(sensor_values[6])
            float_bottom = int(sensor_values[7])

            try:
                self.temperature_label.config(text=f"{temp_indoor} / {temp_outdoor} °C", fg="black")
            except Exception as e:
                print(f"⚠ GUI update error: {e}")
            try:
                self.humidity_label.config(text=f"{humid_indoor} / {humid_outdoor} %", fg="black")
            except Exception as e:
                print(f"⚠ GUI update error: {e}")
            try:
                self.water_temp1_label.config(text=f"Top reservoir: {water_temp1:.1f} °C", fg="black")
            except Exception as e:
                print(f"⚠ GUI update error: {e}")
            try:
                self.water_temp2_label.config(text=f"Bottom reservoir: {water_temp2:.1f} °C", fg="black")
            except Exception as e:
                print(f"⚠ GUI update error: {e}")
            try:
                self.float_top_label.config(
                    text=f"Top: {'Okay' if float_top else 'Low'}",
                    fg="red" if not float_top else "black"
                )
            except Exception as e:
                print(f"⚠ GUI update error: {e}")
            try:
                self.float_bottom_label.config(
                    text=f"Bottom: {'Okay' if float_bottom else 'Low'}",
                    fg="red" if not float_bottom else "black"
                )
            except Exception as e:
                print(f"⚠ GUI update error: {e}")

            # Ensure GUI updates immediately after sensor state change
            try:
                self.root.update_idletasks()
            except Exception as e:
                print(f"⚠ GUI update error: {e}")

            self.write_status_to_file()
            # Log sensor state update to arduino_log.txt
            with open("arduino_log.txt", "a") as log_file:
                log_file.write(f"{datetime.now().isoformat()} - SENSOR: {response}\n")

            # Log sensor data to CSV
            sensor_log_path = os.path.join("hydro_dashboard", "sensor_log.csv")
            sensor_headers = [
                "timestamp",
                "air_temp_indoor", "humidity_indoor",
                "air_temp_outdoor", "humidity_outdoor",
                "water_temp_top", "water_temp_bottom",
                "float_top", "float_bottom"
            ]
            sensor_row = [
                datetime.now().isoformat(),
                temp_indoor, humid_indoor,
                temp_outdoor, humid_outdoor,
                water_temp1, water_temp2,
                float_top, float_bottom
            ]
            file_exists = os.path.exists(sensor_log_path)
            os.makedirs(os.path.dirname(sensor_log_path), exist_ok=True)
            with open(sensor_log_path, "a", newline="") as f:
                writer = csv.writer(f)
                if not file_exists or os.path.getsize(sensor_log_path) == 0:
                    writer.writerow(sensor_headers)
                writer.writerow(sensor_row)

        except Exception as e:
            print(f"⚠ Error parsing sensor state: {e}")

    def set_gui_state(self, key, state):
        """Update button color and state based on relay state."""
        self.states[key]["state"] = bool(state)
        new_color = "green" if state else "red"
        self.states[key]["button"].config(bg=new_color)


    def set_heater_state(self, on):
        """Override heater relay from Pi logic."""
        key = "heater"
        if key not in self.states:
            print("⚠ Heater key not found in relay states.")
            return

        self.states[key]["state"] = on
        new_color = "green" if on else "red"
        self.states[key]["button"].config(bg=new_color)
        if on:
            send_command_to_arduino(self.arduino, f"{self.states[key]['device_code']}:ON\n")
        else:
            send_command_to_arduino(self.arduino, f"{self.states[key]['device_code']}:OFF\n")
        print(f"🔧 Heater override: {'ON' if on else 'OFF'}")
        self.write_status_to_file()


    def set_time_on_arduino(self):
        """Send the current system time to the Arduino."""
        if self.arduino:
            try:
                current_time = datetime.now().strftime("%H:%M:%S")
                full_command = f"SET_TIME:{current_time}\n"
                print(f"[DEBUG] Sending to Arduino: {repr(full_command)}")
                send_command_to_arduino(self.arduino, full_command)
            except Exception as e:
                print(f"Error sending time to Arduino: {e}")





def main():
    arduino = connect_to_arduino()
    root = tk.Tk()
    gui = HydroponicsGUI(root, arduino)
    root.mainloop()
    if arduino:
        arduino.close()


if __name__ == "__main__":
    main()