import tkinter as tk
from datetime import datetime, timedelta
import threading
import time
from arduino_helpers import send_command_to_arduino

def create_switch(gui_instance, label_text, row, state_key, device_code):
    """Create a switch with a light indicator."""
    label = tk.Label(gui_instance.left_frame, text=label_text, font=("Helvetica", 18))
    label.grid(row=row, column=0, padx=10, pady=10, sticky="w")

    button = tk.Button(
        gui_instance.left_frame,
        text="OFF",
        font=("Helvetica", 18),
        bg="darkgrey",
        fg="white",
        width=10,
        command=lambda: toggle_state(gui_instance, state_key, button, light, device_code),
    )
    button.grid(row=row, column=1, padx=10, pady=10)

    light = tk.Canvas(gui_instance.left_frame, width=20, height=20, highlightthickness=0)
    light.grid(row=row, column=2, padx=10, pady=10)
    light.create_oval(2, 2, 18, 18, fill="red")

    description_label = tk.Label(gui_instance.left_frame, text="", font=("Helvetica", 12), fg="gray")
    description_label.grid(row=row + 1, column=0, columnspan=3, sticky="w")

    gui_instance.states[state_key]["button"] = button
    gui_instance.states[state_key]["light"] = light
    gui_instance.states[state_key]["device_code"] = device_code
    gui_instance.states[state_key]["description_label"] = description_label

def toggle_state(gui_instance, state_key, button, light, device_code):
    """Toggle the state, update the button and light, and send a command to the Arduino."""
    current_state = not gui_instance.states[state_key]["state"]
    gui_instance.states[state_key]["state"] = current_state

    if current_state:
        button.config(text="ON", bg="darkgreen")
        light.delete("all")
        light.create_oval(2, 2, 18, 18, fill="green")
        command = f"{device_code}:ON\n"
        print(f"Toggle ON for {device_code}. Command: {command.strip()}")
        send_command_to_arduino(gui_instance.arduino, command)
    else:
        button.config(text="OFF", bg="darkgrey")
        light.delete("all")
        light.create_oval(2, 2, 18, 18, fill="red")
        command = f"{device_code}:OFF\n"
        print(f"Toggle OFF for {device_code}. Command: {command.strip()}")
        send_command_to_arduino(gui_instance.arduino, command)

def create_reset_button(gui):
    """Create a reset button that tells the Arduino to follow its schedule."""
    reset_button = tk.Button(
        gui.left_frame,
        text="Reset to Schedule",
        font=("Helvetica", 18),
        bg="blue",
        fg="white",
        width=20,
        command=gui.reset_to_arduino_schedule,  # ✅ FIXED: Call the correct function
    )
    reset_button.grid(row=9, column=0, columnspan=3, pady=20)

def update_clock(gui_instance):
    """Update the clock every second."""
    def refresh_time():
        current_time = datetime.now().strftime("%b %d %H:%M")
        gui_instance.clock_label.config(text=current_time)
        gui_instance.root.after(1000, refresh_time)

    refresh_time()

def update_connection_status(gui):
    """Update the Arduino connection indicator every second."""
    def check_arduino():
        if gui.arduino:
            try:
                gui.arduino.write(b"PING\n")  # Send a test command
                gui.arduino.flush()  # Ensure it's sent
                time.sleep(0.1)  # Allow time for a response

                if gui.arduino.in_waiting > 0:
                    response = gui.arduino.readline().decode().strip()
                    if response == "PING_OK":
                        gui.connection_indicator.delete("all")
                        gui.connection_indicator.create_oval(2, 2, 18, 18, fill="green")  # ✅ Turn GREEN
                        return

            except Exception:
                pass

        gui.connection_indicator.delete("all")
        gui.connection_indicator.create_oval(2, 2, 18, 18, fill="red")  # ❌ Stay RED
        gui.root.after(1000, check_arduino)  # Repeat every second

    check_arduino()

def load_schedule(gui_instance):
    """Load schedule from file and update switch descriptions."""
    try:
        with open("schedule.txt", "r") as file:
            for line in file:
                if line.strip() and not line.startswith("#"):
                    parts = line.split(maxsplit=3)
                    if len(parts) == 4:
                        device, start_time, duration, description = parts
                        if device in ["LT", "LB", "PT", "PB"]:
                            gui_instance.states[device.lower()]["schedule"] = description.strip()
                            if gui_instance.schedule_enabled.get():
                                gui_instance.states[device.lower()]["description_label"].config(text=description.strip())
    except Exception as e:
        print(f"Error loading schedule: {e}")

def update_schedule_visibility(gui_instance):
    """Show or hide schedule descriptions based on the toggle."""
    for state_key, info in gui_instance.states.items():
        if gui_instance.schedule_enabled.get():
            info["description_label"].config(text=info.get("schedule", ""))
        else:
            info["description_label"].config(text="")
