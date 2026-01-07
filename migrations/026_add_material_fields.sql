-- Migration 026: Add color_hex, location, and is_active fields to materials table
-- color_hex: Hex color code for visual display (e.g., #FF5733)
-- location: Storage location (e.g., "Shelf A3, Drawer 2")
-- is_active: Whether the material is active/available for use

ALTER TABLE materials ADD COLUMN color_hex TEXT;
ALTER TABLE materials ADD COLUMN location TEXT;
ALTER TABLE materials ADD COLUMN is_active BOOLEAN DEFAULT 1;
