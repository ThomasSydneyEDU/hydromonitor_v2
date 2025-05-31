

from flask import Flask, render_template, Response, url_for
import cv2
import os
from datetime import datetime
import threading
import time
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

def take_snapshot(camera_device, filename):
    cap = cv2.VideoCapture(camera_device)
    if not cap.isOpened():
        logging.error(f"Error opening camera {camera_device}")
        return
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(filename, frame)
        logging.info(f"Snapshot taken from {camera_device} and saved to {filename}")
    else:
        logging.warning(f"Failed to capture image from {camera_device}")
    cap.release()

def daily_snapshot_job():
    while True:
        now = datetime.now()
        if now.hour == 13 and now.minute == 0:
            date_str = now.strftime("%d%m%Y")
            top_img_path = os.path.join(SNAPSHOT_FOLDER, f"TopCamera_{date_str}.jpg")
            bottom_img_path = os.path.join(SNAPSHOT_FOLDER, f"BottomCamera_{date_str}.jpg")
            take_snapshot(TOP_CAMERA_DEVICE, top_img_path)
            take_snapshot(BOTTOM_CAMERA_DEVICE, bottom_img_path)
            time.sleep(60)  # prevent taking multiple photos in the same minute
        time.sleep(20)  # check every 20 seconds

@app.route('/')
def index():
    top_image = url_for('static', filename='snapshots/TopCamera.jpg', _external=False)
    bottom_image = url_for('static', filename='snapshots/BottomCamera.jpg', _external=False)
    return render_template('index.html', top_image=top_image, bottom_image=bottom_image)

def start_server():
    app.run(host='0.0.0.0', port=5050,debug=True)

if __name__ == '__main__':
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Thread(target=daily_snapshot_job, daemon=True).start()
    start_server()