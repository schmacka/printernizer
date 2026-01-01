# Printernizer Architecture & Context

## Project Overview

**Printernizer** is a professional 3D print management system for managing Bambu Lab A1 and Prusa Core One printers. It provides automated job tracking, file downloads, and business reporting capabilities.

**Primary Use Case**: Enterprise-grade 3D printer fleet management with automated job monitoring, file organization, and business analytics.

**Language**: English (for logging, GUI, and reports)
**Timezone**: Configurable (defaults to system timezone)
**Business Focus**: Distinguish between business orders and private models

## Core Components

- **Printer APIs**: 
  - Bambu Lab MQTT integration via bambulabs-api library
  - Prusa PrusaLink HTTP API integration
- **Job Monitoring**: Real-time tracking with 30-second polling intervals
- **File Management**: Automatic downloads and organization system
- **Database**: SQLite with job-based architecture
- **Web Interface**: Primary access method (desktop GUI planned for later)

## Technology Stack

- **Backend**: Python 3.11+, FastAPI
- **Database**: SQLite for job storage and tracking
- **MQTT Client**: bambulabs-api library for Bambu Lab integration
- **HTTP Client**: Standard library or requests for Prusa API
- **3D Processing**: Trimesh, numpy-stl, matplotlib for preview features
- **Frontend**: Modern web standards with WebSocket connectivity

## API Integration Specifications

### Bambu Lab A1
- **Protocol**: MQTT over bambulabs-api library
- **Authentication**: IP + Access Code + Serial Number
- **Features**: Real-time status, job progress, temperature monitoring
- **Polling**: Event-driven via MQTT callbacks

### Prusa Core One  
- **Protocol**: HTTP REST API via PrusaLink
- **Authentication**: API Key
- **Features**: Job status, file downloads, print history
- **Polling**: HTTP requests every 30 seconds

## Project Structure

Key directories:
- `/src/` - Primary application code (EDIT HERE)
- `/frontend/` - Primary web interface (EDIT HERE)
- `/migrations/` - Database migrations
- `/docs/` - Documentation
- `/tests/` - Test suite

**Note**: HA add-on is in separate [printernizer-ha](https://github.com/schmacka/printernizer-ha) repo (auto-synced via GitHub Actions).

Important files:
- `assets/database/schema.sql` - SQLite schema (formerly `database_schema.sql`)
- `requirements.txt` - Python dependencies
- `.env` - Configuration (use `.env.example` as template)
