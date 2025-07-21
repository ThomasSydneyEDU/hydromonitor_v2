#!/usr/bin/env python3
import os
import firebase_admin
from firebase_admin import credentials, storage

# --- CONFIG ---
SERVICE_ACCOUNT_KEY_PATH = '/Users/tcar5787/APIKeys/hydrowebkey/serviceAccountKey.json'
BUCKET_NAME = 'hydroweb-fe1ae.firebasestorage.app' 
LOCAL_IMAGE_PATH = 'TopCamera.jpg'  # Change this to test a different image
REMOTE_IMAGE_PATH = 'TopCamera.jpg'  # This will appear in the Firebase bucket

# --- INITIALIZE FIREBASE ---
if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
    firebase_admin.initialize_app(cred, {
        'storageBucket': BUCKET_NAME
    })

# --- UPLOAD TO FIREBASE ---
bucket = storage.bucket()

if os.path.exists(LOCAL_IMAGE_PATH):
    blob = bucket.blob(REMOTE_IMAGE_PATH)
    blob.upload_from_filename(LOCAL_IMAGE_PATH, content_type='image/jpeg')

    # Make public (optional, only if your bucket settings allow it)
    blob.make_public()
    print(f"Upload successful. Public URL: {blob.public_url}")
else:
    print(f"Image file not found: {LOCAL_IMAGE_PATH}")