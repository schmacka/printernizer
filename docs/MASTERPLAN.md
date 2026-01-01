# Printernizer Development Masterplan

**Last Updated**: 2026-01-01
**Current Version**: v2.11.6
**Status**: Production Ready with Identified Improvement Areas

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Critical Priorities](#critical-priorities)
3. [Medium Priority - Test Coverage](#medium-priority---test-coverage)
4. [User-Facing Issues](#user-facing-issues)
5. [Feature Completeness](#feature-completeness)
6. [Code Quality & Cleanup](#code-quality--cleanup)
7. [Future Roadmap](#future-roadmap)
8. [Project Health Metrics](#project-health-metrics)

---

## Executive Summary

Printernizer is **production-ready** with 95% core feature completion. The main gaps are:
- **Test coverage** for critical services (30% vs target 80%)
- **Frontend polish** issues (notifications, UI feedback)
- **Documentation updates** (outdated TODO comments)

### Quick Stats

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Core Features | 95% | 95% | ✅ Met |
| API Endpoints | 90% | 95% | ⚠️ Close |
| Service Tests | 30% | 80% | ❌ Gap |
| API Router Tests | 40% | 80% | ❌ Gap |
| Frontend Features | 85% | 90% | ⚠️ Close |

### Estimated Remaining Work
- **Critical Fixes**: 8-10 hours
- **Test Coverage**: 20-30 hours
- **Feature Completion**: 15-20 hours
- **Polish & Cleanup**: 8-12 hours
- **Total**: ~50-70 hours

---

## Critical Priorities

### 🔴 Priority 1: Backend Endpoints (8-10 hours)

#### 1.1 Material Consumption History ⚠️
**Status**: Returns 501 "Not Yet Implemented"
**Impact**: Analytics feature incomplete
**Location**: `src/api/routers/materials.py:318`

**Endpoint**: `GET /api/v1/materials/consumption/history`

**Requirements**:
- Query consumption table with time-based filters
- Support date range filtering (`?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`)
- Aggregate by material, printer, or time period
- Return formatted data for charting
- Support grouping: daily, weekly, monthly

**Implementation Plan**:
```python
@router.get("/consumption/history")
async def get_consumption_history(
    material_id: Optional[str] = None,
    printer_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    group_by: str = "day"  # day, week, month
):
    # 1. Query material_consumption table
    # 2. Apply filters (material, printer, date range)
    # 3. Aggregate by time period
    # 4. Return formatted results
```

**Estimated Effort**: 3-4 hours

**Tests Needed**:
- `test_consumption_history_by_material()`
- `test_consumption_history_by_printer()`
- `test_consumption_history_date_range()`
- `test_consumption_history_aggregation()`

---

#### 1.2 Job Status Update Validation ⚠️
**Status**: 6 skipped tests
**Impact**: Manual job status changes not fully validated
**Location**: `tests/backend/test_api_jobs.py` (lines 305, 331, 366, 394, 621, 687)

**Current State**:
- Endpoint `PUT /api/v1/jobs/{id}/status` **exists and works**
- Tests are skipped awaiting edge case handling

**Requirements**:
- Enable all skipped tests
- Ensure transition validation works correctly
- Add comprehensive error messages
- Test force flag behavior
- Validate timestamp updates

**Implementation Plan**:
1. Review skipped tests in `test_api_jobs.py`
2. Implement any missing edge case handling
3. Enable and fix all 6 tests
4. Add integration tests for WebSocket events

**Estimated Effort**: 2-3 hours

**Affected Tests**:
```python
# Line 305: test_update_job_status_invalid_transition
# Line 331: test_update_job_status_force_flag
# Line 366: test_update_job_status_timestamps
# Line 394: test_update_job_status_completion_notes
# Line 621: test_update_job_status_not_found
# Line 687: test_update_job_status_websocket_event
```

---

#### 1.3 Printer CRUD Operations ⚠️
**Status**: Multiple skipped tests
**Impact**: Edge cases in printer management not covered
**Location**: `tests/backend/test_api_printers.py`

**Skipped Tests**:
- `test_create_printer` (lines 112, 142)
- `test_update_printer` (lines 293, 317)
- `test_delete_printer` (lines 342, 363)
- `test_filter_printers` (lines 86, 99)

**Requirements**:
- Review existing CRUD endpoints
- Implement missing validation
- Add error handling for edge cases
- Enable all skipped tests

**Estimated Effort**: 3-4 hours

---

### 🔴 Priority 2: Documentation Cleanup (1-2 hours)

#### 2.1 Remove Outdated TODO Comments ✅

**Job Update API**:
- **File**: `frontend/js/jobs.js:1088`
- **Status**: Backend fully implemented since v2.11+
- **Action**: Remove "TODO: Implement actual API call" comment
- **See**: `docs/plans/JOB_UPDATE_API_STATUS.md` for full details

**Other Outdated TODOs**:
Search for and review:
```bash
grep -r "TODO.*Implement.*API" frontend/js/
```

#### 2.2 Update REMAINING_TASKS.md ✅

**Changes**:
1. Mark Job Update API as ✅ Complete
2. Update test coverage statistics
3. Add completion dates
4. Archive completed items

**Estimated Effort**: 30 minutes

---

## Medium Priority - Test Coverage

### 🟠 Critical Services Without Tests (20-30 hours)

Current test coverage: **30%** (12/40 services)
Target: **80%** (32/40 services)

#### Phase 1: Core Infrastructure (8-10 hours)

##### 1. EventService (`src/services/event_service.py`)
**Priority**: CRITICAL
**Impact**: WebSocket event broadcasting for real-time UI

**Tests Needed**:
```python
# tests/services/test_event_service.py
async def test_emit_event()
async def test_subscribe_to_event()
async def test_unsubscribe_from_event()
async def test_event_delivery()
async def test_concurrent_subscribers()
async def test_event_history()
```

**Estimated Effort**: 2-3 hours

---

##### 2. PrinterMonitoringService (`src/services/printer_monitoring_service.py`)
**Priority**: CRITICAL
**Impact**: Real-time printer status polling

**Tests Needed**:
```python
# tests/services/test_printer_monitoring_service.py
async def test_start_monitoring()
async def test_stop_monitoring()
async def test_poll_printer_status()
async def test_status_change_detection()
async def test_monitoring_interval()
async def test_error_recovery()
async def test_concurrent_monitoring()
```

**Estimated Effort**: 3-4 hours

---

##### 3. ConfigService (`src/services/config_service.py`)
**Priority**: CRITICAL
**Impact**: Configuration loading and validation

**Tests Needed**:
```python
# tests/services/test_config_service.py
def test_load_config()
def test_validate_config()
def test_invalid_config_raises_error()
def test_default_values()
def test_environment_overrides()
def test_config_reload()
```

**Estimated Effort**: 2-3 hours

---

##### 4. BusinessService (`src/services/business_service.py`)
**Priority**: CRITICAL
**Impact**: VAT calculations, pricing (financial accuracy!)

**Tests Needed**:
```python
# tests/services/test_business_service.py
def test_calculate_vat()
def test_calculate_material_cost()
def test_calculate_power_cost()
def test_generate_business_report()
def test_export_accounting_data()
def test_eur_formatting()
```

**Estimated Effort**: 2-3 hours

---

#### Phase 2: Feature Services (6-8 hours)

##### 5. FileWatcherService
**Tests**: Watch folder automation

##### 6. FileUploadService
**Tests**: Upload validation and processing

##### 7. CameraSnapshotService
**Tests**: Camera/timelapse functionality

##### 8. SearchService
**Tests**: Search across entities

##### 9. MaterialService
**Tests**: Material/filament tracking

---

#### Phase 3: Printer Services (4-6 hours)

##### 10. BambuService
**Tests**: Bambu Lab specific logic

##### 11. PrusaService
**Tests**: Prusa specific logic

##### 12. PrinterControlService
**Tests**: Printer commands (pause/resume/stop)

---

## User-Facing Issues

### 🟡 Frontend Issues (Priority 3)

Source: `docs/development/root-todos.md`

#### 3.1 Notification System Issues

**A. Offline Backend Detection ⚠️**
- **Issue**: "Autodownload notification says ready even when backend is offline"
- **Impact**: Users confused about system status
- **Location**: Auto-download system initialization
- **Fix**: Add proper backend connectivity check before showing "ready" status

**Implementation**:
```javascript
// frontend/js/auto-download-init.js
async checkBackendConnectivity() {
    try {
        const response = await fetch('/api/v1/health', {
            timeout: 5000
        });
        return response.ok;
    } catch {
        return false;
    }
}

async showReadyNotification() {
    const isOnline = await this.checkBackendConnectivity();
    if (!isOnline) {
        showToast('error', 'Backend Offline', 'Autodownload nicht verfügbar');
        return;
    }
    showToast('success', 'System bereit', 'Autodownload aktiv');
}
```

**Estimated Effort**: 1-2 hours

---

**B. Duplicate Notifications ⚠️**
- **Issue**: "Too many notifications piling up - multiple of same one"
- **Impact**: Cluttered UI, poor UX
- **Fix**: Implement notification deduplication

**Implementation**:
```javascript
// frontend/js/utils.js
const activeToasts = new Map(); // toast_key -> toast_element

function showToast(type, title, message) {
    const key = `${type}-${title}-${message}`;

    // If same toast already showing, don't create duplicate
    if (activeToasts.has(key)) {
        return;
    }

    const toastEl = createToastElement(type, title, message);
    activeToasts.set(key, toastEl);

    // Remove from tracking when toast closes
    setTimeout(() => {
        activeToasts.delete(key);
    }, 5000);

    document.body.appendChild(toastEl);
}
```

**Estimated Effort**: 1-2 hours

---

#### 3.2 Printer Dashboard Improvements

**A. Connection Progress Indicator**
- **Issue**: "Grey out printer in dashboard when connection is in progress"
- **Impact**: Unclear when printer is connecting vs connected
- **Fix**: Add loading state to printer tiles

**Implementation**:
```javascript
// frontend/js/dashboard.js
function renderPrinterCard(printer) {
    const connectionState = printer.connection_status; // connecting | connected | failed

    return `
        <div class="printer-card ${connectionState === 'connecting' ? 'connecting' : ''}">
            ${connectionState === 'connecting' ? `
                <div class="connection-overlay">
                    <div class="spinner"></div>
                    <span>Verbinde mit ${printer.printer_type}...</span>
                </div>
            ` : ''}
            <!-- rest of card -->
        </div>
    `;
}
```

**CSS**:
```css
.printer-card.connecting {
    opacity: 0.6;
    pointer-events: none;
}

.connection-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.7);
    border-radius: 8px;
}
```

**Estimated Effort**: 2 hours

---

**B. Camera Preview Placeholder**
- **Issue**: "Printer tile: Show preview image or placeholder if preview is not available"
- **Impact**: Blank space when camera unavailable
- **Fix**: Add placeholder image/icon

**Implementation**:
```javascript
function renderPrinterPreview(printer) {
    if (printer.has_camera && printer.camera_url) {
        return `<img src="${printer.camera_url}" alt="Drucker-Vorschau">`;
    }

    // Show placeholder
    return `
        <div class="camera-placeholder">
            <i class="fas fa-camera-slash"></i>
            <span>Keine Kamera</span>
        </div>
    `;
}
```

**Estimated Effort**: 1 hour

---

#### 3.3 Debug Page Formatting

**Issue**: "Show Anwendungsprotokolle with multiple columns instead of blocks"
**Impact**: Hard to read logs

**Fix**: Table layout for logs

**Implementation**:
```javascript
// frontend/js/debug.js
function renderLogTable(logs) {
    return `
        <table class="log-table">
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Level</th>
                    <th>Source</th>
                    <th>Message</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
                ${logs.map(log => `
                    <tr class="log-${log.level}">
                        <td>${formatTimestamp(log.timestamp)}</td>
                        <td><span class="badge badge-${log.level}">${log.level}</span></td>
                        <td>${log.source}</td>
                        <td>${log.message}</td>
                        <td><button onclick="showLogDetails('${log.id}')">Details</button></td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}
```

**Estimated Effort**: 2 hours

---

### 🟡 Backend Issues (Priority 3)

Source: `docs/development/root-todos.md`

#### 3.4 Environment Configuration

**Issue**: "Cleanup .env or .env.sample - Which values are actually used?"
**Impact**: Confusion about required config

**Fix**: Audit and document all environment variables

**Action Items**:
1. List all environment variables read by application
2. Mark as REQUIRED vs OPTIONAL
3. Add descriptions and examples
4. Remove unused variables
5. Update `.env.example` with clear comments

**Implementation**:
```bash
# .env.example (cleaned up version)

# === REQUIRED ===
DATABASE_PATH=/data/printernizer.db  # SQLite database location
ENVIRONMENT=production  # production | development | testing

# === OPTIONAL - Paths ===
DOWNLOAD_PATH=/data/downloads  # Where printer files are downloaded
LIBRARY_PATH=/data/library  # 3D model library location

# === OPTIONAL - Printers ===
# Bambu Lab Printer
BAMBU_PRINTER_IP=  # Leave empty to skip
BAMBU_ACCESS_CODE=  # 8-character code from printer
BAMBU_SERIAL=  # Printer serial number

# Prusa Printer
PRUSA_PRINTER_IP=  # Leave empty to skip
PRUSA_API_KEY=  # API key from PrusaLink

# === OPTIONAL - Features ===
TIMELAPSE_ENABLED=false  # Enable timelapse video creation
USAGE_STATS_ENABLED=false  # Opt-in to anonymous usage stats
```

**Estimated Effort**: 2-3 hours

---

#### 3.5 Platform Compatibility Issues

**A. Watchdog Observer Thread Failure (Windows)**
- **Issue**: Windows threading compatibility - running in degraded polling mode
- **Impact**: File watcher slower on Windows
- **Status**: Currently using PollingObserver fallback
- **Priority**: LOW (workaround in place)

**B. Bambu FTP Connection Timeouts**
- **Issue**: Initial connection attempts fail, retry works but slow
- **Impact**: First download attempt often fails
- **Priority**: MEDIUM
- **Location**: `src/services/bambu_ftp_service.py`

**Potential Fix**:
- Increase initial connection timeout
- Implement connection pooling
- Add connection pre-warming

**C. Bambu MQTT Connection Instability**
- **Issue**: Multiple timeout/reconnect cycles before stable
- **Impact**: Delayed status updates on startup
- **Priority**: MEDIUM
- **Location**: `src/printers/bambu_lab.py`

---

## Feature Completeness

### 🟢 Low Priority Polish Features

#### 4.1 3D File Preview

**Status**: Placeholder
**Location**: `frontend/js/milestone-1-2-functions.js:427`
**Priority**: LOW (nice-to-have)

**Current**: Shows toast "3D-Vorschau wird in einer späteren Version verfügbar sein"

**Implementation Options**:

**Option A: Three.js Integration**
```javascript
import * as THREE from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';

async function preview3DFile(fileId) {
    const file = await fetchFile(fileId);
    const blob = await fetchFileBlob(fileId);

    // Create Three.js scene
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer();

    // Load STL
    const loader = new STLLoader();
    loader.load(URL.createObjectURL(blob), (geometry) => {
        const material = new THREE.MeshPhongMaterial({
            color: 0x00ff00,
            specular: 0x111111,
            shininess: 200
        });
        const mesh = new THREE.Mesh(geometry, material);
        scene.add(mesh);
    });

    // Show in modal
    showPreviewModal(renderer.domElement);
}
```

**Dependencies**:
- `three.js` (~600KB)
- STL/3MF/OBJ loaders

**Estimated Effort**: 8-12 hours

---

**Option B: Lightweight Alternative**
Use existing thumbnail + metadata display (already implemented)

**Estimated Effort**: 2 hours (just connect existing features)

---

#### 4.2 Local File Opening

**Status**: Placeholder
**Location**: `frontend/js/milestone-1-2-functions.js:435`
**Priority**: LOW

**Current**: Shows toast "Lokale Datei-Funktion wird in einer späteren Version verfügbar sein"

**Challenge**: Web browsers can't directly open local files for security

**Solutions**:

**Option A: Electron Wrapper**
- Package as Electron app
- Use `shell.openPath()` API
- Effort: 10-15 hours

**Option B: System File Protocol**
- Register custom `printernizer://` handler
- Platform-specific installers
- Effort: 15-20 hours

**Option C: Defer to Future**
- Keep as placeholder
- Low user demand
- Effort: 0 hours (status quo)

**Recommendation**: Option C (defer) - low ROI

---

#### 4.3 Excel Export for Materials

**Status**: Returns 501
**Location**: `src/api/routers/materials.py:168`
**Priority**: LOW (CSV export works)

**Implementation**:
```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

@router.get("/export/excel")
async def export_materials_excel():
    materials = await material_service.list_materials()

    wb = Workbook()
    ws = wb.active
    ws.title = "Materials"

    # Header row
    headers = ["Name", "Type", "Color", "Weight (g)", "Cost (EUR)", "Created"]
    ws.append(headers)

    # Style header
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="DDDDDD", fill_type="solid")

    # Data rows
    for mat in materials:
        ws.append([
            mat.name,
            mat.type,
            mat.color,
            mat.weight_grams,
            mat.cost_eur,
            mat.created_at.isoformat()
        ])

    # Save to BytesIO
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=materials.xlsx"}
    )
```

**Dependencies**: `openpyxl>=3.0.0`

**Estimated Effort**: 2-3 hours

---

#### 4.4 Enhanced Printer Details Modal

**Status**: Simple placeholder
**Location**: `frontend/js/printers.js:582`
**Priority**: LOW

**Current**: Shows basic toast with printer info

**Enhancement**: Full modal with:
- Printer specifications
- Print history
- Usage statistics
- Control buttons
- Camera preview
- Error log

**Estimated Effort**: 6-8 hours

---

#### 4.5 Detailed Log Viewer

**Status**: Placeholder
**Location**: `frontend/js/auto-download-ui.js:590`
**Priority**: LOW

**Enhancement**: Rich log viewer with:
- Filtering by level
- Search functionality
- Expandable details
- Export logs

**Estimated Effort**: 4-6 hours

---

## Code Quality & Cleanup

### 🔵 Maintenance Items

#### 5.1 Remove Deprecated Code

**Location**: `src/services/printer_service.py:185-199`

**Method**: `get_printers()` (deprecated in favor of `list_printers()`)

**Action**: Remove before v2.0.0 release

```python
@deprecated("Use list_printers() instead")
async def get_printers(self) -> List[Dict[str, Any]]:
    """DEPRECATED: Use list_printers() instead."""
    logger.warning("get_printers() is deprecated, use list_printers()")
    return await self.list_printers()
```

**Estimated Effort**: 30 minutes (search for usages, replace, test)

---

#### 5.2 Review Legacy Exception Handler

**Location**: `src/main.py:730-734`

**Description**: Legacy PrinternizerException handler for backwards compatibility

**Action**: Verify if still needed, remove if not

**Estimated Effort**: 1 hour (code audit, testing)

---

#### 5.3 Fix Flaky WebSocket Test

**Status**: Skipped
**Location**: `tests/frontend/websocket.test.js:159`
**Issue**: Timing issues with reconnection in CI/CD

**Fix**: Use proper test utilities with timeouts and retries

```javascript
test('WebSocket reconnection', async () => {
    // Increase timeout for CI environments
    jest.setTimeout(10000);

    // Use waitFor utility
    await waitFor(() => {
        expect(websocket.isConnected()).toBe(true);
    }, { timeout: 5000 });
});
```

**Estimated Effort**: 2-3 hours

---

#### 5.4 Library Feature: Custom Tags

**Status**: Planned
**Source**: `docs/development/root-todos.md`

**Feature**: Add custom tags to files in library

**Implementation**:
1. Add `tags` column to `library_files` table (JSON array)
2. API endpoints:
   - `POST /api/v1/library/{id}/tags` - Add tag
   - `DELETE /api/v1/library/{id}/tags/{tag}` - Remove tag
   - `GET /api/v1/library/tags` - List all tags
3. Frontend tag picker UI
4. Filter by tags

**Estimated Effort**: 4-6 hours

---

## Future Roadmap

### Phase 6: Advanced Home Assistant Integration

**Features**:
- MQTT discovery
- Sensor entities for printer status
- Automation triggers (print_started, print_completed)
- Service calls (start_print, pause_print)

**Effort**: 15-20 hours

---

### Phase 7: Watch Folders Enhancement

**Current**: Basic watch folder monitoring exists

**Enhancements**:
- Processing workflows (auto-slice, auto-upload)
- Thingiverse/Printables integration
- Auto-tagging based on folder structure
- Duplicate detection

**Effort**: 20-25 hours

---

### Phase 8: Multi-User System

**Features**:
- User authentication (JWT)
- Role-based access control
- Permission system (admin, operator, viewer)
- User activity logging

**Effort**: 30-40 hours

---

### Phase 9: Advanced Analytics

**Features**:
- Predictive maintenance (based on print hours)
- Failure pattern analysis
- ML-based optimization suggestions
- Cost forecasting

**Effort**: 40-50 hours

---

### Phase 10: Expanded Printer Support

**Current**: Bambu Lab A1, Prusa Core One

**Additional**:
- Klipper firmware (via Moonraker API)
- Creality (via Cloud API)
- Anycubic
- Generic OctoPrint

**Effort**: 10-15 hours per manufacturer

---

## Project Health Metrics

### Current Status

| Category | Percentage | Status |
|----------|------------|--------|
| Core Features Complete | 95% | ✅ Excellent |
| API Endpoints Implemented | 90% | ✅ Very Good |
| Service Test Coverage | 30% | ❌ Needs Work |
| API Router Test Coverage | 40% | ⚠️ Needs Work |
| Frontend Features | 85% | ✅ Good |
| Documentation Quality | 80% | ✅ Good |

### Active Technical Debt

| Priority | Count | Total Hours |
|----------|-------|-------------|
| High (P1) | 3 items | 8-10 hours |
| Medium (P2) | 15 items | 25-35 hours |
| Low (P3) | 8 items | 15-20 hours |
| Cleanup | 4 items | 5-8 hours |
| **Total** | **30 items** | **53-73 hours** |

### Velocity Estimates

Assuming 1 developer working part-time (15 hours/week):
- **Critical fixes** (P1): 1 week
- **Test coverage** (P2 services): 2-3 weeks
- **Feature completion** (P2 features): 2 weeks
- **Polish & cleanup** (P3): 1-2 weeks

**Total timeline**: 6-8 weeks

---

## Sprint Planning Recommendations

### Sprint 1: Critical Backend (Week 1)
**Goal**: Complete all P1 backend endpoints

- [ ] Material consumption history endpoint (3-4h)
- [ ] Enable job status update tests (2-3h)
- [ ] Fix printer CRUD tests (3-4h)
- [ ] Remove outdated TODOs (1h)
- [ ] Update documentation (1h)

**Total**: 10-13 hours

---

### Sprint 2: Core Service Tests (Weeks 2-3)
**Goal**: Achieve 50% service test coverage

- [ ] EventService tests (2-3h)
- [ ] PrinterMonitoringService tests (3-4h)
- [ ] ConfigService tests (2-3h)
- [ ] BusinessService tests (2-3h)
- [ ] FileWatcherService tests (2h)
- [ ] MaterialService tests (2h)

**Total**: 13-17 hours

---

### Sprint 3: User-Facing Polish (Week 4)
**Goal**: Fix top frontend issues

- [ ] Fix offline backend detection (1-2h)
- [ ] Fix duplicate notifications (1-2h)
- [ ] Add printer connection progress (2h)
- [ ] Add camera placeholder (1h)
- [ ] Improve debug page layout (2h)
- [ ] Clean up .env documentation (2-3h)

**Total**: 9-12 hours

---

### Sprint 4: Feature Completion (Week 5-6)
**Goal**: Complete partially implemented features

- [ ] Excel export for materials (2-3h)
- [ ] Library custom tags (4-6h)
- [ ] Enhanced printer details modal (6-8h)
- [ ] 3D file preview (8-12h) OR defer

**Total**: 12-17 hours (or 4-5h if deferring preview)

---

### Sprint 5: Cleanup & Documentation (Week 7-8)
**Goal**: Code quality and maintainability

- [ ] Remove deprecated code (0.5h)
- [ ] Review legacy exception handler (1h)
- [ ] Fix flaky tests (2-3h)
- [ ] Update all documentation (3-4h)
- [ ] Create release notes (2h)

**Total**: 8-10 hours

---

## Success Criteria

### Definition of Done for Masterplan

- ✅ All P1 items complete
- ✅ Service test coverage ≥ 50%
- ✅ API router test coverage ≥ 60%
- ✅ All user-facing issues resolved
- ✅ Documentation up-to-date
- ✅ No failing tests in CI/CD
- ✅ Release notes published

### Key Performance Indicators

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Test Coverage (Services) | 30% | 80% | pytest --cov |
| Test Coverage (Routers) | 40% | 80% | pytest --cov |
| Open Critical Issues | 3 | 0 | GitHub Issues |
| Open Medium Issues | 15 | 5 | GitHub Issues |
| CI/CD Success Rate | 95% | 100% | GitHub Actions |
| Build Time | 3min | <2min | CI/CD logs |

---

## Appendix

### Related Documentation

- [REMAINING_TASKS.md](REMAINING_TASKS.md) - Detailed task breakdown
- [root-todos.md](development/root-todos.md) - User-reported issues
- [todos.md](development/todos.md) - Code-level TODOs
- [JOB_UPDATE_API_STATUS.md](plans/JOB_UPDATE_API_STATUS.md) - Example completed feature

### Contact & Support

- **Issues**: https://github.com/schmacka/printernizer/issues
- **Discussions**: https://github.com/schmacka/printernizer/discussions

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-01 | Initial masterplan created |

---

**End of Masterplan**

*This is a living document and should be updated as work progresses.*
