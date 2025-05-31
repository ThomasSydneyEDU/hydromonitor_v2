

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
        try:
            now = datetime.now()
            if now.hour == 13 and now.minute == 0:
                date_str = now.strftime("%d%m%Y_%H%M%S")
                timestamp_top_img = os.path.join(SNAPSHOT_FOLDER, f"TopCamera_{date_str}.jpg")
                timestamp_bottom_img = os.path.join(SNAPSHOT_FOLDER, f"BottomCamera_{date_str}.jpg")
                overwrite_top_img = os.path.join(SNAPSHOT_FOLDER, "TopCamera.jpg")
                overwrite_bottom_img = os.path.join(SNAPSHOT_FOLDER, "BottomCamera.jpg")

                take_snapshot(TOP_CAMERA_DEVICE, timestamp_top_img)
                take_snapshot(TOP_CAMERA_DEVICE, overwrite_top_img)
                time.sleep(1)
                take_snapshot(BOTTOM_CAMERA_DEVICE, timestamp_bottom_img)
                take_snapshot(BOTTOM_CAMERA_DEVICE, overwrite_bottom_img)

                logging.info("Snapshots captured and saved successfully.")
                time.sleep(60)
            time.sleep(20)
        except Exception as e:
            logging.exception("Error in daily_snapshot_job loop:")

@app.route('/')
def index():
    top_image = '/static/snapshots/TopCamera.jpg'
    bottom_image = '/static/snapshots/BottomCamera.jpg'
    return render_template('index.html', top_image=top_image, bottom_image=bottom_image)

def start_server():
    app.run(host='0.0.0.0', port=5050,debug=True)

if __name__ == '__main__':
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Thread(target=daily_snapshot_job, daemon=True).start()
    start_server()