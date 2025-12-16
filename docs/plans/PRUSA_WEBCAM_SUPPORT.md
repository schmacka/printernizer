# Prusa Webcam Support via PrusaLink Camera API

## Overview

Enable webcam preview for Prusa printers on the dashboard by implementing the PrusaLink Camera API endpoints that already exist but aren't currently being used.

**Status**: Planned
**Priority**: Enhancement
**Effort**: Low (single file change)

## Background

Currently, Prusa printers show "No camera available" on the dashboard because the camera methods in `PrusaPrinter` class return `False`/`None`. However, the PrusaLink API actually supports camera endpoints that can auto-detect connected webcams.

### Current State

```python
# src/printers/prusa.py (lines 1025-1041)
async def has_camera(self) -> bool:
    return False  # Always returns False

async def get_camera_stream_url(self) -> Optional[str]:
    return None  # Always returns None

async def take_snapshot(self) -> Optional[bytes]:
    return None  # Always returns None
```

## PrusaLink Camera API

The PrusaLink API has camera endpoints (documented in [OpenAPI spec](https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml)):

| Endpoint | Method | Purpose | Returns |
|----------|--------|---------|---------|
| `/api/v1/cameras` | GET | List available cameras | JSON array of camera configs |
| `/api/v1/cameras/snap` | GET | Snapshot from default camera | PNG binary |
| `/api/v1/cameras/{id}/snap` | GET | Snapshot from specific camera | PNG binary |
| `/api/v1/cameras/{id}/snap` | POST | Trigger new snapshot | PNG binary |

**Note**: These endpoints require a camera to be configured on the Prusa printer (USB webcam, Raspberry Pi camera, etc.).

## Implementation Plan

### File to Modify

**`src/printers/prusa.py`**

### Changes Required

#### 1. Add `_get_cameras()` helper method

```python
async def _get_cameras(self) -> List[dict]:
    """Get list of available cameras from PrusaLink API."""
    if not self.session:
        return []
    try:
        async with self.session.get(f"{self.base_url}/v1/cameras") as response:
            if response.status == 200:
                return await response.json()
    except Exception as e:
        logger.debug("Failed to get cameras", printer_id=self.printer_id, error=str(e))
    return []
```

#### 2. Update `has_camera()` method

```python
async def has_camera(self) -> bool:
    """Check if Prusa printer has camera support via PrusaLink API."""
    try:
        cameras = await self._get_cameras()
        has_cam = len(cameras) > 0
        logger.debug("Prusa camera check", printer_id=self.printer_id, has_camera=has_cam)
        return has_cam
    except Exception as e:
        logger.debug("Camera check failed", printer_id=self.printer_id, error=str(e))
        return False
```

#### 3. Update `take_snapshot()` method

```python
async def take_snapshot(self) -> Optional[bytes]:
    """Take a camera snapshot from Prusa printer via PrusaLink API."""
    if not self.session:
        return None
    try:
        async with self.session.get(f"{self.base_url}/v1/cameras/snap") as response:
            if response.status == 200:
                # PrusaLink returns PNG, may need conversion to JPEG for consistency
                png_data = await response.read()
                logger.debug("Prusa snapshot captured",
                           printer_id=self.printer_id, size=len(png_data))
                return png_data
            elif response.status == 204:
                logger.debug("No camera image available", printer_id=self.printer_id)
            elif response.status == 404:
                logger.debug("No camera configured", printer_id=self.printer_id)
    except Exception as e:
        logger.error("Failed to capture Prusa snapshot",
                    printer_id=self.printer_id, error=str(e))
    return None
```

#### 4. Update `get_camera_stream_url()` method

```python
async def get_camera_stream_url(self) -> Optional[str]:
    """Get camera stream URL for Prusa printer."""
    if await self.has_camera():
        # Return the preview endpoint URL (snapshot-based, not true streaming)
        return f"/api/v1/printers/{self.printer_id}/camera/preview"
    return None
```

### Additional Considerations

#### PNG vs JPEG Format

PrusaLink returns **PNG** images while Bambu Lab returns **JPEG**. Options:

1. **Accept both formats** - Update `CameraSnapshotService` and camera router to handle both content types
2. **Convert PNG to JPEG** - Add conversion in `take_snapshot()` for consistency:

```python
from PIL import Image
import io

# Convert PNG to JPEG
png_data = await response.read()
img = Image.open(io.BytesIO(png_data))
jpeg_buffer = io.BytesIO()
img.convert('RGB').save(jpeg_buffer, format='JPEG', quality=85)
return jpeg_buffer.getvalue()
```

Recommendation: Accept both formats (option 1) to preserve image quality and reduce processing overhead.

## Testing

### Prerequisites
- Prusa Core One printer with PrusaLink enabled
- Webcam configured on the printer (USB webcam or Pi camera)

### Test Cases

1. **Auto-detection**: Verify `has_camera()` returns `True` when camera is configured
2. **No camera**: Verify `has_camera()` returns `False` when no camera is configured
3. **Snapshot capture**: Verify `take_snapshot()` returns valid PNG data
4. **Dashboard display**: Verify camera preview appears on printer tile
5. **Error handling**: Verify graceful fallback when printer is offline

## Frontend Changes

**None required.** The existing frontend already handles camera previews via:
- `CameraManager` class in `frontend/js/camera.js`
- Camera API endpoints in `src/api/routers/camera.py`
- `CameraSnapshotService` for caching (5-second TTL)

## Related Files

| File | Role |
|------|------|
| `src/printers/prusa.py` | Prusa printer implementation (to be modified) |
| `src/printers/base.py` | Base printer interface with camera abstract methods |
| `src/printers/bambu_lab.py` | Reference implementation for Bambu Lab cameras |
| `src/services/camera_snapshot_service.py` | Camera snapshot caching service |
| `src/api/routers/camera.py` | Camera API endpoints |
| `frontend/js/camera.js` | Frontend camera management |

## References

- [PrusaLink OpenAPI Specification](https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml)
- [Prusa Connect Camera API Documentation](https://help.prusa3d.com/article/prusa-connect-camera-api_569012)
- [Camera Setup for PrusaLink](https://help.prusa3d.com/guide/camera-setup-for-prusalink-prusa-connect_470943)
