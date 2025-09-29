# Bambu Lab A1 File Download Guide

This guide explains how to download files from your Bambu Lab A1 printer using the Printernizer application.

## Overview

Printernizer's **Drucker-Dateien** (Printer Files) system provides automated file discovery and one-click downloads from your Bambu Lab A1 printer. The system supports multiple download methods and organizes files automatically in local storage.

## Prerequisites

Before downloading files, ensure:

- **Printer Connection**: Your Bambu Lab A1 is properly configured in Printernizer with:
  - IP address
  - Access code
  - Serial number
- **Network Access**: Both printer and Printernizer are on the same network
- **Dependencies**: bambulabs_api library is installed (recommended for optimal functionality)

## Method 1: Web Interface (Recommended)

### Step 1: Access Printernizer
1. Open your web browser
2. Navigate to the Printernizer web interface (typically `http://localhost:8000`)
3. Ensure your Bambu Lab A1 printer shows as "Connected" in the status

### Step 2: Navigate to Files Section
1. Click on the **Files** or **Drucker-Dateien** menu item
2. This opens the unified file management interface showing both local and printer files

### Step 3: Discover Available Files
1. Click the **"Sync Files"** button to scan your printer for available files
2. The system will:
   - Connect to your Bambu Lab A1 via MQTT/API
   - Scan multiple file locations (cache, models, current prints)
   - Update the file list with discovered files

### Step 4: View File Status
Files are displayed with status indicators:
- **📁 Available**: File exists on printer, not downloaded locally
- **✓ Downloaded**: File has been downloaded to local storage
- **💾 Local**: File exists only in local storage/watch folders

### Step 5: Download Files
1. Locate the file you want to download in the list
2. Click the **Download** button next to the file
3. Monitor the download progress (for large files)
4. Once complete, file status changes to **✓ Downloaded**

## Method 2: API Access (Advanced Users)

### Sync Files
```bash
curl -X POST "http://localhost:8000/api/v1/files/sync"
```

### List Available Files
```bash
curl "http://localhost:8000/api/v1/files/"
```

### Download Specific File
```bash
curl -X POST "http://localhost:8000/api/v1/files/{file_id}/download"
```

### Get File Statistics
```bash
curl "http://localhost:8000/api/v1/files/statistics"
```

## Technical Implementation Details

### File Discovery Methods

The system discovers files through multiple methods:

1. **Real-time MQTT Monitoring**
   - Monitors current print jobs
   - Detects active file references
   - Updates file list automatically during printing

2. **FTP Directory Scanning**
   - Scans `/cache/` directory for temporary files
   - Checks `/model/` directory for stored models
   - Examines image directories for preview files

3. **Current Print Job Detection**
   - Extracts filename from active print status
   - Identifies recently printed files
   - Tracks file references from printer status

### Download Methods (Automatic Fallback)

The system attempts downloads in this order:

1. **bambulabs_api FTP Client** (Primary)
   - Uses the bambulabs_api library's built-in FTP functionality
   - Provides most reliable access to printer files
   - Supports authentication and secure transfer

2. **HTTP Fallback** (Secondary)
   - Attempts multiple HTTP endpoints:
     - `http://{printer_ip}/cache/{filename}`
     - `http://{printer_ip}/model/{filename}`
     - `http://{printer_ip}/files/{filename}`
     - Port 8080 variants of all above
   - Uses printer access code for authentication when required

### File Organization

Downloaded files are automatically organized:

```
downloads/
├── bambu_lab_a1_{printer_id}/
│   ├── 2024-01-15/
│   │   ├── model_001.3mf
│   │   └── print_job_002.gcode
│   └── 2024-01-16/
│       └── custom_part.3mf
```

- **Printer-specific folders**: Separate downloads by printer ID
- **Date-based organization**: Files grouped by download date
- **Secure file naming**: Prevents conflicts and ensures safe storage

## Supported File Types

The system can download various 3D printing file formats:

- **3MF files** (`.3mf`) - 3D Manufacturing Format (preferred by Bambu Lab)
- **G-code files** (`.gcode`, `.bgcode`) - Print instruction files
- **STL files** (`.stl`) - 3D model files
- **OBJ files** (`.obj`) - 3D object files
- **Preview images** (`.jpg`, `.png`) - Thumbnails and previews

## Filtering and Search

### Available Filters
- **By Printer**: Show files from specific printer only
- **By Status**: Filter by Available/Downloaded/Local status
- **By File Type**: Filter by file format (3MF, G-code, STL, etc.)
- **By Thumbnail**: Show only files with preview images

### Search Options
- **Filename search**: Find files by partial filename match
- **Date range**: Filter files by creation or download date
- **Size filtering**: Find files within specific size ranges

## Troubleshooting

### Connection Issues
- **Symptom**: "Printer not connected" error
- **Solution**: Verify printer IP, access code, and network connectivity

### No Files Found
- **Symptom**: File sync returns empty list
- **Possible causes**:
  - No files stored on printer
  - SD card not inserted
  - Files in unsupported locations
- **Solution**: Check printer storage and recent print history

### Download Failures
- **Symptom**: Download button fails or times out
- **Troubleshooting steps**:
  1. Verify printer is online and accessible
  2. Check file size (large files may timeout)
  3. Try downloading during non-print times
  4. Restart printer connection if persistent issues

### Authentication Errors
- **Symptom**: HTTP 401 or access denied errors
- **Solution**: Verify access code is correct and hasn't changed

## Best Practices

### When to Download
- **After completing prints**: Immediately after successful prints
- **During idle periods**: When printer is not actively printing
- **Regular backups**: Schedule periodic downloads of important files

### File Management
- **Regular cleanup**: Remove old or unnecessary files to save storage
- **Backup important files**: Keep copies of critical models
- **Monitor storage usage**: Check available disk space regularly

### Performance Tips
- **Download during idle**: Large file downloads work best when printer is idle
- **Batch operations**: Use sync to discover multiple files before downloading
- **Network optimization**: Ensure strong WiFi signal to printer

## Security Considerations

- **Access codes**: Keep printer access codes secure
- **Network security**: Use secure WiFi networks when possible
- **File validation**: Verify downloaded files for integrity
- **Local storage**: Secure local storage location with appropriate permissions

## Integration with Business Workflow

For business users, the file download system integrates with:

- **Job tracking**: Links downloaded files to print job records
- **Cost calculation**: Associates material usage with specific files
- **Client management**: Organizes files by customer projects
- **Archive system**: Maintains historical record of printed items

## API Documentation

For developers integrating with Printernizer's file system, see:
- `/api/v1/files/` - File management endpoints
- `/api/v1/printers/` - Printer status and control
- `/api/v1/jobs/` - Print job tracking and history

---

*Last updated: 2025-09-29*
*Version: 1.0*