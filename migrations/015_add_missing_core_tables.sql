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
