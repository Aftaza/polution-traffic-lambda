import json
import logging
from typing import Dict, Any, Optional, Iterator
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import os


class KafkaConsumerWrapper:
    """Wrapper class for Kafka Consumer with error handling and deserialization."""
    
    def __init__(self, bootstrap_servers: str = None, topic: str = None, group_id: str = None):
        """
        Initialize Kafka Consumer.
        
        Args:
            bootstrap_servers: Comma-separated list of Kafka broker addresses
            topic: Topic name to consume from
            group_id: Consumer group ID
        """
        self.bootstrap_servers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        self.topic = topic or os.getenv("KAFKA_TOPIC", "traffic-aqi-data")
        self.group_id = group_id or os.getenv("KAFKA_CONSUMER_GROUP", "speed-layer-consumer")
        self.consumer = None
        self._initialize_consumer()
    
    def _initialize_consumer(self):
        """Initialize the Kafka consumer with JSON deserialization."""
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers.split(','),
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='latest',  # Start from latest messages for real-time processing
                enable_auto_commit=True,     # Auto-commit offsets
                auto_commit_interval_ms=1000,  # Commit every second
                max_poll_records=100         # Batch size for processing
            )
            logging.info(f"✅ Kafka Consumer initialized: {self.bootstrap_servers}, topic: {self.topic}, group: {self.group_id}")
        except Exception as e:
            logging.error(f"❌ Failed to initialize Kafka Consumer: {e}")
            raise
    
    def consume_messages(self) -> Iterator[Dict[str, Any]]:
        """
        Consume messages from Kafka topic.
        
        Yields:
            Dict containing message data
        """
        try:
            for message in self.consumer:
                yield {
                    'topic': message.topic,
                    'partition': message.partition,
                    'offset': message.offset,
                    'key': message.key,
                    'value': message.value,
                    'timestamp': message.timestamp
                }
        except KafkaError as e:
            logging.error(f"❌ Kafka error consuming messages: {e}")
        except Exception as e:
            logging.error(f"❌ Unexpected error consuming messages: {e}")
    
    def consume_location_data(self) -> Iterator[Dict[str, Any]]:
        """
        Consume location data messages from Kafka.
        
        Yields:
            Dict containing location data (location, AQI, traffic, etc.)
        """
        for message in self.consume_messages():
            try:
                location_data = message['value']
                logging.debug(f"📨 Received: {location_data.get('location', 'Unknown')} from partition {message['partition']}")
                yield location_data
            except Exception as e:
                logging.error(f"❌ Error processing message: {e}")
                continue
    
    def close(self):
        """Close the Kafka consumer connection."""
        if self.consumer:
            self.consumer.close()
            logging.info("🔌 Kafka Consumer closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
