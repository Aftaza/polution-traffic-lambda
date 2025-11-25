# Jakarta Traffic & Pollution Heatmap - OOP Refactored

This project visualizes real-time traffic and air quality (AQI) data for Jakarta using a heatmap interface built with Streamlit. The project has been refactored to use Object-Oriented Programming (OOP) principles.

## Features

- Real-time heatmap visualization of Jakarta's traffic and air quality
- Data ingestion from TomTom (traffic) and AQICN (air quality) APIs
- PostgreSQL database for data storage
- Dockerized deployment with docker-compose

## Architecture Overview

The project has been refactored into a modular OOP structure:

### Models
- `DatabaseConnection`: Handles database connections with retry logic
- `DataRepository`: Manages database operations (CRUD)
- `APIClient`: Contains API clients for TomTom and AQICN services
- `DataProcessor`: Processes and transforms raw API data
- `IngestionService`: Orchestrates the data ingestion process
- `VisualizationService`: Creates heatmap visualizations
- `DataModels`: Contains data classes for structured data handling

### Components
- `app.py`: Streamlit application (now a class: `StreamlitApp`)
- `ingestion_service.py`: Data ingestion service (now uses the `IngestionService` class)
- `utils.py`: Utility functions for configuration loading and data formatting

## Environment Variables

The project uses a `.env` file to manage API keys and configuration:

```
# Database Configuration
POSTGRES_HOST=db
POSTGRES_DB=pid_db
POSTGRES_USER=pid_user
POSTGRES_PASSWORD=pid_password

# API Keys (should be set in environment or secrets)
TOMTOM_API_KEY=your_tomtom_api_key
AQICN_TOKEN=your_aqicn_token

# Application Configuration
STREAMLIT_SERVER_PORT=8501
INGESTION_SERVICE_PORT=5000
```

## Setup and Running

### Prerequisites
- Docker and Docker Compose
- Valid API keys for TomTom and AQICN services

### Local Development
1. Clone the repository
2. Create a `.env` file with your API keys (use `.env.example` as template)
3. Install dependencies: `pip install -r requirements.txt`
4. Run the ingestion service: `python ingestion_service.py`
5. Run the Streamlit app: `streamlit run app.py`

### Docker Deployment
1. Ensure Docker and Docker Compose are installed
2. Make sure your `.env` file is properly configured
3. Run: `docker-compose up --build`

This will start:
- PostgreSQL database
- Ingestion service (fetches data from APIs every 15 seconds)
- Streamlit visualization app

## Project Structure

```
.
├── app.py                 # Main Streamlit application class
├── ingestion_service.py   # Main ingestion service entry point
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not committed)
├── .env.example          # Example environment variables file
├── init.sql              # Database initialization script
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
└── models/               # OOP model classes
    ├── __init__.py
    ├── database.py       # Database connection class
    ├── data_models.py    # Data classes
    ├── api_client.py     # API client classes
    ├── data_processor.py # Data processing class
    ├── data_repository.py # Data repository class
    ├── ingestion_service.py # Ingestion service class
    └── visualization.py   # Visualization service class
```

## API Configuration

To use the application, you need to obtain API keys from:
- [TomTom API](https://developer.tomtom.com/)
- [AQICN API](http://aqicn.org/api/)

**Note:** The map visualization uses Carto's free dark basemap, so no Mapbox API token is required.

## Security Notes

- Never commit your `.env` file with real API keys
- Consider using Docker secrets or cloud key management services for production deployments
- The API keys are now loaded from environment variables rather than hardcoded

## Docker Configuration

The `docker-compose.yml` file has been updated to:
- Use `.env` file for configuration
- Properly handle environment variables with defaults
- Use proper dependency ordering between services
- Apply consistent naming conventions

## Migration Notes

This refactoring replaced the original functional programming approach with OOP principles:
- Improved code organization and maintainability
- Better separation of concerns
- Enhanced testability
- More robust error handling
- Configuration management through .env files