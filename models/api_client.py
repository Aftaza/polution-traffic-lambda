import requests
import os
from typing import Dict, Any, Optional
from .data_models import APIConfiguration


class TomTomAPIClient:
    """API client for TomTom traffic data."""
    
    def __init__(self, config: APIConfiguration):
        self.api_key = config.tomtom_api_key
        self.base_url = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
    
    def get_traffic_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get traffic data for a specific location."""
        url = f"{self.base_url}?point={lat},{lon}&key={self.api_key}"
        response = requests.get(url)
        return response.json()


class AQICNAPIClient:
    """API client for AQICN air quality data."""
    
    def __init__(self, config: APIConfiguration):
        self.token = config.aqicn_token
        self.base_url = "https://api.waqi.info/feed"
    
    def get_aqi_data(self, station_id: str) -> Dict[str, Any]:
        """Get AQI data for a specific station ID.
        
        Args:
            station_id: The AQICN station ID (e.g., 'A416857' for Depok)
            
        Returns:
            Dict containing AQI data from the station
        """
        url = f"{self.base_url}/{station_id}/?token={self.token}"
        response = requests.get(url)
        return response.json()