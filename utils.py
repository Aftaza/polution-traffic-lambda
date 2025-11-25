import os
from dotenv import load_dotenv
from models.data_models import APIConfiguration


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


def format_datetime_for_display(dt):
    """Format datetime for display in the UI."""
    if isinstance(dt, str):
        return dt
    else:
        return dt.strftime('%Y-%m-%d %H:%M:%S')