import requests
import pandas as pd
from datetime import datetime
from db_connector import get_db_connection
from apscheduler.schedulers.background import BackgroundScheduler
import time
import os

# --- Kredensial API ---
TOMTOM_API_KEY = "a7wpPeCw8Uom3GEVdUbW7DA4rp1n9hex"
AQICN_TOKEN = "bb97bec86e0cd851da1d9f21c3080c630bbaa18d"

# --- LIST LOKASI (Agar Map Penuh/Tersebar) ---
POLLING_LOCATIONS = [
    {"lat": -6.1754, "lon": 106.8272, "name": "Bundaran HI"},
    {"lat": -6.2297, "lon": 106.7749, "name": "Palmerah"},
    {"lat": -6.2420, "lon": 106.8080, "name": "Blok M"},
    {"lat": -6.2605, "lon": 106.9038, "name": "Bekasi Barat"},
    {"lat": -6.1770, "lon": 106.6000, "name": "Bandara Soetta"},
    {"lat": -6.1911, "lon": 106.8491, "name": "Kemayoran"},
    {"lat": -6.2831, "lon": 106.7212, "name": "Pondok Indah"},
    {"lat": -6.1523, "lon": 106.8650, "name": "Tanjung Priok"},
    {"lat": -6.1400, "lon": 106.8200, "name": "Pluit"},
    {"lat": -6.3000, "lon": 106.8200, "name": "Cilandak"}
]

def fetch_and_insert_data():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if not conn:
            print("❌ Tidak ada koneksi DB.")
            return

        cur = conn.cursor()
        current_timestamp = pd.to_datetime('now')
        
        # Loop lokasi agar data bervariasi di peta
        for location in POLLING_LOCATIONS:
            POLLING_LAT = location["lat"]
            POLLING_LON = location["lon"]
            LOCATION_NAME = location["name"]

            # --- 1. TRAFFIC (TomTom) ---
            tomtom_url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point={POLLING_LAT},{POLLING_LON}&key={TOMTOM_API_KEY}"
            traffic_response = requests.get(tomtom_url).json()

            traffic_level = 1
            if "flowSegmentData" in traffic_response:
                flow_data = traffic_response["flowSegmentData"]
                ff_speed = flow_data.get("freeFlowSpeed", 0) 
                curr_speed = flow_data.get("currentSpeed", 0)
                
                # Logika Traffic Level 1-5
                if ff_speed > 0:
                    ratio = (ff_speed - curr_speed) / ff_speed
                    if ratio < 0.1: traffic_level = 1
                    elif ratio < 0.3: traffic_level = 2
                    elif ratio < 0.5: traffic_level = 3
                    elif ratio < 0.7: traffic_level = 4
                    else: traffic_level = 5
            
            # --- 2. AQI (AQICN - Geo Polling) ---
            # Menggunakan koordinat agar mendapat data real di titik tersebut
            aqicn_url = f"https://api.waqi.info/feed/geo:{POLLING_LAT};{POLLING_LON}/?token={AQICN_TOKEN}"
            aqi_resp = requests.get(aqicn_url).json()
            
            aqi_value = None
            if aqi_resp.get("status") == "ok":
                try:
                    aqi_value = int(aqi_resp["data"].get("aqi"))
                except:
                    aqi_value = None

            # --- 3. INSERT KE DATABASE ---
            if aqi_value is not None:
                insert_query = """
                INSERT INTO raw_data (timestamp, location, latitude, longitude, aqi_value, traffic_level)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cur.execute(insert_query, (
                    current_timestamp, 
                    LOCATION_NAME, 
                    POLLING_LAT, 
                    POLLING_LON, 
                    aqi_value, 
                    traffic_level
                ))
                conn.commit()
                print(f" Ingest: {LOCATION_NAME} | AQI: {aqi_value} | Traffic: {traffic_level}")
            else:
                 print(f" Skip {LOCATION_NAME}: AQI None")
            
    except Exception as e:
        print(f" Error: {e}")
        if conn: conn.rollback()
    finally:
        if cur: cur.close()
        if conn: conn.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Poll setiap 15 detik agar tidak kena rate limit API
    scheduler.add_job(fetch_and_insert_data, 'interval', seconds=15)
    scheduler.start()
    print(" Ingestion Service Scheduler Started (Multi-Location)...")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == '__main__':
    start_scheduler()