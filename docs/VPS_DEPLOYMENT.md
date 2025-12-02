# VPS Deployment Guide

Panduan lengkap untuk deploy Jakarta Traffic & Pollution Monitoring System ke VPS dengan Docker Compose dan Nginx reverse proxy.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [VPS Setup](#vps-setup)
3. [Installation](#installation)
4. [SSL Configuration](#ssl-configuration)
5. [Deployment](#deployment)
6. [Monitoring](#monitoring)
7. [Maintenance](#maintenance)
8. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### VPS Requirements

- **OS:** Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **RAM:** Minimum 4GB (8GB recommended)
- **Storage:** Minimum 20GB SSD
- **CPU:** 2+ cores
- **Network:** Public IP address
- **Domain:** (Optional) untuk SSL/HTTPS

### Required Software

- Docker 20.10+
- Docker Compose 2.0+
- Git
- (Optional) Nginx untuk reverse proxy

### API Keys

- **TomTom API Key:** [Get here](https://developer.tomtom.com/)
- **AQICN Token:** [Get here](https://aqicn.org/data-platform/token/)

---

## 🚀 VPS Setup

### 1. Initial Server Setup

```bash
# SSH to your VPS
ssh root@your-vps-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl git ufw

# Create non-root user (recommended)
sudo adduser deploy
sudo usermod -aG sudo deploy
sudo su - deploy
```

### 2. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Verify installation
docker --version
```

### 3. Install Docker Compose

```bash
# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

### 4. Configure Firewall

```bash
# Enable UFW
sudo ufw enable

# Allow SSH (IMPORTANT!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check status
sudo ufw status
```

---

## 📦 Installation

### 1. Clone Repository

```bash
# Navigate to home directory
cd ~

# Clone repository
git clone <your-repository-url> jakarta-traffic-monitoring
cd jakarta-traffic-monitoring
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
```

**Required variables in `.env`:**

```env
# Database Configuration
POSTGRES_DB=pid_db
POSTGRES_USER=pid_user
POSTGRES_PASSWORD=your_secure_password_here

# API Keys (REQUIRED!)
TOMTOM_API_KEY=your_tomtom_api_key_here
AQICN_TOKEN=your_aqicn_token_here

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC=traffic-aqi-data
```

**Security Tips:**
- Use strong passwords (16+ characters)
- Never commit `.env` to Git
- Keep API keys secure

### 3. Create Required Directories

```bash
# Create nginx directory structure
mkdir -p nginx/ssl

# Set permissions
chmod 755 nginx
chmod 700 nginx/ssl
```

---

## 🔒 SSL Configuration

### Option 1: Let's Encrypt (Recommended)

**Prerequisites:**
- Domain name pointing to your VPS IP
- Port 80 accessible

**Steps:**

```bash
# Install Certbot
sudo apt install -y certbot

# Generate certificates
sudo certbot certonly --standalone \
  -d your-domain.com \
  -d www.your-domain.com \
  --email your-email@example.com \
  --agree-tos

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
sudo chown $USER:$USER nginx/ssl/*.pem
sudo chmod 644 nginx/ssl/*.pem
```

**Update Nginx Configuration:**

```bash
# Edit nginx.conf
nano nginx/nginx.conf

# Uncomment HTTPS server block (lines ~95-155)
# Update server_name with your domain
# Save and exit (Ctrl+X, Y, Enter)
```

**Setup Auto-Renewal:**

```bash
# Test renewal
sudo certbot renew --dry-run

# Add cron job
sudo crontab -e

# Add this line:
0 0,12 * * * certbot renew --quiet && cd /home/deploy/jakarta-traffic-monitoring && docker-compose -f docker-compose.prod.yml restart nginx
```

### Option 2: Cloudflare SSL (Easiest)

1. **Add domain to Cloudflare**
2. **Update DNS records:**
   - Type: A
   - Name: @
   - Content: your-vps-ip
   - Proxy: Enabled (orange cloud)
3. **Enable SSL in Cloudflare:**
   - SSL/TLS → Overview → Full
4. **No Nginx SSL configuration needed** - Cloudflare handles it

### Option 3: Self-Signed (Testing Only)

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privkey.pem \
  -out nginx/ssl/fullchain.pem \
  -subj "/C=ID/ST=Jakarta/L=Jakarta/O=YourOrg/CN=your-domain.com"

# Update nginx.conf (uncomment HTTPS block)
```

**Warning:** Browsers will show security warnings with self-signed certificates.

---

## 🚢 Deployment

### 1. Build and Start Services

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### 2. Verify Deployment

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Check specific service
docker-compose -f docker-compose.prod.yml logs -f streamlit_app
docker-compose -f docker-compose.prod.yml logs -f ingestion_service

# Check Nginx
docker-compose -f docker-compose.prod.yml logs nginx
```

### 3. Test Access

**HTTP (without SSL):**
```
http://your-vps-ip
```

**HTTPS (with SSL):**
```
https://your-domain.com
```

**Health Check:**
```bash
curl http://your-vps-ip/health
# Should return: healthy
```

---

## 📊 Monitoring

### Service Health

```bash
# Check all services
docker-compose -f docker-compose.prod.yml ps

# Check resource usage
docker stats

# Check logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100
```

### Database Monitoring

```bash
# Connect to database
docker exec -it pid-postgres-db psql -U pid_user -d pid_db

# Check data
SELECT COUNT(*) FROM realtime_data;
SELECT COUNT(*) FROM batch_aggregations;

# Exit
\q
```

### Kafka Monitoring

```bash
# List topics
docker exec pid-kafka kafka-topics --list --bootstrap-server localhost:9092

# Check consumer lag
docker exec pid-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group speed-layer-consumer
```

### System Resources

```bash
# Disk usage
df -h

# Memory usage
free -h

# CPU usage
top

# Docker disk usage
docker system df
```

---

## 🔧 Maintenance

### Update Application

```bash
# Pull latest changes
cd ~/jakarta-traffic-monitoring
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### Backup Database

```bash
# Create backup directory
mkdir -p ~/backups

# Backup database
docker exec pid-postgres-db pg_dump -U pid_user pid_db > ~/backups/pid_db_$(date +%Y%m%d_%H%M%S).sql

# Compress backup
gzip ~/backups/pid_db_*.sql
```

### Restore Database

```bash
# Stop services
docker-compose -f docker-compose.prod.yml stop speed_layer batch_layer streamlit_app

# Restore database
gunzip -c ~/backups/pid_db_20250101_120000.sql.gz | \
  docker exec -i pid-postgres-db psql -U pid_user -d pid_db

# Restart services
docker-compose -f docker-compose.prod.yml start speed_layer batch_layer streamlit_app
```

### Clean Up

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused containers
docker container prune

# Full cleanup (careful!)
docker system prune -a --volumes
```

### Log Rotation

```bash
# Configure Docker log rotation
sudo nano /etc/docker/daemon.json

# Add:
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}

# Restart Docker
sudo systemctl restart docker
```

---

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs <service-name>

# Check environment variables
docker-compose -f docker-compose.prod.yml config

# Restart service
docker-compose -f docker-compose.prod.yml restart <service-name>
```

### Nginx 502 Bad Gateway

```bash
# Check if Streamlit is running
docker-compose -f docker-compose.prod.yml ps streamlit_app

# Check Streamlit logs
docker-compose -f docker-compose.prod.yml logs streamlit_app

# Restart Streamlit
docker-compose -f docker-compose.prod.yml restart streamlit_app
```

### Database Connection Issues

```bash
# Check database health
docker-compose -f docker-compose.prod.yml ps db

# Check database logs
docker-compose -f docker-compose.prod.yml logs db

# Restart database
docker-compose -f docker-compose.prod.yml restart db
```

### Kafka Issues

```bash
# Check Kafka health
docker-compose -f docker-compose.prod.yml logs kafka

# Restart Kafka and Zookeeper
docker-compose -f docker-compose.prod.yml restart zookeeper kafka

# Wait for Kafka to be ready
docker-compose -f docker-compose.prod.yml logs -f kafka | grep "started"
```

### Out of Memory

```bash
# Check memory usage
free -h
docker stats

# Restart services one by one
docker-compose -f docker-compose.prod.yml restart ingestion_service
docker-compose -f docker-compose.prod.yml restart speed_layer
docker-compose -f docker-compose.prod.yml restart batch_layer
```

### SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in nginx/ssl/fullchain.pem -text -noout

# Renew Let's Encrypt certificate
sudo certbot renew

# Copy renewed certificates
sudo cp /etc/letsencrypt/live/your-domain.com/*.pem nginx/ssl/
docker-compose -f docker-compose.prod.yml restart nginx
```

---

## 🔐 Security Best Practices

1. **Use strong passwords** for database and API keys
2. **Enable firewall** (UFW) with minimal open ports
3. **Keep system updated:** `sudo apt update && sudo apt upgrade`
4. **Use SSL/HTTPS** for production
5. **Disable root SSH login**
6. **Use SSH keys** instead of passwords
7. **Regular backups** of database
8. **Monitor logs** for suspicious activity
9. **Keep Docker updated**
10. **Use environment variables** for secrets

---

## 📞 Support

For issues:
- Check logs: `docker-compose -f docker-compose.prod.yml logs`
- Review documentation in `docs/`
- Create GitHub issue

---

**Last Updated:** 2025-12-02  
**Version:** 2.0.0
