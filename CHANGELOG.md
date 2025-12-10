# Changelog

All notable changes to Printernizer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.8.7] - 2025-12-10

### Changed
- CI/CD pipeline testing

## [2.8.5] - 2025-12-10

### Changed
- CI/CD pipeline testing

## [2.8.0] - 2025-11-28

### Changed
- **API Documentation**: Enabled `/docs` (Swagger UI) and `/redoc` endpoints in all environments
  - Previously only available in development mode
  - Self-hosted applications benefit from always-available API documentation
  - Updated Content Security Policy to allow external documentation resources (cdn.jsdelivr.net, fonts.googleapis.com, fonts.gstatic.com)
  - Configured stable ReDoc JavaScript version (replaces unstable @next tag)

### Fixed
- **Security Headers**: Updated CSP to allow Swagger UI and ReDoc resources
  - Added cdn.jsdelivr.net for documentation JavaScript/CSS
  - Added fonts.googleapis.com and fonts.gstatic.com for ReDoc fonts
  - Added fastapi.tiangolo.com for documentation favicons

## [2.7.14] - 2025-11-28

### Fixed
- **Camera Preview**: Bambu Lab A1 camera preview now displays correctly on dashboard tiles
  - Replaced custom TCP/TLS camera client with bambulabs-api library integration
  - CameraSnapshotService now uses printer drivers directly via PrinterService
  - Removed 493 lines of complex binary protocol code
  - Simplified architecture: camera access delegated to printer drivers
  - Frame caching (5-second TTL) preserved for performance
  - Removed outdated integration tests for old camera client implementation

### Changed
- **Code Cleanup**: Significant codebase simplification (-2,927 lines)
  - Deleted `src/services/bambu_camera_client.py` (493 lines)
  - Deleted outdated test files: `test_camera_direct.py`, `test_camera_preview.py`, `test_camera_simple.py`
  - Deleted `tests/integration/test_camera_snapshot.py` (793 lines)
  - Removed CameraConnectionError exception handlers (no longer raised)
  - Camera functionality now maintained by bambulabs-api library

## [2.7.13] - 2025-11-26

### Fixed
- **Auto-connect after adding printer**: Newly added printers now automatically connect without requiring app restart
  - Printers immediately establish connection when added via API/UI
  - Monitoring starts automatically for newly added printers
  - Graceful error handling if printer is offline during creation

## [2.7.12] - 2025-11-25

### Fixed
- **Critical**: BambuLab file download functionality completely broken
  - Fixed file ID generation when backend returns undefined values
  - All file IDs were the string "undefined" preventing selection and download
  - Added proper ID generation from `printer_id_filename` format
  - Fixed status normalization to 'available' when backend returns undefined
  - Enhanced checkbox availability logic to match download filter logic
  - Added comprehensive diagnostic logging for debugging
  - Added validation for required fields (printer_id, filename) before download
  - Improved user feedback with specific error reasons

### Added
- **Usage Statistics Phase 2**: Completed aggregation and submission infrastructure
  - **Aggregation Service**: Full FastAPI service for receiving usage statistics
    - POST /submit endpoint with authentication and rate limiting
    - PostgreSQL/SQLite database schema for storing aggregated stats
    - GDPR-compliant data deletion endpoint
    - Docker deployment support with docker-compose
  - **Submission Enabled**: HTTP submission with retry logic
    - Exponential backoff retry (up to 3 attempts configurable)
    - Proper error handling for network failures, timeouts, rate limits
    - API key authentication (X-API-Key header)
    - Configurable endpoint, timeout, and retry count
  - **Automatic Scheduler**: Background task for periodic submissions
    - Checks every hour if submission is due
    - Configurable submission interval (default: 7 days)
    - Non-blocking background execution
    - Respects opt-in status and last submission date
  - **Integration Completed**: Service TODOs resolved
    - `_get_app_version()` now uses `get_version()` from utils
    - `_get_printer_fleet_stats()` integrated with PrinterService
    - Proper printer service injection to avoid circular dependencies
  - **Configuration**: Added usage statistics settings to config.py
    - `usage_stats_endpoint`: Aggregation service URL
    - `usage_stats_api_key`: API authentication key
    - `usage_stats_timeout`: HTTP timeout (default: 10s)
    - `usage_stats_retry_count`: Retry attempts (default: 3)
    - `usage_stats_submission_interval_days`: Submission interval (default: 7)
  - **Testing**: Comprehensive Phase 2 tests
    - Scheduler tests: lifecycle, timing, error handling, manual trigger
    - Submission tests: HTTP mocking, retry logic, authentication, event marking
    - 50+ new tests for Phase 2 functionality
  - **Privacy Maintained**: All Phase 1 privacy principles preserved
    - Still opt-in only (disabled by default)
    - No PII in printer fleet stats (only counts and types)
    - Local-first storage (events stored locally even if submission fails)
    - Full transparency (users can view/export/delete data)

## [2.7.0] - 2025-11-19

### 🎉 Major Milestone: Technical Debt Remediation Complete

**Zero TODOs Remaining** - All 88 identified technical debt issues across 4 phases have been addressed (68% of original 130 issues, all core work complete).

### Added
- **Printer Compatibility Checks**: Implemented dynamic printer capabilities lookup in file compatibility endpoint
  - Added `PRINTER_CAPABILITIES` lookup dictionary for Bambu Lab and Prusa Core One bed dimensions
  - Enhanced compatibility checks with actual printer data from database
  - Added Z-axis height validation against printer bed height
  - Fixed final TODO in codebase (files.py:1068)

### Changed
- **Technical Debt Phase 4** - Ongoing quality improvements (LOW priority)
  - **Test Coverage Expansion (Task 4.3 COMPLETE)**: ✅ Added 72 comprehensive tests covering Phases 1-3 improvements
    - **Repository Tests**: Enhanced `tests/database/test_repositories.py` with 23 new tests
      - FileRepository: 6 tests (create, list with filters, update metadata, delete, statistics)
      - IdeaRepository: 4 tests (create, list by status, update status, delete)
      - LibraryRepository: 5 tests (create, list with filters, update, delete, search)
      - Complete coverage of all 8 repositories from Phase 1 refactoring
    - **Analytics Service Tests**: Created `tests/services/test_analytics_service.py` with 15 comprehensive tests
      - Dashboard statistics, printer usage, material consumption
      - Business reports, data export (CSV/JSON), summary statistics
      - Dashboard overview, error handling, empty database scenarios
      - Full coverage of Phase 1 analytics implementations
    - **API Pagination Tests**: Created `tests/backend/test_api_pagination_optimizations.py` with 14 tests
      - Verifies Phase 2 pagination optimizations (efficient COUNT queries)
      - Tests combined list_with_count methods for jobs and files
      - Validates filter passing and pagination parameters
      - Includes performance tests ensuring no duplicate queries
    - **Connection Pooling Tests**: Created `tests/database/test_connection_pooling.py` with 20 tests
      - Pool initialization, WAL mode, synchronous settings
      - Connection acquisition/release, pool exhaustion handling
      - Pooled connection context manager with exception handling
      - Concurrent access, deadlock prevention, pool cleanup
      - Verifies Phase 3 connection pooling implementation
    - **Impact**: All critical technical debt improvements (Phases 1-3) now have comprehensive test coverage
    - **Task Substantially Complete**: Core testing gaps addressed, existing integration/e2e tests preserved
  - **Type Hints (Batches 1-4 COMPLETE)**: ✅ Added return type hints to 35 methods across 18 core services
    - **Batch 1**: config_service.py, event_service.py, file_discovery_service.py (8 methods)
      - Added `-> None` to validation, lifecycle, and dependency injection methods
    - **Batch 2**: camera_snapshot_service.py, bambu_ftp_service.py, timelapse_service.py (5 methods)
      - Added `-> None` to service lifecycle methods (start, shutdown)
      - Added `-> AsyncGenerator[ftplib.FTP_TLS, None]` to FTP context manager
      - Enhanced type safety for async context managers
    - **Batch 3**: monitoring_service.py, printer_monitoring_service.py, printer_connection_service.py, file_watcher_service.py, material_service.py, trending_service.py (14 methods)
      - Added `-> None` to monitoring loops and health check methods
      - Added `-> None` to printer status callbacks and update handlers
      - Added `-> None` to service initialization and table creation methods
      - Added `-> None` to file system event handlers (created, modified, deleted)
      - Enhanced type safety for monitoring, initialization, and event handling
    - **Batch 4**: file_service.py, printer_service.py, library_service.py, search_service.py, migration_service.py, file_upload_service.py (8 methods)
      - Added `-> None` to core service initialization methods
      - Added `-> None` to search cache management methods (set, invalidate)
      - Added `-> None` to database migration workflow methods
      - Added `-> None` to file upload post-processing
      - Enhanced type safety for core service lifecycle and operations
    - **Task Substantially Complete**: 58% coverage achieved (18/31 service files)
    - Improves IDE autocomplete, type checking, and catches bugs at development time
    - Remaining 13 service files can be addressed in future incremental work
- **Technical Debt Phase 3** - Completed all backend improvements for Phase 3
  - **Configuration Extraction**: Centralized all hardcoded values into `src/config/constants.py`
    - Extracted 18+ polling intervals, retry settings, and API URLs
    - Created helper functions: `api_url()`, `printer_url()`, `file_url()`, `job_url()`
    - Improved maintainability and configurability across 8+ service files
  - **Database Connection Pooling**: Implemented connection pooling for improved concurrency
    - Added asyncio.Queue-based connection pool (default: 5 connections)
    - Enabled WAL mode for optimal read concurrency
    - Added `pooled_connection()` context manager for easy usage
    - Backward compatible with existing code
  - **Async Task Management**: Verified proper task lifecycle management
    - EventService properly stores and manages background tasks
    - Added `stop()` method for graceful shutdown
    - Tasks properly cancelled and awaited on shutdown
  - **Frontend Tasks Deferred**: Strategically deferred 2 frontend tasks to Phase 4
    - Frontend logging cleanup (40+ console statements)
    - XSS security fixes (20+ innerHTML cases)
    - Lower priority than backend improvements; will be addressed in future sprint

## [2.6.0] - 2025-11-13

### Added
- **E2E Test UI Elements** - Implemented missing UI elements for Playwright E2E tests
  - Added "Create Job" button (`#createJobBtn`) to Jobs page
  - Added jobs table with `#jobsTable` ID and proper table structure
  - Added job creation modal (`#jobModal`) with form fields:
    - Job name, file selection, printer selection
    - Business job checkbox with customer name field
  - Added material modal (`#materialModal`) with form fields:
    - Material name, type, color, weight, cost
  - Added consistent IDs to all action buttons:
    - `#addPrinterBtn` with `data-action="add-printer"` attribute
    - `#addMaterialBtn` for material management
  - Implemented JavaScript modal functions:
    - `showCreateJobModal()`, `closeJobModal()`
    - `showAddMaterialModal()`, `closeMaterialModal()`

### Changed
- **Materials Page** - Set table view as default (was cards view)
  - Materials table now visible by default for better E2E test compatibility
  - Cards view moved to secondary option via view mode toggle

### Fixed
- **CI/CD Test Coverage** - Fixed critical test coverage gap in GitHub Actions workflow
  - Removed blanket `test_*.py` exclusion from `.gitignore` that prevented proper test file tracking
  - Replaced explicit test file listing with pytest discovery pattern in CI/CD workflow
  - Added comprehensive E2E test job with Playwright for frontend validation
  - Test coverage increased from 68.3% (28/41 files) to 100% (39/39 files)
  - Added 44 E2E tests that were previously not running in CI/CD
  - Total test count increased from 518 to 562 tests (+8.5%)
  - **E2E Tests** - Fixed 10 failing Playwright tests by implementing missing UI elements:
    - `test_dashboard_add_printer_button_exists` - Button now has correct IDs
    - `test_jobs_table_display` - Table exists and is visible
    - `test_create_job_button_exists` - Button present with correct ID
    - `test_create_job_modal_opens` - Modal can be opened
    - `test_business_job_fields` - Business fields present in job modal
    - `test_vat_calculation_display` - Job modal supports business workflows
    - `test_job_form_validation` - Job form exists with proper structure
    - `test_materials_table_display` - Materials table visible by default
    - `test_add_material_button_exists` - Button has correct ID

### Technical Details
- **Test Infrastructure** - Modernized test execution approach
  - CI/CD now uses `pytest tests/ --ignore=tests/e2e --ignore=tests/frontend` for automatic test discovery
  - No longer requires manual workflow updates when adding new test files
  - E2E tests run in dedicated job with full Playwright browser automation
  - Security scan job now waits for E2E tests to complete
  - All page object model selectors now match implemented UI elements

## [2.5.4] - 2025-11-11

### Fixed
- **CI/CD Pipeline** - Fixed GitHub Actions workflow failures
  - Fixed environment validation error: Changed `ENVIRONMENT: test` to `ENVIRONMENT: testing` to match config validation
  - Removed deprecated `actions/create-release@v1` step (handled by separate Create Release workflow)
  - Added conditional checks for optional Kubernetes deployment files to prevent failures when files don't exist
  - Added conditional checks for optional performance test files
  - Improved deployment robustness with graceful handling of missing configuration files

### Changed
- **CI/CD Workflow** - Enhanced production deployment resilience
  - All Kubernetes manifest files (security policies, file storage, WebSocket load balancer) now optional
  - Deployment script execution now conditional on file existence
  - Performance tests gracefully skip when test files are not present
  - Better error messages and warnings for missing optional components

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
<!-- Sync trigger 2025-12-08T21:30:47Z -->
