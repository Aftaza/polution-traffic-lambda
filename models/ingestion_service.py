from .api_client import TomTomAPIClient, AQICNAPIClient
from .data_processor import DataProcessor
from .data_repository import DataRepository
from .data_models import APIConfiguration, IngestionResult
import time
from apscheduler.schedulers.background import BackgroundScheduler
from typing import List, Dict, Any
import logging


class IngestionService:
    """Service class for data ingestion from APIs to database."""
    
    def __init__(self, db_connection, config: APIConfiguration):
        self.db_connection = db_connection
        self.config = config
        self.tomtom_client = TomTomAPIClient(config)
        self.aqicn_client = AQICNAPIClient(config)
        self.data_processor = DataProcessor()
        self.repository = DataRepository(db_connection)
        
        # Default locations for polling
        self.polling_locations = [
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
    
    def fetch_and_insert_data(self) -> List[IngestionResult]:
        """Fetch data from APIs and insert into database."""
        results = []
        
        for location in self.polling_locations:
            lat = location["lat"]
            lon = location["lon"]
            name = location["name"]
            
            try:
                # Fetch data from APIs
                traffic_data = self.tomtom_client.get_traffic_data(lat, lon)
                aqi_data = self.aqicn_client.get_aqi_data(lat, lon)
                
                # Extract and process data
                ingestion_result = DataProcessor.extract_location_data(
                    name, lat, lon, traffic_data, aqi_data
                )
                
                if ingestion_result.success:
                    # Insert data to database
                    from .data_models import LocationData
                    from datetime import datetime

                    location_data = LocationData(
                        timestamp=datetime.now(),
                        location=name,
                        latitude=lat,
                        longitude=lon,
                        aqi_value=ingestion_result.aqi_value,
                        traffic_level=ingestion_result.traffic_level
                    )

                    success = self.repository.insert_location_data(location_data)
                    ingestion_result.success = success
                
                results.append(ingestion_result)
                
                # Log the result
                if ingestion_result.success:
                    print(f" Ingest: {name} | AQI: {ingestion_result.aqi_value} | Traffic: {ingestion_result.traffic_level}")
                else:
                    print(f" Skip {name}: {ingestion_result.error_message}")
                    
            except Exception as e:
                error_result = IngestionResult(
                    location=name,
                    aqi_value=None,
                    traffic_level=None,
                    success=False,
                    error_message=str(e)
                )
                results.append(error_result)
                print(f" Error processing {name}: {e}")
        
        return results
    
    def start_scheduler(self, interval_seconds: int = 15):
        """Start the background scheduler for periodic data ingestion."""
        scheduler = BackgroundScheduler()
        scheduler.add_job(self.fetch_and_insert_data, 'interval', seconds=interval_seconds)
        scheduler.start()
        print(" Ingestion Service Scheduler Started (Multi-Location)...")

        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()