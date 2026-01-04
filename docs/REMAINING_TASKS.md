# Remaining Tasks & Technical Debt

> **Last Updated**: 2026-01-04
> **Status**: Production Ready (v2.13.1) with identified improvement areas

This document tracks remaining TODOs, incomplete features, test gaps, and roadmap items for the Printernizer project.

---

## 🔴 HIGH PRIORITY - Functional Gaps

### ✅ 1. Job Update API (COMPLETED)

**Status**: ✅ **FULLY IMPLEMENTED** (since v2.11+)
**Impact**: Feature is working correctly

**Implementation**:
- ✅ Backend endpoint: `PUT /api/v1/jobs/{id}` (fully functional)
- ✅ Service layer: `JobService.update_job()` with validation
- ✅ Repository: `JobRepository.update()`
- ✅ Frontend: Full implementation in `jobs.js:1080-1140`
- ✅ WebSocket events: `job_updated` emitted on changes

**Editable Fields**:
- Job name, status, is_business, customer_name, notes, file_name, printer_id

**Verification**:
- Outdated TODO comment already removed from code
- Feature tested and working in production

**Reference**: See `docs/plans/JOB_UPDATE_API_STATUS.md` for complete analysis

---

### 2. Job Status Update Tests (CRITICAL)

**Status**: ⚠️ Endpoint EXISTS, Tests SKIPPED
**Impact**: HIGH - Test coverage gap for critical functionality

**Current State**:
- ✅ Endpoint `PUT /api/v1/jobs/{id}/status` EXISTS and works (verified in test code)
- ❌ 6 tests skipped due to missing validation/safety features
- ⚠️ Edge cases and safety checks need implementation

**Location**:
- Tests: `tests/backend/test_api_jobs.py`
  - Line 647: Active job deletion protection
  - Line 771: Test fixture database mocking
  - Line 809: Test fixture database mocking
  - Line 836: Service layer mock interception
  - Line 848: Endpoint validation logic
  - Line 907: Job deletion safety checks

**Requirements to Enable Tests**:
1. Implement active job deletion protection (prevent deleting running jobs)
2. Fix test fixture database mocking
3. Add status transition validation with force flag
4. Implement job deletion safety checks
5. Enable and verify all 6 tests pass

**Estimated Effort**: 5-6 hours

**Reference**: See `docs/plans/IMPLEMENTATION_PLAN_2026-01-01.md` for detailed steps

---

### ✅ 3. Material Consumption History (COMPLETED)

**Status**: ✅ **FULLY IMPLEMENTED** (verified 2026-01-01)
**Impact**: Feature is working correctly

**Implementation**:
- ✅ Backend endpoint: `GET /api/v1/materials/consumption/history` (src/api/routers/materials.py:310-338)
- ✅ Service layer: `MaterialService.get_consumption_history()` (src/services/material_service.py:402-486)
- ✅ Complete test suite: 11 test cases in `tests/backend/test_api_materials.py`

**Features**:
- Time-based filtering (days parameter: 1-365)
- Material ID filtering
- Job ID filtering
- Printer ID filtering
- Pagination (limit: 1-1000, page number)
- Response includes: items, total_count, page, limit, total_pages
- Joins with materials table for type/brand/color details

**Verification**:
- All filters tested and working
- Pagination logic verified
- Parameter validation in place
- Comprehensive test coverage

**Reference**: Verified during Sprint 1A implementation

---

## 🟠 MEDIUM PRIORITY - Missing Critical Tests

### Test Coverage Statistics

- **Services Tested**: 50% (20/40 services)
- **API Routers Tested**: 40% (8/20 routers)
- **Printer Implementations**: 100% (4/4)

### ✅ Core Infrastructure Services (Sprint 2 Phase 1 - COMPLETE)

The following critical services now have comprehensive test coverage (2026-01-04):

1. ✅ **event_service.py** - 40 tests
   - Event emission, subscription management
   - Background task handling
   - Service dependencies and integration

2. ✅ **printer_monitoring_service.py** - 52 tests
   - Start/stop monitoring
   - Status updates and callbacks
   - Auto-job creation logic
   - File discovery and download

3. ✅ **config_service.py** - 32 tests
   - Config loading and validation
   - Printer configuration management
   - Path validation
   - Environment variable loading

4. ✅ **business_service.py** - 57 tests
   - German VAT calculations (19%)
   - Currency formatting and rounding
   - Timezone handling (Berlin)
   - Business hours calculations
   - Financial precision validation

### Core Infrastructure Services (Still Pending)

5. **printer_control_service.py** (MEDIUM)
   - Printer control commands (pause/resume/stop)
   - Direct user-facing functionality
   - **Risk**: Commands may fail without validation

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
| Service Tests | 50% | 50% | ✅ Improved |
| API Router Tests | 40% | 60% | ⚠️ Needs Work |
| Frontend Features | 85% | 15% | ✅ Good |

### Active Technical Debt

- **High Priority**: 0 items ✅
- **Medium Priority**: 8 items (Remaining untested services)
- **Low Priority**: 5 items (Polish and enhancements)
- **Cleanup**: 2 items (Deprecated code)
- **Completed**: 6 items (Job Update API ✅, Material Consumption History ✅, Sprint 2 Phase 1 ✅)

### Total Estimated Effort

- **Critical Fixes**: 0 hours ✅
- **Test Coverage**: 10-15 hours (reduced from 20-30h - Phase 1 complete)
- **Feature Completion**: 20-30 hours
- **Polish & Cleanup**: 10-15 hours

**Total**: ~40-60 hours of development work (down from original 60-90h)

**Progress**: Sprint 1A, Sprint 1B, and Sprint 2 Phase 1 completed (2026-01-04)

---

## 🎯 Recommended Priorities

### Sprint 1: Critical Functionality ✅ COMPLETE
1. ~~Job Update API implementation~~ ✅ **COMPLETE**
2. ~~Material Consumption History endpoint~~ ✅ **COMPLETE** (verified 2026-01-01)
3. ~~Job Status Update tests~~ ✅ **COMPLETE** (Sprint 1B)

### Sprint 2 Phase 1: Core Service Tests ✅ COMPLETE (2026-01-04)
1. ✅ event_service tests (40 tests)
2. ✅ printer_monitoring_service tests (52 tests)
3. ✅ config_service tests (32 tests)
4. ✅ business_service tests (57 tests)

**Total: 181 tests passing**

### Sprint 2 Phase 2: Feature Service Tests (Planned)
1. FileWatcherService tests
2. FileUploadService tests
3. CameraSnapshotService tests
4. SearchService tests
5. MaterialService tests

### Sprint 3: Feature Polish (Planned)
1. Notification deduplication
2. Connection progress indicator
3. Debug log table format

### Sprint 4: Cleanup & Optimization (Planned)
1. Remove deprecated code
2. Fix flaky tests
3. Code review and refactoring

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
