# Configuration

Complete guide to configuring Printernizer for your environment. Configuration can be done via environment variables, `.env` file, or the web interface.

## Configuration Methods

### Method 1: Web Interface (Recommended)

The easiest way to configure Printernizer:

1. Navigate to [http://localhost:8000/settings](http://localhost:8000/settings)
2. Modify settings through the GUI
3. Changes are saved automatically
4. Restart may be required for some settings

### Method 2: Environment Variables

Set environment variables before starting Printernizer:

**Linux/Mac:**
```bash
export PORT=8001
export LOG_LEVEL=DEBUG
python src/main.py
```

**Windows (PowerShell):**
```powershell
$env:PORT="8001"
$env:LOG_LEVEL="DEBUG"
python src/main.py
```

**Windows (CMD):**
```cmd
set PORT=8001
set LOG_LEVEL=DEBUG
python src/main.py
```

### Method 3: .env File

Create a `.env` file in the project root:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_PATH=./data/printernizer.db

# Logging
LOG_LEVEL=INFO

# Features
AUTO_DOWNLOAD_ENABLED=true
BUSINESS_MODE_ENABLED=true
```

Then start Printernizer normally:
```bash
python src/main.py
```

## Complete Settings Reference

For a complete list of all available settings, see:

**[Settings Reference](../user-guide/SETTINGS_REFERENCE.md)**

## Common Configuration Scenarios

### Development Environment

```env
# .env for development
HOST=127.0.0.1
PORT=8000
LOG_LEVEL=DEBUG
DATABASE_PATH=./data/dev.db
AUTO_DOWNLOAD_ENABLED=false
```

### Production Environment

```env
# .env for production
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
DATABASE_PATH=/var/lib/printernizer/printernizer.db
AUTO_DOWNLOAD_ENABLED=true
BUSINESS_MODE_ENABLED=true
```

### Docker Deployment

Use environment variables in `docker-compose.yml`:

```yaml
services:
  printernizer:
    image: ghcr.io/schmacka/printernizer:latest
    environment:
      - PORT=8000
      - LOG_LEVEL=INFO
      - AUTO_DOWNLOAD_ENABLED=true
    ports:
      - "8000:8000"
    volumes:
      - printernizer-data:/app/data
```

### Home Assistant Add-on

Configure via the Home Assistant add-on configuration UI:

```yaml
# Add-on configuration
log_level: info
port: 8000
auto_download: true
business_mode: true
```

## Server Settings

### Network Configuration

```env
# Bind address (0.0.0.0 for all interfaces, 127.0.0.1 for localhost only)
HOST=0.0.0.0

# Port to listen on
PORT=8000

# Base URL (for reverse proxy setups)
BASE_URL=https://printernizer.example.com
```

### Performance Tuning

```env
# Worker processes (for gunicorn)
WORKERS=4

# Worker timeout
TIMEOUT=120

# Max request size (in MB)
MAX_REQUEST_SIZE=100
```

## Database Settings

```env
# Database file path
DATABASE_PATH=./data/printernizer.db

# Enable WAL mode for better concurrency
DATABASE_WAL_MODE=true

# Database connection pool size
DATABASE_POOL_SIZE=20
```

## Logging Settings

```env
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Log format: json or text
LOG_FORMAT=json

# Log file path (optional, logs to stdout by default)
LOG_FILE=/var/log/printernizer/printernizer.log

# Log rotation
LOG_MAX_BYTES=10485760  # 10MB
LOG_BACKUP_COUNT=5
```

## Feature Flags

### Auto File Download

```env
# Enable automatic file downloads after print completion
AUTO_DOWNLOAD_ENABLED=true

# Download location
DOWNLOAD_PATH=./downloads

# Delete from printer after download
DELETE_AFTER_DOWNLOAD=false
```

### Business Mode

```env
# Enable business vs. private job tracking
BUSINESS_MODE_ENABLED=true

# Default to business mode for new jobs
DEFAULT_TO_BUSINESS=false
```

### File Previews

```env
# Enable 3D file preview generation
PREVIEW_ENABLED=true

# Preview cache duration (days)
PREVIEW_CACHE_DAYS=30

# Supported formats
PREVIEW_FORMATS=stl,3mf,gcode,bgcode
```

## Printer Configuration

### Bambu Lab Settings

```env
# MQTT connection timeout (seconds)
BAMBU_MQTT_TIMEOUT=10

# MQTT keep-alive interval (seconds)
BAMBU_MQTT_KEEPALIVE=60

# Reconnection retry interval (seconds)
BAMBU_RETRY_INTERVAL=30

# Max reconnection attempts
BAMBU_MAX_RETRIES=5
```

### Prusa Settings

```env
# HTTP request timeout (seconds)
PRUSA_HTTP_TIMEOUT=30

# Status poll interval (seconds)
PRUSA_POLL_INTERVAL=5

# Max concurrent connections
PRUSA_MAX_CONNECTIONS=10
```

### Discovery Settings

```env
# Enable auto-discovery
DISCOVERY_ENABLED=true

# Discovery timeout (seconds)
DISCOVERY_TIMEOUT=30

# Discovery interval (seconds)
DISCOVERY_INTERVAL=300
```

## Security Settings

```env
# Enable HTTPS (requires reverse proxy)
FORCE_HTTPS=false

# Enable CORS
CORS_ENABLED=true

# CORS allowed origins
CORS_ORIGINS=http://localhost:3000,https://app.example.com

# API rate limiting
RATE_LIMIT_ENABLED=false
RATE_LIMIT_PER_MINUTE=60
```

## Monitoring & Metrics

```env
# Enable Prometheus metrics
METRICS_ENABLED=true

# Metrics endpoint
METRICS_PATH=/metrics

# Health check endpoint
HEALTH_CHECK_PATH=/api/v1/health
```

## Advanced Configuration

### Reverse Proxy Setup

If running behind a reverse proxy (nginx, Apache, Traefik):

```env
# Trust proxy headers
TRUST_PROXY_HEADERS=true

# Proxy header for original IP
PROXY_IP_HEADER=X-Forwarded-For

# Proxy header for original scheme
PROXY_SCHEME_HEADER=X-Forwarded-Proto
```

**nginx example:**
```nginx
location / {
    proxy_pass http://localhost:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### WebSocket Configuration

```env
# WebSocket connection timeout
WS_TIMEOUT=300

# WebSocket ping interval
WS_PING_INTERVAL=30

# Max WebSocket connections
WS_MAX_CONNECTIONS=100
```

### File Storage

```env
# File storage backend: local, s3
STORAGE_BACKEND=local

# Local storage path
STORAGE_PATH=./data/files

# S3 configuration (if using S3)
S3_BUCKET=printernizer
S3_REGION=us-east-1
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
```

## Validation

After configuring, verify settings:

### Check Health

```bash
curl http://localhost:8000/api/v1/health
```

### Verify Configuration

```bash
curl http://localhost:8000/api/v1/system/config
```

### Test Printer Connection

```bash
curl http://localhost:8000/api/v1/printers
```

## Configuration Best Practices

1. **Use .env for development** - Easy to edit and version control
2. **Use environment variables for production** - More secure, no file access needed
3. **Document custom settings** - Add comments in .env file
4. **Keep secrets secret** - Never commit API keys or passwords to git
5. **Test in development first** - Verify settings before deploying to production
6. **Use default values** - Only override what you need to change

## Configuration File Locations

- **Python Standalone:** `.env` in project root
- **Docker:** Environment variables in `docker-compose.yml`
- **Home Assistant:** Add-on configuration UI
- **Raspberry Pi:** `/opt/printernizer/.env`

## Troubleshooting Configuration

### Settings Not Taking Effect

1. Restart Printernizer after changing settings
2. Check for typos in environment variable names
3. Verify .env file is in correct location
4. Check logs for configuration errors

### Priority Order

Configuration is loaded in this order (later overrides earlier):

1. Default values (in code)
2. .env file
3. Environment variables
4. Command-line arguments (if supported)

### Debug Configuration

Enable debug logging to see loaded configuration:

```env
LOG_LEVEL=DEBUG
```

Then check logs for configuration values.

## Need Help?

- **All Settings:** [Settings Reference](../user-guide/SETTINGS_REFERENCE.md)
- **Troubleshooting:** [Troubleshooting Guide](../user-guide/troubleshooting.md)
- **Issues:** [GitHub Issues](https://github.com/schmacka/printernizer/issues)

---

**Next Steps:**
- [Quick Start Guide](quick-start.md) - Learn to use Printernizer
- [User Guide](../user-guide/index.md) - Explore all features
- [API Reference](../api-reference/index.md) - Integrate with other tools
