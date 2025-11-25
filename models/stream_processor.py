from typing import Dict, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy import text


class StreamProcessor:
    """Stream processor for real-time data processing (Lambda Architecture - Speed Layer)."""
    
    def __init__(self, db_connection):
        """
        Initialize stream processor.
        
        Args:
            db_connection: DatabaseConnection instance
        """
        self.db_connection = db_connection
        # Window size for real-time aggregation (in minutes)
        self.window_size_minutes = 5
    
    def process_location_data(self, location_data: Dict[str, Any]) -> bool:
        """
        Process incoming location data from Kafka and store to realtime_data table.
        
        Args:
            location_data: Dictionary containing location, AQI, and traffic data
        
        Returns:
            bool: True if successfully processed and stored
        """
        try:
            # Parse ISO timestamp string
            timestamp_str = location_data.get('timestamp')
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.now()
            
            # Insert into realtime_data table
            success = self._insert_realtime_data(
                timestamp=timestamp,
                location=location_data.get('location'),
                latitude=location_data.get('latitude'),
                longitude=location_data.get('longitude'),
                aqi_value=location_data.get('aqi_value'),
                traffic_level=location_data.get('traffic_level')
            )
            
            if success:
                # Optionally: cleanup old real-time data (keep only last 1 hour)
                self._cleanup_old_realtime_data(hours=1)
            
            return success
            
        except Exception as e:
            logging.error(f"Error processing location data: {e}")
            return False
    
    def _insert_realtime_data(self, timestamp, location, latitude, longitude, 
                              aqi_value, traffic_level) -> bool:
        """Insert data into realtime_data table."""
        conn = None
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                return False
            
            insert_query = text("""
            INSERT INTO realtime_data (timestamp, location, latitude, longitude, aqi_value, traffic_level, is_active)
            VALUES (:timestamp, :location, :latitude, :longitude, :aqi_value, :traffic_level, TRUE)
            """)
            
            conn.execute(insert_query, {
                'timestamp': timestamp,
                'location': location,
                'latitude': latitude,
                'longitude': longitude,
                'aqi_value': aqi_value,
                'traffic_level': traffic_level
            })
            conn.commit()
            return True
            
        except Exception as e:
            logging.error(f"Database error in _insert_realtime_data: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def _cleanup_old_realtime_data(self, hours: int = 1):
        """
        Clean up old real-time data to keep the table size manageable.
        
        Args:
            hours: Keep only data from the last N hours
        """
        conn = None
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                return
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Mark old data as inactive instead of deleting (for debugging/audit trail)
            update_query = text("""
            UPDATE realtime_data 
            SET is_active = FALSE 
            WHERE timestamp < :cutoff_time AND is_active = TRUE
            """)
            
            result = conn.execute(update_query, {'cutoff_time': cutoff_time})
            conn.commit()
            
            if result.rowcount > 0:
                logging.info(f"🧹 Cleaned up {result.rowcount} old realtime records")
            
        except Exception as e:
            logging.error(f"Error in cleanup_old_realtime_data: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    def get_recent_aggregates(self, minutes: int = 5) -> Dict[str, Any]:
        """
        Get aggregated data for the recent time window.
        
        Args:
            minutes: Time window in minutes
        
        Returns:
            Dict with aggregated statistics
        """
        conn = None
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                return {}
            
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            
            query = text("""
            SELECT 
                location,
                AVG(aqi_value) as avg_aqi,
                AVG(traffic_level) as avg_traffic,
                MAX(aqi_value) as max_aqi,
                MAX(traffic_level) as max_traffic,
                COUNT(*) as data_points
            FROM realtime_data
            WHERE timestamp >= :cutoff_time AND is_active = TRUE
            GROUP BY location
            """)
            
            result = conn.execute(query, {'cutoff_time': cutoff_time})
            rows = result.fetchall()
            
            aggregates = {}
            for row in rows:
                aggregates[row[0]] = {
                    'avg_aqi': float(row[1]) if row[1] else 0,
                    'avg_traffic': float(row[2]) if row[2] else 0,
                    'max_aqi': row[3],
                    'max_traffic': row[4],
                    'data_points': row[5]
                }
            
            return aggregates
            
        except Exception as e:
            logging.error(f"Error getting recent aggregates: {e}")
            return {}
        finally:
            if conn:
                conn.close()
