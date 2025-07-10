# arduino_manager.py

import threading
from datetime import datetime

class ArduinoManager:
    def __init__(self, arduino, on_relay_update, on_sensor_update, on_time_update):
        self.arduino = arduino
        self.on_relay_update = on_relay_update
        self.on_sensor_update = on_sensor_update
        self.on_time_update = on_time_update

    def start_listener(self):
        def loop():
            while True:
                try:
                    if not self.arduino or not self.arduino.in_waiting:
                        continue

                    response = self.arduino.readline().decode().strip()
                    if not response:
                        continue

                    now = datetime.now().isoformat()
                    with open("arduino_log.txt", "a") as log_file:
                        log_file.write(f"{now} - {response}\n")

                    if response.startswith("RSTATE:"):
                        self.on_relay_update(response)
                    elif response.startswith("SSTATE:"):
                        self.on_sensor_update(response)
                    elif response.startswith("TIME:"):
                        self.on_time_update(response)
                except Exception as e:
                    print(f"[ArduinoManager] Error: {e}")
                    break

        threading.Thread(target=loop, daemon=True).start()