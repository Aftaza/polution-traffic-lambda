# Architecture Documentation

## Lambda Architecture Implementation

### Overview

Sistem ini mengimplementasikan **Lambda Architecture** untuk memproses data traffic dan polusi udara secara real-time dan batch.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAMBDA ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐                                              │
│  │ External APIs│                                              │
│  │ - TomTom     │                                              │
│  │ - AQICN      │                                              │
│  └──────┬───────┘                                              │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ INGESTION LAYER (Container: ingestion_service)          │  │
│  │ - Polls APIs every 5 minutes                            │  │
│  │ - Sends to Kafka topic: "traffic-aqi-data"              │  │
│  │ - Backup to raw_data table (with is_peak_hour, aqi_cat) │  │
│  └──────────────┬───────────────────────────────────────────┘  │
│                 │                                               │
│                 │ Kafka Stream                                  │
│                 │                                               │
│         ┌───────┴────────┬──────────────────────────┐          │
│         ▼                ▼                          ▼          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ SPEED LAYER  │  │ BATCH LAYER  │  │ SERVING LAYER        │ │
│  │ (Container)  │  │ (Container)  │  │ (Embedded in App)    │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
│         │                 │                          ▲          │
│         │                 │                          │          │
│         ▼                 ▼                          │          │
│  ┌──────────────────────────────────────────────────┴────────┐ │
│  │              PostgreSQL Database                          │ │
│  │  - raw_data (historical)                                  │ │
│  │  - realtime_data (speed layer)                            │ │
│  │  - batch_aggregations (batch layer)                       │ │
│  │  - peak_hours_analysis (both layers)                      │ │
│  │  - peak_hours, daily_summary (batch layer)                │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ PRESENTATION LAYER (Container: streamlit_app)             │ │
│  │ - Uses ServingLayer class to query data                   │ │
│  │ - Combines Speed + Batch data                             │ │
│  │ - 4 Tabs: Heatmaps, Peak Hours, Statistics, Raw Data      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layers Explanation

### 1. Ingestion Layer

**Purpose:** Collect data from external APIs

**Components:**
- `ingestion_service.py` - Main service
- `models/ingestion_service.py` - API polling logic
- `models/data_repository.py` - Database backup

**Data Flow:**
```
External APIs → Ingestion Service → Kafka Topic + raw_data table
```

**Key Features:**
- Polls TomTom API for traffic data
- Polls AQICN API for air quality data
- Enriches data with `is_peak_hour` and `aqi_category`
- Sends to Kafka for real-time processing
- Backs up to `raw_data` for batch processing

**Schedule:** Every 5 minutes (configurable)

---

### 2. Speed Layer (Real-time Processing)

**Purpose:** Process streaming data in real-time

**Components:**
- `speed_layer_service.py` - Kafka consumer
- `models/stream_processor.py` - Stream processing logic
- `models/kafka_consumer.py` - Kafka wrapper

**Data Flow:**
```
Kafka Topic → Speed Layer → realtime_data + peak_hours_analysis
```

**Key Features:**
- Consumes messages from Kafka
- Real-time peak hour detection
- Real-time AQI categorization
- Incremental aggregation to `peak_hours_analysis`
- Stores in `realtime_data` table

**Processing Time:** < 1 second per message

---

### 3. Batch Layer (Historical Processing)

**Purpose:** Process historical data for accurate aggregations

**Components:**
- `batch_layer_service.py` - Scheduler
- `models/batch_processor.py` - Batch processing logic

**Data Flow:**
```
raw_data → Batch Layer → batch_aggregations + peak_hours + daily_summary
```

**Key Features:**
- Daily aggregations (runs at 00:00)
- Hourly aggregations (runs every hour)
- Peak hours analysis (daily)
- Historical trend analysis

**Schedule:**
- Daily aggregation: 00:00 WIB
- Hourly aggregation: Every hour
- Peak hours analysis: Daily at 01:00 WIB

---

### 4. Serving Layer (Query Interface)

**Purpose:** Provide unified access to Speed + Batch data

**Components:**
- `models/serving_layer.py` - Query abstraction

**Data Flow:**
```
realtime_data + batch_aggregations → ServingLayer → Dashboard
```

**Key Features:**
- Combines Speed and Batch data
- Intelligent fallback (Speed → Batch)
- Optimized queries
- Data freshness detection

**Why No Container?**
- Serving Layer is a **library**, not a service
- Embedded in Streamlit app
- No long-running process needed
- More efficient (no network overhead)

---

### 5. Presentation Layer (Dashboard)

**Purpose:** Display data to users

**Components:**
- `app.py` - Streamlit dashboard
- `models/visualization.py` - Visualization service

**Features:**
- **Tab 1: Heatmaps** - Traffic & AQI pinpoint maps
- **Tab 2: Peak Hours Analysis** - Hourly trends
- **Tab 3: Statistics** - Real-time metrics
- **Tab 4: Raw Data** - Data table with download

**Access:** http://localhost:8501

---

## Database Schema

### Tables

#### 1. `raw_data` (Ingestion Layer)
```sql
- id (SERIAL PRIMARY KEY)
- timestamp (TIMESTAMP)
- location (VARCHAR)
- latitude (DECIMAL)
- longitude (DECIMAL)
- aqi_value (INTEGER)
- traffic_level (INTEGER)
- is_peak_hour (BOOLEAN)      -- NEW
- aqi_category (VARCHAR)       -- NEW
- created_at (TIMESTAMP)
```

#### 2. `realtime_data` (Speed Layer)
```sql
- id (SERIAL PRIMARY KEY)
- timestamp (TIMESTAMP)
- location (VARCHAR)
- latitude (DECIMAL)
- longitude (DECIMAL)
- aqi_value (INTEGER)
- traffic_level (INTEGER)
- is_peak_hour (BOOLEAN)      -- NEW
- aqi_category (VARCHAR)       -- NEW
- created_at (TIMESTAMP)
```

#### 3. `batch_aggregations` (Batch Layer)
```sql
- id (SERIAL PRIMARY KEY)
- date (DATE)
- location (VARCHAR)
- avg_aqi (DECIMAL)
- avg_traffic (DECIMAL)
- max_aqi (INTEGER)
- max_traffic (INTEGER)
- is_peak_hour (BOOLEAN)      -- NEW
- created_at (TIMESTAMP)
```

#### 4. `peak_hours_analysis` (Speed + Batch Layers)
```sql
- id (SERIAL PRIMARY KEY)
- date (DATE)
- hour (INTEGER)
- location (VARCHAR)
- avg_traffic_level (DECIMAL)
- avg_aqi_value (DECIMAL)
- is_peak_hour (BOOLEAN)
- total_records (INTEGER)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

#### 5. `peak_hours` (Batch Layer)
```sql
- id (SERIAL PRIMARY KEY)
- date (DATE)
- hour (INTEGER)
- location (VARCHAR)
- avg_traffic (DECIMAL)
- avg_aqi (DECIMAL)
- created_at (TIMESTAMP)
```

#### 6. `daily_summary` (Batch Layer)
```sql
- id (SERIAL PRIMARY KEY)
- date (DATE)
- total_records (INTEGER)
- avg_aqi (DECIMAL)
- avg_traffic (DECIMAL)
- created_at (TIMESTAMP)
```

---

## Data Flow Details

### Real-time Flow (Speed Layer)

```
1. External API → Ingestion Service
   - TomTom API (traffic data)
   - AQICN API (AQI data)

2. Ingestion Service → Kafka
   - Topic: "traffic-aqi-data"
   - Format: JSON
   - Enriched with is_peak_hour, aqi_category

3. Kafka → Speed Layer
   - Consumer group: "speed-layer-consumer"
   - Processes each message

4. Speed Layer → Database
   - Insert to realtime_data
   - Update peak_hours_analysis (incremental)

5. Database → Serving Layer → Dashboard
   - Query realtime_data
   - Display in dashboard
```

**Latency:** ~2-5 seconds end-to-end

### Batch Flow (Batch Layer)

```
1. Ingestion Service → raw_data table
   - Backup of all incoming data
   - Historical record

2. Scheduler triggers Batch Layer
   - Daily: 00:00 WIB
   - Hourly: Every hour

3. Batch Layer → Database
   - Read from raw_data
   - Aggregate by date/hour/location
   - Write to batch_aggregations, peak_hours, daily_summary

4. Database → Serving Layer → Dashboard
   - Query batch_aggregations
   - Fallback when realtime_data is old
```

**Latency:** Minutes to hours (acceptable for historical data)

---

## Why Lambda Architecture?

### Benefits

1. **Fault Tolerance**
   - If Speed Layer fails, Batch Layer provides data
   - If Batch Layer fails, Speed Layer provides real-time data

2. **Scalability**
   - Speed Layer handles real-time load
   - Batch Layer processes large historical datasets

3. **Accuracy**
   - Speed Layer: Fast but approximate
   - Batch Layer: Slow but accurate
   - Serving Layer: Best of both worlds

4. **Flexibility**
   - Easy to add new data sources
   - Easy to add new aggregations
   - Easy to reprocess historical data

### Trade-offs

1. **Complexity**
   - More components to manage
   - More code to maintain

2. **Duplication**
   - Some logic duplicated in Speed and Batch layers
   - Mitigated by shared utility functions

3. **Resource Usage**
   - Multiple containers running
   - More memory and CPU needed

---

## Performance Characteristics

### Speed Layer

- **Throughput:** ~100 messages/second
- **Latency:** < 1 second
- **Data Retention:** 7 days (configurable)

### Batch Layer

- **Throughput:** Processes all historical data
- **Latency:** Minutes to hours
- **Data Retention:** Unlimited

### Serving Layer

- **Query Time:** < 100ms
- **Cache TTL:** 10 seconds (dashboard)
- **Fallback:** Automatic (Speed → Batch)

---

## Monitoring & Observability

### Health Checks

All containers have health checks:
- **Kafka:** Broker API versions check
- **PostgreSQL:** pg_isready check
- **Services:** Dependency-based startup

### Logs

Access logs via Docker Compose:
```bash
docker-compose logs -f <service-name>
```

### Metrics

Key metrics to monitor:
- Kafka lag (consumer group)
- Database size
- Query response time
- API call success rate

---

## Scaling Considerations

### Horizontal Scaling

**Speed Layer:**
- Add more Kafka consumers
- Partition Kafka topic by location

**Batch Layer:**
- Distribute processing by date ranges
- Use Spark for large datasets

**Database:**
- Read replicas for queries
- Partitioning by date

### Vertical Scaling

- Increase container resources in docker-compose.yml
- Optimize database queries
- Add indexes for common queries

---

## Security

### API Keys

- Stored in `.env` file (not committed to git)
- Passed as environment variables
- Never hardcoded in code

### Database

- Password-protected
- Not exposed to public (only internal network)
- Regular backups recommended

### Network

- All services in private Docker network
- Only Streamlit exposed (port 8501)
- Use reverse proxy (Nginx) for production

---

## Disaster Recovery

### Backup Strategy

1. **Database Backups:**
```bash
docker exec pid-postgres-db pg_dump -U pid_user pid_db > backup.sql
```

2. **Restore:**
```bash
docker exec -i pid-postgres-db psql -U pid_user pid_db < backup.sql
```

3. **Automated Backups:**
- Use cron job for daily backups
- Store in cloud storage (S3, GCS)

### Recovery Scenarios

**Scenario 1: Speed Layer Failure**
- Serving Layer automatically falls back to Batch Layer
- Users see slightly older data
- No data loss (Kafka retains messages)

**Scenario 2: Batch Layer Failure**
- Speed Layer continues processing
- Historical aggregations delayed
- Can reprocess from raw_data when recovered

**Scenario 3: Database Failure**
- Restore from latest backup
- Replay Kafka messages (if within retention)
- Rerun batch processing

---

## Future Enhancements

1. **Machine Learning:**
   - Traffic prediction
   - AQI forecasting
   - Anomaly detection

2. **Additional Data Sources:**
   - Weather data
   - Events data
   - Social media sentiment

3. **Advanced Analytics:**
   - Correlation analysis
   - Trend detection
   - Alert system

4. **Performance:**
   - Caching layer (Redis)
   - CDN for static assets
   - Database optimization

---

**Last Updated:** 2025-12-02  
**Version:** 2.0.0
