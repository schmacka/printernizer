# Slicer Integration - API Examples

## Quick Start

### 1. Detect Available Slicers

Automatically detect installed slicers on the system:

```bash
curl -X POST http://localhost:8000/api/v1/slicing/detect
```

Response:
```json
{
  "detected": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "PrusaSlicer",
      "slicer_type": "prusaslicer",
      "executable_path": "/usr/bin/prusa-slicer",
      "version": "2.7.0",
      "config_dir": "/home/user/.config/PrusaSlicer",
      "is_available": true,
      "last_verified": "2026-01-03T21:00:00",
      "created_at": "2026-01-03T21:00:00",
      "updated_at": "2026-01-03T21:00:00"
    }
  ],
  "count": 1
}
```

### 2. List Registered Slicers

Get all registered slicers (available and unavailable):

```bash
curl http://localhost:8000/api/v1/slicing
```

Get only available slicers:

```bash
curl http://localhost:8000/api/v1/slicing?available_only=true
```

### 3. Import Profiles

Import profiles from slicer config directory:

```bash
curl -X POST http://localhost:8000/api/v1/slicing/550e8400-e29b-41d4-a716-446655440000/profiles/import
```

Response:
```json
{
  "profiles": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "slicer_id": "550e8400-e29b-41d4-a716-446655440000",
      "profile_name": "0.2mm SPEED",
      "profile_type": "print",
      "profile_path": "/home/user/.config/PrusaSlicer/print/0.2mm_SPEED.ini",
      "settings_json": null,
      "compatible_printers": null,
      "is_default": false,
      "created_at": "2026-01-03T21:00:00",
      "updated_at": "2026-01-03T21:00:00"
    }
  ],
  "count": 1
}
```

### 4. List Profiles

Get all profiles for a slicer:

```bash
curl http://localhost:8000/api/v1/slicing/550e8400-e29b-41d4-a716-446655440000/profiles
```

Filter by profile type:

```bash
curl http://localhost:8000/api/v1/slicing/550e8400-e29b-41d4-a716-446655440000/profiles?profile_type=print
```

## Slicing Operations

### 5. Create Basic Slicing Job

Create a job to slice a file from the library:

```bash
curl -X POST http://localhost:8000/api/v1/slicing/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "file_checksum": "abc123def456...",
    "slicer_id": "550e8400-e29b-41d4-a716-446655440000",
    "profile_id": "660e8400-e29b-41d4-a716-446655440001",
    "priority": 5
  }'
```

Response:
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "file_checksum": "abc123def456...",
  "filename": "model.stl",
  "slicer_id": "550e8400-e29b-41d4-a716-446655440000",
  "slicer_name": "PrusaSlicer",
  "profile_id": "660e8400-e29b-41d4-a716-446655440001",
  "profile_name": "0.2mm SPEED",
  "target_printer_id": null,
  "status": "queued",
  "priority": 5,
  "progress": 0,
  "output_file_path": null,
  "estimated_print_time": null,
  "filament_used": null,
  "error_message": null,
  "retry_count": 0,
  "auto_upload": false,
  "auto_start": false,
  "started_at": null,
  "completed_at": null,
  "created_at": "2026-01-03T21:00:00",
  "updated_at": "2026-01-03T21:00:00"
}
```

### 6. Create Job with Auto-Upload

Slice and automatically upload to printer:

```bash
curl -X POST http://localhost:8000/api/v1/slicing/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "file_checksum": "abc123def456...",
    "slicer_id": "550e8400-e29b-41d4-a716-446655440000",
    "profile_id": "660e8400-e29b-41d4-a716-446655440001",
    "target_printer_id": "bambu_001",
    "priority": 8,
    "auto_upload": true,
    "auto_start": false
  }'
```

### 7. Slice and Print (One-Click)

Complete workflow in one API call:

```bash
curl -X POST http://localhost:8000/api/v1/slicing/slice-and-print \
  -H "Content-Type: application/json" \
  -d '{
    "file_checksum": "abc123def456...",
    "slicer_id": "550e8400-e29b-41d4-a716-446655440000",
    "profile_id": "660e8400-e29b-41d4-a716-446655440001",
    "printer_id": "bambu_001",
    "auto_start": true,
    "priority": 10
  }'
```

### 8. Slice Library File

Alternative endpoint for slicing from library:

```bash
curl -X POST http://localhost:8000/api/v1/slicing/library/abc123def456.../slice \
  -H "Content-Type: application/json" \
  -d '{
    "slicer_id": "550e8400-e29b-41d4-a716-446655440000",
    "profile_id": "660e8400-e29b-41d4-a716-446655440001",
    "priority": 5
  }'
```

## Job Management

### 9. List All Jobs

Get all slicing jobs:

```bash
curl http://localhost:8000/api/v1/slicing/jobs
```

Filter by status:

```bash
# Queued jobs
curl http://localhost:8000/api/v1/slicing/jobs?status=queued

# Running jobs
curl http://localhost:8000/api/v1/slicing/jobs?status=running

# Completed jobs
curl http://localhost:8000/api/v1/slicing/jobs?status=completed

# Failed jobs
curl http://localhost:8000/api/v1/slicing/jobs?status=failed
```

Limit results:

```bash
curl http://localhost:8000/api/v1/slicing/jobs?limit=10
```

### 10. Get Job Status

Check status of specific job:

```bash
curl http://localhost:8000/api/v1/slicing/jobs/770e8400-e29b-41d4-a716-446655440002
```

Response (running job):
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "file_checksum": "abc123def456...",
  "filename": "model.stl",
  "slicer_id": "550e8400-e29b-41d4-a716-446655440000",
  "slicer_name": "PrusaSlicer",
  "profile_id": "660e8400-e29b-41d4-a716-446655440001",
  "profile_name": "0.2mm SPEED",
  "target_printer_id": "bambu_001",
  "status": "running",
  "priority": 8,
  "progress": 50,
  "output_file_path": null,
  "estimated_print_time": null,
  "filament_used": null,
  "error_message": null,
  "retry_count": 0,
  "auto_upload": true,
  "auto_start": false,
  "started_at": "2026-01-03T21:00:00",
  "completed_at": null,
  "created_at": "2026-01-03T21:00:00",
  "updated_at": "2026-01-03T21:00:05"
}
```

### 11. Cancel Job

Cancel a running or queued job:

```bash
curl -X POST http://localhost:8000/api/v1/slicing/jobs/770e8400-e29b-41d4-a716-446655440002/cancel
```

Response:
```json
{
  "success": true,
  "message": "Slicing job cancelled successfully"
}
```

### 12. Delete Job

Delete a completed, failed, or cancelled job:

```bash
curl -X DELETE http://localhost:8000/api/v1/slicing/jobs/770e8400-e29b-41d4-a716-446655440002
```

Response:
```json
{
  "success": true,
  "message": "Slicing job deleted successfully"
}
```

## Profile Management

### 13. Get Profile Details

Get specific profile information:

```bash
curl http://localhost:8000/api/v1/slicing/profiles/660e8400-e29b-41d4-a716-446655440001
```

### 14. Delete Profile

Remove a profile:

```bash
curl -X DELETE http://localhost:8000/api/v1/slicing/profiles/660e8400-e29b-41d4-a716-446655440001
```

## Slicer Management

### 15. Get Slicer Details

Get specific slicer information:

```bash
curl http://localhost:8000/api/v1/slicing/550e8400-e29b-41d4-a716-446655440000
```

### 16. Delete Slicer

Remove a slicer configuration:

```bash
curl -X DELETE http://localhost:8000/api/v1/slicing/550e8400-e29b-41d4-a716-446655440000
```

Note: This will also delete all associated profiles and cancel running jobs.

## WebSocket Integration

### 17. Connect to WebSocket for Real-Time Updates

```javascript
// JavaScript example
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'slicing_job.created':
      console.log('Job created:', message.data.job_id);
      break;
      
    case 'slicing_job.status_changed':
      console.log('Job status:', message.data.status);
      break;
      
    case 'slicing_job.progress':
      console.log('Progress:', message.data.progress, '%');
      updateProgressBar(message.data.job_id, message.data.progress);
      break;
      
    case 'slicing_job.completed':
      console.log('Job completed:', message.data.job_id);
      showNotification('Slicing completed!');
      break;
      
    case 'slicing_job.failed':
      console.error('Job failed:', message.data.error);
      showErrorNotification(message.data.error);
      break;
      
    case 'slicing_job.cancelled':
      console.log('Job cancelled:', message.data.job_id);
      break;
  }
};
```

## Error Handling

### Common Error Responses

#### 404 Not Found
```json
{
  "error": "Slicer '550e8400-e29b-41d4-a716-446655440000' not found"
}
```

#### 500 Internal Server Error
```json
{
  "error": "Failed to create slicing job: Slicer is not available"
}
```

#### 400 Bad Request
```json
{
  "error": "Invalid request",
  "detail": {
    "field": "file_checksum",
    "message": "File not found in library"
  }
}
```

## Best Practices

1. **Poll for status updates** every 2-5 seconds for pending jobs (or use WebSocket for real-time updates)
2. **Use priority levels** to manage job order (1=low, 10=urgent)
3. **Clean up completed jobs** regularly to avoid database bloat
4. **Monitor queue depth** to avoid overwhelming the system
5. **Set appropriate timeouts** based on typical model complexity
6. **Use auto-upload** for streamlined workflow
7. **Verify slicer availability** before creating jobs

## Rate Limits

Default API rate limits apply to slicing endpoints. See main API documentation for details.

## Support

- API Documentation: http://localhost:8000/docs
- WebSocket Test: http://localhost:8000/docs#/WebSocket
- Health Check: http://localhost:8000/api/v1/health
