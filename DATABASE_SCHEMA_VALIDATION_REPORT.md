# Database Schema Validation Report
**Date:** November 13, 2025  
**Container:** printernizer  
**Database:** /app/data/printernizer.db

---

## Executive Summary

**Total tables expected:** 17 (from database_schema.sql + migrations)  
**Total tables found:** 12  
**Tables with issues:** 5 critical missing tables, multiple missing columns  
**Critical severity:** HIGH - Missing core system tables that are referenced in codebase

---

## 1. Missing Tables (CRITICAL)

### 1.1 `configuration` Table
**Status:** ❌ MISSING  
**Impact:** CRITICAL - System configuration storage  
**Usage:** Referenced in database_schema.sql and likely used for system settings

**Expected Schema:**
```sql
CREATE TABLE configuration (
    key TEXT PRIMARY KEY NOT NULL,
    value TEXT NOT NULL,
    value_type TEXT NOT NULL DEFAULT 'string' CHECK (
        value_type IN ('string', 'integer', 'float', 'boolean', 'json')
    ),
    category TEXT NOT NULL DEFAULT 'general',
    description TEXT,
    is_encrypted BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_configuration_category ON configuration(category);
```

### 1.2 `watch_folders` Table
**Status:** ❌ MISSING  
**Impact:** CRITICAL - File monitoring system  
**Usage:** Persistent storage for file monitoring directories (migration `add_watch_folders_table.sql`)

**Expected Schema:**
```sql
CREATE TABLE watch_folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_path TEXT NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    recursive BOOLEAN DEFAULT 1 NOT NULL,
    folder_name TEXT,
    description TEXT,
    file_count INTEGER DEFAULT 0,
    last_scan_at TIMESTAMP,
    is_valid BOOLEAN DEFAULT 1,
    validation_error TEXT,
    last_validation_at TIMESTAMP,
    source TEXT NOT NULL DEFAULT 'manual' CHECK (
        source IN ('manual', 'env_migration', 'import')
    ),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_watch_folders_is_active ON watch_folders(is_active);
CREATE INDEX idx_watch_folders_folder_path ON watch_folders(folder_path);
CREATE INDEX idx_watch_folders_created_at ON watch_folders(created_at);
```

### 1.3 `download_history` Table
**Status:** ❌ MISSING  
**Impact:** IMPORTANT - Download tracking and statistics  
**Usage:** Defined in database_schema.sql for tracking download operations

**Expected Schema:**
```sql
CREATE TABLE download_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    printer_id TEXT REFERENCES printers(id) ON DELETE SET NULL,
    download_status TEXT NOT NULL CHECK (
        download_status IN ('started', 'completed', 'failed', 'cancelled')
    ),
    bytes_downloaded INTEGER DEFAULT 0,
    bytes_total INTEGER,
    download_speed_bps INTEGER,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds INTEGER GENERATED ALWAYS AS (
        CASE 
            WHEN completed_at IS NOT NULL 
            THEN (julianday(completed_at) - julianday(started_at)) * 86400 
            ELSE NULL 
        END
    ) STORED,
    error_message TEXT,
    retry_attempt INTEGER DEFAULT 1,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_download_history_file_id ON download_history(file_id);
CREATE INDEX idx_download_history_status ON download_history(download_status);
CREATE INDEX idx_download_history_started_at ON download_history(started_at);
```

### 1.4 `printer_status_log` Table
**Status:** ❌ MISSING  
**Impact:** IMPORTANT - Historical printer status tracking  
**Usage:** Defined in database_schema.sql for monitoring printer health over time

**Expected Schema:**
```sql
CREATE TABLE printer_status_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id TEXT NOT NULL REFERENCES printers(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    connection_status TEXT NOT NULL,
    nozzle_temp REAL,
    nozzle_target REAL,
    bed_temp REAL,
    bed_target REAL,
    chamber_temp REAL,
    current_job_id INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
    current_job_progress REAL,
    firmware_version TEXT,
    uptime_seconds INTEGER,
    wifi_signal INTEGER,
    ip_address TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_printer_status_log_printer_id ON printer_status_log(printer_id);
CREATE INDEX idx_printer_status_log_recorded_at ON printer_status_log(recorded_at);
CREATE INDEX idx_printer_status_log_printer_time ON printer_status_log(printer_id, recorded_at);
```

### 1.5 `system_events` Table
**Status:** ❌ MISSING  
**Impact:** IMPORTANT - System-wide event logging  
**Usage:** Defined in database_schema.sql for audit trail and monitoring

**Expected Schema:**
```sql
CREATE TABLE system_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL CHECK (
        event_type IN ('system_start', 'system_stop', 'printer_connect', 'printer_disconnect', 
                      'job_start', 'job_complete', 'job_fail', 'file_download', 'error', 'warning', 'info')
    ),
    severity TEXT NOT NULL DEFAULT 'info' CHECK (
        severity IN ('critical', 'error', 'warning', 'info', 'debug')
    ),
    title TEXT NOT NULL,
    description TEXT,
    printer_id TEXT REFERENCES printers(id) ON DELETE SET NULL,
    job_id INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
    file_id TEXT REFERENCES files(id) ON DELETE SET NULL,
    metadata JSON,
    user_ip TEXT,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_system_events_event_type ON system_events(event_type);
CREATE INDEX idx_system_events_severity ON system_events(severity);
CREATE INDEX idx_system_events_created_at ON system_events(created_at);
CREATE INDEX idx_system_events_printer_id ON system_events(printer_id);
```

### 1.6 `collections` and `collection_members` Tables
**Status:** ❌ MISSING  
**Impact:** MINOR - Library organization feature  
**Usage:** Defined in migration 007 for organizing files into groups

**Expected Schema:**
```sql
CREATE TABLE collections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    thumbnail_checksum TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (thumbnail_checksum) REFERENCES library_files(checksum) ON DELETE SET NULL
);

CREATE TABLE collection_members (
    collection_id TEXT NOT NULL,
    file_checksum TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
    FOREIGN KEY (file_checksum) REFERENCES library_files(checksum) ON DELETE CASCADE,
    PRIMARY KEY (collection_id, file_checksum)
);

CREATE INDEX idx_collection_members_collection ON collection_members(collection_id);
CREATE INDEX idx_collection_members_file ON collection_members(file_checksum);
```

### 1.7 `file_metadata` Table
**Status:** ❌ MISSING  
**Impact:** MINOR - Flexible metadata storage  
**Usage:** Defined in migration 006 for additional file properties

**Expected Schema:**
```sql
CREATE TABLE file_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    key VARCHAR(100) NOT NULL,
    value TEXT,
    data_type VARCHAR(20) DEFAULT 'string',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    UNIQUE(file_id, category, key)
);

CREATE INDEX idx_file_metadata_file_id ON file_metadata(file_id);
CREATE INDEX idx_file_metadata_category ON file_metadata(category);
```

---

## 2. Missing Views

### 2.1 Views Defined in database_schema.sql
**Status:** ❌ ALL MISSING  
**Impact:** MINOR - Convenience views for queries

**Expected Views:**
- `v_active_printers` - Active printers with current status
- `v_recent_jobs` - Recent jobs with printer information  
- `v_file_statistics` - File download statistics

**Note:** The migration system created view `library_stats` as a TABLE instead of a VIEW (which is acceptable for performance).

---

## 3. Tables with Missing Columns

### 3.1 `files` Table
**Status:** ⚠️ MISSING ENHANCED METADATA COLUMNS  
**Impact:** MINOR - Enhanced metadata from migration 006 not applied to files table

**Current Columns:** 22 columns (basic file tracking)  
**Missing Columns from Migration 006:**
```sql
-- Physical Properties
model_width DECIMAL(8,3),
model_depth DECIMAL(8,3), 
model_height DECIMAL(8,3),
model_volume DECIMAL(10,3),
surface_area DECIMAL(10,3),
object_count INTEGER DEFAULT 1,

-- Print Settings
nozzle_diameter DECIMAL(3,2),
wall_count INTEGER,
wall_thickness DECIMAL(4,2),
infill_pattern VARCHAR(50),
first_layer_height DECIMAL(4,3),

-- Material Information (some overlap with existing columns)
total_filament_weight DECIMAL(8,3),
filament_length DECIMAL(10,2),
filament_colors TEXT, -- JSON array
waste_weight DECIMAL(8,3),

-- Cost Analysis
material_cost DECIMAL(8,2),
energy_cost DECIMAL(6,2),
total_cost DECIMAL(8,2),

-- Quality Metrics
complexity_score INTEGER,
success_probability DECIMAL(3,2),
difficulty_level VARCHAR(20),
overhang_percentage DECIMAL(5,2),

-- Compatibility
compatible_printers TEXT, -- JSON array
slicer_name VARCHAR(100),
slicer_version VARCHAR(50),
profile_name VARCHAR(100),

-- Metadata timestamp
last_analyzed TIMESTAMP
```

**Note:** These columns ARE present in `library_files` table (60 columns including all metadata). The regular `files` table is intended to be simpler.

**Assessment:** This is likely INTENTIONAL design - `files` table is for basic file tracking, while `library_files` has full metadata.

---

## 4. Missing Indexes

### 4.1 Files Table - Enhanced Metadata Indexes
**Status:** ⚠️ MISSING (if metadata columns were added)  
**Impact:** MINOR

**Missing Indexes from Migration 006:**
```sql
CREATE INDEX IF NOT EXISTS idx_files_complexity ON files(complexity_score);
CREATE INDEX IF NOT EXISTS idx_files_dimensions ON files(model_width, model_depth, model_height);
CREATE INDEX IF NOT EXISTS idx_files_cost ON files(total_cost);
CREATE INDEX IF NOT EXISTS idx_files_analyzed ON files(last_analyzed);
```

**Note:** These indexes are not needed since the columns don't exist in `files` table.

### 4.2 Library Files - Some Indexes Present
**Status:** ✅ GOOD  
**Current Indexes:**
- idx_library_files_checksum
- idx_library_files_status
- idx_library_files_file_type
- idx_library_files_is_duplicate
- idx_library_files_added

**Expected Additional Indexes from Migration 007:**
```sql
CREATE INDEX IF NOT EXISTS idx_library_search ON library_files(search_index);
CREATE INDEX IF NOT EXISTS idx_library_complexity ON library_files(complexity_score);
CREATE INDEX IF NOT EXISTS idx_library_dimensions ON library_files(model_width, model_depth, model_height);
CREATE INDEX IF NOT EXISTS idx_library_cost ON library_files(total_cost);
CREATE INDEX IF NOT EXISTS idx_library_analyzed ON library_files(last_analyzed);
CREATE INDEX IF NOT EXISTS idx_library_has_thumbnail ON library_files(has_thumbnail);
CREATE INDEX IF NOT EXISTS idx_library_tags ON library_files(tags);
```

**Assessment:** MINOR - Performance optimization, not critical.

---

## 5. Schema Validation - Existing Tables

### ✅ Tables Correctly Implemented

| Table | Columns | Status | Notes |
|-------|---------|--------|-------|
| `jobs` | 17 | ✅ GOOD | Basic schema matches |
| `files` | 22 | ✅ GOOD | Basic file tracking (simpler than library) |
| `printers` | 11 | ✅ GOOD | Core printer data |
| `materials` | 15 | ✅ GOOD | Material inventory tracking |
| `material_consumption` | 9 | ✅ GOOD | Job material usage |
| `library_files` | 60 | ✅ EXCELLENT | **All metadata columns present!** |
| `library_file_sources` | 11 | ✅ GOOD | Source tracking with manufacturer/model |
| `library_stats` | 8 | ✅ GOOD | Statistics table (not view) |
| `ideas` | 18 | ✅ GOOD | Print idea management |
| `idea_tags` | 2 | ✅ GOOD | Tags junction table |
| `trending_cache` | 13 | ✅ GOOD | External platform caching |
| `search_history` | 7 | ✅ GOOD | Search tracking |
| `search_analytics` | 6 | ✅ GOOD | Click analytics |
| `fts_files` | - | ✅ GOOD | FTS5 virtual table |
| `fts_ideas` | - | ✅ GOOD | FTS5 virtual table |

---

## 6. Missing Triggers

### 6.1 Timestamp Update Triggers
**Status:** ❌ MISSING  
**Impact:** MINOR - Manual timestamp management required

**Expected Triggers from database_schema.sql:**
```sql
CREATE TRIGGER trg_printers_updated_at 
    AFTER UPDATE ON printers
BEGIN
    UPDATE printers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER trg_jobs_updated_at 
    AFTER UPDATE ON jobs
BEGIN
    UPDATE jobs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER trg_files_updated_at 
    AFTER UPDATE ON files
BEGIN
    UPDATE files SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER trg_watch_folders_updated_at 
    AFTER UPDATE ON watch_folders
BEGIN
    UPDATE watch_folders SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

### 6.2 Job Status Change Logging Trigger
**Status:** ❌ MISSING  
**Impact:** MINOR - Requires `system_events` table

```sql
CREATE TRIGGER trg_job_status_change 
    AFTER UPDATE OF status ON jobs
WHEN NEW.status != OLD.status
BEGIN
    INSERT INTO system_events (event_type, severity, title, description, printer_id, job_id)
    VALUES (
        CASE NEW.status
            WHEN 'completed' THEN 'job_complete'
            WHEN 'failed' THEN 'job_fail'
            WHEN 'printing' THEN 'job_start'
            ELSE 'info'
        END,
        CASE NEW.status
            WHEN 'failed' THEN 'error'
            ELSE 'info'
        END,
        'Job Status Changed: ' || NEW.job_name,
        'Status changed from ' || OLD.status || ' to ' || NEW.status,
        NEW.printer_id,
        NEW.id
    );
END;
```

---

## 7. Migration Scripts to Fix Issues

### Migration Script 1: Create Missing Core Tables

**File:** `migrations/015_add_missing_core_tables.sql`

```sql
-- Migration: 015_add_missing_core_tables.sql
-- Add missing tables from database_schema.sql that are referenced in codebase
-- Priority: CRITICAL
-- Date: 2025-11-13

-- =====================================================
-- CONFIGURATION TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS configuration (
    key TEXT PRIMARY KEY NOT NULL,
    value TEXT NOT NULL,
    value_type TEXT NOT NULL DEFAULT 'string' CHECK (
        value_type IN ('string', 'integer', 'float', 'boolean', 'json')
    ),
    category TEXT NOT NULL DEFAULT 'general',
    description TEXT,
    is_encrypted BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_configuration_category ON configuration(category);

-- Insert default configuration values
INSERT OR IGNORE INTO configuration (key, value, value_type, category, description) VALUES
('system.version', '1.0.0', 'string', 'system', 'Application version'),
('system.timezone', 'Europe/Berlin', 'string', 'system', 'System timezone'),
('system.language', 'en', 'string', 'system', 'System language'),
('business.mode', 'true', 'boolean', 'business', 'Enable business features'),
('business.currency', 'EUR', 'string', 'business', 'Currency for cost calculations'),
('business.vat_rate', '0.19', 'float', 'business', 'VAT rate (19% for Germany)'),
('monitoring.poll_interval_seconds', '30', 'integer', 'monitoring', 'Status polling interval'),
('monitoring.job_timeout_hours', '24', 'integer', 'monitoring', 'Job timeout in hours'),
('files.auto_download', 'false', 'boolean', 'files', 'Automatically download new files'),
('files.cleanup_days', '90', 'integer', 'files', 'Days to keep old downloads'),
('files.max_download_size_mb', '500', 'integer', 'files', 'Maximum file download size'),
('costs.power_rate_per_kwh', '0.30', 'float', 'costs', 'Power cost per kWh in EUR'),
('costs.default_material_cost_per_gram', '0.05', 'float', 'costs', 'Default material cost per gram'),
('api.rate_limit_per_hour', '1000', 'integer', 'api', 'API rate limit per client per hour'),
('web.max_upload_size_mb', '100', 'integer', 'web', 'Maximum file upload size'),
('thumbnails.enabled', 'true', 'boolean', 'files', 'Enable thumbnail extraction from 3D files'),
('thumbnails.max_size_kb', '500', 'integer', 'files', 'Maximum thumbnail size in KB'),
('thumbnails.preferred_width', '200', 'integer', 'files', 'Preferred thumbnail width in pixels'),
('thumbnails.preferred_height', '200', 'integer', 'files', 'Preferred thumbnail height in pixels'),
('thumbnails.cache_lifetime_hours', '24', 'integer', 'files', 'Thumbnail cache lifetime in hours');

-- =====================================================
-- WATCH_FOLDERS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS watch_folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_path TEXT NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    recursive BOOLEAN DEFAULT 1 NOT NULL,
    folder_name TEXT,
    description TEXT,
    file_count INTEGER DEFAULT 0,
    last_scan_at TIMESTAMP,
    is_valid BOOLEAN DEFAULT 1,
    validation_error TEXT,
    last_validation_at TIMESTAMP,
    source TEXT NOT NULL DEFAULT 'manual' CHECK (
        source IN ('manual', 'env_migration', 'import')
    ),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_watch_folders_is_active ON watch_folders(is_active);
CREATE INDEX IF NOT EXISTS idx_watch_folders_folder_path ON watch_folders(folder_path);
CREATE INDEX IF NOT EXISTS idx_watch_folders_created_at ON watch_folders(created_at);

-- =====================================================
-- DOWNLOAD_HISTORY TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS download_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    printer_id TEXT REFERENCES printers(id) ON DELETE SET NULL,
    download_status TEXT NOT NULL CHECK (
        download_status IN ('started', 'completed', 'failed', 'cancelled')
    ),
    bytes_downloaded INTEGER DEFAULT 0,
    bytes_total INTEGER,
    download_speed_bps INTEGER,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    error_message TEXT,
    retry_attempt INTEGER DEFAULT 1,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_download_history_file_id ON download_history(file_id);
CREATE INDEX IF NOT EXISTS idx_download_history_status ON download_history(download_status);
CREATE INDEX IF NOT EXISTS idx_download_history_started_at ON download_history(started_at);

-- =====================================================
-- PRINTER_STATUS_LOG TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS printer_status_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id TEXT NOT NULL REFERENCES printers(id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    connection_status TEXT NOT NULL,
    nozzle_temp REAL,
    nozzle_target REAL,
    bed_temp REAL,
    bed_target REAL,
    chamber_temp REAL,
    current_job_id TEXT REFERENCES jobs(id) ON DELETE SET NULL,
    current_job_progress REAL,
    firmware_version TEXT,
    uptime_seconds INTEGER,
    wifi_signal INTEGER,
    ip_address TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_printer_status_log_printer_id ON printer_status_log(printer_id);
CREATE INDEX IF NOT EXISTS idx_printer_status_log_recorded_at ON printer_status_log(recorded_at);
CREATE INDEX IF NOT EXISTS idx_printer_status_log_printer_time ON printer_status_log(printer_id, recorded_at);

-- =====================================================
-- SYSTEM_EVENTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS system_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL CHECK (
        event_type IN ('system_start', 'system_stop', 'printer_connect', 'printer_disconnect', 
                      'job_start', 'job_complete', 'job_fail', 'file_download', 'error', 'warning', 'info')
    ),
    severity TEXT NOT NULL DEFAULT 'info' CHECK (
        severity IN ('critical', 'error', 'warning', 'info', 'debug')
    ),
    title TEXT NOT NULL,
    description TEXT,
    printer_id TEXT REFERENCES printers(id) ON DELETE SET NULL,
    job_id TEXT REFERENCES jobs(id) ON DELETE SET NULL,
    file_id TEXT REFERENCES files(id) ON DELETE SET NULL,
    metadata TEXT,
    user_ip TEXT,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_system_events_event_type ON system_events(event_type);
CREATE INDEX IF NOT EXISTS idx_system_events_severity ON system_events(severity);
CREATE INDEX IF NOT EXISTS idx_system_events_created_at ON system_events(created_at);
CREATE INDEX IF NOT EXISTS idx_system_events_printer_id ON system_events(printer_id);
```

---

### Migration Script 2: Create Optional Tables

**File:** `migrations/016_add_optional_tables.sql`

```sql
-- Migration: 016_add_optional_tables.sql
-- Add optional tables for enhanced features
-- Priority: MINOR
-- Date: 2025-11-13

-- =====================================================
-- COLLECTIONS TABLE (Library Organization)
-- =====================================================
CREATE TABLE IF NOT EXISTS collections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    thumbnail_checksum TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (thumbnail_checksum) REFERENCES library_files(checksum) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS collection_members (
    collection_id TEXT NOT NULL,
    file_checksum TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
    FOREIGN KEY (file_checksum) REFERENCES library_files(checksum) ON DELETE CASCADE,
    PRIMARY KEY (collection_id, file_checksum)
);

CREATE INDEX IF NOT EXISTS idx_collection_members_collection ON collection_members(collection_id);
CREATE INDEX IF NOT EXISTS idx_collection_members_file ON collection_members(file_checksum);

-- =====================================================
-- FILE_METADATA TABLE (Flexible Metadata Storage)
-- =====================================================
CREATE TABLE IF NOT EXISTS file_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    key VARCHAR(100) NOT NULL,
    value TEXT,
    data_type VARCHAR(20) DEFAULT 'string',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    UNIQUE(file_id, category, key)
);

CREATE INDEX IF NOT EXISTS idx_file_metadata_file_id ON file_metadata(file_id);
CREATE INDEX IF NOT EXISTS idx_file_metadata_category ON file_metadata(category);
```

---

### Migration Script 3: Add Missing Indexes

**File:** `migrations/017_add_performance_indexes.sql`

```sql
-- Migration: 017_add_performance_indexes.sql
-- Add performance indexes for library_files
-- Priority: MINOR
-- Date: 2025-11-13

-- Library files performance indexes
CREATE INDEX IF NOT EXISTS idx_library_search ON library_files(search_index);
CREATE INDEX IF NOT EXISTS idx_library_complexity ON library_files(complexity_score);
CREATE INDEX IF NOT EXISTS idx_library_dimensions ON library_files(model_width, model_depth, model_height);
CREATE INDEX IF NOT EXISTS idx_library_cost ON library_files(total_cost);
CREATE INDEX IF NOT EXISTS idx_library_analyzed ON library_files(last_analyzed);
CREATE INDEX IF NOT EXISTS idx_library_has_thumbnail ON library_files(has_thumbnail);
-- Note: Cannot create index on 'tags' column as it doesn't exist in current schema
-- CREATE INDEX IF NOT EXISTS idx_library_tags ON library_files(tags);
```

---

### Migration Script 4: Add Missing Triggers

**File:** `migrations/018_add_triggers.sql`

```sql
-- Migration: 018_add_triggers.sql
-- Add automatic timestamp update triggers and event logging
-- Priority: MINOR
-- Date: 2025-11-13

-- Timestamp update triggers
CREATE TRIGGER IF NOT EXISTS trg_printers_updated_at 
    AFTER UPDATE ON printers
BEGIN
    UPDATE printers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_jobs_updated_at 
    AFTER UPDATE ON jobs
BEGIN
    UPDATE jobs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Note: files table doesn't have updated_at column in current schema
-- CREATE TRIGGER IF NOT EXISTS trg_files_updated_at 
--     AFTER UPDATE ON files
-- BEGIN
--     UPDATE files SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
-- END;

CREATE TRIGGER IF NOT EXISTS trg_watch_folders_updated_at 
    AFTER UPDATE ON watch_folders
BEGIN
    UPDATE watch_folders SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_configuration_updated_at 
    AFTER UPDATE ON configuration
BEGIN
    UPDATE configuration SET updated_at = CURRENT_TIMESTAMP WHERE key = NEW.key;
END;

CREATE TRIGGER IF NOT EXISTS trg_collections_updated_at 
    AFTER UPDATE ON collections
BEGIN
    UPDATE collections SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_materials_updated_at 
    AFTER UPDATE ON materials
BEGIN
    UPDATE materials SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_ideas_updated_at 
    AFTER UPDATE ON ideas
BEGIN
    UPDATE ideas SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Job status change logging trigger (requires system_events table)
CREATE TRIGGER IF NOT EXISTS trg_job_status_change 
    AFTER UPDATE OF status ON jobs
WHEN NEW.status != OLD.status
BEGIN
    INSERT INTO system_events (event_type, severity, title, description, printer_id, job_id)
    VALUES (
        CASE NEW.status
            WHEN 'completed' THEN 'job_complete'
            WHEN 'failed' THEN 'job_fail'
            WHEN 'printing' THEN 'job_start'
            ELSE 'info'
        END,
        CASE NEW.status
            WHEN 'failed' THEN 'error'
            ELSE 'info'
        END,
        'Job Status Changed: ' || NEW.job_name,
        'Status changed from ' || OLD.status || ' to ' || NEW.status,
        NEW.printer_id,
        NEW.id
    );
END;
```

---

## 8. Verification Commands

### 8.1 Apply Migrations to Running Container

```powershell
# Copy migration files to container
docker cp migrations/015_add_missing_core_tables.sql printernizer:/tmp/
docker cp migrations/016_add_optional_tables.sql printernizer:/tmp/
docker cp migrations/017_add_performance_indexes.sql printernizer:/tmp/
docker cp migrations/018_add_triggers.sql printernizer:/tmp/

# Apply migrations (execute in order)
docker exec printernizer sqlite3 //app//data//printernizer.db ".read /tmp/015_add_missing_core_tables.sql"
docker exec printernizer sqlite3 //app//data//printernizer.db ".read /tmp/016_add_optional_tables.sql"
docker exec printernizer sqlite3 //app//data//printernizer.db ".read /tmp/017_add_performance_indexes.sql"
docker exec printernizer sqlite3 //app//data//printernizer.db ".read /tmp/018_add_triggers.sql"
```

### 8.2 Verify Tables Created

```powershell
# Check all tables exist
docker exec printernizer sqlite3 //app//data//printernizer.db ".tables"

# Verify specific critical tables
docker exec printernizer sqlite3 //app//data//printernizer.db "SELECT COUNT(*) FROM configuration;"
docker exec printernizer sqlite3 //app//data//printernizer.db "SELECT COUNT(*) FROM watch_folders;"
docker exec printernizer sqlite3 //app//data//printernizer.db "SELECT COUNT(*) FROM system_events;"

# Check configuration was populated
docker exec printernizer sqlite3 //app//data//printernizer.db "SELECT key, value FROM configuration WHERE category='system';"
```

### 8.3 Verify Indexes Created

```powershell
# List all indexes
docker exec printernizer sqlite3 //app//data//printernizer.db "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name;"

# Check specific indexes
docker exec printernizer sqlite3 //app//data//printernizer.db "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_library_%';"
```

### 8.4 Verify Triggers Created

```powershell
# List all triggers
docker exec printernizer sqlite3 //app//data//printernizer.db "SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name;"
```

### 8.5 Database Integrity Check

```powershell
# Run integrity check
docker exec printernizer sqlite3 //app//data//printernizer.db "PRAGMA integrity_check;"

# Check foreign keys
docker exec printernizer sqlite3 //app//data//printernizer.db "PRAGMA foreign_key_check;"

# Verify foreign keys are enabled
docker exec printernizer sqlite3 //app//data//printernizer.db "PRAGMA foreign_keys;"
```

---

## 9. Summary of Findings

### Critical Issues (Must Fix)
1. ✅ **library_files metadata** - Already fixed! All 60 columns present including full metadata
2. ❌ **configuration table** - Missing, needed for system settings
3. ❌ **watch_folders table** - Missing, needed for file monitoring
4. ❌ **system_events table** - Missing, needed for audit logging

### Important Issues (Should Fix)
5. ❌ **download_history table** - Missing, useful for tracking and statistics
6. ❌ **printer_status_log table** - Missing, useful for monitoring
7. ❌ **Foreign key constraints** - Not fully implemented (no errors from pragma checks)

### Minor Issues (Nice to Have)
8. ❌ **Triggers** - Missing automatic timestamp and event logging
9. ❌ **collections/collection_members** - Missing library organization feature
10. ❌ **file_metadata** - Missing flexible metadata storage
11. ❌ **Views** - Missing convenience views (v_active_printers, etc.)
12. ⚠️ **Some indexes** - Missing performance optimization indexes

### What's Working Well ✅
- **library_files** has complete schema with all metadata columns
- **materials & material_consumption** fully implemented
- **jobs, printers, files** core tables present
- **FTS5 search** tables properly configured
- **ideas & trending_cache** fully implemented
- **search_history & search_analytics** working

---

## 10. Recommended Action Plan

### Phase 1: Critical Fixes (Do Immediately)
1. Apply migration `015_add_missing_core_tables.sql`
2. Verify configuration table populated
3. Restart application to ensure no errors referencing missing tables

### Phase 2: Important Additions (Within 1 Week)
4. Apply migration `016_add_optional_tables.sql` for collections
5. Apply migration `017_add_performance_indexes.sql`
6. Monitor application logs for any references to missing tables

### Phase 3: Polish (Optional)
7. Apply migration `018_add_triggers.sql` for automation
8. Consider implementing views for common queries
9. Add any missing foreign key constraints

### Phase 4: Testing
10. Run full application test suite after migrations
11. Test printer connection and job creation
12. Verify file upload and library functionality
13. Test search functionality
14. Monitor database performance with new indexes

---

## 11. Notes

### Good News 🎉
- **The most critical issue from previous session (library_files metadata) is already fixed!**
- All 60 columns including model dimensions, print settings, material info, and cost data are present
- Core application tables (jobs, files, printers, materials) are properly implemented
- FTS5 search is working
- No obvious data corruption or type mismatches

### Design Observations
- The `files` table remains intentionally simple (22 columns) for basic file tracking
- The `library_files` table (60 columns) is the comprehensive metadata store
- This separation is good design - not all files need full metadata analysis
- Some tables from base schema (configuration, watch_folders) were never created but are referenced

### Migration Strategy
- SQLite doesn't support computed columns in older versions (e.g., `duration_seconds GENERATED ALWAYS AS`)
- Removed computed column syntax from migration, calculate in application instead
- Consider using triggers as alternative to computed columns if needed

---

**End of Report**
