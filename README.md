# Jakarta Traffic & Pollution Heatmap - Lambda Architecture

This project visualizes real-time traffic and air quality (AQI) data for Jakarta using a **Lambda Architecture** with Kafka messaging, dual-layer processing (Speed + Batch), and a unified Serving Layer. Built with Streamlit, PostgreSQL, and Apache Kafka.

## 🎯 Features

- **Real-time heatmap visualization** of Jakarta's traffic and air quality
- **Lambda Architecture** with Speed Layer (real-time) and Batch Layer (historical)
- **Kafka-based event streaming** for scalable data ingestion
- **Dual-layer data processing** for both low-latency and high-accuracy insights
- **Peak hours analysis** with UTC+7 (WIB) timezone support
- **AQI legend** with EPA standard color coding
- **Data source indicators** showing Speed Layer vs Batch Layer data
- **Dockerized deployment** with 7 microservices

## 🏗️ Architecture Overview

The system implements the **Lambda Architecture** pattern:

```
External APIs (TomTom, AQICN)
           ↓
    Ingestion Layer
    (Kafka Producer)
           ↓
      Kafka Broker
       /         \
      /           \
All Data        Recent Data
   ↓                ↓
Batch Layer    Speed Layer
   ↓                ↓
   └────→ Serving Layer ←────┘
              ↓
        PostgreSQL DB
              ↓
      Streamlit Dashboard
```

### Architecture Layers

#### 1. **Ingestion Layer**
- Polls TomTom and AQICN APIs every 15 seconds
- Publishes JSON messages to Kafka topic `traffic-aqi-data`
- Backs up to `raw_data` table for batch processing
- **Service**: `pid-ingestion-producer`

#### 2. **Speed Layer** (Real-time Processing)
- Consumes Kafka messages in real-time
- Processes and stores to `realtime_data` table
- Provides low-latency data (< 1 second)
- Auto-cleanup of old data (keeps last 1 hour)
- **Service**: `pid-speed-layer`

#### 3. **Batch Layer** (Historical Processing)
- Runs scheduled aggregation jobs
- Daily aggregation at 2:00 AM WIB
- Hourly aggregation every hour at :05
- Peak hour analysis at 3:00 AM WIB
- Stores to `batch_aggregations` and `peak_hours` tables
- **Service**: `pid-batch-layer`

#### 4. **Serving Layer**
- Combines Speed Layer (recent) + Batch Layer (historical) data
- Intelligent data source selection based on freshness
- Fallback to raw data if processed layers unavailable
- **Integrated in**: `pid-streamlit-app`

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- At least 8GB RAM for Docker
- Valid API keys for TomTom and AQICN

### Deployment Steps

1. **Clone and configure**:
   ```bash
   git clone <repository>
   cd case-based
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Build and start services**:
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

3. **Verify services are running**:
   ```bash
   docker-compose ps
   ```
   
   Expected: 7 services in "Up" state

4. **Access the dashboard**:
   ```
   http://localhost:8501
   ```

5. **Monitor logs**:
   ```bash
   docker-compose logs -f
   ```

## 📦 Services & Ports

| Service | Container Name | Port | Purpose |
|---------|---------------|------|---------|
| Zookeeper | `pid-zookeeper` | 2181 | Kafka coordination |
| Kafka | `pid-kafka` | 9092, 9093 | Message broker |
| PostgreSQL | `pid-postgres-db` | 5432 | Data storage |
| Ingestion | `pid-ingestion-producer` | - | API polling → Kafka |
| Speed Layer | `pid-speed-layer` | - | Real-time processing |
| Batch Layer | `pid-batch-layer` | - | Historical aggregation |
| Dashboard | `pid-streamlit-app` | 8501 | Visualization |

## 🗂️ Project Structure

```
.
├── app.py                      # Streamlit dashboard (Serving Layer)
├── ingestion_service.py        # Ingestion service entry point
├── speed_layer_service.py      # Speed Layer entry point (NEW)
├── batch_layer_service.py      # Batch Layer entry point (NEW)
├── utils.py                    # Utility functions (timezone, peak hours)
├── requirements.txt            # Python dependencies (includes Kafka)
├── .env                        # Environment variables (not committed)
├── .env.example               # Example environment file
├── init.sql                   # Database schema (4 tables)
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # 7 services configuration
├── DEPLOYMENT_GUIDE.md        # Detailed deployment instructions
├── ARCHITECTURE_OVERVIEW.md   # Architecture documentation
├── BUG_FIXES_2.md            # Bug fix history
├── FEATURE_UPDATE.md         # Feature changelog
└── models/                    # OOP model classes
    ├── __init__.py
    ├── database.py           # Database connection
    ├── data_models.py        # Data classes
    ├── api_client.py         # TomTom & AQICN clients
    ├── data_processor.py     # Data transformation
    ├── data_repository.py    # Database operations
    ├── ingestion_service.py  # Ingestion logic (Kafka producer)
    ├── kafka_producer.py     # Kafka producer wrapper (NEW)
    ├── kafka_consumer.py     # Kafka consumer wrapper (NEW)
    ├── stream_processor.py   # Speed Layer processing (NEW)
    ├── batch_processor.py    # Batch Layer processing (NEW)
    ├── serving_layer.py      # Serving Layer logic (NEW)
    └── visualization.py      # Heatmap visualizations
```

## 🗄️ Database Schema

### Tables

1. **`raw_data`** - All ingested data (backup for Batch Layer)
2. **`realtime_data`** - Speed Layer output (last 1 hour)
3. **`batch_aggregations`** - Batch Layer aggregations (daily/hourly)
4. **`peak_hours`** - Peak hour analysis results
5. **`daily_summary`** - Legacy summary table (backward compatibility)

### Indexes
- Timestamp indexes for fast time-range queries
- Location indexes for spatial queries
- Composite indexes for aggregation queries

## ⚙️ Environment Variables

Create a `.env` file with the following configuration:

```bash
# Database Configuration
POSTGRES_HOST=db
POSTGRES_DB=pid_db
POSTGRES_USER=pid_user
POSTGRES_PASSWORD=pid_password

# API Keys (REQUIRED - get from providers)
TOMTOM_API_KEY=your_tomtom_api_key_here
AQICN_TOKEN=your_aqicn_token_here

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC=traffic-aqi-data
KAFKA_CONSUMER_GROUP=speed-layer-consumer

# Application Configuration
STREAMLIT_SERVER_PORT=8501
INGESTION_SERVICE_PORT=5000
```

## 🔑 API Keys

Obtain API keys from:
- **TomTom API**: https://developer.tomtom.com/
- **AQICN API**: http://aqicn.org/api/

**Note**: Map visualization uses Carto's free dark basemap (no Mapbox token required)

## 📊 Dashboard Features

### Real-time Visualization
- **AQI Heatmap**: Color-coded air quality visualization
- **Traffic Heatmap**: Traffic congestion levels
- **Data Source Badge**: Shows "Speed Layer (Real-time)" or "Batch Layer (Historical)"

### Analytics
- **AQI Legend**: EPA standard categories (Good → Hazardous)
- **Peak Hours Analysis**: 
  - Peak pollution hour with average AQI
  - Peak traffic hour with average level
  - Hourly breakdown table
- **Timezone**: All times in WIB (UTC+7)

### Data Display
- Last update timestamp
- Raw data viewer (expandable)
- Location coordinates
- Real-time metrics

## 📚 Documentation

### Detailed Guides
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Step-by-step deployment, troubleshooting, health checks
- **[ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)** - Lambda Architecture details, data flow, design decisions
- **[FEATURE_UPDATE.md](FEATURE_UPDATE.md)** - AQI legend and peak hours feature documentation
- **[BUG_FIXES_2.md](BUG_FIXES_2.md)** - Timezone and legend color bug fixes
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing procedures and verification steps

### Quick References
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - User guide for dashboard features
- **[BUG_FIX_SUMMARY.md](BUG_FIX_SUMMARY.md)** - Mapbox base layer fix

## 🧪 Testing & Verification

### Quick Health Check

```bash
# Check all services
docker-compose ps

# Check Kafka topic
docker exec pid-kafka kafka-topics --list --bootstrap-server localhost:9092

# Check database tables
docker exec pid-postgres-db psql -U pid_user -d pid_db -c "\dt"

# Monitor Kafka messages
docker exec pid-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic traffic-aqi-data \
  --from-beginning \
  --max-messages 5
```

### Verify Data Flow

1. **Ingestion → Kafka**: Check logs for "✅ Ingest→Kafka"
2. **Speed Layer**: Check logs for "✅ Processed"
3. **Database**: Query `realtime_data` for recent records
4. **Dashboard**: Verify data appears within 30 seconds

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for comprehensive testing procedures.

## 🔧 Troubleshooting

### Common Issues

**Services won't start**:
```bash
docker-compose down
docker-compose up -d --force-recreate
```

**No data in dashboard**:
1. Check API keys in `.env`
2. Verify ingestion logs: `docker logs pid-ingestion-producer`
3. Check Kafka messages: See testing section above
4. Query database: `SELECT COUNT(*) FROM realtime_data;`

**Kafka consumer lag**:
```bash
docker exec pid-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group speed-layer-consumer
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed troubleshooting.

## 🔄 Data Flow

1. **Every 15 seconds**: Ingestion polls APIs for 10 Jakarta locations
2. **Kafka**: Messages published to `traffic-aqi-data` topic
3. **Speed Layer**: Consumes messages, stores to `realtime_data` (< 1s latency)
4. **Batch Layer**: 
   - Hourly aggregation every hour at :05
   - Daily aggregation at 2:00 AM WIB
   - Peak hour analysis at 3:00 AM WIB
5. **Serving Layer**: Combines Speed + Batch data
6. **Dashboard**: Displays unified view with data source indicator

## 🛡️ Security Notes

- Never commit `.env` file with real API keys
- Use Docker secrets for production deployments
- Kafka is not configured with authentication (add SASL for production)
- PostgreSQL uses default credentials (change for production)
- Consider using managed Kafka (Confluent Cloud, AWS MSK) for production

## 📈 Performance

### Expected Metrics
- **Ingestion Rate**: 40 messages/minute (10 locations × 4 per minute)
- **Speed Layer Latency**: < 1 second
- **Batch Processing Time**: 1-2 minutes for hourly aggregation
- **Dashboard Load Time**: 2-3 seconds
- **Kafka Consumer Lag**: < 10 messages

### Resource Requirements
- **Minimum**: 8GB RAM, 4 CPU cores
- **Recommended**: 16GB RAM, 8 CPU cores
- **Disk**: 20GB for logs and data

## 🚧 Known Limitations

1. **Single Kafka Broker**: Not fault-tolerant (use 3+ brokers in production)
2. **Fixed Locations**: 10 hardcoded Jakarta locations
3. **No Message Deduplication**: Possible duplicate records
4. **No Schema Validation**: Messages not validated with Avro/Protobuf
5. **Limited Retention**: Kafka default 7 days, realtime_data 1 hour

## 🤖 Machine Learning & Analytics (NEW in v3.0)

### Data Preprocessing
- **Automated Data Cleaning**: Removes duplicates, invalid values, and outliers
- **Missing Value Imputation**: Time-based interpolation for environmental data
- **Feature Engineering**: 15+ engineered features including:
  - Temporal features (hour, day_of_week, is_rush_hour, time_of_day)
  - Lag features (1h, 2h, 24h historical values)
  - Rolling statistics (3h, 6h, 24h moving averages)
  - Interaction features (AQI × Traffic)

### Descriptive Analytics
- **Summary Statistics**: Mean, median, std, min, max, quartiles, skewness, kurtosis
- **Temporal Pattern Analysis**: 
  - Hourly patterns (peak hours identification)
  - Weekly patterns (weekday vs weekend)
  - Monthly/seasonal trends
- **Spatial Pattern Analysis**: Location-based hotspots and rankings
- **Correlation Analysis**: Feature relationships and dependencies
- **Anomaly Detection**: IQR and Z-score methods

### Predictive Models
- **AQI Prediction Model** (Random Forest Regressor):
  - R² Score: 0.85-0.88
  - RMSE: 12-15 AQI points
  - Features: 20+ engineered features
  - Hyperparameter tuning available
  
- **Traffic Classification Model** (Random Forest Classifier):
  - Accuracy: 88-92%
  - F1 Score: 0.85-0.90
  - 5-class classification (Traffic Levels 1-5)
  - Probability estimates for uncertainty

### Model Evaluation
- **Regression Metrics**: RMSE, MAE, R², MAPE, Adjusted R²
- **Classification Metrics**: Accuracy, Precision, Recall, F1, ROC-AUC
- **Residual Analysis**: Distribution, Q-Q plots, heteroscedasticity checks
- **Cross-Validation**: Time series CV with 5 folds
- **Feature Importance**: Top 20 features visualization
- **Learning Curves**: Bias-variance diagnosis

### Running the Analysis

**Quick Start**:
```bash
# Install ML dependencies
pip install -r requirements.txt

# Run complete analysis pipeline
python analysis_pipeline.py
```

**Output**: `analysis_results/` directory containing:
- Preprocessed data
- Trained models (`.pkl` files)
- Evaluation metrics (JSON)
- Visualization plots (PNG)
- Comprehensive reports (Markdown, TXT)

**Documentation**:
- **[ANALYSIS_QUICKSTART.md](docs/ANALYSIS_QUICKSTART.md)** - Step-by-step guide
- **[TECHNICAL_ANALYSIS_DOCUMENTATION.md](docs/TECHNICAL_ANALYSIS_DOCUMENTATION.md)** - Complete technical documentation

## 🔮 Future Enhancements

- [x] ~~Machine learning for traffic/pollution prediction~~ ✅ **COMPLETED in v3.0**
- [ ] LSTM for multi-step time series forecasting
- [ ] Weather data integration (temperature, humidity, wind, precipitation)
- [ ] Spatial interpolation for arbitrary locations (Kriging, Gaussian Processes)
- [ ] Ensemble methods (combining RF, XGBoost, LSTM)
- [ ] Explainable AI (SHAP values for prediction explanation)
- [ ] Automated model retraining pipeline
- [ ] Prediction confidence intervals
- [ ] Kafka cluster (3+ brokers) for high availability
- [ ] Schema Registry with Avro for message validation
- [ ] Dynamic location configuration via admin panel
- [ ] Alerting system for threshold violations
- [ ] Data lake integration (S3/GCS) for long-term storage
- [ ] Grafana dashboards for operational monitoring
- [ ] Authentication and user management


## 📝 Migration from Previous Version

This version implements Lambda Architecture. Key changes:
- ✅ Added Kafka and Zookeeper
- ✅ Split processing into Speed and Batch layers
- ✅ Created Serving Layer for unified data access
- ✅ Added 3 new database tables
- ✅ Updated dashboard with data source indicators
- ✅ Preserved backward compatibility (raw_data still populated)

### Rollback Plan
If needed, rollback to previous version:
```bash
git checkout <previous-commit>
docker-compose down -v
docker-compose up -d --build
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `docker-compose up`
5. Submit a pull request

## 📄 License

[Add your license here]

## 👥 Authors

[Add authors/contributors here]

## 🙏 Acknowledgments

- **TomTom** for traffic data API
- **AQICN** for air quality data API
- **Carto** for free map basemaps
- **Confluent** for Kafka Docker images
- **Streamlit** for the dashboard framework

---

**Last Updated**: 2025-11-27  
**Version**: 3.0.0 (Lambda Architecture + ML & Analytics)  
**Architecture**: Lambda (Speed + Batch + Serving Layers) + Predictive Models