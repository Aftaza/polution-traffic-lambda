import json
from kafka import KafkaConsumer
from db_connector import get_db_connection
import time
import os
from datetime import datetime

# --- Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = "traffic-pollution-data"
KAFKA_GROUP_ID = "traffic-pollution-consumer-group"

# Peak hours definition (Jakarta rush hours)
MORNING_PEAK = (6, 10)  # 6 AM - 10 AM
EVENING_PEAK = (16, 20)  # 4 PM - 8 PM

def is_peak_hour(timestamp_str):
    """Check if timestamp is during peak hours"""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        hour = dt.hour
        return (MORNING_PEAK[0] <= hour < MORNING_PEAK[1]) or (EVENING_PEAK[0] <= hour < EVENING_PEAK[1])
    except:
        return False

def get_aqi_category(aqi_value):
    """Categorize AQI value"""
    if aqi_value <= 50:
        return "Good"
    elif aqi_value <= 100:
        return "Moderate"
    elif aqi_value <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi_value <= 200:
        return "Unhealthy"
    elif aqi_value <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"

def create_kafka_consumer():
    """Create Kafka consumer with retry logic"""
    max_retries = 10
    for attempt in range(max_retries):
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=KAFKA_GROUP_ID,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                consumer_timeout_ms=1000
            )
            print(f"✅ Kafka Consumer connected on attempt {attempt + 1}")
            return consumer
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⏳ Kafka connection failed (attempt {attempt + 1}): {e}. Retrying in 5s...")
                time.sleep(5)
            else:
                raise e
    return None

def consume_and_store():
    """Consume messages from Kafka and store in PostgreSQL"""
    consumer = create_kafka_consumer()
    
    if not consumer:
        print("❌ Failed to create Kafka consumer")
        return
    
    print(f"🎧 Consumer listening to topic: {KAFKA_TOPIC}")
    
    try:
        for message in consumer:
            conn = None
            cur = None
            try:
                data = message.value
                
                conn = get_db_connection()
                if not conn:
                    print("❌ No database connection")
                    continue
                
                cur = conn.cursor()
                
                # Determine if peak hour
                peak_hour = is_peak_hour(data['timestamp'])
                
                # Get AQI category
                aqi_category = get_aqi_category(data['aqi_value'])
                
                # Insert into TRAFFIC_DATA table (NOT raw_data view!)
                traffic_query = """
                INSERT INTO traffic_data (timestamp, location, latitude, longitude, traffic_level, is_peak_hour)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cur.execute(traffic_query, (
                    data['timestamp'],
                    data['location'],
                    data['latitude'],
                    data['longitude'],
                    data['traffic_level'],
                    peak_hour
                ))
                
                # Insert into AQI_DATA table (NOT raw_data view!)
                aqi_query = """
                INSERT INTO aqi_data (timestamp, location, latitude, longitude, aqi_value, aqi_category)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                cur.execute(aqi_query, (
                    data['timestamp'],
                    data['location'],
                    data['latitude'],
                    data['longitude'],
                    data['aqi_value'],
                    aqi_category
                ))
                
                # Update peak hours analysis (hourly aggregation)
                dt = datetime.fromisoformat(data['timestamp'])
                peak_analysis_query = """
                INSERT INTO peak_hours_analysis (date, hour, location, avg_traffic_level, avg_aqi_value, is_peak_hour, total_records)
                VALUES (%s, %s, %s, %s, %s, %s, 1)
                ON CONFLICT (date, hour, location)
                DO UPDATE SET
                    avg_traffic_level = (peak_hours_analysis.avg_traffic_level * peak_hours_analysis.total_records + EXCLUDED.avg_traffic_level) / (peak_hours_analysis.total_records + 1),
                    avg_aqi_value = (peak_hours_analysis.avg_aqi_value * peak_hours_analysis.total_records + EXCLUDED.avg_aqi_value) / (peak_hours_analysis.total_records + 1),
                    total_records = peak_hours_analysis.total_records + 1
                """
                cur.execute(peak_analysis_query, (
                    dt.date(),
                    dt.hour,
                    data['location'],
                    data['traffic_level'],
                    data['aqi_value'],
                    peak_hour
                ))
                
                conn.commit()
                
                peak_indicator = "🔴 PEAK" if peak_hour else "🟢 OFF-PEAK"
                print(f"💾 Stored: {data['location']} | AQI: {data['aqi_value']} ({aqi_category}) | Traffic: {data['traffic_level']} | {peak_indicator}")
                
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                if conn:
                    conn.rollback()
            finally:
                if cur:
                    cur.close()
                if conn:
                    conn.close()
                
    except KeyboardInterrupt:
        print("🛑 Consumer shutting down...")
    finally:
        consumer.close()
        print("✅ Consumer closed")

if __name__ == '__main__':
    print("🚀 Consumer Service Starting...")
    consume_and_store()