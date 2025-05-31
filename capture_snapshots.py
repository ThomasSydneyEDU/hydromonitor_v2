import datetime
import subprocess
from pathlib import Path
import logging
import time

# Directory for snapshots
snapshot_dir = Path(__file__).resolve().parent / 'static' / 'snapshots'
snapshot_dir.mkdir(parents=True, exist_ok=True)

# Filenames with today's date
date_str = datetime.datetime.now().strftime('%Y%m%d')
timestamp_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = snapshot_dir / f'snapshot_log_{date_str}.txt'
logging.basicConfig(filename=log_file, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
top_filename = snapshot_dir / f'TopCamera.jpg'
bottom_filename = snapshot_dir / f'BottomCamera.jpg'
top_archive_filename = snapshot_dir / f'TopCamera_{timestamp_str}.jpg'
bottom_archive_filename = snapshot_dir / f'BottomCamera_{timestamp_str}.jpg'

def capture_camera(device, current_filename, archive_filename, label):
    try:
        result = subprocess.run(
            ['fswebcam', '-d', device, '-r', '1280x720', str(current_filename)],
            capture_output=True, text=True, check=True
        )
        # Copy current to archive
        subprocess.run(['cp', str(current_filename), str(archive_filename)], check=True)
        msg = f"[{label}] Capture successful: {current_filename}, archived as: {archive_filename}"
        print(msg)
        logging.info(msg)
    except subprocess.CalledProcessError as e:
        err_msg = f"[{label}] Capture failed for {device}: {e.stderr}"
        print(err_msg)
        logging.error(err_msg)

capture_camera('/dev/video0', top_filename, top_archive_filename, "Top Camera")
time.sleep(1)
capture_camera('/dev/video2', bottom_filename, bottom_archive_filename, "Bottom Camera")