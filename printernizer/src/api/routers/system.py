"""System management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import structlog

from src.services.config_service import ConfigService
from src.utils.dependencies import get_config_service


logger = structlog.get_logger()
router = APIRouter()


class SystemInfoResponse(BaseModel):
    """System information response."""
    version: str
    environment: str
    timezone: str
    database_size_mb: float
    uptime_seconds: int


@router.get("/info", response_model=SystemInfoResponse)
async def get_system_info(
    config_service: ConfigService = Depends(get_config_service)
):
    """Get system information."""
    try:
        info = await config_service.get_system_info()
        return info
    except Exception as e:
        logger.error("Failed to get system info", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system information"
        )


@router.post("/backup")
async def create_backup(
    config_service: ConfigService = Depends(get_config_service)
):
    """Create system backup."""
    try:
        backup_path = await config_service.create_backup()
        return {"backup_path": backup_path}
    except Exception as e:
        logger.error("Failed to create backup", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create backup"
        )