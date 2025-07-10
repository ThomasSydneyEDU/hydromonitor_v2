# relay_controller.py

class RelayController:
    def __init__(self, send_command_fn):
        self.send_command = send_command_fn
        self.states = {
            "lights_top": {"device_code": "LT", "state": False},
            "lights_bottom": {"device_code": "LB", "state": False},
            "pump_top": {"device_code": "PT", "state": False},
            "pump_bottom": {"device_code": "PB", "state": False},
            "fan_vent": {"device_code": "FV", "state": False},
            "fan_circ": {"device_code": "FC", "state": False},
            "heater": {"device_code": "HE", "state": False},
        }

    def assign_button(self, key, button):
        """Attach a button to a specific relay."""
        if key in self.states:
            self.states[key]["button"] = button

    def toggle(self, key):
        """Toggle a relay and update GUI/button."""
        if key not in self.states:
            print(f"[RelayController] Unknown key: {key}")
            return

        state = not self.states[key]["state"]
        self.states[key]["state"] = state
        cmd = f"{self.states[key]['device_code']}:{'ON' if state else 'OFF'}\n"
        self.send_command(cmd)
        self._update_button_color(key)

    def set_state_from_arduino(self, response):
        """Update relay states from Arduino RSTATE response."""
        try:
            state_values = response.split(":", 1)[1].split(",")
            for item in state_values:
                if "=" in item:
                    code, val = item.strip().split("=")
                    key = self._code_to_key(code.strip())
                    if key:
                        self.states[key]["state"] = bool(int(val))
                        self._update_button_color(key)
        except Exception as e:
            print(f"[RelayController] Failed to parse response: {e}")

    def _update_button_color(self, key):
        state_info = self.states[key]
        if "button" in state_info:
            new_color = "green" if state_info["state"] else "red"
            state_info["button"].config(bg=new_color)

    def _code_to_key(self, code):
        mapping = {
            "LT": "lights_top",
            "LB": "lights_bottom",
            "PT": "pump_top",
            "PB": "pump_bottom",
            "FV": "fan_vent",
            "FC": "fan_circ",
            "HE": "heater",
        }
        return mapping.get(code)