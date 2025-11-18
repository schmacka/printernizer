# Printernizer Settings Reference

**Last Updated:** November 8, 2025
**Version:** 2.2.0+

This document provides a comprehensive reference for all Printernizer configuration settings. All settings can be configured via environment variables or a `.env` file.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Required Settings](#required-settings)
- [Optional Settings](#optional-settings)
- [Settings Categories](#settings-categories)
  - [Database Configuration](#database-configuration)
  - [Server Configuration](#server-configuration)
  - [Logging Configuration](#logging-configuration)
  - [Security Settings](#security-settings)
  - [CORS Configuration](#cors-configuration)
  - [Printer Settings](#printer-settings)
  - [File Management](#file-management)
  - [Watch Folders](#watch-folders)
  - [German Business Features](#german-business-features)
  - [Library System](#library-system)
  - [Timelapse Features](#timelapse-features)
  - [MQTT Integration](#mqtt-integration-optional)
  - [G-code Preview Optimization](#g-code-preview-optimization)
- [Validation Rules](#validation-rules)
- [Startup Validation](#startup-validation)
- [Examples](#examples)

---

## Quick Start

1. Copy `.env.example` to `.env`
2. Update required settings (SECRET_KEY at minimum)
3. Customize optional settings as needed
4. Run the application - settings are validated on startup

---

## Required Settings

While most settings have sensible defaults, these settings are **strongly recommended** to be explicitly set:

| Setting | Default | Why Set It |
|---------|---------|------------|
| `SECRET_KEY` | Auto-generated | Must be set for production to persist sessions across restarts |
| `DATABASE_PATH` | `/app/data/printernizer.db` | Change if using custom data directory |
| `DOWNLOADS_PATH` | `downloads` | Change to your preferred download location |

**Note:** If `SECRET_KEY` is not set or uses a default placeholder, a new key is auto-generated on each startup. This means sessions will be invalidated on restart.

---

## Optional Settings

All other settings are optional and have sensible defaults. You only need to set them if you want to customize behavior.

---

## Settings Categories

### Database Configuration

#### `DATABASE_PATH`
- **Environment Variable:** `DATABASE_PATH`
- **Type:** String (file path)
- **Default:** `/app/data/printernizer.db`
- **Description:** Path to SQLite database file. Parent directory must exist and be writable.
- **Validation:** Path is automatically converted to absolute. Parent directory is created if needed.
- **Example:** `/app/data/printernizer.db`

---

### Server Configuration

#### `API_HOST`
- **Environment Variable:** `API_HOST`
- **Type:** String (IP address)
- **Default:** `0.0.0.0`
- **Range:** Valid IP address
- **Description:** API server bind address. Use `0.0.0.0` for all interfaces or `127.0.0.1` for localhost only.
- **Example:** `0.0.0.0`

#### `API_PORT`
- **Environment Variable:** `API_PORT`
- **Type:** Integer
- **Default:** `8000`
- **Range:** 1-65535
- **Description:** API server port. Using ports < 1024 may require root privileges.
- **Validation:** Must be a valid port number between 1 and 65535.
- **Example:** `8000`

#### `ENVIRONMENT`
- **Environment Variable:** `ENVIRONMENT`
- **Type:** String (enum)
- **Default:** `production`
- **Valid Values:** `development`, `production`, `homeassistant`, `testing`
- **Description:** Application environment. Affects logging verbosity and some features.
- **Example:** `production`

---

### Logging Configuration

#### `LOG_LEVEL`
- **Environment Variable:** `LOG_LEVEL`
- **Type:** String (enum)
- **Default:** `info`
- **Valid Values:** `debug`, `info`, `warning`, `error`, `critical`
- **Description:** Logging level for application output.
- **Validation:** Case-insensitive, automatically lowercased.
- **Example:** `info`

---

### Security Settings

#### `SECRET_KEY`
- **Environment Variable:** `SECRET_KEY`
- **Type:** String
- **Default:** Auto-generated if not set
- **Minimum Length:** 32 characters
- **Description:** Secret key for session encryption and signing. **CRITICAL FOR PRODUCTION.**
- **Validation:**
  - Must be at least 32 characters
  - Auto-generates secure key if not provided or uses default placeholder
  - Logs warning if auto-generated
- **Generation:** `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- **Example:** `xg8wZJ3kL2mN9vB6qR5tY7uI0oP1aS2dF3gH4jK5lM6nN7bV8cC9xZ0`

---

### CORS Configuration

#### `CORS_ORIGINS`
- **Environment Variable:** `CORS_ORIGINS`
- **Type:** String (comma-separated list)
- **Default:** `""` (empty, no CORS restrictions)
- **Description:** Comma-separated list of allowed CORS origins. Empty means all origins allowed.
- **Example:** `http://localhost:3000,http://192.168.1.100:3000`

---

### Printer Settings

#### `PRINTER_POLLING_INTERVAL`
- **Environment Variable:** `PRINTER_POLLING_INTERVAL`
- **Type:** Integer (seconds)
- **Default:** `30`
- **Range:** 5-3600
- **Description:** Interval in seconds between printer status polls.
- **Validation:** Must be between 5 and 3600 seconds.
- **Example:** `30`

#### `MAX_CONCURRENT_DOWNLOADS`
- **Environment Variable:** `MAX_CONCURRENT_DOWNLOADS`
- **Type:** Integer
- **Default:** `5`
- **Range:** 1-20
- **Description:** Maximum number of concurrent file downloads from printers.
- **Validation:** Must be between 1 and 20.
- **Example:** `5`

---

### File Management

#### `DOWNLOADS_PATH`
- **Environment Variable:** `DOWNLOADS_PATH`
- **Type:** String (directory path)
- **Default:** `downloads`
- **Description:** Directory path for downloaded files. Will be created if it doesn't exist.
- **Validation:** Converted to absolute path. Created on startup if missing.
- **Example:** `/app/data/downloads`

#### `MAX_FILE_SIZE`
- **Environment Variable:** `MAX_FILE_SIZE`
- **Type:** Integer (MB)
- **Default:** `100`
- **Range:** 1-10000
- **Description:** Maximum file size in MB for downloads.
- **Validation:** Must be between 1 and 10000 MB.
- **Example:** `100`

#### `MONITORING_INTERVAL`
- **Environment Variable:** `MONITORING_INTERVAL`
- **Type:** Integer (seconds)
- **Default:** `30`
- **Range:** 5-3600
- **Description:** Interval in seconds for file monitoring.
- **Validation:** Must be between 5 and 3600 seconds.
- **Example:** `30`

#### `CONNECTION_TIMEOUT`
- **Environment Variable:** `CONNECTION_TIMEOUT`
- **Type:** Integer (seconds)
- **Default:** `30`
- **Range:** 5-300
- **Description:** Connection timeout in seconds for printer communication.
- **Validation:** Must be between 5 and 300 seconds.
- **Example:** `30`

---

### Watch Folders

#### `WATCH_FOLDERS`
- **Environment Variable:** `WATCH_FOLDERS`
- **Type:** String (comma-separated paths)
- **Default:** `""` (empty)
- **Description:** Comma-separated list of folder paths to watch for new files. Leave empty to disable.
- **Example:** `/path/to/folder1,/path/to/folder2`

#### `WATCH_FOLDERS_ENABLED`
- **Environment Variable:** `WATCH_FOLDERS_ENABLED`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable or disable watch folder monitoring globally.
- **Example:** `true`

#### `WATCH_RECURSIVE`
- **Environment Variable:** `WATCH_RECURSIVE`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable recursive monitoring of subdirectories in watch folders.
- **Example:** `true`

---

### German Business Features

#### `ENABLE_GERMAN_COMPLIANCE`
- **Environment Variable:** `ENABLE_GERMAN_COMPLIANCE`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable German business compliance features (VAT, invoicing, etc.).
- **Example:** `true`

#### `VAT_RATE`
- **Environment Variable:** `VAT_RATE`
- **Type:** Float (percentage)
- **Default:** `19.0`
- **Range:** 0.0-100.0
- **Description:** VAT rate as percentage. German standard VAT is 19%.
- **Validation:** Must be between 0.0 and 100.0.
- **Example:** `19.0`

#### `CURRENCY`
- **Environment Variable:** `CURRENCY`
- **Type:** String (ISO 4217 code)
- **Default:** `EUR`
- **Description:** Currency code for business features. Must be 3-letter ISO 4217 code.
- **Validation:** Must be exactly 3 characters. Automatically uppercased.
- **Example:** `EUR`

#### `TZ` (Timezone)
- **Environment Variable:** `TZ`
- **Type:** String (IANA timezone)
- **Default:** `Europe/Berlin`
- **Description:** Timezone for timestamps and scheduling. Use IANA timezone database names.
- **Validation:** Validated against IANA timezone database. Falls back to default if invalid.
- **Example:** `Europe/Berlin`

---

### Library System

#### `LIBRARY_ENABLED`
- **Environment Variable:** `LIBRARY_ENABLED`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable library system for file organization and management.
- **Example:** `true`

#### `LIBRARY_PATH`
- **Environment Variable:** `LIBRARY_PATH`
- **Type:** String (directory path)
- **Default:** `/app/data/library`
- **Description:** Directory path for library files. Must be absolute path. Will be created if doesn't exist.
- **Validation:** Converted to absolute path. Created on startup if missing.
- **Example:** `/app/data/library`

#### `LIBRARY_AUTO_ORGANIZE`
- **Environment Variable:** `LIBRARY_AUTO_ORGANIZE`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Automatically organize library files into subfolders.
- **Example:** `true`

#### `LIBRARY_AUTO_EXTRACT_METADATA`
- **Environment Variable:** `LIBRARY_AUTO_EXTRACT_METADATA`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Automatically extract metadata from uploaded files.
- **Example:** `true`

#### `LIBRARY_AUTO_DEDUPLICATE`
- **Environment Variable:** `LIBRARY_AUTO_DEDUPLICATE`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Automatically detect and handle duplicate files in library.
- **Example:** `true`

#### `LIBRARY_PRESERVE_ORIGINALS`
- **Environment Variable:** `LIBRARY_PRESERVE_ORIGINALS`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Preserve original files when processing library items.
- **Example:** `true`

#### `LIBRARY_CHECKSUM_ALGORITHM`
- **Environment Variable:** `LIBRARY_CHECKSUM_ALGORITHM`
- **Type:** String (enum)
- **Default:** `sha256`
- **Valid Values:** `md5`, `sha1`, `sha256`
- **Description:** Checksum algorithm for file hashing.
- **Validation:** Case-insensitive, automatically lowercased.
- **Example:** `sha256`

#### `LIBRARY_PROCESSING_WORKERS`
- **Environment Variable:** `LIBRARY_PROCESSING_WORKERS`
- **Type:** Integer
- **Default:** `2`
- **Range:** 1-10
- **Description:** Number of worker threads for library processing.
- **Validation:** Must be between 1 and 10.
- **Example:** `2`

#### `LIBRARY_SEARCH_ENABLED`
- **Environment Variable:** `LIBRARY_SEARCH_ENABLED`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable full-text search in library.
- **Example:** `true`

#### `LIBRARY_SEARCH_MIN_LENGTH`
- **Environment Variable:** `LIBRARY_SEARCH_MIN_LENGTH`
- **Type:** Integer
- **Default:** `3`
- **Range:** 1-10
- **Description:** Minimum search query length.
- **Validation:** Must be between 1 and 10 characters.
- **Example:** `3`

---

### Timelapse Features

#### `TIMELAPSE_ENABLED`
- **Environment Variable:** `TIMELAPSE_ENABLED`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable timelapse video creation feature.
- **Example:** `true`

#### `TIMELAPSE_SOURCE_FOLDER`
- **Environment Variable:** `TIMELAPSE_SOURCE_FOLDER`
- **Type:** String (directory path)
- **Default:** `/app/data/timelapse-images`
- **Description:** Folder to watch for timelapse image subfolders. Will be created if doesn't exist.
- **Validation:** Converted to absolute path. Created on startup if missing (with warning if fails).
- **Example:** `/app/data/timelapse-images`

#### `TIMELAPSE_OUTPUT_FOLDER`
- **Environment Variable:** `TIMELAPSE_OUTPUT_FOLDER`
- **Type:** String (directory path)
- **Default:** `/app/data/timelapses`
- **Description:** Folder for completed timelapse videos. Will be created if doesn't exist.
- **Validation:** Converted to absolute path. Created on startup if missing (with warning if fails).
- **Example:** `/app/data/timelapses`

#### `TIMELAPSE_OUTPUT_STRATEGY`
- **Environment Variable:** `TIMELAPSE_OUTPUT_STRATEGY`
- **Type:** String (enum)
- **Default:** `separate`
- **Valid Values:** `same`, `separate`, `both`
- **Description:** Video output location strategy.
- **Validation:** Case-insensitive, automatically lowercased.
- **Example:** `separate`

#### `TIMELAPSE_AUTO_PROCESS_TIMEOUT`
- **Environment Variable:** `TIMELAPSE_AUTO_PROCESS_TIMEOUT`
- **Type:** Integer (seconds)
- **Default:** `300`
- **Range:** 60-3600
- **Description:** Seconds to wait after last image before auto-processing.
- **Validation:** Must be between 60 and 3600 seconds.
- **Example:** `300`

#### `TIMELAPSE_CLEANUP_AGE_DAYS`
- **Environment Variable:** `TIMELAPSE_CLEANUP_AGE_DAYS`
- **Type:** Integer (days)
- **Default:** `30`
- **Range:** 1-365
- **Description:** Age threshold in days for cleanup recommendations.
- **Validation:** Must be between 1 and 365 days.
- **Example:** `30`

#### `TIMELAPSE_FLICKERFREE_PATH`
- **Environment Variable:** `TIMELAPSE_FLICKERFREE_PATH`
- **Type:** String (file path)
- **Default:** `/usr/local/bin/do_timelapse.sh`
- **Description:** Path to FlickerFree do_timelapse.sh script for video processing.
- **Validation:** Warns if file doesn't exist when timelapse is enabled.
- **Example:** `/usr/local/bin/do_timelapse.sh`

---

### MQTT Integration (Optional)

#### `MQTT_HOST`
- **Environment Variable:** `MQTT_HOST`
- **Type:** String (hostname or IP)
- **Default:** `None` (disabled)
- **Description:** MQTT broker hostname or IP address. Leave empty to disable MQTT integration.
- **Example:** `homeassistant.local`

#### `MQTT_PORT`
- **Environment Variable:** `MQTT_PORT`
- **Type:** Integer
- **Default:** `1883`
- **Range:** 1-65535
- **Description:** MQTT broker port. Standard ports are 1883 (unencrypted) or 8883 (TLS).
- **Validation:** Must be a valid port number.
- **Example:** `1883`

#### `MQTT_USERNAME`
- **Environment Variable:** `MQTT_USERNAME`
- **Type:** String
- **Default:** `None` (optional)
- **Description:** MQTT broker username for authentication.
- **Example:** `printernizer`

#### `MQTT_PASSWORD`
- **Environment Variable:** `MQTT_PASSWORD`
- **Type:** String
- **Default:** `None` (optional)
- **Description:** MQTT broker password for authentication.
- **Example:** `your_password_here`

#### `MQTT_DISCOVERY_PREFIX`
- **Environment Variable:** `MQTT_DISCOVERY_PREFIX`
- **Type:** String
- **Default:** `homeassistant`
- **Description:** MQTT topic prefix for Home Assistant discovery.
- **Example:** `homeassistant`

---

### G-code Preview Optimization

#### `GCODE_OPTIMIZE_PRINT_ONLY`
- **Environment Variable:** `GCODE_OPTIMIZE_PRINT_ONLY`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Optimize G-code preview by showing only print moves (no travel).
- **Example:** `true`

#### `GCODE_OPTIMIZATION_MAX_LINES`
- **Environment Variable:** `GCODE_OPTIMIZATION_MAX_LINES`
- **Type:** Integer
- **Default:** `1000`
- **Range:** 100-100000
- **Description:** Maximum lines to process for G-code optimization.
- **Validation:** Must be between 100 and 100000.
- **Example:** `1000`

#### `GCODE_RENDER_MAX_LINES`
- **Environment Variable:** `GCODE_RENDER_MAX_LINES`
- **Type:** Integer
- **Default:** `10000`
- **Range:** 100-1000000
- **Description:** Maximum lines to render in G-code preview.
- **Validation:** Must be between 100 and 1000000.
- **Example:** `10000`

---

### WebSocket Configuration

#### `ENABLE_WEBSOCKETS`
- **Environment Variable:** `ENABLE_WEBSOCKETS`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable WebSocket connections for real-time updates.
- **Example:** `true`

---

### Redis Configuration (Optional)

#### `REDIS_URL`
- **Environment Variable:** `REDIS_URL`
- **Type:** String (URL)
- **Default:** `None` (disabled)
- **Description:** Redis connection URL for caching. Format: `redis://host:port/db`
- **Example:** `redis://localhost:6379/0`

---

## Validation Rules

All settings are validated on startup using Pydantic validators:

### Automatic Validations
- **Numeric Ranges:** All numeric settings have min/max constraints enforced by Pydantic
- **Enum Values:** String settings with fixed choices are validated against allowed values
- **Path Normalization:** All path settings are normalized to absolute paths
- **Type Safety:** All settings are type-checked

### Custom Validations
- **SECRET_KEY:** Minimum 32 characters, auto-generates if not set
- **Paths:** Converted to absolute paths, created if missing
- **Timezone:** Validated against IANA timezone database
- **Currency:** Must be 3-letter ISO 4217 code
- **Checksums:** Must be valid algorithm (md5, sha1, sha256)

### Startup Validation
The application performs comprehensive validation on startup:
- Directory existence and permissions
- Required paths are creatable and writable
- Security settings are properly configured
- Feature dependencies are satisfied

If validation fails, the application exits with clear error messages.

---

## Startup Validation

The `validate_settings_on_startup()` function performs these checks:

1. **Critical Paths Validation**
   - Database parent directory exists and is writable
   - Downloads path is creatable and writable
   - Library path is creatable and writable (if enabled)
   - Timelapse paths are creatable (if enabled)

2. **Security Validation**
   - Secret key meets minimum length requirement

3. **Feature Dependencies**
   - FlickerFree script exists (if timelapse enabled)
   - MQTT authentication configured (if MQTT host set)

4. **Result Categories**
   - **Errors:** Critical issues that prevent startup (exit code 1)
   - **Warnings:** Non-critical issues logged for review
   - **Info:** Configuration status messages

---

## Examples

### Minimal Production Configuration

```env
# Required
SECRET_KEY=xg8wZJ3kL2mN9vB6qR5tY7uI0oP1aS2dF3gH4jK5lM6nN7bV8cC9xZ0

# Recommended
DATABASE_PATH=/app/data/printernizer.db
DOWNLOADS_PATH=/app/data/downloads
LIBRARY_PATH=/app/data/library
```

### Development Configuration

```env
ENVIRONMENT=development
LOG_LEVEL=debug
API_PORT=8000
SECRET_KEY=development-key-minimum-32-characters-long
DOWNLOADS_PATH=./downloads
LIBRARY_PATH=./library
```

### Home Assistant Add-on Configuration

```env
ENVIRONMENT=homeassistant
DATABASE_PATH=/data/printernizer.db
DOWNLOADS_PATH=/share/printernizer/downloads
LIBRARY_PATH=/share/printernizer/library

# MQTT Integration
MQTT_HOST=core-mosquitto
MQTT_PORT=1883
MQTT_USERNAME=printernizer
MQTT_PASSWORD=your_mqtt_password
MQTT_DISCOVERY_PREFIX=homeassistant
```

### Full Featured Configuration

```env
# Core
ENVIRONMENT=production
SECRET_KEY=your-generated-secret-key-here

# Server
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=info

# Paths
DATABASE_PATH=/app/data/printernizer.db
DOWNLOADS_PATH=/app/data/downloads
LIBRARY_PATH=/app/data/library

# File Management
MAX_FILE_SIZE=500
MAX_CONCURRENT_DOWNLOADS=10
MONITORING_INTERVAL=30
CONNECTION_TIMEOUT=30

# Watch Folders
WATCH_FOLDERS=/path/to/watch1,/path/to/watch2
WATCH_FOLDERS_ENABLED=true
WATCH_RECURSIVE=true

# German Business
ENABLE_GERMAN_COMPLIANCE=true
VAT_RATE=19.0
CURRENCY=EUR
TZ=Europe/Berlin

# Library
LIBRARY_ENABLED=true
LIBRARY_AUTO_ORGANIZE=true
LIBRARY_AUTO_EXTRACT_METADATA=true
LIBRARY_AUTO_DEDUPLICATE=true
LIBRARY_CHECKSUM_ALGORITHM=sha256
LIBRARY_PROCESSING_WORKERS=4

# Timelapse
TIMELAPSE_ENABLED=true
TIMELAPSE_SOURCE_FOLDER=/app/data/timelapse-images
TIMELAPSE_OUTPUT_FOLDER=/app/data/timelapses
TIMELAPSE_OUTPUT_STRATEGY=separate
TIMELAPSE_AUTO_PROCESS_TIMEOUT=300
TIMELAPSE_CLEANUP_AGE_DAYS=30

# MQTT (Home Assistant)
MQTT_HOST=homeassistant.local
MQTT_PORT=1883
MQTT_USERNAME=printernizer
MQTT_PASSWORD=your_password
MQTT_DISCOVERY_PREFIX=homeassistant

# G-code Preview
GCODE_OPTIMIZE_PRINT_ONLY=true
GCODE_OPTIMIZATION_MAX_LINES=1000
GCODE_RENDER_MAX_LINES=10000

# CORS
CORS_ORIGINS=http://localhost:3000,http://192.168.1.100:3000
```

---

## Troubleshooting

### Application Won't Start

Check the startup logs for validation errors:
```
CONFIGURATION VALIDATION FAILED
  ❌ Cannot create database directory /invalid/path: Permission denied
```

Fix the reported errors and restart.

### Sessions Lost on Restart

Set a persistent `SECRET_KEY`:
```env
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### Permission Errors

Ensure the application has write access to:
- Database parent directory
- Downloads path
- Library path
- Timelapse folders

### MQTT Connection Issues

If MQTT host is set but connection fails:
- Verify MQTT broker is running
- Check username/password are correct
- Ensure MQTT port is accessible
- Review MQTT broker logs

---

## See Also

- [.env.example](.env.example) - Example configuration file
- [CLAUDE.md](CLAUDE.md) - Project overview
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development guidelines
- [src/utils/config.py](src/utils/config.py) - Settings implementation

---

**Need Help?**
- GitHub Issues: Report configuration problems
- GitHub Discussions: Ask questions about settings
