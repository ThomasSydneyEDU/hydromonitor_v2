import datetime
import subprocess
from pathlib import Path
import logging
import time
import cv2
import numpy as np

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


def apply_color_correction_from_reference(image_path, reference_path):
    import cv2
    import numpy as np

    # Load the current (grow light) and reference (white light) images
    img = cv2.imread(str(image_path))
    ref = cv2.imread(str(reference_path))

    if img is None or ref is None:
        logging.error("Could not read images for correction.")
        return

    img = img.astype('float32') / 255.0
    ref = ref.astype('float32') / 255.0

    # Crop area (tablet cover region) - manually estimated for current camera view
    x, y, w, h = 50, 80, 500, 550
    img_crop = img[y:y+h, x:x+w].reshape(-1, 3)
    ref_crop = ref[y:y+h, x:x+w].reshape(-1, 3)

    # Solve for 3x3 color correction matrix using least squares
    A, _, _, _ = np.linalg.lstsq(img_crop, ref_crop, rcond=None)

    corrected = np.dot(img.reshape(-1, 3), A).reshape(img.shape)
    corrected = np.clip(corrected, 0, 1)
    corrected = (corrected * 255).astype('uint8')

    cv2.imwrite(str(image_path), corrected)
    logging.info(f"Color corrected (from reference) image saved: {image_path}")

capture_camera('/dev/video0', top_filename, top_archive_filename, "Top Camera")
apply_color_correction_from_reference(top_filename, Path('/home/tcar5787/Documents/hydromonitor_v2/reference_white.png'))

time.sleep(1)

capture_camera('/dev/video2', bottom_filename, bottom_archive_filename, "Bottom Camera")
apply_color_correction_from_reference(bottom_filename, Path('/home/tcar5787/Documents/hydromonitor_v2/reference_white.png'))