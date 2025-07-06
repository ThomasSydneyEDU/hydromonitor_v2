import pandas as pd
import matplotlib.pyplot as plt
import re
from datetime import datetime

# Load the log file
log_file = "arduino_log.txt"  # Update path if needed
with open(log_file, "r") as file:
    lines = file.readlines()

parsed_data = []

for line in lines:
    sensor_match = re.match(r"(.+?) - SENSOR: SSTATE:(.+)", line)
    if sensor_match:
        timestamp_str, data_str = sensor_match.groups()
        timestamp = datetime.fromisoformat(timestamp_str)
        values = data_str.strip().split(",")
        if len(values) == 8:
            try:
                parsed_data.append({
                    "timestamp": timestamp,
                    "air_temp_indoor": int(values[0])
                })
            except:
                continue

    relay_match = re.match(r"(.+?) - RELAY: RSTATE:(.+)", line)
    if relay_match:
        timestamp_str, relay_str = relay_match.groups()
        timestamp = datetime.fromisoformat(timestamp_str)
        relay_parts = dict(item.split("=") for item in relay_str.strip().split(",") if "=" in item)
        try:
            parsed_data.append({
                "timestamp": timestamp,
                "heater_state": int(relay_parts.get("HE", -1)),
                "fan_circ_state": int(relay_parts.get("FC", -1))
            })
        except:
            continue

# Build DataFrame
df = pd.DataFrame(parsed_data).sort_values("timestamp").drop_duplicates("timestamp")
df.set_index("timestamp", inplace=True)
df = df.ffill().dropna()

# Plotting in three horizontal (stacked) subplots
fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(12, 8), sharex=True)

# Indoor temperature
axes[0].plot(df.index, df["air_temp_indoor"], color="tab:blue")
axes[0].set_ylabel("Indoor Temp (°C)", color="tab:blue")
axes[0].tick_params(axis='y', labelcolor="tab:blue")
axes[0].set_title("Indoor Temperature")

# Heater state
axes[1].plot(df.index, df["heater_state"], color="tab:red", linestyle='--')
axes[1].set_ylabel("Heater", color="tab:red")
axes[1].set_yticks([0, 1])
axes[1].tick_params(axis='y', labelcolor="tab:red")
axes[1].set_title("Heater Relay State")

# Circulation fan state
axes[2].plot(df.index, df["fan_circ_state"], color="tab:green", linestyle='--')
axes[2].set_ylabel("Circ Fan", color="tab:green")
axes[2].set_yticks([0, 1])
axes[2].tick_params(axis='y', labelcolor="tab:green")
axes[2].set_title("Circulation Fan Relay State")

# Analyze heater activity
df["state_change"] = df["heater_state"].diff().fillna(0)
on_periods = []
on_start = None

for time, row in df.iterrows():
    if row["state_change"] == 1:
        on_start = time
    elif row["state_change"] == -1 and on_start:
        on_periods.append((on_start, time))
        on_start = None

on_durations = [(end - start).total_seconds() / 60 for start, end in on_periods]
total_hours = (df.index[-1] - df.index[0]).total_seconds() / 3600
on_events_per_hour = len(on_periods) / total_hours if total_hours > 0 else 0
avg_on_duration = sum(on_durations) / len(on_durations) if on_durations else 0

analysis_text = (
    f"Heater ON events: {len(on_periods)}  |  "
    f"Avg ON duration: {avg_on_duration:.2f} min  |  "
    f"ON events/hour: {on_events_per_hour:.2f}"
)

plt.xlabel("Time")
plt.xticks(rotation=45)
# Add text summary below plots
plt.figtext(0.5, 0.01, analysis_text, ha="center", fontsize=10, bbox={"facecolor":"lightgrey", "alpha":0.5, "pad":4})
plt.tight_layout()
plt.show()