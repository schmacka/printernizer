"""File management endpoints - Drucker-Dateien system."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
import structlog

from models.file import File, FileStatus, FileSource, WatchFolderSettings, WatchFolderStatus
from services.file_service import FileService
from services.config_service import ConfigService
from utils.dependencies import get_file_service, get_config_service


logger = structlog.get_logger()
router = APIRouter()


class FileResponse(BaseModel):
    """Response model for file data."""
    id: UUID
    printer_id: UUID
    filename: str
    source: FileSource
    status: FileStatus
    file_size_bytes: Optional[int]
    local_path: Optional[str]
    printer_path: Optional[str]
    checksum: Optional[str]
    downloaded_at: Optional[str]
    created_at: str
    updated_at: str


@router.get("/", response_model=List[FileResponse])
async def list_files(
    printer_id: Optional[UUID] = Query(None, description="Filter by printer ID"),
    status: Optional[FileStatus] = Query(None, description="Filter by file status"),
    source: Optional[FileSource] = Query(None, description="Filter by file source"),
    file_service: FileService = Depends(get_file_service)
):
    """List files from printers and local storage."""
    try:
        files = await file_service.list_files(
            printer_id=printer_id,
            status=status,
            source=source
        )
        return [FileResponse.model_validate(file.__dict__) for file in files]
    except Exception as e:
        logger.error("Failed to list files", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve files"
        )


@router.post("/{file_id}/download")
async def download_file(
    file_id: UUID,
    file_service: FileService = Depends(get_file_service)
):
    """Download a file from printer to local storage."""
    try:
        success = await file_service.download_file(file_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to download file"
            )
        return {"status": "downloaded"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to download file", file_id=str(file_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file"
        )


@router.post("/sync")
async def sync_printer_files(
    printer_id: Optional[UUID] = Query(None, description="Sync specific printer, or all if not specified"),
    file_service: FileService = Depends(get_file_service)
):
    """Synchronize file list with printers."""
    try:
        await file_service.sync_printer_files(printer_id)
        return {"status": "synced"}
    except Exception as e:
        logger.error("Failed to sync files", printer_id=str(printer_id) if printer_id else "all", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync files"
        )


# Watch Folder Management Endpoints

@router.get("/watch-folders/settings", response_model=WatchFolderSettings)
async def get_watch_folder_settings(
    config_service: ConfigService = Depends(get_config_service)
):
    """Get watch folder settings."""
    try:
        settings = config_service.get_watch_folder_settings()
        return WatchFolderSettings(**settings)
    except Exception as e:
        logger.error("Failed to get watch folder settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get watch folder settings"
        )


@router.get("/watch-folders/status")
async def get_watch_folder_status(
    file_service: FileService = Depends(get_file_service),
    config_service: ConfigService = Depends(get_config_service)
):
    """Get watch folder status."""
    try:
        status_info = await file_service.get_watch_status()
        return status_info
    except Exception as e:
        logger.error("Failed to get watch folder status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get watch folder status"
        )


@router.get("/local")
async def list_local_files(
    watch_folder_path: Optional[str] = Query(None, description="Filter by watch folder path"),
    file_service: FileService = Depends(get_file_service)
):
    """List local files from watch folders."""
    try:
        files = await file_service.get_local_files()
        
        # Filter by watch folder path if specified
        if watch_folder_path:
            files = [f for f in files if f.get('watch_folder_path') == watch_folder_path]
        
        return {"files": files}
    except Exception as e:
        logger.error("Failed to list local files", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list local files"
        )


@router.post("/watch-folders/reload")
async def reload_watch_folders(
    file_service: FileService = Depends(get_file_service)
):
    """Reload watch folders configuration."""
    try:
        result = await file_service.reload_watch_folders()
        return result
    except Exception as e:
        logger.error("Failed to reload watch folders", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reload watch folders"
        )


@router.post("/watch-folders/validate")
async def validate_watch_folder(
    folder_path: str = Query(..., description="Folder path to validate"),
    config_service: ConfigService = Depends(get_config_service)
):
    """Validate a watch folder path."""
    try:
        validation = config_service.validate_watch_folder(folder_path)
        return validation
    except Exception as e:
        logger.error("Failed to validate watch folder", folder_path=folder_path, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate watch folder"
        )