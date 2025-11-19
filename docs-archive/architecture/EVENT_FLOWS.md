# Event Flow Diagrams

**Version:** 1.0
**Date:** November 8, 2025
**Phase:** Phase 2 - Circular Dependency Resolution

---

## Overview

This document provides visual representations of event flows through the Printernizer system. Each workflow shows how events are emitted, propagated through EventService, and handled by subscriber services.

**Legend:**
```
[Service] ───> Direct method call
[Service] ═══> Event emission
[Service] ···> Event subscription/handling
{Event}       Event name
```

---

## Table of Contents

1. [File Download Workflow](#1-file-download-workflow)
2. [Printer Connection Workflow](#2-printer-connection-workflow)
3. [Job Monitoring Workflow](#3-job-monitoring-workflow)
4. [File Metadata Extraction Workflow](#4-file-metadata-extraction-workflow)
5. [Background Monitoring Workflow](#5-background-monitoring-workflow)
6. [Auto-Download Workflow](#6-auto-download-workflow)
7. [Material Low Stock Workflow](#7-material-low-stock-workflow)
8. [Library File Management Workflow](#8-library-file-management-workflow)

---

## 1. File Download Workflow

### Standard User-Initiated Download

```
┌─────────────────┐
│   API Request   │
│  (User/Frontend)│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                        FileService                          │
│  (Coordinator - delegates to FileDownloadService)           │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FileDownloadService                        │
└────────┬────────────────────────────────────────────────────┘
         │
         │ (1) Emit: file_download_started
         ├═══════════════════════════════════════════════════╗
         │                                                    ║
         ▼                                                    ║
┌────────────────────┐                                        ║
│ PrinterInstance    │ ← get_printer_instance()              ║
│ (BambuLab/Prusa)   │                                        ║
└────────┬───────────┘                                        ║
         │                                                    ║
         │ download_file()                                   ║
         ▼                                                    ▼
┌────────────────────┐                          ┌─────────────────────┐
│   Printer MQTT/    │                          │    EventService     │
│   HTTP API         │                          └──────────┬──────────┘
└────────┬───────────┘                                     │
         │                                                  │
         │ (file data)                                     │
         ▼                                                  │
┌─────────────────────────────────────────────────────────────┐
│                   FileDownloadService                        │
│  - Save file to disk                                        │
│  - Store in database                                        │
│  - Calculate checksum                                       │
└────────┬────────────────────────────────────────────────────┘
         │
         │ (2) Emit: file_needs_thumbnail_processing
         ├═══════════════════════════════════════════════════╗
         │                                                    ║
         │ (3) Emit: file_download_complete                  ║
         ├═══════════════════════════════════════════════════╣
         │                                                    ║
         ▼                                                    ║
┌────────────────────┐                                        ║
│  Return result to  │                                        ║
│     FileService    │                                        ║
└────────────────────┘                                        ▼
                                                 ┌─────────────────────┐
                                                 │    EventService     │
                                                 │  - Notify subscribers│
                                                 └──────────┬──────────┘
                                                            │
                                    ┌───────────────────────┴────────────────────┐
                                    │                                            │
                                    ▼                                            ▼
                      ┌──────────────────────────┐              ┌────────────────────────┐
                      │ FileThumbnailService     │              │     UI / Frontend      │
                      │ (subscribed to:          │              │ (subscribed to:        │
                      │  file_needs_thumbnail_   │              │  file_download_        │
                      │  processing)             │              │  complete)             │
                      └──────────┬───────────────┘              └────────────────────────┘
                                 │
                                 │ Extract thumbnails
                                 ▼
                      ┌──────────────────────────┐
                      │ Process file thumbnails  │
                      │ - Extract embedded images│
                      │ - Generate sizes         │
                      │ - Store in database      │
                      └──────────┬───────────────┘
                                 │
                                 │ (4) Emit: file_thumbnails_processed
                                 ├═══════════════════════════════╗
                                 │                                ║
                                 ▼                                ▼
                      ┌──────────────────────────┐  ┌─────────────────────┐
                      │  Thumbnail processing    │  │    EventService     │
                      │      complete            │  │  (notify UI)        │
                      └──────────────────────────┘  └─────────────────────┘
```

**Event Sequence:**
1. `file_download_started` - Download begins
2. `file_needs_thumbnail_processing` - Command event to trigger thumbnail extraction
3. `file_download_complete` - Download successful
4. `file_thumbnails_processed` - Thumbnail extraction complete

**Timing:**
- Total download: 2-30 seconds (depends on file size)
- Thumbnail processing: 1-5 seconds (async, doesn't block download)

---

## 2. Printer Connection Workflow

### Initial Printer Connection

```
┌─────────────────┐
│   API Request   │
│ POST /printers  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                      PrinterService                         │
│  (Coordinator - delegates to PrinterConnectionService)      │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                 PrinterConnectionService                     │
└────────┬────────────────────────────────────────────────────┘
         │
         │ (1) Emit: printer_connection_progress (status: "connecting")
         ├═══════════════════════════════════════════════════╗
         │                                                    ║
         ▼                                                    ║
┌────────────────────┐                                        ▼
│ Create printer     │                          ┌─────────────────────┐
│ instance (Bambu/   │                          │    EventService     │
│ Prusa)             │                          └──────────┬──────────┘
└────────┬───────────┘                                     │
         │                                                  │
         │ connect()                                       │
         ▼                                                  │
┌────────────────────┐                                     │
│   Printer connects │                                     │
│   (MQTT/HTTP)      │                                     │
└────────┬───────────┘                                     │
         │                                                  │
         │ Connection successful                           │
         ▼                                                  │
┌─────────────────────────────────────────────────────────────┐
│                 PrinterConnectionService                     │
│  - Store in database                                        │
│  - Add to active printers                                   │
└────────┬────────────────────────────────────────────────────┘
         │
         │ (2) Emit: printer_connection_progress (status: "connected")
         ├═══════════════════════════════════════════════════╣
         │                                                    ║
         │ (3) Emit: printer_connected                       ║
         ├═══════════════════════════════════════════════════╣
         │                                                    ║
         ▼                                                    ▼
┌────────────────────┐                          ┌─────────────────────┐
│ Start monitoring   │◄─────────────────────────│    EventService     │
│ (via Printer       │                          └──────────┬──────────┘
│ MonitoringService) │                                     │
└────────┬───────────┘                                     │
         │                                                  ▼
         │ (4) Emit: printer_monitoring_started  ┌────────────────────┐
         ├═══════════════════════════════════════│  UI / Frontend     │
         │                                        │ (Real-time status  │
         ▼                                        │  updates)          │
┌────────────────────┐                          └────────────────────┘
│ Monitoring active  │
│ (status updates    │
│  every few seconds)│
└────────────────────┘
```

**Event Sequence:**
1. `printer_connection_progress` (connecting) - Connection attempt starts
2. `printer_connection_progress` (connected) - Connection successful
3. `printer_connected` - Printer now online
4. `printer_monitoring_started` - Status monitoring active

**Failure Path:**
```
PrinterConnectionService
         │
         │ Connection fails
         ├═══════════════════════════════════════════════════╗
         │                                                    ║
         │ (1) Emit: printer_connection_progress (status: "failed")
         │                                                    ║
         ▼                                                    ▼
   Return error                                 ┌─────────────────────┐
   to API                                       │    EventService     │
                                                └──────────┬──────────┘
                                                           │
                                                           ▼
                                                ┌────────────────────┐
                                                │  UI / Frontend     │
                                                │ (Show error msg)   │
                                                └────────────────────┘
```

---

## 3. Job Monitoring Workflow

### Background Job Status Tracking

```
┌──────────────────────────────────────────────────────────────┐
│                        EventService                          │
│              (Background monitoring task)                     │
│              Runs every 10 seconds                            │
└────────┬─────────────────────────────────────────────────────┘
         │
         │ get_active_jobs()
         ▼
┌─────────────────────────────────────────────────────────────┐
│                        JobService                            │
│  - Query database for active jobs                           │
│  - Return jobs with status: running, paused, etc.           │
└────────┬────────────────────────────────────────────────────┘
         │
         │ [List of active jobs]
         ▼
┌─────────────────────────────────────────────────────────────┐
│                        EventService                          │
│  - Compare with last known state                            │
│  - Detect status changes                                    │
│  - Detect progress changes (>10% difference)                │
└────────┬────────────────────────────────────────────────────┘
         │
         │ Status changed: "pending" → "running"
         ├═══════════════════════════════════════════════════╗
         │                                                    ║
         │ (1) Emit: job_started                             ║
         │                                                    ║
         │ Status changed: "running" → "completed"           ║
         ├═══════════════════════════════════════════════════╣
         │                                                    ║
         │ (2) Emit: job_completed                           ║
         │                                                    ║
         │ General update with all active jobs               ║
         ├═══════════════════════════════════════════════════╣
         │                                                    ║
         │ (3) Emit: job_update                              ║
         │                                                    ║
         ▼                                                    ▼
┌────────────────────┐                          ┌─────────────────────┐
│ Wait 10 seconds    │                          │    EventService     │
│ Repeat cycle       │                          └──────────┬──────────┘
└────────────────────┘                                     │
                                                           ▼
                                                ┌────────────────────┐
                                                │  UI / Frontend     │
                                                │ - Job progress bars│
                                                │ - Status indicators│
                                                │ - Notifications    │
                                                └────────────────────┘
```

**Event Sequence:**
1. `job_started` - Job begins printing (status → "running")
2. `job_update` - Periodic status/progress updates
3. `job_completed` - Job finished (status → completed/failed/cancelled)

**Event Frequency:**
- `job_update`: Every 10 seconds (if any active jobs)
- `job_started`: Once per job lifecycle
- `job_completed`: Once per job lifecycle

---

## 4. File Metadata Extraction Workflow

### Metadata Extraction After Download

```
┌─────────────────────────────────────────────────────────────┐
│                        FileService                          │
│  sync_printer_files() or download_file()                    │
└────────┬────────────────────────────────────────────────────┘
         │
         │ Calls FileMetadataService.extract_metadata()
         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FileMetadataService                        │
│  - Read file from disk                                      │
│  - Parse GCODE/3MF/BGCode                                   │
│  - Extract metadata (print time, filament, settings)        │
└────────┬────────────────────────────────────────────────────┘
         │
         │ Success path
         ├─────────────────────────────────────────────╗
         │                                              ║
         │ Update database with metadata               ║
         │                                              ║
         │ (1) Emit: file_metadata_extracted           ║
         │                                              ║
         ▼                                              ▼
┌────────────────────┐                  ┌─────────────────────┐
│ Return metadata    │                  │    EventService     │
│ to FileService     │                  └──────────┬──────────┘
└────────────────────┘                             │
                                                   ▼
                                        ┌────────────────────┐
                                        │  UI / Frontend     │
                                        │ (Display metadata) │
                                        └────────────────────┘

Failure path (Currently logs only, no event):
┌─────────────────────────────────────────────────────────────┐
│                   FileMetadataService                        │
│  - Parsing fails                                            │
│  - Log error                                                │
│  - Return None                                              │
└────────┬────────────────────────────────────────────────────┘
         │
         │ ⚠️  Should emit: metadata_extraction_failed
         │     (Currently not implemented)
         ▼
   Log error only
```

**Event Sequence:**
1. `file_metadata_extracted` - Metadata successfully parsed and stored

**Missing Events:**
- `metadata_extraction_failed` - Should be emitted on parsing errors

---

## 5. Background Monitoring Workflow

### EventService Background Tasks

```
┌──────────────────────────────────────────────────────────────┐
│                    EventService.start()                      │
│  Creates 3 background monitoring tasks                        │
└────────┬─────────────────────────────────────────────────────┘
         │
         ├──────────────────┬──────────────────┬────────────────┐
         │                  │                  │                │
         ▼                  ▼                  ▼                │
    ┌────────┐      ┌──────────┐      ┌────────────┐          │
    │Printer │      │   Job    │      │    File    │          │
    │Monitor │      │ Monitor  │      │ Discovery  │          │
    │(30s)   │      │  (10s)   │      │   (300s)   │          │
    └────┬───┘      └────┬─────┘      └─────┬──────┘          │
         │               │                   │                 │
         │               │                   │                 │
         ▼               ▼                   ▼                 │
    ┌────────┐      ┌──────────┐      ┌────────────┐          │
    │Get all │      │Get active│      │Scan all    │          │
    │printer │      │jobs from │      │printers for│          │
    │statuses│      │database  │      │new files   │          │
    └────┬───┘      └────┬─────┘      └─────┬──────┘          │
         │               │                   │                 │
         │ Emit:         │ Emit:             │ Emit:           │
         │ - printer_status                  │ - files_discovered
         │ - printer_connected               │ - new_files_found
         │ - printer_disconnected            │                 │
         │               │ - job_started     │                 │
         │               │ - job_completed   │                 │
         │               │ - job_update      │                 │
         ▼               ▼                   ▼                 │
    ┌──────────────────────────────────────────────┐          │
    │              EventService                    │          │
    │          Emit events to subscribers          │          │
    └──────────────────┬───────────────────────────┘          │
                       │                                       │
                       ▼                                       │
            ┌────────────────────┐                            │
            │  UI / Frontend     │                            │
            │  Real-time updates │                            │
            └────────────────────┘                            │
                                                               │
         Loop back ────────────────────────────────────────────┘
         (runs continuously until shutdown)
```

**Background Task Details:**

1. **Printer Monitoring Task** (30-second interval)
   - Polls all configured printers
   - Detects online/offline status changes
   - Emits: `printer_status`, `printer_connected`, `printer_disconnected`

2. **Job Monitoring Task** (10-second interval)
   - Queries active jobs from database
   - Detects status/progress changes
   - Emits: `job_started`, `job_completed`, `job_update`

3. **File Discovery Task** (5-minute interval)
   - Scans all printers for new files
   - Discovers local files (if file watcher enabled)
   - Emits: `files_discovered`, `new_files_found`

---

## 6. Auto-Download Workflow

### Automatic Download of Current Print Job

```
┌──────────────────────────────────────────────────────────────┐
│                  PrinterMonitoringService                    │
│  handle_status_update() - Called when printer status changes │
└────────┬─────────────────────────────────────────────────────┘
         │
         │ (1) Store status in database
         │ (2) Emit: printer_status_update
         │ (3) Check auto-download conditions
         ▼
┌─────────────────────────────────────────────────────────────┐
│  _check_auto_download()                                     │
│  Conditions:                                                │
│  - Printer status: "printing"                               │
│  - Has current_job filename                                 │
│  - Is printable file (.gcode, .bgcode, .3mf)                │
│  - Not already attempted for this file                      │
└────────┬────────────────────────────────────────────────────┘
         │
         │ All conditions met
         ├═══════════════════════════════════════════════════╗
         │                                                    ║
         │ Create background task:                           ║
         │ _attempt_download_current_job()                   ║
         │                                                    ║
         │ ⚠️  Could emit: auto_download_triggered           ║
         │     (Currently not implemented)                   ║
         │                                                    ║
         ▼                                                    ▼
┌─────────────────────────────────────────────────────────────┐
│  _attempt_download_current_job()                            │
│  - Try exact filename                                       │
│  - Try filename variants (case, special chars)              │
│  - Try all variants until success                           │
└────────┬────────────────────────────────────────────────────┘
         │
         │ Call FileService.download_file()
         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FileDownloadService                        │
│  (See: File Download Workflow above)                        │
└────────┬────────────────────────────────────────────────────┘
         │
         ├────────────────────────┬────────────────────────────┐
         │                        │                            │
         ▼ Success                ▼ All variants fail          │
┌────────────────────┐   ┌────────────────────┐              │
│ Log: "Auto-download│   │ Log warning:       │              │
│      completed"    │   │ "Auto-download     │              │
└────────────────────┘   │  failed"           │              │
                         └────────┬───────────┘              │
                                  │                           │
                                  │ ⚠️  Could emit:           │
                                  │ auto_download_failed      │
                                  │ (Currently not            │
                                  │  implemented)             │
                                  ▼                           │
                         (Logs only, no event)                │
                                                               │
         Return to monitoring ─────────────────────────────────┘
         (Status updates continue)
```

**Current Implementation:**
- Auto-download happens silently in background
- Success: Logged only
- Failure: Logged as warning

**Missing Events:**
- `auto_download_triggered` - When auto-download starts
- `auto_download_failed` - When all download attempts fail

**Recommended Addition:**
```python
# In PrinterMonitoringService._check_auto_download()
await self.event_service.emit_event("auto_download_triggered", {
    "printer_id": printer_id,
    "filename": filename,
    "timestamp": datetime.now().isoformat()
})

# In PrinterMonitoringService._attempt_download_current_job()
# After all attempts fail:
await self.event_service.emit_event("auto_download_failed", {
    "printer_id": printer_id,
    "filename": filename,
    "error": last_error_message,
    "attempts": len(attempts),
    "timestamp": datetime.now().isoformat()
})
```

---

## 7. Material Low Stock Workflow

### Filament Usage Tracking

```
┌─────────────────┐
│   API Request   │
│ PATCH /materials│
│  (update usage) │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                      MaterialService                         │
│  update_material()                                          │
└────────┬────────────────────────────────────────────────────┘
         │
         │ Calculate remaining_percentage
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Check: remaining_percentage < 20%                          │
└────────┬────────────────────────────────────────────────────┘
         │
         │ Low stock detected
         ├═══════════════════════════════════════════════════╗
         │                                                    ║
         │ (1) Emit: material_low_stock                      ║
         │                                                    ║
         ▼                                                    ▼
┌────────────────────┐                          ┌─────────────────────┐
│ Update database    │                          │    EventService     │
│ Return to API      │                          └──────────┬──────────┘
└────────────────────┘                                     │
                                                           ▼
                                                ┌────────────────────┐
                                                │  UI / Frontend     │
                                                │ - Show notification│
                                                │ - Badge on material│
                                                │ - Reminder to order│
                                                └────────────────────┘
```

**Event Sequence:**
1. `material_updated` - Every material update
2. `material_low_stock` - Only when < 20% remaining

**Threshold:**
- Emitted when remaining drops below 20%
- Not emitted again until material is refilled and drops below 20% again

---

## 8. Library File Management Workflow

### Adding File to Personal Library

```
┌─────────────────┐
│   API Request   │
│ POST /library   │
│  (with file)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                      LibraryService                          │
│  add_file()                                                 │
│  - Calculate checksum                                       │
│  - Check for duplicates                                     │
│  - Store file in library directory                          │
│  - Create database record                                   │
└────────┬────────────────────────────────────────────────────┘
         │
         │ (1) Emit: library_file_added
         ├═══════════════════════════════════════════════════╗
         │                                                    ║
         ▼                                                    ▼
┌────────────────────┐                          ┌─────────────────────┐
│ Return file info   │                          │    EventService     │
│ to API             │                          └──────────┬──────────┘
└────────────────────┘                                     │
                                                           ▼
                                                ┌────────────────────┐
                                                │  UI / Frontend     │
                                                │ - Update library   │
                                                │   view             │
                                                │ - Show success msg │
                                                └────────────────────┘
```

**Deletion Flow:**
```
┌─────────────────┐
│   API Request   │
│ DELETE /library │
│  /{checksum}    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                      LibraryService                          │
│  delete_file()                                              │
│  - Remove file from disk                                    │
│  - Delete database record                                   │
└────────┬────────────────────────────────────────────────────┘
         │
         │ (1) Emit: library_file_deleted
         ├═══════════════════════════════════════════════════╗
         │                                                    ║
         ▼                                                    ▼
┌────────────────────┐                          ┌─────────────────────┐
│ Return success     │                          │    EventService     │
│ to API             │                          └──────────┬──────────┘
└────────────────────┘                                     │
                                                           ▼
                                                ┌────────────────────┐
                                                │  UI / Frontend     │
                                                │ - Remove from view │
                                                │ - Show confirmation│
                                                └────────────────────┘
```

---

## Complex Multi-Service Flow Example

### Complete Print Job Lifecycle

```
Printer starts printing → Auto-download → Thumbnail processing → Job completion

┌──────────────────────────────────────────────────────────────┐
│                  Bambu Lab Printer (MQTT)                    │
│  Status: "printing", current_job: "awesome_model.3mf"        │
└────────┬─────────────────────────────────────────────────────┘
         │
         │ MQTT status message
         ▼
┌─────────────────────────────────────────────────────────────┐
│              BambuLabPrinter (instance)                     │
│  handle_message() → parse status                            │
└────────┬────────────────────────────────────────────────────┘
         │
         │ Callback to PrinterMonitoringService
         ▼
┌─────────────────────────────────────────────────────────────┐
│              PrinterMonitoringService                        │
│  handle_status_update()                                     │
└────────┬────────────────────────────────────────────────────┘
         │
         ├═══════════════════════════════════════════════════╗
         │ (1) Emit: printer_status_update                   ║
         │                                                    ║
         │ _check_auto_download()                            ▼
         │ → Conditions met                      ┌─────────────────────┐
         │                                        │    EventService     │
         ▼                                        └──────────┬──────────┘
┌─────────────────────────────────────────────────────────────┐
│  Background task: _attempt_download_current_job()           │
│  → FileService.download_file("awesome_model.3mf")           │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│              FileDownloadService                             │
│  download_file()                                            │
└────────┬────────────────────────────────────────────────────┘
         │
         ├═══════════════════════════════════════════════════╗
         │ (2) Emit: file_download_started                   ║
         │                                                    ║
         │ Download file from printer                        ▼
         │ Store in database                     ┌─────────────────────┐
         │                                        │    EventService     │
         ├═══════════════════════════════════════╣                     │
         │ (3) Emit: file_needs_thumbnail_processing                  │
         │                                        └──────────┬──────────┘
         ├═══════════════════════════════════════╣          │
         │ (4) Emit: file_download_complete      ║          │
         │                                        ▼          │
         ▼                                                   │
┌────────────────────┐                                      │
│ Download complete  │                                      │
└────────────────────┘                 ┌───────────────────┴────────────┐
                                       │                                 │
                                       ▼                                 ▼
                         ┌──────────────────────────┐      ┌─────────────────┐
                         │ FileThumbnailService     │      │  UI / Frontend  │
                         │ (subscribed)             │      │  (Show download)│
                         └──────────┬───────────────┘      └─────────────────┘
                                    │
                                    │ Extract thumbnails
                                    ▼
                         ┌──────────────────────────┐
                         │ Process 3MF embedded     │
                         │ images                   │
                         └──────────┬───────────────┘
                                    │
                                    ├═══════════════════════════╗
                                    │ (5) Emit: file_thumbnails_processed
                                    │                            ║
                                    ▼                            ▼
                         ┌──────────────────────────┐ ┌─────────────────────┐
                         │ Thumbnails ready         │ │    EventService     │
                         └──────────────────────────┘ └──────────┬──────────┘
                                                                  │
                                                                  ▼
                                                       ┌─────────────────┐
                                                       │  UI / Frontend  │
                                                       │ (Display thumbs)│
                                                       └─────────────────┘

[Meanwhile, printing continues...]

┌──────────────────────────────────────────────────────────────┐
│                  Bambu Lab Printer (MQTT)                    │
│  Status: "idle", current_job: null (print completed)         │
└────────┬─────────────────────────────────────────────────────┘
         │
         │ MQTT status message
         ▼
┌─────────────────────────────────────────────────────────────┐
│              PrinterMonitoringService                        │
│  handle_status_update()                                     │
│  Status changed: "printing" → "idle"                        │
└────────┬────────────────────────────────────────────────────┘
         │
         ├═══════════════════════════════════════════════════╗
         │ (6) Emit: printer_status_update (status: "idle")  ║
         │                                                    ║
         ▼                                                    ▼
                                              ┌─────────────────────┐
                                              │    EventService     │
                                              └──────────┬──────────┘
                                                         │
                                                         ▼
                                              ┌─────────────────┐
                                              │  UI / Frontend  │
                                              │ (Print complete │
                                              │  notification)  │
                                              └─────────────────┘
```

**Complete Event Sequence:**
1. `printer_status_update` (status: printing)
2. `file_download_started`
3. `file_needs_thumbnail_processing`
4. `file_download_complete`
5. `file_thumbnails_processed`
6. `printer_status_update` (status: idle)

**Total Time:**
- Print start to auto-download: < 5 seconds
- Download: 5-30 seconds
- Thumbnail processing: 1-5 seconds
- **Total overhead: ~10-40 seconds** (transparent to user during print)

---

## Event Timing Reference

| Event Type | Frequency | Latency | Notes |
|------------|-----------|---------|-------|
| `printer_status_update` | 1-5s during print | < 100ms | Real-time MQTT/polling |
| `printer_status` (background) | 30s | N/A | Background monitoring |
| `job_update` (background) | 10s | N/A | Background monitoring |
| `files_discovered` (background) | 300s (5min) | N/A | Background monitoring |
| `file_download_started` | On-demand | < 100ms | Emitted immediately |
| `file_download_complete` | On-demand | 5-30s | File transfer time |
| `file_thumbnails_processed` | On-demand | 1-5s | After download |
| `file_metadata_extracted` | On-demand | < 1s | Quick parsing |
| `job_started` | On job start | < 10s | Detected by background |
| `job_completed` | On job end | < 10s | Detected by background |
| `material_low_stock` | On update | < 100ms | When threshold crossed |

---

## Debugging Event Flows

### Enable Event Tracing

Add logging to track event flows:

```python
import structlog
logger = structlog.get_logger()

# Enable DEBUG level
logger.setLevel("DEBUG")

# All events will be logged:
# event_type="file_download_started" printer_id="bambu_001" filename="model.3mf"
```

### Monitor Event Counts

```python
# Check event statistics
status = await event_service.get_status()
print(status["event_counts"])

# Example output:
# {
#     'printer_status': 1205,
#     'printer_status_update': 5420,
#     'file_download_complete': 47,
#     'file_thumbnails_processed': 45,
#     'job_started': 23,
#     'job_completed': 21
# }
```

### Trace Specific Workflow

Add temporary logging in event handlers:

```python
async def _handle_download_complete(self, data: Dict[str, Any]):
    logger.info("TRACE: Download complete handler triggered",
                file_id=data["file_id"],
                filename=data["filename"])
    # ... rest of handler
```

---

## See Also

- [EVENT_CONTRACTS.md](EVENT_CONTRACTS.md) - Complete event documentation
- [CIRCULAR_DEPENDENCY_AUDIT.md](CIRCULAR_DEPENDENCY_AUDIT.md) - Service dependency audit
- [Architecture Documentation](.claude/skills/printernizer-architecture.md) - System architecture
- [EventService Implementation](../src/services/event_service.py) - Event system source code
