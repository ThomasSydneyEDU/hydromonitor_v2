import tkinter as tk
from datetime import datetime
import time

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

    gui_instance.states[state_key]["button"] = button
    gui_instance.states[state_key]["light"] = light
    gui_instance.states[state_key]["device_code"] = device_code

def toggle_state(gui_instance, state_key, button, light, device_code):
    """Toggle the state, update the button and light, and send a command to the Arduino."""
    current_state = not gui_instance.states[state_key]["state"]
    gui_instance.states[state_key]["state"] = current_state

    if current_state:
        button.config(text="ON", bg="darkgreen")
        light.delete("all")
        light.create_oval(2, 2, 18, 18, fill="green")
        gui_instance.send_command(device_code, "ON")
    else:
        button.config(text="OFF", bg="darkgrey")
        light.delete("all")
        light.create_oval(2, 2, 18, 18, fill="red")
        gui_instance.send_command(device_code, "OFF")

def create_reset_button(gui_instance):
    """Create a reset button to turn off all switches."""
    reset_button = tk.Button(
        gui_instance.left_frame,
        text="Reset All",
        font=("Helvetica", 18),
        bg="red",
        fg="white",
        width=15,
        command=gui_instance.reset_all_switches,
    )
    reset_button.grid(row=9, column=0, columnspan=3, pady=20)

def update_clock(gui_instance):
    """Update the clock every second."""
    def refresh_time():
        current_time = datetime.now().strftime("%b %d %H:%M")
        gui_instance.clock_label.config(text=current_time)
        gui_instance.root.after(1000, refresh_time)

    refresh_time()

def update_connection_status(gui_instance):
    """Update the Arduino connection indicator every second."""
    def check_connection():
        if gui_instance.arduino:
            try:
                gui_instance.arduino.write(b"PING\n")
                time.sleep(0.1)  # Allow time for Arduino to respond
                if gui_instance.arduino.in_waiting > 0:
                    gui_instance.connection_indicator.delete("all")
                    gui_instance.connection_indicator.create_oval(2, 2, 18, 18, fill="green")
                else:
                    gui_instance.connection_indicator.delete("all")
                    gui_instance.connection_indicator.create_oval(2, 2, 18, 18, fill="red")
            except Exception:
                gui_instance.connection_indicator.delete("all")
                gui_instance.connection_indicator.create_oval(2, 2, 18, 18, fill="red")
        else:
            gui_instance.connection_indicator.delete("all")
            gui_instance.connection_indicator.create_oval(2, 2, 18, 18, fill="red")

        gui_instance.root.after(1000, check_connection)

    check_connection()
