"""
Printernizer - Professional 3D Print Management System
Main application entry point for production deployment.

Enterprise-grade 3D printer fleet management with configurable compliance features.
"""

import asyncio
import logging
import os
import platform
import signal
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

# Add parent directory to Python path for src imports when running from src/
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from src.api.routers import (
    health_router,
    printers_router,
    jobs_router,
    files_router,
    analytics_router,
    system_router,
    websocket_router,
    settings_router,
    errors_router,
    camera_router
)
from src.api.routers.websocket import broadcast_printer_status
from src.api.routers.ideas import router as ideas_router
from src.api.routers.idea_url import router as idea_url_router
from src.api.routers.trending import router as trending_router
from src.api.routers.debug import router as debug_router
from src.api.routers.library import router as library_router
from src.api.routers.materials import router as materials_router
from src.api.routers.timelapses import router as timelapses_router
from src.api.routers.search import router as search_router
from src.api.routers.usage_statistics import router as usage_statistics_router
from src.api.routers.setup import router as setup_router
from src.api.routers.slicing import router as slicing_router
from src.api.routers.tags import router as tags_router
from src.database.database import Database
from src.services.event_service import EventService
from src.services.config_service import ConfigService
from src.services.printer_service import PrinterService
from src.services.job_service import JobService
from src.services.file_service import FileService
from src.services.file_watcher_service import FileWatcherService
from src.services.usage_statistics_service import UsageStatisticsService
from src.services.usage_statistics_scheduler import UsageStatisticsScheduler
from src.services.migration_service import MigrationService
from src.services.monitoring_service import monitoring_service
from src.services.trending_service import TrendingService
from src.services.thumbnail_service import ThumbnailService
from src.services.url_parser_service import UrlParserService
from src.services.timelapse_service import TimelapseService
from src.utils.logging_config import setup_logging
from src.utils.exceptions import PrinternizerException
from src.utils.errors import (
    PrinternizerError,
    printernizer_exception_handler as new_printernizer_exception_handler,
    generic_exception_handler,
    http_exception_handler
)
from src.utils.middleware import (
    RequestTimingMiddleware,
    GermanComplianceMiddleware,
    SecurityHeadersMiddleware
)
from src.utils.version import get_version
from src.utils.timing import StartupTimer
from src.constants import (
    PortConstants,
    TimeoutConstants,
    ServerConstants
)


# Application version - Automatically extracted from git tags
# Fallback version used when git is unavailable
APP_VERSION = get_version(fallback="2.15.4")


# Prometheus metrics - initialized once
try:
    REQUEST_COUNT = Counter('printernizer_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
    REQUEST_DURATION = Histogram('printernizer_request_duration_seconds', 'Request duration')
    ACTIVE_CONNECTIONS = Counter('printernizer_active_connections', 'Active WebSocket connections')
except ValueError:
    # Metrics already registered (happens during reload)
    from prometheus_client import REGISTRY
    REQUEST_COUNT = REGISTRY._names_to_collectors['printernizer_requests_total']
    REQUEST_DURATION = REGISTRY._names_to_collectors['printernizer_request_duration_seconds']
    ACTIVE_CONNECTIONS = REGISTRY._names_to_collectors['printernizer_active_connections']


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup/shutdown."""
    # Startup
    setup_logging()
    logger = structlog.get_logger()

    # Initialize startup performance timer
    timer = StartupTimer()

    logger.info("=" * 60)
    logger.info("Starting Printernizer application", version=APP_VERSION)
    logger.info("=" * 60)

    # Validate configuration before proceeding
    timer.start("Settings validation")
    logger.info("Validating application settings...")
    from src.utils.config import validate_settings_on_startup, get_settings

    validation_result = validate_settings_on_startup()

    # Log validation results
    if validation_result["info"]:
        for info_msg in validation_result["info"]:
            logger.info(info_msg)

    if validation_result["warnings"]:
        for warning_msg in validation_result["warnings"]:
            logger.warning(warning_msg)

    if not validation_result["valid"]:
        logger.error("=" * 60)
        logger.error("CONFIGURATION VALIDATION FAILED")
        logger.error("=" * 60)
        for error_msg in validation_result["errors"]:
            logger.error(f"  ❌ {error_msg}")
        logger.error("=" * 60)
        logger.error("Please fix the configuration errors above and restart the application.")
        sys.exit(1)

    timer.end("Settings validation")
    logger.info("[OK] Settings validation completed successfully")

    # Initialize database
    timer.start("Database initialization")
    logger.info("Initializing database...")
    settings = get_settings()
    logger.info(f"Database path: {settings.database_path}")
    database = Database(db_path=settings.database_path)
    await database.initialize()
    app.state.database = database
    timer.end("Database initialization")
    logger.info("[OK] Database initialized successfully")

    # Run database migrations
    timer.start("Database migrations")
    logger.info("Running database migrations...")
    migration_service = MigrationService(database)
    await migration_service.run_migrations()
    app.state.migration_service = migration_service
    timer.end("Database migrations")
    logger.info("[OK] Database migrations completed")
    
    # Initialize services
    timer.start("Core services initialization")
    logger.info("Initializing core services...")
    config_service = ConfigService(database=database)
    event_service = EventService()

    # Initialize usage statistics service early (privacy-first telemetry)
    # This needs to be available for other services like JobService
    logger.info("Initializing usage statistics service...")
    usage_statistics_service = UsageStatisticsService(database)
    await usage_statistics_service.initialize()
    # Record app start event
    await usage_statistics_service.record_event("app_start", {
        "app_version": APP_VERSION,
        "python_version": platform.python_version(),
        "platform": platform.system().lower()
    })
    logger.info("[OK] Usage statistics service initialized")

    job_service = JobService(database, event_service, usage_statistics_service)
    printer_service = PrinterService(database, event_service, config_service, usage_stats_service=usage_statistics_service)

    # Inject PrinterService into UsageStatisticsService for fleet stats
    # (done after initialization to avoid circular dependencies)
    usage_statistics_service.set_printer_service(printer_service)

    # Initialize and start usage statistics scheduler (Phase 2)
    logger.info("Starting usage statistics scheduler...")
    usage_statistics_scheduler = UsageStatisticsScheduler(usage_statistics_service)
    await usage_statistics_scheduler.start()
    logger.info("[OK] Usage statistics scheduler started")

    # Initialize camera snapshot service
    from src.services.camera_snapshot_service import CameraSnapshotService
    camera_snapshot_service = CameraSnapshotService(printer_service)
    await camera_snapshot_service.start()

    timer.end("Core services initialization")
    logger.info("[OK] Core services initialized")

    # Initialize Library and Material services in parallel (independent)
    timer.start("Domain services initialization (parallel)")
    logger.info("Initializing library and material services in parallel...")
    from src.services.library_service import LibraryService
    from src.services.material_service import MaterialService

    async def init_library():
        library_service = LibraryService(database, config_service, event_service)
        await library_service.initialize()
        return library_service

    async def init_material():
        material_service = MaterialService(database, event_service)
        await material_service.initialize()
        return material_service

    # Run in parallel
    library_service, material_service = await asyncio.gather(
        init_library(),
        init_material()
    )
    timer.end("Domain services initialization (parallel)")
    logger.info("[OK] Library and material services initialized")

    # Initialize timelapse service
    timer.start("Timelapse service initialization")
    logger.info("Initializing timelapse service...")
    timelapse_service = TimelapseService(database, event_service)
    timer.end("Timelapse service initialization")
    logger.info("[OK] Timelapse service initialized")

    # Initialize file watcher and ideas services in parallel (independent)
    timer.start("File system & ideas services initialization (parallel)")
    logger.info("Initializing file watcher and ideas services in parallel...")

    async def init_file_watcher():
        return FileWatcherService(config_service, event_service, library_service)

    async def init_ideas_services():
        return ThumbnailService(event_service), UrlParserService()

    # Run in parallel
    (file_watcher_service, (thumbnail_service, url_parser_service)) = await asyncio.gather(
        init_file_watcher(),
        init_ideas_services()
    )
    timer.end("File system & ideas services initialization (parallel)")
    logger.info("[OK] File watcher and ideas services initialized")

    # Initialize file service (depends on file_watcher)
    timer.start("File service initialization")
    logger.info("Initializing file service...")
    file_service = FileService(database, event_service, file_watcher_service, printer_service, config_service, library_service, usage_statistics_service)
    await file_service.initialize()  # Initialize event subscriptions
    timer.end("File service initialization")
    logger.info("[OK] File service initialized")

    # Set file service reference in printer service for circular dependency
    printer_service.file_service = file_service

    # Set job service and config service in monitoring service for auto-job creation
    printer_service.monitoring.set_job_service(job_service)
    printer_service.monitoring.set_config_service(config_service)

    # Initialize TrendingService (re-enabled in master)
    timer.start("Trending service initialization")
    logger.info("Initializing trending service...")
    trending_service = TrendingService(database, event_service)
    await trending_service.initialize()
    timer.end("Trending service initialization")
    logger.info("[OK] Trending service initialized")

    # Initialize slicer services
    timer.start("Slicer services initialization")
    logger.info("Initializing slicer services...")
    from src.services.slicer_service import SlicerService
    from src.services.slicing_queue import SlicingQueue
    
    slicer_service = SlicerService(database, event_service)
    await slicer_service.initialize()
    
    slicing_queue = SlicingQueue(
        database,
        event_service,
        slicer_service,
        file_service=file_service,
        printer_service=printer_service,
        library_service=library_service
    )
    await slicing_queue.initialize()
    
    timer.end("Slicer services initialization")
    logger.info("[OK] Slicer services initialized")

    app.state.config_service = config_service
    app.state.event_service = event_service
    app.state.job_service = job_service
    app.state.printer_service = printer_service
    app.state.file_service = file_service
    app.state.file_watcher_service = file_watcher_service
    app.state.thumbnail_service = thumbnail_service
    app.state.url_parser_service = url_parser_service
    app.state.trending_service = trending_service
    app.state.library_service = library_service
    app.state.material_service = material_service
    app.state.timelapse_service = timelapse_service
    app.state.usage_statistics_service = usage_statistics_service
    app.state.usage_statistics_scheduler = usage_statistics_scheduler
    app.state.camera_snapshot_service = camera_snapshot_service
    app.state.slicer_service = slicer_service
    app.state.slicing_queue = slicing_queue

    # Initialize and start background services in parallel
    timer.start("Background services startup (parallel)")
    logger.info("Starting background services in parallel...")
    await asyncio.gather(
        event_service.start(),
        printer_service.initialize(),
        timelapse_service.start(),
    )
    timer.end("Background services startup (parallel)")
    logger.info("[OK] Background services started")

    # Subscribe WebSocket broadcast for individual printer status updates (includes thumbnails)
    async def _on_printer_status_update(data):
        try:
            # data contains printer_id and status fields
            await broadcast_printer_status(
                printer_id=data.get("printer_id"),
                status_data=data
            )
        except Exception as e:
            logger.warning("Failed to broadcast printer status update", error=str(e))

    event_service.subscribe("printer_status_update", _on_printer_status_update)

    # Initialize Ideas-related services
    # logger.info("Starting trending service...")  # DISABLED
    # await trending_service.initialize()  # DISABLED
    # logger.info("[OK] Trending service started")  # DISABLED

    # Start printer monitoring and file watcher in parallel
    timer.start("Monitoring services startup (parallel)")
    logger.info("Starting printer monitoring and file watcher in parallel...")

    async def start_printer_monitoring():
        try:
            await printer_service.start_monitoring()
            logger.info("[OK] Printer monitoring started successfully")
        except Exception as e:
            logger.warning("[WARNING] Failed to start printer monitoring", error=str(e))

    async def start_file_watcher():
        try:
            await file_watcher_service.start()
            logger.info("[OK] File watcher service started successfully")
        except Exception as e:
            logger.warning("[WARNING] Failed to start file watcher service", error=str(e))

    # Run in parallel
    await asyncio.gather(
        start_printer_monitoring(),
        start_file_watcher()
    )
    timer.end("Monitoring services startup (parallel)")

    # Initialize empty list for discovered printers
    app.state.startup_discovered_printers = []

    # Optional: Schedule automatic printer discovery to run after startup delay
    if os.getenv("DISCOVERY_RUN_ON_STARTUP", "true").lower() == "true":
        delay_seconds = int(os.getenv("DISCOVERY_STARTUP_DELAY_SECONDS", str(TimeoutConstants.DISCOVERY_STARTUP_DELAY_SECONDS)))
        logger.info(f"Automatic printer discovery scheduled to run in {delay_seconds} seconds")

        async def delayed_discovery():
            """Run printer discovery after startup delay."""
            try:
                # Wait for the configured delay
                await asyncio.sleep(delay_seconds)

                logger.info("Starting automatic printer discovery (delayed startup)")

                # Import discovery service
                try:
                    from src.services.discovery_service import DiscoveryService

                    # Get timeout from config
                    timeout = int(os.getenv("DISCOVERY_TIMEOUT_SECONDS", str(TimeoutConstants.DISCOVERY_TIMEOUT_SECONDS)))
                    discovery_service = DiscoveryService(timeout=timeout)

                    # Get configured printer IPs for duplicate detection
                    printers = await printer_service.list_printers()
                    configured_ips = [p.ip_address for p in printers if p.ip_address]

                    # Run discovery
                    results = await discovery_service.discover_all(
                        interface=None,
                        configured_ips=configured_ips,
                        scan_subnet=True  # Full scan for best results
                    )

                    # Store discovered printers in app state for dashboard display
                    app.state.startup_discovered_printers = results.get('discovered', [])

                    discovered_count = len(results.get('discovered', []))
                    new_count = sum(1 for p in results.get('discovered', []) if not p.get('already_added', False))

                    if discovered_count > 0:
                        logger.info(f"[OK] Automatic discovery found {discovered_count} printers ({new_count} new)",
                                  discovered_count=discovered_count,
                                  new_count=new_count,
                                  duration_ms=results.get('scan_duration_ms'))
                    else:
                        logger.info("[OK] Automatic discovery completed (no printers found)")

                except ImportError:
                    logger.warning("[WARNING] Discovery service not available (netifaces not installed)")
                    app.state.startup_discovered_printers = []

            except Exception as e:
                logger.warning("[WARNING] Automatic printer discovery failed", error=str(e))
                app.state.startup_discovered_printers = []

        # Start discovery as background task (don't await it)
        asyncio.create_task(delayed_discovery())

    # Generate startup performance report
    timer.report()

    # Server ready confirmation with useful connection information
    port = os.getenv("PORT", str(PortConstants.DEFAULT_API_PORT))
    logger.info("=" * 60)
    logger.info("🚀 PRINTERNIZER BACKEND READY")
    logger.info(f"Server is accepting connections at http://0.0.0.0:{port}")
    logger.info(f"API documentation available at http://0.0.0.0:{port}/docs")
    logger.info(f"Health check endpoint: http://0.0.0.0:{port}/api/v1/health")
    if os.getenv("DISABLE_RELOAD") == "true":
        logger.info("⚡ Fast startup mode (reload disabled)")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown with proper error handling and timeouts
    logger.info("Shutting down Printernizer gracefully")
    shutdown_timeout = TimeoutConstants.SHUTDOWN_TIMEOUT_SECONDS  # seconds

    async def shutdown_with_timeout(coro, service_name: str, timeout: float = TimeoutConstants.SERVICE_SHUTDOWN_TIMEOUT_SECONDS):
        """Execute shutdown coroutine with timeout."""
        try:
            await asyncio.wait_for(coro, timeout=timeout)
            logger.info(f"{service_name} stopped successfully")
        except asyncio.TimeoutError:
            logger.warning(f"{service_name} shutdown timed out after {timeout}s")
        except Exception as e:
            logger.warning(f"Error stopping {service_name}", error=str(e))

    # Shutdown services in parallel where possible
    shutdown_tasks = []

    # Printer service shutdown
    if hasattr(app.state, 'printer_service') and app.state.printer_service:
        shutdown_tasks.append(
            shutdown_with_timeout(
                app.state.printer_service.shutdown(),
                "Printer service",
                timeout=TimeoutConstants.PRINTER_SERVICE_SHUTDOWN_TIMEOUT_SECONDS
            )
        )

    # File watcher service
    if hasattr(app.state, 'file_watcher_service') and app.state.file_watcher_service:
        shutdown_tasks.append(
            shutdown_with_timeout(
                app.state.file_watcher_service.stop(),
                "File watcher service",
                timeout=TimeoutConstants.SERVICE_SHUTDOWN_TIMEOUT_SECONDS
            )
        )

    # Trending service
    if hasattr(app.state, 'trending_service') and app.state.trending_service:
        shutdown_tasks.append(
            shutdown_with_timeout(
                app.state.trending_service.cleanup(),
                "Trending service",
                timeout=TimeoutConstants.SERVICE_SHUTDOWN_TIMEOUT_SECONDS
            )
        )

    # Thumbnail service
    if hasattr(app.state, 'thumbnail_service') and app.state.thumbnail_service:
        shutdown_tasks.append(
            shutdown_with_timeout(
                app.state.thumbnail_service.cleanup(),
                "Thumbnail service",
                timeout=TimeoutConstants.SERVICE_SHUTDOWN_TIMEOUT_SECONDS
            )
        )

    # URL parser service
    if hasattr(app.state, 'url_parser_service') and app.state.url_parser_service:
        shutdown_tasks.append(
            shutdown_with_timeout(
                app.state.url_parser_service.close(),
                "URL parser service",
                timeout=TimeoutConstants.SERVICE_SHUTDOWN_TIMEOUT_SECONDS
            )
        )

    # Usage statistics scheduler
    if hasattr(app.state, 'usage_statistics_scheduler') and app.state.usage_statistics_scheduler:
        shutdown_tasks.append(
            shutdown_with_timeout(
                app.state.usage_statistics_scheduler.stop(),
                "Usage statistics scheduler",
                timeout=TimeoutConstants.SERVICE_SHUTDOWN_TIMEOUT_SECONDS
            )
        )

    # Timelapse service
    if hasattr(app.state, 'timelapse_service') and app.state.timelapse_service:
        shutdown_tasks.append(
            shutdown_with_timeout(
                app.state.timelapse_service.shutdown(),
                "Timelapse service",
                timeout=TimeoutConstants.SERVICE_SHUTDOWN_TIMEOUT_SECONDS
            )
        )

    # Camera snapshot service
    if hasattr(app.state, 'camera_snapshot_service') and app.state.camera_snapshot_service:
        shutdown_tasks.append(
            shutdown_with_timeout(
                app.state.camera_snapshot_service.shutdown(),
                "Camera snapshot service",
                timeout=TimeoutConstants.SERVICE_SHUTDOWN_TIMEOUT_SECONDS
            )
        )

    # Slicing queue
    if hasattr(app.state, 'slicing_queue') and app.state.slicing_queue:
        shutdown_tasks.append(
            shutdown_with_timeout(
                app.state.slicing_queue.shutdown(),
                "Slicing queue",
                timeout=TimeoutConstants.SERVICE_SHUTDOWN_TIMEOUT_SECONDS
            )
        )

    # Execute all service shutdowns in parallel
    if shutdown_tasks:
        await asyncio.gather(*shutdown_tasks, return_exceptions=True)

    # Stop event service (depends on other services)
    if hasattr(app.state, 'event_service') and app.state.event_service:
        await shutdown_with_timeout(
            app.state.event_service.stop(),
            "Event service",
            timeout=TimeoutConstants.SERVICE_SHUTDOWN_TIMEOUT_SECONDS
        )

    # Close database connection last
    if hasattr(app.state, 'database') and app.state.database:
        await shutdown_with_timeout(
            app.state.database.close(),
            "Database",
            timeout=TimeoutConstants.SERVICE_SHUTDOWN_TIMEOUT_SECONDS
        )

    logger.info("Printernizer shutdown complete")


def create_application() -> FastAPI:
    """Create FastAPI application with production configuration."""
    
    # Initialize settings to get configuration
    from src.services.config_service import Settings
    settings = Settings()
    
    app = FastAPI(
        title="Printernizer API",
        description="Professional 3D Print Management System for Bambu Lab & Prusa Printers",
        version=APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc/bundles/redoc.standalone.js",  # Use stable version instead of @next
        lifespan=lifespan,
        redirect_slashes=False  # Disable automatic trailing slash redirects to fix API routing with StaticFiles
    )
    
    # CORS Configuration
    cors_origins = settings.get_cors_origins()
    # Add additional origins for development
    if settings.environment == "development":
        cors_origins.extend([
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://192.168.176.159:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://192.168.176.159:8000"
        ])
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )
    
    # Path normalization middleware for Home Assistant Ingress
    # HA Ingress sometimes creates double slashes in paths which cause 404 errors
    if os.getenv("HA_INGRESS") == "true":
        import re
        logger = structlog.get_logger()
        
        @app.middleware("http")
        async def normalize_path_middleware(request: Request, call_next):
            """Normalize paths by collapsing double slashes (common HA Ingress issue)."""
            original_path = request.scope.get("path", "")
            
            # Log all incoming requests for debugging HA Ingress issues
            logger.info(
                "HA Ingress request received",
                path=original_path,
                method=request.method,
                url=str(request.url)
            )
            
            # Collapse multiple consecutive slashes into single slash
            # But preserve the leading slash
            if "//" in original_path:
                normalized_path = re.sub(r'/+', '/', original_path)
                # Ensure leading slash is preserved
                if not normalized_path.startswith('/'):
                    normalized_path = '/' + normalized_path
                    
                logger.info(
                    "Normalized request path (double slash detected)",
                    original=original_path,
                    normalized=normalized_path
                )
                # Update both path and raw_path in the scope
                request.scope["path"] = normalized_path
                # raw_path is bytes, encode the normalized path
                request.scope["raw_path"] = normalized_path.encode("utf-8")
            
            return await call_next(request)
        
        logger.info("Path normalization middleware enabled for HA Ingress")
    
    # Home Assistant Ingress security middleware (only active when HA_INGRESS=true)
    if os.getenv("HA_INGRESS") == "true":
        logger = structlog.get_logger()
        logger.info("Home Assistant Ingress mode enabled - trusting HA authentication")

        @app.middleware("http")
        async def ingress_security_middleware(request: Request, call_next):
            """Log requests in HA Ingress mode but allow all (HA handles auth)."""
            client_ip = request.client.host if request.client else None

            # In HA Ingress mode, Home Assistant already handles authentication
            # and security before forwarding requests to the add-on.
            # We trust HA's authentication and don't need additional IP restrictions.
            # Just log the request for debugging purposes.
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "HA Ingress request",
                    client_ip=client_ip,
                    path=request.url.path,
                    method=request.method
                )

            return await call_next(request)

    # Security and compliance middleware
    # Skip middlewares during testing to avoid BaseHTTPMiddleware issues with TestClient
    # Check if pytest is running by looking for pytest in sys.modules
    import sys
    is_testing = 'pytest' in sys.modules or os.getenv("TESTING") == "true"
    if not is_testing:
        app.add_middleware(SecurityHeadersMiddleware)
        app.add_middleware(GermanComplianceMiddleware)
        app.add_middleware(RequestTimingMiddleware)
    
    # API Routes
    app.include_router(health_router, prefix="/api/v1", tags=["Health"])
    app.include_router(printers_router, prefix="/api/v1/printers", tags=["Printers"])
    app.include_router(camera_router, prefix="/api/v1/printers", tags=["Camera"])
    app.include_router(jobs_router, prefix="/api/v1/jobs", tags=["Jobs"])
    app.include_router(files_router, prefix="/api/v1/files", tags=["Files"])
    app.include_router(library_router, prefix="/api/v1", tags=["Library"])  # New library system
    app.include_router(materials_router, prefix="/api/v1", tags=["Materials"])  # Material management
    app.include_router(timelapses_router, prefix="/api/v1/timelapses", tags=["Timelapses"])  # Timelapse management
    app.include_router(analytics_router, prefix="/api/v1", tags=["Analytics"])
    app.include_router(ideas_router, prefix="/api/v1", tags=["Ideas"])
    app.include_router(idea_url_router, prefix="/api/v1", tags=["Ideas-URL"])
    app.include_router(trending_router, prefix="/api/v1", tags=["Trending"])
    app.include_router(search_router, prefix="/api/v1/search", tags=["Search"])
    app.include_router(system_router, prefix="/api/v1/system", tags=["System"])
    app.include_router(settings_router, prefix="/api/v1/settings", tags=["Settings"])
    app.include_router(setup_router, prefix="/api/v1/setup", tags=["Setup"])
    app.include_router(errors_router, prefix="/api/v1/errors", tags=["Error Reporting"])
    app.include_router(usage_statistics_router, prefix="/api/v1/usage-stats", tags=["Usage Statistics"])
    app.include_router(slicing_router, prefix="/api/v1/slicing", tags=["Slicing"])
    app.include_router(tags_router, prefix="/api/v1", tags=["Tags"])  # File tagging system
    app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])
    # Temporary debug endpoints (remove before production if not needed)
    app.include_router(debug_router, prefix="/api/v1/debug", tags=["Debug"])
    
    # Static files and frontend
    frontend_path = Path(__file__).parent.parent / "frontend"
    if frontend_path.exists():
        logger = structlog.get_logger()
        logger.info("Mounting frontend static files", path=str(frontend_path))

        # Serve specific HTML files first
        @app.get("/")
        async def read_index():
            from fastapi.responses import FileResponse
            return FileResponse(str(frontend_path / "index.html"))

        # Handle Home Assistant Ingress double-slash issue
        # HA Ingress sometimes forwards requests as // instead of /
        # REDIRECT to single slash to fix relative path resolution in browser
        @app.get("//")
        async def redirect_double_slash():
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/", status_code=301)

        @app.get("/debug")
        async def read_debug():
            from fastapi.responses import FileResponse
            return FileResponse(str(frontend_path / "debug.html"))

        # Mount static files at root for proper resource loading
        # This must be done AFTER all API routes and specific routes are registered
        # so that API routes take precedence
        app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

        logger.info("Frontend routes configured successfully")
    
    # Prometheus metrics endpoint
    @app.get("/metrics")
    async def metrics():
        from fastapi.responses import Response
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    
    # Global exception handlers - Phase 3 Standardized Error Handling

    # New standardized PrinternizerError handler (Phase 3)
    app.add_exception_handler(PrinternizerError, new_printernizer_exception_handler)

    # Legacy PrinternizerException handler (backwards compatibility)
    # NOTE: Still needed - many exceptions inherit from PrinternizerException
    # (PrinterConnectionError, NotFoundError, etc. in src/utils/exceptions.py)
    # TODO: Migrate all exceptions to inherit from PrinternizerError (src/utils/errors.py)
    @app.exception_handler(PrinternizerException)
    async def legacy_printernizer_exception_handler(request: Request, exc: PrinternizerException):
        logger = structlog.get_logger()
        logger.error(
            "Legacy Printernizer exception",
            error_code=exc.error_code,
            status_code=exc.status_code,
            message=exc.message,
            path=request.url.path,
            method=request.method
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "error_code": exc.error_code,  # Fixed: was "error" (inconsistent with new format)
                "message": exc.message,
                "details": exc.details,
                "timestamp": exc.timestamp.isoformat()
            }
        )

    # HTTPException handler (converts FastAPI HTTPExceptions to standard format)
    app.add_exception_handler(HTTPException, http_exception_handler)

    # Request validation error handler (Pydantic validation errors)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger = structlog.get_logger()
        logger.warning("Validation error", errors=exc.errors(), path=request.url.path)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "status": "error",
                "message": "Request validation failed",
                "error_code": "VALIDATION_ERROR",
                "details": {"validation_errors": exc.errors()},
                "timestamp": datetime.now().isoformat()
            }
        )

    # Generic exception handler (catches all unhandled exceptions) - Must be last
    app.add_exception_handler(Exception, generic_exception_handler)
    
    return app


def setup_signal_handlers():
    """Setup graceful shutdown signal handlers."""
    def signal_handler(signum, frame):
        logger = structlog.get_logger()
        logger.info("Received shutdown signal", signal=signum)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


app = create_application()


if __name__ == "__main__":
    # Production server configuration
    setup_signal_handlers()

    port = int(os.getenv("PORT", str(PortConstants.DEFAULT_API_PORT)))
    host = "0.0.0.0"

    config = {
        "host": host,
        "port": port,
        "workers": ServerConstants.UVICORN_WORKERS,  # Force single worker to avoid database initialization conflicts
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),  # Normalize to lowercase for uvicorn
        "access_log": True,
        "use_colors": False,
        "server_header": False,
        "date_header": False
    }

    # Development mode configuration with reload optimizations
    if os.getenv("ENVIRONMENT") == "development":
        # Allow disabling reload for faster startup when needed
        use_reload = os.getenv("DISABLE_RELOAD", "false").lower() != "true"

        config.update({
            "reload": use_reload,
            "reload_dirs": ["src"] if use_reload else [],
            "reload_excludes": [
                "*.db",           # SQLite database files
                "*.db-journal",   # Database journals
                "*.db-shm",       # Shared memory files
                "*.db-wal",       # Write-ahead log files
                "*.log",          # Log files
                "__pycache__",    # Python cache directories
                "*.pyc",          # Compiled Python files
                ".pytest_cache",  # Test cache
                "frontend/*",     # Frontend static files
                "*/downloads/*",  # Downloads directory
            ],
            "workers": 1
        })

    # Log server startup
    logger = structlog.get_logger()
    logger.info("=" * 60)
    logger.info("STARTING UVICORN SERVER")
    logger.info(f"Listening on: http://{host}:{port}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'production')}")
    logger.info(f"Deployment Mode: {os.getenv('DEPLOYMENT_MODE', 'standalone')}")
    if os.getenv("HA_INGRESS") == "true":
        logger.info("Home Assistant Ingress: ENABLED")
    logger.info("=" * 60)

    uvicorn.run("src.main:app", **config)