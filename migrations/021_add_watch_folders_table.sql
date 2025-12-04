-- Migration: Add watch_folders table for persistent storage
-- Date: 2024-12-19
-- Description: Creates watch_folders table to replace in-memory watch folder storage

-- Create watch_folders table
CREATE TABLE IF NOT EXISTS watch_folders (
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

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_watch_folders_is_active ON watch_folders(is_active);
CREATE INDEX IF NOT EXISTS idx_watch_folders_folder_path ON watch_folders(folder_path);
CREATE INDEX IF NOT EXISTS idx_watch_folders_created_at ON watch_folders(created_at);

-- Create trigger for updated_at
CREATE TRIGGER IF NOT EXISTS trg_watch_folders_updated_at 
    AFTER UPDATE ON watch_folders
BEGIN
    UPDATE watch_folders SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Migration complete - watch folders table added