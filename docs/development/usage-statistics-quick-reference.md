# Usage Statistics - Quick Reference

**Purpose:** Fast lookup for developers during implementation
**Updated:** 2025-11-20

---

## 🚦 Privacy Rules (Memorize These!)

### ✅ SAFE to Collect
```python
# System information
"app_version": "2.7.0"
"python_version": "3.11.0"
"platform": "linux"
"deployment_mode": "homeassistant"

# Aggregated counts
"printer_count": 3
"printer_types": ["bambu_lab", "prusa"]
"job_count": 23

# Feature flags
"library_enabled": true
"timelapse_enabled": false

# Error types ONLY
"error_type": "connection_timeout"
"component": "printer_service"

# Geographic (from timezone, not IP)
"country_code": "DE"
```

### ❌ NEVER Collect
```python
# Personal information
"user_name": "John"          # ❌ NO
"email": "john@example.com"  # ❌ NO

# File information
"file_name": "secret.3mf"    # ❌ NO
"file_path": "/home/user/..."# ❌ NO

# Network information
"ip_address": "192.168.1.5"  # ❌ NO
"hostname": "my-printer"     # ❌ NO
"mac_address": "AA:BB:CC..." # ❌ NO

# Device identifiers
"printer_serial": "XYZ123"   # ❌ NO
"pi_serial": "100000000..."  # ❌ NO

# Behavioral tracking
"click_count": 47            # ❌ NO
"time_on_page": 120          # ❌ NO

# Precise data (aggregate instead!)
"job_started_at": "2024-..." # ❌ NO (use counts)
"exact_duration": 3724       # ❌ NO (use ranges)
```

---

## 📝 Event Recording Patterns

### Basic Event (No Metadata)
```python
await stats_service.record_event("app_start")
```

### Event with Safe Metadata
```python
await stats_service.record_event(
    "job_completed",
    metadata={
        "printer_type": "bambu_lab",
        "duration_minutes": 60  # Rounded, not precise
    }
)
```

### Error Event (Sanitized!)
```python
try:
    await printer.connect()
except Exception as e:
    await stats_service.record_event(
        "error_occurred",
        metadata={
            "error_type": type(e).__name__,  # ✅ Class name only
            "component": "printer_service",
            # ❌ NO: "message": str(e)  # May contain PII!
            # ❌ NO: "traceback": ...   # May contain paths!
        }
    )
```

---

## 🗄️ Database Queries

### Insert Event
```python
event = UsageEvent(
    event_type="job_created",
    metadata={"printer_type": "bambu_lab"}
)
await repository.insert_event(event)
```

### Get Events for Period
```python
events = await repository.get_events(
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now(),
    event_type="job_completed"  # Optional filter
)
```

### Check Opt-In Status
```python
status = await repository.get_setting("opt_in_status")
is_opted_in = (status == "enabled")
```

### Mark Events as Submitted
```python
await repository.mark_events_submitted(
    start_date=period_start,
    end_date=period_end
)
```

---

## 🔌 API Endpoints

### Get Local Stats (Frontend)
```javascript
fetch('/api/v1/usage-stats/local')
  .then(res => res.json())
  .then(stats => {
    // Display in UI
  })
```

### Opt In
```javascript
fetch('/api/v1/usage-stats/opt-in', {
  method: 'POST'
})
```

### Opt Out
```javascript
fetch('/api/v1/usage-stats/opt-out', {
  method: 'POST'
})
```

### Export Data
```javascript
window.open('/api/v1/usage-stats/export')  // Downloads JSON
```

### Delete All Data
```javascript
fetch('/api/v1/usage-stats/delete-all', {
  method: 'DELETE'
})
```

---

## 🎨 UI Patterns

### Settings Toggle
```html
<label>
  <input type="checkbox" v-model="optedIn" @change="toggleOptIn" />
  Share anonymous usage statistics
</label>

<p class="privacy-note">
  Help improve Printernizer by sharing anonymous usage data.
  <a href="#" @click="showPrivacyPolicy">What we collect</a>
</p>
```

### Privacy Disclosure
```html
<div class="privacy-disclosure">
  <h3>What we collect:</h3>
  <ul>
    <li>✓ App version and deployment mode</li>
    <li>✓ Number and types of printers</li>
    <li>✓ Feature usage (on/off)</li>
    <li>✓ Anonymous error types</li>
  </ul>

  <h3>What we DON'T collect:</h3>
  <ul>
    <li>✗ Personal information</li>
    <li>✗ File names or content</li>
    <li>✗ IP addresses or location</li>
    <li>✗ Printer serial numbers</li>
  </ul>
</div>
```

### Local Stats Viewer
```html
<div class="stats-card">
  <h4>This Week</h4>
  <div class="stat">
    <span class="label">Jobs Completed:</span>
    <span class="value">{{ stats.job_count }}</span>
  </div>
  <div class="stat">
    <span class="label">Files Downloaded:</span>
    <span class="value">{{ stats.file_count }}</span>
  </div>
</div>

<button @click="exportData">Download My Data</button>
<button @click="deleteAll" class="danger">Delete All Statistics</button>
```

---

## ⚙️ Service Integration

### Application Startup
```python
# src/main.py

async def on_startup():
    # Initialize service
    stats_service = UsageStatisticsService(repository)

    # Record startup event
    await stats_service.record_event("app_start", metadata={
        "app_version": APP_VERSION,
        "python_version": platform.python_version(),
        "platform": sys.platform,
        "deployment_mode": get_deployment_mode()
    })

    # Start background submission task
    asyncio.create_task(periodic_stats_submission(stats_service))
```

### Job Service Integration
```python
# src/services/job_service.py

async def create_job(self, job_data: JobCreate):
    # ... existing job creation logic ...

    # Record event
    await self.stats_service.record_event("job_created", metadata={
        "printer_type": printer.type
    })

    return job
```

### Error Handler Integration
```python
# src/api/error_handlers.py

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # ... existing error handling ...

    # Record anonymized error
    await stats_service.record_event("error_occurred", metadata={
        "error_type": type(exc).__name__,
        "endpoint": request.url.path,  # Generic, no query params
        # ❌ NO user input, NO stack trace, NO PII
    })

    return JSONResponse(...)
```

---

## 🧪 Testing Patterns

### Test Event Recording
```python
async def test_record_event(stats_service):
    event = await stats_service.record_event(
        "test_event",
        metadata={"key": "value"}
    )

    assert event is not None
    assert event.event_type == "test_event"
```

### Test Opt-In/Out
```python
async def test_opt_in(stats_service):
    await stats_service.opt_in()
    assert await stats_service.is_opted_in() == True

    await stats_service.opt_out()
    assert await stats_service.is_opted_in() == False
```

### Test Privacy (No PII)
```python
async def test_no_pii_in_metadata():
    """Ensure metadata never contains PII."""
    event = await stats_service.record_event("test", metadata={
        "printer_type": "bambu_lab"
    })

    metadata = json.loads(event.metadata)

    # These should NEVER be in metadata
    assert "email" not in metadata
    assert "user_name" not in metadata
    assert "ip_address" not in metadata
    assert "file_name" not in metadata
```

### Test Submission
```python
async def test_submit_stats_when_opted_in(
    stats_service,
    mock_http_client
):
    await stats_service.opt_in()

    success = await stats_service.submit_stats()

    assert success == True
    assert mock_http_client.post_called_once()
```

---

## 📊 Aggregation Patterns

### Weekly Aggregation
```python
async def aggregate_stats(
    start_date: datetime,
    end_date: datetime
) -> AggregatedStats:

    # Get events for period
    events = await repository.get_events(start_date, end_date)

    # Count by type
    event_counts = {}
    for event in events:
        event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1

    # Get printer fleet info (from PrinterService, not events!)
    printers = await printer_service.list_printers()
    printer_types = [p.type for p in printers]

    # Build aggregated stats
    return AggregatedStats(
        installation=InstallationInfo(
            installation_id=await get_installation_id(),
            app_version=APP_VERSION,
            # ... etc
        ),
        period=TimePeriod(
            start=start_date,
            end=end_date,
            duration_days=(end_date - start_date).days
        ),
        printer_fleet=PrinterFleetStats(
            printer_count=len(printers),
            printer_types=list(set(printer_types)),
            printer_type_counts={
                t: printer_types.count(t) for t in set(printer_types)
            }
        ),
        usage_stats=UsageStats(
            job_count=event_counts.get("job_completed", 0),
            file_count=event_counts.get("file_downloaded", 0),
            # ... etc
        ),
        error_summary={
            # Count errors by type
        }
    )
```

---

## 🔒 Security Checklist

Before submitting to aggregation service:

- [ ] Payload contains no PII
- [ ] Payload contains no file names/paths
- [ ] Payload contains no network information
- [ ] Payload contains no device identifiers
- [ ] Timestamps rounded to day/week boundaries
- [ ] Error messages sanitized
- [ ] Payload size < 10KB
- [ ] Installation ID is random UUID (not hardware-based)
- [ ] HTTPS endpoint only
- [ ] Rate limiting respected (max 1 req/hour)

---

## ⏱️ Background Tasks

### Periodic Submission
```python
async def periodic_stats_submission(service: UsageStatisticsService):
    """Submit stats weekly (runs daily, checks if submission needed)."""
    while True:
        try:
            # Check if opted in
            if not await service.is_opted_in():
                await asyncio.sleep(86400)  # 24 hours
                continue

            # Check if submission needed
            last_submission = await service.repository.get_setting(
                "last_submission_date"
            )

            if last_submission:
                last_date = datetime.fromisoformat(last_submission)
                days_since = (datetime.utcnow() - last_date).days

                if days_since >= 7:
                    await service.submit_stats()
            else:
                # First submission
                await service.submit_stats()

        except Exception as e:
            logger.error("Error in periodic submission", error=str(e))

        # Check every 24 hours
        await asyncio.sleep(86400)
```

---

## 🐛 Common Pitfalls

### ❌ DON'T: Include user input in metadata
```python
# BAD!
await stats_service.record_event("search_performed", metadata={
    "search_query": user_query  # ❌ Contains PII!
})

# GOOD!
await stats_service.record_event("search_performed", metadata={
    "query_length": len(user_query)  # ✅ Aggregated only
})
```

### ❌ DON'T: Include file paths in errors
```python
# BAD!
await stats_service.record_event("error_occurred", metadata={
    "error_message": str(exc)  # ❌ May contain file paths!
})

# GOOD!
await stats_service.record_event("error_occurred", metadata={
    "error_type": type(exc).__name__  # ✅ Type only
})
```

### ❌ DON'T: Block on statistics operations
```python
# BAD!
event = await stats_service.record_event(...)
if not event:
    raise Exception("Failed to record stats")  # ❌ Never fail app!

# GOOD!
try:
    await stats_service.record_event(...)
except Exception:
    pass  # ✅ Fail silently, don't break app
```

### ❌ DON'T: Collect data before opt-in check
```python
# BAD!
if await stats_service.is_opted_in():
    # ... but we already collected the data above!

# GOOD! (our design)
# We store locally always (so user can review before opting in)
# But only SUBMIT if opted in
```

---

## 📞 Need Help?

### Privacy Question?
→ Check [Privacy Policy](./usage-statistics-privacy.md)
→ Section: "What We DON'T Collect"

### Implementation Question?
→ Check [Technical Spec](./usage-statistics-technical-spec.md)
→ Section: "Service Layer Implementation"

### Planning Question?
→ Check [Roadmap](./usage-statistics-roadmap.md)
→ Section: "Phase 1 Tasks"

### Architecture Question?
→ Check [Master Plan](./usage-statistics-plan.md)
→ Section: "Architecture Overview"

---

**Remember: When in doubt, DON'T collect it!**

Privacy first, always. ✅
