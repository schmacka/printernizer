"""Camera endpoints for printer camera functionality."""

import os
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import structlog
import aiofiles
import aiofiles.os

from src.models.snapshot import Snapshot, SnapshotCreate, SnapshotResponse, CameraStatus, CameraTrigger
from src.services.printer_service import PrinterService
from src.utils.dependencies import get_printer_service

logger = structlog.get_logger()
router = APIRouter()


@router.get("/{printer_id}/camera/status", response_model=CameraStatus)
async def get_camera_status(
    printer_id: UUID,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Get camera status and availability for a printer."""
    try:
        printer_id_str = str(printer_id)
        printer_driver = await printer_service.get_printer_driver(printer_id_str)
        
        if not printer_driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Printer not found"
            )
        
        has_camera = await printer_driver.has_camera()
        stream_url = None
        error_message = None
        
        if has_camera:
            try:
                stream_url = await printer_driver.get_camera_stream_url()
                is_available = stream_url is not None
            except Exception as e:
                is_available = False
                error_message = str(e)
        else:
            is_available = False
            
        return CameraStatus(
            has_camera=has_camera,
            is_available=is_available,
            stream_url=stream_url,
            error_message=error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get camera status", 
                    printer_id=str(printer_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get camera status"
        )


@router.get("/{printer_id}/camera/stream")
async def get_camera_stream(
    printer_id: UUID,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Proxy camera stream from printer."""
    try:
        printer_id_str = str(printer_id)
        printer_driver = await printer_service.get_printer_driver(printer_id_str)
        
        if not printer_driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Printer not found"
            )
            
        if not await printer_driver.has_camera():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Printer does not have camera support"
            )
            
        stream_url = await printer_driver.get_camera_stream_url()
        if not stream_url:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Camera stream not available"
            )
            
        # Return redirect to actual stream URL for now
        # In production, this might proxy the stream directly
        return Response(
            status_code=302,
            headers={"Location": stream_url}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get camera stream", 
                    printer_id=str(printer_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to access camera stream"
        )


@router.post("/{printer_id}/camera/snapshot", response_model=SnapshotResponse)
async def take_snapshot(
    printer_id: UUID,
    snapshot_data: SnapshotCreate,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Take a camera snapshot and save it."""
    try:
        printer_id_str = str(printer_id)
        printer_driver = await printer_service.get_printer_driver(printer_id_str)
        
        if not printer_driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Printer not found"
            )
            
        if not await printer_driver.has_camera():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Printer does not have camera support"
            )
            
        # Take snapshot
        image_data = await printer_driver.take_snapshot()
        if not image_data:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to capture snapshot"
            )
            
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"snapshot_{printer_id_str}_{timestamp}.jpg"
        
        # Ensure snapshots directory exists
        snapshots_dir = "/home/runner/work/printernizer/printernizer/snapshots"
        await aiofiles.os.makedirs(snapshots_dir, exist_ok=True)
        
        storage_path = os.path.join(snapshots_dir, filename)
        
        # Save image file
        async with aiofiles.open(storage_path, 'wb') as f:
            await f.write(image_data)
            
        # Create snapshot record (for now, just return response without database)
        snapshot_response = SnapshotResponse(
            id=1,  # Would be from database
            printer_id=printer_id_str,
            job_id=snapshot_data.job_id,
            filename=filename,
            file_size=len(image_data),
            content_type="image/jpeg",
            captured_at=datetime.now().isoformat(),
            capture_trigger=snapshot_data.capture_trigger,
            width=None,  # Would extract from image
            height=None,
            is_valid=True,
            notes=snapshot_data.notes
        )
        
        logger.info("Snapshot captured and saved",
                   printer_id=printer_id_str,
                   filename=filename,
                   file_size=len(image_data))
                   
        return snapshot_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to take snapshot", 
                    printer_id=str(printer_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to take snapshot"
        )


@router.get("/{printer_id}/snapshots", response_model=List[SnapshotResponse])
async def list_snapshots(
    printer_id: UUID,
    limit: int = 10,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """List snapshots for a printer."""
    try:
        printer_id_str = str(printer_id)
        
        # For now, return empty list - would query database in full implementation
        return []
        
    except Exception as e:
        logger.error("Failed to list snapshots", 
                    printer_id=str(printer_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list snapshots"
        )


@router.get("/snapshots/{snapshot_id}/download")
async def download_snapshot(
    snapshot_id: int,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Download a snapshot file."""
    try:
        # For now, return not found - would query database and serve file in full implementation
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Snapshot not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to download snapshot", 
                    snapshot_id=snapshot_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download snapshot"
        )