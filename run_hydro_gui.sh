#!/bin/bash

# Path setup
PROJECT_DIR="/home/tcar5787/Documents/hydromonitor_v2"
VENV="$PROJECT_DIR/venv"
LOGFILE="/home/tcar5787/gui_autostart.log"

# Activate virtual environment
source "$VENV/bin/activate"

# Run the GUI
echo "[$(date)] Starting hydro GUI..." >> "$LOGFILE"
python "$PROJECT_DIR/hydro_gui.py" >> "$LOGFILE" 2>&1
echo "[$(date)] GUI exited." >> "$LOGFILE"

# Optional: wait before closing terminal
sleep 5