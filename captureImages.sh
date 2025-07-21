#!/bin/bash

# Navigate to the script's directory (in case cron runs from a different location)
cd "$(dirname "$0")"

# Activate the virtual environment (assumes it's in ./VENV)
source ./VENV/bin/activate

# Run the Python script
python hydro_dashboard/uploadDailyImages.py

# Optional: deactivate the environment (not strictly needed for cron)
deactivate