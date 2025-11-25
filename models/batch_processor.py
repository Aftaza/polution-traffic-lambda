from typing import Dict, Any, List
from datetime import datetime, timedelta, date
import logging
from sqlalchemy import text
import pandas as pd


class BatchProcessor:
    """Batch processor for historical data aggregation (Lambda Architecture - Batch Layer)."""
    
    def __init__(self, db_connection):
        """
        Initialize batch processor.
        
        Args:
            db_connection: DatabaseConnection instance
        """
        self.db_connection = db_connection
    
    def run_daily_aggregation(self):
        """Run daily aggregation on all historical data."""
        try:
            logging.info("📊 Starting daily aggregation...")
            
            # Get yesterday's date (process previous day's data)
            target_date = (datetime.now() - timedelta(days=1)).date()
            
            # Aggregate by location for the entire day
            self._aggregate_by_location_and_date(target_date)
            
            logging.info(f"✅ Daily aggregation completed for {target_date}")
            
        except Exception as e:
            logging.error(f"❌ Error in daily aggregation: {e}", exc_info=True)
    
    def run_hourly_aggregation(self):
        """Run hourly aggregation on recent data."""
        try:
            logging.info("⏱️ Starting hourly aggregation...")
            
            # Get current and previous hour
            now = datetime.now()
            current_hour = now.replace(minute=0, second=0, microsecond=0)
            previous_hour = current_hour - timedelta(hours=1)
            
            # Aggregate last hour's data
            self._aggregate_by_hour(previous_hour.date(), previous_hour.hour)
            
            logging.info(f"✅ Hourly aggregation completed for {previous_hour}")
            
        except Exception as e:
            logging.error(f"❌ Error in hourly aggregation: {e}", exc_info=True)
    
    def run_peak_hour_analysis(self):
        """Analyze and detect peak hours for pollution and traffic."""
        try:
            logging.info("🔍 Starting peak hour analysis...")
            
            # Analyze yesterday's data
            target_date = (datetime.now() - timedelta(days=1)).date()
            
            peak_hours = self._detect_peak_hours(target_date)
            
            if peak_hours:
                self._save_peak_hours(target_date, peak_hours)
                logging.info(
                    f"✅ Peak hour analysis completed: "
                    f"AQI peak at {peak_hours['peak_aqi_hour']}:00, "
                    f"Traffic peak at {peak_hours['peak_traffic_hour']}:00"
                )
            else:
                logging.warning(f"⚠️ No data available for peak hour analysis on {target_date}")
                
        except Exception as e:
            logging.error(f"❌ Error in peak hour analysis: {e}", exc_info=True)
    
    def _aggregate_by_location_and_date(self, target_date: date):
        """Aggregate data by location for a specific date."""
        conn = None
        try:
            engine = self.db_connection.get_engine()
            if not engine:
                return
            
            # Query to aggregate daily data by location
            query = text("""
            INSERT INTO batch_aggregations (date, hour, location, avg_aqi, avg_traffic, max_aqi, max_traffic, min_aqi, min_traffic, data_points_count)
            SELECT 
                :target_date as date,
                NULL as hour,
                location,
                AVG(aqi_value) as avg_aqi,
                AVG(traffic_level) as avg_traffic,
                MAX(aqi_value) as max_aqi,
                MAX(traffic_level) as max_traffic,
                MIN(aqi_value) as min_aqi,
                MIN(traffic_level) as min_traffic,
                COUNT(*) as data_points_count
            FROM raw_data
            WHERE DATE(timestamp) = :target_date
            GROUP BY location
            ON CONFLICT (date, hour, location) 
            DO UPDATE SET
                avg_aqi = EXCLUDED.avg_aqi,
                avg_traffic = EXCLUDED.avg_traffic,
                max_aqi = EXCLUDED.max_aqi,
                max_traffic = EXCLUDED.max_traffic,
                min_aqi = EXCLUDED.min_aqi,
                min_traffic = EXCLUDED.min_traffic,
                data_points_count = EXCLUDED.data_points_count,
                created_at = NOW()
            """)
            
            conn = self.db_connection.get_connection()
            conn.execute(query, {'target_date': target_date})
            conn.commit()
            
        except Exception as e:
            logging.error(f"Error in _aggregate_by_location_and_date: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    def _aggregate_by_hour(self, target_date: date, hour: int):
        """Aggregate data by location for a specific hour."""
        conn = None
        try:
            # Query to aggregate hourly data by location
            query = text("""
            INSERT INTO batch_aggregations (date, hour, location, avg_aqi, avg_traffic, max_aqi, max_traffic, min_aqi, min_traffic, data_points_count)
            SELECT 
                :target_date as date,
                :hour as hour,
                location,
                AVG(aqi_value) as avg_aqi,
                AVG(traffic_level) as avg_traffic,
                MAX(aqi_value) as max_aqi,
                MAX(traffic_level) as max_traffic,
                MIN(aqi_value) as min_aqi,
                MIN(traffic_level) as min_traffic,
                COUNT(*) as data_points_count
            FROM raw_data
            WHERE DATE(timestamp) = :target_date
              AND EXTRACT(HOUR FROM timestamp) = :hour
            GROUP BY location
            ON CONFLICT (date, hour, location) 
            DO UPDATE SET
                avg_aqi = EXCLUDED.avg_aqi,
                avg_traffic = EXCLUDED.avg_traffic,
                max_aqi = EXCLUDED.max_aqi,
                max_traffic = EXCLUDED.max_traffic,
                min_aqi = EXCLUDED.min_aqi,
                min_traffic = EXCLUDED.min_traffic,
                data_points_count = EXCLUDED.data_points_count,
                created_at = NOW()
            """)
            
            conn = self.db_connection.get_connection()
            conn.execute(query, {'target_date': target_date, 'hour': hour})
            conn.commit()
            
        except Exception as e:
            logging.error(f"Error in _aggregate_by_hour: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    def _detect_peak_hours(self, target_date: date) -> Dict[str, Any]:
        """Detect peak hours for AQI and traffic on a specific date."""
        try:
            engine = self.db_connection.get_engine()
            if not engine:
                return {}
            
            # Query hourly aggregations for the target date
            query = """
            SELECT 
                hour,
                location,
                avg_aqi,
                avg_traffic
            FROM batch_aggregations
            WHERE date = %s AND hour IS NOT NULL
            ORDER BY hour, location
            """
            
            df = pd.read_sql(query, engine, params=(target_date,))
            
            if df.empty:
                return {}
            
            # Group by hour and calculate overall averages
            hourly_stats = df.groupby('hour').agg({
                'avg_aqi': 'mean',
                'avg_traffic': 'mean'
            })
            
            # Find peak hours
            peak_aqi_hour = int(hourly_stats['avg_aqi'].idxmax())
            peak_traffic_hour = int(hourly_stats['avg_traffic'].idxmax())
            
            peak_aqi_value = hourly_stats.loc[peak_aqi_hour, 'avg_aqi']
            peak_traffic_value = hourly_stats.loc[peak_traffic_hour, 'avg_traffic']
            
            # Find locations with peak values
            peak_aqi_location = df[df['hour'] == peak_aqi_hour].nlargest(1, 'avg_aqi')['location'].values[0]
            peak_traffic_location = df[df['hour'] == peak_traffic_hour].nlargest(1, 'avg_traffic')['location'].values[0]
            
            return {
                'peak_aqi_hour': peak_aqi_hour,
                'peak_aqi_value': float(peak_aqi_value),
                'peak_aqi_location': peak_aqi_location,
                'peak_traffic_hour': peak_traffic_hour,
                'peak_traffic_value': float(peak_traffic_value),
                'peak_traffic_location': peak_traffic_location
            }
            
        except Exception as e:
            logging.error(f"Error in _detect_peak_hours: {e}")
            return {}
    
    def _save_peak_hours(self, analysis_date: date, peak_hours: Dict[str, Any]):
        """Save peak hours analysis to database."""
        conn = None
        try:
            query = text("""
            INSERT INTO peak_hours (analysis_date, peak_aqi_hour, peak_aqi_value, peak_aqi_location, 
                                   peak_traffic_hour, peak_traffic_value, peak_traffic_location)
            VALUES (:analysis_date, :peak_aqi_hour, :peak_aqi_value, :peak_aqi_location,
                    :peak_traffic_hour, :peak_traffic_value, :peak_traffic_location)
            ON CONFLICT (analysis_date) 
            DO UPDATE SET
                peak_aqi_hour = EXCLUDED.peak_aqi_hour,
                peak_aqi_value = EXCLUDED.peak_aqi_value,
                peak_aqi_location = EXCLUDED.peak_aqi_location,
                peak_traffic_hour = EXCLUDED.peak_traffic_hour,
                peak_traffic_value = EXCLUDED.peak_traffic_value,
                peak_traffic_location = EXCLUDED.peak_traffic_location,
                created_at = NOW()
            """)
            
            conn = self.db_connection.get_connection()
            conn.execute(query, {
                'analysis_date': analysis_date,
                'peak_aqi_hour': peak_hours['peak_aqi_hour'],
                'peak_aqi_value': peak_hours['peak_aqi_value'],
                'peak_aqi_location': peak_hours['peak_aqi_location'],
                'peak_traffic_hour': peak_hours['peak_traffic_hour'],
                'peak_traffic_value': peak_hours['peak_traffic_value'],
                'peak_traffic_location': peak_hours['peak_traffic_location']
            })
            conn.commit()
            
        except Exception as e:
            logging.error(f"Error in _save_peak_hours: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
