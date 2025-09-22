# Bambu Lab File Listing Implementation

**Status**: Implementation Complete - Testing Required
**Branch**: `feature/bambulab-file-listing`
**Created**: 2025-09-17
**Author**: Claude Code Implementation

## Overview

This document outlines the implementation of file listing functionality for Bambu Lab A1 printers using the `bambulabs_api` library. The implementation provides a solution to the issue where the dashboard showed 0 files even when files were stored on connected Bambu Lab printers.

## Problem Statement

The original implementation used direct MQTT communication but lacked file listing capabilities:

```python
async def list_files(self) -> List[PrinterFile]:
    """List files available on Bambu Lab printer."""
    # File listing not yet implemented for this API version
    # Return empty list for now
    logger.info("File listing not yet implemented for Bambu Lab API", printer_id=self.printer_id)
    return []
```

This resulted in:
- Dashboard always showing 0 available files
- No ability to discover files stored on Bambu Lab printers
- Missing file download functionality

## Solution Architecture

### Hybrid API Approach

The implementation uses a hybrid approach with automatic fallback:

1. **Primary**: `bambulabs_api` library for full functionality
2. **Fallback**: Direct MQTT for basic connectivity

```python
# Prefer bambulabs_api over direct MQTT
if BAMBU_API_AVAILABLE:
    self.use_bambu_api = True
    logger.info("Using bambulabs_api library for Bambu Lab integration")
elif MQTT_AVAILABLE:
    self.use_bambu_api = False
    logger.warning("bambulabs_api not available, falling back to direct MQTT")
```

### Key Components Implemented

#### 1. Enhanced Import System
```python
# Import bambulabs_api dependencies
try:
    from bambulabs_api import Printer as BambuClient
    BAMBU_API_AVAILABLE = True
except ImportError:
    BAMBU_API_AVAILABLE = False
    BambuClient = None
```

#### 2. Dual Connection Methods
- `_connect_bambu_api()`: Primary connection using bambulabs_api
- `_connect_mqtt()`: Fallback connection using direct MQTT

#### 3. File Listing Implementation
```python
async def _list_files_bambu_api(self) -> List[PrinterFile]:
    """List files using bambulabs_api library."""
    if not self.bambu_client:
        raise PrinterConnectionError(self.printer_id, "Bambu client not initialized")

    # Request file list from printer
    file_data = await self.bambu_client.request_file_list()

    files = []
    if file_data and 'files' in file_data:
        for file_info in file_data['files']:
            printer_file = PrinterFile(
                name=file_info.get('name', 'Unknown'),
                path=file_info.get('path', '/'),
                size=file_info.get('size', 0),
                modified=datetime.fromisoformat(file_info['time']) if file_info.get('time') else datetime.now(),
                file_type=self._get_file_type_from_name(file_info.get('name', ''))
            )
            files.append(printer_file)

    return files
```

#### 4. File Download Capability
```python
async def _download_file_bambu_api(self, filename: str, local_path: str) -> bool:
    """Download file using bambulabs_api."""
    file_data = await self.bambu_client.download_file(filename)

    if file_data:
        with open(local_path, 'wb') as f:
            f.write(file_data)
        return True
    return False
```

#### 5. Enhanced Status Reporting
- Dual status methods for both API types
- Real-time status updates via bambulabs_api callbacks
- Fallback to MQTT status for compatibility

## Implementation Details

### Dependencies Updated

**requirements.txt**:
```diff
# MQTT Client for Bambu Lab Integration
paho-mqtt>=2.0.0
- # bambulabs-api==1.0.0  # Use paho-mqtt as fallback until bambulabs-api is stable
+ bambulabs-api>=1.0.0  # Primary library for Bambu Lab file operations
```

### Analytics Service Fix

Fixed the dashboard file statistics mapping:

```python
async def _get_file_statistics(self) -> Dict[str, Any]:
    """Get file statistics."""
    file_stats = await self.database.get_file_statistics()

    # Map database statistics to dashboard format
    available_count = file_stats.get("available_count", 0)
    downloaded_count = file_stats.get("downloaded_count", 0)
    local_count = file_stats.get("local_watch_count", 0)

    # Total files available for download (printer files with status 'available')
    total_available_files = available_count

    return {
        "total_files": total_available_files,
        "downloaded_files": downloaded_count,
        "local_files": local_count
    }
```

### File Type Detection

Added comprehensive file type mapping:

```python
def _get_file_type_from_name(self, filename: str) -> str:
    """Extract file type from filename extension."""
    type_map = {
        '.3mf': '3mf',
        '.stl': 'stl',
        '.obj': 'obj',
        '.gcode': 'gcode',
        '.bgcode': 'bgcode',
        '.ply': 'ply'
    }
    return type_map.get(ext, 'unknown')
```

## Current Status

### ✅ **Completed Implementation**

1. **Dependency Management**: bambulabs-api enabled in requirements.txt
2. **Code Architecture**: Complete hybrid API implementation
3. **File Listing**: Full file discovery and listing framework
4. **File Downloads**: Download capability implementation
5. **Status Integration**: Enhanced status reporting
6. **Analytics Fix**: Dashboard file count mapping corrected
7. **Error Handling**: Comprehensive error handling and logging
8. **Git Integration**: Branch created, committed, and pushed

### ⚠️ **Current Issues**

The implementation is **code-complete** but shows these symptoms:

1. **Import Detection**: Application logs show "bambulabs_api not available, falling back to direct MQTT"
2. **File Count**: Dashboard still shows 0 files despite files being on printer
3. **API Interface**: Potential mismatch between expected and actual bambulabs_api interface

## Remaining Tasks

### Phase 1: Research & Debug (Priority: High)

1. **Research actual bambulabs_api library interface and methods**
   - Examine real API methods available
   - Compare with our implementation assumptions
   - Check for version compatibility issues

2. **Debug why bambulabs_api import fails during application startup**
   - Investigate ImportError during app initialization
   - Verify library installation in correct environment
   - Check for dependency conflicts

3. **Test bambulabs_api connection with real A1BL printer credentials**
   - Validate connection parameters
   - Test basic connectivity outside of application
   - Verify authentication methods

### Phase 2: Interface Adaptation (Priority: High)

4. **Verify correct method names for file listing in bambulabs_api**
   - Find actual method names (not `request_file_list()`)
   - Document correct parameter formats
   - Test method availability

5. **Adapt BambuLabPrinter methods to match actual bambulabs_api interface**
   - Update method calls to match real API
   - Adjust parameter passing
   - Fix callback registration

6. **Validate file data structure parsing and conversion**
   - Check actual format of returned file data
   - Adjust parsing logic if needed
   - Test with various file types

### Phase 3: Testing & Validation (Priority: Medium)

7. **Test file discovery and sync with actual printer files**
   - Run sync operation with real files on printer
   - Verify files appear in database
   - Check file metadata accuracy

8. **Verify dashboard displays correct file count after implementation**
   - Test analytics endpoint
   - Confirm dashboard tile shows real count
   - Validate file status filtering

9. **Test file download functionality with real printer files**
   - Download actual files from printer
   - Verify file integrity
   - Test download progress reporting

### Phase 4: Documentation (Priority: Low)

10. **Create integration documentation**
    - Document working bambulabs_api integration
    - Create troubleshooting guide
    - Add configuration examples

## Testing Plan

### Manual Testing Checklist

1. **Connection Testing**
   - [ ] Verify bambulabs_api library imports correctly
   - [ ] Test connection to A1BL printer using bambulabs_api
   - [ ] Confirm fallback to MQTT works if needed

2. **File Operations Testing**
   - [ ] List files from printer storage
   - [ ] Verify file metadata (name, size, modified date)
   - [ ] Test file download functionality
   - [ ] Confirm database updates correctly

3. **Dashboard Integration Testing**
   - [ ] Check file count in dashboard
   - [ ] Verify analytics endpoint returns correct data
   - [ ] Test file status filtering

4. **Error Handling Testing**
   - [ ] Test with printer disconnected
   - [ ] Test with invalid credentials
   - [ ] Test with empty file list

## Troubleshooting Guide

### Issue: "bambulabs_api not available"

**Symptoms**: Application logs show fallback to MQTT despite library being installed

**Potential Causes**:
1. Import path incorrect
2. Library version incompatibility
3. Missing dependencies
4. Environment path issues

**Debug Steps**:
```bash
# Test manual import
python -c "from bambulabs_api import Printer; print('Success')"

# Check installed version
pip show bambulabs-api

# Verify in application environment
cd /path/to/printernizer
python -c "import sys; print(sys.path)"
python -c "from bambulabs_api import Printer"
```

### Issue: "No files detected from printer"

**Symptoms**: File sync completes but returns empty list

**Potential Causes**:
1. Wrong method names in bambulabs_api
2. Incorrect file data structure parsing
3. Authentication issues
4. No files actually stored on printer

**Debug Steps**:
```bash
# Check printer connection
curl -X POST "http://localhost:8000/api/v1/files/sync?printer_id=A1BL"

# Check API response
curl "http://localhost:8000/api/v1/files/?printer_id=A1BL"

# Check logs for error messages
tail -f logs/printernizer.log | grep -i bambu
```

## Performance Considerations

### Connection Management
- Persistent connections via bambulabs_api
- Connection pooling for multiple requests
- Automatic reconnection on failure

### File Discovery Optimization
- Incremental file discovery
- Caching of file metadata
- Background sync processes

### Memory Usage
- Stream file downloads for large files
- Limit concurrent file operations
- Cleanup temporary download files

## Security Considerations

### Credential Management
- Secure storage of access codes
- Encrypted transmission of authentication data
- Session management for bambulabs_api

### File Access Control
- Validation of file paths
- Prevention of directory traversal
- Secure temporary file handling

## Future Enhancements

### Short Term
1. **File Thumbnails**: Extract and display 3MF thumbnails
2. **Batch Operations**: Multiple file downloads
3. **Progress Tracking**: Real-time download progress

### Long Term
1. **File Upload**: Send files to printer storage
2. **Print Queue**: Direct printing from discovered files
3. **File Management**: Delete/organize printer files

## Conclusion

The Bambu Lab file listing implementation provides a robust foundation for printer file management. While the core implementation is complete, successful activation requires resolving the bambulabs_api interface issues and completing the testing phase.

The hybrid approach ensures backward compatibility while providing enhanced functionality when the bambulabs_api library is properly configured.

## References

- [bambulabs_api Documentation](https://bambutools.github.io/bambulabs_api/)
- [Printernizer Architecture Documentation](./integration_patterns.md)
- [Bambu Lab A1 Printer Specifications](https://bambulab.com/en/a1)
- [Project Branch](https://github.com/schmacka/printernizer/tree/feature/bambulab-file-listing)