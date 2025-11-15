# API Documentation - Automated Job Creation

## Overview

This document describes the API changes and additions related to the automated job creation feature.

## Job Model Updates

### customer_info Field

The `customer_info` field now contains auto-creation metadata when a job is automatically created.

#### Structure

```json
{
  "customer_info": {
    "auto_created": true,
    "discovery_time": "2025-01-09T14:30:00.123456",
    "printer_start_time": "2025-01-09T14:28:45.000000",
    "discovered_on_startup": false
  }
}
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `auto_created` | boolean | `true` if job was auto-created, `false` or absent otherwise |
| `discovery_time` | string (ISO 8601) | When Printernizer first detected the print |
| `printer_start_time` | string (ISO 8601) | Start time reported by printer (if available) |
| `discovered_on_startup` | boolean | `true` if print was discovered on system startup |

#### Example Response

```json
{
  "id": "job_12345",
  "printer_id": "bambu_001",
  "job_name": "test_cube",
  "filename": "test_cube.3mf",
  "status": "running",
  "start_time": "2025-01-09T14:28:45",
  "customer_info": {
    "auto_created": true,
    "discovery_time": "2025-01-09T14:30:00",
    "printer_start_time": "2025-01-09T14:28:45",
    "discovered_on_startup": false
  },
  ...
}
```

## WebSocket Events

### job_auto_created

Emitted when a job is automatically created.

#### Event Structure

```json
{
  "type": "job_auto_created",
  "data": {
    "id": "job_12345",
    "printer_id": "bambu_001",
    "job_name": "test_cube",
    "filename": "test_cube.3mf",
    "status": "running",
    "start_time": "2025-01-09T14:28:45",
    "customer_info": {
      "auto_created": true,
      "discovery_time": "2025-01-09T14:30:00",
      "printer_start_time": "2025-01-09T14:28:45",
      "discovered_on_startup": false
    }
  }
}
```

#### Listening for Events

**JavaScript Example:**

```javascript
// Using WebSocketManager
websocketManager.ws.on('job_auto_created', (data) => {
    console.log('Auto-created job:', data);

    // Show notification
    showToast('info', 'Job Auto-Created', `${data.job_name} on ${data.printer_id}`);

    // Refresh job list
    if (window.jobManager) {
        window.jobManager.loadJobs();
    }
});
```

**Python Example (using websocket-client):**

```python
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    if data['type'] == 'job_auto_created':
        job = data['data']
        print(f"Auto-created job: {job['job_name']} on {job['printer_id']}")

ws = websocket.WebSocketApp(
    "ws://localhost:8000/ws",
    on_message=on_message
)
ws.run_forever()
```

## Settings API

### GET /api/v1/settings

Returns application settings including auto-creation configuration.

#### Response

```json
{
  "job_creation_auto_create": true,
  "monitoring_interval": 30,
  ...
}
```

### PUT /api/v1/settings

Update application settings, including auto-creation toggle.

#### Request Body

```json
{
  "job_creation_auto_create": false
}
```

#### Response

```json
{
  "status": "success",
  "message": "Settings updated successfully"
}
```

## Jobs API

No changes to existing endpoints. Jobs created automatically appear in all job endpoints:

- `GET /api/v1/jobs` - List includes auto-created jobs
- `GET /api/v1/jobs/{id}` - Auto-created jobs have `customer_info` with metadata
- `PUT /api/v1/jobs/{id}` - Auto-created jobs can be edited like manual jobs
- `DELETE /api/v1/jobs/{id}` - Auto-created jobs can be deleted

### Filtering Auto-Created Jobs

Currently, no dedicated filter exists for auto-created jobs. Use client-side filtering:

```javascript
const autoJobs = jobs.filter(job =>
    job.customer_info?.auto_created === true
);
```

**Future Enhancement**: Add `?auto_created=true` query parameter to jobs endpoint.

## Monitoring Service

The automated job creation feature integrates with the existing printer monitoring service.

### Internal Flow

1. **Status Polling**: `PrinterMonitoringService` polls printers every `monitoring_interval` seconds
2. **Auto-Creation Check**: On each status update, `_auto_create_job_if_needed()` is called
3. **Deduplication**: Checks in-memory cache and database for existing jobs
4. **Job Creation**: Creates job via `JobService.create_job()`
5. **Event Emission**: Emits `job_auto_created` event via WebSocket

### Configuration

Auto-creation behavior is controlled by:

```python
# In src/services/config_service.py
class Settings(BaseSettings):
    job_creation_auto_create: bool = True  # Default: enabled
```

Environment variable: `JOB_CREATION_AUTO_CREATE=true|false`

## Integration Examples

### Frontend Integration

Complete example of handling auto-created jobs in frontend:

```javascript
class AutoJobHandler {
    constructor() {
        this.setupWebSocket();
    }

    setupWebSocket() {
        // Listen for auto-created jobs
        websocketManager.ws.on('job_auto_created', (data) => {
            this.handleAutoJob(data);
        });
    }

    handleAutoJob(jobData) {
        // Show notification
        const message = `${jobData.job_name} on ${jobData.printer_id}`;
        if (jobData.customer_info?.discovered_on_startup) {
            showToast('info', '⚡ Job Discovered',
                     `${message} (on startup)`);
        } else {
            showToast('info', '⚡ Job Auto-Created', message);
        }

        // Update UI
        this.refreshJobsList();
        this.updateDashboard();
    }

    refreshJobsList() {
        if (window.jobManager) {
            window.jobManager.loadJobs();
        }
    }

    isAutoCreated(job) {
        return job.customer_info?.auto_created === true;
    }

    renderJobBadge(job) {
        if (this.isAutoCreated(job)) {
            const tooltip = this.buildTooltip(job);
            return `<span class="badge-auto" title="${tooltip}">⚡ Auto</span>`;
        }
        return '';
    }

    buildTooltip(job) {
        let text = 'Automatically created';
        if (job.customer_info?.discovered_on_startup) {
            text += ' (discovered on startup)';
        }
        if (job.customer_info?.discovery_time) {
            text += `\nDiscovered: ${formatDateTime(job.customer_info.discovery_time)}`;
        }
        return text;
    }
}

// Initialize
const autoJobHandler = new AutoJobHandler();
```

### Backend Integration

Example of subscribing to auto-creation events:

```python
from src.services.event_service import EventService

# Subscribe to job auto-creation events
async def on_job_auto_created(data):
    job_id = data['id']
    printer_id = data['printer_id']
    filename = data['filename']

    print(f"Auto-created job {job_id}: {filename} on {printer_id}")

    # Custom logic here
    # e.g., send email notification, update external system, etc.

event_service = EventService()
event_service.subscribe('job_auto_created', on_job_auto_created)
```

## Error Handling

### Auto-Creation Failures

If job creation fails, the system:

1. Logs the error (see logs for details)
2. Does NOT show error to user (silent failure)
3. Will retry on next status update
4. Does NOT affect printer monitoring

### Duplicate Prevention

The deduplication strategy prevents:

- Multiple jobs from rapid status updates
- Duplicates across system restarts
- Duplicates from cache/filename variations

**Edge case**: If a job is manually created at nearly the same time as auto-creation, a duplicate may occur. This is rare and can be deleted manually.

## Performance Considerations

### Monitoring Overhead

Auto-creation adds minimal overhead to status updates:

- **Average**: < 1ms per status update (cache hit)
- **Worst case**: < 50ms (database lookup + job creation)
- **Memory**: ~50 bytes per tracked print

### Database Impact

- Queries limited to 20 results
- Uses indexes on `printer_id`, `filename`, `created_at`
- Typical query time: < 30ms

### WebSocket Load

- One event per auto-created job
- Event size: ~500 bytes (typical)
- Broadcast to all connected clients

## Migration Notes

### Existing Jobs

Jobs created before this feature:
- Will NOT have `customer_info.auto_created` field
- Can be identified by absence of this field
- No migration needed

### Database Schema

No database migrations required. The `customer_info` field already exists as TEXT (JSON).

## Versioning

| Version | Changes |
|---------|---------|
| 2.3.0 | Initial release of automated job creation |
| Future | Planned: Per-printer settings, custom filters, enhanced metadata |

## Testing

### Manual Testing

1. Start a print on a connected printer
2. Wait 30 seconds (monitoring interval)
3. Check job list for auto-created job with ⚡ badge
4. Verify WebSocket event received
5. Check job details show correct `customer_info`

### API Testing

```bash
# Get jobs and check for auto-created
curl http://localhost:8000/api/v1/jobs | jq '.jobs[] | select(.customer_info.auto_created == true)'

# Get settings
curl http://localhost:8000/api/v1/settings | jq '.job_creation_auto_create'

# Toggle auto-creation
curl -X PUT http://localhost:8000/api/v1/settings \
  -H "Content-Type: application/json" \
  -d '{"job_creation_auto_create": false}'
```

### WebSocket Testing

```javascript
// Browser console
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'job_auto_created') {
        console.log('Auto-created job:', data);
    }
};
```

## Security Considerations

### Authorization

- Auto-creation respects same authorization as manual job creation
- No special permissions required
- Settings changes require admin access (if auth enabled)

### Data Privacy

- Only captures data already available from printer status
- No additional PII collected
- Metadata stored in existing `customer_info` field

### Rate Limiting

- Auto-creation inherits monitoring service rate limiting
- Maximum: 1 job per (printer, filename, minute)
- Prevents spam from rapid status changes

## Support

For issues or questions:

- **Documentation**: `docs/design/automated-job-creation.md`
- **User Guide**: `docs/user-guide-auto-job-creation.md`
- **Testing Guide**: `docs/automated-job-creation-testing.md`
- **GitHub**: Submit issues at repository

---

**Version**: 2.3.0
**Last Updated**: 2025-01-09
**API Status**: Stable
