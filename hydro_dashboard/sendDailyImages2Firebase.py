import os
import datetime
import subprocess
import firebase_admin
from firebase_admin import credentials, initialize_app, storage

# --- CONFIGURATION ---
SERVICE_ACCOUNT_KEY_PATH = '/home/tcar5787/APIkeys/hydrowebkey/serviceAccountKey.json'
# SERVICE_ACCOUNT_KEY_PATH = '/Users/tcar5787/APIKeys/hydrowebkey/serviceAccountKey.json'
BUCKET_NAME = 'hydroweb-fe1ae.firebasestorage.app' 
LOCAL_TOP_IMG = 'TopCamera.jpg'
LOCAL_BOTTOM_IMG = 'BottomCamera.jpg'
REMOTE_FOLDER = 'daily-images'

# --- INIT FIREBASE ---
if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
    initialize_app(cred, {'storageBucket': BUCKET_NAME})

bucket = storage.bucket()

# --- GET DATE STAMP ---
today = datetime.datetime.now().strftime("%d-%m-%Y")
remote_top_name = f'{REMOTE_FOLDER}/TopCamera_{today}.jpg'
remote_bottom_name = f'{REMOTE_FOLDER}/BottomCamera_{today}.jpg'

overwrite_top_name = f'{REMOTE_FOLDER}/TopCamera.jpg'
overwrite_bottom_name = f'{REMOTE_FOLDER}/BottomCamera.jpg'

# --- CAPTURE IMAGES ---
subprocess.run(['fswebcam', '-d', '/dev/video0', LOCAL_TOP_IMG], check=True)
subprocess.run(['fswebcam', '-d', '/dev/video2', LOCAL_BOTTOM_IMG], check=True)

# --- UPLOAD IMAGES ---
def upload_to_firebase(local_path, remote_path):
    blob = bucket.blob(remote_path)
    blob.upload_from_filename(local_path)
    print(f'Uploaded {local_path} to {remote_path}')

upload_to_firebase(LOCAL_TOP_IMG, remote_top_name)
upload_to_firebase(LOCAL_BOTTOM_IMG, remote_bottom_name)

upload_to_firebase(LOCAL_TOP_IMG, overwrite_top_name)
upload_to_firebase(LOCAL_BOTTOM_IMG, overwrite_bottom_name)

print('Upload complete.')