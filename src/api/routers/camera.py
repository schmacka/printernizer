"""Camera endpoints for printer camera functionality."""

import os
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import structlog
import aiofiles
import aiofiles.os

from src.models.snapshot import Snapshot, SnapshotCreate, SnapshotResponse, CameraStatus, CameraTrigger
from src.services.printer_service import PrinterService
from src.utils.dependencies import get_printer_service
from src.utils.errors import (
    PrinterNotFoundError,
    ServiceUnavailableError,
    NotFoundError,
    ValidationError as PrinternizerValidationError
)

logger = structlog.get_logger()
router = APIRouter()


@router.get("/{printer_id}/camera/status", response_model=CameraStatus)
async def get_camera_status(
    printer_id: UUID,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Get camera status and availability for a printer."""
    printer_id_str = str(printer_id)
    printer_driver = await printer_service.get_printer_driver(printer_id_str)

    if not printer_driver:
        raise PrinterNotFoundError(printer_id_str)

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


@router.get("/{printer_id}/camera/stream")
async def get_camera_stream(
    printer_id: UUID,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Proxy camera stream from printer."""
    printer_id_str = str(printer_id)
    printer_driver = await printer_service.get_printer_driver(printer_id_str)

    if not printer_driver:
        raise PrinterNotFoundError(printer_id_str)

    if not await printer_driver.has_camera():
        raise PrinternizerValidationError(
            field="camera",
            error="Printer does not have camera support"
        )

    stream_url = await printer_driver.get_camera_stream_url()
    if not stream_url:
        raise ServiceUnavailableError("Camera stream not available")

    # Return redirect to actual stream URL for now
    # In production, this might proxy the stream directly
    return Response(
        status_code=302,
        headers={"Location": stream_url}
    )


@router.post("/{printer_id}/camera/snapshot", response_model=SnapshotResponse)
async def take_snapshot(
    printer_id: UUID,
    snapshot_data: SnapshotCreate,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Take a camera snapshot and save it."""
    printer_id_str = str(printer_id)
    printer_driver = await printer_service.get_printer_driver(printer_id_str)

    if not printer_driver:
        raise PrinterNotFoundError(printer_id_str)

    if not await printer_driver.has_camera():
        raise PrinternizerValidationError(
            field="camera",
            error="Printer does not have camera support"
        )

    # Take snapshot
    image_data = await printer_driver.take_snapshot()
    if not image_data:
        raise ServiceUnavailableError("Failed to capture snapshot")

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


@router.get("/{printer_id}/snapshots", response_model=List[SnapshotResponse])
async def list_snapshots(
    printer_id: UUID,
    limit: int = 10,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """List snapshots for a printer."""
    printer_id_str = str(printer_id)

    # For now, return empty list - would query database in full implementation
    return []


@router.get("/snapshots/{snapshot_id}/download")
async def download_snapshot(
    snapshot_id: int,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Download a snapshot file."""
    # For now, return not found - would query database and serve file in full implementation
    raise NotFoundError(resource_type="snapshot", resource_id=str(snapshot_id))