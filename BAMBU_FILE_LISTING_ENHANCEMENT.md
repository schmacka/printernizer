# Bambu Lab File Listing Enhancement

## Overview
Enhanced the Bambu Lab printer file listing functionality to provide comprehensive file discovery through multiple methods when the standard `get_files()` API is not available or returns empty results.

## What Was Implemented

### 1. **Enhanced `_list_files_bambu_api()` Method**
The main file listing method now uses a cascading approach with multiple discovery methods:

#### Method 0: Cached Files (Performance Optimization)
- Uses recently cached files (within 30 seconds) to reduce API calls
- Improves response time for repeated requests

#### Method 1: Direct API (`get_files()`)
- Attempts to use the bambulabs_api library's native `get_files()` method
- Falls back gracefully if method is unavailable or fails

#### Method 2: FTP Client Discovery
- Uses the FTP client methods available in bambulabs_api
- Analyzes image directories to infer print files from preview images
- Checks cache directories for temporary files
- Discovers files in multiple directories: `images/`, `cache/`, etc.

#### Method 3: MQTT Dump Analysis
- Analyzes MQTT data dump for file references
- Extracts current print job files
- Looks for task names and file references in status data
- Searches system data for storage/file information

#### Method 4: Uploaded Files Tracking
- Checks for any internal tracking of uploaded files
- Useful for recently uploaded files not yet visible in other methods

### 2. **Enhanced MQTT File Discovery**
Improved the `_list_files_mqtt()` method to:
- Extract file information from live MQTT data
- Find current print job files
- Discover task names and infer file names
- Search system data for file references
- Provide informative logging when no files are found

### 3. **Improved Callbacks and Caching**
Enhanced the `_on_bambu_file_list_update()` callback to:
- Properly parse and store file list updates from the bambulabs_api
- Cache files with timestamps for performance optimization
- Convert raw API data to `PrinterFile` objects
- Handle errors gracefully

### 4. **Helper Methods**
Added two new helper methods:

#### `_discover_files_via_ftp()`
- Leverages FTP client capabilities
- Lists image directories and infers model files
- Checks cache directories for actual files
- Handles various FTP directory structures

#### `_discover_files_via_mqtt_dump()`
- Analyzes MQTT dump data for file references
- Extracts current print job information
- Searches for storage and file system data
- Handles nested data structures safely

### 5. **Better Error Handling and Logging**
- Graceful fallbacks when methods fail
- Informative logging at appropriate levels
- Clear user feedback about what methods are available
- Detailed error messages for troubleshooting

## File Discovery Strategy

The implementation uses a **multi-method approach** because:

1. **Bambu Lab API Limitations**: The bambulabs_api library doesn't always provide direct file listing
2. **Different Storage Locations**: Files can be on SD card, internal storage, or cache
3. **Protocol Variations**: Different API versions have different capabilities
4. **Real-world Reliability**: Multiple fallbacks ensure something usually works

## Key Benefits

### ✅ **Robustness**
- Multiple discovery methods ensure files are found when possible
- Graceful fallbacks prevent complete failures
- Works with various bambulabs_api library versions

### ✅ **Performance**
- Caching reduces redundant API calls
- Fast fallbacks when primary methods fail
- Minimal overhead for unsuccessful attempts

### ✅ **Comprehensive Discovery**
- Finds files in multiple locations (SD card, internal, cache)
- Discovers both active and stored files
- Infers files from preview images and metadata

### ✅ **Maintainability**
- Clear separation of discovery methods
- Comprehensive logging for debugging
- Consistent error handling patterns

## Usage

The enhanced file listing is **fully backward compatible**. Existing code using:

```python
files = await bambu_printer.list_files()
```

Will automatically benefit from all the enhanced discovery methods without any code changes.

## Testing

Created an enhanced test script (`test_file_listing.py`) that:
- Tests all discovery methods individually
- Shows available bambulabs_api capabilities
- Provides detailed diagnostics when files aren't found
- Compares with Prusa implementation as reference

## Expected Results

### When Files Are Available
- Discovers files from any available source
- Returns properly formatted `PrinterFile` objects
- Shows file names, sizes (when available), and paths

### When No Files Found
- Provides informative logging about why no files were found
- Shows what discovery methods were attempted
- Indicates available bambulabs_api capabilities
- Suggests troubleshooting steps

## Compatibility

The implementation:
- ✅ **Maintains backward compatibility**
- ✅ **Works with existing bambulabs_api versions**
- ✅ **Handles missing/unavailable methods gracefully**
- ✅ **Provides informative feedback in all scenarios**

## Next Steps

To further enhance file discovery, consider:
1. **MQTT Command Integration**: Send active file listing commands via MQTT
2. **File Upload Tracking**: Track files as they're uploaded to the printer
3. **Periodic Refresh**: Automatically refresh file lists periodically
4. **SD Card Detection**: Detect when SD cards are inserted/removed