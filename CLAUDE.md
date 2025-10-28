# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Printernizer** is a professional 3D print management system designed for managing Bambu Lab A1 and Prusa Core One printers. It provides automated job tracking, file downloads, and business reporting capabilities for 3D printing operations.

**Primary Use Case**: Enterprise-grade 3D printer fleet management with automated job monitoring, file organization, and business analytics while maintaining simplicity for individual users.

**Language**: English (for logging, GUI, and reports)
**Timezone**: Configurable (defaults to system timezone)
**Business Focus**: Distinguish between business orders and private models

## Architecture Overview

### Core Components
- **Printer APIs**: 
  - Bambu Lab MQTT integration via bambulabs-api library
  - Prusa PrusaLink HTTP API integration
- **Job Monitoring**: Real-time tracking with 30-second polling intervals
- **File Management**: Automatic downloads and organization system
- **Database**: SQLite with job-based architecture
- **Web Interface**: Primary access method (desktop GUI planned for later)

### API Integration Specifications

#### Bambu Lab A1
- **Protocol**: MQTT over bambulabs-api library
- **Authentication**: IP + Access Code + Serial Number
- **Features**: Real-time status, job progress, temperature monitoring
- **Polling**: Event-driven via MQTT callbacks

#### Prusa Core One  
- **Protocol**: HTTP REST API via PrusaLink
- **Authentication**: API Key
- **Features**: Job status, file downloads, print history
- **Polling**: HTTP requests every 30 seconds

## Core Feature Requirements

### Job Monitoring System
- Real-time job tracking for multiple printers
- 30-second polling intervals for status updates
- Job-based database architecture using SQLite

### File Management (Drucker-Dateien System)
- **Automatic printer detection** of saved files on Bambu Lab & Prusa
- **One-click downloads** directly from GUI
- **Combined file listing** showing local and printer files in unified view
- **Smart download organization** by printer/date with secure file naming
- **Status tracking**: Available 📁, Downloaded ✓, Local 💾
- **Filter options** by printer and download status
- **Download statistics** and cleanup management

### Business & Export Features
- **Excel/CSV export** for accounting software integration
- **Cost calculations** including material and power costs
- **Material consumption tracking** based on job data
- **Business statistics** for commercial operations

### 3D Preview System (Planned)
- **Multi-format support**: STL/3MF/G-Code with automatic format detection
- **Click-to-preview** directly from print list
- **Multiple rendering backends**: Trimesh, numpy-stl, matplotlib
- **Modal view** for detailed examination
- **Intelligent caching** for performance optimization

## Development Guidelines

### Business Logic Requirements
- **Business Integration**: Flexible workflow and reporting capabilities
- **Material Tracking**: Comprehensive material usage monitoring
- **Localization**: Configurable timezone and locale settings
- **Export Compatibility**: Excel/CSV formats for standard accounting software

### Technology Stack Expectations
- **Database**: SQLite for job storage and tracking
- **Web Framework**: To be determined (Flask/FastAPI recommended)
- **MQTT Client**: bambulabs-api library for Bambu Lab integration
- **HTTP Client**: Standard library or requests for Prusa API
- **3D Processing**: Trimesh, numpy-stl, matplotlib for preview features

### File Organization
- Downloads organized by printer and date
- Secure file naming conventions
- Local file management with status tracking
- Flexible file organization and management

### API Routing Standards

**CRITICAL: Trailing Slash Policy**

This application has `redirect_slashes=False` configured in FastAPI to prevent conflicts with StaticFiles mounted at the root path. This setting requires strict adherence to routing patterns.

**Mandatory Routing Pattern:**
- **NEVER use `"/"` as the endpoint path** in router decorators
- **ALWAYS use `""` (empty string)** for root resource endpoints
- This ensures API routes work WITHOUT trailing slashes (standard REST behavior)

**Why This Matters:**
- FastAPI combines router prefix + endpoint path to create final routes
- With `redirect_slashes=False`, routes must match exactly (no automatic redirects)
- Using `"/"` creates routes ending in `/`, requiring trailing slash in client URLs
- Using `""` creates routes without `/`, matching standard HTTP client behavior
- **This issue has occurred 3+ times** - strict adherence prevents recurrence

**Correct Patterns:**

```python
# ✅ CORRECT - Root resource operations (list, create)
@router.get("")          # GET /api/v1/printers (no trailing slash)
@router.post("")         # POST /api/v1/printers (no trailing slash)

# ✅ CORRECT - Specific resource operations
@router.get("/{id}")     # GET /api/v1/printers/abc123
@router.put("/{id}")     # UPDATE /api/v1/printers/abc123
@router.delete("/{id}")  # DELETE /api/v1/printers/abc123

# ✅ CORRECT - Nested operations
@router.post("/{id}/connect")    # POST /api/v1/printers/abc123/connect
@router.get("/health")            # GET /api/v1/health
```

```python
# ❌ INCORRECT - Will cause 405 errors when accessed without trailing slash
@router.get("/")         # Creates route /api/v1/printers/ (WITH slash)
@router.post("/")        # Requires POST /api/v1/printers/ (WITH slash)
                         # Standard clients send without slash → 405 ERROR
```

**Testing Requirements:**
- All API endpoints MUST be tested WITHOUT trailing slash
- Integration tests should verify POST/PUT/DELETE work without trailing slash
- Any new router must follow the empty string `""` pattern for root endpoints

**Git History Reference:**
- Previous fixes: commits ddf53ea, 34680e6, branch fix/disable-redirect-slashes
- Root cause: StaticFiles at "/" + redirect_slashes=False + "/" endpoints
- This is a permanent architectural constraint - do not attempt to re-enable redirect_slashes

## Deployment Architecture

Printernizer supports **three independent deployment methods**. Each method uses the same core codebase but has deployment-specific configurations:

### 1. Python Standalone
- **Location**: Root directory (`run.sh`, `run.bat`)
- **Use Case**: Development, testing, local installation
- **Setup**: Direct Python execution
- **Configuration**: `.env` file
- **Data Storage**: Local directories (`data/`, `printer-files/`)

### 2. Docker Standalone
- **Location**: `docker/` directory
- **Use Case**: Production servers, NAS systems
- **Setup**: `docker-compose up -d`
- **Configuration**: Environment variables in `docker-compose.yml`
- **Data Storage**: Docker volumes (persistent)
- **Files**:
  - `Dockerfile` - Multi-stage build with Python 3.11
  - `docker-compose.yml` - Full orchestration
  - `entrypoint.sh` - Container initialization
  - `README.md` - Docker deployment guide

### 3. Home Assistant Add-on
- **Location**: `printernizer/` directory (Add-on name)
- **Use Case**: Home Assistant users, 24/7 integration
- **Setup**: Install via HA Add-on Store (repository.json)
- **Configuration**: HA UI (`options.json`)
- **Data Storage**: `/data/printernizer/` (HA persistent storage)
- **Files**:
  - `Dockerfile` - Alpine-based with `ARG BUILD_FROM`
  - `config.yaml` - Add-on metadata and schema
  - `build.yaml` - Multi-architecture builds
  - `run.sh` - HA-specific startup with bashio
  - `README.md` - Add-on store description
  - `DOCS.md` - Detailed user documentation
  - `CHANGELOG.md` - Add-on version history
- **Repository**: `repository.json` in root for HA Add-on Store discovery

### Deployment Mode Detection

The application automatically detects deployment mode via environment variables:
- `DEPLOYMENT_MODE=standalone` - Default Python mode
- `DEPLOYMENT_MODE=docker` - Docker standalone
- `DEPLOYMENT_MODE=homeassistant` - HA Add-on mode
- `HA_INGRESS=true` - Enables Ingress security (HA only)

### Shared Codebase

**IMPORTANT**: All three deployment methods share:
- `src/` - Application code (unchanged for all modes)
- `frontend/` - Web interface (unchanged for all modes)
- `requirements.txt` - Python dependencies
- Core business logic and features

**Deployment-specific**:
- Startup scripts (`run.sh` vs `entrypoint.sh` vs HA `run.sh`)
- Configuration parsing (`.env` vs env vars vs `options.json`)
- Path mapping (local vs volumes vs `/data`)
- Security (direct vs Docker vs Ingress)

## Future Enhancements
- **MQTT discovery** for Home Assistant sensors (printer status, job completion)
- **HA automations** integration with triggers and actions
- **Kubernetes deployment** for enterprise scale-out
- **Desktop GUI application** as alternative to web interface
- **Advanced 3D preview capabilities** with multiple rendering options

## Development Notes
- Focus on enterprise features while maintaining simplicity
- Consider standard business practices and configurable accounting requirements
- **Remember to increase version number** accordingly when branches get integrated into master
- **Always create a new branch** when you develop a new feature or major bugfix
- **Keep deployment methods independent** - changes should not break any deployment option
- **Test all three deployment methods** before merging to master