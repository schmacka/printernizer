# Usage Statistics - Technical Specification

**Version:** 1.0 (Draft)
**Last Updated:** 2025-11-20
**Status:** Draft for Implementation

## System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Printernizer Application                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  src/services/usage_statistics_service.py                │   │
│  │                                                           │   │
│  │  - record_event(event_type, metadata)                    │   │
│  │  - aggregate_stats() → dict                              │   │
│  │  - submit_stats() → bool                                 │   │
│  │  - get_local_stats() → dict                              │   │
│  │  - delete_all_stats() → bool                             │   │
│  │  - export_stats() → JSON                                 │   │
│  └────────────────┬─────────────────────────────────────────┘   │
│                   │                                              │
│  ┌────────────────▼─────────────────────────────────────────┐   │
│  │  src/database/repositories/usage_statistics_repository.py│   │
│  │                                                           │   │
│  │  - insert_event(event)                                   │   │
│  │  - get_events(filters) → List[Event]                     │   │
│  │  - get_setting(key) → str                                │   │
│  │  - set_setting(key, value)                               │   │
│  │  - delete_all_events()                                   │   │
│  └────────────────┬─────────────────────────────────────────┘   │
│                   │                                              │
│  ┌────────────────▼─────────────────────────────────────────┐   │
│  │  SQLite Database (printernizer.db)                       │   │
│  │                                                           │   │
│  │  Tables:                                                  │   │
│  │  - usage_events                                          │   │
│  │  - usage_settings                                        │   │
│  │  - usage_aggregates (optional cache)                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  src/api/routers/usage_statistics.py                     │   │
│  │                                                           │   │
│  │  GET  /api/v1/usage-stats/local                          │   │
│  │  GET  /api/v1/usage-stats/export                         │   │
│  │  POST /api/v1/usage-stats/opt-in                         │   │
│  │  POST /api/v1/usage-stats/opt-out                        │   │
│  │  DELETE /api/v1/usage-stats/delete-all                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Frontend: Settings UI                                   │   │
│  │  - Privacy settings page                                 │   │
│  │  - Local statistics viewer                               │   │
│  │  - Export/delete controls                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└───────────────────────────┬───────────────────────────────────────┘
                            │ HTTPS POST (weekly, if opted in)
                            │
              ┌─────────────▼─────────────────────────────────┐
              │  Aggregation Service (Phase 2)                │
              │  https://stats.printernizer.com               │
              │                                               │
              │  POST /submit                                 │
              │  - Validate payload                           │
              │  - Rate limiting                              │
              │  - Store in SQL Server                        │
              └───────────────────────────────────────────────┘
```

## Database Schema (Phase 1: Local Storage)

### Table: `usage_events`

Stores individual usage events for local analysis and aggregation.

```sql
CREATE TABLE IF NOT EXISTS usage_events (
    id TEXT PRIMARY KEY,                    -- UUID v4
    event_type TEXT NOT NULL,               -- Event category (see Event Types below)
    timestamp DATETIME NOT NULL,            -- ISO 8601 format
    metadata TEXT,                          -- JSON blob with event-specific data
    submitted BOOLEAN DEFAULT 0,            -- Flag: has this been submitted?
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Indexes for performance
    INDEX idx_event_type (event_type),
    INDEX idx_timestamp (timestamp),
    INDEX idx_submitted (submitted)
);
```

**Event Types:**
- `app_start` - Application started
- `app_shutdown` - Application stopped gracefully
- `job_created` - Print job created
- `job_completed` - Print job completed successfully
- `job_failed` - Print job failed
- `file_downloaded` - File downloaded from printer
- `file_uploaded` - File uploaded to library
- `printer_connected` - Printer connected successfully
- `printer_disconnected` - Printer disconnected
- `error_occurred` - Error encountered (with sanitized details)
- `feature_enabled` - Feature toggled on
- `feature_disabled` - Feature toggled off

**Metadata Examples:**

```json
// app_start event
{
  "app_version": "2.7.0",
  "python_version": "3.11.0",
  "platform": "linux",
  "deployment_mode": "homeassistant"
}

// job_completed event
{
  "duration_seconds": 3600,
  "printer_type": "bambu_lab"
}

// error_occurred event
{
  "error_type": "connection_timeout",
  "component": "printer_service",
  "printer_type": "prusa"
}
```

### Table: `usage_settings`

Stores configuration for usage statistics feature.

```sql
CREATE TABLE IF NOT EXISTS usage_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Keys:**
- `opt_in_status` - `"enabled"` or `"disabled"`
- `installation_id` - Random UUID (generated on first run)
- `first_run_date` - ISO 8601 timestamp
- `last_submission_date` - ISO 8601 timestamp
- `submission_count` - Number of times stats submitted
- `privacy_policy_version` - Version user agreed to

### Table: `usage_aggregates` (Optional Cache)

Pre-computed aggregates for faster local statistics viewing.

```sql
CREATE TABLE IF NOT EXISTS usage_aggregates (
    period_start DATE PRIMARY KEY,          -- Week/day start
    period_end DATE NOT NULL,               -- Week/day end
    aggregate_data TEXT NOT NULL,           -- JSON blob
    computed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Data Models (Pydantic)

### Event Model

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

class UsageEvent(BaseModel):
    """Individual usage event."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = Field(..., min_length=1, max_length=50)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    submitted: bool = False

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "event_type": "job_completed",
                "timestamp": "2024-11-20T12:00:00Z",
                "metadata": {"duration_seconds": 3600, "printer_type": "bambu_lab"},
                "submitted": False
            }
        }
```

### Aggregated Stats Model

```python
class AggregatedStats(BaseModel):
    """Aggregated statistics for a time period."""
    schema_version: str = "1.0"
    submission_timestamp: datetime = Field(default_factory=datetime.utcnow)

    installation: InstallationInfo
    period: TimePeriod
    printer_fleet: PrinterFleetStats
    usage_stats: UsageStats
    error_summary: Dict[str, int]

    class Config:
        json_schema_extra = {
            "example": {
                "schema_version": "1.0",
                "submission_timestamp": "2024-11-20T12:00:00Z",
                "installation": {...},
                "period": {...},
                "printer_fleet": {...},
                "usage_stats": {...},
                "error_summary": {"connection_timeout": 2}
            }
        }

class InstallationInfo(BaseModel):
    """Anonymous installation information."""
    installation_id: str = Field(..., min_length=36, max_length=36)
    first_seen: datetime
    app_version: str
    python_version: str
    platform: str  # "linux", "windows", "darwin"
    deployment_mode: str  # "homeassistant", "docker", "standalone", "pi"
    country_code: str = Field(..., min_length=2, max_length=2)

class TimePeriod(BaseModel):
    """Time period for aggregated stats."""
    start: datetime
    end: datetime
    duration_days: int

class PrinterFleetStats(BaseModel):
    """Printer fleet composition (anonymous)."""
    printer_count: int = Field(..., ge=0)
    printer_types: list[str]
    printer_type_counts: Dict[str, int]

class UsageStats(BaseModel):
    """Usage activity statistics."""
    job_count: int = Field(..., ge=0)
    file_count: int = Field(..., ge=0)
    upload_count: int = Field(..., ge=0)
    uptime_hours: int = Field(..., ge=0)
    feature_usage: Dict[str, bool]
```

## Service Layer Implementation

### UsageStatisticsService

```python
# src/services/usage_statistics_service.py

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import structlog
import aiohttp
from src.database.repositories.usage_statistics_repository import UsageStatisticsRepository
from src.models.usage_statistics import UsageEvent, AggregatedStats
from src.utils.config import get_settings

logger = structlog.get_logger()

class UsageStatisticsService:
    """
    Privacy-first usage statistics service.

    Responsibilities:
    - Record usage events locally
    - Aggregate statistics for submission
    - Submit to aggregation service (if opted in)
    - Provide local statistics viewer data
    - Handle opt-in/opt-out
    """

    def __init__(self, repository: UsageStatisticsRepository):
        self.repository = repository
        self.settings = get_settings()
        self.aggregation_endpoint = "https://stats.printernizer.com/submit"

    async def is_opted_in(self) -> bool:
        """Check if user has opted in to usage statistics."""
        opt_in_status = await self.repository.get_setting("opt_in_status")
        return opt_in_status == "enabled"

    async def opt_in(self) -> bool:
        """Enable usage statistics collection and submission."""
        logger.info("User opted in to usage statistics")
        await self.repository.set_setting("opt_in_status", "enabled")

        # Generate installation ID if not exists
        installation_id = await self.repository.get_setting("installation_id")
        if not installation_id:
            installation_id = str(uuid.uuid4())
            await self.repository.set_setting("installation_id", installation_id)
            await self.repository.set_setting("first_run_date", datetime.utcnow().isoformat())

        return True

    async def opt_out(self) -> bool:
        """Disable usage statistics collection and submission."""
        logger.info("User opted out of usage statistics")
        await self.repository.set_setting("opt_in_status", "disabled")
        return True

    async def record_event(
        self,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[UsageEvent]:
        """
        Record a usage event.

        Events are stored locally regardless of opt-in status
        (allows user to review before opting in).
        Submission only happens if opted in.
        """
        try:
            event = UsageEvent(
                event_type=event_type,
                metadata=metadata or {}
            )

            await self.repository.insert_event(event)
            logger.debug("Usage event recorded", event_type=event_type)
            return event

        except Exception as e:
            # Never let statistics break the app
            logger.error("Failed to record usage event", error=str(e), event_type=event_type)
            return None

    async def aggregate_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AggregatedStats:
        """
        Aggregate usage statistics for a time period.

        Default: last 7 days if no dates provided.
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=7)

        # Get events for period
        events = await self.repository.get_events(
            start_date=start_date,
            end_date=end_date
        )

        # TODO: Implement aggregation logic
        # - Count events by type
        # - Get printer fleet composition (from PrinterService)
        # - Calculate uptime
        # - Summarize errors

        return aggregated_stats

    async def submit_stats(self) -> bool:
        """
        Submit aggregated statistics to remote endpoint.

        Only submits if opted in.
        Returns True if submission successful or not needed.
        """
        if not await self.is_opted_in():
            logger.debug("Skipping stats submission - user opted out")
            return True

        try:
            # Get aggregated stats
            stats = await self.aggregate_stats()

            # Submit via HTTPS
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.aggregation_endpoint,
                    json=stats.model_dump(),
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("Usage statistics submitted successfully")

                        # Mark events as submitted
                        await self.repository.mark_events_submitted(
                            start_date=stats.period.start,
                            end_date=stats.period.end
                        )

                        # Update last submission date
                        await self.repository.set_setting(
                            "last_submission_date",
                            datetime.utcnow().isoformat()
                        )

                        return True
                    else:
                        logger.warning(
                            "Failed to submit usage statistics",
                            status_code=response.status
                        )
                        return False

        except Exception as e:
            # Never let statistics break the app
            logger.error("Error submitting usage statistics", error=str(e))
            return False

    async def get_local_stats(self) -> Dict[str, Any]:
        """
        Get local statistics for user viewing.

        Returns human-readable summary of collected data.
        """
        # TODO: Implement local stats viewer data
        pass

    async def export_stats(self) -> str:
        """Export all local statistics as JSON."""
        events = await self.repository.get_all_events()
        settings = await self.repository.get_all_settings()

        return json.dumps({
            "events": [e.model_dump() for e in events],
            "settings": settings,
            "exported_at": datetime.utcnow().isoformat()
        }, indent=2)

    async def delete_all_stats(self) -> bool:
        """Delete all local statistics."""
        logger.info("Deleting all local usage statistics")
        await self.repository.delete_all_events()
        return True
```

## API Endpoints (Phase 1)

### GET `/api/v1/usage-stats/local`

Get local statistics summary for user viewing.

**Response:**
```json
{
  "installation_id": "550e8400...",
  "first_seen": "2024-11-01T00:00:00Z",
  "opt_in_status": "disabled",
  "total_events": 1234,
  "this_week": {
    "job_count": 23,
    "file_count": 18,
    "error_count": 2
  },
  "last_submission": null
}
```

### POST `/api/v1/usage-stats/opt-in`

Enable usage statistics collection and submission.

**Response:**
```json
{
  "success": true,
  "installation_id": "550e8400...",
  "message": "Usage statistics enabled. Thank you for helping improve Printernizer!"
}
```

### POST `/api/v1/usage-stats/opt-out`

Disable usage statistics submission.

**Response:**
```json
{
  "success": true,
  "message": "Usage statistics disabled. Your data will remain local."
}
```

### GET `/api/v1/usage-stats/export`

Export all local statistics as JSON.

**Response:** (JSON file download)

### DELETE `/api/v1/usage-stats/delete-all`

Delete all local usage statistics.

**Response:**
```json
{
  "success": true,
  "deleted_events": 1234,
  "message": "All local statistics have been deleted."
}
```

## Background Tasks

### Submission Scheduler

```python
# src/tasks/usage_statistics_submitter.py

import asyncio
from datetime import datetime, timedelta

async def periodic_stats_submission(service: UsageStatisticsService):
    """
    Background task to submit statistics weekly.

    Runs every 24 hours, submits if 7 days since last submission.
    """
    while True:
        try:
            last_submission = await service.repository.get_setting("last_submission_date")

            if last_submission:
                last_date = datetime.fromisoformat(last_submission)
                if datetime.utcnow() - last_date >= timedelta(days=7):
                    await service.submit_stats()
            else:
                # First submission after opt-in
                await service.submit_stats()

        except Exception as e:
            logger.error("Error in periodic stats submission", error=str(e))

        # Check every 24 hours
        await asyncio.sleep(86400)
```

## Integration Points

### Application Startup

```python
# src/main.py

from src.services.usage_statistics_service import UsageStatisticsService

async def on_startup():
    # ... existing startup code ...

    # Initialize usage statistics
    stats_service = UsageStatisticsService(repository=stats_repo)
    await stats_service.record_event("app_start", metadata={
        "app_version": APP_VERSION,
        "python_version": platform.python_version(),
        "platform": platform.system().lower(),
        "deployment_mode": get_deployment_mode()
    })

    # Start background submission task
    asyncio.create_task(periodic_stats_submission(stats_service))
```

### Job Service Integration

```python
# src/services/job_service.py

async def create_job(self, ...):
    # ... existing job creation logic ...

    # Record usage event
    if self.stats_service:
        await self.stats_service.record_event("job_created", metadata={
            "printer_type": printer.type
        })
```

## Performance Considerations

### Non-Blocking Design
- All statistics operations are async
- Never block main application flow
- Fail silently if statistics fail

### Database Optimization
- Indexes on frequently queried columns
- Batch inserts for multiple events
- Periodic cleanup of old events (optional)

### Memory Usage
- Events are not kept in memory
- Direct database writes
- Aggregation done on-demand

### Network Impact
- Submissions are async and background
- Max 1 submission per week
- Payload size: ~1KB (minimal bandwidth)

## Testing Strategy

### Unit Tests
- `test_usage_statistics_service.py`
- `test_usage_statistics_repository.py`
- Mock external HTTP calls

### Integration Tests
- Test full event flow
- Test aggregation accuracy
- Test opt-in/opt-out behavior

### Privacy Tests
- Verify no PII in payloads
- Test data sanitization
- Verify opt-out stops submission

## Migration

### Database Migration

```python
# src/database/migrations/00XX_add_usage_statistics.py

async def upgrade(connection):
    """Add usage statistics tables."""
    await connection.execute("""
        CREATE TABLE IF NOT EXISTS usage_events (
            id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            metadata TEXT,
            submitted BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await connection.execute("""
        CREATE INDEX idx_usage_events_type ON usage_events(event_type)
    """)

    await connection.execute("""
        CREATE INDEX idx_usage_events_timestamp ON usage_events(timestamp)
    """)

    await connection.execute("""
        CREATE TABLE IF NOT EXISTS usage_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

async def downgrade(connection):
    """Remove usage statistics tables."""
    await connection.execute("DROP TABLE IF EXISTS usage_events")
    await connection.execute("DROP TABLE IF EXISTS usage_settings")
```

## Security Considerations

### Input Validation
- Sanitize all event metadata
- Validate event types against whitelist
- Limit metadata size (max 1KB per event)

### Rate Limiting
- Max 1 submission per hour per installation
- Prevent DoS of aggregation service

### Data Sanitization
- Remove file paths from error messages
- Remove network information
- Remove user input

---

**Next Steps:**
1. Review and approve technical design
2. Implement Phase 1 (local collection)
3. Write comprehensive tests
4. Deploy and monitor
