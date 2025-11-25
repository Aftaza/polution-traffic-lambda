import json
import logging
from typing import Dict, Any, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
import os


class KafkaProducerWrapper:
    """Wrapper class for Kafka Producer with error handling and serialization."""
    
    def __init__(self, bootstrap_servers: str = None, topic: str = None):
        """
        Initialize Kafka Producer.
        
        Args:
            bootstrap_servers: Comma-separated list of Kafka broker addresses
            topic: Default topic name for messages
        """
        self.bootstrap_servers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        self.topic = topic or os.getenv("KAFKA_TOPIC", "traffic-aqi-data")
        self.producer = None
        self._initialize_producer()
    
    def _initialize_producer(self):
        """Initialize the Kafka producer with JSON serialization."""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers.split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,   # Retry failed sends
                max_in_flight_requests_per_connection=1,  # Ensure ordering
                compression_type='gzip'  # Compress messages
            )
            logging.info(f"✅ Kafka Producer initialized: {self.bootstrap_servers}")
        except Exception as e:
            logging.error(f"❌ Failed to initialize Kafka Producer: {e}")
            raise
    
    def send_message(self, message: Dict[str, Any], topic: str = None, key: str = None) -> bool:
        """
        Send a message to Kafka topic.
        
        Args:
            message: Dictionary to send as JSON
            topic: Topic name (optional, uses default if not provided)
            key: Message key for partitioning (optional)
        
        Returns:
            bool: True if successful, False otherwise
        """
        target_topic = topic or self.topic
        
        try:
            future = self.producer.send(target_topic, value=message, key=key)
            # Wait for confirmation (with timeout)
            record_metadata = future.get(timeout=10)
            
            logging.debug(
                f"✅ Message sent to {record_metadata.topic} "
                f"partition {record_metadata.partition} "
                f"offset {record_metadata.offset}"
            )
            return True
            
        except KafkaError as e:
            logging.error(f"❌ Kafka error sending message: {e}")
            return False
        except Exception as e:
            logging.error(f"❌ Unexpected error sending message: {e}")
            return False
    
    def send_location_data(self, location_data: Dict[str, Any]) -> bool:
        """
        Send location data message to Kafka.
        
        Args:
            location_data: Dictionary containing location, AQI, and traffic data
        
        Returns:
            bool: True if successful
        """
        # Use location name as key for partitioning (keeps same location in same partition)
        key = location_data.get('location', '')
        return self.send_message(location_data, key=key)
    
    def flush(self):
        """Flush any pending messages."""
        if self.producer:
            self.producer.flush()
            logging.info("🔄 Kafka Producer flushed")
    
    def close(self):
        """Close the Kafka producer connection."""
        if self.producer:
            self.producer.close()
            logging.info("🔌 Kafka Producer closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
