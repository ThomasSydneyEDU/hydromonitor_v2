import tkinter as tk
import serial

class HydroponicsGUI:
    def __init__(self, root, serial_port):
        self.root = root
        self.root.title("Hydroponics System Control")

        # Initialize serial communication with Arduino
        self.arduino = serial.Serial(serial_port, 9600, timeout=1)

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

    def toggle_state(self, state_key, button, light, device_code):
        """Toggle the state, update the button and light, and send a command to the Arduino."""
        self.states[state_key] = not self.states[state_key]
        if self.states[state_key]:
            button.config(text="ON", bg="darkgreen")
            light.config(bg="green")
            self.send_command(device_code, "ON")
        else:
            button.config(text="OFF", bg="darkgrey")
            light.config(bg="red")
            self.send_command(device_code, "OFF")

    def send_command(self, device_code, state):
        """Send a command to the Arduino via serial."""
        command = f"{device_code}:{state}\n"  # Format: DEVICE:STATE
        print(f"Sending command: {command.strip()}")
        self.arduino.write(command.encode())

# Run the GUI
if __name__ == "__main__":
    serial_port = "/dev/ttyACM0"  # Update with your Arduino's USB port
    root = tk.Tk()
    app = HydroponicsGUI(root, serial_port)
    root.mainloop()