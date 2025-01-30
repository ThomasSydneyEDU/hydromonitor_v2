import tkinter as tk
import threading
import time

from arduino_helpers import connect_to_arduino  # ✅ Use existing function

def create_switch(gui, label_text, row, state_key, device_code):
    """Create a switch with a light indicator."""
    label = tk.Label(gui.left_frame, text=label_text, font=("Helvetica", 18))
    label.grid(row=row, column=0, padx=10, pady=10, sticky="w")

    button = tk.Button(
        gui.left_frame,
        text="OFF",
        font=("Helvetica", 18),
        bg="darkgrey",
        fg="white",
        width=10,
        command=lambda: gui.toggle_switch(state_key),
    )
    button.grid(row=row, column=1, padx=10, pady=10)

    light = tk.Canvas(gui.left_frame, width=20, height=20, highlightthickness=0)
    light.grid(row=row, column=2, padx=10, pady=10)
    light.create_oval(2, 2, 18, 18, fill="red")

    gui.states[state_key]["button"] = button
    gui.states[state_key]["light"] = light

def create_reset_button(gui):
    """Create a reset button to restore Arduino’s schedule."""
    reset_button = tk.Button(
        gui.left_frame,
        text="Reset to Schedule",
        font=("Helvetica", 16),
        bg="blue",
        fg="white",
        width=20,
        command=gui.reset_to_arduino_schedule,
    )
    reset_button.grid(row=5, column=0, columnspan=3, pady=20)

def update_clock(gui):
    """Update the clock display every second."""
    def refresh_clock():
        while True:
            current_time = time.strftime("%b %d %H:%M")
            gui.clock_label.config(text=current_time)
            time.sleep(1)

    threading.Thread(target=refresh_clock, daemon=True).start()



def update_connection_status(gui):
    """ Continuously check the Arduino connection and update the UI. """
    def check_connection():
        while True:
            if gui.arduino and gui.arduino.is_open:
                try:
                    gui.arduino.write(b"PING\n")  # Send PING command
                    time.sleep(0.5)  # Wait for response
                    if gui.arduino.in_waiting > 0:
                        response = gui.arduino.readline().decode().strip()
                        if response == "PING_OK":
                            update_indicator(gui.connection_indicator, "green")
                        else:
                            update_indicator(gui.connection_indicator, "red")
                    else:
                        update_indicator(gui.connection_indicator, "red")
                except Exception:
                    update_indicator(gui.connection_indicator, "red")
                    gui.arduino = connect_to_arduino()  # ✅ Use existing function to reconnect
            else:
                update_indicator(gui.connection_indicator, "red")
                gui.arduino = connect_to_arduino()  # ✅ Attempt reconnect
            time.sleep(3)  # Check every 3 seconds

    threading.Thread(target=check_connection, daemon=True).start()

def update_indicator(indicator, color):
    """ Update the color of a status indicator. """
    indicator.delete("all")
    indicator.create_oval(2, 2, 18, 18, fill=color)