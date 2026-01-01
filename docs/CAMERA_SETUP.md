# Camera Setup and Troubleshooting Guide

This guide helps you set up and troubleshoot camera functionality in Printernizer for both Prusa Core One and Bambu Lab printers.

## Supported Printers

### Prusa Core One
- **Camera Type**: USB webcam via PrusaLink
- **Protocol**: HTTP REST API (`/api/v1/cameras`)
- **Image Format**: PNG
- **Requirements**:
  - PrusaLink firmware 2.1.2 or higher
  - USB camera connected to printer
  - Camera configured in PrusaLink settings

### Bambu Lab (A1, P1 Series)
- **Camera Type**: Built-in camera
- **Protocol**: TCP/TLS (port 6000)
- **Image Format**: JPEG
- **Requirements**:
  - Printer connected to network
  - Access code configured

## Quick Start

### For Prusa Core One

1. **Connect the Camera**
   - Plug a compatible USB webcam into your Prusa Core One
   - Ensure the camera is recognized by the printer

2. **Configure in PrusaLink**
   - Access PrusaLink web interface: `http://<printer-ip>`
   - Navigate to **Settings** → **Camera**
   - Enable camera support
   - Test the camera using PrusaLink's built-in viewer
   - Save settings and restart if prompted

3. **Verify in Printernizer**
   - Navigate to your printer card in Printernizer
   - The camera section should appear automatically
   - You'll see a live preview (updates every 30 seconds)
   - Click "Snapshot" to capture images
   - Click "Vollbild" (Fullscreen) for larger view

### For Bambu Lab

1. **Ensure Network Connection**
   - Printer must be connected to your local network
   - Note the IP address and access code

2. **Add Printer in Printernizer**
   - Camera is automatically detected
   - No additional configuration needed

## Troubleshooting

### Camera Not Appearing in Printernizer

**Use the Diagnostic Tool:**

```bash
# Replace {printer_id} with your printer's UUID
curl http://localhost:8000/api/v1/printers/{printer_id}/camera/diagnostics
```

Or visit in your browser:
```
http://localhost:8000/api/v1/printers/{printer_id}/camera/diagnostics
```

This will run 4 tests:
1. **Camera Support** - Verifies printer type supports cameras
2. **Camera Detected** - Checks if PrusaLink/printer reports a camera
3. **Stream URL** - Tests if preview endpoint is available
4. **Snapshot Capture** - Attempts to capture a test image

The diagnostics will provide specific recommendations based on which tests fail.

### Common Issues

#### Issue: "No camera detected by PrusaLink"

**Solution:**
1. Verify camera is physically connected to printer USB port
2. Access PrusaLink web interface: `http://<printer-ip>`
3. Go to **Settings** → **Camera**
4. Enable camera and configure resolution/format
5. Test camera in PrusaLink first before using Printernizer
6. Restart PrusaLink service or reboot printer
7. Check PrusaLink version: `curl http://<printer-ip>/api/version`
   - Minimum version: 2.1.2

#### Issue: "Camera detected but snapshot capture failed"

**Solution:**
1. Test camera directly in PrusaLink web interface
2. Check camera permissions in PrusaLink
3. Review PrusaLink logs for camera errors:
   ```bash
   # SSH into printer (if accessible)
   journalctl -u prusalink -f
   ```
4. Try a different USB port
5. Try a different camera (if available)
6. Check camera compatibility with Raspberry Pi (if using Pi-based printer)

#### Issue: "Image shows but is very slow to update"

**Explanation:**
- Prusa cameras use polling-based preview (not live streaming)
- Default refresh interval: 30 seconds
- This is intentional to reduce load on printer

**Options:**
- Click "🔄 Aktualisieren" to manually refresh
- Full-screen view also auto-refreshes every 30 seconds

#### Issue: "Camera works in PrusaLink but not in Printernizer"

**Solution:**
1. Check Printernizer logs:
   ```bash
   docker logs printernizer  # If using Docker
   # or
   tail -f logs/printernizer.log  # If using direct Python
   ```
2. Verify API key has camera permissions in PrusaLink
3. Test API endpoint directly:
   ```bash
   curl -H "X-Api-Key: YOUR_API_KEY" http://<printer-ip>/api/v1/cameras
   ```
4. Restart Printernizer service
5. Check browser console (F12) for JavaScript errors

### Testing Camera API Directly

#### Check Camera List (Prusa)
```bash
curl -H "X-Api-Key: YOUR_API_KEY" \
  http://<printer-ip>/api/v1/cameras
```

Expected response:
```json
[
  {
    "id": "camera_id",
    "name": "PrusaLink Camera",
    "resolution": "1280x720"
  }
]
```

#### Capture Test Snapshot (Prusa)
```bash
curl -H "X-Api-Key: YOUR_API_KEY" \
  http://<printer-ip>/api/v1/cameras/snap \
  --output test_snapshot.png
```

#### Check Camera in Printernizer
```bash
# Get camera status
curl http://localhost:8000/api/v1/printers/{printer_id}/camera/status

# Get camera preview
curl http://localhost:8000/api/v1/printers/{printer_id}/camera/preview \
  --output preview.png

# Run diagnostics
curl http://localhost:8000/api/v1/printers/{printer_id}/camera/diagnostics
```

## Camera Features in Printernizer

### Preview Mode
- **Auto-refresh**: Updates every 30 seconds
- **Manual refresh**: Click "🔄 Aktualisieren" button
- **Full-screen view**: Click "🔍 Vollbild" button
- **Cached images**: 5-second cache to reduce printer load

### Snapshot Capture
- **Manual snapshots**: Click "📸 Snapshot" button
- **Automatic snapshots**: Triggered by job events (optional)
- **Storage**: Saved to `data/snapshots/` directory
- **Database**: Tracked in `snapshots` table
- **History**: View all snapshots in "🖼️ Snapshot-Historie"

### Snapshot Triggers
- `manual` - Manually captured by user
- `auto` - Automatically captured by system
- `job_start` - Captured when print job starts
- `job_complete` - Captured when print job completes
- `job_failed` - Captured when print job fails

## API Endpoints

### Camera Status
```
GET /api/v1/printers/{printer_id}/camera/status
```

Returns:
```json
{
  "has_camera": true,
  "is_available": true,
  "stream_url": "/api/v1/printers/{printer_id}/camera/preview",
  "error_message": null
}
```

### Camera Diagnostics (NEW)
```
GET /api/v1/printers/{printer_id}/camera/diagnostics
```

Returns detailed test results and troubleshooting recommendations.

### Camera Preview
```
GET /api/v1/printers/{printer_id}/camera/preview
```

Returns PNG or JPEG image data.

### Take Snapshot
```
POST /api/v1/printers/{printer_id}/camera/snapshot
```

Body:
```json
{
  "job_id": "optional-job-id",
  "capture_trigger": "manual",
  "notes": "Optional notes"
}
```

### List Snapshots
```
GET /api/v1/printers/{printer_id}/snapshots?limit=50&offset=0
```

### Download Snapshot
```
GET /api/v1/snapshots/{snapshot_id}/download
```

## Known Limitations

### Prusa Core One
- **No live streaming**: Uses polling-based preview
- **30-second refresh**: Intentional to reduce load
- **Single camera**: Only one camera per printer supported
- **USB cameras only**: Network cameras not supported
- **PrusaLink dependency**: Requires PrusaLink firmware with camera support

### Bambu Lab
- **Proprietary protocol**: Uses bambulabs-api library
- **JPEG only**: PNG not supported
- **No RTSP streaming**: Uses snapshot-based preview

## Browser Compatibility

Tested browsers:
- ✅ Chrome/Chromium 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Performance Tips

1. **Reduce Preview Frequency**: 30-second default is optimal
2. **Close Modals**: Close full-screen view when not in use
3. **Limit Concurrent Previews**: Don't open multiple printers simultaneously
4. **Use Snapshots**: Capture important moments instead of continuous monitoring
5. **Cache Headers**: Browser caches preview images for 5 seconds

## Getting Help

If you're still experiencing issues:

1. **Run diagnostics endpoint** and share output
2. **Check Printernizer logs** for error messages
3. **Test camera in PrusaLink** directly to isolate issue
4. **Verify PrusaLink version** meets minimum requirements
5. **Open GitHub issue** with:
   - Diagnostic output
   - PrusaLink version
   - Camera model
   - Error logs

## See Also

- [PrusaLink API Documentation](https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml)
- [PrusaLink Camera Setup Guide](https://help.prusa3d.com/article/prusalink-and-prusa-connect_428132)
- [Bambu Lab API Documentation](https://github.com/Doridian/OpenBambuAPI)
