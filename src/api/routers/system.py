"""System management endpoints."""

import os
import signal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import structlog

from src.services.config_service import ConfigService
from src.utils.dependencies import get_config_service
from src.utils.errors import success_response


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
    info = await config_service.get_system_info()
    return info


@router.post("/backup")
async def create_backup(
    config_service: ConfigService = Depends(get_config_service)
):
    """Create system backup."""
    backup_path = await config_service.create_backup()
    return success_response({"backup_path": backup_path})


@router.post("/shutdown")
async def shutdown_server():
    """Shutdown the server gracefully.

    Triggers a SIGTERM signal to the current process, which will be handled
    by the application's signal handler to perform a graceful shutdown.
    """
    logger.info("Server shutdown requested via API")

    # Send SIGTERM to current process for graceful shutdown
    # This will trigger the signal handler in main.py
    os.kill(os.getpid(), signal.SIGTERM)

    return success_response({
        "status": "success",
        "message": "Server shutdown initiated"
    })