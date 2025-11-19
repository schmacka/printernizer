# Features

Printernizer provides a comprehensive set of features for professional 3D printer management. This section details each feature's implementation, usage, and configuration.

## Core Features

### Job Monitoring
- **[Job Monitoring](job-monitoring.md)** - Real-time print job tracking and progress monitoring

### File Management
- **[File Management](file-management.md)** - Unified file browser for all printers
- **[Auto File Download](auto-file-download.md)** - Automatic file downloads from printers
- **[Metadata System](metadata.md)** - File metadata and tagging system

### Business Features
- **[Business Analytics](business-analytics.md)** - Usage statistics and performance metrics

## Feature Categories

### Printer Integration
- Multi-printer support (Bambu Lab A1, Prusa Core One)
- Auto-discovery (SSDP for Bambu Lab, mDNS for Prusa)
- Connection health monitoring
- Automatic retry logic

### Real-time Monitoring
- Live status updates via WebSocket
- Temperature tracking
- Layer-by-layer progress
- Time remaining estimates

### File Operations
- Unified file browser
- One-click downloads
- 3D preview generation (STL, 3MF, GCODE, BGCODE)
- Thumbnail caching (30-day retention)
- Status tracking

### Analytics & Reporting
- Print success rates
- Material usage tracking
- Printer utilization metrics
- Business vs. private job tracking

## Detailed Documentation

Browse the feature documentation to learn about specific capabilities:

- **Auto-download** → See [Auto File Download](auto-file-download.md)
- **Job tracking** → See [Job Monitoring](job-monitoring.md)
- **File management** → See [File Management](file-management.md)
- **Business analytics** → See [Business Analytics](business-analytics.md)
- **Metadata** → See [Metadata System](metadata.md)

## Configuration

Most features can be configured via the settings interface or environment variables. See the [Settings Reference](../user-guide/SETTINGS_REFERENCE.md) for details.

## Planned Features

Check the [GitHub Issues](https://github.com/schmacka/printernizer/issues) for upcoming features and enhancements.
