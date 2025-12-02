# Deployment Guide

Complete guide for deploying Jakarta Traffic & Pollution Monitoring System.

---

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Compose Deployment](#docker-compose-deployment)
3. [Streamlit Cloud Deployment](#streamlit-cloud-deployment)
4. [VPS/Server Deployment](#vpsserver-deployment)
5. [Cloud Platform Deployment](#cloud-platform-deployment)
6. [Production Checklist](#production-checklist)

---

## 1. Local Development

### Prerequisites

- Python 3.9+
- PostgreSQL 14+
- Kafka 2.8+
- Git

### Setup

```bash
# Clone repository
git clone <repository-url>
cd case-based

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
nano .env  # Add your API keys

# Setup database
psql -U postgres -f init.sql

# Run services (separate terminals)
python ingestion_service.py
python speed_layer_service.py
python batch_layer_service.py
streamlit run app.py
```

---

## 2. Docker Compose Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Quick Start

```bash
# 1. Clone and configure
git clone <repository-url>
cd case-based
cp .env.example .env
nano .env  # Add API keys

# 2. Build and start
docker-compose up -d

# 3. Check status
docker-compose ps

# 4. View logs
docker-compose logs -f

# 5. Access dashboard
open http://localhost:8501
```

### Detailed Steps

#### Step 1: Environment Configuration

Create `.env` file with all required variables:

```env
# Database Configuration
POSTGRES_HOST=db
POSTGRES_DB=pid_db
POSTGRES_USER=pid_user
POSTGRES_PASSWORD=your_secure_password_here

# API Keys (REQUIRED!)
TOMTOM_API_KEY=your_tomtom_api_key_here
AQICN_TOKEN=your_aqicn_token_here

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC=traffic-aqi-data
KAFKA_CONSUMER_GROUP=speed-layer-consumer

# Application Configuration
STREAMLIT_SERVER_PORT=8501
```

#### Step 2: Verify Configuration

```bash
# Check if all variables are loaded
docker-compose config | grep -E "TOMTOM|AQICN"

# Should output:
# TOMTOM_API_KEY: your_actual_key
# AQICN_TOKEN: your_actual_token
```

#### Step 3: Start Services

```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d db kafka zookeeper
docker-compose up -d ingestion_service speed_layer batch_layer
docker-compose up -d streamlit_app
```

#### Step 4: Verify Deployment

```bash
# Check all containers are running
docker-compose ps

# Expected output:
# NAME                    STATUS
# pid-postgres-db         Up (healthy)
# pid-kafka               Up (healthy)
# pid-zookeeper           Up
# pid-ingestion-producer  Up
# pid-speed-layer         Up
# pid-batch-layer         Up
# pid-streamlit-app       Up
```

#### Step 5: Monitor Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f ingestion_service
docker-compose logs -f speed_layer
docker-compose logs -f streamlit_app
```

#### Step 6: Access Dashboard

Open browser: `http://localhost:8501`

### Management Commands

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data!)
docker-compose down -v

# Restart specific service
docker-compose restart ingestion_service

# Rebuild and restart
docker-compose up -d --build

# View resource usage
docker stats

# Execute command in container
docker exec -it pid-postgres-db psql -U pid_user -d pid_db
```

---

## 3. Streamlit Cloud Deployment

### Overview

Streamlit Cloud provides free hosting for Streamlit apps. However, it only hosts the dashboard - other services must be deployed separately.

### Prerequisites

- GitHub account
- Streamlit Cloud account ([streamlit.io/cloud](https://streamlit.io/cloud))
- Managed PostgreSQL database (AWS RDS, DigitalOcean, etc.)

### Architecture

```
┌─────────────────────────────────────────┐
│ Streamlit Cloud                         │
│ ┌─────────────────────────────────────┐ │
│ │ Dashboard (app.py)                  │ │
│ └─────────────┬───────────────────────┘ │
└───────────────┼─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ Your VPS/Server                         │
│ ┌─────────────────────────────────────┐ │
│ │ PostgreSQL Database                 │ │
│ │ Ingestion Service                   │ │
│ │ Speed Layer                         │ │
│ │ Batch Layer                         │ │
│ │ Kafka                               │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Step-by-Step Guide

#### Step 1: Setup Database

Deploy PostgreSQL on managed service:

**Option A: AWS RDS**
1. Create PostgreSQL 14 instance
2. Note connection details
3. Run `init.sql` to create tables

**Option B: DigitalOcean Managed Database**
1. Create PostgreSQL cluster
2. Add your IP to trusted sources
3. Run `init.sql`

**Option C: Railway.app**
1. Create new project
2. Add PostgreSQL service
3. Get connection string
4. Run `init.sql`

#### Step 2: Setup Backend Services

Deploy on VPS (see VPS Deployment section):
```bash
# On your VPS
docker-compose up -d db kafka zookeeper ingestion_service speed_layer batch_layer
```

#### Step 3: Prepare Repository

```bash
# Create requirements.txt for Streamlit Cloud
cat > requirements_streamlit.txt << EOF
streamlit==1.28.0
pandas==2.0.3
pydeck==0.8.0
plotly==5.17.0
psycopg2-binary==2.9.7
python-dotenv==1.0.0
EOF

# Create .streamlit/config.toml
mkdir -p .streamlit
cat > .streamlit/config.toml << EOF
[server]
port = 8501
enableCORS = false
enableXsrfProtection = false

[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
font = "sans serif"
EOF

# Commit and push
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

#### Step 4: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select your GitHub repository
4. Configure:
   - **Main file:** `app.py`
   - **Python version:** 3.9
   - **Requirements file:** `requirements_streamlit.txt` (if created)

5. Add secrets in "Advanced settings":
```toml
# .streamlit/secrets.toml
POSTGRES_HOST = "your-db-host.amazonaws.com"
POSTGRES_PORT = "5432"
POSTGRES_DB = "pid_db"
POSTGRES_USER = "pid_user"
POSTGRES_PASSWORD = "your-password"
```

6. Click "Deploy"

#### Step 5: Update Database Connection

Modify `models/database.py` to use Streamlit secrets:

```python
import streamlit as st

class DatabaseConnection:
    def __init__(self):
        # Try Streamlit secrets first, then environment variables
        try:
            self.host = st.secrets["POSTGRES_HOST"]
            self.port = st.secrets.get("POSTGRES_PORT", "5432")
            self.database = st.secrets["POSTGRES_DB"]
            self.user = st.secrets["POSTGRES_USER"]
            self.password = st.secrets["POSTGRES_PASSWORD"]
        except:
            self.host = os.getenv("POSTGRES_HOST", "localhost")
            self.port = os.getenv("POSTGRES_PORT", "5432")
            self.database = os.getenv("POSTGRES_DB", "pid_db")
            self.user = os.getenv("POSTGRES_USER", "pid_user")
            self.password = os.getenv("POSTGRES_PASSWORD", "pid_password")
```

### Limitations

- ❌ Cannot run Kafka on Streamlit Cloud
- ❌ Cannot run background services
- ❌ Limited to dashboard only
- ✅ Free tier available
- ✅ Automatic HTTPS
- ✅ Easy deployment

---

## 4. VPS/Server Deployment

### Prerequisites

- VPS with Ubuntu 20.04+ (DigitalOcean, AWS EC2, Linode, etc.)
- Minimum: 2 CPU, 4GB RAM, 20GB storage
- Recommended: 4 CPU, 8GB RAM, 40GB storage

### Step-by-Step Guide

#### Step 1: Setup VPS

```bash
# SSH to server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

#### Step 2: Setup Firewall

```bash
# Install UFW
apt install ufw

# Allow SSH
ufw allow 22/tcp

# Allow Streamlit
ufw allow 8501/tcp

# Allow PostgreSQL (if needed externally)
ufw allow 5432/tcp

# Enable firewall
ufw enable

# Check status
ufw status
```

#### Step 3: Deploy Application

```bash
# Clone repository
git clone <repository-url>
cd case-based

# Setup environment
cp .env.example .env
nano .env  # Add your API keys

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

#### Step 4: Setup Domain (Optional)

**Using Cloudflare:**

1. Add A record: `traffic.yourdomain.com` → `your-server-ip`
2. Enable proxy (orange cloud)
3. SSL/TLS mode: Full

**Using Nginx Reverse Proxy:**

```bash
# Install Nginx
apt install nginx

# Create config
nano /etc/nginx/sites-available/traffic-dashboard

# Add configuration:
server {
    listen 80;
    server_name traffic.yourdomain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Enable site
ln -s /etc/nginx/sites-available/traffic-dashboard /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

#### Step 5: Setup SSL (Let's Encrypt)

```bash
# Install Certbot
apt install certbot python3-certbot-nginx

# Get certificate
certbot --nginx -d traffic.yourdomain.com

# Auto-renewal is configured automatically
# Test renewal
certbot renew --dry-run
```

#### Step 6: Setup Monitoring

```bash
# Install monitoring tools
apt install htop iotop nethogs

# Monitor Docker containers
docker stats

# Setup log rotation
nano /etc/logrotate.d/docker-compose

# Add:
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    missingok
    delaycompress
    copytruncate
}
```

#### Step 7: Setup Backups

```bash
# Create backup script
nano /root/backup-database.sh

# Add:
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/backups"
mkdir -p $BACKUP_DIR

docker exec pid-postgres-db pg_dump -U pid_user pid_db > $BACKUP_DIR/backup_$DATE.sql
gzip $BACKUP_DIR/backup_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

# Make executable
chmod +x /root/backup-database.sh

# Add to crontab
crontab -e

# Add line (daily at 2 AM):
0 2 * * * /root/backup-database.sh
```

---

## 5. Cloud Platform Deployment

### AWS Deployment

**Services Used:**
- **ECS Fargate:** Container hosting
- **RDS PostgreSQL:** Database
- **MSK:** Managed Kafka
- **ECR:** Container registry
- **CloudWatch:** Monitoring

**Estimated Cost:** $50-100/month

### Google Cloud Deployment

**Services Used:**
- **Cloud Run:** Container hosting
- **Cloud SQL:** PostgreSQL
- **Pub/Sub:** Message streaming (Kafka alternative)
- **Container Registry:** Image storage
- **Cloud Monitoring:** Observability

**Estimated Cost:** $40-80/month

### Azure Deployment

**Services Used:**
- **Container Instances:** Container hosting
- **Azure Database for PostgreSQL:** Database
- **Event Hubs:** Kafka-compatible streaming
- **Container Registry:** Image storage
- **Azure Monitor:** Monitoring

**Estimated Cost:** $45-90/month

---

## 6. Production Checklist

### Pre-Deployment

- [ ] All API keys configured in `.env`
- [ ] Database password changed from default
- [ ] Firewall configured
- [ ] SSL certificate installed
- [ ] Backup strategy implemented
- [ ] Monitoring setup
- [ ] Log rotation configured

### Security

- [ ] API keys not in git repository
- [ ] Database not exposed to public
- [ ] HTTPS enabled
- [ ] Regular security updates scheduled
- [ ] Access logs enabled

### Performance

- [ ] Database indexes created
- [ ] Kafka retention configured
- [ ] Container resource limits set
- [ ] Caching strategy implemented

### Monitoring

- [ ] Health checks configured
- [ ] Alerts setup for failures
- [ ] Log aggregation setup
- [ ] Performance metrics tracked

### Documentation

- [ ] Deployment process documented
- [ ] Runbook created for common issues
- [ ] Contact information updated
- [ ] Architecture diagram current

---

## Troubleshooting Deployment

### Issue: Container Won't Start

```bash
# Check logs
docker-compose logs <service-name>

# Check if port is in use
lsof -i :8501

# Restart service
docker-compose restart <service-name>
```

### Issue: Database Connection Failed

```bash
# Check if database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Test connection
docker exec -it pid-postgres-db psql -U pid_user -d pid_db
```

### Issue: Kafka Not Working

```bash
# Check Kafka logs
docker-compose logs kafka

# Check Zookeeper
docker-compose logs zookeeper

# Restart Kafka stack
docker-compose restart zookeeper kafka
```

---

**Last Updated:** 2025-12-02  
**Version:** 2.0.0
