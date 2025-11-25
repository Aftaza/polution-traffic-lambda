from models.database import DatabaseConnection
from models.kafka_consumer import KafkaConsumerWrapper
from models.stream_processor import StreamProcessor
from datetime import datetime
import logging
import sys


def main():
    """Main function to start the Speed Layer service (Kafka Consumer + Stream Processing)."""
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Initialize database connection
        db_connection = DatabaseConnection()
        
        # Initialize stream processor
        stream_processor = StreamProcessor(db_connection)
        
        # Initialize Kafka consumer
        kafka_consumer = KafkaConsumerWrapper()
        
        print("🚀 Speed Layer Service Started (Kafka Consumer + Stream Processing)...")
        print("👂 Listening for messages from Kafka...")
        
        # Consume and process messages
        for location_data in kafka_consumer.consume_location_data():
            try:
                # Process the message through stream processor
                success = stream_processor.process_location_data(location_data)
                
                if success:
                    logging.info(
                        f"✅ Processed: {location_data.get('location')} "
                        f"| AQI: {location_data.get('aqi_value')} "
                        f"| Traffic: {location_data.get('traffic_level')}"
                    )
                else:
                    logging.warning(f"⚠️ Failed to process: {location_data.get('location')}")
                    
            except Exception as e:
                logging.error(f"❌ Error processing message: {e}")
                continue
                
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Speed Layer service...")
        kafka_consumer.close()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting Speed Layer service: {e}")
        logging.error(f"Speed Layer startup error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
