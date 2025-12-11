-- Migration: Add manufacturer and printer_model fields to library_file_sources
-- Purpose: Enhanced source tracking with manufacturer and model information for better filtering and analytics
-- Version: 1.0.4
-- Date: 2025-10-04

-- Add manufacturer column (maps to PrinterType enum: bambu_lab, prusa_research)
ALTER TABLE library_file_sources ADD COLUMN manufacturer TEXT;

-- Add printer_model column (e.g., A1, P1P, X1C, Core One, MK4)
ALTER TABLE library_file_sources ADD COLUMN printer_model TEXT;

-- Create indexes for efficient filtering by manufacturer and model
CREATE INDEX IF NOT EXISTS idx_library_sources_manufacturer
    ON library_file_sources(manufacturer);

CREATE INDEX IF NOT EXISTS idx_library_sources_printer_model
    ON library_file_sources(printer_model);

-- Create composite index for combined manufacturer+model filtering
CREATE INDEX IF NOT EXISTS idx_library_sources_manufacturer_model
    ON library_file_sources(manufacturer, printer_model);

-- Optional: Backfill existing records with manufacturer info from metadata JSON
-- This will extract manufacturer from existing metadata where available
UPDATE library_file_sources
SET manufacturer = (
    CASE
        WHEN source_type = 'printer' AND json_extract(metadata, '$.printer_type') IS NOT NULL
        THEN json_extract(metadata, '$.printer_type')
        ELSE NULL
    END
)
WHERE manufacturer IS NULL AND source_type = 'printer';

-- Note: printer_model backfilling would require parsing printer_name or additional metadata
-- This can be done manually or via a background task after deployment
