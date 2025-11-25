from typing import Tuple, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import logging
from sqlalchemy import text


class ServingLayer:
    """Serving layer that combines Batch Layer and Speed Layer data."""
    
    def __init__(self, db_connection):
        """
        Initialize serving layer.
        
        Args:
            db_connection: DatabaseConnection instance
        """
        self.db_connection = db_connection
        # Time threshold: use speed layer for data newer than this
        self.realtime_threshold_minutes = 60  # Last 1 hour
    
    def get_combined_heatmap_data(self) -> Tuple[pd.DataFrame, Any]:
        """
        Get combined data from Speed Layer (recent) and Batch Layer (historical).
        
        Returns:
            Tuple of (DataFrame, last_update_timestamp)
        """
        try:
            # Get recent data from Speed Layer (realtime_data)
            df_realtime = self._get_realtime_data()
            
            # If we have enough recent data, use it
            if not df_realtime.empty and len(df_realtime) >= 10:
                last_update = df_realtime['timestamp'].max()
                logging.info(f"📡 Serving Layer: Using Speed Layer data ({len(df_realtime)} records)")
                return df_realtime, last_update
            
            # Otherwise, supplement with batch layer data
            df_batch = self._get_batch_data()
            
            if df_batch.empty and df_realtime.empty:
                # Fallback to raw_data if both layers are empty
                logging.warning("⚠️ Both Speed and Batch layers empty, falling back to raw_data")
                return self._get_raw_data_fallback()
            
            # Combine both layers
            df_combined = pd.concat([df_realtime, df_batch], ignore_index=True)
            df_combined = df_combined.drop_duplicates(subset=['location', 'timestamp'], keep='first')
            df_combined = df_combined.sort_values('timestamp', ascending=False).head(100)
            
            last_update = df_combined['timestamp'].max()
            logging.info(
                f"🔄 Serving Layer: Combined data "
                f"(Speed: {len(df_realtime)}, Batch: {len(df_batch)}, Total: {len(df_combined)})"
            )
            
            return df_combined, last_update
            
        except Exception as e:
            logging.error(f"Error in get_combined_heatmap_data: {e}")
            # Fallback to raw data
            return self._get_raw_data_fallback()
    
    def _get_realtime_data(self) -> pd.DataFrame:
        """Get recent data from Speed Layer (realtime_data table)."""
        try:
            engine = self.db_connection.get_engine()
            if not engine:
                return pd.DataFrame()
            
            cutoff_time = datetime.now() - timedelta(minutes=self.realtime_threshold_minutes)
            
            query = """
            SELECT timestamp, location, latitude, longitude, aqi_value, traffic_level
            FROM realtime_data
            WHERE timestamp >= %s AND is_active = TRUE
            ORDER BY timestamp DESC
            """
            
            df = pd.read_sql(query, engine, params=(cutoff_time,))
            
            if not df.empty:
                # Add normalized AQI column
                df['aqi_clean'] = df['aqi_value'].fillna(0).astype(int)
            
            return df
            
        except Exception as e:
            logging.error(f"Error getting realtime data: {e}")
            return pd.DataFrame()
    
    def _get_batch_data(self) -> pd.DataFrame:
        """Get aggregated data from Batch Layer (batch_aggregations table)."""
        try:
            engine = self.db_connection.get_engine()
            if not engine:
                return pd.DataFrame()
            
            # Get latest hourly aggregations (last 24 hours)
            cutoff_date = (datetime.now() - timedelta(days=1)).date()
            
            query = """
            SELECT 
                CAST(date AS TIMESTAMP) + INTERVAL '1 hour' * COALESCE(hour, 12) as timestamp,
                location,
                AVG(latitude) as latitude,  -- Assuming we'll join with location data
                AVG(longitude) as longitude,
                CAST(avg_aqi AS INTEGER) as aqi_value,
                CAST(avg_traffic AS INTEGER) as traffic_level
            FROM batch_aggregations ba
            WHERE date >= %s AND hour IS NOT NULL
            GROUP BY date, hour, location
            ORDER BY timestamp DESC
            LIMIT 100
            """
            
            df = pd.read_sql(query, engine, params=(cutoff_date,))
            
            if not df.empty:
                # Get location coordinates (since batch_aggregations doesn't have them)
                df = self._enrich_with_coordinates(df)
                df['aqi_clean'] = df['aqi_value'].fillna(0).astype(int)
            
            return df
            
        except Exception as e:
            logging.error(f"Error getting batch data: {e}")
            return pd.DataFrame()
    
    def _enrich_with_coordinates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrich batch data with latitude/longitude from raw_data."""
        try:
            engine = self.db_connection.get_engine()
            if not engine:
                return df
            
            # Get latest coordinates for each location
            query = """
            SELECT DISTINCT ON (location) 
                location, latitude, longitude
            FROM raw_data
            ORDER BY location, timestamp DESC
            """
            
            df_coords = pd.read_sql(query, engine)
            
            # Merge coordinates
            df = df.merge(df_coords, on='location', how='left', suffixes=('', '_new'))
            df['latitude'] = df['latitude_new'].fillna(df['latitude'])
            df['longitude'] = df['longitude_new'].fillna(df['longitude'])
            df = df.drop(columns=['latitude_new', 'longitude_new'], errors='ignore')
            
            return df
            
        except Exception as e:
            logging.error(f"Error enriching with coordinates: {e}")
            return df
    
    def _get_raw_data_fallback(self) -> Tuple[pd.DataFrame, Any]:
        """Fallback to raw_data if serving layers are not available."""
        try:
            engine = self.db_connection.get_engine()
            if not engine:
                return pd.DataFrame(), "No Data"
            
            query = "SELECT * FROM raw_data ORDER BY timestamp DESC LIMIT 100"
            df = pd.read_sql(query, engine)
            
            if not df.empty:
                df['aqi_clean'] = df['aqi_value'].fillna(0).astype(int)
                last_update = df['timestamp'].max()
                logging.info(f"🔙 Serving Layer: Using fallback raw_data ({len(df)} records)")
                return df, last_update
            else:
                return pd.DataFrame(), "No Data"
                
        except Exception as e:
            logging.error(f"Error in fallback: {e}")
            return pd.DataFrame(), "Error"
    
    def get_peak_hours_from_batch(self) -> Dict[str, Any]:
        """Get peak hours analysis from Batch Layer."""
        conn = None
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                return {}
            
            # Get latest peak hours analysis
            query = text("""
            SELECT 
                peak_aqi_hour,
                peak_aqi_value,
                peak_aqi_location,
                peak_traffic_hour,
                peak_traffic_value,
                peak_traffic_location,
                analysis_date
            FROM peak_hours
            ORDER BY analysis_date DESC
            LIMIT 1
            """)
            
            result = conn.execute(query)
            row = result.fetchone()
            
            if row:
                return {
                    'peak_aqi_hour': row[0],
                    'peak_aqi_value': float(row[1]) if row[1] else 0,
                    'peak_aqi_location': row[2],
                    'peak_traffic_hour': row[3],
                    'peak_traffic_value': float(row[4]) if row[4] else 0,
                    'peak_traffic_location': row[5],
                    'analysis_date': row[6],
                    'hourly_stats': None  # We can expand this if needed
                }
            else:
                return {}
                
        except Exception as e:
            logging.error(f"Error getting peak hours from batch: {e}")
            return {}
        finally:
            if conn:
                conn.close()
