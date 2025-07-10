import json
import csv
from datetime import datetime
import os

class StatusLogger:
    def __init__(self, status_file='status.json', env_file='environment_log.csv', health_file='system_health.csv'):
        self.status_file = status_file
        self.env_file = env_file
        self.health_file = health_file

    def write_status(self, status):
        try:
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=4)
        except Exception as e:
            print(f"[StatusLogger] Failed to write status: {e}")

    def log_environment_data(self, timestamp, temperature, humidity, water_temp, ec, ph):
        try:
            file_exists = os.path.isfile(self.env_file)
            with open(self.env_file, 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['timestamp', 'air_temp', 'humidity', 'water_temp', 'ec', 'ph'])
                writer.writerow([timestamp, temperature, humidity, water_temp, ec, ph])
        except Exception as e:
            print(f"[StatusLogger] Failed to log environment data: {e}")

    def log_system_health(self, timestamp, uptime, free_mem, cpu_temp):
        try:
            file_exists = os.path.isfile(self.health_file)
            with open(self.health_file, 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['timestamp', 'uptime', 'free_mem', 'cpu_temp'])
                writer.writerow([timestamp, uptime, free_mem, cpu_temp])
        except Exception as e:
            print(f"[StatusLogger] Failed to log system health: {e}")