# Printernizer Deployment Architecture

## Deployment Methods

Printernizer supports **three independent deployment methods**. Each uses the same core codebase but has deployment-specific configurations.

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
- **Use Case**: Production deployments, containerized environments
- **Setup**: `docker-compose up -d`
- **Configuration**: Environment variables or `.env`
- **Data Storage**: Docker volumes
- **Files**:
  - `docker/Dockerfile` - Container definition
  - `docker/docker-compose.yml` - Service orchestration
  - `docker/.env.example` - Configuration template

### 3. Home Assistant Add-on

- **Location**: `printernizer/` directory (Add-on name)
- **Use Case**: Home Assistant users, 24/7 integration
- **Setup**: Install via HA Add-on Store (repository.json)
- **Configuration**: HA UI (`options.json`)
- **Data Storage**: `/data/printernizer/` (HA persistent storage)
- **Files**:
  - `printernizer/Dockerfile` - Alpine-based with `ARG BUILD_FROM`
  - `printernizer/config.yaml` - Add-on metadata and schema
  - `printernizer/build.yaml` - Multi-architecture builds
  - `printernizer/run.sh` - HA-specific startup with bashio
  - `printernizer/README.md` - Add-on store description
  - `printernizer/DOCS.md` - Detailed user documentation
  - `printernizer/CHANGELOG.md` - Add-on version history
- **Repository**: `repository.json` in root for HA Add-on Store discovery

## Deployment Mode Detection

The application detects its deployment mode via environment variables:

```python
DEPLOYMENT_MODE = os.getenv('DEPLOYMENT_MODE', 'standalone')
# Options: 'standalone', 'docker', 'homeassistant'

if DEPLOYMENT_MODE == 'homeassistant':
    HA_INGRESS = os.getenv('HA_INGRESS', 'false').lower() == 'true'
    # Use /data/ for storage, parse options.json
elif DEPLOYMENT_MODE == 'docker':
    # Use volumes, read env vars
else:
    # Use local data/, read .env
```

## Shared Codebase Architecture

**IMPORTANT**: All three deployment methods share the same codebase with automated synchronization.

**Single Source of Truth**:
- `/src/` - Primary application code (EDIT HERE)
- `/frontend/` - Primary web interface (EDIT HERE)
- `requirements.txt` - Python dependencies
- Core business logic and features

**Automated Sync to Home Assistant Add-on**:
- `/printernizer/src/` - Auto-synced copy (DO NOT EDIT DIRECTLY)
- `/printernizer/frontend/` - Auto-synced copy (DO NOT EDIT DIRECTLY)
- Synchronization happens automatically via:
  1. **Git pre-commit hook** - Auto-syncs when you commit changes
  2. **GitHub Actions CI/CD** - Validates sync on push to master
  3. **Manual script** - Run sync script when needed

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
