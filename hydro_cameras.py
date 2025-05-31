from flask import Flask, render_template, Response, url_for
import cv2
import os
 
import logging


app = Flask(__name__)

# Set paths for snapshots
SNAPSHOT_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'snapshots')
os.makedirs(SNAPSHOT_FOLDER, exist_ok=True)

# Logging configuration
LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'camera_log.txt')
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

TOP_CAMERA_DEVICE = '/dev/video2'
BOTTOM_CAMERA_DEVICE = '/dev/video0'

def take_snapshot(camera_device, filename, backup_filename=None):
    cap = cv2.VideoCapture(camera_device)
    if not cap.isOpened():
        logging.error(f"Error opening camera {camera_device}")
        return
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(filename, frame)
        if backup_filename:
            cv2.imwrite(backup_filename, frame)
        logging.info(f"Snapshot taken from {camera_device} and saved to {filename}")
    else:
        logging.warning(f"Failed to capture image from {camera_device}")
    cap.release()

@app.route('/')
def index():
    top_image = '/static/snapshots/TopCamera.jpg'
    bottom_image = '/static/snapshots/BottomCamera.jpg'
    return render_template('index.html', top_image=top_image, bottom_image=bottom_image)

def start_server():
    app.run(host='0.0.0.0', port=5050,debug=True)

if __name__ == '__main__':
    start_server()