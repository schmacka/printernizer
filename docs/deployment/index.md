# Deployment

Printernizer offers multiple deployment options to fit different use cases, from local development to production environments.

## Deployment Methods

### Python Standalone

**Best for:** Development, testing, local installation

**Setup time:** 5 minutes

Direct Python installation for maximum flexibility and control. Perfect for developers and users who want to run Printernizer without containers.

**[View Python Deployment Guide →](#python-standalone)**

### Docker Standalone

**Best for:** Production servers, NAS systems, isolated environments

**Setup time:** 5 minutes

Containerized deployment with Docker Compose for easy management and portability.

**[View Docker Deployment Guide →](docker.md)**

### Home Assistant Add-on

**Best for:** Home Assistant users, 24/7 operation, smart home integration

**Setup time:** 10 minutes

Seamless integration with Home Assistant for centralized management alongside your smart home.

**[View Home Assistant Guide →](home-assistant.md)**

### Raspberry Pi

**Best for:** Dedicated hardware, edge deployment

**Setup time:** 10 minutes

Automated setup script for quick deployment on Raspberry Pi devices.

**[View Raspberry Pi Guide →](raspberry-pi.md)**

## Python Standalone

### Quick Start

```bash
# 1. Create virtual environment (recommended)
python -m venv venv

# Windows:
venv\\Scripts\\activate
# Linux/Mac:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment (optional)
cp .env.example .env
# Edit .env with your settings

# 4. Start the application
# Windows:
run.bat
# Linux/Mac:
./run.sh

# Access the application
# Web Interface: http://localhost:8000
# API Documentation: http://localhost:8000/docs
```

### Requirements

- Python 3.8 or higher
- 100MB disk space
- Network access to printers

### Configuration

Create a `.env` file or set environment variables:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_PATH=./data/printernizer.db

# Logging
LOG_LEVEL=INFO
```

See [Settings Reference](../user-guide/SETTINGS_REFERENCE.md) for all options.

## Production Considerations

### Security
- Use HTTPS in production (configure reverse proxy)
- Implement firewall rules
- Keep dependencies updated

### Performance
- Allocate adequate resources (2GB RAM recommended)
- Use SSD for database storage
- Monitor system resources

### Backup
- Regular database backups
- Configuration file backups
- File downloads backup (if storing locally)

### Monitoring
- Health check endpoint: `/api/v1/health`
- Prometheus metrics: `/metrics`
- Structured logging

## Migration

### From Development to Production
1. Export database
2. Copy configuration files
3. Set up production environment
4. Import database
5. Verify connections

### Between Deployment Methods
All deployment methods use the same database schema and configuration format, making migrations straightforward.

## Troubleshooting

Common deployment issues:

- **Can't connect to printers** → Check network configuration
- **Database errors** → Verify file permissions
- **Port conflicts** → Change PORT in .env
- **Performance issues** → Increase resource allocation

See [Troubleshooting](../user-guide/troubleshooting.md) for more help.

## Advanced Topics

- **[Production Deployment](production.md)** - Best practices for production
- **[Docker Guide](docker.md)** - Advanced Docker configuration
- **[Raspberry Pi](raspberry-pi.md)** - Pi-specific optimizations

## Need Help?

- Check the [User Guide](../user-guide/index.md)
- Review [Architecture](../architecture/index.md)
- Visit [GitHub Issues](https://github.com/schmacka/printernizer/issues)
