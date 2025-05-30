#!/bin/bash

set -e
trap 'echo "Script failed at line $LINENO"; exit 1' ERR

# Define variables
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$BASE_DIR/hydromonitor_v2"
LOG_DIR="$REPO_DIR/logs"
mkdir -p "$LOG_DIR"
VENV_DIR="$REPO_DIR/venv"
REPO_URL="https://github.com/ThomasSydneyEDU/hydromonitor_v2.git"
REQUIREMENTS_FILE="$REPO_DIR/requirements.txt"
SCRIPT_NAME="hydroponics_gui.py" # Main script to run

echo "==== Hydro Monitor Script ===="
echo "Script started at $(date)" >> "$LOG_DIR/script_run.log"

# Check if the repository directory exists
if [ ! -d "$REPO_DIR" ]; then
    echo "Repository not found. Cloning from GitHub..."
    git clone "$REPO_URL"
else
    echo "Repository found. Pulling latest changes..."
    cd "$REPO_DIR" || exit
    git pull origin main
    cd ..
fi

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv "$VENV_DIR"
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Change to the repository directory
cd "$REPO_DIR"

# Install required packages
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing required packages from requirements.txt..."
    pip install --upgrade pip
    pip install -r "$REQUIREMENTS_FILE"
else
    echo "No requirements.txt file found. Skipping package installation."
fi

# Run the Python script
if [ -f "$SCRIPT_NAME" ]; then
    echo "Running the main script: $SCRIPT_NAME..."
    LOG_FILE="$LOG_DIR/gui_$(date +'%Y%m%d_%H%M%S').log"
    echo "Logging output to $LOG_FILE"
    nohup python "$SCRIPT_NAME" > "$LOG_FILE" 2>&1 &
else
    echo "Error: $SCRIPT_NAME not found in the repository."
    exit 1
fi

echo "==== Script Completed ===="
