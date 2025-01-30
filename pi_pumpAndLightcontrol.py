import tkinter as tk
from gui_helpers import (
    create_switch,
    create_reset_button,
    update_clock,
    monitor_arduino_connection,
    update_relay_states,
)

from arduino_helpers import connect_to_arduino, send_command_to_arduino, reset_to_arduino_schedule, start_relay_state_listener

class HydroponicsGUI:
    def __init__(self, root):
        self.root = root
        self.arduino = None  # No connection initially
        self.root.title("Hydroponics System Control")
        self.root.geometry("800x480")
        self.root.attributes("-fullscreen", False)

        # Top frame for clock and Arduino connection indicator
        self.top_frame = tk.Frame(self.root, padx=20, pady=10)
        self.top_frame.pack(fill=tk.X, side=tk.TOP)

        # Clock display
        self.clock_label = tk.Label(self.top_frame, text="", font=("Helvetica", 24))
        self.clock_label.pack(side=tk.LEFT, padx=20)

        # Arduino connection indicator
        self.connection_indicator = tk.Canvas(self.top_frame, width=20, height=20, highlightthickness=0)
        self.connection_indicator.pack(side=tk.RIGHT, padx=20)

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

        create_reset_button(self)

        update_clock(self)

        monitor_arduino_connection(self)
        start_relay_state_listener(self)

def main():
    root = tk.Tk()
    app = HydroponicsGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()