# Automated Job Creation - Design Document

**Status:** Ready for Implementation
**Author:** Claude & User
**Date:** 2025-01-08
**Updated:** 2025-01-08 (All open questions resolved)
**Target Version:** TBD

## Overview

Automatically create job records when a printer starts printing, including when Printernizer starts and finds a printer already in the middle of a print job.

## Problem Statement

Currently, jobs must be created manually via `POST /api/v1/jobs` before or during a print. This creates several issues:

1. **Missed Jobs**: If a user starts a print without creating a job record, it won't be tracked
2. **Startup Gap**: When Printernizer starts and a printer is already printing, no job record exists
3. **Manual Overhead**: Users must remember to create jobs before printing
4. **Analytics Gap**: Untracked prints mean incomplete business analytics

## Goals

### Primary Goals
- ✅ Auto-create job records when a print starts (ONLINE → PRINTING transition)
- ✅ Auto-create job records on startup if printer is already printing
- ✅ No duplicate jobs for the same print
- ✅ Use accurate printer-reported start times when available

### Non-Goals
- ❌ Calculating/estimating start times (too unreliable)
- ❌ Retroactively creating jobs for completed prints
- ❌ Auto-detecting business vs. private jobs (manual flag)
- ❌ Modifying existing manual job creation workflow

## Key Design Principles

### 1. **Discovery Time vs. Start Time**

We distinguish between two timestamps:

| Timestamp | Definition | Source | Use Case |
|-----------|------------|--------|----------|
| **Discovery Time** | When Printernizer first detected the print | System (our polling) | Deduplication key |
| **Start Time** | When the print actually started | Printer (if available) | Analytics, reporting |

**Rationale:** Discovery time is stable and under our control - perfect for preventing duplicates. Start time is optional but valuable for accurate analytics.

### 2. **No Calculations**

We will **NOT** calculate start times from progress + remaining time. Reasons:

- **Unreliable**: Different calculations at different times = different keys = duplicates
- **Inaccurate**: Could be off by several minutes depending on print speed variations
- **Complex**: Adds unnecessary complexity and edge cases

**Rule:** Only use start time if printer directly provides it. Otherwise, leave it NULL.

### 3. **Deduplication Strategy**

**Deduplication Key:**
```
printer_id : filename : discovery_time_rounded_to_minute
```

**Why round to minute?**
- Handles polling jitter (status checked every 30 seconds)
- Prevents duplicates from multiple status updates during same print
- Still allows printing same file twice in production

**Implementation:**
- In-memory cache for recent prints (last 2 hours)
- Database fallback check (±2 minute window)
- `asyncio.Lock` to prevent race conditions

## Current System Architecture

### Status Polling Flow

```
┌─────────────────────────────────────────────────────────────┐
│ PrinterService.start_monitoring()                           │
│   ├─ Connect to printers                                    │
│   ├─ Start monitoring (every 30 seconds)                    │
│   └─ _handle_status_update() on each poll                   │
│                                                              │
│ _handle_status_update(status: PrinterStatusUpdate)          │
│   ├─ Store status in database                               │
│   ├─ Emit "printer_status_update" event                     │
│   ├─ Auto-download file for thumbnails                      │
│   └─ [NEW] Auto-create job if needed                        │
└─────────────────────────────────────────────────────────────┘
```

### Available Printer Data

**Bambu Lab** (via MQTT):
```python
PrinterStatusUpdate(
    status = PRINTING | ONLINE | PAUSED | ...
    current_job = "model.3mf"  # Filename
    progress = 0-100
    remaining_time_minutes = 45
    temperature_bed = 60.0
    temperature_nozzle = 220.0
    # START TIME: Need to investigate MQTT fields
)
```

**Prusa** (via HTTP API):
```python
PrinterStatusUpdate(
    status = PRINTING | ONLINE | PAUSED | ...
    current_job = "model.gcode"
    progress = 0-100
    remaining_time_minutes = 45
    # START TIME: Available via printTime field (seconds elapsed)
)
```

## Detailed Design

### 1. Data Model Changes

#### 1.1 PrinterStatusUpdate Enhancement

**File:** `src/models/printer.py`

```python
class PrinterStatusUpdate(BaseModel):
    """Printer status update model."""
    printer_id: str
    status: PrinterStatus
    message: Optional[str] = None
    temperature_bed: Optional[float] = None
    temperature_nozzle: Optional[float] = None
    progress: Optional[int] = None
    current_job: Optional[str] = None
    current_job_file_id: Optional[str] = None
    current_job_has_thumbnail: Optional[bool] = None
    current_job_thumbnail_url: Optional[str] = None
    remaining_time_minutes: Optional[int] = None
    estimated_end_time: Optional[datetime] = None

    # NEW: Direct printer-reported timing (only if available)
    elapsed_time_minutes: Optional[int] = None  # Time since print started
    print_start_time: Optional[datetime] = None  # Actual start time from printer

    timestamp: datetime = Field(default_factory=datetime.now)
    raw_data: Optional[Dict[str, Any]] = None
```

**Notes:**
- `print_start_time` is **ONLY** set if printer directly provides it
- `elapsed_time_minutes` is informational (for UI/debugging)
- Both can be `None` - that's perfectly acceptable

#### 1.2 Job Metadata

No schema changes needed! Use existing fields:

```python
{
    "id": UUID,
    "printer_id": str,
    "job_name": str,  # Cleaned filename
    "filename": str,  # Original filename
    "status": "running",  # Not "pending"!

    "created_at": datetime,  # = Discovery time for auto jobs
    "start_time": datetime | None,  # Printer-reported (if available)

    "customer_info": JSON | None,  # Can include {"auto_created": true}

    # ... other existing fields
}
```

### 2. Printer Implementation Changes

#### 2.1 Prusa - Extract Start Time

**File:** `src/printers/prusa.py`

**Location:** `get_status()` method, around line 180

```python
async def get_status(self) -> PrinterStatusUpdate:
    # ... existing status extraction ...

    # Extract job information
    current_job = ''
    progress = 0
    remaining_time_minutes = None
    estimated_end_time = None
    elapsed_time_minutes = None  # NEW
    print_start_time = None       # NEW

    if job_data:
        job_info = job_data.get('job', {})
        if job_info and job_info.get('file'):
            file_info = job_info.get('file', {})
            current_job = file_info.get('display_name', file_info.get('name', ''))

        progress_info = job_data.get('progress', {})
        if progress_info:
            progress = int(progress_info.get('completion', 0) or 0)

            # Remaining time
            print_time_left = progress_info.get('printTimeLeft')
            if print_time_left is not None and print_time_left > 0:
                remaining_time_minutes = int(print_time_left // 60)
                estimated_end_time = datetime.now() + timedelta(minutes=remaining_time_minutes)

            # NEW: Elapsed time and start time
            print_time = progress_info.get('printTime', 0)  # Seconds since start
            if print_time and print_time > 0:
                elapsed_time_minutes = int(print_time // 60)
                print_start_time = datetime.now() - timedelta(seconds=print_time)

    return PrinterStatusUpdate(
        printer_id=self.printer_id,
        status=printer_status,
        message=f"Prusa status: {prusa_state}",
        temperature_bed=float(bed_temp),
        temperature_nozzle=float(nozzle_temp),
        progress=progress,
        current_job=current_job if current_job else None,
        current_job_file_id=current_job_file_id,
        current_job_has_thumbnail=current_job_has_thumbnail,
        current_job_thumbnail_url=thumbnail_url,
        remaining_time_minutes=remaining_time_minutes,
        estimated_end_time=estimated_end_time,
        elapsed_time_minutes=elapsed_time_minutes,      # NEW
        print_start_time=print_start_time,              # NEW
        timestamp=datetime.now(),
        raw_data={**status_data, 'job': job_data or {}}
    )
```

#### 2.2 Bambu Lab - Extract Start Time (If Available)

**File:** `src/printers/bambu_lab.py`

**Location:** `_get_status_bambu_api()` method, around line 450

```python
async def _get_status_bambu_api(self) -> PrinterStatusUpdate:
    # ... existing code to get status ...

    # Try to get elapsed time from MQTT dump
    elapsed_time_minutes = None
    print_start_time = None

    try:
        if hasattr(self.bambu_client, 'mqtt_dump'):
            mqtt_data = self.bambu_client.mqtt_dump()
            if isinstance(mqtt_data, dict) and 'print' in mqtt_data:
                print_data = mqtt_data['print']
                if isinstance(print_data, dict):
                    # Try direct elapsed time field (in seconds)
                    # Common fields: mc_print_time, print_time, elapsed_time
                    elapsed_time_fields = ['mc_print_time', 'print_time', 'elapsed_time']
                    for field in elapsed_time_fields:
                        if field in print_data and print_data[field] is not None:
                            elapsed_seconds = int(print_data[field])
                            if elapsed_seconds > 0:
                                elapsed_time_minutes = elapsed_seconds // 60
                                print_start_time = datetime.now() - timedelta(seconds=elapsed_seconds)
                                logger.debug("Extracted Bambu elapsed time",
                                           field=field,
                                           elapsed_minutes=elapsed_time_minutes)
                                break

                    # Try direct start timestamp (Unix timestamp)
                    # Common fields: gcode_start_time, start_time
                    if not elapsed_time_minutes:
                        timestamp_fields = ['gcode_start_time', 'start_time']
                        for field in timestamp_fields:
                            if field in print_data and print_data[field]:
                                start_timestamp = int(print_data[field])
                                if start_timestamp > 0:
                                    print_start_time = datetime.fromtimestamp(start_timestamp)
                                    elapsed = (datetime.now() - print_start_time).total_seconds()
                                    elapsed_time_minutes = int(elapsed // 60)
                                    logger.debug("Extracted Bambu start timestamp",
                                               field=field,
                                               start_time=print_start_time.isoformat())
                                    break
    except Exception as e:
        logger.debug("Could not extract Bambu start time (field may not exist)",
                    error=str(e))

    # NOTE: If fields not available, elapsed_time_minutes and print_start_time remain None
    # This is acceptable! We'll use discovery time for deduplication instead.

    return PrinterStatusUpdate(
        printer_id=self.printer_id,
        status=printer_status,
        message=message,
        temperature_bed=float(bed_temp),
        temperature_nozzle=float(nozzle_temp),
        progress=int(progress),
        current_job=current_job,
        current_job_file_id=current_job_file_id,
        current_job_has_thumbnail=current_job_has_thumbnail,
        current_job_thumbnail_url=thumbnail_url,
        remaining_time_minutes=remaining_time_minutes,
        estimated_end_time=estimated_end_time,
        elapsed_time_minutes=elapsed_time_minutes,  # NEW - may be None
        print_start_time=print_start_time,          # NEW - may be None
        timestamp=datetime.now(),
        raw_data=status.__dict__ if hasattr(status, '__dict__') else {}
    )
```

**TODO:** Test with real Bambu printer to discover actual field names. Add debug logging to see all available MQTT fields.

### 3. Auto-Creation Logic

#### 3.1 PrinterService Enhancement

**File:** `src/services/printer_service.py`

**New Instance Variables:**

```python
class PrinterService:
    def __init__(self, database: Database, event_service: EventService,
                 config_service: ConfigService, file_service=None, job_service=None):
        self.database = database
        self.event_service = event_service
        self.config_service = config_service
        self.file_service = file_service
        self.job_service = job_service  # NEW: Injected dependency

        self.printer_instances: Dict[str, BasePrinter] = {}
        self.monitoring_active = False
        self._auto_download_attempts: Dict[str, set] = {}
        self._background_tasks: set = set()

        # NEW: Auto-job creation tracking
        self._print_discoveries: Dict[str, datetime] = {}  # "printer_id:filename" -> discovery_time
        self._auto_job_cache: Dict[str, Set[str]] = {}    # printer_id -> {job_keys}
        self._job_creation_lock = asyncio.Lock()
        self.auto_create_jobs = True  # TODO: Read from config
```

#### 3.2 Core Methods

```python
async def _auto_create_job_if_needed(self, status: PrinterStatusUpdate, is_startup: bool = False):
    """
    Auto-create job record if printer is printing.

    Args:
        status: Current printer status
        is_startup: True if this is called during system startup/reconnection
    """
    # Only create for printing status with a known file
    if status.status != PrinterStatus.PRINTING or not status.current_job:
        return

    printer_id = status.printer_id
    filename = status.current_job

    # Track when we FIRST discovered this print
    discovery_key = f"{printer_id}:{filename}"

    if discovery_key not in self._print_discoveries:
        # First time seeing this print!
        discovery_time = datetime.now()
        self._print_discoveries[discovery_key] = discovery_time

        logger.info("Discovered new print",
                   printer_id=printer_id,
                   filename=filename,
                   discovery_time=discovery_time.isoformat(),
                   is_startup=is_startup)
    else:
        # We've seen this print before (subsequent status updates)
        discovery_time = self._print_discoveries[discovery_key]

    # Generate deduplication key using discovery time
    job_key = self._make_job_key(printer_id, filename, discovery_time)

    # Thread-safe check and create
    async with self._job_creation_lock:
        # Check in-memory cache first (fast path)
        if printer_id not in self._auto_job_cache:
            self._auto_job_cache[printer_id] = set()

        if job_key in self._auto_job_cache[printer_id]:
            logger.debug("Job already created (in cache)", job_key=job_key)
            return

        # Check database (handles restarts, cache misses)
        existing = await self._find_existing_job(printer_id, filename, discovery_time)
        if existing:
            logger.info("Job already exists in database", job_id=existing['id'])
            self._auto_job_cache[printer_id].add(job_key)
            return

        # Create the job!
        await self._create_auto_job(status, discovery_time, is_startup)
        self._auto_job_cache[printer_id].add(job_key)


def _make_job_key(self, printer_id: str, filename: str, discovery_time: datetime) -> str:
    """
    Generate unique job key for deduplication.

    Uses discovery time rounded to minute to handle polling jitter.
    Format: "printer_id:filename:YYYY-MM-DDTHH:MM"
    """
    # Round to minute to handle 30-second polling jitter
    discovery_minute = discovery_time.replace(second=0, microsecond=0)

    # Clean filename for key (remove cache/ prefix if present)
    clean_filename = filename
    if clean_filename.startswith('cache/'):
        clean_filename = clean_filename[6:]

    return f"{printer_id}:{clean_filename}:{discovery_minute.isoformat()}"


async def _find_existing_job(self, printer_id: str, filename: str,
                            discovery_time: datetime) -> Optional[Dict[str, Any]]:
    """
    Check database for existing job near this discovery time.

    Looks for jobs created within ±2 minutes to handle:
    - System restarts
    - Network reconnections
    - Clock drift
    """
    # Search window: ±2 minutes
    start_window = discovery_time - timedelta(minutes=2)
    end_window = discovery_time + timedelta(minutes=2)

    # Get recent jobs for this printer
    jobs = await self.database.list_jobs(
        printer_id=printer_id,
        status='running',
        limit=20  # Reasonable limit for active jobs
    )

    # Clean filename for comparison
    clean_filename = filename
    if clean_filename.startswith('cache/'):
        clean_filename = clean_filename[6:]

    for job in jobs:
        job_filename = job.get('filename', '')
        if job_filename.startswith('cache/'):
            job_filename = job_filename[6:]

        created_at = datetime.fromisoformat(job['created_at'])

        if (job_filename == clean_filename and
            start_window <= created_at <= end_window):
            logger.debug("Found existing job in database",
                        job_id=job['id'],
                        created_at=job['created_at'],
                        discovery_time=discovery_time.isoformat())
            return job

    return None


async def _create_auto_job(self, status: PrinterStatusUpdate,
                          discovery_time: datetime, is_startup: bool):
    """
    Create auto job record.

    Args:
        status: Current printer status with all available data
        discovery_time: When we first discovered this print
        is_startup: Whether this is during system startup
    """
    if not self.job_service:
        logger.error("Cannot create auto job - JobService not available")
        return

    # Clean filename for job name
    job_name = self._clean_filename(status.current_job)

    # Get printer type
    printer_instance = self.printer_instances.get(status.printer_id)
    if printer_instance:
        printer_type = 'bambu_lab' if 'Bambu' in type(printer_instance).__name__ else 'prusa_core'
    else:
        printer_type = 'unknown'

    # Build job data
    job_data = {
        'printer_id': status.printer_id,
        'printer_type': printer_type,
        'job_name': job_name,
        'filename': status.current_job,
        'status': 'running',  # Already in progress!

        # Discovery time (when we first saw it)
        'created_at': discovery_time.isoformat(),

        # Actual start time from printer (if available)
        'start_time': status.print_start_time.isoformat() if status.print_start_time else None,

        # Metadata
        'customer_info': json.dumps({
            'auto_created': True,
            'discovery_time': discovery_time.isoformat(),
            'discovered_on_startup': is_startup,
            'printer_start_time': status.print_start_time.isoformat() if status.print_start_time else None
        }),

        # Optional fields
        'progress': status.progress or 0,
        'is_business': False,  # Default, user can update later
    }

    # Try to link to file if it exists
    if status.current_job_file_id:
        job_data['file_id'] = status.current_job_file_id

    try:
        job = await self.job_service.create_job(job_data)

        logger.info("Auto-created job",
                   job_id=job.get('id'),
                   printer_id=status.printer_id,
                   filename=status.current_job,
                   discovery_time=discovery_time.isoformat(),
                   printer_start_time=status.print_start_time.isoformat() if status.print_start_time else 'unknown',
                   is_startup=is_startup)

        # Emit event for UI updates
        await self.event_service.emit_event("job_auto_created", {
            "job_id": job.get('id'),
            "printer_id": status.printer_id,
            "filename": status.current_job,
            "discovery_time": discovery_time.isoformat()
        })

    except Exception as e:
        logger.error("Failed to auto-create job",
                    printer_id=status.printer_id,
                    filename=status.current_job,
                    error=str(e),
                    exc_info=True)


def _clean_filename(self, filename: str) -> str:
    """
    Clean filename for job name.

    Removes:
    - cache/ prefix (Bambu Lab)
    - File extensions (.gcode, .3mf, .bgcode)
    - Extra whitespace
    """
    clean = filename

    # Remove cache/ prefix
    if clean.startswith('cache/'):
        clean = clean[6:]

    # Remove common extensions
    for ext in ['.gcode', '.bgcode', '.3mf', '.stl']:
        if clean.lower().endswith(ext):
            clean = clean[:-len(ext)]
            break

    # Clean whitespace
    clean = clean.strip()

    return clean
```

#### 3.3 Integration Points

**Modify `_handle_status_update()`:**

```python
async def _handle_status_update(self, status: PrinterStatusUpdate):
    """Handle status updates from printers."""
    # Store status in database
    await self._store_status_update(status)

    # Emit event for real-time updates
    await self.event_service.emit_event("printer_status_update", {
        "printer_id": status.printer_id,
        "status": status.status.value,
        "message": status.message,
        "temperature_bed": status.temperature_bed,
        "temperature_nozzle": status.temperature_nozzle,
        "progress": status.progress,
        "current_job": status.current_job,
        "current_job_file_id": status.current_job_file_id,
        "current_job_has_thumbnail": status.current_job_has_thumbnail,
        "current_job_thumbnail_url": status.current_job_thumbnail_url,
        "timestamp": status.timestamp.isoformat()
    })

    # Auto-download & process current job file if needed
    # ... existing auto-download code ...

    # NEW: Auto-create job if needed
    if self.auto_create_jobs and self.job_service:
        await self._auto_create_job_if_needed(status)

    # Clean up discovery tracking when print ends
    if status.status in [PrinterStatus.ONLINE, PrinterStatus.ERROR]:
        if status.current_job:
            discovery_key = f"{status.printer_id}:{status.current_job}"
            self._print_discoveries.pop(discovery_key, None)
```

**Modify `start_monitoring()` for startup detection:**

```python
async def _connect_and_monitor_printer(self, printer_id: str, instance: BasePrinter):
    """Connect to printer and start monitoring (background task helper)."""
    start_time = time.time()
    try:
        # ... existing connection code ...

        if connected:
            # ... existing code ...

            # NEW: Check if printer is already printing (startup detection)
            try:
                status = await instance.get_status()
                if status.status == PrinterStatus.PRINTING and status.current_job:
                    logger.info("Detected print in progress on startup",
                               printer_id=printer_id,
                               filename=status.current_job,
                               progress=status.progress)

                    # Auto-create job with is_startup=True flag
                    if self.auto_create_jobs and self.job_service:
                        await self._auto_create_job_if_needed(status, is_startup=True)
            except Exception as e:
                logger.warning("Failed to check for active print on startup",
                             printer_id=printer_id,
                             error=str(e))

        await instance.start_monitoring()
        # ... rest of existing code ...
```

### 4. Configuration

#### 4.1 Config Schema

**File:** `src/services/config_service.py` or `config.yaml`

```yaml
job_creation:
  # Global toggle for auto-creation
  auto_create: true

  # Future: Per-printer overrides
  # printer_overrides:
  #   "printer-abc-123":
  #     auto_create: false  # Disable for this specific printer
```

#### 4.2 Reading Configuration

```python
class PrinterService:
    async def initialize(self):
        """Initialize printer service and load configured printers."""
        logger.info("Initializing printer service")
        await self._load_printers()
        await self._sync_database_printers()

        # NEW: Load auto-creation config
        self.auto_create_jobs = self.config_service.get_config(
            'job_creation.auto_create',
            default=True
        )
        logger.info("Auto job creation", enabled=self.auto_create_jobs)
```

### 5. Edge Cases & Solutions

| Edge Case | Scenario | Solution |
|-----------|----------|----------|
| **Same file twice** | User prints model.gcode at 10:00 and again at 11:00 | Different discovery times → Different job keys → Two jobs ✅ |
| **Pause/Resume** | Print paused at 10:30, resumed at 10:45 | Same discovery key → Job exists in cache → No duplicate ✅ |
| **Network reconnect** | Lost connection at 10:15, reconnect at 10:20 | Same discovery time → DB query finds existing job → No duplicate ✅ |
| **System restart** | Printernizer restarts at 10:30, print still running | New discovery time, but DB query (±2min window) finds job → No duplicate ✅ |
| **Very short print** | Print completes in <30 seconds | May miss it, but acceptable for v1 ⚠️ |
| **File downloaded later** | Job created before file record exists | Job created without file_id, can be linked later ✅ |
| **Multiple printers, same file** | Both printers print model.gcode | Different printer_id → Different job keys → Two jobs ✅ |
| **Clock drift** | System clock adjusted during print | ±2 minute DB search window handles this ✅ |
| **Job manually created** | User manually creates job, then we try to auto-create | DB query finds manual job → No duplicate ✅ |

### 6. Testing Strategy

#### 6.1 Unit Tests

**File:** `tests/services/test_printer_service_auto_jobs.py`

```python
# Test _make_job_key() consistency
def test_make_job_key_stable():
    """Job key should be stable for same inputs."""

def test_make_job_key_different_for_different_times():
    """Job key should differ for prints at different times."""

def test_make_job_key_rounds_to_minute():
    """Job key should be same within same minute."""

# Test _clean_filename()
def test_clean_filename_removes_extensions():
    """Should remove .gcode, .3mf, etc."""

def test_clean_filename_removes_cache_prefix():
    """Should remove cache/ prefix from Bambu files."""

# Test _find_existing_job()
async def test_find_existing_job_time_window():
    """Should find jobs within ±2 minute window."""

async def test_find_existing_job_filename_match():
    """Should match on cleaned filename."""

# Test deduplication
async def test_no_duplicate_on_multiple_status_updates():
    """Multiple PRINTING status updates shouldn't create duplicates."""

async def test_no_duplicate_after_restart():
    """Restarting during a print shouldn't create duplicate."""
```

#### 6.2 Integration Tests

**File:** `tests/integration/test_auto_job_creation.py`

```python
# Scenario: Print starts normally
async def test_auto_create_on_print_start():
    """Job created when status transitions ONLINE → PRINTING."""

# Scenario: System startup with active print
async def test_auto_create_on_startup():
    """Job created when Printernizer starts and printer is already printing."""

# Scenario: Same file printed twice
async def test_two_jobs_for_same_file():
    """Printing same file twice should create two separate jobs."""

# Scenario: Pause and resume
async def test_no_duplicate_on_pause_resume():
    """Pausing and resuming should not create duplicate job."""

# Scenario: Network reconnection
async def test_no_duplicate_on_reconnect():
    """Network disconnect/reconnect should not create duplicate."""

# Scenario: Manual job already exists
async def test_no_duplicate_when_manual_job_exists():
    """Should not create auto job if manual job already exists."""
```

#### 6.3 Manual Testing Checklist

- [ ] **Bambu Lab - Normal print start**
  - Start print from Bambu Studio
  - Verify job auto-created within 30 seconds
  - Check start_time is populated (if field available)

- [ ] **Bambu Lab - Startup with active print**
  - Start print
  - Restart Printernizer
  - Verify job created on startup with is_startup flag

- [ ] **Prusa - Normal print start**
  - Start print from PrusaSlicer
  - Verify job auto-created
  - Check start_time is populated from printTime

- [ ] **Prusa - Pause/Resume**
  - Start print, pause it, resume
  - Verify only one job created

- [ ] **Same file twice**
  - Print model.gcode
  - Wait for completion
  - Print model.gcode again
  - Verify two separate jobs

### 7. UI/UX Considerations

#### 7.1 Job List Display

Auto-created jobs should be visually distinguished:

```typescript
// Frontend: Job badge/indicator
{job.auto_created && (
  <Badge variant="secondary" size="sm">
    <Icon name="zap" /> Auto
  </Badge>
)}

// Tooltip: Show discovery vs start time
<Tooltip>
  <p>Discovered: {job.created_at}</p>
  {job.start_time ? (
    <p>Print Started: {job.start_time}</p>
  ) : (
    <p>Print start time unknown</p>
  )}
</Tooltip>
```

#### 7.2 Editing Auto-Created Jobs

Users should be able to:
- ✅ Rename job
- ✅ Mark as business job
- ✅ Add customer info
- ✅ Convert to manual job (remove auto flag)
- ❌ Cannot change printer_id or filename

#### 7.3 Settings Toggle

```typescript
// Settings page
<Switch
  label="Automatically create jobs when prints start"
  checked={config.job_creation.auto_create}
  onChange={(enabled) => updateConfig('job_creation.auto_create', enabled)}
/>

<HelpText>
  When enabled, Printernizer will automatically create job records when a
  printer starts printing. Jobs will be marked with start times from the
  printer when available.
</HelpText>
```

### 8. Future Enhancements

#### Phase 2 Features (Not in Initial Implementation)

1. **Smart Business Detection**
   - Detect business jobs based on filename patterns
   - Prompt user to confirm business type
   - Learn from user corrections

2. **Per-Printer Configuration**
   - Enable/disable auto-creation per printer
   - Different naming rules per printer
   - Custom business detection rules

3. **Retroactive Job Creation**
   - Analyze past prints from printer logs
   - Create historical jobs for analytics
   - Import from OctoPrint/other systems

4. **Enhanced Time Detection**
   - Query printer for historical start times
   - Use layer timestamps for better accuracy
   - Detect print restarts/failures

5. **Job Templates**
   - Pre-defined job templates
   - Auto-apply based on filename patterns
   - Bulk job operations

6. **Analytics Integration**
   - Track auto-creation success rate
   - Report on missed prints
   - Optimize duplicate detection algorithm

### 9. Migration & Rollout

#### Phase 1: Core Implementation (Week 1)
- [ ] Update PrinterStatusUpdate model
- [ ] Extract start times from Prusa
- [ ] Investigate Bambu MQTT fields for start time
- [ ] Implement auto-creation logic in PrinterService
- [ ] Add deduplication with discovery time
- [ ] Integrate into status update flow
- [ ] Add startup detection
- [ ] Unit tests for core logic

#### Phase 2: Testing & Polish (Week 2)
- [ ] Integration tests
- [ ] Manual testing with real printers
- [ ] Add configuration toggle
- [ ] Improve logging and debugging
- [ ] Performance testing (memory leaks, cache size)

#### Phase 3: UI & Documentation (Week 3)
- [ ] Frontend: Auto-job indicator badges
- [ ] Frontend: Settings toggle
- [ ] API documentation updates
- [ ] User guide updates
- [ ] Release notes

### 10. Logging & Debugging

#### 10.1 Log Levels

```python
# INFO: Key events
logger.info("Discovered new print", printer_id=..., filename=...)
logger.info("Auto-created job", job_id=..., discovery_time=...)

# DEBUG: Detailed flow
logger.debug("Job already created (in cache)", job_key=...)
logger.debug("Found existing job in database", job_id=...)
logger.debug("Extracted start time from printer", field=..., value=...)

# WARNING: Issues (non-fatal)
logger.warning("Could not extract start time from printer", error=...)
logger.warning("JobService not available, auto-creation disabled")

# ERROR: Failures
logger.error("Failed to auto-create job", printer_id=..., error=...)
```

#### 10.2 Metrics to Track

```python
# For observability
metrics = {
    "auto_jobs_created_total": Counter,
    "auto_jobs_duplicate_prevented": Counter,
    "auto_jobs_startup_detected": Counter,
    "auto_job_creation_duration_seconds": Histogram,
    "auto_jobs_with_start_time": Counter,
    "auto_jobs_without_start_time": Counter,
}
```

### 11. Open Questions & Recommendations

#### For Implementation

##### 1. **Bambu MQTT Fields** ✅

**Decision:**
- Add verbose debug logging to capture all available MQTT fields during development
- Test with real Bambu printer across different firmware versions
- Document discovered fields in code comments with firmware version compatibility matrix
- Use field fallback chain (try multiple field names) for robustness

**Rationale:**
- Existing code already stores `raw_data` for debugging purposes
- Bambu MQTT API is reverse-engineered, so field names may vary
- Similar pattern exists in current Bambu implementation with `mqtt_dump()` method

**Implementation:**
```python
# Priority order for elapsed time fields
elapsed_fields = ['mc_print_time', 'print_time', 'elapsed_time']
# Priority order for start timestamp fields
timestamp_fields = ['gcode_start_time', 'start_time']
```

**Action Items:**
- [x] Define field fallback chains in design
- [ ] Test with real Bambu printer
- [ ] Document findings in code comments
- [ ] Add firmware version compatibility notes

---

##### 2. **Cache Cleanup** ✅

**Decision:**
- **When:** Clean up on print state transitions (PRINTING → ONLINE/ERROR/COMPLETED)
- **Max Size:** Keep last 2 hours of discoveries, implement LRU eviction
- **Periodic:** Optional background task every 30 minutes to remove stale entries
- **On Shutdown:** Clear all caches (no persistence needed)

**Rationale:**
- Matches existing `_auto_download_attempts` cache pattern in `PrinterMonitoringService`
- Memory efficient: ~100 bytes per entry × 50 prints = ~5KB (negligible)
- 2-hour window handles most edge cases (restarts, network issues)
- No need for persistent cache across application restarts

**Implementation:**
```python
# Already shown in design doc (cleanup on state transition)
if status.status in [PrinterStatus.ONLINE, PrinterStatus.ERROR]:
    if status.current_job:
        discovery_key = f"{status.printer_id}:{status.current_job}"
        self._print_discoveries.pop(discovery_key, None)

# Add periodic cleanup task
async def _cleanup_old_discoveries(self):
    """Remove discovery entries older than 2 hours."""
    cutoff = datetime.now() - timedelta(hours=2)
    self._print_discoveries = {
        k: v for k, v in self._print_discoveries.items()
        if v > cutoff
    }
```

**Action Items:**
- [x] Define cleanup strategy
- [ ] Implement state transition cleanup
- [ ] Add periodic cleanup task
- [ ] Add metrics for cache size monitoring

---

##### 3. **Job Service Integration** ✅

**Decision:**
- **Optional dependency** - inject via constructor, handle gracefully if None
- Use existing pattern from `PrinterMonitoringService` with `file_service`
- Log warning if unavailable, continue monitoring without auto-creation
- No interface needed - duck typing is sufficient for internal services

**Rationale:**
- Matches existing pattern in `printer_monitoring_service.py` (file_service handling)
- Allows testing in isolation
- Graceful degradation if service unavailable
- No tight coupling needed for internal services

**Implementation:**
```python
# In PrinterService.__init__
def __init__(self, ..., job_service=None):
    self.job_service = job_service
    # ... rest of init

# In monitoring code
if self.auto_create_jobs and self.job_service:
    await self._auto_create_job_if_needed(status)
else:
    logger.debug("Auto job creation disabled or JobService unavailable")
```

**Action Items:**
- [x] Define integration pattern
- [ ] Update PrinterService constructor
- [ ] Add graceful degradation logic
- [ ] Add tests for both with/without JobService

---

##### 4. **Configuration Location** ✅

**Decision:**
- **Phase 1:** File-based config (config.yaml) + environment variables
- Store in `Settings` class with `job_creation_auto_create: bool = True`
- Read once at startup, reload requires restart (acceptable for v1)
- **Phase 2:** Consider database storage for runtime changes

**Rationale:**
- Matches existing config patterns in `config_service.py` (Settings class)
- Home Assistant add-on already uses `config.yaml`
- Environment variables supported (`PRINTERNIZER_*` pattern in ConfigService)
- Simpler to implement, test, and debug
- Restart acceptable for config changes in v1

**Implementation:**
```python
# Add to Settings class (src/services/config_service.py)
class Settings(BaseSettings):
    # ... existing fields ...

    # Job Creation
    job_creation_auto_create: bool = True

# Add to config.yaml (printernizer/config.yaml)
options:
  # ... existing options ...
  job_creation_auto_create: true

schema:
  # ... existing schema ...
  job_creation_auto_create: bool?

# Access in code
self.auto_create_jobs = self.config_service.settings.job_creation_auto_create
```

**Action Items:**
- [x] Define config structure
- [ ] Update Settings class
- [ ] Update config.yaml schema
- [ ] Add config validation
- [ ] Document environment variable option

---

#### For Product Decisions

##### 1. **UI Workflow** ✅

**Decision:**
- **Silent creation** - no modal/blocking dialogs
- **Event emission** - emit `job_auto_created` event for UI refresh
- **Toast notification** - small, dismissible notification in corner
- **Immediate editing** - clicking notification opens job edit dialog
- **Visual indicator** - badge on job list showing "Auto" or ⚡ icon

**Rationale:**
- Matches existing event-driven architecture (`event_service.emit_event`)
- Non-intrusive UX - user can ignore if not interested
- Event system already in place
- Similar pattern to file auto-download notifications

**Event Payload:**
```json
{
  "job_id": "uuid",
  "printer_id": "bambu_001",
  "filename": "model.3mf",
  "discovery_time": "2025-01-08T10:30:00",
  "is_startup": false
}
```

**UI Components:**
```
Toast Notification:
🖨️ Auto-created job for model.3mf on Bambu A1 #01 [Edit] [Dismiss]

Job List Badge:
⚡ Auto  (with tooltip: "Auto-created at 10:30 AM")

One-time Tip (first auto-created job):
ℹ️ Jobs are now tracked automatically! You can edit details or disable
   this in Settings > Job Creation.
```

**Action Items:**
- [x] Define UI workflow
- [ ] Implement event emission (already in design)
- [ ] Create toast notification component
- [ ] Add job list badge
- [ ] Add one-time tip system
- [ ] Add edit shortcut from notification

---

##### 2. **Default Behavior** ✅

**Decision:**
- **Enabled by default** (opt-out, not opt-in)
- Same default for all users (business and hobby)
- Show one-time tip on first auto-created job explaining the feature
- Easy toggle in Settings page

**Rationale:**
- Solves primary problem: "missed jobs" issue
- Most users benefit from automatic tracking
- Opt-out allows power users to disable if unwanted
- Consistent with modern UX patterns (features enabled by default)
- Can always be disabled without data loss

**Settings UI:**
```
Job Creation Settings
─────────────────────
[ ✓ ] Automatically create jobs when prints start

      When enabled, Printernizer will automatically create job records when
      a printer starts printing. Jobs are marked as non-business by default
      and can be edited anytime.

      Default: Enabled
```

**Action Items:**
- [x] Define default behavior
- [ ] Set default to `true` in Settings
- [ ] Add Settings UI toggle
- [ ] Implement one-time tip
- [ ] Add help text explaining feature
- [ ] Document in user guide

---

##### 3. **Error Handling** ✅

**Decision:**
- **Log error** at ERROR level with full context
- **Continue monitoring** - don't crash or stop polling
- **Emit event** for UI notification (optional display)
- **No retry** - wait for next status update (30 seconds)
- **User notification** - show in UI activity log, not blocking alert

**Rationale:**
- Matches existing error handling in `PrinterMonitoringService`
- Resilient system - one failure shouldn't stop monitoring
- Structured logging already in place (structlog)
- Event system can route to UI notification center
- Auto-recovery via next polling cycle

**Implementation:**
```python
# Error handling (already in design doc)
try:
    job = await self.job_service.create_job(job_data)
    logger.info("Auto-created job", job_id=job.get('id'), ...)
    await self.event_service.emit_event("job_auto_created", {...})

except Exception as e:
    logger.error("Failed to auto-create job",
                printer_id=status.printer_id,
                filename=status.current_job,
                error=str(e),
                exc_info=True)

    # Emit event for UI notification
    await self.event_service.emit_event("job_auto_create_failed", {
        "printer_id": status.printer_id,
        "filename": status.current_job,
        "error": str(e),
        "timestamp": datetime.now().isoformat()
    })

    # Continue monitoring - will retry on next status update
```

**UI Notification:**
```
⚠️ Failed to auto-create job for model.3mf
   Will retry on next update. [Details] [Dismiss]
```

**Action Items:**
- [x] Define error handling strategy
- [ ] Implement error logging (already in design)
- [ ] Add error event emission
- [ ] Create UI error notification component
- [ ] Add activity log for errors
- [ ] Add retry counter metrics

---

## Summary of Decisions

| Question | Decision | Implementation | Phase |
|----------|----------|---------------|-------|
| **Bambu MQTT Fields** | Debug logging + field fallback | Add to Bambu integration | Phase 1 |
| **Cache Cleanup** | 2-hour LRU + state cleanup | Add cleanup methods | Phase 1 |
| **Job Service Integration** | Optional dependency pattern | Use existing pattern | Phase 1 |
| **Configuration** | File-based (v1) → DB (v2) | Settings + config.yaml | Phase 1 |
| **UI Workflow** | Silent + toast + edit shortcut | Event-driven | Phase 3 |
| **Default Behavior** | Enabled by default (opt-out) | Settings default=true | Phase 1 |
| **Error Handling** | Log + continue + emit event | Resilient error handling | Phase 1 |

**All questions resolved and ready for implementation!** ✅

## References

### Related Issues
- #XXX - Automated job tracking
- #XXX - Startup print detection

### Related Code
- `src/services/printer_service.py` - Main service
- `src/services/job_service.py` - Job management
- `src/printers/bambu_lab.py` - Bambu integration
- `src/printers/prusa.py` - Prusa integration
- `src/models/printer.py` - Data models

### External Documentation
- [Bambu Lab MQTT Protocol](https://github.com/Doridian/OpenBambuAPI)
- [PrusaLink API Documentation](https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml)

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 2025-01-08 | Claude & User | Initial design document |
