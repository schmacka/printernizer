# Printernizer - Professional 3D Print Management System
GitHub Copilot instructions for working effectively in this codebase.

**ALWAYS reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Overview
Printernizer is a **production-ready** professional 3D printer management system for Bambu Lab A1 and Prusa Core One printers. It provides real-time monitoring, file management ("Drucker-Dateien"), and German business compliance features for Porcus3D's 3D printing service in Kornwestheim, Germany.

## Working Effectively

### Bootstrap and Build (CRITICAL TIMING NOTES)
**NEVER CANCEL builds or long-running commands.** Build and test operations may take significant time.

#### Option 1: Python Development Setup (Recommended)
```bash
# 1. Database setup (< 1 second)
sqlite3 printernizer.db < database_schema.sql

# 2. Install dependencies (2-5 minutes - NEVER CANCEL, set timeout to 600+ seconds)
# NOTE: pip install may fail due to network issues or package conflicts
# If pip fails, document the issue and use Docker approach instead
pip install -r requirements.txt
# Common issue: magic==0.4.27 should be python-magic==0.4.27
# Workaround: pip install python-magic then pip install -r requirements.txt --ignore-installed

# 3. Start backend (starts immediately)
cd src
python main.py
# Backend runs on http://localhost:8000
# API docs available at http://localhost:8000/docs (development only)

# 4. Start frontend (starts immediately)
# In separate terminal:
cd frontend
python -m http.server 3000
# Frontend runs on http://localhost:3000
```

#### Option 2: Docker Approach (for pip install issues)
```bash
# Build may take 5-10 minutes - NEVER CANCEL, set timeout to 1200+ seconds
docker build -t printernizer-backend -f Dockerfile .

# Start with Docker Compose (2-3 minutes startup - NEVER CANCEL)
docker-compose up -d

# Access:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api/v1
# WebSocket: ws://localhost:8000/ws
```

### Testing (CRITICAL TIMING NOTES)
**NEVER CANCEL test commands.** Tests may take 5-15 minutes to complete.

```bash
# Run test suite (5-15 minutes - NEVER CANCEL, set timeout to 1800+ seconds)
python tests/test_runner.py --full-suite

# Run specific test types (1-5 minutes each - NEVER CANCEL, set timeout to 600+ seconds)
python tests/test_runner.py --type unit          # Unit tests
python tests/test_runner.py --type integration  # Integration tests
python tests/test_runner.py --type e2e          # End-to-end tests
python tests/test_runner.py --type german       # German business logic tests

# Alternative pytest approach (may have dependency issues)
python -m pytest tests/backend/ --tb=short -v
```

### Validation and Health Checks
```bash
# Validate deployment (2-5 minutes - NEVER CANCEL, set timeout to 600+ seconds)
./validate-deployment.sh

# Production readiness check (1-3 minutes - NEVER CANCEL, set timeout to 300+ seconds)
./production-readiness-check.sh

# Database validation (< 1 second)
sqlite3 printernizer.db ".tables"
```

## Key Architecture Components

### Backend Structure (`src/`)
- **Entry Point**: `src/main.py` - FastAPI application with WebSocket support
- **API Routes**: `src/api/routers/` - REST API endpoints
- **Database**: `src/database/` - SQLite with async support
- **Services**: `src/services/` - Business logic (printers, files, events)
- **Printer Integration**: `src/printers/` - Bambu Lab (MQTT) + Prusa (HTTP)
- **Models**: `src/models/` - Pydantic data models

### Frontend Structure (`frontend/`)
- **Static Files**: Pure HTML/CSS/JavaScript (no build step required)
- **Entry Point**: `frontend/index.html` - Main application
- **Configuration**: `frontend/js/config.js` - German settings (EUR, timezone)
- **Components**: Modular JS files for different features

### Database
- **Type**: SQLite with comprehensive schema
- **Setup**: `database_schema.sql` contains all tables, indexes, views, triggers
- **Features**: German business compliance, printer monitoring, file tracking
- **Performance**: Optimized with indexes and computed columns

## Common Development Tasks

### Adding New Features
1. **Backend**: Add router in `src/api/routers/`, service in `src/services/`, model in `src/models/`
2. **Frontend**: Update relevant JS files in `frontend/js/`
3. **Database**: Add migrations in `migrations/` if schema changes needed
4. **Tests**: Add tests in `tests/backend/` following existing patterns

### Working with Printers
- **Bambu Lab**: Uses MQTT protocol via `paho-mqtt`
- **Prusa**: Uses HTTP API via `aiohttp`
- **Configuration**: Stored in database `printers` table
- **Monitoring**: Real-time via WebSocket at `/ws`

### German Business Compliance
- **Language**: German UI ("Drucker", "Aufträge", "Dateien")
- **Currency**: EUR with 19% VAT calculations
- **Timezone**: Europe/Berlin
- **Compliance**: GDPR/DSGVO features built-in

### File Management ("Drucker-Dateien")
- **Status Icons**: 📁 Available, ✓ Downloaded, 💾 Local, ❌ Error
- **Download Flow**: Discover → Download → Store → Track
- **Storage**: Organized by printer and date

## CRITICAL: Known Issues and Workarounds

### Dependency Installation Issues
- **Problem**: `pip install -r requirements.txt` may fail with network timeouts or SSL errors
- **Workaround**: Use Docker approach OR install packages individually
- **Common Fix**: Replace `magic==0.4.27` with `python-magic==0.4.27`

### Testing Dependencies
- **Problem**: Some tests may fail due to missing dependencies
- **Workaround**: Install test-specific dependencies: `pip install -r requirements-test.txt`
- **Known Working**: Database tests, basic API tests

### Docker Build Issues
- **Problem**: Docker build may fail with SSL certificate errors
- **Workaround**: Use `--build-arg PIP_TRUSTED_HOST=pypi.org` or network-based fixes
- **Time**: Docker builds take 5-10 minutes when working

## Validation Scenarios (ALWAYS TEST THESE)

### After Making Backend Changes
1. **Database**: `sqlite3 test.db < database_schema.sql` (works, < 1 second)
2. **Frontend**: `cd frontend && python -m http.server 3000` (works, immediate)
3. **API Test**: `curl http://localhost:8000/api/v1/health` (when backend running)
4. **WebSocket**: Test real-time updates through frontend

### After Making Frontend Changes
1. **Serve Frontend**: `python -m http.server 3000` from `frontend/` directory
2. **Access**: http://localhost:3000
3. **Test UI**: Navigate through dashboard, printer management, file management
4. **German Compliance**: Verify EUR formatting, German text, timezone

### End-to-End Validation
1. **Full System**: Start backend (`python src/main.py`) and frontend
2. **Test Flow**: Dashboard → Printers → Files → Settings
3. **WebSocket**: Verify real-time updates work
4. **German Features**: Check VAT calculations, date formatting

## File Locations Reference

### Configuration Files
- `requirements.txt` - Python dependencies
- `pytest.ini` - Test configuration
- `docker-compose.yml` - Full production stack
- `.env.example` - Environment variable template
- `database_schema.sql` - Complete database schema

### Documentation
- `README.md` - Main project documentation
- `DEVELOPMENT_PLAN.md` - Complete roadmap
- `docs/` - Detailed technical documentation
- `tests/README.md` - Test suite documentation

### Scripts
- `deploy.sh` - Production deployment
- `validate-deployment.sh` - Post-deployment validation
- `production-readiness-check.sh` - Pre-deployment checks
- `tests/test_runner.py` - Comprehensive test execution

## Time Expectations (NEVER CANCEL)
- **Database Setup**: < 1 second
- **Frontend Start**: Immediate
- **Backend Start**: Immediate (if dependencies installed)
- **Dependency Install**: 2-10 minutes (may fail, use Docker)
- **Full Test Suite**: 5-15 minutes
- **Docker Build**: 5-10 minutes (when working)
- **Deployment Validation**: 2-5 minutes

## Production Features
- **Monitoring**: Prometheus + Grafana dashboards
- **Security**: CORS, HTTPS, security headers
- **Compliance**: German GDPR/DSGVO compliance
- **Scalability**: Kubernetes deployment ready
- **Business**: German VAT, EUR currency, business reporting

## Success Indicators
- ✅ Database creates tables successfully
- ✅ Frontend serves on port 3000
- ✅ Backend API responds to health checks
- ✅ WebSocket connections work
- ✅ German business features display correctly
- ✅ Test suite passes (when dependencies available)

**Remember: This is a production-ready system with comprehensive German business features. Always test the complete user workflow after making changes.**