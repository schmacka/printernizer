# Copilot Instructions – Printernizer

Purpose: Make AI agents immediately productive in this repo by following existing patterns, workflows, and integration rules. For tone and broader context, also see `CLAUDE.md` and docs in `docs/`.

## Big Picture
- **Architecture:** FastAPI app (`src/main.py`) with routers (`src/api/routers/*`), async services (`src/services/*`), printer drivers (`src/printers/*`), SQLite via aiosqlite (`src/database/*`), and a static frontend (`frontend/`).
- **Data Flow:** Drivers push status → `PrinterService` → `EventService.emit_event("printer_status_update", …)` → WebSocket clients; file events → `FileWatcherService` → `FileService` → thumbnails/metadata via `BambuParser`; DB migrations run at startup.
- **Why structured this way:** Clear service boundaries, non-blocking async loops, explicit drivers per vendor, and centralized eventing simplify realtime monitoring and error isolation.

## Core Workflows
- **Run (dev):** install deps `pip install -r requirements.txt`; set `ENVIRONMENT=development`; start `python src/main.py` (Uvicorn config inside `__main__`, single worker enforced).
- **Tests (essential):** `python tests/run_essential_tests.py [-v|--coverage]`. For printer-focused tests: `python tests/run_milestone_1_2_tests.py`.
- **Docker (dev):** `docker-compose up -d` (see `docker-compose.dev.yml`). Data in `data/printernizer.db`.

## Conventions & Patterns
- **Async-first:** Routers call services; services do I/O. Use `async`/`await` and `asyncio.create_task(...)` for background work; never block the event loop (no long CPU work inline).
- **Logging:** Use `structlog` everywhere: `logger = structlog.get_logger(); logger.info("msg", key=value)`. No `print()`.
- **Errors:** Raise `PrinternizerException` (or specific subclasses) from `src/utils/exceptions.py`. Global handlers in `src/main.py` convert to JSON.
- **Routers:** One file per resource (e.g., `health.py`, `printers.py`). Register via `app.include_router(...)` in `create_application()` with the correct `prefix` and tag.
- **Models/DTOs:** Pydantic v2 models in `src/models/*`. See `docs/data_models.md` for canonical fields/enums.
- **Metrics:** Prometheus at `/metrics`; counters/histograms are created once in `src/main.py`.

## Integrations
- **Bambu Lab (A1):** MQTT via `paho-mqtt` directly to printer (`port 8883`, user `bblp`, password=`access_code`). Driver: `src/printers/bambu_lab.py` subscribes `device/{serial}/report`. Test credentials with `scripts/test_bambu_credentials.*` and `scripts/quick_bambu_check.py`.
- **Prusa Core One:** HTTP via PrusaLink API using `api_key`. Driver: `src/printers/prusa.py`. Polling intervals are handled in `EventService` and driver monitor loops.
- **Polling & Backoff:** Base monitor loop in `BasePrinter` uses 30s default with exponential backoff and jitter; emit updates via status callbacks.

## Database & Config
- **DB:** Async SQLite (`aiosqlite`). Use `Database` instance from `app.state.database`; do not instantiate raw sqlite3 connections. Migrations live in `migrations/` and are applied by `MigrationService` at startup.
- **Config:** `ConfigService` loads printers (see `config/printers.json` and env patterns like `PRINTERNIZER_PRINTER_*`). CORS/dev settings resolved in `Settings` used in `create_application()`.

## Extending Safely (examples)
- **New API endpoint:** create `src/api/routers/feature.py` with an `APIRouter`; access services via dependencies (`get_config_service`, `get_database`); register in `create_application()` with a versioned prefix (e.g., `/api/v1/feature`).
- **New printer type:** subclass `BasePrinter`, implement connect/status/jobs/files; map it in `PrinterService._create_printer_instance`; ensure status callbacks call `_handle_status_update` (already wired by service).
- **Emit realtime updates:** use `await event_service.emit_event(event_name, payload)`; follow existing shapes (see `_handle_status_update` in `PrinterService`).
- **File processing:** route file events to `FileService.process_file_thumbnails(...)`; heavy parsing runs in background tasks created by services.

## Pointers
- Key files: `src/main.py`, `src/api/routers/health.py`, `src/services/printer_service.py`, `src/services/event_service.py`, `src/services/file_service.py`, `src/printers/base.py`, `src/printers/bambu_lab.py`, `src/printers/prusa.py`, `src/utils/exceptions.py`.
- API contract: `docs/api_specification.md`; data contracts: `docs/data_models.md`.
- Keep one Uvicorn worker (DB init depends on it). Respect German compliance middleware and settings when touching auth/headers/timezones.

## Gotchas
- **Single worker only:** `src/main.py` enforces 1 worker; multiple workers break DB init and background tasks.
- **Don’t block the loop:** Heavy CPU or file parsing must run in background tasks; rely on services’ `asyncio.create_task(...)` patterns.
- **Windows PowerShell:** Use backticks or quotes carefully; chain commands with `;` (e.g., `setx ENVIRONMENT development ; python src/main.py`).
- **MQTT timing:** Bambu MQTT needs a few seconds after `connect()` before status data is present; drivers already `sleep(3)`.
- **CORS/dev origins:** `Settings` appends dev origins; update via env/config instead of hardcoding in routers.
- **Prometheus metrics:** Declare once. Reuse collectors from `REGISTRY` to avoid duplicate registration on reload.

## Minimal Router Example
Create `src/api/routers/example.py`:

```python
from fastapi import APIRouter, Depends
from src.utils.dependencies import get_database

router = APIRouter()

@router.get("/ping")
async def ping(db = Depends(get_database)):
	# ... use db or services via dependencies
	return {"status": "ok"}
```

Register in `create_application()` (in `src/main.py`):

```python
from src.api.routers import example as example_router

app.include_router(example_router.router, prefix="/api/v1/example", tags=["Example"])
```
