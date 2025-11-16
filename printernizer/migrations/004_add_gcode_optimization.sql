-- Migration: Add G-code preview optimization settings
-- Date: 2025-09-30
-- Description: Add configuration options for G-code preview optimization

-- Add G-code optimization configuration options
INSERT OR IGNORE INTO configuration (key, value, value_type, category, description) VALUES
('gcode_optimization.enabled', 'true', 'boolean', 'preview', 'Enable G-code print optimization (skip warmup phase in previews)'),
('gcode_optimization.max_analysis_lines', '1000', 'integer', 'preview', 'Maximum lines to analyze for print start detection'),
('gcode_optimization.max_render_lines', '10000', 'integer', 'preview', 'Maximum lines to render in G-code preview'),
('gcode_optimization.line_color', '#007bff', 'string', 'preview', 'Color for G-code toolpath lines'),
('gcode_optimization.background_color', '#ffffff', 'string', 'preview', 'Background color for G-code renders');

-- Add index for configuration category queries
CREATE INDEX IF NOT EXISTS idx_configuration_category ON configuration(category);