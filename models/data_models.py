from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class LocationData:
    """Data class for location-based environmental data."""
    timestamp: datetime
    location: str
    latitude: float
    longitude: float
    aqi_value: Optional[int]
    traffic_level: int
    is_processed: bool = False


@dataclass
class IngestionResult:
    """Data class for ingestion results."""
    location: str
    aqi_value: Optional[int]
    traffic_level: int
    success: bool
    error_message: Optional[str] = None


@dataclass
class APIConfiguration:
    """Configuration for API keys."""
    tomtom_api_key: str
    aqicn_token: str