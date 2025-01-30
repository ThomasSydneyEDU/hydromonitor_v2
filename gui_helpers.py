import threading
import time
from arduino_helpers import connect_to_arduino, check_arduino_connection, set_time_on_arduino, send_command_to_arduino

def monitor_arduino_connection(gui):
    """ Periodically checks the connection and attempts reconnection if lost. """
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
                set_time_on_arduino(gui.arduino)
                send_command_to_arduino(gui.arduino, "GET_STATE\n")

                # Update GUI indicators
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