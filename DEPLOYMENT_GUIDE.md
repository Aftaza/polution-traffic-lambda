# Lambda Architecture - Deployment Guide

## Overview
This guide will help you deploy the newly implemented Lambda Architecture for the Jakarta Traffic & Pollution Heatmap application.

## Prerequisites
- Docker and Docker Compose installed
- At least 8GB RAM available for Docker
- 4 CPU cores recommended
- API keys for TomTom and AQICN

## Step 1: Update Environment Variables

Update your `.env` file with the Kafka configuration (or create it from `.env.example`):

```bash
# Database Configuration
POSTGRES_HOST=db
POSTGRES_DB=pid_db
POSTGRES_USER=pid_user
POSTGRES_PASSWORD=pid_password

# API Keys
TOMTOM_API_KEY=your_actual_tomtom_key
AQICN_TOKEN=your_actual_aqicn_token

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC=traffic-aqi-data
KAFKA_CONSUMER_GROUP=speed-layer-consumer

# Application Configuration
STREAMLIT_SERVER_PORT=8501
INGESTION_SERVICE_PORT=5000
```

## Step 2: Stop Existing Services

If you have the old version running:

```bash
docker-compose down
```

## Step 3: Clean Up Old Data (Optional)

If you want a fresh start:

```bash
docker-compose down -v  # This removes volumes (WARNING: deletes all data)
```

## Step 4: Build and Start Services

```bash
# Build images with new dependencies
docker-compose build --no-cache

# Start all services
docker-compose up -d
```

## Step 5: Verify Services are Running

Check that all 7 services are up:

```bash
docker-compose ps
```

Expected services:
- `pid-zookeeper` - Zookeeper (port 2181)
- `pid-kafka` - Kafka broker (ports 9092, 9093)
- `pid-postgres-db` - PostgreSQL (port 5432)
- `pid-ingestion-producer` - Kafka producer (ingestion)
- `pid-speed-layer` - Kafka consumer (real-time processing)
- `pid-batch-layer` - Batch processor (aggregations)
- `pid-streamlit-app` - Dashboard (port 8501)

## Step 6: Monitor Logs

### All Services
```bash
docker-compose logs -f
```

### Specific Services
```bash
# Kafka messages
docker-compose logs -f ingestion_service

# Speed layer processing
docker-compose logs -f speed_layer

# Batch layer processing
docker-compose logs -f batch_layer

# Dashboard
docker-compose logs -f streamlit_app
```

## Step 7: Verify Kafka Topics

Check that the Kafka topic was created:

```bash
docker exec -it pid-kafka kafka-topics --list --bootstrap-server localhost:9092
```

You should see: `traffic-aqi-data`

## Step 8: Monitor Kafka Messages

Watch messages being produced:

```bash
docker exec -it pid-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic traffic-aqi-data \
  --from-beginning \
  --max-messages 10
```

## Step 9: Verify Database Tables

Connect to PostgreSQL and verify tables exist:

```bash
docker exec -it pid-postgres-db psql -U pid_user -d pid_db
```

Then run:
```sql
-- Check tables exist
\dt

-- Check raw_data (from ingestion backup)
SELECT COUNT(*) FROM raw_data;

-- Check realtime_data (from speed layer)
SELECT COUNT(*) FROM realtime_data WHERE is_active = TRUE;

-- Check batch_aggregations (from batch layer)
SELECT COUNT(*) FROM batch_aggregations;

-- Check peak_hours
SELECT * FROM peak_hours ORDER BY analysis_date DESC LIMIT 5;
```

Exit with `\q`

## Step 10: Access Dashboard

Open your browser and navigate to:
```
http://localhost:8501
```

You should see:
- ✅ Update timestamp in WIB timezone
- ✅ Data source indicator badge (Speed Layer or Batch Layer)
- ✅ AQI legend
- ✅ Peak hours analysis
- ✅ Heatmap visualizations

## Troubleshooting

### Service Won't Start

**If Kafka fails to start:**
```bash
# Check if Zookeeper is healthy
docker logs pid-zookeeper

# Restart Kafka
docker-compose restart kafka
```

**If ingestion_service fails:**
```bash
# Check logs for API key issues
docker logs pid-ingestion-producer

# Verify API keys in .env file
```

### No Data Appearing

**Check ingestion to Kafka:**
```bash
# Should see "✅ Ingest→Kafka" messages
docker logs pid-ingestion-producer --tail 50
```

**Check speed layer consumption:**
```bash
# Should see "✅ Processed" messages
docker logs pid-speed-layer --tail 50
```

**Check database:**
```bash
docker exec -it pid-postgres-db psql -U pid_user -d pid_db -c \
  "SELECT COUNT(*), MAX(timestamp) FROM realtime_data WHERE is_active = TRUE;"
```

### Kafka Consumer Lag

Check consumer group lag:
```bash
docker exec pid-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group speed-layer-consumer
```

If lag is increasing, the speed layer might be overloaded.

### Dashboard Shows "No Data"

1. Wait 15-30 seconds for initial data ingestion
2. Check that at least one service has data:
   - Speed Layer: `SELECT * FROM realtime_data LIMIT 5;`
   - Batch Layer: `SELECT * FROM batch_aggregations LIMIT 5;`
   - Fallback: `SELECT * FROM raw_data LIMIT 5;`

## Performance Tuning

### Increase Kafka Resources

Edit `docker-compose.yml`:
```yaml
kafka:
  ...
  environment:
    ...
    KAFKA_HEAP_OPTS: "-Xms1g -Xmx2g"  # Increase memory
```

### Adjust Speed Layer Window

Edit `models/stream_processor.py`:
```python
self.window_size_minutes = 10  # Increase from 5 to 10 minutes
```

### Adjust Batch Schedule

Edit `batch_layer_service.py` to change batch job times.

## Data Flow Verification

Expected flow:
1. **Ingestion → Kafka**: Every 15 seconds, 10 locations
2. **Kafka → Speed Layer**: Real-time consumption to `realtime_data`
3. **Kafka → raw_data**: Backup for batch processing
4. **Batch Layer**: Hourly aggregation every hour, daily at 2 AM
5. **Serving Layer**: Combines speed + batch for dashboard
6. **Dashboard**: Displays combined data with source indicator

## Health Check

Run this script to check all components:

```bash
#!/bin/bash
echo "=== Service Status ==="
docker-compose ps

echo -e "\n=== Kafka Topics ==="
docker exec pid-kafka kafka-topics --list --bootstrap-server localhost:9092

echo -e "\n=== Database Counts ==="
docker exec pid-postgres-db psql -U pid_user -d pid_db -c "
  SELECT 'raw_data' as table_name, COUNT(*) as count FROM raw_data
  UNION ALL
  SELECT 'realtime_data', COUNT(*) FROM realtime_data WHERE is_active = TRUE
  UNION ALL
  SELECT 'batch_aggregations', COUNT(*) FROM batch_aggregations
  UNION ALL
  SELECT 'peak_hours', COUNT(*) FROM peak_hours;
"

echo -e "\n=== Consumer Lag ==="
docker exec pid-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group speed-layer-consumer

echo -e "\n✅ Health check complete!"
```

Save as `health_check.sh` and run with `bash health_check.sh`

## Rollback Plan

If you need to rollback to the previous version:

1. Stop new services:
   ```bash
   docker-compose down
   ```

2. Restore old docker-compose.yml from git:
   ```bash
   git checkout HEAD~1 docker-compose.yml
   ```

3. Restore old files:
   ```bash
   git checkout HEAD~1 models/ingestion_service.py
   git checkout HEAD~1 app.py
   git checkout HEAD~1 requirements.txt
   ```

4. Restart with old version:
   ```bash
   docker-compose up -d --build
   ```

## Next Steps

After successful deployment:
- ✅ Monitor for 24 hours to verify stability
- ✅ Check Kafka disk usage growth
- ✅ Verify batch jobs run correctly at scheduled times
- ✅ Test peak hour analysis after first full day
- ✅ Set up alerts for service failures
- ✅ Consider Kafka topic retention policies

## Support

For issues, check:
- Docker logs: `docker-compose logs -f [service_name]`
- Database: Connect with psql and query tables
- Kafka: Use kafka-console-consumer to inspect messages
