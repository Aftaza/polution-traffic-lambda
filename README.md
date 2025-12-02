# Jakarta Traffic & Pollution Monitoring System

## 🚀 Quick Start

Sistem monitoring real-time untuk traffic dan polusi udara di Jakarta menggunakan Lambda Architecture.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Deployment](#deployment)
7. [Usage](#usage)
8. [API Documentation](#api-documentation)
9. [Troubleshooting](#troubleshooting)
10. [Contributing](#contributing)

---

## 🎯 Overview

### Features

- ✅ **Real-time Traffic Monitoring** - Data dari TomTom API
- ✅ **Air Quality Monitoring** - Data AQI dari AQICN
- ✅ **Lambda Architecture** - Speed + Batch + Serving Layers
- ✅ **Interactive Dashboard** - Streamlit dengan visualisasi pinpoint
- ✅ **Peak Hours Analysis** - Analisis jam puncak otomatis
- ✅ **Historical Data** - Batch processing untuk analisis historis
- ✅ **Kafka Streaming** - Real-time data streaming
- ✅ **PostgreSQL Storage** - Reliable data persistence

### Tech Stack

- **Backend:** Python 3.9+
- **Database:** PostgreSQL 14
- **Streaming:** Apache Kafka
- **Dashboard:** Streamlit
- **Visualization:** Pydeck, Plotly
- **Containerization:** Docker & Docker Compose

---

## 🏗️ Architecture

### Lambda Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LAMBDA ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  External APIs (TomTom, AQICN)                             │
│         ↓                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ INGESTION LAYER                                      │  │
│  │ - Polls APIs every 5 minutes                         │  │
│  │ - Sends to Kafka + raw_data table                    │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                           │
│         ┌───────┴────────┬──────────────────────┐          │
│         ▼                ▼                      ▼          │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ SPEED LAYER  │  │ BATCH LAYER  │  │ SERVING LAYER   │  │
│  │ (Real-time)  │  │ (Historical) │  │ (Unified Query) │  │
│  └──────┬───────┘  └──────┬───────┘  └────────▲────────┘  │
│         │                 │                    │           │
│         └─────────────────┴────────────────────┘           │
│                           │                                │
│                           ▼                                │
│                  ┌─────────────────┐                       │
│                  │ PostgreSQL DB   │                       │
│                  └─────────────────┘                       │
│                           ▲                                │
│                           │                                │
│                  ┌─────────────────┐                       │
│                  │ STREAMLIT APP   │                       │
│                  │ (Dashboard)     │                       │
│                  └─────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### Services

| Service | Container | Purpose |
|---------|-----------|---------|
| **Zookeeper** | `pid-zookeeper` | Kafka coordination |
| **Kafka** | `pid-kafka` | Message streaming |
| **PostgreSQL** | `pid-postgres-db` | Data storage |
| **Ingestion** | `pid-ingestion-producer` | API polling & Kafka producer |
| **Speed Layer** | `pid-speed-layer` | Real-time processing |
| **Batch Layer** | `pid-batch-layer` | Historical aggregation |
| **Dashboard** | `pid-streamlit-app` | Web UI (port 8501) |

---

## 📦 Prerequisites

### Required

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **API Keys:**
  - TomTom API Key ([Get here](https://developer.tomtom.com/))
  - AQICN Token ([Get here](https://aqicn.org/data-platform/token/))

### Optional

- **Git** (for cloning repository)
- **Python 3.9+** (for local development)

---

## 🔧 Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd case-based
```

### 2. Setup Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

**Required variables in `.env`:**
```env
# Database
POSTGRES_DB=pid_db
POSTGRES_USER=pid_user
POSTGRES_PASSWORD=your_secure_password

# API Keys (REQUIRED!)
TOMTOM_API_KEY=your_tomtom_api_key_here
AQICN_TOKEN=your_aqicn_token_here

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC=traffic-aqi-data
```

### 3. Verify Configuration

```bash
# Check if all required variables are set
docker-compose config | grep -E "TOMTOM|AQICN"
```

---

## 🚀 Deployment

### Option 1: Docker Compose (Recommended)

#### Start All Services

```bash
# Build and start all containers
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Stop Services

```bash
# Stop all containers
docker-compose down

# Stop and remove volumes (WARNING: deletes data!)
docker-compose down -v
```

#### Restart Specific Service

```bash
# Restart ingestion service
docker-compose restart ingestion_service

# Restart dashboard
docker-compose restart streamlit_app
```

### Option 2: Streamlit Cloud Deployment

#### Prerequisites
- GitHub repository
- Streamlit Cloud account ([streamlit.io/cloud](https://streamlit.io/cloud))

#### Steps

1. **Push to GitHub:**
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

2. **Deploy on Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your repository
   - Set main file: `app.py`
   - Add secrets in "Advanced settings":
     ```toml
     POSTGRES_HOST = "your-db-host"
     POSTGRES_DB = "pid_db"
     POSTGRES_USER = "pid_user"
     POSTGRES_PASSWORD = "your-password"
     ```

3. **Deploy Database Separately:**
   - Use managed PostgreSQL (e.g., AWS RDS, DigitalOcean)
   - Run `init.sql` to create tables
   - Update connection string in Streamlit secrets

**Note:** Streamlit Cloud deployment hanya untuk dashboard. Services lain (Kafka, Speed Layer, Batch Layer) harus di-deploy terpisah.

### Option 3: Production Server Deployment

#### Using Docker Compose on VPS

1. **Setup VPS:**
```bash
# SSH to server
ssh user@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. **Clone and Configure:**
```bash
git clone <repository-url>
cd case-based
cp .env.example .env
nano .env  # Add your API keys
```

3. **Deploy:**
```bash
# Start services
docker-compose up -d

# Setup firewall
sudo ufw allow 8501/tcp  # Streamlit
sudo ufw allow 5432/tcp  # PostgreSQL (if needed)
```

4. **Setup Reverse Proxy (Optional):**

Using Nginx:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

5. **Setup SSL (Optional):**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 📊 Usage

### Access Dashboard

**Local:**
```
http://localhost:8501
```

**Production:**
```
http://your-server-ip:8501
# or
https://your-domain.com
```

### Dashboard Features

#### 1. **Heatmaps Tab** 🗺️
- Traffic heatmap dengan pinpoint berwarna
- AQI heatmap dengan kategori
- Hover untuk detail informasi
- Legenda interaktif

#### 2. **Peak Hours Analysis Tab** 📊
- Grafik traffic by hour
- Grafik AQI by hour
- Combined view (Traffic vs AQI)
- Peak hours indicator

#### 3. **Statistics Tab** 📈
- Real-time metrics
- Traffic level distribution
- AQI category distribution
- Average values

#### 4. **Raw Data Tab** 📋
- Real-time data table
- Sortable columns
- Download CSV
- Summary metrics

### Timezone

All timestamps displayed in **WIB (UTC+7)** for user convenience.
Database stores in **UTC** for consistency.

---

## 🔍 Monitoring

### Check Service Health

```bash
# All services
docker-compose ps

# Specific service logs
docker-compose logs -f ingestion_service
docker-compose logs -f speed_layer
docker-compose logs -f batch_layer
docker-compose logs -f streamlit_app
```

### Database Access

```bash
# Connect to PostgreSQL
docker exec -it pid-postgres-db psql -U pid_user -d pid_db

# Check tables
\dt

# Query real-time data
SELECT * FROM realtime_data ORDER BY timestamp DESC LIMIT 10;

# Check batch aggregations
SELECT * FROM batch_aggregations ORDER BY date DESC LIMIT 10;
```

### Kafka Monitoring

```bash
# List topics
docker exec pid-kafka kafka-topics --list --bootstrap-server localhost:9092

# Check consumer groups
docker exec pid-kafka kafka-consumer-groups --list --bootstrap-server localhost:9092

# View messages
docker exec pid-kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic traffic-aqi-data --from-beginning --max-messages 10
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. **Ingestion Service Crashes**

**Error:** `ValueError: TOMTOM_API_KEY and AQICN_TOKEN must be set`

**Solution:**
```bash
# Check .env file
cat .env | grep -E "TOMTOM|AQICN"

# Ensure keys are set
docker-compose config | grep -E "TOMTOM|AQICN"

# Restart service
docker-compose restart ingestion_service
```

#### 2. **Dashboard Shows No Data**

**Solution:**
```bash
# Check if ingestion is running
docker-compose logs ingestion_service

# Check database
docker exec -it pid-postgres-db psql -U pid_user -d pid_db -c "SELECT COUNT(*) FROM realtime_data;"

# Wait 5-10 minutes for data to accumulate
```

#### 3. **Kafka Connection Issues**

**Solution:**
```bash
# Check Kafka health
docker-compose logs kafka

# Restart Kafka
docker-compose restart kafka zookeeper

# Wait for Kafka to be ready
docker-compose logs -f kafka | grep "started"
```

#### 4. **Port Already in Use**

**Error:** `Bind for 0.0.0.0:8501 failed: port is already allocated`

**Solution:**
```bash
# Find process using port
lsof -i :8501  # macOS/Linux
netstat -ano | findstr :8501  # Windows

# Kill process or change port in docker-compose.yml
```

---

## 📚 Additional Documentation

Detailed documentation available in `docs/` folder:

- **[ARCHITECTURE_ANALYSIS.md](docs/ARCHITECTURE_ANALYSIS.md)** - Lambda Architecture deep dive
- **[ENV_ANALYSIS.md](docs/ENV_ANALYSIS.md)** - Environment variables guide
- **[TIMEZONE_RAWDATA_UPDATE.md](docs/TIMEZONE_RAWDATA_UPDATE.md)** - Timezone handling
- **[VISUALIZATION_UPDATE.md](docs/VISUALIZATION_UPDATE.md)** - Visualization features
- **[MIGRATION_SUMMARY.md](docs/MIGRATION_SUMMARY.md)** - Feature migration notes

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 👥 Authors

- **Your Name** - Initial work

---

## 🙏 Acknowledgments

- TomTom API for traffic data
- AQICN for air quality data
- Streamlit for dashboard framework
- Apache Kafka for streaming platform

---

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Contact: your-email@example.com

---

**Last Updated:** 2025-12-02  
**Version:** 2.0.0