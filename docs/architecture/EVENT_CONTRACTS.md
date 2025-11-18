# Event Contracts Documentation

**Version:** 1.0
**Date:** November 8, 2025
**Phase:** Phase 2 - Circular Dependency Resolution

---

## Overview

Printernizer uses an event-driven architecture to decouple services and prevent circular dependencies. This document provides a comprehensive reference of all events in the system, their payload schemas, emitters, and subscribers.

## Event System Architecture

### Core Components

- **EventService** (`src/services/event_service.py`): Central event bus that manages subscriptions and event emission
- **Event Emitters**: Services that publish events when state changes occur
- **Event Subscribers**: Services that react to events asynchronously

### Event Flow Pattern

```
[Service A] → emit_event() → [EventService] → notify subscribers → [Service B, C, D...]
```

### Key Principles

1. **Decoupling**: Services communicate through events, not direct method calls
2. **Asynchronous**: Event handlers run asynchronously to avoid blocking
3. **Error Isolation**: Exceptions in handlers don't propagate to emitters
4. **Late Binding**: Services set dependencies via setters to avoid circular imports

---

## Event Categories

### 1. Printer Connection Events
### 2. Printer Monitoring Events
### 3. Printer Control Events
### 4. File Discovery Events
### 5. File Download Events
### 6. File Processing Events
### 7. Job Lifecycle Events
### 8. Library Management Events
### 9. Material Management Events
### 10. Trending & External Content Events
### 11. Background Monitoring Events (EventService)

---

## 1. Printer Connection Events

### `printer_connected`

**Emitted by:** `PrinterConnectionService`, `EventService` (background monitoring)

**When:** A printer successfully connects and becomes available

**Payload Schema:**
```python
{
    "printer_id": str,        # Unique printer identifier
    "name": str,              # Printer display name
    "type": str,              # Printer type ("bambu_lab" or "prusa")
    "timestamp": str          # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

**Usage Example:**
```python
await self.event_service.emit_event("printer_connected", {
    "printer_id": "bambu_001",
    "name": "Bambu Lab A1",
    "type": "bambu_lab",
    "timestamp": "2025-11-08T10:30:00Z"
})
```

**Error Handling:** Connection failures do not emit this event; see `printer_connection_progress` for failure status

---

### `printer_disconnected`

**Emitted by:** `PrinterConnectionService`, `EventService` (background monitoring)

**When:** A printer disconnects or becomes unavailable

**Payload Schema:**
```python
{
    "printer_id": str,        # Unique printer identifier
    "name": str,              # Printer display name
    "timestamp": str          # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

**Usage Example:**
```python
await self.event_service.emit_event("printer_disconnected", {
    "printer_id": "bambu_001",
    "name": "Bambu Lab A1",
    "timestamp": "2025-11-08T11:45:00Z"
})
```

---

### `printer_connection_progress`

**Emitted by:** `PrinterConnectionService`

**When:** Connection state changes during connection attempt

**Payload Schema:**
```python
{
    "printer_id": str,        # Unique printer identifier
    "status": str,            # One of: "connecting", "connected", "failed", "monitoring", "error"
    "timestamp": str,         # ISO 8601 timestamp
    "message": str            # Optional status message (present for "failed", "error")
}
```

**Subscribers:** None (informational, used for real-time UI updates)

**Usage Example:**
```python
# Connection attempt started
await self.event_service.emit_event("printer_connection_progress", {
    "printer_id": "prusa_001",
    "status": "connecting",
    "timestamp": "2025-11-08T10:30:00Z"
})

# Connection failed
await self.event_service.emit_event("printer_connection_progress", {
    "printer_id": "prusa_001",
    "status": "failed",
    "timestamp": "2025-11-08T10:30:15Z",
    "message": "Connection timeout after 30s"
})
```

**Status Values:**
- `connecting`: Initial connection attempt
- `connected`: Successfully connected
- `failed`: Connection attempt failed (transient error)
- `monitoring`: Monitoring started successfully
- `error`: Unrecoverable error occurred

---

## 2. Printer Monitoring Events

### `printer_status_update`

**Emitted by:** `PrinterMonitoringService`

**When:** Printer status changes (after processing status update from printer)

**Payload Schema:**
```python
{
    "printer_id": str,            # Unique printer identifier
    "status": str,                # Printer status (e.g., "printing", "idle", "paused")
    "temperature": dict,          # Temperature data (nozzle, bed, chamber)
    "progress": int,              # Print progress percentage (0-100)
    "current_job": Optional[str], # Current job filename (if printing)
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational, used for real-time UI updates)

**Usage Example:**
```python
await self.event_service.emit_event("printer_status_update", {
    "printer_id": "bambu_001",
    "status": "printing",
    "temperature": {
        "nozzle": 220.0,
        "bed": 60.0,
        "chamber": 35.0
    },
    "progress": 45,
    "current_job": "model.3mf",
    "timestamp": "2025-11-08T10:35:00Z"
})
```

**Frequency:** Emitted after every status update processed (typically every few seconds during printing)

---

### `printer_monitoring_started`

**Emitted by:** `PrinterMonitoringService`

**When:** Monitoring begins for a specific printer

**Payload Schema:**
```python
{
    "printer_id": str,        # Unique printer identifier
    "timestamp": str          # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

---

### `printer_monitoring_stopped`

**Emitted by:** `PrinterMonitoringService`

**When:** Monitoring stops for a specific printer

**Payload Schema:**
```python
{
    "printer_id": str,        # Unique printer identifier
    "timestamp": str          # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

---

## 3. Printer Control Events

### `print_paused`

**Emitted by:** `PrinterControlService`

**When:** Print job successfully paused

**Payload Schema:**
```python
{
    "printer_id": str,        # Unique printer identifier
    "timestamp": str          # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

---

### `print_resumed`

**Emitted by:** `PrinterControlService`

**When:** Print job successfully resumed

**Payload Schema:**
```python
{
    "printer_id": str,        # Unique printer identifier
    "timestamp": str          # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

---

### `print_stopped`

**Emitted by:** `PrinterControlService`

**When:** Print job successfully stopped/cancelled

**Payload Schema:**
```python
{
    "printer_id": str,        # Unique printer identifier
    "timestamp": str          # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

---

## 4. File Discovery Events

### `files_discovered`

**Emitted by:** `FileDiscoveryService`, `EventService` (background monitoring)

**When:** File discovery completes on printer(s) or local folders

**Payload Schema:**
```python
{
    "printer_id": str,            # Printer identifier (or "all" for multi-printer scans)
    "files": List[dict],          # List of discovered/stored files
    "total_found": int,           # Total files found
    "new_files": int,             # Number of new files added to database
    "existing_files": int,        # Number of files already tracked
    "timestamp": str,             # ISO 8601 timestamp

    # Optional fields (EventService background discovery)
    "discovery_results": dict,    # Per-printer discovery results
    "new_files": List[dict]       # Detailed new file information
}
```

**Subscribers:** None (informational)

**Usage Example:**
```python
# From FileDiscoveryService
await self.event_service.emit_event("files_discovered", {
    "printer_id": "bambu_001",
    "files": [
        {"filename": "model1.3mf", "file_size": 1024000},
        {"filename": "model2.gcode", "file_size": 2048000}
    ],
    "total_found": 2,
    "new_files": 1,
    "existing_files": 1,
    "timestamp": "2025-11-08T10:40:00Z"
})

# From EventService background task
await self.event_service.emit_event("files_discovered", {
    "timestamp": "2025-11-08T10:40:00Z",
    "new_files": [
        {
            "printer_id": "bambu_001",
            "printer_name": "Bambu Lab A1",
            "filename": "model.3mf",
            "file_size": 1024000,
            "file_type": "3mf",
            "discovered_at": "2025-11-08T10:40:00Z"
        }
    ],
    "discovery_results": {
        "bambu_001": {
            "printer_name": "Bambu Lab A1",
            "files_found": 5,
            "success": True
        }
    },
    "total_new_files": 1
})
```

---

### `file_sync_complete`

**Emitted by:** `FileDiscoveryService`

**When:** File synchronization completes for a printer (including cleanup of removed files)

**Payload Schema:**
```python
{
    "printer_id": str,            # Unique printer identifier
    "files_added": int,           # Number of files added
    "files_removed": int,         # Number of files marked as removed
    "total_files": int,           # Total files currently tracked
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

---

### `new_files_found`

**Emitted by:** `EventService` (background monitoring)

**When:** New files are discovered during background scan (subset of `files_discovered`)

**Payload Schema:**
```python
{
    "timestamp": str,             # ISO 8601 timestamp
    "files": List[dict],          # List of new files with details
    "count": int                  # Number of new files
}
```

**Subscribers:** None (informational, triggers UI notifications)

---

## 5. File Download Events

### `file_download_started`

**Emitted by:** `FileDownloadService`

**When:** File download from printer begins

**Payload Schema:**
```python
{
    "printer_id": str,            # Unique printer identifier
    "filename": str,              # Name of file being downloaded
    "file_size": Optional[int],   # File size in bytes (if known)
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational, used for download progress UI)

---

### `file_download_complete`

**Emitted by:** `FileDownloadService`

**When:** File download successfully completes

**Payload Schema:**
```python
{
    "printer_id": str,            # Unique printer identifier
    "filename": str,              # Name of downloaded file
    "file_id": str,               # Database file ID
    "file_path": str,             # Local path to downloaded file
    "file_size": int,             # File size in bytes
    "download_time": float,       # Download duration in seconds
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

---

### `file_download_failed`

**Emitted by:** `FileDownloadService`

**When:** File download fails

**Payload Schema:**
```python
{
    "printer_id": str,            # Unique printer identifier
    "filename": str,              # Name of file that failed to download
    "error": str,                 # Error message
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational, triggers UI error notifications)

---

## 6. File Processing Events

### `file_needs_thumbnail_processing`

**Emitted by:** `FileDownloadService`

**When:** File download completes and file needs thumbnail extraction

**Payload Schema:**
```python
{
    "file_id": str,               # Database file ID
    "file_path": str              # Local path to downloaded file
}
```

**Subscribers:** `FileThumbnailService` (listens and processes thumbnails)

**Usage:** This is a **command event** that triggers thumbnail processing

---

### `file_thumbnails_processed`

**Emitted by:** `FileThumbnailService`

**When:** Thumbnail extraction completes successfully

**Payload Schema:**
```python
{
    "file_id": str,               # Database file ID
    "file_path": str,             # Local path to file
    "thumbnails": dict,           # Thumbnail paths by size
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

**Thumbnail Structure:**
```python
{
    "thumbnails": {
        "small": "/path/to/small.jpg",
        "medium": "/path/to/medium.jpg",
        "large": "/path/to/large.jpg"
    }
}
```

**Note:** Event `thumbnail_processing_failed` is mentioned in docstrings but not currently implemented.

---

### `file_metadata_extracted`

**Emitted by:** `FileMetadataService`

**When:** Metadata extraction completes successfully

**Payload Schema:**
```python
{
    "file_id": str,               # Database file ID
    "file_path": str,             # Local path to file
    "metadata": dict,             # Extracted metadata
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

**Metadata Structure:**
```python
{
    "metadata": {
        "print_time": 7200,       # Estimated print time in seconds
        "filament_used": 125.5,   # Filament used in grams
        "layer_height": 0.2,      # Layer height in mm
        "infill": 20,             # Infill percentage
        # ... additional metadata fields
    }
}
```

**Note:** Event `metadata_extraction_failed` is mentioned in docstrings but not currently implemented.

---

### `file_deleted`

**Emitted by:** `FileService`

**When:** File is successfully deleted from system

**Payload Schema:**
```python
{
    "file_id": str,               # Database file ID
    "filename": str,              # Name of deleted file
    "printer_id": Optional[str],  # Printer ID (if applicable)
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

---

### `thumbnail_cached`

**Emitted by:** `ThumbnailService`

**When:** External thumbnail is downloaded and cached

**Payload Schema:**
```python
{
    "url": str,                   # Original thumbnail URL
    "cache_path": str,            # Local cache path
    "source_type": str            # Source type (e.g., "makerworld", "printables")
}
```

**Subscribers:** None (informational)

---

### `file_watcher`

**Emitted by:** `FileWatcherService`

**When:** File system changes detected in watched folders

**Payload Schema:**
```python
{
    "event_type": str,            # "created", "modified", "deleted", "moved"
    "path": str,                  # File path
    "is_directory": bool,         # Whether path is directory
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational, triggers re-scan)

---

## 7. Job Lifecycle Events

### `job_created`

**Emitted by:** `JobService`, `EventService` (background monitoring as `job_started`)

**When:** New print job is created in database

**Payload Schema:**
```python
{
    "job_id": str,                # Unique job identifier
    "printer_id": str,            # Printer identifier
    "job_name": str,              # Job/file name
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

---

### `job_started`

**Emitted by:** `EventService` (background monitoring)

**When:** Job transitions to "running" status

**Payload Schema:**
```python
{
    "job_id": str,                # Unique job identifier
    "printer_id": str,            # Printer identifier
    "job_name": str,              # Job/file name
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

---

### `job_status_changed`

**Emitted by:** `JobService`

**When:** Job status is explicitly updated via API

**Payload Schema:**
```python
{
    "job_id": str,                # Unique job identifier
    "status": str,                # New status value
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

---

### `job_progress_updated`

**Emitted by:** `JobService`

**When:** Job progress is updated

**Payload Schema:**
```python
{
    "job_id": str,                # Unique job identifier
    "progress": int,              # Progress percentage (0-100)
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

---

### `job_completed`

**Emitted by:** `EventService` (background monitoring)

**When:** Job transitions to terminal status ("completed", "failed", "cancelled")

**Payload Schema:**
```python
{
    "job_id": str,                # Unique job identifier
    "printer_id": str,            # Printer identifier
    "job_name": str,              # Job/file name
    "status": str,                # Final status ("completed", "failed", "cancelled")
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

---

### `job_deleted`

**Emitted by:** `JobService`

**When:** Job is deleted from database

**Payload Schema:**
```python
{
    "job_id": str,                # Unique job identifier
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

---

## 8. Library Management Events

### `library_file_added`

**Emitted by:** `LibraryService`

**When:** File is added to user's library

**Payload Schema:**
```python
{
    "checksum": str,              # File checksum (unique identifier)
    "filename": str,              # Original filename
    "file_size": int,             # File size in bytes
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

---

### `library_file_deleted`

**Emitted by:** `LibraryService`

**When:** File is removed from user's library

**Payload Schema:**
```python
{
    "checksum": str,              # File checksum
    "filename": str,              # Original filename
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

---

## 9. Material Management Events

### `material_created`

**Emitted by:** `MaterialService`

**When:** New material/filament spool is added

**Payload Schema:**
```python
{
    "material": dict              # Complete material object (Material.__dict__)
}
```

**Subscribers:** None (informational)

---

### `material_updated`

**Emitted by:** `MaterialService`

**When:** Material/spool information is updated

**Payload Schema:**
```python
{
    "material": dict              # Updated material object (Material.__dict__)
}
```

**Subscribers:** None (informational)

---

### `material_deleted`

**Emitted by:** `MaterialService`

**When:** Material/spool is deleted

**Payload Schema:**
```python
{
    "material_id": str            # Unique material identifier
}
```

**Subscribers:** None (informational)

---

### `material_low_stock`

**Emitted by:** `MaterialService`

**When:** Material remaining drops below 20%

**Payload Schema:**
```python
{
    "material_id": str,           # Unique material identifier
    "remaining_percentage": float, # Remaining material percentage
    "material_name": str,         # Material display name
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational, triggers notifications)

---

## 10. Trending & External Content Events

### `trending_updated`

**Emitted by:** `TrendingService`

**When:** Trending models are refreshed from external platforms

**Payload Schema:**
```python
{
    "platforms": List[str],       # Platforms updated (e.g., ["makerworld", "printables"])
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

---

### `idea_created_from_trending`

**Emitted by:** `TrendingService`

**When:** User creates an idea from a trending model

**Payload Schema:**
```python
{
    "idea_id": str,               # Created idea ID
    "trending_id": str,           # Source trending model ID
    "platform": str,              # Source platform
    "timestamp": str              # ISO 8601 timestamp
}
```

**Subscribers:** None (informational)

---

## 11. Background Monitoring Events (EventService)

These events are emitted by EventService's internal background monitoring tasks.

### `printer_status`

**Emitted by:** `EventService` (background monitoring task)

**When:** Background printer status check completes (every 30 seconds)

**Payload Schema:**
```python
{
    "timestamp": str,             # ISO 8601 timestamp
    "printers": List[dict],       # Status of all printers
    "status_changes": List[dict]  # Printers with status changes
}
```

**Printers Array Structure:**
```python
{
    "printer_id": str,
    "name": str,
    "type": str,
    "status": str,                # "online", "offline", "unknown"
    "temperature": dict,
    "progress": int,
    "current_job": Optional[str],
    "last_seen": str
}
```

**Status Changes Array Structure:**
```python
{
    "printer_id": str,
    "old_status": str,
    "new_status": str,
    "timestamp": str
}
```

**Subscribers:** None (informational)

---

### `job_update`

**Emitted by:** `EventService` (background monitoring task)

**When:** Background job status check completes (every 10 seconds)

**Payload Schema:**
```python
{
    "timestamp": str,             # ISO 8601 timestamp
    "active_jobs": int,           # Number of active jobs
    "job_updates": List[dict]     # Jobs with status/progress changes
}
```

**Job Updates Array Structure:**
```python
{
    "job_id": str,
    "printer_id": str,
    "job_name": str,
    "old_status": Optional[str],  # Present if status changed
    "new_status": Optional[str],  # Present if status changed
    "status": str,                # Current status
    "old_progress": Optional[int],# Present if progress changed significantly
    "new_progress": Optional[int],# Present if progress changed significantly
    "progress": int,              # Current progress
    "timestamp": str
}
```

**Subscribers:** None (informational)

---

## Error Handling in Event System

### Event Handler Exceptions

Exceptions in event handlers are caught and logged by EventService but do not propagate to the emitter:

```python
# In EventService.emit_event()
for handler in handlers:
    try:
        if asyncio.iscoroutinefunction(handler):
            await handler(data)
        else:
            handler(data)
    except Exception as e:
        logger.error("Error in event handler",
                   event_type=event_type, error=str(e))
```

**Best Practices:**
- Handlers should implement their own error handling
- Log errors with context for debugging
- Don't let exceptions propagate to event system

### Missing Events (Not Currently Implemented)

The following events are mentioned in service docstrings but **not currently emitted**:

1. **`thumbnail_processing_failed`** (FileThumbnailService)
   - Should be emitted when thumbnail extraction fails
   - Recommended payload: `{"file_id": str, "error": str, "timestamp": str}`

2. **`metadata_extraction_failed`** (FileMetadataService)
   - Should be emitted when metadata extraction fails
   - Recommended payload: `{"file_id": str, "error": str, "timestamp": str}`

3. **`auto_download_triggered`** (PrinterMonitoringService)
   - Mentioned in prompt but not implemented
   - Could be emitted when auto-download starts for current job

4. **`auto_download_failed`** (PrinterMonitoringService)
   - Mentioned in prompt but not implemented
   - Currently only logs warnings, could emit event for UI notification

**Recommendation:** Implement these events for consistency and better error visibility.

---

## Event Timing and Ordering

### Guarantees

1. **Order Preservation**: Events emitted by same service are processed in order
2. **Async Execution**: Handlers run concurrently, no guaranteed inter-handler ordering
3. **Fire-and-Forget**: Emitters don't wait for handler completion

### No Guarantees

1. **Cross-Service Ordering**: Events from different services may arrive in any order
2. **Handler Completion**: Emitter doesn't wait for handlers to finish
3. **Delivery**: If no subscribers, event is silently discarded

### Timing Examples

**File Download Workflow:**
```
t=0s:   file_download_started
t=5s:   file_download_complete
t=5.1s: file_needs_thumbnail_processing  # Triggered by download complete
t=7s:   file_thumbnails_processed        # Async processing completes
```

**Job Monitoring Workflow:**
```
t=0s:   job_status_changed → "running"
t=1s:   job_started                      # Background monitoring detects
t=10s:  job_progress_updated → 10%
t=20s:  job_progress_updated → 20%
...
t=100s: job_status_changed → "completed"
t=101s: job_completed                    # Background monitoring detects
```

---

## Subscription Patterns

### Subscribe to Events

```python
def __init__(self, event_service: EventService):
    self.event_service = event_service

    # Subscribe to events
    self.event_service.subscribe("file_needs_thumbnail_processing",
                                 self._handle_thumbnail_request)

async def _handle_thumbnail_request(self, data: Dict[str, Any]):
    """Handle thumbnail processing request."""
    file_id = data["file_id"]
    file_path = data["file_path"]
    await self._process_thumbnails(file_id, file_path)
```

### Emit Events

```python
async def download_file(self, printer_id: str, filename: str):
    # Emit start event
    await self.event_service.emit_event("file_download_started", {
        "printer_id": printer_id,
        "filename": filename,
        "timestamp": datetime.now().isoformat()
    })

    try:
        # ... perform download ...

        # Emit success event
        await self.event_service.emit_event("file_download_complete", {
            "printer_id": printer_id,
            "filename": filename,
            "file_id": file_id,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        # Emit failure event
        await self.event_service.emit_event("file_download_failed", {
            "printer_id": printer_id,
            "filename": filename,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
```

---

## Best Practices

### For Event Emitters

1. **Use structured payloads** with consistent field names
2. **Include timestamps** for all events
3. **Add context** (IDs, names) for debugging
4. **Emit events after** state changes complete
5. **Don't rely on subscribers** - events are fire-and-forget

### For Event Subscribers

1. **Handle errors internally** - don't let exceptions propagate
2. **Log with context** for debugging
3. **Keep handlers fast** - offload heavy work to background tasks
4. **Check payload schema** - validate required fields exist
5. **Be idempotent** - handlers may be called multiple times

### For Event Naming

1. **Use past tense** for completed actions (`file_downloaded`, not `download_file`)
2. **Use present tense** for state updates (`printer_status_update`)
3. **Be specific** (`file_download_complete` vs `file_complete`)
4. **Group related events** with prefixes (`job_created`, `job_deleted`, `job_updated`)

---

## Debugging Events

### View Event Counts

```python
# Get event service status
status = event_service.get_status()
print(status["event_counts"])

# Output:
# {
#     'printer_status': 120,
#     'job_update': 240,
#     'files_discovered': 8,
#     'printer_connected': 2,
#     'printer_disconnected': 1,
#     'job_started': 5,
#     'job_completed': 4,
#     'new_files_found': 3
# }
```

### Enable Event Logging

Set log level to DEBUG to see all event emissions:

```python
import structlog
logger = structlog.get_logger()
logger.setLevel("DEBUG")

# Will log:
# event="emit_event" event_type="file_download_started" printer_id="bambu_001"
```

---

## Migration Guide

### Adding New Events

1. **Define event contract** in this document
2. **Add event emission** in service code
3. **Add subscribers** (if needed)
4. **Update tests** to verify event emission
5. **Update EVENT_FLOWS.md** with event flow

### Deprecating Events

1. **Mark as deprecated** in this document
2. **Add deprecation warning** in emitter code
3. **Wait 2+ versions** before removing
4. **Remove event** and update documentation

---

## See Also

- [EVENT_FLOWS.md](EVENT_FLOWS.md) - Visual event flow diagrams
- [CIRCULAR_DEPENDENCY_AUDIT.md](CIRCULAR_DEPENDENCY_AUDIT.md) - Service dependency audit
- [Architecture Documentation](.claude/skills/printernizer-architecture.md) - Overall architecture
- [EventService Implementation](../src/services/event_service.py) - Event system source code
