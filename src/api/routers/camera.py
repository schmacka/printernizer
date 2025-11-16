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
from src.services.camera_snapshot_service import CameraSnapshotService
from src.services.bambu_camera_client import CameraConnectionError
from src.database.database import Database
from src.utils.dependencies import get_printer_service, get_camera_snapshot_service, get_database
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
    printer_service: PrinterService = Depends(get_printer_service),
    camera_service: CameraSnapshotService = Depends(get_camera_snapshot_service),
    database: Database = Depends(get_database)
):
    """Take a camera snapshot and save it."""
    printer_id_str = str(printer_id)
    printer_driver = await printer_service.get_printer_driver(printer_id_str)

    if not printer_driver:
        raise PrinterNotFoundError(printer_id_str)

    # Get printer details for camera connection
    printer_config = printer_driver._config  # Access printer configuration

    if not hasattr(printer_driver, 'access_code') or not hasattr(printer_driver, 'serial_number'):
        raise PrinternizerValidationError(
            field="camera",
            error="Printer does not support camera (missing access code or serial number)"
        )

    # Take snapshot using camera service
    try:
        image_data = await camera_service.get_snapshot(
            printer_id=printer_id_str,
            ip_address=printer_driver.ip_address,
            access_code=printer_driver.access_code,
            serial_number=printer_driver.serial_number,
            force_refresh=snapshot_data.capture_trigger == CameraTrigger.MANUAL
        )
    except CameraConnectionError as e:
        logger.error("Camera connection failed", printer_id=printer_id_str, error=str(e))
        raise ServiceUnavailableError(f"Camera connection failed: {e}")
    except ValueError as e:
        logger.error("No frame available", printer_id=printer_id_str, error=str(e))
        raise ServiceUnavailableError("Failed to capture snapshot: No frame available")

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"snapshot_{printer_id_str}_{timestamp}.jpg"

    # Ensure snapshots directory exists
    from pathlib import Path
    snapshots_dir = Path(__file__).parent.parent.parent.parent / "data" / "snapshots"
    await aiofiles.os.makedirs(str(snapshots_dir), exist_ok=True)

    storage_path = str(snapshots_dir / filename)

    # Save image file
    async with aiofiles.open(storage_path, 'wb') as f:
        await f.write(image_data)

    # Extract image dimensions if needed
    width = None
    height = None
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(image_data))
        width, height = img.size
    except Exception as e:
        logger.debug("Failed to extract image dimensions", error=str(e))

    # Create snapshot record in database
    snapshot_db_data = {
        'printer_id': printer_id_str,
        'job_id': snapshot_data.job_id,
        'filename': filename,
        'file_size': len(image_data),
        'content_type': 'image/jpeg',
        'storage_path': storage_path,
        'captured_at': datetime.now().isoformat(),
        'capture_trigger': snapshot_data.capture_trigger.value,
        'width': width,
        'height': height,
        'is_valid': True,
        'notes': snapshot_data.notes
    }

    snapshot_id = await database.create_snapshot(snapshot_db_data)

    if not snapshot_id:
        logger.error("Failed to create snapshot database record", printer_id=printer_id_str)
        raise ServiceUnavailableError("Failed to save snapshot to database")

    # Get full snapshot record with context
    snapshot_record = await database.get_snapshot_by_id(snapshot_id)

    snapshot_response = SnapshotResponse(
        id=snapshot_id,
        printer_id=printer_id_str,
        job_id=snapshot_data.job_id,
        filename=filename,
        file_size=len(image_data),
        content_type="image/jpeg",
        captured_at=snapshot_record['captured_at'] if snapshot_record else datetime.now().isoformat(),
        capture_trigger=snapshot_data.capture_trigger,
        width=width,
        height=height,
        is_valid=True,
        notes=snapshot_data.notes,
        job_name=snapshot_record.get('job_name') if snapshot_record else None,
        job_status=snapshot_record.get('job_status') if snapshot_record else None,
        printer_name=snapshot_record.get('printer_name') if snapshot_record else None,
        printer_type=snapshot_record.get('printer_type') if snapshot_record else None
    )

    logger.info("Snapshot captured and saved",
               printer_id=printer_id_str,
               snapshot_id=snapshot_id,
               filename=filename,
               file_size=len(image_data))

    return snapshot_response


@router.get("/{printer_id}/snapshots", response_model=List[SnapshotResponse])
async def list_snapshots(
    printer_id: UUID,
    limit: int = 50,
    offset: int = 0,
    database: Database = Depends(get_database)
):
    """List snapshots for a printer."""
    printer_id_str = str(printer_id)

    snapshots = await database.list_snapshots(
        printer_id=printer_id_str,
        limit=limit,
        offset=offset
    )

    return [
        SnapshotResponse(
            id=s['id'],
            printer_id=s['printer_id'],
            job_id=s.get('job_id'),
            filename=s['filename'],
            file_size=s['file_size'],
            content_type=s['content_type'],
            captured_at=s['captured_at'],
            capture_trigger=CameraTrigger(s['capture_trigger']),
            width=s.get('width'),
            height=s.get('height'),
            is_valid=bool(s.get('is_valid', True)),
            notes=s.get('notes'),
            job_name=s.get('job_name'),
            job_status=s.get('job_status'),
            printer_name=s.get('printer_name'),
            printer_type=s.get('printer_type')
        )
        for s in snapshots
    ]


@router.get("/snapshots/{snapshot_id}/download")
async def download_snapshot(
    snapshot_id: int,
    database: Database = Depends(get_database)
):
    """Download a snapshot file."""
    snapshot = await database.get_snapshot_by_id(snapshot_id)

    if not snapshot:
        raise NotFoundError(resource_type="snapshot", resource_id=str(snapshot_id))

    storage_path = snapshot['storage_path']

    # Check if file exists
    from pathlib import Path
    if not Path(storage_path).exists():
        logger.error("Snapshot file not found", snapshot_id=snapshot_id, path=storage_path)
        raise NotFoundError(resource_type="snapshot file", resource_id=str(snapshot_id))

    # Return file as streaming response
    return StreamingResponse(
        content=open(storage_path, 'rb'),
        media_type=snapshot['content_type'],
        headers={
            'Content-Disposition': f'attachment; filename="{snapshot["filename"]}"'
        }
    )