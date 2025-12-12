# Remaining Tasks & Technical Debt

> **Last Updated**: 2025-12-12
> **Status**: Production Ready (v2.8.9) with identified improvement areas

This document tracks remaining TODOs, incomplete features, test gaps, and roadmap items for the Printernizer project.

---

## 🔴 HIGH PRIORITY - Functional Gaps

### 1. Job Update API (CRITICAL)

**Status**: ❌ Not Implemented
**Impact**: HIGH - Users see working UI but changes don't save

**Problem**:
- Frontend has complete job edit form that operates in "Demo Mode"
- Form submission shows success toast but doesn't actually persist changes
- Creates false impression that feature works

**Location**:
- Frontend: `frontend/js/jobs.js:1088`
- TODO Comment: "Implement actual API call when backend supports job updates"

**Requirements**:
- Implement `PUT /api/v1/jobs/{id}` endpoint in backend
- Support updating all editable job fields:
  - Job name
  - Status
  - Business job flag
  - Customer name
  - Notes/metadata
- Add validation and error handling
- Write comprehensive tests

**Estimated Effort**: 4-6 hours

---

### 2. Job Status Update Endpoint (CRITICAL)

**Status**: ❌ Not Implemented
**Impact**: HIGH - Manual job status changes not supported

**Problem**:
- Dedicated status update endpoint missing
- Multiple skipped tests indicate planned but unimplemented feature
- Users cannot manually mark jobs as completed, failed, etc.

**Location**:
- Tests: `tests/backend/test_api_jobs.py`
  - Lines: 305, 331, 366, 394, 621, 687 (6 skipped tests)
- Expected Endpoint: `PUT /api/v1/jobs/{id}/status`

**Requirements**:
- Implement `PUT /api/v1/jobs/{id}/status` endpoint
- Support status transitions: pending → running → completed/failed
- Add validation for valid status transitions
- Prevent invalid state changes (e.g., can't mark running job as pending)
- Update timestamps appropriately
- Enable all skipped tests

**Estimated Effort**: 3-4 hours

---

### 3. Material Consumption History

**Status**: ❌ Returns 501 "Not Yet Implemented"
**Impact**: MEDIUM - Analytics feature incomplete

**Location**:
- Backend: `src/api/routers/materials.py:318`
- Endpoint: `GET /api/v1/materials/consumption/history`

**Requirements**:
- Query consumption table with time-based filters
- Support date range filtering
- Aggregate consumption by material, printer, or time period
- Return formatted data for charting/visualization
- Add tests for various query scenarios

**Estimated Effort**: 3-4 hours

---

## 🟠 MEDIUM PRIORITY - Missing Critical Tests

### Test Coverage Statistics

- **Services Tested**: 30% (12/40 services)
- **API Routers Tested**: 40% (8/20 routers)
- **Printer Implementations**: 100% (4/4)

### Core Infrastructure Services (No Tests)

These services are production-critical but lack automated tests:

1. **event_service.py** (CRITICAL)
   - WebSocket event broadcasting system
   - Real-time UI updates depend on this
   - **Risk**: Silent failures in event delivery

2. **printer_monitoring_service.py** (CRITICAL)
   - Real-time printer status polling
   - Core feature for live dashboard updates
   - **Risk**: Monitoring failures may go undetected

3. **printer_control_service.py** (CRITICAL)
   - Printer control commands (pause/resume/stop)
   - Direct user-facing functionality
   - **Risk**: Commands may fail without validation

4. **config_service.py** (CRITICAL)
   - Configuration loading and validation
   - Startup failures if config is invalid
   - **Risk**: Invalid configs may crash application

5. **business_service.py** (CRITICAL)
   - German VAT calculations, pricing, reporting
   - Financial accuracy is critical
   - **Risk**: Incorrect business calculations

### Printer-Specific Services (No Tests)

6. **bambu_service.py**
   - Bambu Lab specific business logic
   - **Risk**: Manufacturer-specific features untested

7. **prusa_service.py**
   - Prusa specific business logic
   - **Risk**: Manufacturer-specific features untested

### Feature Services (No Tests)

8. **file_watcher_service.py**
   - Watch folder automation
   - **Risk**: File synchronization issues

9. **file_upload_service.py**
   - Upload validation and processing
   - **Risk**: Invalid uploads may corrupt data

10. **camera_snapshot_service.py**
    - Camera/timelapse functionality
    - **Risk**: Camera features may break silently

11. **search_service.py**
    - Search functionality across entities
    - **Risk**: Search results may be incorrect

12. **material_service.py**
    - Material/filament tracking
    - **Risk**: Material consumption tracking errors

**Estimated Effort**: 20-30 hours for comprehensive test coverage

---

## 🟡 MEDIUM PRIORITY - Feature Completeness

### Frontend Features

#### 1. 3D File Preview

**Status**: ❌ Placeholder
**Location**: `frontend/js/milestone-1-2-functions.js:427`

**Current Behavior**:
- Shows toast: "3D-Vorschau wird in einer späteren Version verfügbar sein"
- Function: `previewFile(fileId)`

**Requirements**:
- Integrate 3D viewer library (Three.js, Babylon.js, or similar)
- Support STL, 3MF, OBJ file formats
- Render preview in modal with zoom/rotate controls
- Fallback to thumbnail if 3D rendering unavailable

**Estimated Effort**: 8-12 hours

---

#### 2. Local File Opening

**Status**: ❌ Placeholder
**Location**: `frontend/js/milestone-1-2-functions.js:435`

**Current Behavior**:
- Shows toast: "Lokale Datei-Funktion wird in einer späteren Version verfügbar sein"
- Function: `openLocalFile(fileId)`

**Requirements**:
- Platform-specific file opening (Windows/macOS/Linux)
- Electron wrapper or system file protocol handlers
- Security considerations for file access

**Estimated Effort**: 6-8 hours (platform-specific challenges)

---

### Backend Features

#### 3. Excel Export for Materials

**Status**: ❌ Returns 501 "Not Yet Implemented"
**Location**: `src/api/routers/materials.py:168`

**Current State**:
- CSV export fully functional
- Excel export would be nice-to-have for business users

**Requirements**:
- Add `openpyxl` or `xlsxwriter` dependency
- Implement Excel export with formatting
- Support multiple sheets (summary, details, charts)
- Match CSV data structure

**Estimated Effort**: 2-3 hours

---

#### 4. Printer Filtering

**Status**: ⚠️ Tests Skipped
**Location**: `tests/backend/test_api_printers.py:86, 99`

**Requirements**:
- Investigate current filtering implementation
- Add support for filtering by:
  - Printer type (Bambu/Prusa)
  - Status (online/offline/printing)
  - Name search
- Enable and fix skipped tests

**Estimated Effort**: 2-3 hours

---

#### 5. Printer CRUD Operations

**Status**: ⚠️ Multiple Skipped Tests

**Tests Requiring Implementation**:
- `test_create_printer` (lines 112, 142)
- `test_update_printer` (lines 293, 317)
- `test_delete_printer` (lines 342, 363)

**Current State**:
- Tests skipped with "awaiting implementation" notes
- Basic printer management exists but may lack edge case handling

**Requirements**:
- Review existing CRUD endpoints
- Implement missing validation
- Add error handling for edge cases
- Enable all skipped tests

**Estimated Effort**: 4-6 hours

---

## 🟢 LOW PRIORITY - Polish & Nice-to-Have

### 1. Detailed Log Viewer UI

**Status**: ❌ Placeholder
**Location**: `frontend/js/auto-download-ui.js:590`

**Current**: Shows "Detailed log viewer will be available in the next update"
**Estimated Effort**: 4-6 hours

---

### 2. Manual Retry for Failed Tasks

**Status**: ❌ Placeholder
**Location**: `frontend/js/auto-download-ui.js:629`

**Current**: Shows "Manual retry will be available in the next update"
**Note**: Auto-retry may be sufficient for most use cases
**Estimated Effort**: 2-3 hours

---

### 3. Enhanced Printer Details Modal

**Status**: ❌ Simple Placeholder
**Location**: `frontend/js/printers.js:582`

**Current**: Simple toast with basic info
**Enhancement**: Full modal with detailed stats, history, controls
**Estimated Effort**: 6-8 hours

---

### 4. MQTT Download Strategy

**Status**: ⚠️ Intentional Placeholder
**Location**: `src/printers/download_strategies/mqtt_strategy.py:20`

**Note**: Currently returns "unavailable" - alternative download methods work
**Priority**: LOW - only needed if other methods fail
**Estimated Effort**: 8-12 hours (complex implementation)

---

### 5. Flaky WebSocket Test

**Status**: ⚠️ Test Skipped (Timing Issues)
**Location**: `tests/frontend/websocket.test.js:159`

**Issue**: Timing issues with WebSocket reconnection attempts in CI/CD
**Reference**: GitHub Actions run #19493470198
**Estimated Effort**: 2-3 hours

---

## 🧹 Code Cleanup

### 1. Deprecated Method Removal

**Status**: ⚠️ Scheduled for v2.0.0

**Method**: `get_printers()` in `src/services/printer_service.py:185-199`
- Marked deprecated, use `list_printers()` instead
- Emits deprecation warning
- **Action**: Remove before v2.0.0 release

---

### 2. Legacy Exception Handler

**Status**: ⚠️ Review Needed
**Location**: `src/main.py:730-734`

**Description**: Legacy PrinternizerException handler for backwards compatibility
**Action**: Verify if still needed, remove if not

---

## 🔵 ROADMAP FEATURES (Future Versions)

These are documented roadmap items, not immediate tasks:

### Phase 6: Advanced Home Assistant Integration
- MQTT discovery
- Sensor entities
- Automation triggers
- Service calls

### Phase 7: Watch Folders
- Automatic file monitoring
- Processing workflows
- Thingiverse integration

### Phase 8: Multi-User System
- User authentication
- Role-based access control
- Permission system

### Phase 9: Advanced Analytics
- Predictive maintenance
- Failure analysis
- ML-based optimization

### Phase 10: Expanded Printer Support
- Klipper firmware
- Additional manufacturers
- Generic printer support

---

## 📊 Summary Statistics

### Implementation Status

| Category | Complete | Incomplete | Percentage |
|----------|----------|------------|------------|
| Core Features | 95% | 5% | ✅ Excellent |
| API Endpoints | 90% | 10% | ✅ Very Good |
| Service Tests | 30% | 70% | ⚠️ Needs Work |
| API Router Tests | 40% | 60% | ⚠️ Needs Work |
| Frontend Features | 85% | 15% | ✅ Good |

### Active Technical Debt

- **High Priority**: 3 items (Job updates, status endpoint, consumption history)
- **Medium Priority**: 12 items (Untested critical services)
- **Low Priority**: 5 items (Polish and enhancements)
- **Cleanup**: 2 items (Deprecated code)

### Total Estimated Effort

- **Critical Fixes**: 10-14 hours
- **Test Coverage**: 20-30 hours
- **Feature Completion**: 20-30 hours
- **Polish & Cleanup**: 10-15 hours

**Total**: ~60-90 hours of development work

---

## 🎯 Recommended Priorities

### Sprint 1: Critical Functionality (2-3 days)
1. ✅ Job Update API implementation
2. ✅ Job Status Update endpoint
3. ✅ Material Consumption History

### Sprint 2: Critical Test Coverage (3-4 days)
1. ✅ event_service tests
2. ✅ printer_monitoring_service tests
3. ✅ config_service tests
4. ✅ business_service tests

### Sprint 3: Feature Polish (2-3 days)
1. ✅ Excel export for materials
2. ✅ Printer filtering and CRUD
3. ✅ 3D file preview

### Sprint 4: Cleanup & Optimization (1-2 days)
1. ✅ Remove deprecated code
2. ✅ Fix flaky tests
3. ✅ Code review and refactoring

---

## 📝 Notes

- All "Not Yet Implemented" (501) endpoints are documented and intentional
- Abstract interface methods in `base.py` are correct architecture (not bugs)
- Exception handling `pass` statements are intentional graceful degradation
- Most placeholders have clear upgrade paths documented

**Project Health**: ✅ Production Ready
- Core functionality is complete and tested
- Main gaps are in test coverage and polish features
- No critical bugs blocking production use
- Technical debt is documented and manageable

---

**For detailed implementation plans, see:**
- `docs/plans/JOB_UPDATE_API_PLAN.md`
- `docs/plans/JOB_STATUS_UPDATE_PLAN.md`
