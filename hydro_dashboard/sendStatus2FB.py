import os
import time
import json
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# --- Configuration ---

# Path to your Firebase service account key JSON file
SERVICE_ACCOUNT_KEY_PATH = '/home/tcar5787/APIkeys/hydrowebkey/serviceAccountKey.json'

# Path to the local status.json file
STATUS_JSON_PATH = '/home/tcar5787/Documents/hydromonitor_v2/hydro_dashboard/status.json'

# Firestore collection and document to update
FIRESTORE_COLLECTION = 'hydroponics'
FIRESTORE_DOCUMENT = 'status_latest'

# Check interval in seconds (20 minutes)
CHECK_INTERVAL = 20 * 60


def initialize_firebase():
    """Initialize Firebase Admin SDK and return Firestore client."""
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
    firebase_admin.initialize_app(cred)
    return firestore.client()


def upload_status_to_firestore(db, status_data):
    """Upload the status dictionary to Firestore."""
    doc_ref = db.collection(FIRESTORE_COLLECTION).document(FIRESTORE_DOCUMENT)
    doc_ref.set(status_data)
    print(f"[{datetime.now().isoformat()}] Uploaded status to Firestore.")


def main():
    db = initialize_firebase()

    last_mod_time = None

    print(f"[{datetime.now().isoformat()}] Starting status.json watcher...")

    while True:
        try:
            if os.path.exists(STATUS_JSON_PATH):
                mod_time = os.path.getmtime(STATUS_JSON_PATH)

                if last_mod_time is None or mod_time > last_mod_time:
                    print(f"[{datetime.now().isoformat()}] Detected change in status.json.")

                    with open(STATUS_JSON_PATH, 'r') as f:
                        status_data = json.load(f)

                    upload_status_to_firestore(db, status_data)
                    last_mod_time = mod_time
                else:
                    print(f"[{datetime.now().isoformat()}] No change detected.")

            else:
                print(f"[{datetime.now().isoformat()}] Status file not found: {STATUS_JSON_PATH}")

        except Exception as e:
            print(f"[{datetime.now().isoformat()}] Error: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()