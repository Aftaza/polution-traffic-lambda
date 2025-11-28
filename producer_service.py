import requests
import json
from datetime import datetime
from kafka import KafkaProducer
from apscheduler.schedulers.background import BackgroundScheduler
import time
import os

# --- Kredensial API ---
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "a7wpPeCw8Uom3GEVdUbW7DA4rp1n9hex")
AQICN_TOKEN = os.getenv("AQICN_TOKEN", "bb97bec86e0cd851da1d9f21c3080c630bbaa18d")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = "traffic-pollution-data"

# --- LIST LOKASI ---
POLLING_LOCATIONS = [
    {"idx": "A521365", "lat": -6.1861, "lon": 106.8236, "name": "Kebon Sirih"},
    {"idx": "A495982", "lat": -6.1593, "lon": 106.8180, "name": "Krukut"},
    {"idx": "A416842", "lat": -6.2154, "lon": 106.8030, "name": "GBK, Gelora"},
    {"idx": "A531565", "lat": -6.2338, "lon": 106.8769, "name": "Jakarta Timur Kebon Nanas"},
    {"idx": "A515938", "lat": -6.1756, "lon": 106.6449, "name": "Tangerang Benteng Betawi"},
    {"idx": "A521380", "lat": -6.1714, "lon": 106.7622, "name": "Kedoya Utara"},
    {"idx": "A570235", "lat": -6.2224, "lon": 106.7883, "name": "Grogol Utara"},
    {"idx": "A537937", "lat": -6.2373, "lon": 106.7861, "name": "Gunung"},
    {"idx": "A511573", "lat": -6.3498, "lon": 106.7782, "name": "Cinere"},
    {"idx": "@8294", "lat": -6.1911, "lon": 106.8491, "name": "Kemayoran"}
]

def create_kafka_producer():
    """Create Kafka producer with retry logic"""
    max_retries = 10
    for attempt in range(max_retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            print(f"✅ Kafka Producer connected on attempt {attempt + 1}")
            return producer
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⏳ Kafka connection failed (attempt {attempt + 1}): {e}. Retrying in 5s...")
                time.sleep(5)
            else:
                raise e
    return None

# Initialize Kafka Producer
producer = create_kafka_producer()

def fetch_and_send_to_kafka():
    """Fetch data from APIs and send to Kafka topic"""
    try:
        current_timestamp = datetime.now().isoformat()
        
        for location in POLLING_LOCATIONS:
            POLLING_LAT = location["lat"]
            POLLING_LON = location["lon"]
            POLLING_IDX = location["idx"]
            LOCATION_NAME = location["name"]

            # --- 1. TRAFFIC (TomTom) ---
            tomtom_url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point={POLLING_LAT},{POLLING_LON}&key={TOMTOM_API_KEY}"
            traffic_response = requests.get(tomtom_url, timeout=10).json()

            traffic_level = 1
            if "flowSegmentData" in traffic_response:
                flow_data = traffic_response["flowSegmentData"]
                ff_speed = flow_data.get("freeFlowSpeed", 0) 
                curr_speed = flow_data.get("currentSpeed", 0)
                
                if ff_speed > 0:
                    ratio = (ff_speed - curr_speed) / ff_speed
                    if ratio < 0.1: traffic_level = 1
                    elif ratio < 0.3: traffic_level = 2
                    elif ratio < 0.5: traffic_level = 3
                    elif ratio < 0.7: traffic_level = 4
                    else: traffic_level = 5
            
            # --- 2. AQI (AQICN) ---
            aqicn_url = f"https://api.waqi.info/feed/{POLLING_IDX}/?token={AQICN_TOKEN}"
            aqi_resp = requests.get(aqicn_url, timeout=10).json()
            
            aqi_value = None
            if aqi_resp.get("status") == "ok":
                try:
                    aqi_value = int(aqi_resp["data"].get("aqi"))
                except:
                    aqi_value = None

            # --- 3. SEND TO KAFKA ---
            if aqi_value is not None:
                message = {
                    "timestamp": current_timestamp,
                    "location": LOCATION_NAME,
                    "latitude": POLLING_LAT,
                    "longitude": POLLING_LON,
                    "aqi_value": aqi_value,
                    "traffic_level": traffic_level
                }
                
                future = producer.send(KAFKA_TOPIC, value=message)
                future.get(timeout=10)
                
                print(f"📤 Sent to Kafka: {LOCATION_NAME} | AQI: {aqi_value} | Traffic: {traffic_level}")
            else:
                print(f"⚠️ Skip {LOCATION_NAME}: AQI None")
            
    except Exception as e:
        print(f"❌ Producer Error: {e}")

def start_scheduler():
    """Start background scheduler"""
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_and_send_to_kafka, 'interval', seconds=15)
    scheduler.start()
    print("🚀 Producer Service Started - Polling every 15 seconds...")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        if producer:
            producer.close()
        print("🛑 Producer Service Stopped")

if __name__ == '__main__':
    start_scheduler()