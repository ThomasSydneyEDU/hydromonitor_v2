import tkinter as tk
import serial
import time

# Define serial port and baud rate
SERIAL_PORT = "/dev/ttyACM0"  # Arduino port
BAUD_RATE = 9600

class HydroponicsGUI:
    def __init__(self, root, arduino):
        self.root = root
        self.arduino = arduino
        self.root.title("Hydroponics System Control")

        # Create a dictionary to manage states
        self.states = {
            "lights_top": False,
            "lights_bottom": False,
            "pump_top": False,
            "pump_bottom": False
        }

        # Define the layout
        self.create_switch("Lights (Top)", 0, "lights_top", "LT")
        self.create_switch("Lights (Bottom)", 1, "lights_bottom", "LB")
        self.create_switch("Pump (Top)", 2, "pump_top", "PT")
        self.create_switch("Pump (Bottom)", 3, "pump_bottom", "PB")

        # Ensure all switches are OFF at startup
        self.initialize_switches()

    def create_switch(self, label_text, row, state_key, device_code):
        """Create a switch with a light indicator."""
        # Label for the switch
        label = tk.Label(self.root, text=label_text, font=("Helvetica", 14))
        label.grid(row=row, column=0, padx=10, pady=10, sticky="w")

        # Button to toggle the state
        button = tk.Button(self.root, text="OFF", font=("Helvetica", 14),
                           bg="darkgrey", fg="white", width=10,
                           command=lambda: self.toggle_state(state_key, button, light, device_code))
        button.grid(row=row, column=1, padx=10, pady=10)

        # Light indicator
        light = tk.Canvas(self.root, width=20, height=20, bg="red", highlightthickness=0)
        light.grid(row=row, column=2, padx=10, pady=10)

        # Store the button and light widgets for future updates
        self.states[state_key] = {"state": False, "button": button, "light": light, "device_code": device_code}

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
        self.arduino.write(command.encode())

    def initialize_switches(self):
        """Ensure all switches are OFF at startup."""
        print("Initializing all switches to OFF...")
        for state_key, info in self.states.items():
            info["state"] = False
            info["button"].config(text="OFF", bg="darkgrey")
            info["light"].config(bg="red")
            self.send_command(info["device_code"], "OFF")


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