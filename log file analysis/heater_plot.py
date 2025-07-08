import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

log_file = "arduino_log.txt"

# Read and parse log entries
with open(log_file, "r") as file:
    lines = file.readlines()

sensor_entries = []
relay_entries = []

for line in lines:
    try:
        timestamp_str, content = line.strip().split(" - ", 1)
        timestamp = datetime.fromisoformat(timestamp_str)

        if content.startswith("SENSOR: SSTATE:"):
            values = content.split("SSTATE:")[1].split(",")
            if len(values) >= 1:
                sensor_entries.append({
                    "timestamp": timestamp,
                    "indoor_temp": float(values[0])
                })

        elif content.startswith("RELAY: RSTATE:"):
            relay_data = {"timestamp": timestamp}
            for item in content.split("RSTATE:")[1].split(","):
                if "=" in item:
                    key, val = item.split("=")
                    relay_data[key] = int(val)
            relay_entries.append(relay_data)

    except Exception:
        continue

# Convert to DataFrames
sensor_df = pd.DataFrame(sensor_entries)
relay_df = pd.DataFrame(relay_entries)

# Merge on timestamp (nearest match within 2s)
merged = pd.merge_asof(
    relay_df.sort_values("timestamp"),
    sensor_df.sort_values("timestamp"),
    on="timestamp",
    direction="nearest",
    tolerance=pd.Timedelta(seconds=2)
).dropna(subset=["indoor_temp", "HE", "FC"])

merged = merged.reset_index(drop=True)

# Analysis: heater on/off counts and average duration
merged["HE_shift"] = merged["HE"].shift(1)
merged["on_change"] = (merged["HE_shift"] == 0) & (merged["HE"] == 1)
merged["off_change"] = (merged["HE_shift"] == 1) & (merged["HE"] == 0)

heater_on_times = merged[merged["on_change"]]["timestamp"].reset_index(drop=True)
heater_off_times = merged[merged["off_change"]]["timestamp"].reset_index(drop=True)

# Align lengths
min_len = min(len(heater_on_times), len(heater_off_times))
durations = (heater_off_times[:min_len] - heater_on_times[:min_len]).dt.total_seconds()

avg_duration = durations.mean() / 60 if not durations.empty else 0
num_activations = len(durations)

# Plot
fig, axs = plt.subplots(3, 1, figsize=(14, 8), sharex=True)
axs[0].plot(merged["timestamp"], merged["indoor_temp"], label="Indoor Temp (°C)")
axs[0].set_ylabel("Temp (°C)")
axs[0].legend()

axs[1].plot(merged["timestamp"], merged["HE"], label="Heater", color="red")
axs[1].set_ylabel("Heater")
axs[1].set_yticks([0, 1])
axs[1].legend()

axs[2].plot(merged["timestamp"], merged["FC"], label="Circ Fan", color="green")
axs[2].set_ylabel("Fan")
axs[2].set_yticks([0, 1])
axs[2].set_xlabel("Time")
axs[2].legend()

plt.tight_layout()
plt.figtext(0.5, -0.03,
    f"Avg heater duration: {avg_duration:.1f} min | Activations: {num_activations}",
    ha="center", fontsize=10
)
plt.show()