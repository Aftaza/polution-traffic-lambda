from models.database import DatabaseConnection
from models.ingestion_service import IngestionService
from models.data_models import APIConfiguration
from utils import load_configuration
import sys


def main():
    """Main function to start the ingestion service."""
    try:
        # Load configuration
        config = load_configuration()

        # Initialize database connection
        db_connection = DatabaseConnection()

        # Initialize ingestion service
        ingestion_service = IngestionService(db_connection, config)

        # Start the scheduler
        ingestion_service.start_scheduler(interval_seconds=15)

    except ValueError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting ingestion service: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()