# Timelapse Management System - Design Document

**Date**: 2025-01-07
**Feature**: Automated Timelapse Video Creation
**Status**: 90% Implemented - Final Phase (Updated 2025-01-07)
**Last Updated**: 2025-01-07

## Overview

This document describes the design for a comprehensive timelapse management system for Printernizer. The system will automatically monitor configured folders for 3D print timelapse images, process them using FlickerFree's deflicker algorithm, and present completed videos in a gallery-focused UI.

### Goals

- **Automated Processing**: Monitor folders and auto-process when print completes
- **High Quality**: Integrate FlickerFree for flicker-free timelapse videos
- **User Control**: Manual trigger, configurable timeout, cleanup management
- **Smart Linking**: Automatically link videos to print jobs when possible
- **Gallery Experience**: Display and play timelapses with rich metadata
- **Cross-Platform**: Support Docker, standalone Python, and Home Assistant add-on

### Key User Workflows

1. **Automatic**: User adds images to subfolder → system detects completion → processes automatically → video appears in gallery
2. **Manual**: User clicks "Process Now" on discovered folder → immediate processing
3. **Viewing**: User browses gallery → clicks video → plays in modal with job info
4. **Cleanup**: System recommends old videos → user reviews and deletes

---

## Implementation Status

**Overall Progress**: 90% Complete

### ✅ Completed Components

#### 1. Database Layer (100%)
- ✅ Migration `012_add_timelapses.sql` created and structured
- ✅ Timelapses table with all required fields
- ✅ Foreign key relationship to jobs table
- ✅ Proper indexes for performance (status, job_id, created_at)
- ✅ All fields from design spec: tracking, metadata, processing, auto-detection, management

#### 2. Configuration (100%)
- ✅ All settings in `src/utils/config.py`:
  - `timelapse_enabled` (bool, default: False)
  - `timelapse_source_folder` (path)
  - `timelapse_output_folder` (path)
  - `timelapse_output_strategy` (same/separate/both)
  - `timelapse_auto_process_timeout` (seconds)
  - `timelapse_cleanup_age_days` (days)
  - `timelapse_flickerfree_path` (script path)
- ✅ Environment variable support
- ✅ Integration with existing settings system

#### 3. Service Layer (100%)
- ✅ `TimelapseService` fully implemented (1018 lines)
- ✅ Background tasks:
  - Folder monitoring (every 30 seconds)
  - Processing queue (every 10 seconds)
- ✅ Core functionality:
  - Folder scanning and discovery
  - Auto-detection with configurable timeout
  - Sequential processing queue
  - FlickerFree script execution
  - Smart job matching algorithm
  - Error handling and retry logic
- ✅ All public methods:
  - `get_timelapses()` - list with filters
  - `get_timelapse()` - single record
  - `trigger_processing()` - manual trigger
  - `delete_timelapse()` - delete video/record
  - `bulk_delete_timelapses()` - batch deletion
  - `toggle_pin()` - pin/unpin
  - `link_to_job()` - manual linking
  - `get_stats()` - statistics
  - `get_cleanup_candidates()` - old videos
- ✅ Service initialized in `src/main.py`
- ✅ Lifecycle management (start/shutdown)

#### 4. API Layer (95%)
- ✅ Router at `/api/v1/timelapses`
- ✅ Implemented endpoints:
  - `GET /api/v1/timelapses` - List timelapses
  - `GET /api/v1/timelapses/stats` - Statistics
  - `GET /api/v1/timelapses/{id}` - Get single
  - `POST /api/v1/timelapses/{id}/process` - Trigger
  - `DELETE /api/v1/timelapses/{id}` - Delete
  - `PATCH /api/v1/timelapses/{id}/link` - Link to job
  - `PATCH /api/v1/timelapses/{id}/pin` - Toggle pin
  - `GET /api/v1/timelapses/cleanup/candidates` - Cleanup list
  - `POST /api/v1/timelapses/bulk-delete` - Bulk delete
- ❌ **MISSING**: `GET /api/v1/timelapses/{id}/video` - Video file serving
  - **Impact**: Frontend references this endpoint but it doesn't exist
  - **Required**: FileResponse/StreamingResponse to serve MP4 files
  - **Pattern**: Similar to file serving in `src/api/routers/library.py:680-729`

#### 5. Frontend (100%)
- ✅ Complete UI implementation:
  - `frontend/js/timelapses.js` (709 lines)
  - `frontend/css/timelapses.css`
  - Navigation integration in `index.html`
  - Page structure with gallery layout
- ✅ Components:
  - `TimelapseManager` class - main controller
  - `TimelapseCard` class - gallery cards
  - `VideoPlayerModal` class - video playback
- ✅ Features:
  - Gallery grid layout
  - Status badges (discovered, pending, processing, completed, failed)
  - Filters (status, linked-only)
  - Stats dashboard
  - Processing queue indicator
  - Auto-refresh (30 seconds)
  - Empty state handling
- ✅ WebSocket integration:
  - Real-time event listeners for all states
  - Live UI updates
- ✅ API client methods in `frontend/js/api.js`
- ✅ All CRUD operations

#### 6. WebSocket Events (100%)
- ✅ All events implemented:
  - `timelapse.discovered`
  - `timelapse.pending`
  - `timelapse.processing`
  - `timelapse.progress`
  - `timelapse.completed`
  - `timelapse.failed`
  - `timelapse.deleted`
- ✅ Frontend handlers for all events
- ✅ Real-time UI updates

### ❌ Incomplete Components (10% Remaining)

#### 1. Video Serving Endpoint (HIGH PRIORITY)
**File**: `src/api/routers/timelapses.py`

**Missing Endpoint**:
```python
@router.get("/{id}/video")
async def get_timelapse_video(id: str):
    """Serve timelapse video file for playback"""
```

**Required Implementation**:
- Validate timelapse exists and has video file
- Check video file exists on disk
- Return `FileResponse` with appropriate headers
- Handle video streaming for large files
- Set correct MIME type (`video/mp4`)

**Reference Pattern**: See `src/api/routers/library.py:680-729` for file serving implementation

**Frontend Dependencies**:
- `frontend/js/timelapses.js:582` - video player source
- `frontend/js/timelapses.js:655` - download video link

#### 2. Docker Configuration (HIGH PRIORITY)

**Missing from both Docker files**:

**Standalone Docker** (`docker/Dockerfile`):
```dockerfile
# Install FlickerFree dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone FlickerFree repository
RUN git clone https://github.com/schmacka/FlickerFree.git /opt/flickerfree

# Make script executable
RUN chmod +x /opt/flickerfree/do_timelapse.sh

# Set default FlickerFree path
ENV TIMELAPSE_FLICKERFREE_PATH=/opt/flickerfree/do_timelapse.sh

# Create mount points
VOLUME ["/data/timelapse-images", "/data/timelapses"]
```

**Home Assistant Add-on** (`printernizer/Dockerfile`):
```dockerfile
# Install FlickerFree dependencies (Alpine Linux)
RUN apk add --no-cache \
    ffmpeg \
    git \
    bash

# Clone FlickerFree repository
RUN git clone https://github.com/schmacka/FlickerFree.git /opt/flickerfree

# Make script executable
RUN chmod +x /opt/flickerfree/do_timelapse.sh
```

**Also needed**: Update `printernizer/config.yaml` with timelapse options

#### 3. Documentation Updates (MEDIUM PRIORITY)
- ❌ Update README.md with timelapse feature documentation
- ❌ Update CHANGELOG.md with feature addition
- ❌ Add timelapse setup instructions for standalone users
- ❌ Document FlickerFree installation requirements

### Priority Action Items

**Before feature can be used**:
1. ⚠️ **CRITICAL**: Add video serving endpoint to API router
2. ⚠️ **CRITICAL**: Update Docker files to install FlickerFree + ffmpeg
3. ⚠️ **CRITICAL**: Test end-to-end with actual FlickerFree processing

**Post-implementation**:
4. 📝 Update README.md documentation
5. 📝 Update CHANGELOG.md
6. 📝 Add setup/installation guides
7. ✅ Comprehensive testing (unit + integration)

### Testing Status
- ❌ Unit tests not yet written
- ❌ Integration tests not yet written
- ❌ Manual testing pending (requires Docker updates)

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Gallery UI)                    │
│  - Video gallery grid with thumbnails and metadata          │
│  - Video player modal                                        │
│  - Processing queue status                                   │
│  - Settings configuration                                    │
│  - Storage usage and cleanup recommendations                │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ WebSocket (real-time updates)
                              │ REST API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                       │
│  GET    /api/v1/timelapses                                  │
│  POST   /api/v1/timelapses/{id}/process                     │
│  DELETE /api/v1/timelapses/{id}                             │
│  PATCH  /api/v1/timelapses/{id}/link                        │
│  ... (full API spec below)                                   │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  TimelapseService (Core Logic)               │
│  - Folder monitoring (every 30s)                            │
│  - Auto-detection with configurable timeout                 │
│  - Processing queue (sequential, one at a time)             │
│  - FlickerFree script execution                             │
│  - Smart job matching algorithm                             │
│  - Error handling and retry logic                           │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database (SQLite)                         │
│  timelapses table: tracks folders, videos, status, metadata │
│  jobs table: existing print jobs (for linking)              │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  File System Integration                     │
│  Source: /data/timelapse-images/*/                          │
│  Output: /data/timelapses/                                  │
│  FlickerFree: do_timelapse.sh script                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Models

### Database Schema

#### Table: `timelapses`

```sql
CREATE TABLE timelapses (
    -- Primary key
    id TEXT PRIMARY KEY,                    -- UUID

    -- Paths
    source_folder TEXT NOT NULL,            -- Absolute path to image folder
    output_video_path TEXT,                 -- Path to generated video (null until complete)

    -- Status tracking
    status TEXT NOT NULL,                   -- discovered|pending|processing|completed|failed

    -- Job linking
    job_id TEXT,                            -- FK to jobs table (nullable)

    -- Metadata
    folder_name TEXT NOT NULL,              -- Just folder name (for display)
    image_count INTEGER,                    -- Number of source images
    video_duration REAL,                    -- Duration in seconds (null until complete)
    file_size_bytes INTEGER,                -- Video file size

    -- Processing tracking
    processing_started_at TEXT,             -- ISO timestamp
    processing_completed_at TEXT,           -- ISO timestamp
    error_message TEXT,                     -- Error details if failed
    retry_count INTEGER DEFAULT 0,          -- Number of retry attempts

    -- Auto-detection
    last_image_detected_at TEXT,            -- Last time new image was found
    auto_process_eligible_at TEXT,          -- When auto-processing can trigger

    -- Management
    pinned BOOLEAN DEFAULT 0,               -- User pinned (exempt from cleanup)
    created_at TEXT NOT NULL,               -- Discovery timestamp
    updated_at TEXT NOT NULL,

    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX idx_timelapses_status ON timelapses(status);
CREATE INDEX idx_timelapses_job_id ON timelapses(job_id);
CREATE INDEX idx_timelapses_created_at ON timelapses(created_at);
```

### Pydantic Models

#### TimelapseStatus (Enum)

```python
class TimelapseStatus(str, Enum):
    DISCOVERED = "discovered"    # Folder found, monitoring for new images
    PENDING = "pending"          # Ready for processing (timeout reached or manual)
    PROCESSING = "processing"    # Currently creating video
    COMPLETED = "completed"      # Video successfully created
    FAILED = "failed"           # Processing error occurred
```

#### Timelapse (Response Model)

```python
class Timelapse(BaseModel):
    id: str
    source_folder: str
    output_video_path: Optional[str]
    status: TimelapseStatus
    job_id: Optional[str]

    folder_name: str
    image_count: Optional[int]
    video_duration: Optional[float]
    file_size_bytes: Optional[int]

    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int

    last_image_detected_at: Optional[datetime]
    auto_process_eligible_at: Optional[datetime]

    pinned: bool
    created_at: datetime
    updated_at: datetime

    # Computed properties
    age_days: int
    is_cleanup_candidate: bool
    linked_job_name: Optional[str]
    video_exists: bool  # Check if file actually exists on disk
```

---

## Configuration

### Pydantic Settings (src/utils/config.py)

Following Printernizer's established configuration pattern using Pydantic BaseSettings with environment variables:

```python
class PrinternizerSettings(BaseSettings):
    # ... existing settings ...

    # Timelapse Configuration
    timelapse_enabled: bool = Field(
        default=True,
        env="TIMELAPSE_ENABLED",
        description="Enable timelapse video creation feature"
    )

    timelapse_source_folder: str = Field(
        default="/app/data/timelapse-images",
        env="TIMELAPSE_SOURCE_FOLDER",
        description="Folder to watch for timelapse image subfolders"
    )

    timelapse_output_folder: str = Field(
        default="/app/data/timelapses",
        env="TIMELAPSE_OUTPUT_FOLDER",
        description="Folder for completed timelapse videos"
    )

    timelapse_output_strategy: str = Field(
        default="separate",
        env="TIMELAPSE_OUTPUT_STRATEGY",
        description="Video output location: same|separate|both"
    )

    timelapse_auto_process_timeout: int = Field(
        default=300,
        env="TIMELAPSE_AUTO_PROCESS_TIMEOUT",
        description="Seconds to wait after last image before auto-processing"
    )

    timelapse_cleanup_age_days: int = Field(
        default=30,
        env="TIMELAPSE_CLEANUP_AGE_DAYS",
        description="Age threshold for cleanup recommendations (days)"
    )

    timelapse_flickerfree_path: str = Field(
        default="/usr/local/bin/do_timelapse.sh",
        env="TIMELAPSE_FLICKERFREE_PATH",
        description="Path to FlickerFree do_timelapse.sh script"
    )
```

### Environment Variables (.env)

```bash
# Timelapse Configuration
TIMELAPSE_ENABLED=true
TIMELAPSE_SOURCE_FOLDER=/app/data/timelapse-images
TIMELAPSE_OUTPUT_FOLDER=/app/data/timelapses
TIMELAPSE_OUTPUT_STRATEGY=separate
TIMELAPSE_AUTO_PROCESS_TIMEOUT=300
TIMELAPSE_CLEANUP_AGE_DAYS=30
TIMELAPSE_FLICKERFREE_PATH=/usr/local/bin/do_timelapse.sh
```

### User-Configurable Settings (via UI)

Expose in `/api/v1/settings` endpoint following existing patterns:

**Runtime-modifiable settings:**
- `timelapse_enabled` - Enable/disable feature
- `timelapse_source_folder` - Source folder path
- `timelapse_output_folder` - Output folder path
- `timelapse_output_strategy` - Output strategy (same/separate/both)
- `timelapse_auto_process_timeout` - Auto-process timeout (0 = manual only)
- `timelapse_cleanup_age_days` - Cleanup recommendation threshold
- `timelapse_flickerfree_path` - Path to FlickerFree script

Settings are persisted to `.env` file via existing `_persist_settings_to_env()` mechanism in ConfigService.

---

## Service Implementation

### TimelapseService

#### Core Responsibilities

1. **Folder Monitoring**: Scan source folder for subfolders with images
2. **Auto-Detection**: Track new images and trigger processing after timeout
3. **Processing Queue**: Manage sequential video creation
4. **FlickerFree Integration**: Execute script and handle errors
5. **Job Matching**: Link videos to existing print jobs
6. **Status Management**: Track lifecycle of each timelapse

#### Key Methods

##### `_scan_source_folders()` - Folder Monitoring

**Runs**: Every 30 seconds (background task)

**Logic**:
1. List subfolders in `timelapse_source_folder`
2. For each subfolder:
   - Count image files (*.jpg, *.png, *.jpeg)
   - If not tracked: create new `timelapses` record with status=`discovered`
   - If tracked:
     - Check if image count increased
     - Update `last_image_detected_at` if new images found
     - Calculate `auto_process_eligible_at` = last_image_detected + timeout
     - If timeout reached and status=`discovered`: update status to `pending`

**Error Handling**:
- Log folder access errors (network share disconnection)
- Retry on transient errors
- Show configuration error if source folder invalid

##### `_process_queue()` - Processing Queue Manager

**Runs**: Every 10 seconds (background task)

**Logic**:
1. Check if any timelapse currently has status=`processing`
2. If none processing:
   - Query for status=`pending` ordered by `auto_process_eligible_at` ASC
   - Start processing first pending timelapse
   - Call `_process_timelapse(timelapse_id)` in background task

**Queue Behavior**:
- Sequential processing (one at a time)
- Prevents system overload from multiple FlickerFree instances
- FIFO order based on when timeout was reached

##### `_process_timelapse(timelapse_id)` - Video Creation

**Logic**:
1. Load timelapse record from database
2. Update status to `processing`, set `processing_started_at`
3. Emit WebSocket event: `timelapse.processing`
4. Determine output video path based on `output_strategy`:
   - `same`: Output in source folder
   - `separate`: Output in `timelapse_output_folder`
   - `both`: Output in both locations
5. Build command: `do_timelapse.sh <source_folder> <output_path>`
6. Execute subprocess with:
   - 30-minute timeout (configurable)
   - Capture stdout/stderr
   - Stream progress updates via WebSocket
7. On success:
   - Update status to `completed`
   - Store `output_video_path`, `file_size_bytes`
   - Calculate `video_duration` from file metadata
   - Set `processing_completed_at`
   - Run smart job matching: `_match_to_job(timelapse_id)`
   - Emit WebSocket event: `timelapse.completed`
8. On failure:
   - Increment `retry_count`
   - If `retry_count < 1`:
     - Reset status to `pending` for one automatic retry
   - Else:
     - Set status to `failed`
     - Store `error_message` with parsed error details
   - Emit WebSocket event: `timelapse.failed`

**Error Parsing**:
- Missing ffmpeg: "FlickerFree requires ffmpeg to be installed"
- Insufficient disk space: "Not enough disk space to create video"
- Corrupted images: "Unable to read image files"
- Timeout: "Processing exceeded 30-minute timeout"

##### `_match_to_job(timelapse_id)` - Smart Job Matching

**Logic**:
1. Extract patterns from folder name:
   - Dates (YYYY-MM-DD, YYYYMMDD, etc.)
   - Filenames (e.g., "model_v2.3mf")
   - Printer names (e.g., "bambu_lab_a1")
2. Query jobs table for potential matches:
   - Match by filename (exact or fuzzy)
   - Match by date range (±1 day)
   - Match by printer name
3. If exactly one confident match found:
   - Set `job_id` field
   - Log match details
4. If multiple matches or no matches:
   - Leave `job_id` as null
   - Log matching attempts for debugging

**Confidence Scoring**:
- Exact filename match: 100%
- Fuzzy filename match: 70%
- Date within range: 50%
- Printer name match: 30%
- Threshold: 80% for auto-linking

##### Public API Methods

```python
async def get_timelapses(
    status: Optional[TimelapseStatus] = None,
    linked_only: bool = False
) -> List[Timelapse]:
    """List timelapses with optional filters"""

async def get_timelapse(timelapse_id: str) -> Timelapse:
    """Get specific timelapse details"""

async def trigger_processing(timelapse_id: str) -> Timelapse:
    """Manually trigger processing (set status to pending)"""

async def link_to_job(timelapse_id: str, job_id: str) -> Timelapse:
    """Manually link timelapse to job"""

async def toggle_pin(timelapse_id: str) -> Timelapse:
    """Toggle pinned status"""

async def delete_timelapse(timelapse_id: str) -> None:
    """Delete video and database record"""

async def get_cleanup_candidates() -> List[Timelapse]:
    """Get videos older than cleanup_age_days and not pinned"""

async def bulk_delete(timelapse_ids: List[str]) -> Dict[str, int]:
    """Delete multiple timelapses, return success/failure counts"""

async def get_stats() -> TimelapseStats:
    """Get storage usage, queue status, and counts"""
```

#### Background Tasks

```python
async def start(self):
    """Start background tasks"""
    if not self.settings.timelapse_enabled:
        logger.info("Timelapse feature disabled")
        return

    # Verify FlickerFree script exists
    if not Path(self.settings.timelapse_flickerfree_path).exists():
        logger.warning(f"FlickerFree script not found at {self.settings.timelapse_flickerfree_path}")
        logger.warning("Timelapse feature will be unavailable")
        return

    # Start background tasks
    asyncio.create_task(self._folder_monitor_loop())
    asyncio.create_task(self._process_queue_loop())

async def _folder_monitor_loop(self):
    """Run folder scanning every 30 seconds"""
    while True:
        try:
            await self._scan_source_folders()
        except Exception as e:
            logger.error(f"Folder monitoring error: {e}")
        await asyncio.sleep(30)

async def _process_queue_loop(self):
    """Run queue processing every 10 seconds"""
    while True:
        try:
            await self._process_queue()
        except Exception as e:
            logger.error(f"Queue processing error: {e}")
        await asyncio.sleep(10)
```

---

## API Specification

### REST Endpoints

#### GET /api/v1/timelapses

**Description**: List all timelapses with optional filters

**Query Parameters**:
- `status` (optional): Filter by status (discovered|pending|processing|completed|failed)
- `linked_only` (optional, boolean): Show only timelapses linked to jobs
- `limit` (optional, integer): Limit results (default: 100)
- `offset` (optional, integer): Pagination offset

**Response**: `List[Timelapse]`

#### GET /api/v1/timelapses/{id}

**Description**: Get specific timelapse details

**Response**: `Timelapse`

#### POST /api/v1/timelapses/{id}/process

**Description**: Manually trigger processing (immediate, bypasses timeout)

**Response**: `Timelapse` (status changed to pending)

#### DELETE /api/v1/timelapses/{id}

**Description**: Delete video file and database record

**Response**: `204 No Content`

#### PATCH /api/v1/timelapses/{id}/link

**Description**: Manually link timelapse to job

**Request Body**:
```json
{
  "job_id": "uuid-of-job"
}
```

**Response**: `Timelapse`

#### PATCH /api/v1/timelapses/{id}/pin

**Description**: Toggle pinned status

**Response**: `Timelapse`

#### GET /api/v1/timelapses/stats

**Description**: Get storage usage and queue statistics

**Response**:
```json
{
  "total_videos": 42,
  "total_size_bytes": 5368709120,
  "discovered_count": 3,
  "pending_count": 1,
  "processing_count": 1,
  "completed_count": 35,
  "failed_count": 2,
  "cleanup_candidates_count": 8
}
```

#### GET /api/v1/timelapses/cleanup

**Description**: Get videos recommended for deletion (older than threshold, not pinned)

**Response**: `List[Timelapse]`

#### POST /api/v1/timelapses/bulk-delete

**Description**: Delete multiple timelapses

**Request Body**:
```json
{
  "timelapse_ids": ["uuid1", "uuid2", "uuid3"]
}
```

**Response**:
```json
{
  "deleted": 3,
  "failed": 0,
  "errors": []
}
```

### WebSocket Events

All events published to WebSocket clients for real-time UI updates:

#### timelapse.discovered

**Payload**:
```json
{
  "event": "timelapse.discovered",
  "data": {
    "id": "uuid",
    "folder_name": "print_job_abc",
    "image_count": 1250,
    "status": "discovered"
  }
}
```

#### timelapse.processing

**Payload**:
```json
{
  "event": "timelapse.processing",
  "data": {
    "id": "uuid",
    "folder_name": "print_job_abc",
    "status": "processing"
  }
}
```

#### timelapse.progress

**Payload**:
```json
{
  "event": "timelapse.progress",
  "data": {
    "id": "uuid",
    "progress_percent": 45,
    "current_step": "Deflickering frames"
  }
}
```

#### timelapse.completed

**Payload**:
```json
{
  "event": "timelapse.completed",
  "data": {
    "id": "uuid",
    "folder_name": "print_job_abc",
    "status": "completed",
    "output_video_path": "/data/timelapses/print_job_abc.mp4",
    "video_duration": 45.2,
    "file_size_bytes": 125829120,
    "job_id": "linked-job-uuid-or-null"
  }
}
```

#### timelapse.failed

**Payload**:
```json
{
  "event": "timelapse.failed",
  "data": {
    "id": "uuid",
    "folder_name": "print_job_abc",
    "status": "failed",
    "error_message": "FlickerFree requires ffmpeg to be installed",
    "retry_count": 1
  }
}
```

#### timelapse.deleted

**Payload**:
```json
{
  "event": "timelapse.deleted",
  "data": {
    "id": "uuid"
  }
}
```

---

## Frontend Implementation

### New Section: Timelapses

#### Gallery View (`frontend/timelapses.html`)

**Layout**:
- Header with filters, search, and processing queue status
- Gallery grid (responsive, similar to Files section)
- Storage usage dashboard (total size, cleanup recommendations)

**Video Cards**:
- Thumbnail (extracted from video or placeholder)
- Title (folder name)
- Metadata: duration, file size, age, status badge
- Linked job indicator (if job_id set)
- Action buttons: play, link, pin, delete, retry (context-aware)

**Status Badges**:
- Discovered: Blue badge
- Pending: Orange badge with countdown
- Processing: Animated spinner with progress bar
- Completed: Green badge
- Failed: Red badge with error icon

**Filters**:
- Status dropdown (all/discovered/pending/processing/completed/failed)
- Age filter (all/recent/old)
- Linked filter (all/linked/unlinked)
- Pinned filter (all/pinned/unpinned)

**Processing Queue Indicator** (top of page):
- Shows current processing video
- Shows queue count (e.g., "2 pending")
- Progress bar for current processing

#### Video Player Modal

**Triggered by**: Clicking play button on video card

**Content**:
- Full video player (HTML5 video element)
- Playback controls (play/pause, seek, volume, fullscreen)
- Metadata panel:
  - Folder name
  - Duration, file size, creation date
  - Linked job info (if job_id set): job name, printer, date
  - "Link to Job" button if not linked
- Actions: pin, download, delete

#### Settings Integration (`frontend/settings.html`)

**New Section**: "Timelapses"

**Settings Fields**:
1. **Enable Timelapses** - Toggle switch
2. **Source Folder** - Text input with folder picker and validation
3. **Output Folder** - Text input with folder picker and validation
4. **Output Strategy** - Dropdown (same folder / separate folder / both)
5. **Auto-Process Timeout** - Slider (0-60 minutes, 0 = manual only)
   - Shows countdown in UI for pending folders
6. **Cleanup Age Threshold** - Slider (7-90 days)
   - Used for cleanup recommendations
7. **FlickerFree Script Path** - Text input with file picker
8. **Test Configuration** - Button
   - Validates paths exist and are accessible
   - Checks FlickerFree script exists and is executable
   - Shows success/error message

#### Job Integration (existing `jobs.html`)

**Enhancement**: Add timelapse section to job detail view

**Display**:
- If job has linked timelapse(s):
  - Show video thumbnail(s)
  - Play inline or "Open in Timelapses" link
  - Link to full gallery view

### WebSocket Integration

**Connection**: Reuse existing WebSocket connection pattern

**Event Handlers**:
```javascript
socket.on('timelapse.discovered', (data) => {
  // Add new card to gallery
  // Show notification
});

socket.on('timelapse.processing', (data) => {
  // Update card to show processing state
  // Show progress bar
  // Update queue indicator
});

socket.on('timelapse.progress', (data) => {
  // Update progress bar
  // Update current step text
});

socket.on('timelapse.completed', (data) => {
  // Update card to completed state
  // Load video thumbnail
  // Show success notification
  // Update storage stats
});

socket.on('timelapse.failed', (data) => {
  // Update card to failed state
  // Show error badge
  // Show retry button
  // Show error notification
});

socket.on('timelapse.deleted', (data) => {
  // Remove card from gallery
  // Update storage stats
});
```

### Storage Usage Dashboard

**Display**:
- Total videos count
- Total storage used (formatted, e.g., "5.2 GB")
- Cleanup candidates count (videos older than threshold)
- "Review Cleanup" button → opens cleanup modal

**Cleanup Modal**:
- List of cleanup candidates with age and size
- Checkboxes for bulk selection
- "Delete Selected" button with confirmation
- Shows space to be freed

---

## Deployment Strategy

### Docker Image

**Dockerfile additions**:
```dockerfile
# Install FlickerFree dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone FlickerFree repository
RUN git clone https://github.com/schmacka/FlickerFree.git /opt/flickerfree

# Make script executable
RUN chmod +x /opt/flickerfree/do_timelapse.sh

# Set default FlickerFree path
ENV TIMELAPSE_FLICKERFREE_PATH=/opt/flickerfree/do_timelapse.sh

# Create mount points
VOLUME ["/data/timelapse-images", "/data/timelapses"]
```

**docker-compose.yml additions**:
```yaml
volumes:
  - ./data/timelapse-images:/data/timelapse-images
  - ./data/timelapses:/data/timelapses

environment:
  - TIMELAPSE_ENABLED=true
  - TIMELAPSE_SOURCE_FOLDER=/data/timelapse-images
  - TIMELAPSE_OUTPUT_FOLDER=/data/timelapses
```

### Standalone Python

**Installation Documentation**:

```markdown
## Timelapse Feature Setup

The timelapse feature requires FlickerFree to be installed separately.

### Install FlickerFree

1. Clone the FlickerFree repository:
   ```bash
   git clone https://github.com/schmacka/FlickerFree.git
   cd FlickerFree
   chmod +x do_timelapse.sh
   ```

2. Install dependencies:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install ffmpeg

   # macOS
   brew install ffmpeg

   # Windows
   # Download ffmpeg from https://ffmpeg.org/download.html
   ```

3. Configure Printernizer:
   - Set `TIMELAPSE_FLICKERFREE_PATH` in `.env`:
     ```
     TIMELAPSE_FLICKERFREE_PATH=/path/to/FlickerFree/do_timelapse.sh
     ```
   - Or configure path in Settings UI after startup

### Configuration

Edit `.env` file:
```
TIMELAPSE_ENABLED=true
TIMELAPSE_SOURCE_FOLDER=/path/to/timelapse-images
TIMELAPSE_OUTPUT_FOLDER=/path/to/timelapses
TIMELAPSE_FLICKERFREE_PATH=/path/to/FlickerFree/do_timelapse.sh
```
```

**Auto-Detection**:
- Check common paths on startup:
  - `/usr/local/bin/do_timelapse.sh`
  - `/opt/flickerfree/do_timelapse.sh`
  - `~/FlickerFree/do_timelapse.sh`
- If found, auto-configure path
- If not found, show warning in UI and disable feature

**Graceful Degradation**:
- Feature disabled if FlickerFree not found
- Show warning message in Settings: "FlickerFree not installed - timelapse feature unavailable"
- Provide installation instructions link

### Home Assistant Add-on

**config.yaml additions**:
```yaml
options:
  timelapse_enabled: true
  timelapse_source_folder: "/share/timelapse-images"
  timelapse_output_folder: "/share/timelapses"
  timelapse_auto_process_timeout: 300
  timelapse_cleanup_age_days: 30

schema:
  timelapse_enabled: bool?
  timelapse_source_folder: str?
  timelapse_output_folder: str?
  timelapse_auto_process_timeout: int(0,3600)?
  timelapse_cleanup_age_days: int(7,90)?
```

**Add-on Dockerfile**:
- Include FlickerFree in container (same as Docker image above)
- Pre-configure paths to use Home Assistant share directory

**Network Share Support**:
- Document how to mount network shares in Home Assistant
- Support SMB/CIFS paths for source folder
- Handle connection errors gracefully

**CHANGELOG entry**:
```markdown
## [X.X.X] - YYYY-MM-DD

### Added
- Timelapse management system with FlickerFree integration
- Automated folder monitoring and video processing
- Gallery UI for viewing and managing timelapses
- Smart job linking with manual override
- Storage usage and cleanup recommendations
```

---

## Error Handling

### FlickerFree Script Errors

**Common Errors and Messages**:

| Error | Detection | User Message | Recovery |
|-------|-----------|--------------|----------|
| Missing ffmpeg | Stderr contains "ffmpeg: not found" | "FlickerFree requires ffmpeg to be installed. [Installation Guide]" | Manual installation |
| Disk space | Stderr contains "No space left" | "Not enough disk space to create video. Free up space and retry." | Free space, retry |
| Corrupted images | Stderr contains "decode error" | "Unable to read one or more image files. Check source folder." | Manual inspection |
| Timeout | Process exceeds 30 min | "Processing exceeded 30-minute timeout. Try with fewer images or increase timeout." | Increase timeout, retry |
| Script not found | Path doesn't exist | "FlickerFree script not found at configured path. [Configuration Guide]" | Configure path |
| Permission denied | Exit code 126 | "Permission denied executing FlickerFree script. Check file permissions." | Fix permissions |

**Error Storage**:
- Full stderr output stored in `error_message` field
- Parsed user-friendly message shown in UI
- Raw error available in expandable details section

**Recovery Actions**:
- Automatic retry: Once (for transient errors)
- Manual retry button: Always available for failed timelapses
- "View Logs" button: Opens logs with filtered output for this timelapse

### Folder Access Errors

**Source Folder Issues**:
- Not readable: Show config error in UI, disable monitoring
- Network share disconnected: Log warning, retry scan on next interval
- Subfolder deleted during processing: Mark as failed, clean up partial output

**Output Folder Issues**:
- Not writable: Show config error in UI, disable processing
- Insufficient space: Fail with actionable message, show cleanup recommendations

**Validation on Settings Update**:
- Check source folder exists and is readable
- Check output folder exists and is writable
- Show immediate feedback in settings UI
- Prevent saving invalid configuration

### Processing Edge Cases

**Scenarios**:
1. **No images in folder**: Skip processing, log warning
2. **Only one image**: Process anyway (single-frame video)
3. **Mixed image formats**: FlickerFree handles this automatically
4. **Partial folder deletion**: Detect missing source during processing, fail gracefully
5. **Output file already exists**: Overwrite with warning, or append timestamp
6. **FlickerFree process killed externally**: Detect abnormal termination, mark as failed

**Concurrent Processing Prevention**:
- Lock mechanism: Only one `status=processing` timelapse at a time
- Queue remaining requests
- If processing timelapse deleted: Release lock immediately

---

## Testing Strategy

### Unit Tests

**TimelapseService Tests** (`tests/services/test_timelapse_service.py`):
- Folder scanning: discovery, image counting, status transitions
- Timeout calculation: auto_process_eligible_at logic
- Status transitions: discovered → pending → processing → completed
- Error handling: script failures, timeouts, retries
- Job matching: pattern extraction, confidence scoring
- Pinning: cleanup exemption logic

**API Tests** (`tests/api/test_timelapses.py`):
- CRUD operations: create, read, update, delete
- Filtering: by status, linked_only, age
- Pagination: limit, offset
- Validation: invalid IDs, duplicate processing requests
- Authorization: if/when auth is implemented

**Configuration Tests** (`tests/test_config.py`):
- Settings validation: paths, timeout ranges
- Environment variable parsing
- Default value handling

### Integration Tests

**Full Workflow Tests** (`tests/integration/test_timelapse_workflow.py`):

**Mock FlickerFree Script**:
```bash
#!/bin/bash
# tests/fixtures/mock_do_timelapse.sh

# Simulate processing time
sleep 2

# Create dummy output video
touch "$2"  # $2 is output path
echo "Mock video created successfully"
exit 0
```

**Test Scenarios**:
1. **Happy path**: Discover folder → timeout → process → complete → job match
2. **Manual trigger**: Discover folder → manual trigger → process → complete
3. **Script failure**: Mock script exit 1 → retry → fail
4. **Timeout**: Mock script sleep 60 → timeout → fail
5. **Output strategies**: Test same/separate/both folder creation
6. **Cleanup**: Create old videos → get recommendations → delete
7. **Pinning**: Pin video → verify excluded from cleanup

**WebSocket Tests**:
- Verify events emitted for each status transition
- Verify payload structure
- Verify multiple clients receive events

### Manual Testing Checklist

**Setup**:
- [ ] Install FlickerFree locally
- [ ] Configure source and output folders
- [ ] Create test image sequences (e.g., 100 images)

**Functionality**:
- [ ] Auto-discovery: Add folder, verify discovered status
- [ ] Auto-processing: Wait for timeout, verify processing starts
- [ ] Manual trigger: Click "Process Now", verify immediate processing
- [ ] Video creation: Verify video file created in correct location(s)
- [ ] Job linking: Verify smart matching works, test manual override
- [ ] Gallery view: Verify videos display, thumbnails load, metadata correct
- [ ] Video player: Play video, verify controls work
- [ ] Filtering: Test all filter combinations
- [ ] Cleanup: Verify recommendations, test bulk delete
- [ ] Pinning: Pin video, verify excluded from cleanup
- [ ] Settings: Update all settings, verify persisted to .env

**Error Scenarios**:
- [ ] Missing ffmpeg: Uninstall ffmpeg, verify error message
- [ ] Disk space: Fill disk, verify error and recovery
- [ ] Corrupted images: Add invalid image file, verify error
- [ ] Script timeout: Process large folder, verify timeout handling
- [ ] Network share disconnect: Disconnect during monitoring, verify resilience

**UI/UX**:
- [ ] Responsive design: Test on mobile, tablet, desktop
- [ ] Real-time updates: Verify WebSocket events update UI immediately
- [ ] Loading states: Verify spinners and progress bars
- [ ] Error messages: Verify user-friendly and actionable
- [ ] Notifications: Verify appropriate toasts for success/error

**Performance**:
- [ ] Large folders: Test with 1000+ images
- [ ] Many timelapses: Test with 50+ tracked folders
- [ ] Concurrent operations: Add multiple folders simultaneously

---

## Database Migration

### Migration File: `migrations/009_add_timelapses.sql`

```sql
-- Migration: Add timelapses table
-- Date: 2025-01-07
-- Description: Create timelapses table for timelapse management system

CREATE TABLE IF NOT EXISTS timelapses (
    -- Primary key
    id TEXT PRIMARY KEY,

    -- Paths
    source_folder TEXT NOT NULL,
    output_video_path TEXT,

    -- Status tracking
    status TEXT NOT NULL,

    -- Job linking
    job_id TEXT,

    -- Metadata
    folder_name TEXT NOT NULL,
    image_count INTEGER,
    video_duration REAL,
    file_size_bytes INTEGER,

    -- Processing tracking
    processing_started_at TEXT,
    processing_completed_at TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Auto-detection
    last_image_detected_at TEXT,
    auto_process_eligible_at TEXT,

    -- Management
    pinned INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_timelapses_status ON timelapses(status);
CREATE INDEX IF NOT EXISTS idx_timelapses_job_id ON timelapses(job_id);
CREATE INDEX IF NOT EXISTS idx_timelapses_created_at ON timelapses(created_at);

-- Update migration version
INSERT INTO schema_migrations (version, applied_at)
VALUES ('009_add_timelapses', datetime('now'));
```

### Migration Rollback

```sql
-- Rollback: Remove timelapses table
DROP INDEX IF EXISTS idx_timelapses_created_at;
DROP INDEX IF EXISTS idx_timelapses_job_id;
DROP INDEX IF EXISTS idx_timelapses_status;
DROP TABLE IF EXISTS timelapses;

DELETE FROM schema_migrations WHERE version = '009_add_timelapses';
```

---

## Performance Considerations

### Folder Scanning Optimization

**Challenges**:
- Scanning large directories can be slow
- Counting files repeatedly is expensive
- Network share access adds latency

**Optimizations**:
1. **Cache image counts**: Only recount if folder mtime changed
2. **Limit recursion**: Only scan 1 level deep (no nested subfolders)
3. **Debounce rapid changes**: Batch updates if multiple images added quickly
4. **Parallel scanning**: Use asyncio to scan multiple folders concurrently
5. **Skip hidden folders**: Ignore folders starting with `.`

**Expected Performance**:
- 100 folders: < 1 second scan time
- 1000 folders: < 5 seconds scan time

### Video Processing

**Resource Usage**:
- CPU: High during deflicker and encoding
- Memory: Proportional to image count and resolution
- Disk I/O: Heavy during read and write operations

**Optimizations**:
1. **Sequential processing**: Prevent system overload
2. **Stream subprocess output**: Avoid buffering entire output in memory
3. **Cleanup temp files**: FlickerFree creates intermediate files
4. **Configurable timeout**: Allow user to increase for large jobs
5. **Process priority**: Run FlickerFree with lower priority (nice value)

**Expected Performance**:
- 100 images (1080p): ~2-3 minutes
- 500 images (1080p): ~10-15 minutes
- 1000 images (1080p): ~20-30 minutes

### Storage Management

**Efficient Queries**:
- Cleanup candidates: Use indexed `created_at` column
- Status filtering: Use indexed `status` column
- Avoid N+1 queries: Fetch jobs with single JOIN query

**Storage Tracking**:
- Cache total storage size (update on video creation/deletion)
- Avoid scanning filesystem repeatedly
- Store file size in database for quick totals

### WebSocket Event Throttling

**Challenge**: Too many events can overwhelm clients

**Optimizations**:
1. **Batch progress updates**: Send progress every 5 seconds, not every frame
2. **Debounce status changes**: Wait 100ms before emitting state changes
3. **Room-based broadcasting**: Only send to clients viewing timelapses section

---

## Security Considerations

### Path Traversal Prevention

**Risk**: Malicious folder names could access files outside configured directories

**Mitigation**:
- Validate all paths are within configured source/output folders
- Use `Path.resolve()` to canonicalize paths
- Reject paths containing `..` or absolute paths

### Command Injection Prevention

**Risk**: Folder names could inject shell commands

**Mitigation**:
- Use `subprocess.run()` with list arguments (not shell=True)
- Escape all arguments passed to FlickerFree script
- Validate folder names match allowed pattern: `^[a-zA-Z0-9_-]+$`

### File System Access Control

**Permissions**:
- Source folder: Read-only access sufficient
- Output folder: Read-write access required
- Validate permissions on startup and settings update

### Resource Limits

**Prevent abuse**:
- Max video processing time (30 minutes default)
- Max concurrent folders tracked (e.g., 1000)
- Max video file size warning (e.g., 1 GB)

---

## Future Enhancements

### Phase 2 Features (Not in Initial Implementation)

1. **Cancellation Support**
   - Cancel button for in-progress processing
   - Kill subprocess gracefully

2. **Advanced Job Matching**
   - Machine learning-based matching
   - User feedback to improve algorithm

3. **Video Editing**
   - Trim start/end
   - Adjust speed
   - Add overlays (timestamp, temperature graph)

4. **Batch Processing**
   - Process multiple folders in parallel (configurable max)
   - Priority queue

5. **Notifications**
   - Email when video completes
   - Push notifications (if mobile app)

6. **Cloud Storage Integration**
   - Upload completed videos to S3, Google Drive, etc.
   - Automatic archival of old videos

7. **Advanced Cleanup**
   - Automatic deletion based on rules
   - Archive instead of delete

8. **Analytics**
   - Track processing times
   - Storage usage trends
   - Most-viewed videos

---

## Implementation Phases

### Phase 1: Backend Foundation ✅ COMPLETE

**Tasks**:
1. ✅ Create database migration (`012_add_timelapses.sql`)
2. ✅ Add configuration to `PrinternizerSettings`
3. ✅ Create `TimelapseService` skeleton
4. ✅ Implement folder monitoring (`_scan_source_folders`)
5. ✅ Implement basic status transitions
6. ✅ Create API router with basic endpoints

**Deliverable**: ✅ Backend can discover folders and track status

### Phase 2: FlickerFree Integration ✅ COMPLETE

**Tasks**:
1. ✅ Implement `_process_timelapse` with subprocess execution
2. ✅ Add error parsing and retry logic
3. ✅ Implement processing queue (`_process_queue`)
4. ✅ Add WebSocket event emission
5. ✅ Implement smart job matching

**Deliverable**: ✅ Backend can create videos end-to-end

### Phase 3: Frontend Gallery ✅ COMPLETE

**Tasks**:
1. ✅ Create `timelapses.html` with gallery grid
2. ✅ Implement video cards with status badges
3. ✅ Create video player modal
4. ✅ Add filtering and sorting
5. ✅ Implement WebSocket event handlers
6. ✅ Add real-time status updates

**Deliverable**: ✅ Users can view and play timelapses (pending video serving endpoint)

### Phase 4: Settings & Management ✅ COMPLETE

**Tasks**:
1. ✅ Add timelapses settings section to settings UI
2. ✅ Implement configuration validation
3. ✅ Add storage usage dashboard
4. ✅ Implement cleanup recommendations
5. ✅ Add bulk delete functionality
6. ✅ Implement pinning feature

**Deliverable**: ✅ Users can configure and manage timelapses

### Phase 5: Deployment & Testing ⚠️ IN PROGRESS (90% Complete)

**Completed Tasks**:
1. ✅ Service integration in `src/main.py`
2. ✅ Complete API router implementation (except video serving)
3. ✅ Frontend fully integrated
4. ✅ WebSocket events fully implemented

**Remaining Tasks**:
1. ❌ **Add video serving endpoint** (`GET /api/v1/timelapses/{id}/video`)
2. ❌ **Update Docker image with FlickerFree** (`docker/Dockerfile`)
3. ❌ **Update Home Assistant add-on** (`printernizer/Dockerfile` + `config.yaml`)
4. ❌ Write installation documentation
5. ❌ Write unit tests
6. ❌ Write integration tests
7. ❌ Manual testing and bug fixes
8. ❌ Update CHANGELOG and README

**Deliverable**: Feature ready for production release

**Next Steps**:
1. Implement video serving endpoint (reference: `src/api/routers/library.py:680-729`)
2. Update both Docker files to install ffmpeg, git, and clone FlickerFree
3. Test end-to-end functionality
4. Write comprehensive tests
5. Document feature in README and CHANGELOG

---

## Success Metrics

### Technical Metrics

- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Zero critical bugs in manual testing
- [ ] Performance targets met (scan < 5s, processing < 30min)
- [ ] Error handling covers all common scenarios

### User Experience Metrics

- [ ] Configuration takes < 5 minutes
- [ ] Videos appear in gallery automatically
- [ ] Error messages are clear and actionable
- [ ] UI is responsive and real-time
- [ ] Cleanup workflow is intuitive

### Deployment Metrics

- [ ] Docker image builds successfully
- [ ] Standalone Python installation documented and tested
- [ ] Home Assistant add-on tested and working
- [ ] Documentation complete and accurate

---

## Conclusion

This design provides a comprehensive timelapse management system that integrates seamlessly with Printernizer's existing architecture. The system follows established patterns for configuration, service implementation, API design, and frontend development.

Key strengths of this design:
- **Automated workflow** with manual override options
- **Flexible deployment** across all Printernizer installation methods
- **User-friendly** gallery and management interface
- **Robust error handling** with clear recovery paths
- **Scalable architecture** ready for future enhancements

### Implementation Progress Summary

**✅ Phases 1-4 Complete (90%)**:
- Full backend implementation (service, database, configuration)
- Comprehensive frontend gallery UI
- Real-time WebSocket integration
- Complete management features (pin, link, delete, cleanup)

**⚠️ Phase 5 In Progress (10% remaining)**:
- Missing video serving endpoint (critical for playback)
- Docker deployments need FlickerFree integration
- Documentation and testing pending

### Critical Next Steps

1. **Add video serving endpoint** to `src/api/routers/timelapses.py`:
   ```python
   @router.get("/{id}/video")
   async def get_timelapse_video(id: str) -> FileResponse:
       """Serve timelapse video file for streaming/download"""
   ```

2. **Update Docker files** to install FlickerFree:
   - `docker/Dockerfile` (Debian-based)
   - `printernizer/Dockerfile` (Alpine-based for HA)

3. **Test end-to-end** with actual timelapse processing

4. **Document** the feature in README and CHANGELOG

The implementation is very close to completion - the core functionality is fully built and just needs the final integration pieces to be production-ready.
