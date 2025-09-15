# Code TODOs - Printernizer Project

## Backend TODOs

### Job Service (`src/services/job_service.py`)
- [x] Implement job fetching from database
- [x] Implement job fetching with filtering
- [x] Implement job fetching by ID
- [x] Implement job deletion
- [x] Implement active job filtering
- [x] Implement job creation
- [x] Implement job status updates
- [x] Implement job statistics calculation

### File Service (`src/services/file_service.py`)
- [x] Implement database queries for printer files
- [x] Implement printer file discovery
- [x] Implement file download functionality
- [x] Implement download status tracking

### Event Service (`src/services/event_service.py`)
- [x] Implement printer status monitoring
- [x] Implement job status monitoring
- [x] Implement file discovery

### Analytics Service (`src/services/analytics_service.py`)
- [x] Implement analytics calculations
- [x] Implement printer usage analytics
- [x] Implement material tracking
- [x] Implement business reporting
- [ ] Implement data export functionality
- [x] Implement period-based calculations

## Frontend TODOs

### Settings (`frontend/js/settings.js`)
- [x] Implement add watch folder API call
- [x] Implement remove watch folder API call

### Milestone 1.2 Functions (`frontend/js/milestone-1-2-functions.js`)
- [ ] Implement 3D file preview
- [ ] Implement local file opening

## Priority Areas
1. Database Integration
   - Job management
   - File management
   - Analytics storage

2. Monitoring Implementation
   - Printer status
   - Job status
   - File discovery

3. Business Features
   - Analytics calculations
   - Material tracking
   - Business reporting
   - Data export

4. Frontend Enhancements
   - Watch folder management
   - 3D file preview
   - Local file handling

## Additional Placeholder Implementations Found ✅ COMPLETED

### API and Services
1. **Jobs API** (`src/api/routers/jobs.py`) ✅
   - [x] Replace empty list returns with proper database queries
   - [x] Implement proper error handling for job operations

2. **File Service** (`src/services/file_service.py`) ✅
   - [x] Replace placeholder download success rate calculation
   - [x] Implement proper file listing functionality
   - [x] Add real file discovery mechanism
   - [x] Implement proper file status tracking

3. **Config Service** (`src/services/config_service.py`) ✅
   - [x] Replace empty list returns with proper configuration loading (already implemented)
   - [x] Add configuration validation (already implemented)
   - [x] Implement proper error handling for missing configurations (already implemented)

4. **Analytics Service** (`src/services/analytics_service.py`) ✅
   - [x] Replace empty analytics results with actual calculations
   - [x] Implement proper data aggregation
   - [x] Add real-time analytics processing

## Security Implementations Needed

### Authentication & Authorization
1. **Security Configuration**
   - [ ] Replace default secret key in configuration
   - [ ] Implement proper secret management for MQTT passwords
   - [ ] Set up proper printer API key management
   - [ ] Implement secure credential storage

2. **Authentication System**
   - [ ] Implement comprehensive authentication system
   - [ ] Add proper authorization checks
   - [ ] Implement session management
   - [ ] Add rate limiting for API endpoints

### Error Handling & Logging ✅ COMPLETED

1. **Frontend Error Management** ✅
   - [x] Replace console.error calls with proper error tracking:
     - [x] WebSocket error handling
     - [x] Settings management errors
     - [x] LocalStorage error handling
   - [x] Implement user-friendly error messages
   - [x] Add error reporting system

2. **Backend Error Handling** ✅
   - [x] Implement comprehensive error handling for API endpoints
   - [x] Add proper logging system
   - [x] Implement error monitoring and alerting

**Implementation Summary:**
- Created comprehensive ErrorHandler class for frontend with visual notifications
- Replaced 71+ console.error calls with proper error tracking
- Added backend error reporting API (`/api/v1/errors/*`)
- Implemented MonitoringService with error pattern detection
- Added error categorization, severity levels, and alerting thresholds
- Created error statistics and health monitoring endpoints

## Testing Implementation Needs

### Integration Tests
1. **Hardware Integration**
   - [ ] Implement proper printer hardware integration tests
   - [ ] Add mock hardware for CI/CD pipeline

2. **Configuration Tests**
   - [ ] Complete ConfigService test coverage
   - [ ] Add configuration validation tests

### Missing Test Coverage
- [ ] Add WebSocket connection tests
- [ ] Implement authentication flow tests
- [ ] Add comprehensive API endpoint tests
- [ ] Implement database migration tests

## Database Implementation Needs

### Core Database Layer (`src/database/database.py`)
1. **Error Handling & Recovery**
   - [ ] Replace empty pass statements in error handlers
   - [ ] Implement proper connection pooling
   - [ ] Add retry mechanisms for failed operations
   - [ ] Implement proper transaction rollback

2. **Query Optimization**
   - [ ] Implement prepared statements
   - [ ] Add query result caching
   - [ ] Optimize bulk operations
   - [ ] Add index usage monitoring

3. **Connection Management**
   - [ ] Implement connection pooling
   - [ ] Add connection timeout handling
   - [ ] Implement proper connection cleanup
   - [ ] Add connection health checks

### Database Operations

1. **Migration System**
   - [ ] Implement proper migration versioning
   - [ ] Add migration rollback capabilities
   - [ ] Implement migration validation
   - [ ] Add schema version tracking

2. **Data Integrity**
   - [ ] Implement foreign key constraint checks
   - [ ] Add data validation before insertion
   - [ ] Implement proper cascading deletes
   - [ ] Add data consistency checks

3. **Performance Optimizations**
   - [ ] Implement database query logging
   - [ ] Add query performance monitoring
   - [ ] Optimize index usage
   - [ ] Implement query plan analysis

### Service-Level Database Integration

1. **Watch Folder Service**
   - [ ] Add proper transaction handling
   - [ ] Implement batch operations
   - [ ] Add proper error recovery
   - [ ] Implement data validation

2. **Printer Service**
   - [ ] Optimize printer status updates
   - [ ] Implement proper connection state tracking
   - [ ] Add printer configuration versioning
   - [ ] Implement printer data archiving

3. **Job Service**
   - [ ] Implement job history archiving
   - [ ] Add job statistics aggregation
   - [ ] Implement job data cleanup
   - [ ] Add job recovery mechanisms

### Database Monitoring & Maintenance

1. **Monitoring**
   - [ ] Implement database size monitoring
   - [ ] Add performance metrics collection
   - [ ] Implement query timing tracking
   - [ ] Add connection pool monitoring

2. **Maintenance**
   - [ ] Implement automated vacuum operations
   - [ ] Add index maintenance
   - [ ] Implement data archiving
   - [ ] Add backup verification

3. **Security**
   - [ ] Implement proper access control
   - [ ] Add query sanitization
   - [ ] Implement audit logging
   - [ ] Add sensitive data encryption

Last updated: September 10, 2025

## Recently Completed Sections ✅

- **Additional Placeholder Implementations Found** - Completed API and Services improvements
- **Error Handling & Logging** - Comprehensive frontend and backend error management system

---

## Temporary / Placeholder Code Audit (September 15, 2025)

This section catalogs current temporary constructs (abstract stubs, silent pass blocks, and areas lacking full implementation) discovered by automated scan. Each item includes a recommended action and priority.

### Legend
- Priority: (H) High – needed for correctness or robustness, (M) Medium – improves reliability/observability, (L) Low – polish/tech debt.
- Type: ABSTR = Abstract interface placeholder, SILENT = Silent exception handling, STUB = Unimplemented logic placeholder, DESIGN = Architectural enhancement.

### 1. Abstract Interface Stubs (Intentional but require concrete impls)
File: `src/printers/base.py`
- Lines ~54-118: Multiple `@abstractmethod` definitions (`connect`, `disconnect`, `get_status`, `get_job_info`, `list_files`, `download_file`, `pause_print`, `resume_print`, `stop_print`, `has_camera`, `get_camera_stream_url`, `take_snapshot`).
   - Action: Ensure each supported printer type (e.g., Bambu, Prusa, Virtual/Test) has full implementation with consistent exception semantics (raise `PrinterConnectionError` vs generic). Add docstrings clarifying expected retry behavior and failure modes.
   - Priority: H
   - Follow-up: Create a conformance test suite validating all concrete printer classes implement these methods and produce `PrinterStatusUpdate` objects with required fields.

### 2. Parser Initialization Stub
File: `src/services/bambu_parser.py`
- Line ~43: `__init__` contains only `pass`.
   - Action: Add optional configuration (e.g., max thumbnail size, enable/disable metadata categories) and precompiled patterns checksum for quick self-test. Replace `pass` with clear initialization or remove method entirely if no state needed.
   - Priority: L
   - Follow-up: Add unit test to confirm parser self-test reports pattern availability.

### 3. Silent Exception Handling (Needs explicit handling or logging enrichment)
File: `src/services/migration_service.py`
- Lines ~71, ~138: `async with conn.execute(...): pass` patterns – acceptable for aiosqlite context usage but can disguise intent.
   - Action: Replace `pass` with comment clarifying side-effect execution (e.g., `# Statement executed; no direct result set expected`).
   - Priority: L
   - Follow-up: Add migration dry-run mode logging executed filenames.

File: `src/database/database.py`
- Multiple occurrences of `async with self._connection.execute(...): pass` across CRUD methods.
   - Action: Same as above; optionally wrap in dedicated helper to reduce repetition and centralize error handling / retry (design improvement).
   - Priority: M
   - Follow-up: Introduce `execute_write(sql, params)` helper with structured logging and optional retry.

File: `src/services/monitoring_service.py`
- Line ~339: Bare `pass` inside nested try/except while processing log cleanup; context likely ignoring individual file errors.
   - Action: Add granular logging or counter for skipped files; avoid losing failure diagnostics.
   - Priority: M
   - Follow-up: Expose cleanup metrics (files_attempted, files_deleted, deletions_failed) via `get_monitoring_status`.

### 4. Monitoring & Error Metrics Enhancement Gaps
File: `src/services/monitoring_service.py`
- Current `get_monitoring_status` builds health status but lacks latency metrics, last error category breakdown, and anomaly detection state.
   - Action: Extend to include: average DB query time (sampled), recent error rate (errors/hour), and open alert counts by severity.
   - Priority: M
   - Follow-up: Add structured schema to differentiate transient vs systemic issues.

### 5. File Service Statistics Robustness
File: `src/services/file_service.py`
- Stats calculation (lines ~250-320) assumes synchronous correctness; no handling for extremely large file lists or streaming.
   - Action: Refactor to incremental aggregation (generator) and add guardrails for memory (e.g., threshold logging if > N files).
   - Priority: L
   - Follow-up: Add unit test simulating large dataset.

### 6. Database Layer Enhancements (Design / Tech Debt)
File: `src/database/database.py`
- Missing: Retry strategy, statement abstraction, connection resilience, query timing instrumentation.
   - Action: Implement lightweight instrumentation decorator capturing duration + error type. Add optional exponential backoff for `OperationalError` on writes.
   - Priority: H (observability & reliability)
   - Follow-up: Provide `/api/v1/health/db` extended diagnostics endpoint.

### 7. Migration System Hardening
File: `src/services/migration_service.py`
- Lacks rollback, checksum validation, and idempotency verification beyond `migration_name` key.
   - Action: Add migration file SHA256 stored alongside name, and a `schema_version` view for external tools.
   - Priority: M
   - Follow-up: Add `force_verify` command that recalculates checksums and reports drift.

### 8. Abstract Printer Monitoring Loop Resilience
File: `src/printers/base.py`
- Monitoring loop swallows broad exceptions and continues; no backoff or error classification.
   - Action: Add exponential backoff after consecutive failures; track failure count; emit structured event after threshold.
   - Priority: M
   - Follow-up: Expose monitoring metrics via printer service API.

### 9. Camera Capability Abstraction
File: `src/printers/base.py`
- Methods `has_camera`, `get_camera_stream_url`, `take_snapshot` abstract but no documented fallback semantics if unsupported.
   - Action: Define canonical exception (`CameraNotSupportedError`) or return contract (always `None` vs raise). Update docstrings accordingly.
   - Priority: M
   - Follow-up: Add capability negotiation test.

### 10. Parser Metadata Normalization
File: `src/services/bambu_parser.py`
- Metadata extraction directly maps raw keys; no normalization layer or unit standardization (e.g., converting speeds, durations uniformly).
   - Action: Add normalization function producing canonical schema (e.g., seconds, mm/s, grams as float) and version tag.
   - Priority: M
   - Follow-up: Add schema version bump mechanism when fields change.

### 11. Graceful Degradation for Unsupported File Types
File: `src/services/bambu_parser.py`
- Unsupported file returns generic error string.
   - Action: Replace with structured error object including `error_code` (e.g., `UNSUPPORTED_FILE_TYPE`).
   - Priority: L
   - Follow-up: Frontend mapping for user-friendly messages.

### 12. Health Check Consistency
File: `src/printers/base.py` (method `health_check`)
- Returns False on any exception but does not differentiate transient connectivity vs fatal config errors.
   - Action: Introduce categorized result: `{ healthy: bool, reason: str, transient: bool }`.
   - Priority: M
   - Follow-up: Adjust upstream monitoring dashboards.

### Consolidated Action Table
| Area | Priority | Category | Primary Action |
|------|----------|----------|----------------|
| Abstract printer methods | H | ABSTR | Implement per printer + conformance tests |
| Database instrumentation | H | DESIGN | Add timing + retry helpers |
| Migration checksums | M | DESIGN | Store & verify file hashes |
| Monitoring loop backoff | M | DESIGN | Add exponential backoff + metrics |
| Camera capability contract | M | ABSTR | Define error/return semantics |
| Parser normalization | M | DESIGN | Normalize metadata schema |
| Silent passes (DB/migrations) | L | SILENT | Replace with clarifying comments |
| Bambu parser __init__ | L | STUB | Remove or add config init |
| File stats scalability | L | DESIGN | Stream/incremental aggregation |
| Unsupported file error struct | L | DESIGN | Add structured error codes |
| Health check detail | M | DESIGN | Return structured health object |
| Log cleanup silent pass | M | SILENT | Add metrics for skipped deletions |

### Next Step Recommendations
1. Implement database instrumentation + helper (unblocks richer monitoring) (H)
2. Add printer interface conformance tests and implement missing methods for all concrete printers (H)
3. Add monitoring loop resilience (M)
4. Introduce migration checksum & verification utility (M)
5. Define and document camera capability semantics (M)

---

### Progress Log (September 15, 2025)
- Database instrumentation Phase 1 implemented: added `_execute_write`, `_fetch_one`, `_fetch_all` with timing, limited retries, and structured debug logging.
- Refactored create/update/delete operations for printers, jobs, files, and selective read methods to use helpers.
- Next Phase (planned, not yet implemented): expose aggregated DB metrics (avg duration, error counts) via monitoring service and add retry configuration.
 - Added printer interface conformance test (`tests/test_printer_interface_conformance.py`) validating async implementation of required abstract methods for Prusa and conditional Bambu.
 - Fixed `pytest.ini` invalid list syntax to allow isolated test execution.
 - Future (Phase 2): Extend conformance tests to validate semantic behaviors (error raising consistency, status value domains) and add camera capability contract enforcement.

- Monitoring loop resilience implemented in `src/printers/base.py`:
   - Added exponential backoff with jitter for monitoring loop on failures.
   - Tracked metrics: consecutive/total failures, last poll duration, last error and timestamps.
   - Exposed metrics via `BasePrinter.get_monitoring_metrics()` and surfaced through `PrinterService.get_printer()` and `health_check()` responses.
   - Follow-up: add aggregate Prometheus-style export and thresholds to MonitoringService.


