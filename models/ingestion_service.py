from .api_client import TomTomAPIClient, AQICNAPIClient
from .data_processor import DataProcessor
from .data_repository import DataRepository
from .data_models import APIConfiguration, IngestionResult
from .kafka_producer import KafkaProducerWrapper
import time
from apscheduler.schedulers.background import BackgroundScheduler
from typing import List, Dict, Any
from datetime import datetime
import logging


class IngestionService:
    """Service class for data ingestion from APIs to Kafka (Lambda Architecture - Ingestion Layer)."""
    
    def __init__(self, db_connection, config: APIConfiguration):
        self.db_connection = db_connection
        self.config = config
        self.tomtom_client = TomTomAPIClient(config)
        self.aqicn_client = AQICNAPIClient(config)
        self.data_processor = DataProcessor()
        self.repository = DataRepository(db_connection)
        
        # Initialize Kafka Producer
        self.kafka_producer = KafkaProducerWrapper()
        
        # Default locations for polling
        # Note: id_station is used for AQICN API, lat/lon are used for TomTom API
        self.polling_locations = [
            {"id_station": "A521365", "lat": -6.1861, "lon": 106.8236, "name": "Kebon Sirih"},
            {"id_station": "A495982", "lat": -6.1593, "lon": 106.8180, "name": "Krukut"},
            {"id_station": "A416842", "lat": -6.2154, "lon": 106.8030, "name": "GBK, Gelora"},
            {"id_station": "A531565", "lat": -6.2338, "lon": 106.8769, "name": "Jakarta Timur Kebon Nanas"},
            {"id_station": "A515938", "lat": -6.1756, "lon": 106.6449, "name": "Tangerang Benteng Betawi"},
            {"id_station": "A521380", "lat": -6.1714, "lon": 106.7622, "name": "Kedoya Utara"},
            {"id_station": "A570235", "lat": -6.2224, "lon": 106.7883, "name": "Grogol Utara"},
            {"id_station": "A537937", "lat": -6.2373, "lon": 106.7861, "name": "Gunung"},
            {"id_station": "A511573", "lat": -6.3498, "lon": 106.7782, "name": "Cinere"},
            {"id_station": "@8294", "lat": -6.1911, "lon": 106.8491, "name": "Kemayoran"}
        ]
    
    def fetch_and_insert_data(self) -> List[IngestionResult]:
        """Fetch data from APIs and publish to Kafka (and also backup to raw_data)."""
        results = []
        
        for location in self.polling_locations:
            lat = location["lat"]
            lon = location["lon"]
            name = location["name"]
            id_station = location["id_station"]
            
            try:
                # Fetch data from APIs
                # TomTom uses lat/lon, AQICN uses station_id
                traffic_data = self.tomtom_client.get_traffic_data(lat, lon)
                aqi_data = self.aqicn_client.get_aqi_data(id_station)
                
                # Extract and process data
                ingestion_result = DataProcessor.extract_location_data(
                    name, lat, lon, traffic_data, aqi_data
                )
                
                if ingestion_result.success:
                    # Create message payload
                    timestamp = datetime.now()
                    message_payload = {
                        'timestamp': timestamp.isoformat(),
                        'location': name,
                        'latitude': float(lat),
                        'longitude': float(lon),
                        'aqi_value': ingestion_result.aqi_value,
                        'traffic_level': ingestion_result.traffic_level
                    }
                    
                    # Send to Kafka (primary path)
                    kafka_success = self.kafka_producer.send_location_data(message_payload)
                    
                    # Also save to raw_data for backup and batch processing (Lambda Architecture - All Data path)
                    if kafka_success:
                        from .data_models import LocationData
                        location_data = LocationData(
                            timestamp=timestamp,
                            location=name,
                            latitude=lat,
                            longitude=lon,
                            aqi_value=ingestion_result.aqi_value,
                            traffic_level=ingestion_result.traffic_level
                        )
                        db_success = self.repository.insert_location_data(location_data)
                        ingestion_result.success = kafka_success and db_success
                    else:
                        ingestion_result.success = False
                        ingestion_result.error_message = "Failed to send to Kafka"
                
                results.append(ingestion_result)
                
                # Log the result
                if ingestion_result.success:
                    print(f"✅ Ingest→Kafka: {name} | AQI: {ingestion_result.aqi_value} | Traffic: {ingestion_result.traffic_level}")
                else:
                    print(f"❌ Skip {name}: {ingestion_result.error_message}")
                    
            except Exception as e:
                error_result = IngestionResult(
                    location=name,
                    aqi_value=None,
                    traffic_level=None,
                    success=False,
                    error_message=str(e)
                )
                results.append(error_result)
                print(f"❌ Error processing {name}: {e}")
        
        return results
    
    def start_scheduler(self, interval_seconds: int = 15):
        """Start the background scheduler for periodic data ingestion."""
        scheduler = BackgroundScheduler()
        scheduler.add_job(self.fetch_and_insert_data, 'interval', seconds=interval_seconds)
        scheduler.start()
        print("🚀 Ingestion Service Scheduler Started (Kafka Producer + Multi-Location)...")

        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            print("🛑 Shutting down ingestion service...")
            self.kafka_producer.close()
            scheduler.shutdown()