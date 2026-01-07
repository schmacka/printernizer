-- Migration 024: Add printer location and description fields
-- These fields allow organizing printers by location and adding descriptions

ALTER TABLE printers ADD COLUMN location TEXT;
ALTER TABLE printers ADD COLUMN description TEXT;
