# Printernizer Deployment Architecture

## Branching Strategy and Deployment

Printernizer uses a **two-branch model** that maps to different deployment targets:

- **`development`** branch → Docker testing deployments
- **`master`** branch → Production deployments (Home Assistant, Raspberry Pi)

## Deployment Methods

Printernizer supports **four independent deployment methods**. Each uses the same core codebase but has deployment-specific configurations.

### 1. Python Standalone

- **Location**: Root directory
- **Use Case**: Development, testing, small installations
- **Setup**: `python -m venv venv && pip install -r requirements.txt`
- **Configuration**: `.env` file
- **Data Storage**: `data/` directory
- **Files**:
  - `run.sh` / `run.bat` - Startup scripts
  - `.env` - Environment configuration
  - `requirements.txt` - Dependencies

### 2. Docker Standalone

- **Location**: Root directory with `docker/` subdirectory
- **Use Case**: Testing (development branch), production deployments (master branch)
- **Setup**: `docker-compose up -d`
- **Configuration**: Environment variables or `.env`
- **Data Storage**: Docker volumes
- **Branch Strategy**:
  - Development: `docker pull ghcr.io/schmacka/printernizer:development`
  - Production: `docker pull ghcr.io/schmacka/printernizer:latest` (from master)
- **Files**:
  - `docker/Dockerfile` - Container definition
  - `docker/docker-compose.yml` - Service orchestration
  - `docker/.env.example` - Configuration template

### 3. Raspberry Pi Deployment

- **Location**: Can be installed anywhere on Pi
- **Use Case**: Dedicated Raspberry Pi server for production
- **Setup**: One-line install script
  ```bash
  # Production (master branch - recommended)
  curl -fsSL https://raw.githubusercontent.com/schmacka/printernizer/master/scripts/pi-deployment/pi-setup.sh | bash

  # Testing (development branch - advanced users)
  curl -fsSL https://raw.githubusercontent.com/schmacka/printernizer/development/scripts/pi-deployment/pi-setup.sh | bash
  ```
- **Configuration**: Interactive prompts during setup + `.env` file
- **Data Storage**: Local filesystem in install directory
- **Features**:
  - Automatic dependency installation
  - Systemd service setup
  - Firewall configuration
  - Auto-start on boot
- **Files**:
  - `scripts/pi-deployment/pi-setup.sh` - Main installation script
  - `scripts/pi-deployment/printernizer.service` - Systemd service template
  - Created `.env` file with user configuration

### 4. Home Assistant Add-on

- **Location**: Separate [printernizer-ha](https://github.com/schmacka/printernizer-ha) repository
- **Use Case**: Home Assistant users, 24/7 integration
- **Setup**: Install via HA Add-on Store (repository.json)
- **Configuration**: HA UI (`options.json`)
- **Data Storage**: `/data/printernizer/` (HA persistent storage)
- **Separate Repository**: HA add-on maintained in [printernizer-ha](https://github.com/schmacka/printernizer-ha)
- **Automatic Sync**: GitHub Actions syncs `src/`, `frontend/`, `migrations/` on push
- **Files** (in printernizer-ha repo):
  - `Dockerfile` - Alpine-based with `ARG BUILD_FROM`
  - `config.yaml` - Add-on metadata and schema
  - `build.yaml` - Multi-architecture builds
  - `run.sh` - HA-specific startup with bashio
  - `README.md` - Add-on store description
  - `DOCS.md` - Detailed user documentation
  - `CHANGELOG.md` - Add-on version history

## Deployment Mode Detection

The application detects its deployment mode via environment variables:

```python
DEPLOYMENT_MODE = os.getenv('DEPLOYMENT_MODE', 'standalone')
# Options: 'standalone', 'docker', 'homeassistant', 'raspberry-pi'

if DEPLOYMENT_MODE == 'homeassistant':
    HA_INGRESS = os.getenv('HA_INGRESS', 'false').lower() == 'true'
    # Use /data/ for storage, parse options.json
elif DEPLOYMENT_MODE == 'docker':
    # Use volumes, read env vars
elif DEPLOYMENT_MODE == 'raspberry-pi':
    # Use systemd service, local data/, read .env
else:
    # Standard standalone: Use local data/, read .env
```

**Note**: Raspberry Pi deployment is technically the same as standalone but with systemd service management.

## Shared Codebase Architecture

**IMPORTANT**: All four deployment methods share the same codebase with automated synchronization.

**Single Source of Truth**:
- `/src/` - Primary application code (EDIT HERE)
- `/frontend/` - Primary web interface (EDIT HERE)
- `requirements.txt` - Python dependencies
- Core business logic and features

**Branching Strategy**:
- **`development`** - Used for Docker testing deployments
- **`master`** - Used for production (HA add-on, Raspberry Pi, production Docker)

**Automated Sync to Home Assistant Add-on**:
- Home Assistant add-on maintained in separate [printernizer-ha](https://github.com/schmacka/printernizer-ha) repository
- Synchronization happens automatically via GitHub Actions workflow `sync-to-ha-repo.yml`
- Push to `master` or `development` branch triggers automatic sync
- **Version bumping**: Only happens on `master` branch (not `development`)

**Deployment-specific Files**:
- Startup scripts (`run.sh` vs `entrypoint.sh` vs HA `run.sh`)
- Configuration parsing (`.env` vs env vars vs `options.json`)
- Path mapping (local vs volumes vs `/data`)
- Security (direct vs Docker vs Ingress)

## Data Persistence

### Python Standalone
```
data/
├── printernizer.db
├── library/
├── printer-files/
├── preview-cache/
└── backups/
```

### Docker
```
volumes:
  - printernizer_data:/app/data
```

### Home Assistant
```
/data/printernizer/
├── printernizer.db
├── library/
├── printer-files/
├── preview-cache/
└── backups/
```

## Future Enhancements

- **MQTT discovery** for Home Assistant sensors (printer status, job completion)
- **HA automations** integration with triggers and actions
- **Kubernetes deployment** for enterprise scale-out
- **Desktop GUI application** as alternative to web interface
- **Advanced 3D preview capabilities** with multiple rendering options
