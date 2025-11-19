# Raspberry Pi Deployment Guide

Complete guide for deploying Printernizer to Raspberry Pi 4 with automated rollback capabilities.

## Quick Start

### 1. Prepare Raspberry Pi (One-Time Setup)

SSH to your Pi and run:
```bash
curl -fsSL https://raw.githubusercontent.com/schmacka/printernizer/main/scripts/pi-deployment/pi-setup.sh | bash
```

Or manually copy and run `scripts/pi-deployment/pi-setup.sh` from this repository.

### 2. Deploy from Windows

```powershell
# Navigate to project directory
cd C:\Users\sebas\OneDrive\porcus3D\printernizer

# Deploy to Pi
.\scripts\pi-deployment\deploy-to-pi.ps1 -PiHost 192.168.1.100

# With force flag (skip health check failures)
.\scripts\pi-deployment\deploy-to-pi.ps1 -PiHost 192.168.1.100 -Force

# Skip backup (not recommended)
.\scripts\pi-deployment\deploy-to-pi.ps1 -PiHost 192.168.1.100 -SkipBackup
```

## Deployment Process

The deployment script performs these steps automatically:

1. **Pre-Deployment Validation**
   - Test SSH connection
   - Verify Docker installation
   - Check disk space (requires 2GB minimum)
   - Validate local project files

2. **Backup Current Deployment**
   - Create timestamped backup on Pi
   - Download backup copy to local machine
   - Keep last 10 backups on Pi

3. **Deploy New Version**
   - Copy source files to Pi
   - Preserve data and configuration
   - Create deployment metadata

4. **Start Container**
   - Pull latest Docker images
   - Build application container
   - Start with docker-compose

5. **Health Checks**
   - Wait for application startup (30s timeout)
   - Verify API health endpoint (`/api/v1/health`)
   - Check container status

6. **Automatic Rollback** (if failure)
   - Restore previous backup
   - Restart container
   - Verify rollback success

## Manual Operations

### Monitor Status

```powershell
# Quick status check
.\scripts\pi-deployment\monitor-pi.ps1 -PiHost 192.168.1.100

# System information
.\scripts\pi-deployment\monitor-pi.ps1 -PiHost 192.168.1.100 -SystemInfo

# Follow logs in real-time
.\scripts\pi-deployment\monitor-pi.ps1 -PiHost 192.168.1.100 -Follow
```

### Manual Rollback

```powershell
# Interactive backup selection
.\scripts\pi-deployment\rollback-pi.ps1 -PiHost 192.168.1.100

# Rollback to specific backup
.\scripts\pi-deployment\rollback-pi.ps1 -PiHost 192.168.1.100 -BackupId 20241113_143022
```

### Direct SSH Operations

```bash
# SSH to Pi
ssh pi@192.168.1.100

# View status
cd ~/printernizer
docker-compose ps

# View logs
docker-compose logs -f printernizer

# Restart container
docker-compose restart

# Stop container
docker-compose down

# Start container
docker-compose up -d

# Rebuild and restart
docker-compose up -d --build
```

## Backup Management

### Automatic Backups

Backups are created automatically:
- Before each deployment
- Before manual rollback (pre-rollback backup)

Location: `/home/pi/printernizer_backups/`

### Manual Backup

```bash
# On Pi
cd ~/printernizer
bash << 'EOF'
BACKUP_DIR="/home/pi/printernizer_backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"
docker-compose stop
tar -czf "$BACKUP_DIR/manual_backup_$DATE.tar.gz" data/ config/ docker-compose.yml .env
docker-compose start
echo "Backup created: $BACKUP_DIR/manual_backup_$DATE.tar.gz"
EOF
```

### Backup Retention

- Last 10 backups kept on Pi automatically
- Local backup copies in `.\deployments\backup_*\` on Windows
- Backups include: database, configuration, uploaded files, environment settings

## Deployment History

All deployments are tracked in `.\deployments\history.json`:

```json
{
  "deployment_id": "20241113_143022",
  "timestamp": "2024-11-13T14:30:22+01:00",
  "target": "pi@192.168.1.100",
  "success": true,
  "duration_seconds": 45.2,
  "rolled_back": false,
  "git_commit": "abc123...",
  "deployed_by": "sebas"
}
```

## Network Configuration

### Static IP (Recommended)

On the Pi:
```bash
sudo nano /etc/dhcpcd.conf

# Add:
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1

sudo systemctl restart dhcpcd
```

### Port Forwarding

To access from internet:
1. Forward port 8000 on router to Pi IP
2. Use DynamicDNS for changing external IP
3. Consider reverse proxy with SSL (Nginx)

### HTTPS Setup (Optional)

```bash
# On Pi - Install Nginx
sudo apt install nginx certbot python3-certbot-nginx

# Configure reverse proxy
sudo nano /etc/nginx/sites-available/printernizer

# Add:
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/printernizer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

## Troubleshooting

### Deployment Fails

1. Check SSH connection: `ssh pi@192.168.1.100`
2. Verify Docker: `ssh pi@192.168.1.100 "docker --version"`
3. Check disk space: `ssh pi@192.168.1.100 "df -h"`
4. View Pi logs: `.\scripts\pi-deployment\monitor-pi.ps1 -PiHost 192.168.1.100`

### Container Won't Start

```bash
# On Pi
cd ~/printernizer

# Check container logs
docker-compose logs

# Check for port conflicts
sudo netstat -tlnp | grep 8000

# Verify file permissions
ls -la data/

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Health Check Fails

```bash
# Manual health check
curl http://localhost:8000/api/v1/health

# Check if port is open
nc -zv localhost 8000

# View application logs
docker-compose logs -f printernizer
```

### Rollback Needed

```powershell
# Automatic during failed deployment
# Or manual:
.\scripts\pi-deployment\rollback-pi.ps1 -PiHost 192.168.1.100
```

## Performance Optimization

### Resource Limits

Edit `docker-compose.yml` on Pi:
```yaml
deploy:
  resources:
    limits:
      memory: 512M    # Adjust based on Pi RAM
    reservations:
      memory: 256M
```

### Database Optimization

```bash
# On Pi - Vacuum database monthly
sqlite3 ~/printernizer/data/database/printernizer.db "VACUUM;"

# Add to crontab
crontab -e
# Add: 0 2 1 * * sqlite3 ~/printernizer/data/database/printernizer.db "VACUUM;"
```

### Log Rotation

```bash
# Install logrotate config
sudo tee /etc/logrotate.d/printernizer << 'EOF'
/home/pi/printernizer/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
EOF
```

## Maintenance

### Weekly Tasks
- Check deployment history for failures
- Review disk usage: `.\scripts\pi-deployment\monitor-pi.ps1 -PiHost 192.168.1.100`
- Verify backups exist

### Monthly Tasks
- Update Pi system: `ssh pi@192.168.1.100 "sudo apt update && sudo apt upgrade -y"`
- Clean old Docker images: `ssh pi@192.168.1.100 "docker system prune -a"`
- Vacuum database (see above)
- Review and clean old backups

### Updates

```powershell
# Update to latest version
git pull
.\scripts\pi-deployment\deploy-to-pi.ps1 -PiHost 192.168.1.100

# Rollback if issues
.\scripts\pi-deployment\rollback-pi.ps1 -PiHost 192.168.1.100
```

## Security Best Practices

1. **Change default Pi password**: `passwd`
2. **Use SSH keys only**: Disable password auth in `/etc/ssh/sshd_config`
3. **Keep system updated**: Regular `apt upgrade`
4. **Enable firewall**: Already done by setup script
5. **Use strong passwords** in Printernizer web UI
6. **Consider VPN** instead of exposing to internet
7. **Regular backups**: Automated by deployment script

## Architecture Notes

- FastAPI backend serves both API (`/api/v1/*`) and static frontend
- Health endpoint: `/api/v1/health` (note: no trailing slash)
- WebSocket for real-time updates: `/ws`
- All printer integrations via service layer pattern
- SQLite database with automatic migrations
- Event-driven architecture for cross-service communication

## Support

- Deployment issues: Check `.\deployments\history.json`
- Application logs: `.\scripts\pi-deployment\monitor-pi.ps1 -PiHost <ip> -Follow`
- System status: `.\scripts\pi-deployment\monitor-pi.ps1 -PiHost <ip> -SystemInfo`
- Manual intervention: SSH and use docker-compose commands
- API errors: Check `/api/v1/health` for service status
