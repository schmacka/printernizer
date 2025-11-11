# Changelog

All notable changes to Printernizer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.5.3] - 2025-11-11

### Added
- **Auto-Download System API Completion** - Added missing thumbnail processing endpoints
  - `POST /api/v1/files/{file_id}/thumbnail/extract` - Extract embedded thumbnails from 3MF/BGCode/G-code files
  - `POST /api/v1/files/{file_id}/thumbnail/generate` - Generate thumbnails for STL/OBJ 3D models
  - `POST /api/v1/files/{file_id}/analyze/gcode` - Analyze G-code files to extract metadata and print settings
  - Completes the Auto-Download System frontend-backend integration
  - Enables manual thumbnail processing through the management UI

## [2.5.2] - 2025-11-11

### Fixed
- **Drag-and-Drop UX** - Corrected hover feedback for library file upload
  - Fixed drag-over visual feedback to properly show upload target area
  - Improved user experience during file drag operations

## [2.5.1] - 2025-11-11

### Added
- **Release Process Documentation** - Complete workflow automation and documentation
  - GitHub Actions workflow for automated release creation
  - Comprehensive RELEASE.md with versioning standards and procedures
  - Updated CONTRIBUTING.md with release process reference

### Fixed
- **Printer Status API** - Fixed attribute name for remaining time in printer status endpoint
  - Corrected property name for accurate time remaining calculations

## [2.5.0] - 2025-11-11

### Added
- **Drag-and-Drop File Upload** - Enhanced library management with drag-and-drop support
  - Intuitive drag-and-drop interface for library file uploads
  - Visual hover feedback with border highlighting
  - Seamless integration with existing upload functionality

### Fixed
- **Docker Deployment** - Resolved critical Docker startup and configuration issues
  - Fixed entrypoint.sh not found error during Docker startup
  - Configured proper environment variables for Docker containers
  - Improved database initialization in Docker environments
- **API Completeness** - Added missing API endpoints and cleaned up unused code
  - Ensured all frontend buttons have corresponding backend endpoints
  - Comprehensive frontend button & API endpoint review completed

## [2.4.5] - 2025-11-10

### Fixed
- **CRITICAL: Home Assistant Add-on Fresh Install** - Fixed schema conflict on fresh installs
  - Removed outdated `database_schema.sql` initialization from run.sh script
  - Fresh installs now use Python code to create database schema (single source of truth)
  - Eliminates schema mismatch between SQL file (old schema with `download_status`) and Python code (new schema with `status`)
  - Fixes "no such column: status" error on fresh Home Assistant add-on installations
  - Database creation and migrations now fully handled by Python application

### Technical Details
- run.sh no longer initializes database with sqlite3 command
- Python application creates all tables with correct schema via `_create_tables()`
- Migrations system then applies any additional schema updates
- Ensures consistency between fresh installs and upgraded installations

## [2.4.4] - 2025-11-10

### Fixed
- **CRITICAL: Database Migration System** - Fixed broken migration system affecting fresh installs and reinstalls
  - Added proper SQL migration runner that executes all migration files from `migrations/` directory
  - Implemented automatic discovery and execution of numbered SQL migration files (001-013)
  - Added safety check that always ensures `source` column exists in files table (prevents "no such column: source" error)
  - Graceful error handling for duplicate columns and missing tables during migrations
  - Fixes issue where migrations 002-013 were never executed despite SQL files existing
  - Ensures databases from failed/partial migrations get properly repaired on next startup
  - Migration tracking now properly records all executed SQL migrations

### Technical Details
- Migration system now scans `migrations/` directory for `[0-9][0-9][0-9]_*.sql` files
- Executes migrations in numerical order (001, 002, 003, etc.)
- Skips already-applied migrations based on `migrations` table
- Handles SQLite limitations (no IF NOT EXISTS for ALTER TABLE) with try/catch
- Backward compatible with existing migration tracking

## [2.4.0] - 2025-11-09

### Added
- **Automated Job Creation** - Automatically create job entries when prints are detected
  - **Auto-Detection**: Monitors printer status and creates jobs when prints start
  - **Startup Discovery**: Detects and creates jobs for prints already in progress on system startup
  - **Deduplication**: Intelligent cache-based and database-backed deduplication prevents duplicate job creation
  - **Time Tracking**: Captures printer-reported start times and tracks discovery time
  - **Visual Indicators**: Auto-created jobs display ⚡ Auto badge in job list
  - **Settings Toggle**: Enable/disable auto-creation in Settings page
  - **Toast Notifications**: Real-time notifications when jobs are auto-created
  - **First-Time Tip**: One-time informational message explaining the auto-creation feature
  - **WebSocket Events**: `job_auto_created` event for real-time UI updates
  - **Metadata Tracking**: Stores auto-creation info in `customer_info` field
  - **Performance**: Sub-millisecond lock contention, < 100ms database queries
  - **Comprehensive Testing**: 53 tests (28 unit, 13 integration, 12 performance)
  - **Documentation**:
    - Design document (`docs/design/automated-job-creation.md`)
    - Testing guide (`docs/automated-job-creation-testing.md`)
    - API documentation (`docs/api-automated-job-creation.md`)
    - User guide (`docs/user-guide-auto-job-creation.md`)

## [2.2.0] - 2025-11-07

### Added
- **Timelapse Configuration UI** - Expose timelapse settings in Home Assistant addon configuration
  - `timelapse_enabled` - Enable/disable timelapse feature
  - `timelapse_source_folder` - Configure source folder for timelapse images
  - `timelapse_output_folder` - Configure output folder for processed videos
  - `timelapse_output_strategy` - Choose where videos are saved (same/separate/both)
  - `timelapse_auto_process_timeout` - Configure auto-processing delay
  - `timelapse_cleanup_age_days` - Configure cleanup recommendation threshold
- Documentation in README for timelapse configuration and setup

### Changed
- Automatic directory creation for timelapse folders on addon startup
- Environment variable mapping in run.sh for all timelapse settings

## [2.1.6] - 2025-11-07

### Fixed
- Fixed timelapse page refresh functionality - added missing case in refreshCurrentPage() switch statement

## [2.1.0] - 2025-11-07

### Added
- **Timelapse Management System** - Complete automated timelapse video creation and management
  - **Automated Monitoring**: Watches configured folders for timelapse images with auto-detection
  - **FlickerFree Integration**: High-quality video processing with deflicker algorithm
  - **Gallery UI**: Modern video gallery with thumbnails, metadata, and fullscreen playback
  - **Smart Job Linking**: Automatically links videos to print jobs when possible
  - **Processing Queue**: Sequential processing with real-time status updates via WebSocket
  - **Storage Management**: Track storage usage and get cleanup recommendations
  - **Manual Control**: Trigger processing on-demand with configurable timeout
  - **Cross-Platform**: Works in Docker, standalone Python, and Home Assistant add-on
  - **New Components**:
    - `src/services/timelapse_service.py` - Core timelapse processing logic (1000+ lines)
    - `src/api/routers/timelapses.py` - Complete REST API endpoints
    - `src/models/timelapse.py` - Database models and schemas
    - `frontend/js/timelapses.js` - Frontend gallery and player (700+ lines)
    - `frontend/css/timelapses.css` - Responsive styles with dark/light theme
    - `migrations/012_add_timelapses.sql` - Database schema
  - **Documentation**: Comprehensive design document with architecture and workflows

### Performance
- **Major Startup Performance Optimization** (Development Mode)
  - Reduced startup time from ~82 seconds to ~20-30 seconds (60-70% improvement)
  - Added intelligent reload exclusions to prevent unnecessary uvicorn restarts
    - Excludes database files (*.db, *.db-journal, *.db-shm, *.db-wal)
    - Excludes log files (*.log)
    - Excludes cache directories (__pycache__, *.pyc, .pytest_cache)
    - Excludes frontend static files and downloads directory
  - Implemented parallel service initialization using asyncio.gather()
    - Domain services (Library + Material) initialize concurrently
    - File system services (File Watcher + Ideas) initialize in parallel
    - Background services startup parallelized
    - Monitoring services (Printer + File Watcher) start concurrently
  - Added DISABLE_RELOAD environment variable for even faster startup without auto-reload
  - Fixed Windows File Watcher threading warnings by using PollingObserver on Windows

### Added
- **Startup Performance Monitoring** (`src/utils/timing.py`)
  - New `StartupTimer` utility class for tracking initialization performance
  - Context managers for timing synchronous and asynchronous operations
  - Automatic generation of detailed startup performance reports
  - Shows duration of each operation with percentage breakdown
  - Identifies slowest operations for data-driven optimization

### Changed
- **Enhanced "Server Ready" Logging**
  - Clear visual feedback when server is ready with rocket emoji 🚀
  - Displays connection URLs (API, documentation, health check)
  - Shows fast mode indicator when DISABLE_RELOAD is enabled
- **File Watcher Service** (`src/services/file_watcher_service.py`)
  - Platform-specific observer selection (PollingObserver on Windows)
  - Cleaner logging without threading warnings
  - More reliable file system monitoring on Windows

### Documentation
- Added comprehensive startup performance analysis in `docs/development/STARTUP_PERFORMANCE_ANALYSIS.md`
- Added implementation summary in `docs/development/STARTUP_OPTIMIZATION_SUMMARY.md`
- Updated `run.bat` with DISABLE_RELOAD usage examples

## [1.5.9] - 2025-11-04

### Fixed
- **Printer Autodiscovery**: Fixed 503 Service Unavailable error on `/api/v1/printers/discover` endpoint
  - Installed `netifaces-plus` package (Windows-compatible fork of netifaces)
  - Fixed conditional import of `zeroconf` ServiceListener to prevent NameError
  - Added stub classes for optional dependencies when not available
- **Frontend Notifications**: Implemented missing `showNotification()` function
  - Created wrapper function that maps to existing `showToast()` system
  - Resolves JavaScript errors: "showNotification is not defined"
  - Affects printers.js, ideas.js, and camera.js modules

### Changed
- Updated `requirements.txt` to use `netifaces-plus>=0.12.0` instead of `netifaces>=0.11.0` for Windows compatibility
- Application version bumped to 1.5.9 (bugfix release)
- Home Assistant add-on version bumped to 2.0.37

### Documentation
- Added detailed fix plan in `docs/fixes/PRINTER_AUTODISCOVERY_FIX.md`

## [1.2.0] - 2025-10-02

### Added - Phase 2: Enhanced 3D Model Metadata Display (Issue #43, #45)
- **Enhanced Metadata Display Component** (`frontend/js/enhanced-metadata.js`)
  - Comprehensive metadata viewer with async loading and caching
  - Summary cards showing dimensions, cost, quality score, and object count
  - Detailed sections for physical properties, print settings, materials, costs, quality metrics, and compatibility
  - Smart caching with 5-minute TTL to reduce API calls
  - Loading, error, and empty state handling
  
- **Enhanced Metadata Styles** (`frontend/css/enhanced-metadata.css`)
  - Modern card-based design system with responsive grid layouts
  - Full responsive design support (desktop, tablet, mobile, small mobile)
  - Dark/light theme compatibility with both media query and class-based support
  - Color-coded quality indicators (green/yellow/red)
  - Smooth animations and transitions for better UX
  - Icon system using emoji for universal recognition
  
- **File Browser Integration**
  - Integrated enhanced metadata into file preview modal
  - Non-blocking async metadata loading for better performance
  - Enhanced 3D file preview with comprehensive information display
  
- **Documentation**
  - Comprehensive Phase 2 implementation documentation
  - Integration verification script
  - Test HTML file for component validation

### Changed
- Updated application version to 1.2.0 in health check endpoint
- Modified file preview rendering to include metadata container
- Enhanced files.js with async metadata loading functionality

### Technical Details
- ES6+ JavaScript with async/await patterns
- Responsive CSS Grid layouts with mobile-first approach
- WCAG 2.1 AA accessibility compliance
- Browser compatibility: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

## [1.1.6] - Previous Version

### Added
- Project cleanup for public GitHub release
- Comprehensive documentation structure in `docs/`
- GitHub community files (CONTRIBUTING.md, SECURITY.md)
- Professional LICENSE file with dual licensing

### Changed
- Moved development documents to `docs/development/`
- Improved .gitignore with comprehensive exclusions
- Organized project structure for public release

### Removed
- Docker files (temporarily removed - not working)
- Temporary debugging and test files
- Development artifacts and cache files

## [1.0.0] - 2025-09-25

### Added
- **Complete Printer Integration**: Full support for Bambu Lab A1 (MQTT) and Prusa Core One (HTTP API)
- **Real-time Monitoring**: Live printer status, temperatures, and job progress with WebSocket updates
- **Drucker-Dateien System**: Unified file management with one-click downloads from all printers
- **German Business Compliance**: VAT calculations, EUR currency, GDPR compliance, timezone support
- **Professional Web Interface**: Mobile-responsive dashboard with accessibility features
- **Business Analytics**: Cost calculations, material tracking, and export capabilities
- **Job Management**: Complete job tracking with business vs. private categorization
- **File Download System**: Smart organization by printer/date with status tracking
- **WebSocket Real-time Updates**: Live dashboard updates without page refresh
- **Advanced Error Handling**: Comprehensive error tracking and monitoring system
- **Database Management**: SQLite with migrations and optimization
- **API Documentation**: Complete REST API with Swagger/OpenAPI documentation
- **Test Suite**: Comprehensive testing framework for backend and frontend
- **Monitoring Integration**: Prometheus metrics and Grafana dashboards ready
- **Security Features**: GDPR compliance, secure credential storage, input validation

### Core Features Completed
- ✅ FastAPI backend with async SQLite database
- ✅ Bambu Lab A1 integration via MQTT (bambulabs-api)
- ✅ Prusa Core One integration via PrusaLink HTTP API
- ✅ Real-time printer monitoring with 30-second polling
- ✅ File management with automatic discovery and downloads
- ✅ German business interface with VAT and EUR support
- ✅ WebSocket connectivity for live updates
- ✅ Mobile-responsive web interface
- ✅ Business analytics and reporting
- ✅ Professional deployment configuration
- ✅ Comprehensive error handling and logging

### Technical Architecture
- **Backend**: FastAPI with async/await patterns
- **Database**: SQLite with SQLAlchemy ORM and migrations
- **Real-time**: WebSocket integration for live updates
- **Printer APIs**: MQTT (Bambu Lab) and HTTP REST (Prusa)
- **Frontend**: Modern vanilla JavaScript with modular components
- **Testing**: pytest with comprehensive test coverage
- **Documentation**: Sphinx-ready documentation structure

### Business Features
- German language interface and error messages
- VAT calculations with 19% German tax rate
- GDPR-compliant data handling and retention
- EUR currency formatting (1.234,56 €)
- Europe/Berlin timezone support
- Export capabilities for German accounting software
- Business vs. private job classification
- Material cost tracking and reporting

### Deployment Ready
- Production-ready FastAPI application
- Environment-based configuration
- Health check endpoints
- Monitoring and logging integration
- Security headers and CORS protection
- Database migrations and versioning

## Development Phases Completed

### Phase 1: Foundation & Core Infrastructure ✅
- Project setup with proper Python structure
- SQLite database with job-based architecture
- Configuration management system
- Logging and error handling framework

### Phase 2: Printer Integration ✅
- Bambu Lab A1 MQTT integration
- Prusa Core One HTTP API integration
- Real-time status monitoring
- Connection health monitoring and recovery

### Phase 3: File Management System ✅
- Automatic file discovery on both printer types
- One-click download system with progress tracking
- Smart file organization by printer and date
- File status tracking (Available, Downloaded, Local)

### Phase 4: Web Interface Development ✅
- Professional responsive web design
- Real-time dashboard with WebSocket updates
- Intuitive file management interface
- Mobile-first approach with accessibility

### Phase 5: Business & Analytics Features ✅
- German business compliance and localization
- Cost calculation system for materials and power
- Export functionality for accounting software
- Business statistics and performance analytics

## Future Roadmap

### Phase 6: 3D Preview System (Planned)
- STL/3MF/G-Code visualization
- Multiple rendering backends
- Interactive preview interface
- Performance optimization for large files

### Phase 7: Advanced Features (Planned)
- Desktop GUI application
- Home Assistant addon integration
- Advanced monitoring and alerting
- Multi-user authentication system

### Phase 8: Enterprise Features (Planned)
- Role-based access control
- Advanced reporting and analytics
- API rate limiting and quotas
- Enterprise deployment options

---

**Note**: This project has successfully completed all core features and is production-ready for 3D printer fleet management. The system provides enterprise-grade functionality while maintaining ease of use for individual users.

**Status**: ✅ Production Ready - Core features complete and tested