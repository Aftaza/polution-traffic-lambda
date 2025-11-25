from typing import Dict, Any, List, Tuple
from .data_models import LocationData, IngestionResult
import pandas as pd
from datetime import datetime


class DataProcessor:
    """Class for processing and transforming environmental data."""
    
    @staticmethod
    def calculate_traffic_level(free_flow_speed: float, current_speed: float) -> int:
        """
        Calculate traffic level based on speed ratio.
        Returns 1-5 where 5 is most congested.
        """
        if free_flow_speed <= 0:
            return 1

        ratio = (free_flow_speed - current_speed) / free_flow_speed
        if ratio < 0.1:
            return 1  # Light traffic
        elif ratio < 0.3:
            return 2
        elif ratio < 0.5:
            return 3
        elif ratio < 0.7:
            return 4
        else:
            return 5  # Heavy traffic

    @staticmethod
    def normalize_aqi(aqi_value: Any) -> int:
        """Normalize AQI value to integer."""
        if aqi_value is None:
            return 0

        try:
            val = int(aqi_value)
            return val
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def extract_location_data(
        location_name: str,
        lat: float,
        lon: float,
        traffic_data: Dict[str, Any],
        aqi_data: Dict[str, Any]
    ) -> IngestionResult:
        """Extract and process location data from API responses."""
        current_timestamp = datetime.now()
        
        # Process traffic data
        traffic_level = 1
        if "flowSegmentData" in traffic_data:
            flow_data = traffic_data["flowSegmentData"]
            ff_speed = flow_data.get("freeFlowSpeed", 0)
            curr_speed = flow_data.get("currentSpeed", 0)
            
            traffic_level = DataProcessor.calculate_traffic_level(ff_speed, curr_speed)
        
        # Process AQI data
        aqi_value = None
        if aqi_data.get("status") == "ok":
            try:
                aqi_value = int(aqi_data["data"].get("aqi"))
            except (ValueError, TypeError):
                aqi_value = None
        
        # Create LocationData instance
        location_data = LocationData(
            timestamp=current_timestamp,
            location=location_name,
            latitude=lat,
            longitude=lon,
            aqi_value=aqi_value,
            traffic_level=traffic_level
        )
        
        return IngestionResult(
            location=location_name,
            aqi_value=aqi_value,
            traffic_level=traffic_level,
            success=(aqi_value is not None),
            error_message=None if aqi_value is not None else "AQI value is None"
        )