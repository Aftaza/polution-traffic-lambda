import psycopg2
import pandas as pd
from typing import List, Optional, Dict, Any
from .data_models import LocationData


class DataRepository:
    """Repository class for database operations."""
    
    def __init__(self, db_connection):
        self.db_connection = db_connection
    
    def insert_location_data(self, location_data: LocationData) -> bool:
        """Insert location data into raw_data table."""
        conn = None
        cur = None
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                return False
            
            cur = conn.cursor()
            insert_query = """
            INSERT INTO raw_data (timestamp, location, latitude, longitude, aqi_value, traffic_level)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cur.execute(insert_query, (
                location_data.timestamp,
                location_data.location,
                location_data.latitude,
                location_data.longitude,
                location_data.aqi_value,
                location_data.traffic_level
            ))
            conn.commit()
            return True
        
        except Exception as e:
            print(f"Database Error: {e}")
            if conn:
                conn.rollback()
            return False
        
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
    
    def get_realtime_heatmap_data(self) -> tuple:
        """Get the latest 100 records for heatmap visualization."""
        conn = None
        try:
            conn = self.db_connection.get_connection()
            query = "SELECT * FROM raw_data ORDER BY timestamp DESC LIMIT 100"
            df_raw = pd.read_sql(query, conn)

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

        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def normalize_aqi(aqi_value: Any) -> int:
        """Normalize AQI value to integer."""
        try:
            val = int(aqi_value)
            return val
        except (ValueError, TypeError):
            return 0