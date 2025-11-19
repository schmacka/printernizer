# Installation

Get Printernizer up and running in just a few minutes. Choose the deployment method that best fits your needs.

## Prerequisites

Before you begin, ensure you have:

- Network connectivity to your 3D printers
- One of the following:
  - Python 3.8 or higher (for Python standalone)
  - Docker and Docker Compose (for Docker deployment)
  - Home Assistant OS (for add-on deployment)
  - Raspberry Pi 3 or newer (for Pi deployment)

## Deployment Options

### Option 1: Python Standalone

Best for: Development, testing, local installation

**Requirements:**
- Python 3.8+
- 100MB disk space
- pip package manager

**Installation:**

```bash
# 1. Clone the repository
git clone https://github.com/schmacka/printernizer.git
cd printernizer

# 2. Create virtual environment (recommended)
python -m venv venv

# Windows:
venv\\Scripts\\activate

# Linux/Mac:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create environment file (optional)
cp .env.example .env
# Edit .env with your settings

# 5. Start the application
# Linux/Mac:
./run.sh

# Or manually (Windows/Linux/Mac):
python -m src.main
```

**Access the application:**
- Web Interface: [http://localhost:8000](http://localhost:8000)
- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

### Option 2: Docker Standalone

Best for: Production servers, NAS systems, isolated environments

**Requirements:**
- Docker Engine 20.10+
- Docker Compose 2.0+
- 2GB RAM recommended

**Installation:**

```bash
# 1. Clone the repository
git clone https://github.com/schmacka/printernizer.git
cd printernizer

# 2. Navigate to Docker folder
cd docker

# 3. Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

**Or use the build script:**

```bash
# From project root
./build-docker.sh
docker run -d -p 8000:8000 --name printernizer printernizer:latest
```

**Access the application:**
- Web Interface: [http://localhost:8000](http://localhost:8000)
- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

**Data persistence:** Data is stored in Docker volumes and persists across container restarts.

See [Docker Deployment Guide](../deployment/docker.md) for advanced configuration.

### Option 3: Home Assistant Add-on

Best for: Home Assistant users, 24/7 operation, smart home integration

**Requirements:**
- Home Assistant OS or Supervised
- Add-on Store access

**Installation:**

1. In Home Assistant: **Settings → Add-ons → Add-on Store**
2. Click **⋮** menu (top right) → **Repositories**
3. Add repository: `https://github.com/schmacka/printernizer`
4. Refresh the page
5. Find "Printernizer" in the add-on list
6. Click **INSTALL**
7. Configure the add-on (see [Configuration](configuration.md))
8. Click **START**

**Access the application:**
- From Home Assistant: Click **OPEN WEB UI**
- Direct access: `http://homeassistant.local:8000`

See [Home Assistant Deployment Guide](../deployment/home-assistant.md) for details.

### Option 4: Raspberry Pi Deployment

Best for: Dedicated hardware, edge deployment

**Requirements:**
- Raspberry Pi 3 or newer
- Raspberry Pi OS (64-bit recommended)
- Internet connection

**Quick Installation:**

```bash
# Production (master branch)
curl -fsSL https://raw.githubusercontent.com/schmacka/printernizer/master/scripts/pi-deployment/pi-setup.sh | bash

# Testing (development branch)
curl -fsSL https://raw.githubusercontent.com/schmacka/printernizer/development/scripts/pi-deployment/pi-setup.sh | bash
```

The script automatically:
- Installs dependencies
- Sets up Python environment
- Configures systemd service
- Configures firewall
- Starts Printernizer

**Access the application:**
- Web Interface: `http://raspberrypi.local:8000`
- API Documentation: `http://raspberrypi.local:8000/docs`

See [Raspberry Pi Deployment Guide](../deployment/raspberry-pi.md) for manual installation and advanced configuration.

## Verification

After installation, verify Printernizer is running:

1. **Health Check:**
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

   Expected response:
   ```json
   {
     "status": "healthy",
     "version": "2.7.0",
     "uptime": 60,
     "database": "connected"
   }
   ```

2. **Web Interface:**
   - Navigate to [http://localhost:8000](http://localhost:8000)
   - You should see the Printernizer dashboard

3. **API Documentation:**
   - Navigate to [http://localhost:8000/docs](http://localhost:8000/docs)
   - Interactive API documentation should load

## Next Steps

After installation:

1. **[Configure your printers](configuration.md)** - Add your Bambu Lab and Prusa printers
2. **[Quick Start Guide](quick-start.md)** - Learn the basics of using Printernizer
3. **[User Guide](../user-guide/index.md)** - Explore all features

## Troubleshooting

### Common Issues

**Port 8000 already in use:**
```bash
# Change port in .env file or environment variable
PORT=8001 python src/main.py
```

**Can't connect to printers:**
- Verify printers are on the same network
- Check firewall settings
- Ensure printer discovery is enabled

**Database errors:**
- Check file permissions for `data/` directory
- Verify sufficient disk space

See [Troubleshooting Guide](../user-guide/troubleshooting.md) for more help.

## Upgrading

### Python Standalone
```bash
git pull origin master
pip install -r requirements.txt --upgrade
```

### Docker
```bash
docker-compose pull
docker-compose up -d
```

### Home Assistant Add-on
Updates are automatic via the Home Assistant add-on store.

## Uninstallation

### Python Standalone
```bash
# Deactivate virtual environment
deactivate

# Remove directory
rm -rf printernizer/
```

### Docker
```bash
docker-compose down -v  # -v removes volumes
```

### Home Assistant Add-on
- Settings → Add-ons → Printernizer → **Uninstall**

## Support

Need help?

- Check [Troubleshooting](../user-guide/troubleshooting.md)
- Visit [GitHub Issues](https://github.com/schmacka/printernizer/issues)
- Review [FAQ](#faq)

## FAQ

**Q: Which deployment method should I choose?**

A:
- Development/testing → Python Standalone
- Production server → Docker
- Home Assistant user → Add-on
- Raspberry Pi → Pi deployment script

**Q: Can I migrate between deployment methods?**

A: Yes! All methods use the same database schema. Export your database and configuration, then import in the new environment.

**Q: How much disk space do I need?**

A: Minimum 100MB for the application, plus additional space for:
- Database (grows with job history)
- Downloaded files (if auto-download enabled)
- Logs (rotated automatically)

**Q: Can I run multiple instances?**

A: Yes, but ensure each instance uses a different port and separate database.
