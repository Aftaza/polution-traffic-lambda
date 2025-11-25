import pandas as pd
from typing import List, Optional, Dict, Any
from .data_models import LocationData
from sqlalchemy import text


class DataRepository:
    """Repository class for database operations using SQLAlchemy."""

    def __init__(self, db_connection):
        self.db_connection = db_connection

    def insert_location_data(self, location_data: LocationData) -> bool:
        """Insert location data into raw_data table."""
        conn = None
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                return False

            insert_query = text("""
            INSERT INTO raw_data (timestamp, location, latitude, longitude, aqi_value, traffic_level)
            VALUES (:timestamp, :location, :latitude, :longitude, :aqi_value, :traffic_level)
            """)

            conn.execute(insert_query, {
                'timestamp': location_data.timestamp,
                'location': location_data.location,
                'latitude': location_data.latitude,
                'longitude': location_data.longitude,
                'aqi_value': location_data.aqi_value,
                'traffic_level': location_data.traffic_level
            })
            conn.commit()
            return True

        except Exception as e:
            print(f"Database Error: {e}")
            if conn:
                conn.rollback()
            return False

        finally:
            if conn:
                conn.close()

    def get_realtime_heatmap_data(self) -> tuple:
        """Get the latest 100 records for heatmap visualization."""
        try:
            # Get the SQLAlchemy engine instead of a connection for pandas
            engine = self.db_connection.get_engine()
            if not engine:
                return pd.DataFrame(), "Error"

            query = "SELECT * FROM raw_data ORDER BY timestamp DESC LIMIT 100"
            df_raw = pd.read_sql(query, engine)

            if df_raw.empty:
                return pd.DataFrame(), "Data Kosong"

            # Normalize AQI values and handle null values
            df_raw['aqi_clean'] = df_raw['aqi_value'].apply(self.normalize_aqi)

            # Handle cases where latitude/longitude might be problematic
            df_raw = df_raw.dropna(subset=['latitude', 'longitude'])

            if df_raw.empty:
                return pd.DataFrame(), "Data Kosong"

            last_update = df_raw['timestamp'].max()

            # Ensure coordinate columns are float type
            df_raw['latitude'] = df_raw['latitude'].astype(float)
            df_raw['longitude'] = df_raw['longitude'].astype(float)

            return df_raw, last_update

        except Exception as e:
            print(f"Database Error: {e}")
            return pd.DataFrame(), "Error"
    
    @staticmethod
    def normalize_aqi(aqi_value: Any) -> int:
        """Normalize AQI value to integer."""
        try:
            val = int(aqi_value)
            return val
        except (ValueError, TypeError):
            return 0