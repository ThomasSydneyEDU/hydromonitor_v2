#!/bin/bash

# Define variables
REPO_DIR="hydromonitor_v2"       # Directory where your repository is cloned
VENV_DIR="$REPO_DIR/venv"        # Path to the virtual environment
REPO_URL="https://github.com/ThomasSydneyEDU/hydromonitor_v2.git"
REQUIREMENTS_FILE="$REPO_DIR/requirements.txt"
SCRIPT_NAME="pi_pumpAndLightcontrol.py" # Main script to run

echo "==== Hydro Monitor Script ===="

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

# Install required packages
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing required packages from requirements.txt..."
    pip install --upgrade pip
    pip install -r "$REQUIREMENTS_FILE"
else
    echo "No requirements.txt file found. Skipping package installation."
fi

# Run the Python script
if [ -f "$REPO_DIR/$SCRIPT_NAME" ]; then
    echo "Running the main script: $SCRIPT_NAME..."
    lxterminal -e "bash -c 'python \"$REPO_DIR/$SCRIPT_NAME\"; exec bash'"
else
    echo "Error: $SCRIPT_NAME not found in the repository."
    deactivate
    exit 1
fi

# Deactivate virtual environment
echo "Deactivating virtual environment..."
deactivate


# Start the Flask web dashboard in the background if not already running
if ! pgrep -f "python app.py" > /dev/null; then
    echo "Starting Flask web server..."
    cd "$REPO_DIR/hydro_dashboard" || exit
    nohup python app.py > flask.log 2>&1 &
    cd ../..
else
    echo "Flask server is already running."
fi

echo "==== Script Completed ===="
