import tkinter as tk
import threading
import time
from arduino_helpers import connect_to_arduino, check_arduino_connection, send_command_to_arduino

def create_switch(gui, label_text, row, state_key, device_code):
    """Create a switch button with a light indicator."""
    label = tk.Label(gui.left_frame, text=label_text, font=("Helvetica", 18))
    label.grid(row=row, column=0, padx=10, pady=10, sticky="w")

    button = tk.Button(
        gui.left_frame,
        text="OFF",
        font=("Helvetica", 18),
        bg="darkgrey",
        fg="white",
        width=10,
        command=lambda: toggle_state(gui, state_key, button, light, device_code),
    )
    button.grid(row=row, column=1, padx=10, pady=10)

    light = tk.Canvas(gui.left_frame, width=20, height=20, highlightthickness=0)
    light.grid(row=row, column=2, padx=10, pady=10)
    light.create_oval(2, 2, 18, 18, fill="red")

    gui.states[state_key].update({"button": button, "light": light, "device_code": device_code})

def toggle_state(gui, state_key, button, light, device_code):
    """Toggle the state, update the button and light, and send a command to the Arduino."""
    current_state = not gui.states[state_key]["state"]
    gui.states[state_key]["state"] = current_state
    new_state = "ON" if current_state else "OFF"

    button.config(text=new_state, bg="darkgreen" if current_state else "darkgrey")
    light.delete("all")
    light.create_oval(2, 2, 18, 18, fill="green" if current_state else "red")

    send_command_to_arduino(gui.arduino, f"{device_code}:{new_state}\n")

def create_reset_button(gui):
    """Create a button to reset devices to Arduino’s schedule."""
    reset_button = tk.Button(
        gui.left_frame,
        text="Reset Schedule",
        font=("Helvetica", 18),
        bg="red",
        fg="white",
        width=15,
        command=lambda: reset_to_arduino_schedule(gui.arduino),
    )
    reset_button.grid(row=5, column=0, columnspan=3, pady=20)

def monitor_arduino_connection(gui):
    """Periodically check connection and attempt reconnection if lost."""
    def monitor():
        while True:
            if gui.arduino and check_arduino_connection(gui.arduino):
                time.sleep(5)
                continue

            print("🔴 Arduino disconnected! Attempting to reconnect...")
            new_arduino = connect_to_arduino()
            if new_arduino:
                print("✅ Arduino reconnected!")
                gui.arduino = new_arduino
                send_command_to_arduino(gui.arduino, "GET_STATE\n")

                gui.connection_indicator.delete("all")
                gui.connection_indicator.create_oval(2, 2, 18, 18, fill="green")
            else:
                gui.connection_indicator.delete("all")
                gui.connection_indicator.create_oval(2, 2, 18, 18, fill="red")

            time.sleep(5)

    threading.Thread(target=monitor, daemon=True).start()

def update_relay_states(gui, response):
    """Parse Arduino relay state message and update GUI indicators."""
    try:
        print(f"📩 Received from Arduino: {response}")

        if not response.startswith("STATE:"):
            print(f"⚠ Unexpected message format: {response}")
            return

        state_values = response.split(":")[1].split(",")

        if len(state_values) != 4:
            print(f"⚠ Unexpected number of values in state update: {state_values}")
            return

        light_top, light_bottom, pump_top, pump_bottom = map(int, state_values)
        set_gui_state(gui, "lights_top", light_top)
        set_gui_state(gui, "lights_bottom", light_bottom)
        set_gui_state(gui, "pump_top", pump_top)
        set_gui_state(gui, "pump_bottom", pump_bottom)

        gui.connection_indicator.delete("all")
        gui.connection_indicator.create_oval(2, 2, 18, 18, fill="green")

    except Exception as e:
        print(f"⚠ Error parsing relay state: {e}")

def set_gui_state(gui, key, state):
    """Update button text and indicator color based on relay state."""
    info = gui.states[key]
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

def update_clock(gui):
    """Update the clock display every second."""
    def update():
        while True:
            gui.clock_label.config(text=time.strftime("%b %d %H:%M"))
            time.sleep(1)

    threading.Thread(target=update, daemon=True).start()