"""
Printernizer - Professional 3D Print Management System
Main application entry point for production deployment.

Enterprise-grade 3D printer fleet management with configurable compliance features.
"""

import asyncio
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Add parent directory to Python path for src imports when running from src/
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import structlog
import uvicorn
from fastapi import FastAPI, Request, status
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
from src.database.database import Database
from src.services.event_service import EventService
from src.services.config_service import ConfigService
from src.services.printer_service import PrinterService
from src.services.file_service import FileService
from src.services.file_watcher_service import FileWatcherService
from src.services.migration_service import MigrationService
from src.services.monitoring_service import monitoring_service
from src.services.trending_service import TrendingService
from src.services.thumbnail_service import ThumbnailService
from src.services.url_parser_service import UrlParserService
from src.utils.logging_config import setup_logging
from src.utils.exceptions import PrinternizerException
from src.utils.middleware import (
    RequestTimingMiddleware,
    GermanComplianceMiddleware,
    SecurityHeadersMiddleware
)
from src.utils.version import get_version


# Application version - Automatically extracted from git tags
# Fallback version used when git is unavailable
APP_VERSION = get_version(fallback="1.5.6")


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
    logger.info("Starting Printernizer application", version=APP_VERSION)
    
    # Initialize database
    database = Database()
    await database.initialize()
    app.state.database = database
    
    # Run database migrations
    migration_service = MigrationService(database)
    await migration_service.run_migrations()
    app.state.migration_service = migration_service
    
    # Initialize services
    config_service = ConfigService(database=database)
    event_service = EventService()
    printer_service = PrinterService(database, event_service, config_service)

    # Initialize Library service (before file_watcher so it can use it)
    from src.services.library_service import LibraryService
    library_service = LibraryService(database, config_service, event_service)
    await library_service.initialize()

    # Initialize file watcher service with library integration
    file_watcher_service = FileWatcherService(config_service, event_service, library_service)

    # Initialize file service with file watcher, printer service, config service, and library
    file_service = FileService(database, event_service, file_watcher_service, printer_service, config_service, library_service)

    # Set file service reference in printer service for circular dependency
    printer_service.file_service = file_service

    # Initialize Ideas-related services
    thumbnail_service = ThumbnailService(event_service)
    url_parser_service = UrlParserService()
    trending_service = TrendingService(database, event_service)

    app.state.config_service = config_service
    app.state.event_service = event_service
    app.state.printer_service = printer_service
    app.state.file_service = file_service
    app.state.file_watcher_service = file_watcher_service
    app.state.thumbnail_service = thumbnail_service
    app.state.url_parser_service = url_parser_service
    app.state.trending_service = trending_service
    app.state.library_service = library_service
    
    # Initialize and start background services
    await event_service.start()
    await printer_service.initialize()

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
    await trending_service.initialize()
    
    # Start printer monitoring
    try:
        await printer_service.start_monitoring()
        logger.info("Printer monitoring started successfully")
    except Exception as e:
        logger.warning("Failed to start printer monitoring", error=str(e))
    
    # Start file watcher service
    try:
        await file_watcher_service.start()
        logger.info("File watcher service started successfully")
    except Exception as e:
        logger.warning("Failed to start file watcher service", error=str(e))
    
    logger.info("Printernizer startup complete")
    
    yield
    
    # Shutdown with proper error handling and timeouts
    logger.info("Shutting down Printernizer gracefully")
    shutdown_timeout = 30  # seconds

    async def shutdown_with_timeout(coro, service_name: str, timeout: float = 10):
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
                timeout=15
            )
        )

    # File watcher service
    if hasattr(app.state, 'file_watcher_service') and app.state.file_watcher_service:
        shutdown_tasks.append(
            shutdown_with_timeout(
                app.state.file_watcher_service.stop(),
                "File watcher service",
                timeout=5
            )
        )

    # Trending service
    if hasattr(app.state, 'trending_service') and app.state.trending_service:
        shutdown_tasks.append(
            shutdown_with_timeout(
                app.state.trending_service.cleanup(),
                "Trending service",
                timeout=5
            )
        )

    # Thumbnail service
    if hasattr(app.state, 'thumbnail_service') and app.state.thumbnail_service:
        shutdown_tasks.append(
            shutdown_with_timeout(
                app.state.thumbnail_service.cleanup(),
                "Thumbnail service",
                timeout=5
            )
        )

    # URL parser service
    if hasattr(app.state, 'url_parser_service') and app.state.url_parser_service:
        shutdown_tasks.append(
            shutdown_with_timeout(
                app.state.url_parser_service.close(),
                "URL parser service",
                timeout=5
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
            timeout=5
        )

    # Close database connection last
    if hasattr(app.state, 'database') and app.state.database:
        await shutdown_with_timeout(
            app.state.database.close(),
            "Database",
            timeout=5
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
        docs_url="/docs" if os.getenv("ENVIRONMENT") == "development" else None,
        redoc_url="/redoc" if os.getenv("ENVIRONMENT") == "development" else None,
        lifespan=lifespan
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
    
    # Home Assistant Ingress security middleware (only active when HA_INGRESS=true)
    if os.getenv("HA_INGRESS") == "true":
        logger = structlog.get_logger()
        logger.info("Home Assistant Ingress mode enabled - restricting access to 172.30.32.2")

        @app.middleware("http")
        async def ingress_security_middleware(request: Request, call_next):
            """Restrict access to Home Assistant Ingress IP only."""
            client_ip = request.client.host if request.client else None
            allowed_ip = "172.30.32.2"

            # Allow health checks from localhost
            if request.url.path == "/api/v1/health" and client_ip in ["127.0.0.1", "localhost"]:
                return await call_next(request)

            # Enforce Ingress security for all other requests
            if client_ip != allowed_ip:
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "FORBIDDEN",
                        "message": "Access denied - Use Home Assistant Ingress",
                        "details": "Direct access is not allowed. Access via Home Assistant UI."
                    }
                )

            return await call_next(request)

    # Security and compliance middleware
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
    app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])
    app.include_router(ideas_router, prefix="/api/v1", tags=["Ideas"])
    app.include_router(idea_url_router, prefix="/api/v1", tags=["Ideas-URL"])
    app.include_router(trending_router, prefix="/api/v1", tags=["Trending"])
    app.include_router(system_router, prefix="/api/v1/system", tags=["System"])
    app.include_router(settings_router, prefix="/api/v1/settings", tags=["Settings"])
    app.include_router(errors_router, prefix="/api/v1/errors", tags=["Error Reporting"])
    app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])
    # Temporary debug endpoints (remove before production if not needed)
    app.include_router(debug_router, prefix="/api/v1/debug", tags=["Debug"])
    
    # Static files and frontend
    frontend_path = Path(__file__).parent.parent / "frontend"
    if frontend_path.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

        @app.get("/")
        async def read_index():
            from fastapi.responses import FileResponse
            return FileResponse(str(frontend_path / "index.html"))

        # Home Assistant Ingress compatibility: handle double-slash path
        @app.get("//")
        async def read_index_double_slash():
            from fastapi.responses import FileResponse
            return FileResponse(str(frontend_path / "index.html"))

        @app.get("/debug")
        async def read_debug():
            from fastapi.responses import FileResponse
            return FileResponse(str(frontend_path / "debug.html"))
    
    # Prometheus metrics endpoint
    @app.get("/metrics")
    async def metrics():
        from fastapi.responses import Response
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    
    # Global exception handlers
    @app.exception_handler(PrinternizerException)
    async def printernizer_exception_handler(request: Request, exc: PrinternizerException):
        logger = structlog.get_logger()
        logger.error("Printernizer exception", error=str(exc), path=request.url.path)
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": exc.timestamp.isoformat()
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger = structlog.get_logger()
        logger.warning("Validation error", errors=exc.errors(), path=request.url.path)
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors()
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger = structlog.get_logger()
        logger.error("Unhandled exception", error=str(exc), path=request.url.path, exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred",
                "details": None
            }
        )
    
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
    
    config = {
        "host": "0.0.0.0",
        "port": int(os.getenv("PORT", 8000)),
        "workers": 1,  # Force single worker to avoid database initialization conflicts
        "log_level": os.getenv("LOG_LEVEL", "info"),
        "access_log": True,
        "use_colors": False,
        "server_header": False,
        "date_header": False
    }
    
    if os.getenv("ENVIRONMENT") == "development":
        config.update({
            "reload": True,
            "reload_dirs": ["src"],
            "workers": 1
        })
    
    uvicorn.run("src.main:app", **config)