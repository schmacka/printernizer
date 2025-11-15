# Prusa BGCode Download Bug Investigation

**Status:** 🔴 INCOMPLETE - Requires Further Research
**Branch:** `fix/prusa-bgcode-download`
**Date:** 2025-10-01
**Version:** 1.1.4

## Problem Summary

When downloading `.bgcode` files from Prusa Core One printer, the system saves **JSON metadata** instead of the actual binary file content. This causes:

1. ❌ No thumbnail display (file is JSON, not BGCode binary)
2. ❌ BGCode parser fails with "Invalid BGCode magic bytes: 7b226e61" (which is `{"na` - JSON!)
3. ❌ Users see empty previews for downloaded files
4. ❌ Cannot process file for print analysis

### Example

File: `[USB] P VAPE large .bgcode`
- Expected: Binary BGCode file (~4.2MB)
- Actual: JSON metadata (638 bytes)

```json
{
  "name": "PVAPEL~1.BGC",
  "ro": false,
  "type": "PRINT_FILE",
  "m_timestamp": 1757141056,
  "size": 4181758,
  "refs": {
    "icon": "/thumb/s/usb/PVAPEL~1.BGC",
    "thumbnail": "/thumb/l/usb/PVAPEL~1.BGC",
    "download": "/usb/PVAPEL~1.BGC"
  },
  "display_name": "P VAPE large .bgcode"
}
```

## Root Cause Analysis

### Discovery Process

1. **Initial Symptom:** No thumbnail for downloaded BGCode file
2. **Investigation:** File content examination revealed JSON instead of binary
3. **URL Construction:** Download URL was incorrectly constructed from Prusa API response

### PrusaLink API Confusion

The Prusa PrusaLink API returns file metadata with a `refs.download` field:

```json
"refs": {
  "resource": "/api/files/usb/PVAPEL~1.BGC",
  "download": "usb/PVAPEL~1.BGC"  // or "/usb/PVAPEL~1.BGC"
}
```

**Attempted URL Constructions:**

| URL Format | Result | Notes |
|------------|--------|-------|
| `http://IP/api/v1/files/usb/FILE` | ❌ Returns JSON metadata | This is the file info endpoint |
| `http://IP/usb/FILE` | ❌ 401 Unauthorized | Direct path fails even with API key header |
| `http://IP/api/files/usb/FILE` | ❌ Returns JSON metadata | Alternative API endpoint format |

### Key Findings

1. **API Endpoint vs Binary Download:** The `/api/v1/files/` endpoint is for metadata queries, not binary downloads
2. **Authentication Issue:** Direct paths (`/usb/FILE`) return 401 even with `X-Api-Key` header
3. **Inconsistent Refs:** The `download` ref sometimes has a leading slash, sometimes doesn't
4. **Missing Documentation:** PrusaLink binary download endpoint not clearly documented

## Changes Implemented

### 1. Download Validation ([src/printers/prusa.py:559-579](../src/printers/prusa.py#L559-L579))

Added validation to detect when JSON metadata is downloaded instead of binary:

```python
# Read first chunk to validate content type
first_chunk = None
chunks = []

async for chunk in response.content.iter_chunked(8192):
    if first_chunk is None:
        first_chunk = chunk
        # Validate that this is not JSON metadata
        if chunk.startswith(b'{') or chunk.startswith(b'['):
            logger.error("Downloaded JSON metadata instead of binary file",
                       content_preview=chunk[:200].decode('utf-8', errors='ignore'))
            return False
```

**Benefits:**
- Immediately detects incorrect downloads
- Logs JSON preview for debugging
- Prevents corrupted files from being saved

### 2. Prusa Thumbnail API ([src/printers/prusa.py:656-722](../src/printers/prusa.py#L656-L722))

New method to download thumbnails directly from Prusa printer:

```python
async def download_thumbnail(self, filename: str, size: str = 'l') -> Optional[bytes]:
    """
    Download thumbnail for a file from Prusa printer.

    Args:
        filename: Display name of the file
        size: Thumbnail size - 's' (small/icon) or 'l' (large/thumbnail)

    Returns:
        PNG thumbnail data as bytes, or None if not available
    """
```

**Features:**
- Fetches thumbnails from `/thumb/s/usb/FILE` or `/thumb/l/usb/FILE`
- Extracts PNG dimensions from header
- Returns raw PNG bytes for storage

### 3. Thumbnail Fallback System ([src/services/file_service.py:758-824](../src/services/file_service.py#L758-L824))

Integrated multi-tier thumbnail approach:

1. **First:** Try to extract embedded thumbnail from BGCode
2. **Second:** If no embedded thumbnail, try Prusa API
3. **Third:** If Prusa API fails, generate preview rendering
4. **Fourth:** If all fail, mark as no thumbnail

```python
elif parse_result.get('needs_generation', False):
    # Try Prusa API first
    if file_id.startswith('59dd18ca-b8c3-4a69-b00d-1931257ecbce'):
        prusa_thumb_bytes = await printer_instance.download_thumbnail(filename, size='l')
        if prusa_thumb_bytes:
            thumbnail_source = 'printer'

    # Fall back to generation
    if not thumbnail_data:
        preview_bytes = await self.preview_render_service.get_or_generate_preview(...)
        thumbnail_source = 'generated'
```

### 4. Enhanced Logging

Added comprehensive debug logging:
- Raw file_info dump from Prusa API
- Download reference extraction
- URL construction steps
- HTTP response details
- Content type validation results

## What Still Needs Investigation

### 1. Correct Download Endpoint

**Question:** What is the proper PrusaLink endpoint for downloading binary files?

**Candidates to test:**
- Query parameter: `/api/v1/files/usb/FILE?download=1`
- Different endpoint: `/download/usb/FILE`
- Different API version: `/api/files/usb/FILE/raw`
- Token-based URL: `/usb/FILE?token=...`

### 2. Authentication Method

**Question:** Does binary download require different authentication than API calls?

**Possibilities:**
- Digest authentication instead of API key
- Session cookie from initial auth
- Token appended to URL
- Different header format

### 3. Network Traffic Analysis

**Recommended:** Capture network traffic when PrusaLink Web UI downloads a file to see:
- Actual HTTP request format
- Headers used
- URL structure
- Authentication method

### 4. OpenAPI Specification

**Action:** Review complete PrusaLink OpenAPI spec at:
https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml

Look for:
- File download operations
- Authentication requirements
- Binary response endpoints

## Testing Recommendations

### Manual Testing

1. **Direct curl test:**
   ```bash
   curl -v -H "X-Api-Key: YOUR_KEY" \
        "http://PRINTER_IP/usb/FILENAME.bgcode" \
        -o test.bgcode
   ```

2. **Check actual file content:**
   ```bash
   xxd -l 32 test.bgcode
   ```
   Should show BGCode magic bytes, not JSON

3. **Test different auth methods:**
   ```bash
   # API key in URL
   curl "http://PRINTER_IP/usb/FILE?api_key=KEY"

   # Basic auth
   curl -u "apikey:KEY" "http://PRINTER_IP/usb/FILE"

   # Digest auth
   curl --digest -u "user:pass" "http://PRINTER_IP/usb/FILE"
   ```

### Automated Testing

1. Compare file sizes: Downloaded file should match `size` field in metadata
2. Verify file format: Should start with BGCode magic bytes
3. Test thumbnail extraction: Should find embedded PNG images

## Workarounds

### For Users

**Current workaround:** Manually copy files from Prusa printer's USB drive via:
1. PrusaLink Web UI file download button
2. Physical USB drive removal
3. Network file share (if configured)

### For Developers

**Testing workaround:** Use files already on disk:
```python
# Skip download, directly process existing file
file_path = "path/to/local/file.bgcode"
await file_service.process_file_thumbnails(file_path, file_id)
```

## Related Issues

- BGCode parser expects binary format with magic bytes `BGD\x00`
- Thumbnail extraction requires valid BGCode file structure
- Preview generation can work as fallback but requires 3D model parsing

## References

- [PrusaLink GitHub Repository](https://github.com/prusa3d/Prusa-Link)
- [PrusaLink Web OpenAPI Spec](https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml)
- [PrusaLink API Forum Discussion](https://forum.prusa3d.com/forum/hardware-firmware-and-software-help/prusalink-api-endpoints/)

## Next Steps

1. **Priority 1:** Research correct PrusaLink binary download endpoint
   - Review OpenAPI specification
   - Capture network traffic from Web UI
   - Test alternative URL formats

2. **Priority 2:** Implement working download solution
   - Update URL construction in [src/printers/prusa.py](../src/printers/prusa.py)
   - Add integration tests
   - Verify binary content validation

3. **Priority 3:** Test thumbnail system end-to-end
   - Download file successfully
   - Extract or fetch thumbnail
   - Display in UI

4. **Priority 4:** Document final solution
   - Update this file with working approach
   - Add code comments
   - Create user documentation

## Contact & Discussion

For questions or progress updates, see:
- Git branch: `fix/prusa-bgcode-download`
- Related commits: Search for "prusa download" or "bgcode"
- Issue tracking: Add to `todo2.md` if needed
