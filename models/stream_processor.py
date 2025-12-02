from typing import Dict, Any
from datetime import datetime, timedelta
import logging
from sqlalchemy import text


class StreamProcessor:
    """Stream processor for real-time data processing (Lambda Architecture - Speed Layer)."""
    
    # Peak hours definition (Jakarta rush hours)
    MORNING_PEAK = (6, 10)  # 6 AM - 10 AM
    EVENING_PEAK = (16, 20)  # 4 PM - 8 PM
    
    def __init__(self, db_connection):
        """
        Initialize stream processor.
        
        Args:
            db_connection: DatabaseConnection instance
        """
        self.db_connection = db_connection
        # Window size for real-time aggregation (in minutes)
        self.window_size_minutes = 5
    
    @staticmethod
    def is_peak_hour(timestamp: datetime) -> bool:
        """
        Check if timestamp is during peak hours.
        
        Args:
            timestamp: datetime object to check
        
        Returns:
            bool: True if during peak hours
        """
        hour = timestamp.hour
        morning_peak = StreamProcessor.MORNING_PEAK[0] <= hour < StreamProcessor.MORNING_PEAK[1]
        evening_peak = StreamProcessor.EVENING_PEAK[0] <= hour < StreamProcessor.EVENING_PEAK[1]
        return morning_peak or evening_peak
    
    @staticmethod
    def get_aqi_category(aqi_value: int) -> str:
        """
        Categorize AQI value according to standard AQI categories.
        
        Args:
            aqi_value: AQI numeric value
        
        Returns:
            str: AQI category name
        """
        if aqi_value <= 50:
            return "Good"
        elif aqi_value <= 100:
            return "Moderate"
        elif aqi_value <= 150:
            return "Unhealthy for Sensitive Groups"
        elif aqi_value <= 200:
            return "Unhealthy"
        elif aqi_value <= 300:
            return "Very Unhealthy"
        else:
            return "Hazardous"
    
    def process_location_data(self, location_data: Dict[str, Any]) -> bool:
        """
        Process incoming location data from Kafka and store to realtime_data table.
        Also updates peak_hours_analysis table for hourly aggregation.
        
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
            
            # Determine peak hour status
            is_peak = self.is_peak_hour(timestamp)
            
            # Get AQI category
            aqi_value = location_data.get('aqi_value')
            aqi_category = self.get_aqi_category(aqi_value) if aqi_value else "Unknown"
            
            # Insert into realtime_data table
            success = self._insert_realtime_data(
                timestamp=timestamp,
                location=location_data.get('location'),
                latitude=location_data.get('latitude'),
                longitude=location_data.get('longitude'),
                aqi_value=aqi_value,
                aqi_category=aqi_category,
                traffic_level=location_data.get('traffic_level'),
                is_peak_hour=is_peak
            )
            
            if success:
                # Update peak hours analysis table
                self._update_peak_hours_analysis(
                    timestamp=timestamp,
                    location=location_data.get('location'),
                    aqi_value=aqi_value,
                    traffic_level=location_data.get('traffic_level'),
                    is_peak_hour=is_peak
                )
                
                # Optionally: cleanup old real-time data (keep only last 1 hour)
                self._cleanup_old_realtime_data(hours=1)
            
            return success
            
        except Exception as e:
            logging.error(f"Error processing location data: {e}")
            return False
    
    def _insert_realtime_data(self, timestamp, location, latitude, longitude, 
                              aqi_value, aqi_category, traffic_level, is_peak_hour) -> bool:
        """Insert data into realtime_data table with peak hours and AQI category."""
        conn = None
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                return False
            
            insert_query = text("""
            INSERT INTO realtime_data 
            (timestamp, location, latitude, longitude, aqi_value, aqi_category, traffic_level, is_peak_hour, is_active)
            VALUES (:timestamp, :location, :latitude, :longitude, :aqi_value, :aqi_category, :traffic_level, :is_peak_hour, TRUE)
            """)
            
            conn.execute(insert_query, {
                'timestamp': timestamp,
                'location': location,
                'latitude': latitude,
                'longitude': longitude,
                'aqi_value': aqi_value,
                'aqi_category': aqi_category,
                'traffic_level': traffic_level,
                'is_peak_hour': is_peak_hour
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
    
    def _update_peak_hours_analysis(self, timestamp: datetime, location: str, 
                                     aqi_value: int, traffic_level: int, is_peak_hour: bool):
        """
        Update peak_hours_analysis table with incremental aggregation.
        This enables real-time hourly analysis from the Speed Layer.
        
        Args:
            timestamp: Data timestamp
            location: Location name
            aqi_value: AQI value
            traffic_level: Traffic level
            is_peak_hour: Whether this is peak hour
        """
        conn = None
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                return
            
            date = timestamp.date()
            hour = timestamp.hour
            
            # Upsert with running average calculation
            upsert_query = text("""
            INSERT INTO peak_hours_analysis 
            (date, hour, location, avg_traffic_level, avg_aqi_value, is_peak_hour, total_records, updated_at)
            VALUES (:date, :hour, :location, :traffic, :aqi, :is_peak, 1, NOW())
            ON CONFLICT (date, hour, location)
            DO UPDATE SET
                avg_traffic_level = (
                    (peak_hours_analysis.avg_traffic_level * peak_hours_analysis.total_records + EXCLUDED.avg_traffic_level) 
                    / (peak_hours_analysis.total_records + 1)
                ),
                avg_aqi_value = (
                    (peak_hours_analysis.avg_aqi_value * peak_hours_analysis.total_records + EXCLUDED.avg_aqi_value) 
                    / (peak_hours_analysis.total_records + 1)
                ),
                total_records = peak_hours_analysis.total_records + 1,
                updated_at = NOW()
            """)
            
            conn.execute(upsert_query, {
                'date': date,
                'hour': hour,
                'location': location,
                'traffic': traffic_level,
                'aqi': aqi_value,
                'is_peak': is_peak_hour
            })
            conn.commit()
            
        except Exception as e:
            logging.error(f"Error updating peak_hours_analysis: {e}")
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
