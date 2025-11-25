import os
from dotenv import load_dotenv
from models.data_models import APIConfiguration
from datetime import datetime, timezone, timedelta
import pandas as pd


def load_configuration():
    """Load configuration from environment variables or .env file."""
    load_dotenv()
    
    tomtom_api_key = os.getenv("TOMTOM_API_KEY")
    aqicn_token = os.getenv("AQICN_TOKEN")
    
    if not tomtom_api_key or not aqicn_token:
        raise ValueError("TOMTOM_API_KEY and AQICN_TOKEN must be set in environment variables or .env file")
    
    return APIConfiguration(
        tomtom_api_key=tomtom_api_key,
        aqicn_token=aqicn_token
    )


def get_jakarta_timezone():
    """Get UTC+7 timezone for Jakarta."""
    return timezone(timedelta(hours=7))


def format_datetime_for_display(dt):
    """Format datetime for display in the UI with UTC+7 timezone."""
    if isinstance(dt, str):
        return dt
    else:
        # Convert to UTC+7 if not already timezone-aware
        jakarta_tz = get_jakarta_timezone()
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc).astimezone(jakarta_tz)
        else:
            dt = dt.astimezone(jakarta_tz)
        return dt.strftime('%Y-%m-%d %H:%M:%S WIB')


def get_aqi_category(aqi_value):
    """Get AQI category and color based on value."""
    if aqi_value <= 50:
        return "Good", "#4CAF50"
    elif aqi_value <= 100:
        return "Moderate", "#FFEB3B"
    elif aqi_value <= 150:
        return "Unhealthy for Sensitive Groups", "#FF9800"
    elif aqi_value <= 200:
        return "Unhealthy", "#F44336"
    elif aqi_value <= 300:
        return "Very Unhealthy", "#9C27B0"
    else:
        return "Hazardous", "#7B1FA2"


def analyze_peak_hours(df):
    """Analyze peak hours for traffic and pollution from the dataframe."""
    if df.empty:
        return None
    
    # Make a copy to avoid modifying original
    df_analysis = df.copy()
    
    # Convert timestamp to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(df_analysis['timestamp']):
        df_analysis['timestamp'] = pd.to_datetime(df_analysis['timestamp'])
    
    # Convert to UTC+7 timezone
    jakarta_tz = get_jakarta_timezone()
    
    # Check if already timezone-aware
    if df_analysis['timestamp'].dt.tz is None:
        # Not timezone-aware, localize first
        df_analysis['timestamp_jakarta'] = df_analysis['timestamp'].dt.tz_localize('UTC').dt.tz_convert(jakarta_tz)
    else:
        # Already timezone-aware, just convert
        df_analysis['timestamp_jakarta'] = df_analysis['timestamp'].dt.tz_convert(jakarta_tz)
    
    # Extract hour
    df_analysis['hour'] = df_analysis['timestamp_jakarta'].dt.hour
    
    # Group by hour and calculate averages
    hourly_stats = df_analysis.groupby('hour').agg({
        'aqi_value': 'mean',
        'traffic_level': 'mean'
    }).round(2)
    
    # Find peak hours
    peak_aqi_hour = hourly_stats['aqi_value'].idxmax()
    peak_traffic_hour = hourly_stats['traffic_level'].idxmax()
    
    peak_aqi_value = hourly_stats['aqi_value'].max()
    peak_traffic_value = hourly_stats['traffic_level'].max()
    
    return {
        'peak_aqi_hour': peak_aqi_hour,
        'peak_aqi_value': peak_aqi_value,
        'peak_traffic_hour': peak_traffic_hour,
        'peak_traffic_value': peak_traffic_value,
        'hourly_stats': hourly_stats
    }