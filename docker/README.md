# Printernizer - Docker Standalone Deployment

This directory contains everything needed to run Printernizer as a standalone Docker container.

## 🚀 Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- Network access to your 3D printers

### Start Printernizer

**Option 1: Using Docker Compose (Recommended)**
```bash
# From project root
cd docker
docker-compose up -d
```

**Option 2: Using Build Script**
```bash
# From project root
./build-docker.sh
docker run -d -p 8000:8000 --name printernizer printernizer:latest
```

**Option 3: Manual Docker Build**
```bash
# IMPORTANT: Build from repository root with correct context
cd /path/to/printernizer  # Must be repo root
docker build -f docker/Dockerfile -t printernizer:latest .
docker run -d -p 8000:8000 --name printernizer printernizer:latest
```

⚠️ **Common Error**: Do NOT build from inside the `docker/` directory like this:
```bash
cd docker
docker build -t printernizer .  # ❌ WRONG - Will fail with "entrypoint.sh not found"
```

Access the application:
- **Web Interface:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/v1/health

### Stop Printernizer

```bash
docker-compose down
```

## 📋 Configuration

### Environment Variables

Edit `docker-compose.yml` to customize configuration:

```yaml
environment:
  # Application settings
  - ENVIRONMENT=production
  - LOG_LEVEL=info

  # German business settings
  - TIMEZONE=Europe/Berlin
  - CURRENCY=EUR
  - VAT_RATE=0.19
  - BUSINESS_LOCATION=Your Location

  # CORS (add your domains for remote access)
  - CORS_ORIGINS=http://localhost:8000,http://your-domain.com
```

### Printer Configuration

Add printers via the web interface at http://localhost:8000 or by editing the configuration through the UI.

**Bambu Lab A1:**
- Name: Your printer name
- Type: bambu_lab
- IP Address: 192.168.1.100
- Access Code: 8-digit code from printer display
- Serial Number: Found on printer

**Prusa Core One:**
- Name: Your printer name
- Type: prusa
- IP Address: 192.168.1.101
- API Key: Generate in PrusaLink settings

## 🗄️ Data Persistence

All data is stored in Docker volumes:

```bash
# View volumes
docker volume ls | grep printernizer

# Backup data
docker-compose down
docker run --rm -v printernizer_printernizer-data:/data -v $(pwd):/backup alpine tar czf /backup/printernizer-backup.tar.gz /data

# Restore data
docker run --rm -v printernizer_printernizer-data:/data -v $(pwd):/backup alpine tar xzf /backup/printernizer-backup.tar.gz -C /
```

## 🔧 Advanced Configuration

### Custom Port

Change the external port in `docker-compose.yml`:

```yaml
ports:
  - "3000:8000"  # Access on port 3000
```

### Resource Limits

Uncomment and adjust resource limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### Bind Mounts (Development)

For development with live code changes:

```yaml
volumes:
  - ../src:/app/src:ro
  - ../frontend:/app/frontend:ro
  - printernizer-data:/app/data
```

## 📊 Monitoring

### View Logs

```bash
# All logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs -f printernizer
```

### Container Status

```bash
# Check running containers
docker-compose ps

# Health check status
docker inspect printernizer | jq '.[0].State.Health'
```

### Access Container Shell

```bash
docker-compose exec printernizer bash
```

## 🔍 Troubleshooting

### "exec /app/entrypoint.sh: no such file or directory"

This error occurs when the Docker image was built with an incorrect build context.

**Solution:**
```bash
# Stop and remove any existing containers
docker-compose down
docker rm -f printernizer 2>/dev/null || true

# Rebuild with correct context using docker-compose
cd docker
docker-compose build --no-cache
docker-compose up -d

# OR use the build script from repo root
cd ..
./build-docker.sh
```

**Root Cause**: The Dockerfile requires the repository root as the build context because it needs to access `src/`, `frontend/`, `assets/database/schema.sql`, and `docker/entrypoint.sh`. Building from inside the `docker/` directory will fail.

### Container Won't Start

```bash
# Check logs
docker-compose logs

# Rebuild container
docker-compose build --no-cache
docker-compose up -d
```

### Database Issues

```bash
# Reset database (WARNING: deletes all data!)
docker volume rm printernizer_printernizer-data
docker-compose up -d
```

### Network Connectivity

```bash
# Test from container
docker-compose exec printernizer ping 192.168.1.100

# Check container network
docker network inspect printernizer_printernizer-network
```

### Permission Issues

```bash
# Fix volume permissions
docker-compose down
docker volume rm printernizer_printernizer-data
docker-compose up -d
```

## 🚀 Production Deployment

### Reverse Proxy (Nginx)

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name printernizer.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL/TLS with Let's Encrypt

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d printernizer.yourdomain.com

# Auto-renewal is configured automatically
```

### Auto-Updates with Watchtower

```bash
# Add to docker-compose.yml
watchtower:
  image: containrrr/watchtower
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
  command: --interval 86400 printernizer
```

## 📈 Performance Optimization

### Database Optimization

```bash
# Vacuum database periodically
docker-compose exec printernizer sqlite3 /app/data/printernizer.db "VACUUM;"
```

### Log Rotation

Configure Docker logging driver:

```yaml
services:
  printernizer:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 🔐 Security

### Production Checklist

- [ ] Change default CORS_ORIGINS
- [ ] Use reverse proxy with SSL/TLS
- [ ] Regular backups of data volume
- [ ] Monitor logs for suspicious activity
- [ ] Keep Docker and images updated
- [ ] Use strong printer access codes/API keys

## 📚 Additional Resources

- **Main Documentation:** [../README.md](../README.md)
- **API Documentation:** http://localhost:8000/docs
- **Issue Tracker:** https://github.com/schmacka/printernizer/issues

## 🆘 Support

If you encounter issues:

1. Check the logs: `docker-compose logs`
2. Verify network connectivity to printers
3. Check the troubleshooting section above
4. Report issues on GitHub

---

**Printernizer Docker Standalone** - Professional 3D Printer Management
