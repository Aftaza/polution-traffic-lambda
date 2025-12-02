# Nginx SSL Directory

This directory is used to store SSL/TLS certificates for HTTPS configuration.

## Setup SSL Certificates

### Option 1: Let's Encrypt (Recommended for Production)

1. **Install Certbot on your VPS:**
```bash
sudo apt update
sudo apt install certbot
```

2. **Stop Nginx temporarily:**
```bash
docker-compose -f docker-compose.prod.yml stop nginx
```

3. **Generate certificates:**
```bash
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com
```

4. **Copy certificates to this directory:**
```bash
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./nginx/ssl/
sudo chmod 644 ./nginx/ssl/*.pem
```

5. **Update nginx.conf:**
   - Uncomment the HTTPS server block
   - Update `server_name` with your domain
   - Restart Nginx

### Option 2: Self-Signed Certificate (Testing Only)

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./nginx/ssl/privkey.pem \
  -out ./nginx/ssl/fullchain.pem \
  -subj "/C=ID/ST=Jakarta/L=Jakarta/O=Organization/CN=your-domain.com"
```

**Note:** Self-signed certificates will show security warnings in browsers.

### Option 3: Cloudflare SSL (Easiest)

If using Cloudflare:
1. Set DNS to point to your VPS IP
2. Enable Cloudflare SSL (Flexible or Full)
3. No need to configure SSL in Nginx
4. Keep HTTP (port 80) configuration only

## Certificate Renewal

Let's Encrypt certificates expire after 90 days. Set up auto-renewal:

```bash
# Test renewal
sudo certbot renew --dry-run

# Add to crontab for auto-renewal
sudo crontab -e

# Add this line to renew twice daily
0 0,12 * * * certbot renew --quiet && docker-compose -f /path/to/docker-compose.prod.yml restart nginx
```

## File Structure

```
nginx/
├── nginx.conf          # Nginx configuration
└── ssl/
    ├── fullchain.pem   # SSL certificate (public)
    ├── privkey.pem     # SSL private key
    └── README.md       # This file
```

## Security Notes

- **Never commit SSL certificates to Git**
- Keep `privkey.pem` secure (600 permissions)
- Use strong SSL protocols (TLSv1.2+)
- Enable HSTS for production
