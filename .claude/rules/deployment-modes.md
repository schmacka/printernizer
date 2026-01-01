# Deployment Modes

Printernizer supports four deployment methods.

## 1. Python Standalone (Development)

Run directly as a Python application:

```bash
pip install -r requirements.txt
python src/main.py
```

**Use for**: Local development and testing.

## 2. Docker Standalone (Testing)

Use `development` branch for testing builds:

```bash
docker pull ghcr.io/schmacka/printernizer:development
docker-compose up -d
```

**Use for**: Integration testing before production.

## 3. Home Assistant Add-on (Production)

Install via Home Assistant Add-on Store.

- Code lives in separate [printernizer-ha](https://github.com/schmacka/printernizer-ha) repository
- Automatically synced from this repository via GitHub Actions
- Auto-updates from tagged releases

**Use for**: Production deployments with Home Assistant.

## 4. Raspberry Pi Deployment (Production Alternative)

Quick deployment script:

```bash
# Production (master branch)
curl -fsSL https://raw.githubusercontent.com/schmacka/printernizer/master/scripts/pi-deployment/pi-setup.sh | bash
```

**Use for**: Standalone Raspberry Pi deployments.

## Deployment Mode Detection

The application detects its deployment mode:

```python
DEPLOYMENT_MODE = os.getenv('DEPLOYMENT_MODE', 'standalone')

# Home Assistant Ingress detection
if os.getenv("HA_INGRESS") == "true":
    # Special HA handling
```

## Branch → Deployment Mapping

| Branch | Docker Tag | HA Add-on |
|--------|------------|-----------|
| `development` | `development` | Testing only |
| `master` | `latest`, `vX.Y.Z` | Production |
