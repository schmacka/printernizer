"""Health check endpoints."""

from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
import structlog

from src.services.config_service import ConfigService
from src.database.database import Database
from src.utils.dependencies import get_config_service, get_database


logger = structlog.get_logger()
router = APIRouter()


class ServiceHealth(BaseModel):
    """Service health status."""
    name: str
    status: str  # healthy, degraded, unhealthy
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    environment: str
    database: Dict[str, Any]
    services: Dict[str, Any]
    uptime_seconds: Optional[float] = None


@router.get("/health", response_model=HealthResponse)
async def health_check(
    request: Request,
    config: ConfigService = Depends(get_config_service),
    db: Database = Depends(get_database)
):
    """
    Enhanced health check endpoint with detailed service status.
    Returns system status and comprehensive information about all services.
    """
    try:
        # Test database connection
        db_status = await db.health_check()

        # Get services from app state
        printer_service = getattr(request.app.state, "printer_service", None)
        file_service = getattr(request.app.state, "file_service", None)
        trending_service = getattr(request.app.state, "trending_service", None)
        event_service = getattr(request.app.state, "event_service", None)

        # Check critical services with detailed status
        services_status = {}

        # Database status
        services_status["database"] = {
            "status": "healthy" if db_status else "unhealthy",
            "type": "sqlite",
            "details": {"connected": db_status}
        }

        # Printer service status
        if printer_service:
            try:
                printer_count = len(printer_service._printers) if hasattr(printer_service, "_printers") else 0
                services_status["printer_service"] = {
                    "status": "healthy",
                    "details": {
                        "printer_count": printer_count,
                        "monitoring_active": hasattr(printer_service, "_monitoring_active") and printer_service._monitoring_active
                    }
                }
            except Exception as e:
                services_status["printer_service"] = {
                    "status": "degraded",
                    "details": {"error": str(e)}
                }
        else:
            services_status["printer_service"] = {"status": "unhealthy", "details": {"error": "not initialized"}}

        # File service status
        if file_service:
            services_status["file_service"] = {
                "status": "healthy",
                "details": {"initialized": True}
            }
        else:
            services_status["file_service"] = {"status": "unhealthy", "details": {"error": "not initialized"}}

        # Trending service status
        if trending_service:
            try:
                has_session = trending_service.session is not None and not trending_service.session.closed
                services_status["trending_service"] = {
                    "status": "healthy" if has_session else "degraded",
                    "details": {"http_session_active": has_session}
                }
            except Exception as e:
                services_status["trending_service"] = {
                    "status": "degraded",
                    "details": {"error": str(e)}
                }
        else:
            services_status["trending_service"] = {"status": "degraded", "details": {"error": "not initialized"}}

        # Event service status
        if event_service:
            services_status["event_service"] = {
                "status": "healthy",
                "details": {"initialized": True}
            }
        else:
            services_status["event_service"] = {"status": "unhealthy", "details": {"error": "not initialized"}}

        # Calculate overall status
        statuses = [s["status"] for s in services_status.values()]
        if all(s == "healthy" for s in statuses):
            overall_status = "healthy"
        elif any(s == "unhealthy" for s in statuses):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"

        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now(),
            version="1.2.0",  # Phase 2: Enhanced metadata display
            environment=getattr(config.settings, "environment", "production"),
            database={
                "type": "sqlite",
                "healthy": db_status,
                "connection_count": 1 if db_status else 0
            },
            services=services_status,
            uptime_seconds=None  # Could be calculated from startup time
        )

    except Exception as e:
        logger.error("Health check failed", error=str(e), exc_info=True)
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            version="1.2.0",  # Phase 2: Enhanced metadata display
            environment=getattr(config.settings, "environment", "production"),
            database={"type": "sqlite", "healthy": False},
            services={"error": str(e)}
        )


@router.get("/readiness")
async def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    Returns 200 when application is ready to serve requests.
    """
    return {"status": "ready"}


@router.get("/liveness")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    Returns 200 when application is alive.
    """
    return {"status": "alive"}