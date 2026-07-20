# Features

Printernizer provides a comprehensive set of features for professional 3D printer management. This section details each feature's implementation, usage, and configuration.

## Feature Documentation

### Files & Library
- **[Auto Download System](AUTO_DOWNLOAD_SYSTEM.md)** - Automatic file downloads from printers
- **[3D Model Metadata](ENHANCED_3D_MODEL_METADATA_TECHNICAL.md)** - Metadata extraction from 3D files
- **[Preview Rendering](PREVIEW_RENDERING.md)** - Server-side preview generation
- **[Thumbnails](THUMBNAILS.md)** - Thumbnail extraction and caching
- **[Bambu Lab Thumbnails](bambu-thumbnails.md)** - Bambu-specific thumbnail handling
- **[GCode Optimization](GCODE_OPTIMIZATION.md)** - G-code parsing and optimization

### Printing & Slicing
- **[Printer Feature Comparison](PRINTER_FEATURE_COMPARISON.md)** - What each printer type supports
- **[Slicer Integration](../SLICER_INTEGRATION.md)** - Local and remote slicing
- **[Slicer Setup](../SLICER-SETUP.md)** - Installing and configuring a slicer
- **[Slicer API Examples](../SLICER_API_EXAMPLES.md)** - Working with the slicing API

### Business
- **[Orders](ORDERS.md)** - Customer orders, statuses, and linked jobs

### Tools
- **[Model Generator](../model-generator.md)** - Browser-based parametric model generation
- **[Camera Setup](../CAMERA_SETUP.md)** - Printer and external camera configuration
- **[Trending Models Workflow](trending-models-workflow.md)** - Importing models from platforms
- **[Frontend Auto Reload](FRONTEND_AUTO_RELOAD.md)** - Development convenience

## Feature Categories

### Printer Integration
- Multi-printer support (Bambu Lab, Prusa, OctoPrint)
- Auto-discovery (SSDP + mDNS)
- Connection health monitoring
- Automatic retry logic

### Real-time Monitoring
- Live status updates via WebSocket
- Temperature tracking
- Layer-by-layer progress
- Time remaining estimates

### File Operations
- Central library with checksum-based deduplication
- Watch folders with per-folder rules and auto-slice
- Tags and unified search
- One-click downloads
- 3D preview generation (STL, 3MF, GCODE, BGCODE)

### Analytics & Reporting
- Print success rates
- Material usage and inventory tracking
- Printer utilization metrics
- Business vs. private job tracking

## Configuration

Most features can be configured via the settings interface or environment variables. See the [Settings Reference](../user-guide/SETTINGS_REFERENCE.md) for details.

## Planned Features

Check the [GitHub Issues](https://github.com/schmacka/printernizer/issues) for upcoming features and enhancements.
