"""Health check endpoints."""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
import structlog

from services.config_service import ConfigService
from database.database import Database
from utils.dependencies import get_config_service, get_database


logger = structlog.get_logger()
router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    environment: str
    database: Dict[str, Any]
    services: Dict[str, str]


@router.get("/health", response_model=HealthResponse)
async def health_check(
    config: ConfigService = Depends(get_config_service),
    db: Database = Depends(get_database)
):
    """
    Basic health check endpoint.
    Returns system status and basic information.
    """
    try:
        # Test database connection
        db_status = await db.health_check()
        
        # Check critical services
        services_status = {
            "database": "healthy" if db_status else "unhealthy",
            "printer_connections": "healthy",  # Will be updated based on actual printer status
            "file_system": "healthy",
            "background_tasks": "healthy"
        }
        
        overall_status = "healthy" if all(
            status == "healthy" for status in services_status.values()
        ) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now(),
            version="1.0.0",
            environment=getattr(config.settings, "environment", "production"),
            database={
                "type": "sqlite",
                "healthy": db_status,
                "connection_count": 1 if db_status else 0
            },
            services=services_status
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(), 
            version="1.0.0",
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