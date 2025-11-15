-- =====================================================
-- Printernizer Database Schema - Phase 1
-- SQLite Database for Professional 3D Print Management
-- =====================================================

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- =====================================================
-- PRINTERS TABLE
-- Core printer configuration and connection details
-- =====================================================

CREATE TABLE printers (
    id TEXT PRIMARY KEY NOT NULL,              -- Unique printer identifier (e.g., 'bambu_a1_001')
    name TEXT NOT NULL,                        -- Human-readable printer name
    type TEXT NOT NULL CHECK (type IN ('bambu_lab', 'prusa')), -- Printer type
    model TEXT,                                -- Printer model (A1, Core One, etc.)
    
    -- Connection details
    ip_address TEXT NOT NULL,                  -- Printer IP address
    port INTEGER DEFAULT NULL,                 -- Custom port (if needed)
    
    -- Authentication (different per printer type)
    api_key TEXT,                             -- API key (Prusa)
    access_code TEXT,                         -- Access code (Bambu Lab)
    serial_number TEXT,                       -- Serial number (Bambu Lab)
    
    -- Status and configuration
    is_active BOOLEAN DEFAULT 1 NOT NULL,     -- Is printer enabled for monitoring
    status TEXT DEFAULT 'unknown',            -- Current connection status
    last_seen TIMESTAMP,                      -- Last successful communication
    firmware_version TEXT,                    -- Printer firmware version
    
    -- Capabilities and features
    has_camera BOOLEAN DEFAULT 0,             -- Camera support
    has_ams BOOLEAN DEFAULT 0,                -- AMS support (Bambu Lab)
    supports_remote_control BOOLEAN DEFAULT 0, -- Remote control capability
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for printers table
CREATE INDEX idx_printers_type ON printers(type);
CREATE INDEX idx_printers_status ON printers(status);
CREATE INDEX idx_printers_is_active ON printers(is_active);
CREATE INDEX idx_printers_last_seen ON printers(last_seen);

-- =====================================================
-- JOBS TABLE  
-- Print job tracking and monitoring
-- =====================================================

CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id TEXT NOT NULL REFERENCES printers(id) ON DELETE CASCADE,
    
    -- Job identification
    job_name TEXT NOT NULL,                   -- Name of the print job
    job_id_on_printer TEXT,                   -- Job ID on the printer (if available)
    file_path TEXT,                          -- Path to the source file
    
    -- Job status and progress
    status TEXT NOT NULL DEFAULT 'queued' CHECK (
        status IN ('queued', 'preparing', 'printing', 'paused', 'completed', 'failed', 'cancelled')
    ),
    progress REAL DEFAULT 0.0 CHECK (progress >= 0.0 AND progress <= 100.0), -- Progress percentage
    layer_current INTEGER DEFAULT 0,         -- Current layer number
    layer_total INTEGER,                     -- Total layers
    
    -- Timing information
    start_time TIMESTAMP,                    -- When printing started
    end_time TIMESTAMP,                      -- When printing ended
    estimated_duration INTEGER,             -- Estimated duration in seconds
    actual_duration INTEGER,                 -- Actual duration in seconds
    estimated_completion TIMESTAMP,         -- Estimated completion time
    
    -- Material information
    material_type TEXT,                      -- Material type (PLA, PETG, etc.)
    material_brand TEXT,                     -- Material brand (OVERTURE, etc.)
    material_color TEXT,                     -- Material color
    material_estimated_usage REAL,          -- Estimated material usage in grams
    material_actual_usage REAL,             -- Actual material usage in grams
    material_cost_per_gram REAL,            -- Cost per gram of material
    
    -- Print settings
    layer_height REAL,                       -- Layer height in mm
    infill_percentage INTEGER,               -- Infill percentage
    print_speed INTEGER,                     -- Print speed in mm/min
    nozzle_temperature INTEGER,             -- Nozzle temperature in Celsius
    bed_temperature INTEGER,                 -- Bed temperature in Celsius
    supports_used BOOLEAN DEFAULT 0,        -- Whether supports were used
    
    -- File information
    file_size INTEGER,                       -- File size in bytes
    file_hash TEXT,                         -- SHA256 hash of the file
    
    -- Cost calculations
    material_cost REAL DEFAULT 0.0,         -- Material cost in EUR
    power_cost REAL DEFAULT 0.0,           -- Power/electricity cost in EUR
    labor_cost REAL DEFAULT 0.0,           -- Labor cost in EUR
    total_cost REAL GENERATED ALWAYS AS (
        COALESCE(material_cost, 0) + 
        COALESCE(power_cost, 0) + 
        COALESCE(labor_cost, 0)
    ) STORED,                               -- Total cost (computed)
    
    -- Business classification
    is_business BOOLEAN DEFAULT 0 NOT NULL, -- Business vs private job
    customer_order_id TEXT,                 -- Customer order reference
    customer_name TEXT,                     -- Customer name
    
    -- Quality and outcome
    quality_rating INTEGER CHECK (quality_rating >= 1 AND quality_rating <= 5),
    first_layer_adhesion TEXT CHECK (
        first_layer_adhesion IN ('excellent', 'good', 'fair', 'poor')
    ),
    surface_finish TEXT CHECK (
        surface_finish IN ('excellent', 'good', 'fair', 'poor')
    ),
    dimensional_accuracy REAL,              -- Dimensional accuracy in mm
    
    -- Notes and additional info
    notes TEXT,                             -- User notes
    failure_reason TEXT,                    -- Reason for failure (if failed)
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for jobs table
CREATE INDEX idx_jobs_printer_id ON jobs(printer_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_is_business ON jobs(is_business);
CREATE INDEX idx_jobs_start_time ON jobs(start_time);
CREATE INDEX idx_jobs_created_at ON jobs(created_at);
CREATE INDEX idx_jobs_printer_status ON jobs(printer_id, status);
CREATE INDEX idx_jobs_business_date ON jobs(is_business, created_at);

-- =====================================================
-- FILES TABLE
-- File management and tracking system
-- =====================================================

CREATE TABLE files (
    id TEXT PRIMARY KEY NOT NULL,            -- Unique file identifier
    printer_id TEXT REFERENCES printers(id) ON DELETE SET NULL, -- Associated printer (null for local files)
    
    -- File identification
    filename TEXT NOT NULL,                  -- Current filename
    original_filename TEXT,                  -- Original filename (before sanitization)
    file_type TEXT NOT NULL,                -- File extension (.3mf, .stl, .gcode)
    file_size INTEGER NOT NULL,             -- File size in bytes
    
    -- Location and paths
    printer_path TEXT,                       -- Path on the printer
    local_path TEXT,                        -- Local filesystem path
    
    -- Status tracking
    download_status TEXT DEFAULT 'available' CHECK (
        download_status IN ('available', 'downloading', 'downloaded', 'local', 'error', 'deleted')
    ),
    status_icon TEXT GENERATED ALWAYS AS (
        CASE download_status
            WHEN 'available' THEN '📁'
            WHEN 'downloading' THEN '⏬'
            WHEN 'downloaded' THEN '✓'
            WHEN 'local' THEN '💾'
            WHEN 'error' THEN '❌'
            WHEN 'deleted' THEN '🗑️'
        END
    ) STORED,                               -- Status icon (computed)
    
    -- Download tracking
    download_attempts INTEGER DEFAULT 0,    -- Number of download attempts
    downloaded_at TIMESTAMP,               -- When file was downloaded
    last_download_attempt TIMESTAMP,       -- Last download attempt
    download_error TEXT,                   -- Last download error message
    
    -- File metadata
    checksum_md5 TEXT,                     -- MD5 checksum
    checksum_sha256 TEXT,                  -- SHA256 checksum
    
    -- Print metadata (extracted from 3MF/GCODE files)
    estimated_print_time INTEGER,          -- Estimated print time in seconds
    layer_count INTEGER,                   -- Total layer count
    layer_height REAL,                     -- Layer height
    infill_percentage INTEGER,             -- Infill percentage
    material_type TEXT,                    -- Required material type
    nozzle_temperature INTEGER,           -- Required nozzle temperature
    bed_temperature INTEGER,              -- Required bed temperature
    support_material BOOLEAN,             -- Requires support material
    
    -- Access tracking
    last_accessed TIMESTAMP,              -- Last time file was accessed
    access_count INTEGER DEFAULT 0,       -- Number of times accessed
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_on_printer TIMESTAMP          -- When file was created on printer
);

-- Indexes for files table
CREATE INDEX idx_files_printer_id ON files(printer_id);
CREATE INDEX idx_files_download_status ON files(download_status);
CREATE INDEX idx_files_file_type ON files(file_type);
CREATE INDEX idx_files_filename ON files(filename);
CREATE INDEX idx_files_created_at ON files(created_at);
CREATE INDEX idx_files_downloaded_at ON files(downloaded_at);
CREATE INDEX idx_files_printer_status ON files(printer_id, download_status);

-- =====================================================
-- DOWNLOAD_HISTORY TABLE
-- Track download operations and statistics
-- =====================================================

CREATE TABLE download_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    printer_id TEXT REFERENCES printers(id) ON DELETE SET NULL,
    
    -- Download details
    download_status TEXT NOT NULL CHECK (
        download_status IN ('started', 'completed', 'failed', 'cancelled')
    ),
    bytes_downloaded INTEGER DEFAULT 0,     -- Bytes successfully downloaded
    bytes_total INTEGER,                    -- Total bytes to download
    download_speed_bps INTEGER,            -- Download speed in bytes per second
    
    -- Timing
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,                -- When download finished
    duration_seconds INTEGER GENERATED ALWAYS AS (
        CASE 
            WHEN completed_at IS NOT NULL 
            THEN (julianday(completed_at) - julianday(started_at)) * 86400 
            ELSE NULL 
        END
    ) STORED,                              -- Download duration (computed)
    
    -- Error handling
    error_message TEXT,                    -- Error message (if failed)
    retry_attempt INTEGER DEFAULT 1,       -- Retry attempt number
    
    -- Metadata
    user_agent TEXT,                       -- Client information
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for download_history table
CREATE INDEX idx_download_history_file_id ON download_history(file_id);
CREATE INDEX idx_download_history_status ON download_history(download_status);
CREATE INDEX idx_download_history_started_at ON download_history(started_at);

-- =====================================================
-- PRINTER_STATUS_LOG TABLE
-- Historical printer status tracking
-- =====================================================

CREATE TABLE printer_status_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id TEXT NOT NULL REFERENCES printers(id) ON DELETE CASCADE,
    
    -- Status information
    status TEXT NOT NULL,                   -- Printer status
    connection_status TEXT NOT NULL,       -- Connection status
    
    -- Temperature readings
    nozzle_temp REAL,                      -- Current nozzle temperature
    nozzle_target REAL,                    -- Target nozzle temperature
    bed_temp REAL,                         -- Current bed temperature
    bed_target REAL,                       -- Target bed temperature
    chamber_temp REAL,                     -- Current chamber temperature
    
    -- Current job info (if any)
    current_job_id INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
    current_job_progress REAL,            -- Current job progress percentage
    
    -- System info
    firmware_version TEXT,                -- Firmware version
    uptime_seconds INTEGER,               -- Printer uptime in seconds
    
    -- Network info
    wifi_signal INTEGER,                  -- WiFi signal strength
    ip_address TEXT,                      -- Current IP address
    
    -- Timestamp
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for printer_status_log table
CREATE INDEX idx_printer_status_log_printer_id ON printer_status_log(printer_id);
CREATE INDEX idx_printer_status_log_recorded_at ON printer_status_log(recorded_at);
CREATE INDEX idx_printer_status_log_printer_time ON printer_status_log(printer_id, recorded_at);

-- =====================================================
-- SYSTEM_EVENTS TABLE
-- System-wide event logging
-- =====================================================

CREATE TABLE system_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Event classification
    event_type TEXT NOT NULL CHECK (
        event_type IN ('system_start', 'system_stop', 'printer_connect', 'printer_disconnect', 
                      'job_start', 'job_complete', 'job_fail', 'file_download', 'error', 'warning', 'info')
    ),
    severity TEXT NOT NULL DEFAULT 'info' CHECK (
        severity IN ('critical', 'error', 'warning', 'info', 'debug')
    ),
    
    -- Event details
    title TEXT NOT NULL,                   -- Event title/summary
    description TEXT,                      -- Detailed description
    
    -- Related entities
    printer_id TEXT REFERENCES printers(id) ON DELETE SET NULL,
    job_id INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
    file_id TEXT REFERENCES files(id) ON DELETE SET NULL,
    
    -- Additional metadata
    metadata JSON,                         -- Additional structured data
    
    -- User info
    user_ip TEXT,                         -- IP address of user (if applicable)
    user_agent TEXT,                      -- User agent (if web request)
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for system_events table
CREATE INDEX idx_system_events_event_type ON system_events(event_type);
CREATE INDEX idx_system_events_severity ON system_events(severity);
CREATE INDEX idx_system_events_created_at ON system_events(created_at);
CREATE INDEX idx_system_events_printer_id ON system_events(printer_id);

-- =====================================================
-- CONFIGURATION TABLE
-- System configuration and settings
-- =====================================================

CREATE TABLE configuration (
    key TEXT PRIMARY KEY NOT NULL,         -- Configuration key
    value TEXT NOT NULL,                   -- Configuration value (JSON or string)
    value_type TEXT NOT NULL DEFAULT 'string' CHECK (
        value_type IN ('string', 'integer', 'float', 'boolean', 'json')
    ),
    category TEXT NOT NULL DEFAULT 'general', -- Configuration category
    description TEXT,                      -- Human-readable description
    is_encrypted BOOLEAN DEFAULT 0,       -- Whether value is encrypted
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for configuration table
CREATE INDEX idx_configuration_category ON configuration(category);

-- =====================================================
-- WATCH_FOLDERS TABLE
-- Persistent storage for file monitoring directories
-- =====================================================

CREATE TABLE watch_folders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_path TEXT NOT NULL UNIQUE,         -- Absolute path to watch folder
    is_active BOOLEAN DEFAULT 1 NOT NULL,    -- Whether folder is actively monitored
    recursive BOOLEAN DEFAULT 1 NOT NULL,    -- Whether to monitor subdirectories
    
    -- Folder information
    folder_name TEXT,                         -- Display name for the folder
    description TEXT,                         -- User description
    
    -- Monitoring statistics
    file_count INTEGER DEFAULT 0,            -- Number of files discovered in folder
    last_scan_at TIMESTAMP,                  -- Last time folder was scanned
    
    -- Error handling
    is_valid BOOLEAN DEFAULT 1,              -- Whether folder path is valid/accessible
    validation_error TEXT,                   -- Last validation error message
    last_validation_at TIMESTAMP,            -- Last validation check
    
    -- Source tracking
    source TEXT NOT NULL DEFAULT 'manual' CHECK (
        source IN ('manual', 'env_migration', 'import')
    ),                                        -- How folder was added
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for watch_folders table
CREATE INDEX idx_watch_folders_is_active ON watch_folders(is_active);
CREATE INDEX idx_watch_folders_folder_path ON watch_folders(folder_path);
CREATE INDEX idx_watch_folders_created_at ON watch_folders(created_at);

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Active printers with current status
CREATE VIEW v_active_printers AS
SELECT 
    p.*,
    COUNT(j.id) as active_jobs,
    MAX(psl.recorded_at) as last_status_update,
    psl.nozzle_temp,
    psl.bed_temp,
    psl.chamber_temp
FROM printers p
LEFT JOIN jobs j ON p.id = j.printer_id AND j.status IN ('queued', 'preparing', 'printing', 'paused')
LEFT JOIN printer_status_log psl ON p.id = psl.printer_id 
    AND psl.id = (
        SELECT id FROM printer_status_log psl2 
        WHERE psl2.printer_id = p.id 
        ORDER BY recorded_at DESC LIMIT 1
    )
WHERE p.is_active = 1
GROUP BY p.id;

-- Recent jobs with printer information
CREATE VIEW v_recent_jobs AS
SELECT 
    j.*,
    p.name as printer_name,
    p.type as printer_type,
    CASE 
        WHEN j.end_time IS NOT NULL THEN 
            (julianday(j.end_time) - julianday(j.start_time)) * 86400
        ELSE 
            (julianday('now') - julianday(j.start_time)) * 86400
    END as duration_seconds_calculated
FROM jobs j
JOIN printers p ON j.printer_id = p.id
WHERE j.created_at > datetime('now', '-30 days')
ORDER BY j.created_at DESC;

-- File download statistics
CREATE VIEW v_file_statistics AS
SELECT 
    f.download_status,
    COUNT(*) as file_count,
    SUM(f.file_size) as total_size_bytes,
    AVG(f.file_size) as avg_size_bytes,
    COUNT(DISTINCT f.printer_id) as unique_printers
FROM files f
GROUP BY f.download_status;

-- =====================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =====================================================

-- Update timestamps on record changes
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

-- Log job status changes
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

-- =====================================================
-- INITIAL CONFIGURATION DATA
-- =====================================================

INSERT INTO configuration (key, value, value_type, category, description) VALUES
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
('web.max_upload_size_mb', '100', 'integer', 'web', 'Maximum file upload size');

-- =====================================================
-- DATABASE SCHEMA VALIDATION
-- =====================================================

-- Verify schema integrity
PRAGMA foreign_key_check;
PRAGMA integrity_check;

-- Show table info
SELECT 
    name,
    type,
    sql
FROM sqlite_master 
WHERE type IN ('table', 'index', 'view', 'trigger')
ORDER BY type, name;

-- =====================================================
-- End of Schema
-- =====================================================

/*
Database Schema Summary:
- 8 main tables: printers, jobs, files, download_history, printer_status_log, system_events, configuration, watch_folders
- 3 views for common queries: v_active_printers, v_recent_jobs, v_file_statistics
- Comprehensive indexing for performance
- Automatic triggers for timestamps and event logging
- Foreign key constraints for data integrity
- Check constraints for data validation
- Computed columns for derived values
- Initial configuration data for system setup
- Persistent watch folder storage with validation and monitoring statistics

Total estimated storage:
- Small deployment (2 printers, 100 jobs/month): ~10MB
- Medium deployment (5 printers, 500 jobs/month): ~50MB  
- Large deployment (10 printers, 1000 jobs/month): ~100MB

Schema designed for:
- Phase 1 core requirements
- Future extensibility
- Performance at scale
- Data integrity and consistency
- German business requirements
*/