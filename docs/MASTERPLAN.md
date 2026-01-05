# Printernizer Development Masterplan

**Last Updated**: 2026-01-05
**Current Version**: v2.14.3
**Status**: Production Ready

---

## Quick Status Overview

| Category | Status | Completion |
|----------|--------|------------|
| Core Features | Production Ready | 98% |
| Printer Support | Bambu + Prusa | 100% |
| Test Coverage | Excellent | ~90% |
| Sprint 1 (P1 Tasks) | Complete | 100% |
| Sprint 2 Phase 1 (Service Tests) | Complete | 100% |
| Sprint 2 Phase 2 (Feature Tests) | Complete | 100% |
| Sprint 2 Phase 3 (Printer Tests) | Complete | 100% |
| Sprint 3 (Frontend Polish) | Complete | 100% |
| Usage Statistics | Phase 2 Complete | 66% |

---

## Table of Contents

1. [Completed Work](#completed-work)
2. [In Progress](#in-progress)
3. [Priority 1 - Critical](#priority-1---critical)
4. [Priority 2 - Test Coverage](#priority-2---test-coverage)
5. [Priority 3 - Frontend Polish](#priority-3---frontend-polish)
6. [Priority 4 - Nice to Have](#priority-4---nice-to-have)
7. [Future Roadmap](#future-roadmap)
8. [Technical Debt](#technical-debt)
9. [Reference](#reference)

---

## Completed Work

### Sprint 1A - Job API (2026-01-01) ✅

- [x] **Material Consumption History** - Verified fully implemented
  - Endpoint: `GET /api/v1/materials/consumption/history`
  - Location: `src/api/routers/materials.py:310-338`
  - Features: Time filtering, pagination, material/job/printer filtering

- [x] **Job Status Update Tests** - All 7 tests passing
  - Endpoint: `PUT /api/v1/jobs/{id}/status`
  - Status transition validation implemented

- [x] **Active Job Deletion Protection** - Implemented
  - Location: `src/services/job_service.py:232-271`
  - Returns 409 Conflict for active jobs

- [x] **Test Infrastructure Fixed**
  - Fixed 5 failing tests (list_jobs → list_jobs_with_count)
  - Enabled 2 high-priority skipped tests
  - Test pass rate: 64.5% → 87.1%

### Sprint 1B - Printer API (2026-01-01) ✅

- [x] **Printer Filtering Support** - Implemented
  - Query params: `printer_type`, `is_active`, `status`
  - Location: `src/api/routers/printers.py:166-209`

- [x] **Printer Deletion Protection** - Implemented
  - Location: `src/services/printer_service.py:842-887`
  - Prevents deletion with active jobs (supports `force=true`)

- [x] **Printer CRUD Tests** - 11/13 enabled (85%)
  - Filtering tests: 2/2 ✅
  - Create printer tests: 2/2 ✅
  - Update printer test: 1/1 ✅
  - Delete printer tests: 2/2 ✅
  - Test connection tests: 2/2 ✅

### Recent Features (v2.10.0 - v2.13.1) ✅

- [x] **v2.13.1** - Fixed printer auto-detection duplicates
- [x] **v2.13.0** - Excel export for materials inventory
- [x] **v2.12.2** - Fixed Prusa job display from PrusaLink v1 API
- [x] **v2.12.1** - Improved Prusa camera detection with fallback
- [x] **v2.12.0** - Filament display in printer tiles (AMS support)
- [x] **v2.11.x** - Setup wizard, camera diagnostics, mobile layout
- [x] **v2.10.0** - Prusa webcam support via PrusaLink Camera API

### Core Features (Phases 1-5) ✅

- [x] **Printer Integration** - Bambu Lab (MQTT) + Prusa (HTTP API)
- [x] **Real-time Monitoring** - WebSocket live updates
- [x] **Job Tracking** - Complete job lifecycle management
- [x] **File Management** - Unified browser, downloads, status tracking
- [x] **3D Preview System** - STL, 3MF, GCODE, BGCODE rendering
- [x] **Timelapse Management** - FlickerFree integration, gallery UI
- [x] **Library System** - Centralized file library with metadata
- [x] **Material Tracking** - Inventory, consumption, cost tracking
- [x] **Business Features** - VAT, analytics, German compliance
- [x] **Auto-Job Creation** - Detect prints automatically
- [x] **Setup Wizard** - Guided first-run configuration

### Usage Statistics (v2.7.0) ✅

- [x] **Phase 1**: Local collection, UI, opt-in/opt-out
- [x] **Phase 2**: Aggregation service, HTTP submission, scheduler
- [ ] **Phase 3**: Analytics dashboard (planned)

---

## In Progress

> No tasks currently in progress. Ready for next sprint.

### Documentation Cleanup ✅ COMPLETE (2026-01-05)

- [x] Consolidate duplicate plan files
- [x] Archive completed sprint reports
- [x] Update README with current features

---

## Priority 1 - Critical

> **Status**: All P1 tasks complete as of Sprint 1 ✅

### Remaining Minor Items

#### Skipped Tests (Low Priority)

**Job API** (4 skipped - defer to future):
- [ ] `test_large_job_list_performance` - Load testing
- [ ] `test_job_filtering_performance` - Filter benchmarks
- [ ] `test_job_api_database_connection_error` - DB failure scenarios
- [ ] `test_job_creation_with_invalid_printer` - Invalid printer validation

**Printer API** (2 skipped - complex mocking):
- [ ] `test_get_printer_status_bambu_lab` - Requires printer instance mocking
- [ ] `test_get_printer_status_prusa` - Requires printer instance mocking

**Recommendation**: Address during Sprint 2 test coverage work

---

## Priority 2 - Test Coverage

> **Current**: ~90% service coverage | **Target**: 80% ✅ EXCEEDED

### Sprint 2 Phase 1: Core Service Tests ✅ COMPLETE (2026-01-04)

**Actual Effort**: Approximately 6-8 hours (under budget)

#### EventService (`src/services/event_service.py`) ✅
- [x] Created `tests/services/test_event_service.py` - **40 tests**
- [x] Test event emission
- [x] Test subscription management
- [x] Test concurrent subscribers
- [x] Test error handling in delivery
- [x] Test background task tracking
- [x] Test service dependencies

#### PrinterMonitoringService (`src/services/printer_monitoring_service.py`) ✅
- [x] Created `tests/services/test_printer_monitoring_service.py` - **52 tests**
- [x] Test start/stop monitoring
- [x] Test status polling
- [x] Test status change detection
- [x] Test error recovery
- [x] Test auto-job creation logic
- [x] Test file discovery and download

#### ConfigService (`src/services/config_service.py`) ✅
- [x] Created `tests/services/test_config_service.py` - **32 tests**
- [x] Test config loading
- [x] Test validation
- [x] Test environment overrides
- [x] Test default values
- [x] Test path validation
- [x] Test printer configuration management

#### BusinessService (`src/services/business_service.py`) ✅
- [x] Created `tests/services/test_business_service.py` - **57 tests**
- [x] Test VAT calculations (German 19%)
- [x] Test currency formatting and rounding
- [x] Test EUR formatting
- [x] Test financial precision (2 decimal places)
- [x] Test Berlin timezone handling
- [x] Test business hours calculations
- [x] Test DST transitions

**Total: 181 tests passing**

### Sprint 2 Phase 2: Feature Service Tests ✅ COMPLETE (2026-01-04)

**Actual Effort**: Completed alongside Phase 1

#### FileWatcherService (`src/services/file_watcher_service.py`) ✅
- [x] Created `tests/services/test_file_watcher_service.py` - **41 tests**
- [x] Test file filtering and extensions
- [x] Test watch folder management
- [x] Test file event handling (create, modify, delete, move)
- [x] Test debouncing and scanning
- [x] Test library integration

#### CameraSnapshotService (`src/services/camera_snapshot_service.py`) ✅
- [x] Created `tests/services/test_camera_snapshot_service.py` - **29 tests**
- [x] Test image format detection
- [x] Test cache lifecycle and expiration
- [x] Test snapshot retrieval and caching
- [x] Test concurrent access handling

#### FileUploadService (`src/services/file_upload_service.py`) ✅
- [x] Created `tests/services/test_file_upload_service.py` - **29 tests**
- [x] Test file validation and extensions
- [x] Test duplicate detection
- [x] Test file saving and hash calculation
- [x] Test post-upload processing
- [x] Test multi-file uploads

#### SearchService (`src/services/search_service.py`) ✅
- [x] Created `tests/services/test_search_service.py` - **48 tests**
- [x] Test cache management
- [x] Test relevance scoring
- [x] Test filter application
- [x] Test unified search
- [x] Test search history and suggestions

#### MaterialService (`src/services/material_service.py`) ✅
- [x] Created `tests/services/test_material_service.py` - **27 tests**
- [x] Test CRUD operations
- [x] Test material filtering
- [x] Test consumption tracking
- [x] Test statistics and reporting
- [x] Test CSV/Excel export

**Total Phase 2: 174 tests passing**

### Sprint 2 Phase 3: Printer Service Tests ✅ COMPLETE (2026-01-04)

**Actual Effort**: Approximately 4-5 hours (on budget)

#### BambuLabPrinter (`src/printers/bambu_lab.py`) ✅
- [x] Created `tests/printers/test_bambu_lab.py` - **47 tests**
- [x] Test initialization (bambulabs_api and MQTT fallback)
- [x] Test connection management
- [x] Test status retrieval and mapping
- [x] Test job information
- [x] Test file operations (FTP, MQTT, downloads)
- [x] Test print control (pause/resume/stop)
- [x] Test camera functionality
- [x] Test helper methods

#### PrusaPrinter (`src/printers/prusa.py`) ✅
- [x] Created `tests/printers/test_prusa.py` - **42 tests**
- [x] Test initialization with PrusaLink HTTP API
- [x] Test connection with retry logic
- [x] Test status retrieval via HTTP
- [x] Test job information
- [x] Test file operations and downloads
- [x] Test print control operations
- [x] Test camera and thumbnail functionality
- [x] Test error handling (auth, timeouts, forbidden)

#### PrinterControlService (`src/services/printer_control_service.py`) ✅
- [x] Created `tests/services/test_printer_control_service.py` - **35 tests**
- [x] Test service initialization
- [x] Test pause/resume/stop operations
- [x] Test monitoring control
- [x] Test event emissions
- [x] Test error handling
- [x] Test auto-connection logic

**Total Phase 3: 124 tests passing**

---

## Priority 3 - Frontend Polish

> **Status**: Sprint 3 Complete ✅ (v2.13.3)

### Notification System Issues ✅ COMPLETE

- [x] **Duplicate Notifications** (v2.13.3)
  - Implemented message-based deduplication with 3-second cooldown
  - Same notification won't appear multiple times within cooldown

- [x] **Backend Offline Detection** (v2.13.3)
  - Added actual health endpoint check
  - Shows "Backend Offline" or "Backend not reachable" on connectivity failure

### Printer Dashboard Improvements ✅ COMPLETE

- [x] **Connection Progress Indicator** (v2.13.3)
  - Grey overlay with shimmer animation during connection
  - Connection type indicator (MQTT/HTTP) in printer tile header
  - Visual feedback for connecting/connected/disconnected states

- [x] **Camera Preview Placeholder** (v2.13.3)
  - Shows camera icon with "Keine Vorschau" text
  - Graceful fallback on image load errors

### Debug Page Improvements ✅ COMPLETE

- [x] **Log Table Format** (v2.13.3)
  - Logs display in proper HTML table with columns
  - Added sticky header, hover states, level-based highlighting

### Library Features (Deferred to Future Sprint)

- [ ] **Custom Tags for Files**
  - Add tags column to library_files table
  - Add tag management API endpoints
  - Add frontend tag picker UI
  - Effort: 4-6 hours

---

## Priority 4 - Nice to Have

### 3D File Preview (Interactive)

**Status**: Placeholder showing "3D-Vorschau wird in einer späteren Version verfügbar sein"
**Location**: `frontend/js/milestone-1-2-functions.js:427`

**Options**:
- **Option A**: Three.js integration (8-12 hours, ~600KB)
- **Option B**: Use existing thumbnails + metadata (2 hours)
- **Recommendation**: Defer or use Option B

### Local File Opening

**Status**: Placeholder
**Location**: `frontend/js/milestone-1-2-functions.js:435`
**Challenge**: Browser security prevents direct file access

**Options**:
- Electron wrapper (10-15 hours)
- Custom protocol handler (15-20 hours)
- **Recommendation**: Defer (low ROI)

### Enhanced Printer Details Modal

**Status**: Simple toast with basic info
**Location**: `frontend/js/printers.js:582`
**Enhancement**: Full modal with specs, history, controls
**Effort**: 6-8 hours

### Detailed Log Viewer

**Status**: Placeholder
**Location**: `frontend/js/auto-download-ui.js:590`
**Enhancement**: Rich viewer with filtering, search, export
**Effort**: 4-6 hours

---

## Future Roadmap

### Phase 6: Advanced Home Assistant Integration
- [ ] MQTT discovery
- [ ] Sensor entities for printer status
- [ ] Automation triggers (print_started, print_completed)
- [ ] Service calls (start_print, pause_print)
- **Effort**: 15-20 hours

### Phase 7: Watch Folders Enhancement
- [ ] Processing workflows (auto-slice, auto-upload)
- [ ] Thingiverse/Printables integration
- [ ] Auto-tagging based on folder structure
- [ ] Duplicate detection
- **Effort**: 20-25 hours

### Phase 8: Multi-User System
- [ ] User authentication (JWT)
- [ ] Role-based access control
- [ ] Permission system (admin, operator, viewer)
- [ ] User activity logging
- **Effort**: 30-40 hours

### Phase 9: Advanced Analytics
- [ ] Predictive maintenance (based on print hours)
- [ ] Failure pattern analysis
- [ ] ML-based optimization suggestions
- [ ] Cost forecasting
- **Effort**: 40-50 hours

### Phase 10: Expanded Printer Support
- [ ] Klipper firmware (via Moonraker API)
- [ ] Creality (via Cloud API)
- [ ] Anycubic
- [ ] Generic OctoPrint
- **Effort**: 10-15 hours per manufacturer

### Usage Statistics Phase 3
- [ ] Analytics dashboard
- [ ] Key metrics visualization
- [ ] Trend analysis
- [ ] Anomaly detection
- **Effort**: 2 weeks

---

## Technical Debt

### Code Cleanup

- [x] **Remove Deprecated Method** (v2.14.1)
  - Removed `get_printers()` from `src/services/printer_service.py`
  - Replaced by `list_printers()` throughout codebase

- [x] **Review Legacy Exception Handler** (v2.14.1)
  - Fixed inconsistent error response format
  - Changed `"error"` field to `"error_code"` for consistency
  - Documented ongoing migration to PrinternizerError

- [x] **Fix Flaky WebSocket Test** (v2.14.1)
  - Fixed undefined `testUtils` reference bug
  - Implemented Jest fake timers for deterministic timing
  - Test now passes reliably in CI/CD

### Environment Configuration ✅ COMPLETE

- [x] **Clean up .env/.env.sample** (v2.14.1)
  - Added clear legend: [REQUIRED], [OPTIONAL], [UNUSED], [INTERNAL]
  - Organized into 13 logical sections with descriptive headers
  - Documented default values inline
  - Marked unused/planned features explicitly

### Platform Compatibility

- [ ] **Watchdog Observer Thread (Windows)**
  - Issue: Threading compatibility, using PollingObserver fallback
  - Priority: LOW (workaround in place)

- [ ] **Bambu FTP Connection Timeouts**
  - Issue: Initial attempts fail, retry works
  - Location: `src/services/bambu_ftp_service.py`
  - Priority: MEDIUM

- [ ] **Bambu MQTT Connection Instability**
  - Issue: Multiple timeout/reconnect cycles
  - Location: `src/printers/bambu_lab.py`
  - Priority: MEDIUM

### Database Improvements

- [ ] Database connection pooling optimization
- [ ] Query performance monitoring
- [ ] Index usage analysis
- [ ] Migration system hardening (checksums)

---

## Reference

### Project Structure

```
/src/              # Backend source code
/frontend/         # Frontend source code
/migrations/       # Database migrations
/tests/            # Test suite
/docs/             # Documentation
  /plans/          # Sprint plans and reports
  /development/    # Technical docs
/.claude/          # Claude Code configuration
```

### Key Files

| File | Purpose |
|------|---------|
| `src/main.py` | Application entry point, version |
| `CHANGELOG.md` | Version history |
| `CONTRIBUTING.md` | Contribution guidelines |
| `RELEASE.md` | Release process |

### Test Commands

```bash
# Run all backend tests
python3 -m pytest tests/backend/ -v

# Run specific test file
python3 -m pytest tests/backend/test_api_jobs.py -v

# Run with coverage
python3 -m pytest --cov=src tests/
```

### Deployment Methods

1. **Python Standalone** (Development)
2. **Docker Standalone** (Testing)
3. **Home Assistant Add-on** (Production)
4. **Raspberry Pi** (Production Alternative)

### Branch Strategy

- **master**: Production releases
- **development**: Integration testing
- Feature branches → development → master

---

## Sprint History

| Sprint | Date | Focus | Status |
|--------|------|-------|--------|
| 1A | 2026-01-01 | Job API, Test Fixes | ✅ Complete |
| 1B | 2026-01-01 | Printer API, Filtering | ✅ Complete |
| 2 Phase 1 | 2026-01-04 | Core Service Tests | ✅ Complete |
| 2 Phase 2 | 2026-01-04 | Feature Service Tests | ✅ Complete |
| 2 Phase 3 | 2026-01-04 | Printer Service Tests | ✅ Complete |
| 3 | 2026-01-04 | Frontend Polish | ✅ Complete |

### Sprint 1 Summary

- **Time**: 7-8 hours (vs 16-19h estimate)
- **Efficiency**: 58% under budget
- **Test Improvement**: +47% pass rate
- **Key Finding**: Most P1 features already implemented

### Sprint 2 Phase 1 Summary

- **Date**: 2026-01-04
- **Tests Added**: 181 tests (EventService, PrinterMonitoringService, ConfigService, BusinessService)
- **Result**: All 181 tests passing
- **Services Covered**: 4 critical infrastructure services
- **Test Coverage Improvement**: ~30% → ~50% service coverage

### Sprint 2 Phase 2 Summary

- **Date**: 2026-01-04
- **Tests Added**: 174 tests (FileWatcher, CameraSnapshot, FileUpload, Search, Material)
- **Result**: All 174 tests passing (179 total with fixtures)
- **Services Covered**: 5 feature services
- **Test Coverage Improvement**: ~50% → ~85% service coverage

### Sprint 2 Phase 3 Summary

- **Date**: 2026-01-04
- **Tests Added**: 124 tests (BambuLabPrinter, PrusaPrinter, PrinterControlService)
- **Result**: All 124 tests passing
- **Components Covered**: 2 printer integrations + 1 control service
- **Test Coverage Improvement**: ~85% → ~90% service coverage
- **Combined Sprint 2 Total**: 479 new tests (181 + 174 + 124)

### Sprint 3 Summary

- **Date**: 2026-01-04 (v2.13.3)
- **Focus**: Frontend polish and UX improvements
- **Completed Items**:
  - Duplicate notification fix with deduplication
  - Backend offline detection for auto-download status
  - Debug log table format with proper columns
  - Printer connection progress indicator
  - Camera preview placeholder
- **Status**: All 5 priority items completed

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 7.0 | 2026-01-05 | Sprint 3 completion, doc cleanup, README update |
| 6.0 | 2026-01-04 | Sprint 2 Phase 3 completion (479 total Sprint 2 tests) |
| 5.0 | 2026-01-04 | Sprint 2 Phase 2 completion (355 total service tests) |
| 4.0 | 2026-01-04 | Sprint 2 Phase 1 completion (181 service tests) |
| 3.0 | 2026-01-03 | Consolidated from multiple docs |
| 2.0 | 2026-01-01 | Sprint 1A/1B completion |
| 1.0 | 2026-01-01 | Initial masterplan |

---

## Archived Documents

The following documents have been consolidated into this masterplan:
- `docs/plans/IMPLEMENTATION_PLAN_2026-01-01.md`
- `docs/plans/SPRINT_1A_STATUS.md`
- `docs/plans/SPRINT_1A_FINAL_REPORT.md`
- `docs/plans/SPRINT_1B_PLAN.md`
- `docs/plans/SPRINT_1B_FINAL_REPORT.md`
- `docs/plans/SPRINT_2_PHASE_1_PLAN.md`
- `docs/REMAINING_TASKS.md`
- `docs/development/todos.md`
- `docs/development/root-todos.md`
- `docs/development/development-plan.md`
- `docs/development/CURRENT_STATE.md`
- `PR_DESCRIPTION.md`

These can be kept for reference or archived.

---

**End of Masterplan**

*This is a living document. Update as work progresses.*
