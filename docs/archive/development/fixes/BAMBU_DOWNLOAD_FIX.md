# Bambu Lab File Download Fix

## Issue Summary

The Bambu Lab file download functionality in Printernizer was not working due to incorrect usage of the `bambulabs-api` library's FTP client methods.

## Root Cause

The implementation in `src/printers/bambu_lab.py` was incorrectly calling the FTP download method expecting a tuple return value:

```python
# INCORRECT (old code):
success, file_data = ftp.download_file(remote_path)
```

However, according to the `bambulabs-api` library documentation and source code, the `download_file()` method actually returns a `BytesIO` object directly:

```python
def download_file(self, file_path: str, blocksize: int = 524288) -> BytesIO:
    """Download file and return BytesIO object."""
```

## Fix Applied

The `_download_via_ftp()` method in `src/printers/bambu_lab.py` was corrected to:

```python
# CORRECT (new code):
file_data_io = ftp.download_file(remote_path)
file_data = file_data_io.getvalue()  # Extract bytes from BytesIO
```

## Key Changes

1. **Fixed FTP download call**: Use correct return type (`BytesIO` instead of tuple)
2. **Extract bytes properly**: Call `.getvalue()` on the returned `BytesIO` object
3. **Improved error handling**: Better handling of empty responses
4. **Updated path priority**: Prioritize `cache/` directory (most common location)

## Technical Details

### Bambu Lab FTP Structure

The `bambulabs-api` library provides access to files via FTP in these directories:
- `cache/` - Most 3D print files (.3mf, .gcode, .bgcode)
- `images/` - Preview images and thumbnails  
- `timelapse/` - Timelapse videos
- `logger/` - Log files

### FTP Methods Available

- `list_cache_dir()` → `(status, file_list)` - List files in cache
- `download_file(path)` → `BytesIO` - Download file content
- `list_images_dir()` → `(status, file_list)` - List preview images

## Verification

The fix has been verified to:
1. ✅ Correctly handle `BytesIO` return values
2. ✅ Extract file data properly using `.getvalue()`
3. ✅ Maintain compatibility with existing code
4. ✅ Pass all existing unit tests
5. ✅ Handle error conditions gracefully

## Impact

**Before**: File downloads from Bambu Lab printers would fail with type errors or incorrect data handling.

**After**: File downloads should work correctly, allowing users to download 3MF, G-code, and other files from their Bambu Lab printers' internal storage.

## Testing

To test the fix with a real printer:
1. Ensure printer is connected and has files in cache
2. Use the file management interface to browse printer files
3. Click download on any available file
4. Verify the file downloads successfully to local storage

## Notes

- The fix maintains backward compatibility
- File listing functionality was already correct and unchanged
- HTTP download fallback remains available for cases where FTP fails
- The `@connect_and_run` decorator in the FTP client handles connection management automatically