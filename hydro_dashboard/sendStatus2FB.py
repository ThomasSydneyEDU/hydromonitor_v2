import os
import time
import json
from datetime import datetime, timedelta
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import traceback
import pytz


# --- Configuration ---
SERVICE_ACCOUNT_KEY_PATH = '/home/tcar5787/APIkeys/hydrowebkey/serviceAccountKey.json'
STATUS_JSON_PATH = '/home/tcar5787/Documents/hydromonitor_v2/hydro_dashboard/status.json'
FIRESTORE_COLLECTION_5MIN = 'Current Days Log'
LOCAL_RAW_DATA_PATH = '/home/tcar5787/Documents/hydromonitor_v2/hydro_dashboard/local_5min_records.pkl'
LOCAL_AGG_DATA_PATH = '/home/tcar5787/Documents/hydromonitor_v2/hydro_dashboard/local_2hour_aggregates.csv'
AGGREGATE_INTERVAL = 2 * 60 * 60  # 2 hours in seconds
CHECK_INTERVAL = 5 * 60  # 5 minutes in seconds

def initialize_firebase():
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
            firebase_admin.initialize_app(cred)
            print(f"[INFO] Firebase initialized successfully.")
        else:
            print(f"[INFO] Firebase already initialized.")
        return firestore.client()
    except Exception as e:
        print(f"[ERROR] Firebase initialization failed: {e}")
        raise

def upload_status_to_firestore(db, status_data, timestamp_key, collection=FIRESTORE_COLLECTION_5MIN):
    try:
        # Convert sensor fields to floats before upload
        for key in ['Air Temp (Indoor)', 'Air Temp (Outdoor)', 'Humidity (Indoor)', 'Humidity (Outdoor)',
                    'Water Temp Top', 'Water Temp Bottom']:
            if key in status_data:
                try:
                    status_data[key] = float(str(status_data[key]).strip())
                except Exception:
                    status_data[key] = None

        print(f"[DEBUG] Preparing to upload to Firestore collection '{collection}' with doc ID '{timestamp_key}'")
        print(f"[DEBUG] Data: {status_data}")
        # Add local ISO 8601 timestamp for web clients
        local_tz = pytz.timezone("Australia/Sydney")
        status_data['timestamp_local'] = datetime.now(local_tz).isoformat()
        doc_ref = db.collection(collection).document(timestamp_key)
        doc_ref.set(status_data)
        print(f"[{datetime.now().isoformat()}] Uploaded status for {timestamp_key} to Firestore collection '{collection}'.")
    except Exception as e:
        print(f"[ERROR] Failed to upload to Firestore: {e}")

def get_5min_rounded_timestamp():
    tz = pytz.timezone("Australia/Sydney")
    now = datetime.now(tz)
    minute = (now.minute // 5) * 5
    rounded = now.replace(minute=minute, second=0, microsecond=0)
    time_str = rounded.strftime("log_%H-%M")
    return time_str

def load_local_data():
    if os.path.exists(LOCAL_RAW_DATA_PATH):
        try:
            return pd.read_pickle(LOCAL_RAW_DATA_PATH)
        except Exception as e:
            print(f"[WARN] Failed to load local raw data: {e}")
    # Return empty dataframe with expected columns
    columns = [
        'timestamp',
        'air_temp_indoor', 'air_temp_outdoor',
        'humidity_indoor', 'humidity_outdoor',
        'water_temp_top', 'water_temp_bottom',
        'relay_lights_top', 'relay_lights_bottom',
        'relay_pump_top', 'relay_pump_bottom',
        'relay_fan_vent', 'relay_fan_circ',
        'relay_heater',
        'float_top_low', 'float_bottom_low'
    ]
    return pd.DataFrame(columns=columns)

def save_local_data(df):
    try:
        df.to_pickle(LOCAL_RAW_DATA_PATH)
    except Exception as e:
        print(f"[ERROR] Failed to save local raw data: {e}")

def append_new_record(df, status_data):
    # Ensure timestamp is converted to pandas.Timestamp
    timestamp = status_data.get('timestamp')
    if timestamp:
        status_data['timestamp'] = pd.to_datetime(timestamp)
    else:
        status_data['timestamp'] = pd.Timestamp.now()

    # Convert relay states ON/OFF -> 1/0
    for relay_key in ['Relay Lights Top', 'Relay Lights Bottom',
                      'Relay Pump Top', 'Relay Pump Bottom',
                      'Relay Fan Vent', 'Relay Fan Circ',
                      'Relay Heater']:
        val = status_data.get(relay_key)
        col_name = relay_key.lower().replace(" ", "_")
        if isinstance(val, str):
            status_data[col_name] = 1 if val.upper() == 'ON' else 0
        else:
            status_data[col_name] = 0

    # Floats: mark 1 if ever "Low"
    for float_key in ['Top Float', 'Bottom Float']:
        val = status_data.get(float_key, '')
        col_name = float_key.lower().replace(" ", "_") + '_low'
        status_data[col_name] = 1 if str(val).lower() == 'low' else 0

    # Remove original relay/float keys to avoid duplicates
    for key in ['Relay Lights Top', 'Relay Lights Bottom', 'Relay Pump Top', 'Relay Pump Bottom',
                'Relay Fan Vent', 'Relay Fan Circ', 'Relay Heater', 'Top Float', 'Bottom Float']:
        if key in status_data:
            status_data.pop(key)


    # Convert sensor string fields to float or None
    for key in ['Air Temp (Indoor)', 'Air Temp (Outdoor)', 'Humidity (Indoor)', 'Humidity (Outdoor)',
                'Water Temp Top', 'Water Temp Bottom']:
        if key in status_data:
            try:
                status_data[key] = float(str(status_data[key]).strip())
            except Exception:
                status_data[key] = None

    # Rename sensor keys to match expected DataFrame columns
    sensor_rename_map = {
        'Air Temp (Indoor)': 'air_temp_indoor',
        'Air Temp (Outdoor)': 'air_temp_outdoor',
        'Humidity (Indoor)': 'humidity_indoor',
        'Humidity (Outdoor)': 'humidity_outdoor',
        'Water Temp Top': 'water_temp_top',
        'Water Temp Bottom': 'water_temp_bottom'
    }
    for old_key, new_key in sensor_rename_map.items():
        if old_key in status_data:
            status_data[new_key] = status_data.pop(old_key)

    # Remove keys not meant for dataframe
    for skip_key in ['data', 'note']:
        if skip_key in status_data:
            status_data.pop(skip_key)

    # Append new row safely
    return pd.concat([df, pd.DataFrame([status_data])], ignore_index=True)

def aggregate_2hour(df):
    if df.empty:
        return pd.DataFrame()

    tz = pytz.timezone("Australia/Sydney")
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize('UTC').dt.tz_convert(tz)
    df = df.dropna(subset=['timestamp'])
    df['time_bin'] = df['timestamp'].dt.floor('2H')

    def any_low(series):
        # Fill NaNs with 0 to avoid NaN sum issues
        return 1 if series.fillna(0).sum() > 0 else 0

    agg_funcs = {
        'air_temp_indoor': lambda x: x.dropna().mean(),
        'air_temp_outdoor': lambda x: x.dropna().mean(),
        'humidity_indoor': lambda x: x.dropna().mean(),
        'humidity_outdoor': lambda x: x.dropna().mean(),
        'water_temp_top': lambda x: x.dropna().mean(),
        'water_temp_bottom': lambda x: x.dropna().mean(),
        'relay_lights_top': lambda x: x.dropna().mean(),
        'relay_lights_bottom': lambda x: x.dropna().mean(),
        'relay_pump_top': lambda x: x.dropna().mean(),
        'relay_pump_bottom': lambda x: x.dropna().mean(),
        'relay_fan_vent': lambda x: x.dropna().mean(),
        'relay_fan_circ': lambda x: x.dropna().mean(),
        'relay_heater': lambda x: x.dropna().mean(),
        'float_top_low': any_low,
        'float_bottom_low': any_low
    }

    agg_df = df.groupby('time_bin').agg(agg_funcs).reset_index()
    agg_df.rename(columns={'time_bin': 'timestamp'}, inplace=True)

    float_cols = ['air_temp_indoor', 'air_temp_outdoor',
                  'humidity_indoor', 'humidity_outdoor',
                  'water_temp_top', 'water_temp_bottom']
    agg_df[float_cols] = agg_df[float_cols].round(2)

    relay_cols = ['relay_lights_top', 'relay_lights_bottom',
                  'relay_pump_top', 'relay_pump_bottom',
                  'relay_fan_vent', 'relay_fan_circ',
                  'relay_heater']
    agg_df[relay_cols] = (agg_df[relay_cols] * 100).round(1)

    return agg_df

def save_aggregates(agg_df):
    try:
        if os.path.exists(LOCAL_AGG_DATA_PATH):
            agg_df_existing = pd.read_csv(LOCAL_AGG_DATA_PATH, parse_dates=['timestamp'])
            agg_df = pd.concat([agg_df_existing, agg_df]).drop_duplicates(subset=['timestamp']).sort_values('timestamp')
        agg_df.to_csv(LOCAL_AGG_DATA_PATH, index=False)
    except Exception as e:
        print(f"[ERROR] Failed to save aggregates: {e}")

def main_loop():
    db = initialize_firebase()
    last_mod_time = None
    df = load_local_data()
    last_aggregate_time = datetime.now() - timedelta(seconds=AGGREGATE_INTERVAL)

    print(f"[{datetime.now().isoformat()}] Starting 5-minute interval status uploader with local aggregation...")

    while True:
        try:
            timestamp_key = get_5min_rounded_timestamp()

            if os.path.exists(STATUS_JSON_PATH):
                mod_time = os.path.getmtime(STATUS_JSON_PATH)
                if last_mod_time is None or mod_time > last_mod_time:
                    with open(STATUS_JSON_PATH, 'r') as f:
                        status_data = json.load(f)
                    last_mod_time = mod_time
                else:
                    status_data = {
                        "timestamp": timestamp_key,
                        "data": None,
                        "note": "No new data at this interval"
                    }
            else:
                status_data = {
                    "timestamp": timestamp_key,
                    "data": None,
                    "note": "Status file missing"
                }

            # Append to local dataframe and save raw data
            df = append_new_record(df, status_data)
            save_local_data(df)

            # Upload 5-min status record to Firestore
            print(f"[DEBUG] Uploading 5-minute status record at {timestamp_key}...")
            upload_status_to_firestore(db, status_data, timestamp_key)

            # Check if time to aggregate 2-hour data
            now = datetime.now()
            if (now - last_aggregate_time).total_seconds() >= AGGREGATE_INTERVAL:
                agg_df = aggregate_2hour(df)
                if not agg_df.empty:
                    save_aggregates(agg_df)
                    # Upload aggregates to Firestore under 'Hydro Records'
                    for _, row in agg_df.iterrows():
                        agg_doc_id = row['timestamp'].strftime("log_%Y-%m-%d_%H-%M")
                        print(f"[DEBUG] Uploading aggregate record at {row['timestamp']} to 'Hydro Records'")
                        upload_status_to_firestore(db, row.to_dict(), agg_doc_id, collection='Hydro Records')
                last_aggregate_time = now

            # Sleep until next 5-minute mark
            now = datetime.utcnow()
            next_time = (now + timedelta(minutes=5)).replace(second=0, microsecond=0)
            wait_seconds = (next_time - now).total_seconds()
            if wait_seconds < 0:
                wait_seconds = 0
            time.sleep(wait_seconds)

        except Exception as e:
            print(f"[{datetime.now().isoformat()}] Error in main loop: {e}")
            traceback.print_exc()
            time.sleep(30)  # short delay before retry

def supervisor():
    """Run the main loop but restart if stuck/crashes."""
    while True:
        start_time = time.time()
        try:
            main_loop()
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] Fatal error: {e}")
            traceback.print_exc()
        elapsed = time.time() - start_time
        if elapsed < 600:  # 10 minutes
            print(f"[{datetime.now().isoformat()}] Restarting main loop after short delay...")
            time.sleep(10)  # cool down before restart

if __name__ == "__main__":
    supervisor()