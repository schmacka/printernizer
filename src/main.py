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

import structlog
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from api.routers import (
    health_router,
    printers_router, 
    jobs_router,
    files_router,
    analytics_router,
    system_router,
    websocket_router,
    settings_router
)
from database.database import Database
from services.event_service import EventService
from services.config_service import ConfigService
from services.printer_service import PrinterService
from services.migration_service import MigrationService
from utils.logging_config import setup_logging
from utils.exceptions import PrinternizerException
from utils.middleware import (
    RequestTimingMiddleware,
    GermanComplianceMiddleware,
    SecurityHeadersMiddleware
)


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
    logger.info("Starting Printernizer application", version="1.0.0")
    
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
    
    app.state.config_service = config_service
    app.state.event_service = event_service
    app.state.printer_service = printer_service
    
    # Initialize and start background services
    await event_service.start()
    await printer_service.initialize()
    
    logger.info("Printernizer startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Printernizer")
    await printer_service.shutdown()
    await event_service.stop()
    await database.close()
    logger.info("Printernizer shutdown complete")


def create_application() -> FastAPI:
    """Create FastAPI application with production configuration."""
    
    # Initialize settings to get configuration
    from services.config_service import Settings
    settings = Settings()
    
    app = FastAPI(
        title="Printernizer API",
        description="Professional 3D Print Management System for Bambu Lab & Prusa Printers",
        version="1.0.0",
        docs_url="/docs" if os.getenv("ENVIRONMENT") == "development" else None,
        redoc_url="/redoc" if os.getenv("ENVIRONMENT") == "development" else None,
        lifespan=lifespan
    )
    
    # CORS Configuration
    cors_origins = settings.get_cors_origins()
    # Add localhost for development
    if settings.environment == "development":
        cors_origins.extend(["http://localhost:3000", "http://127.0.0.1:3000"])
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
    )
    
    # Security and compliance middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(GermanComplianceMiddleware)
    app.add_middleware(RequestTimingMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # API Routes
    app.include_router(health_router, prefix="/api/v1", tags=["Health"])
    app.include_router(printers_router, prefix="/api/v1/printers", tags=["Printers"])
    app.include_router(jobs_router, prefix="/api/v1/jobs", tags=["Jobs"]) 
    app.include_router(files_router, prefix="/api/v1/files", tags=["Files"])
    app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])
    app.include_router(system_router, prefix="/api/v1/system", tags=["System"])
    app.include_router(settings_router, prefix="/api/v1/settings", tags=["Settings"])
    app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])
    
    # Static files and frontend
    frontend_path = Path(__file__).parent.parent / "frontend"
    if frontend_path.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
        
        @app.get("/")
        async def read_index():
            from fastapi.responses import FileResponse
            return FileResponse(str(frontend_path / "index.html"))
    
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
    
    uvicorn.run("main:app", **config)