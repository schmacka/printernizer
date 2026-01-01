# Copilot Instructions for Printernizer

**Printernizer** is a professional 3D printer fleet management system for Bambu Lab A1 and Prusa Core One printers. Python/FastAPI backend with vanilla JS frontend, targeting SMB/prosumer 3D printing operations with German compliance features.

## Architecture & Core Components

### Service Layer Pattern
All core logic lives in `/src/services/` with consistent initialization:
```python
class SomeService:
    def __init__(self, database: Database, event_service: EventService, ...):
        # Dependency injection pattern
    
    async def initialize(self):
        # Async initialization after instantiation
```

**Key Services:**
- `PrinterService` - Printer connection & monitoring (MQTT for Bambu, HTTP for Prusa)
- `JobService` - Print job tracking with business metadata
- `FileService` - File management with auto-download & library integration
- `LibraryService` - Centralized 3D model storage with deduplication
- `MaterialService` - Filament spool inventory tracking
- `EventService` - Pub/sub event system for cross-service communication
- `ConfigService` - Manages `config/printers.json` and settings

### Database Layer
- **SQLite** with `aiosqlite` for async operations
- Schema in `database_schema.sql`, applied via `Database._create_tables()`
- Migrations in `migrations/*.sql`, auto-run on startup by `MigrationService`
- Always use parameterized queries: `await cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))`

### API Routing - CRITICAL PATTERN
```python
# ✅ CORRECT - No trailing slash routes
@router.get("")          # GET /api/v1/resource
@router.post("")         # POST /api/v1/resource  
@router.get("/{id}")     # GET /api/v1/resource/123

# ❌ WRONG - Will cause 405 errors
@router.get("/")         # FastAPI has redirect_slashes=False
```
**Why:** Root path `/` is reserved for StaticFiles. All API routes use empty string `""` for resource root.

### Printer Integration
- Base class: `BasePrinter` in `src/printers/base.py`
- Implementations: `BambuLabPrinter` (MQTT), `PrusaPrinter` (HTTP polling)
- Status updates flow: Printer → callback → `PrinterService._handle_status_update()` → EventService → WebSocket broadcast
- File operations: Printers use FTP (`BambuFTPService`) or HTTP (`PrusaFileClient`)

## Development Workflows

### Environment Configuration
Set via `ENVIRONMENT` env var in `.env` or `run.bat`:
- **development**: Verbose logging (`LOG_LEVEL=DEBUG`), detailed errors, development CORS
- **production**: JSON logging (`LOG_LEVEL=INFO`), generic errors, strict security headers

Start server: `run.bat` (Windows) or `./run.sh` (Linux) → launches `python -m src.main`

### Testing
```bash
pytest                           # All tests
pytest tests/backend/           # Backend only
pytest --cov=src tests/         # With coverage
```
Tests in `tests/backend/` use pytest fixtures. Mock printer services for integration tests.

### Database Changes
1. Create migration: `migrations/XXX_description.sql`
2. `MigrationService` auto-runs on startup (tracks in `migrations` table)
3. Always test up/down migrations locally

### Code Sync for Home Assistant Add-on
**Home Assistant add-on is maintained in a separate repository**: [printernizer-ha](https://github.com/schmacka/printernizer-ha)
- Code automatically syncs via GitHub Actions workflow `.github/workflows/sync-to-ha-repo.yml`
- Always edit source: `/src/` and `/frontend/` in this repository
- Push to `master` or `development` branch triggers automatic sync to printernizer-ha

## Key Conventions

### Structured Logging
```python
import structlog
logger = structlog.get_logger()
logger.info("Operation completed", printer_id=printer_id, duration=elapsed)
```
Use key-value context instead of string formatting. Outputs JSON in production.

### Error Handling
- Custom exceptions in `src/utils/exceptions.py`: `PrinterConnectionError`, `NotFoundError`, etc.
- API errors return standardized JSON: `{"error": "message", "detail": {...}}`
- Use HTTP status codes correctly: 404 for not found, 503 for service unavailable

### Async Patterns
- All I/O is async: `await cursor.execute()`, `await printer.connect()`
- Use `asyncio.create_task()` for fire-and-forget background work
- Lifecycle: `lifespan()` context manager in `main.py` handles startup/shutdown

### Business Requirements (German Compliance)
- **is_business** flag on jobs distinguishes business orders from private prints
- VAT calculations, cost tracking per job
- Data retention: 7 years for business records (GDPR compliant)
- Timezone: `Europe/Berlin`, Currency: `EUR`

## Frontend Integration

### Static Frontend
- Vanilla JS (no framework) in `/frontend/js/`
- Served by FastAPI `StaticFiles` at root `/`
- API calls to `/api/v1/...` endpoints
- Real-time updates via WebSocket at `/ws`

### WebSocket Protocol
```javascript
ws = new WebSocket('ws://localhost:8000/ws');
// Server pushes: {"type": "printer_status_update", "data": {...}}
```
Broadcast function: `broadcast_printer_status()` in `src/api/routers/websocket.py`

## Common Gotchas

1. **Circular Dependencies**: Services with circular deps (e.g., `PrinterService` ↔ `FileService`) use post-init assignment:
   ```python
   printer_service.file_service = file_service  # After both initialized
   ```

2. **File Operations**: Auto-download for active jobs configured per-printer. Track attempts in `PrinterService._auto_download_attempts` to avoid loops.

3. **Event Subscriptions**: Use `EventService.subscribe(event_type, callback)` for loose coupling. Emit with `event_service.emit(event_type, data)`.

4. **Printer Discovery**: Optional (requires `netifaces`). Endpoints return 503 if unavailable. Code wrapped in try/except imports.

5. **Thumbnail Extraction**: 3D files (STL, 3MF, GCODE) have embedded thumbnails extracted by `ThumbnailService`. Cached in `data/thumbnails/`.

## Version Management
- Version defined in `src/utils/version.py` (reads git tags, fallback in `main.py`)
- Keep synced:
  - `src/api/routers/health.py` - API version response
  - `CHANGELOG.md` - User-facing changes
- Home Assistant add-on version in `printernizer-ha/config.yaml` is automatically synced from `src/main.py`

## Deployment Modes
1. **Python Standalone**: `run.bat` → Local development/testing
2. **Docker**: `docker-compose.yml` → Production single-container
3. **Home Assistant Add-on**: [printernizer-ha repository](https://github.com/schmacka/printernizer-ha) → Supervised HA environment

Check mode via `os.getenv("DEPLOYMENT_MODE")` if behavior differs.

## When Making Changes

1. **Adding API Endpoints**: Follow router pattern in `/src/api/routers/`, use empty string for root routes
2. **Adding Services**: Inherit from `BaseService`, implement `initialize()`, inject via `main.py` lifespan
3. **Database Schema**: Create migration file, test thoroughly (no rollback in SQLite)
4. **Printer Support**: Subclass `BasePrinter`, implement abstract methods, add to `PrinterService._create_printer_instance()`
5. **UI Changes**: Edit `/frontend/` directly (HTML/CSS/JS), API integration via fetch to `/api/v1/...`

## Reference Documentation
- Architecture deep-dive: `CLAUDE.md` + `.claude/skills/` directory
- API spec: `docs/api_specification.md`
- Testing guide: `docs/TESTING_GUIDE.md`
- Deployment: `docs/PRODUCTION_DEPLOYMENT.md`
