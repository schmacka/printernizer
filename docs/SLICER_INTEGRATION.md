# Slicer Integration Feature

## Overview

The Slicer Integration feature enables Printernizer to slice 3D model files (STL, 3MF, OBJ) directly using **PrusaSlicer** and **BambuStudio** command-line interfaces. This eliminates the need to leave the application for slicing operations.

## Features

### ✅ Implemented

- **Cross-Platform Slicer Detection**: Automatically detects PrusaSlicer, BambuStudio, OrcaSlicer, and SuperSlicer on Windows, Linux, and macOS
- **Profile Management**: Import and manage slicer profiles from existing installations
- **Job Queue System**: FIFO queue with priority support and concurrent job execution
- **Progress Tracking**: Real-time progress updates via WebSocket events
- **Auto-Upload**: Automatically upload sliced G-code to selected printer
- **Auto-Start**: Optionally start print job immediately after upload
- **Retry Logic**: Automatic retry on failure with configurable attempts
- **Persistent Queue**: Job queue persists across application restarts

### 🚧 Pending (Frontend Integration)

- Web UI for slicer management
- Job queue dashboard
- Progress indicators
- Library integration (slice from library page)

## Architecture

### Database Schema

Three new tables added via migration `022_slicer_integration.sql`:

1. **slicer_configs**: Stores detected slicer installations
2. **slicer_profiles**: Stores imported slicer profiles
3. **slicing_jobs**: Tracks slicing operations and progress

### Services

#### SlicerDetector
- Detects slicer installations on the system
- Extracts version information
- Validates slicer executables
- **Location**: `src/services/slicer_detector.py`

#### SlicerService
- Manages slicer configurations
- Imports and manages profiles
- Verifies slicer availability
- **Location**: `src/services/slicer_service.py`

#### SlicingQueue
- Manages job queue (FIFO with priority)
- Executes slicing commands via subprocess
- Tracks progress and sends WebSocket updates
- Handles auto-upload and auto-start
- **Location**: `src/services/slicing_queue.py`

### API Endpoints

Base path: `/api/v1/slicing`

#### Slicer Management
- `GET /` - List all registered slicers
- `POST /detect` - Trigger slicer detection
- `GET /{slicer_id}` - Get slicer configuration
- `DELETE /{slicer_id}` - Delete slicer configuration

#### Profile Management
- `GET /{slicer_id}/profiles` - List profiles for slicer
- `POST /{slicer_id}/profiles/import` - Import profiles from config directory
- `GET /profiles/{profile_id}` - Get profile details
- `DELETE /profiles/{profile_id}` - Delete profile

#### Slicing Operations
- `POST /jobs` - Create slicing job
- `GET /jobs` - List slicing jobs
- `GET /jobs/{job_id}` - Get job status
- `POST /jobs/{job_id}/cancel` - Cancel job
- `DELETE /jobs/{job_id}` - Delete job

#### Quick Actions
- `POST /library/{checksum}/slice` - Slice library file
- `POST /slice-and-print` - Slice + upload + print in one operation

## Configuration

### Environment Variables

```bash
# Enable/disable slicing feature
SLICING_ENABLED=true

# Maximum concurrent slicing jobs
SLICING_MAX_CONCURRENT=2

# Output directory for sliced G-code
SLICING_OUTPUT_DIR=/data/printernizer/sliced

# Cleanup old files after N days
SLICING_CLEANUP_DAYS=7

# Auto-retry failed jobs
SLICING_AUTO_RETRY=true
SLICING_MAX_RETRIES=3

# Job timeout in seconds
SLICING_TIMEOUT_SECONDS=3600

# Auto-detect slicers on startup
SLICING_AUTO_DETECT=true
```

### Database Configuration

Settings stored in `configuration` table with `slicing.*` keys:

- `slicing.enabled`
- `slicing.max_concurrent`
- `slicing.output_dir`
- `slicing.cleanup_days`
- `slicing.auto_retry`
- `slicing.max_retries`
- `slicing.timeout_seconds`
- `slicing.auto_detect`

## Usage Examples

### 1. Detect Slicers

```bash
POST /api/v1/slicing/detect
```

Response:
```json
{
  "detected": [
    {
      "id": "uuid",
      "name": "PrusaSlicer",
      "slicer_type": "prusaslicer",
      "executable_path": "/usr/bin/prusa-slicer",
      "version": "2.7.0",
      "config_dir": "/home/user/.config/PrusaSlicer",
      "is_available": true
    }
  ],
  "count": 1
}
```

### 2. Import Profiles

```bash
POST /api/v1/slicing/{slicer_id}/profiles/import
```

### 3. Create Slicing Job

```bash
POST /api/v1/slicing/jobs
Content-Type: application/json

{
  "file_checksum": "abc123...",
  "slicer_id": "uuid",
  "profile_id": "uuid",
  "target_printer_id": "bambu_001",
  "priority": 5,
  "auto_upload": true,
  "auto_start": false
}
```

### 4. Slice and Print (One Step)

```bash
POST /api/v1/slicing/slice-and-print
Content-Type: application/json

{
  "file_checksum": "abc123...",
  "slicer_id": "uuid",
  "profile_id": "uuid",
  "printer_id": "bambu_001",
  "auto_start": true
}
```

## WebSocket Events

Subscribe to slicing events via WebSocket (`/ws`):

### Events Emitted

```javascript
// Slicer detected
{
  "type": "slicer.detected",
  "data": {
    "count": 1
  }
}

// Job created
{
  "type": "slicing_job.created",
  "data": {
    "job_id": "uuid"
  }
}

// Status changed
{
  "type": "slicing_job.status_changed",
  "data": {
    "job_id": "uuid",
    "status": "running"
  }
}

// Progress update
{
  "type": "slicing_job.progress",
  "data": {
    "job_id": "uuid",
    "progress": 50
  }
}

// Job completed
{
  "type": "slicing_job.completed",
  "data": {
    "job_id": "uuid"
  }
}

// Job failed
{
  "type": "slicing_job.failed",
  "data": {
    "job_id": "uuid",
    "error": "Error message"
  }
}

// Job cancelled
{
  "type": "slicing_job.cancelled",
  "data": {
    "job_id": "uuid"
  }
}
```

## Security Considerations

### ✅ Implemented Safeguards

1. **Command Injection Prevention**
   - All subprocess calls use list args (no `shell=True`)
   - Paths are validated as Path objects
   - No string interpolation in commands

2. **Path Validation**
   - File operations restricted to configured directories
   - Input files must exist in library
   - Output directory is controlled

3. **Executable Validation**
   - Only registered slicer executables can be used
   - Verification checks executable existence and response

4. **Resource Limits**
   - Maximum concurrent jobs (default: 2)
   - Job timeout (default: 1 hour)
   - Progress tracking with timeout enforcement

## Testing

### Unit Tests (33 tests, 100% passing)

- **SlicerDetector**: 11 tests
  - Initialization
  - Slicer detection (found/not found)
  - Version extraction
  - Verification

- **SlicerService**: 12 tests
  - Registration and retrieval
  - Profile management
  - Availability verification
  - Auto-detection

- **SlicingQueue**: 10 tests
  - Job creation and retrieval
  - Queue management
  - Cancellation and deletion
  - Status and progress updates

### Running Tests

```bash
# All slicer tests
pytest tests/services/test_slicer*.py -v

# Individual service tests
pytest tests/services/test_slicer_detector.py -v
pytest tests/services/test_slicer_service.py -v
pytest tests/services/test_slicing_queue.py -v
```

## Troubleshooting

### Slicer Not Detected

**Problem**: Slicers installed but not detected

**Solutions**:
1. Check slicer is in standard installation path
2. Manually register slicer via API
3. Set executable path in environment variables:
   ```bash
   PRUSASLICER_PATH=/custom/path/to/prusa-slicer
   BAMBUSTUDIO_PATH=/custom/path/to/bambustudio
   ```

### Job Timeout

**Problem**: Slicing jobs timing out

**Solutions**:
1. Increase timeout: `SLICING_TIMEOUT_SECONDS=7200`
2. Check slicer profile settings (high quality = longer time)
3. Verify input file is not corrupted

### Failed to Import Profiles

**Problem**: Profile import fails or returns empty

**Solutions**:
1. Check config directory path is correct
2. Ensure profiles exist in slicer config directory
3. Verify directory permissions

## Future Enhancements

### Planned Features

1. **Profile Editor**: Edit profile settings via API
2. **Batch Slicing**: Slice multiple files with same settings
3. **Thumbnail Preview**: Extract and display slicer-generated thumbnails
4. **Time Estimation**: Parse G-code for accurate time estimates
5. **Filament Calculation**: Extract filament usage from G-code
6. **Custom Profiles**: Create profiles without slicer installation
7. **Profile Templates**: Share profiles across installations

### Frontend Integration

- Visual job queue dashboard
- Drag-and-drop file slicing
- Profile selector UI
- Real-time progress indicators
- Slicer settings management page

## Performance

- **Concurrent Jobs**: Up to 2 simultaneous slicing operations (configurable)
- **Queue Processing**: FIFO with priority support (1-10)
- **Progress Updates**: Every 5 seconds during slicing
- **Job Persistence**: Queue survives application restarts
- **Cleanup**: Automatic deletion of old G-code files

## Compatibility

### Supported Slicers

- ✅ PrusaSlicer (v2.7.0+)
- ✅ BambuStudio (v1.9.0+)
- ✅ OrcaSlicer (v1.8.0+)
- ✅ SuperSlicer (v2.5.0+)

### Supported Platforms

- ✅ Linux (Ubuntu, Debian, Fedora, etc.)
- ✅ Windows 10/11
- ✅ macOS (Intel and Apple Silicon)

### Supported File Formats

- ✅ STL
- ✅ 3MF
- ✅ OBJ
- ✅ AMF
- ✅ STEP (if supported by slicer)

## License

Same as Printernizer project license.

## Support

For issues or questions:
1. Check GitHub Issues
2. Review API documentation at `/docs`
3. Check application logs for errors
