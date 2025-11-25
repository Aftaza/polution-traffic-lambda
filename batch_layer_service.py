from models.database import DatabaseConnection
from models.batch_processor import BatchProcessor
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, time as dt_time
import logging
import sys
import time


def main():
    """Main function to start the Batch Layer service (Daily Aggregation + Peak Hour Detection)."""
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Initialize database connection
        db_connection = DatabaseConnection()
        
        # Initialize batch processor
        batch_processor = BatchProcessor(db_connection)
        
        print("🚀 Batch Layer Service Started (Daily Aggregation + Peak Hours)...")
        
        # Create scheduler
        scheduler = BackgroundScheduler()
        
        # Schedule daily aggregation at 2 AM WIB
        scheduler.add_job(
            batch_processor.run_daily_aggregation,
            'cron',
            hour=2,
            minute=0,
            name='daily_aggregation'
        )
        
        # Schedule peak hour analysis at 3 AM WIB (after aggregation)
        scheduler.add_job(
            batch_processor.run_peak_hour_analysis,
            'cron',
            hour=3,
            minute=0,
            name='peak_hour_analysis'
        )
        
        # Also run hourly aggregation every hour
        scheduler.add_job(
            batch_processor.run_hourly_aggregation,
            'cron',
            minute=5,  # Run at 5 minutes past the hour
            name='hourly_aggregation'
        )
        
        scheduler.start()
        print("⏰ Scheduled jobs:")
        print("  - Daily aggregation: 02:00 WIB")
        print("  - Peak hour analysis: 03:00 WIB")
        print("  - Hourly aggregation: Every hour at :05")
        
        # Run initial aggregation on startup
        print("\n🔄 Running initial batch processing...")
        batch_processor.run_hourly_aggregation()
        batch_processor.run_daily_aggregation()
        batch_processor.run_peak_hour_analysis()
        print("✅ Initial batch processing complete\n")
        
        # Keep the service running
        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            print("\n🛑 Shutting down Batch Layer service...")
            scheduler.shutdown()
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ Error starting Batch Layer service: {e}")
        logging.error(f"Batch Layer startup error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
