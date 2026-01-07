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
from src.services.external_camera_service import mask_url_credentials, detect_url_type, is_ffmpeg_available
from src.database.database import Database
from src.database.repositories import SnapshotRepository
from src.utils.dependencies import get_printer_service, get_camera_snapshot_service, get_database, get_snapshot_repository
from src.utils.errors import (
    PrinterNotFoundError,
    ServiceUnavailableError,
    NotFoundError,
    ValidationError as PrinternizerValidationError
)

logger = structlog.get_logger()
router = APIRouter()


@router.get("/{printer_id}/camera/diagnostics")
async def get_camera_diagnostics(
    printer_id: UUID,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """
    Diagnostic endpoint for camera troubleshooting.
    Returns detailed information about camera availability and connectivity.
    """
    printer_id_str = str(printer_id)
    printer_driver = await printer_service.get_printer_driver(printer_id_str)

    if not printer_driver:
        return {
            "success": False,
            "error": "Printer not found",
            "printer_id": printer_id_str
        }

    diagnostics = {
        "printer_id": printer_id_str,
        "printer_type": type(printer_driver).__name__,
        "printer_ip": printer_driver.ip_address if hasattr(printer_driver, 'ip_address') else None,
        "tests": {}
    }

    # Test 1: Check if printer type supports cameras
    diagnostics["tests"]["camera_support"] = {
        "test": "Printer type supports cameras",
        "passed": hasattr(printer_driver, 'has_camera'),
        "details": f"{type(printer_driver).__name__} {'has' if hasattr(printer_driver, 'has_camera') else 'does not have'} camera support methods"
    }

    # Test 2: Check camera availability via API
    try:
        has_camera = await printer_driver.has_camera()
        diagnostics["tests"]["camera_detected"] = {
            "test": "Camera detected by printer API",
            "passed": has_camera,
            "details": f"Camera {'detected' if has_camera else 'NOT detected'} (checked via API + snapshot fallback)"
        }

        # For Prusa printers, get more details about camera list endpoint
        if hasattr(printer_driver, '_get_cameras'):
            try:
                cameras = await printer_driver._get_cameras()
                diagnostics["tests"]["camera_list"] = {
                    "test": "Camera list endpoint (/api/v1/cameras)",
                    "passed": len(cameras) > 0 if cameras else False,
                    "details": f"Endpoint returned {len(cameras) if cameras else 0} camera(s)",
                    "cameras": cameras if cameras else [],
                    "note": "Empty list is OK if snapshot endpoint works (see test below)"
                }
            except Exception as e:
                diagnostics["tests"]["camera_list"] = {
                    "test": "Camera list endpoint (/api/v1/cameras)",
                    "passed": False,
                    "details": f"Endpoint failed: {str(e)}",
                    "note": "This is OK if snapshot endpoint works (see test below)"
                }
    except Exception as e:
        diagnostics["tests"]["camera_detected"] = {
            "test": "Camera detected by printer API",
            "passed": False,
            "details": f"Error checking camera: {str(e)}"
        }

    # Test 3: Try to get stream URL
    try:
        stream_url = await printer_driver.get_camera_stream_url()
        diagnostics["tests"]["stream_url"] = {
            "test": "Camera stream URL available",
            "passed": stream_url is not None,
            "details": f"Stream URL: {stream_url if stream_url else 'None - will use polling-based preview'}"
        }
    except Exception as e:
        diagnostics["tests"]["stream_url"] = {
            "test": "Camera stream URL available",
            "passed": False,
            "details": f"Error getting stream URL: {str(e)}"
        }

    # Test 4: Try to capture a test snapshot
    try:
        snapshot_data = await printer_driver.take_snapshot()
        diagnostics["tests"]["snapshot_capture"] = {
            "test": "Camera snapshot capture",
            "passed": snapshot_data is not None and len(snapshot_data) > 0,
            "details": f"Snapshot {'captured successfully' if snapshot_data else 'FAILED'} ({len(snapshot_data) if snapshot_data else 0} bytes)"
        }
    except Exception as e:
        diagnostics["tests"]["snapshot_capture"] = {
            "test": "Camera snapshot capture",
            "passed": False,
            "details": f"Snapshot capture failed: {str(e)}"
        }

    # Summary
    all_tests_passed = all(test.get("passed", False) for test in diagnostics["tests"].values())
    diagnostics["summary"] = {
        "all_tests_passed": all_tests_passed,
        "total_tests": len(diagnostics["tests"]),
        "passed_tests": sum(1 for test in diagnostics["tests"].values() if test.get("passed", False)),
        "recommendation": None
    }

    # Provide troubleshooting recommendations
    if not all_tests_passed:
        if not diagnostics["tests"].get("camera_detected", {}).get("passed"):
            # Camera not detected at all
            diagnostics["summary"]["recommendation"] = (
                "Camera is not detected. Please check:\n"
                "1. Is a camera physically connected to your Prusa printer?\n"
                "2. Access PrusaLink web interface at http://<printer-ip>\n"
                "3. Navigate to Settings → Camera and verify camera is enabled\n"
                "4. Test the camera directly in PrusaLink (you should see a live view)\n"
                "5. Check PrusaLink firmware version (requires 2.1.2+)\n"
                "6. After configuring, restart PrusaLink or reboot the printer"
            )
        elif not diagnostics["tests"].get("snapshot_capture", {}).get("passed"):
            # Camera detected but snapshot fails
            diagnostics["summary"]["recommendation"] = (
                "Camera is detected but snapshot capture failed. Please:\n"
                "1. Test camera in PrusaLink web interface (http://<printer-ip>)\n"
                "2. Check if you can see camera preview in PrusaLink\n"
                "3. Verify camera permissions in PrusaLink settings\n"
                "4. Check PrusaLink logs: journalctl -u prusalink -f\n"
                "5. Try reconnecting the camera or using a different USB port\n"
                "6. Ensure camera is compatible with your printer hardware"
            )
        elif diagnostics["tests"].get("camera_list", {}).get("passed") == False:
            # Camera list endpoint failed but camera might still work
            diagnostics["summary"]["recommendation"] = (
                "Note: Camera list endpoint returned empty, but this may be OK.\n"
                "The camera might still work if snapshot endpoint succeeds.\n"
                "If snapshots work, you can safely ignore the empty camera list."
            )

    return diagnostics


@router.get("/{printer_id}/camera/status", response_model=CameraStatus)
async def get_camera_status(
    printer_id: UUID,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Get camera status and availability for a printer, including external webcam info."""
    printer_id_str = str(printer_id)
    printer_driver = await printer_service.get_printer_driver(printer_id_str)

    if not printer_driver:
        raise PrinterNotFoundError(printer_id_str)

    has_camera = False
    is_available = False
    stream_url = None
    error_message = None
    printer_type = type(printer_driver).__name__

    # Check for external webcam
    has_external_webcam = False
    external_webcam_url = None
    external_webcam_type = None
    ffmpeg_available = True
    ffmpeg_required = False

    try:
        # Get printer info for webcam_url
        printer = await printer_service.get_printer(printer_id_str)
        if printer and getattr(printer, 'webcam_url', None):
            has_external_webcam = True
            external_webcam_url = mask_url_credentials(printer.webcam_url)
            external_webcam_type = detect_url_type(printer.webcam_url)

            # Check if ffmpeg is required and available for RTSP streams
            if external_webcam_type == 'rtsp':
                ffmpeg_required = True
                ffmpeg_available = is_ffmpeg_available()
    except Exception as e:
        logger.debug(
            "Failed to check external webcam",
            printer_id=printer_id_str,
            error=str(e)
        )

    try:
        has_camera = await printer_driver.has_camera()

        if has_camera:
            # Camera is available for snapshots even without live streaming
            is_available = True
            try:
                # Try to get live stream URL (will be None for Bambu Lab A1/P1)
                live_stream_url = await printer_driver.get_camera_stream_url()

                if live_stream_url:
                    # Live stream available (e.g., future X1 series with RTSP)
                    stream_url = live_stream_url
                else:
                    # Fall back to preview endpoint for snapshot-based preview
                    stream_url = f"/api/v1/printers/{printer_id}/camera/preview"
            except Exception as e:
                # Stream URL not available, but snapshots still work
                logger.warning(
                    "Camera stream URL unavailable, using preview",
                    printer_id=printer_id_str,
                    error=str(e)
                )
                error_message = str(e)
                # Still provide preview endpoint
                stream_url = f"/api/v1/printers/{printer_id}/camera/preview"
        else:
            # No built-in camera, but external webcam may still be available
            if has_external_webcam:
                is_available = True
            else:
                is_available = False
                # Provide helpful error message based on printer type
                if printer_type == "PrusaPrinter":
                    error_message = (
                        "No camera detected by PrusaLink. "
                        "Please ensure a camera is connected and configured in PrusaLink settings. "
                        "Access PrusaLink at http://<printer-ip> to configure the camera."
                    )
                elif printer_type == "BambuLabPrinter":
                    error_message = "Camera not available. Bambu Lab printers have built-in cameras that should be automatically detected."
                else:
                    error_message = f"Camera not supported or not detected for {printer_type}"

            logger.info(
                "Camera not detected",
                printer_id=printer_id_str,
                printer_type=printer_type,
                has_camera=has_camera,
                has_external_webcam=has_external_webcam
            )
    except Exception as e:
        logger.error(
            "Error checking camera status",
            printer_id=printer_id_str,
            error=str(e),
            exc_info=True
        )
        has_camera = False
        # External webcam may still work even if built-in camera check fails
        is_available = has_external_webcam
        error_message = f"Failed to check built-in camera status: {str(e)}"

    # Add ffmpeg warning to error message if RTSP is configured but ffmpeg is missing
    if ffmpeg_required and not ffmpeg_available:
        ffmpeg_error = "RTSP stream requires ffmpeg. Install with: apt-get install ffmpeg"
        if error_message:
            error_message = f"{error_message}. {ffmpeg_error}"
        else:
            error_message = ffmpeg_error

    # External webcam is only truly available if it doesn't require ffmpeg OR ffmpeg is installed
    external_webcam_available = has_external_webcam and (not ffmpeg_required or ffmpeg_available)

    return CameraStatus(
        has_camera=has_camera,
        has_external_webcam=has_external_webcam,
        is_available=is_available or external_webcam_available,
        stream_url=stream_url,
        external_webcam_url=external_webcam_url,
        external_webcam_type=external_webcam_type,
        ffmpeg_available=ffmpeg_available,
        ffmpeg_required=ffmpeg_required,
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
        raise ServiceUnavailableError("camera_stream", "Camera stream not available")

    # Return redirect to actual stream URL for now
    # In production, this might proxy the stream directly
    return Response(
        status_code=302,
        headers={"Location": stream_url}
    )


@router.get("/{printer_id}/camera/preview")
async def get_camera_preview(
    printer_id: UUID,
    printer_service: PrinterService = Depends(get_printer_service),
    camera_service: CameraSnapshotService = Depends(get_camera_snapshot_service)
):
    """
    Get current camera preview as image (JPEG or PNG).

    Returns a fresh or cached snapshot without saving to disk or database.
    Intended for periodic polling to create "live preview" effect.
    Uses 5-second cache to reduce load on printer.
    
    Supports both Bambu Lab (JPEG) and Prusa (PNG) printers.
    """
    printer_id_str = str(printer_id)
    printer_driver = await printer_service.get_printer_driver(printer_id_str)

    if not printer_driver:
        raise PrinterNotFoundError(printer_id_str)

    # Check if printer supports camera using the driver's has_camera() method
    if not await printer_driver.has_camera():
        raise PrinternizerValidationError(
            field="camera",
            error="Printer does not have camera support"
        )

    # Get snapshot using camera service (uses cache if fresh)
    try:
        image_data, content_type = await camera_service.get_snapshot_by_id(
            printer_id=printer_id_str,
            force_refresh=False  # Use cached frame if available
        )
    except ValueError as e:
        logger.error("No frame available", printer_id=printer_id_str, error=str(e))
        raise ServiceUnavailableError("camera_preview", "Failed to get preview: No frame available")

    # Return image with appropriate content type and caching headers
    return Response(
        content=image_data,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=5",  # Match cache TTL
            "Content-Disposition": "inline"
        }
    )


@router.get("/{printer_id}/camera/external-preview")
async def get_external_camera_preview(
    printer_id: UUID,
    printer_service: PrinterService = Depends(get_printer_service),
    camera_service: CameraSnapshotService = Depends(get_camera_snapshot_service)
):
    """
    Get preview from external webcam URL only.

    Returns a snapshot from the configured external webcam URL (HTTP or RTSP).
    Uses 5-second cache to reduce load on external camera.

    Returns 400 error if no external webcam URL is configured.
    """
    printer_id_str = str(printer_id)

    # Get snapshot from external webcam using camera service
    try:
        image_data, content_type = await camera_service.get_snapshot_by_id(
            printer_id=printer_id_str,
            force_refresh=False,
            source='external'
        )
    except ValueError as e:
        error_msg = str(e)
        logger.warning("External webcam preview failed", printer_id=printer_id_str, error=error_msg)
        if "No external webcam URL configured" in error_msg:
            raise PrinternizerValidationError(
                field="webcam_url",
                error="No external webcam URL configured for this printer"
            )
        raise ServiceUnavailableError("external_camera", f"Failed to get external preview: {error_msg}")

    # Return image with appropriate content type and caching headers
    return Response(
        content=image_data,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=5",
            "Content-Disposition": "inline"
        }
    )


@router.post("/{printer_id}/camera/snapshot", response_model=SnapshotResponse)
async def take_snapshot(
    printer_id: UUID,
    snapshot_data: SnapshotCreate,
    printer_service: PrinterService = Depends(get_printer_service),
    camera_service: CameraSnapshotService = Depends(get_camera_snapshot_service),
    snapshot_repository: SnapshotRepository = Depends(get_snapshot_repository)
):
    """Take a camera snapshot and save it.
    
    Supports both Bambu Lab (JPEG) and Prusa (PNG) printers.
    """
    printer_id_str = str(printer_id)
    printer_driver = await printer_service.get_printer_driver(printer_id_str)

    if not printer_driver:
        raise PrinterNotFoundError(printer_id_str)

    # Check if printer supports camera using the driver's has_camera() method
    if not await printer_driver.has_camera():
        raise PrinternizerValidationError(
            field="camera",
            error="Printer does not have camera support"
        )

    # Take snapshot using camera service
    try:
        image_data, content_type = await camera_service.get_snapshot_by_id(
            printer_id=printer_id_str,
            force_refresh=snapshot_data.capture_trigger == CameraTrigger.MANUAL
        )
    except ValueError as e:
        logger.error("No frame available", printer_id=printer_id_str, error=str(e))
        raise ServiceUnavailableError("camera_snapshot", "Failed to capture snapshot: No frame available")

    # Determine file extension based on content type
    file_ext = 'png' if content_type == 'image/png' else 'jpg'
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"snapshot_{printer_id_str}_{timestamp}.{file_ext}"

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
        'content_type': content_type,
        'storage_path': storage_path,
        'captured_at': datetime.now().isoformat(),
        'capture_trigger': snapshot_data.capture_trigger.value,
        'width': width,
        'height': height,
        'is_valid': True,
        'notes': snapshot_data.notes
    }

    snapshot_id = await snapshot_repository.create(snapshot_db_data)

    if not snapshot_id:
        logger.error("Failed to create snapshot database record", printer_id=printer_id_str)
        raise ServiceUnavailableError("snapshot_storage", "Failed to save snapshot to database")

    # Get full snapshot record with context
    snapshot_record = await snapshot_repository.get(snapshot_id)

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
    snapshot_repository: SnapshotRepository = Depends(get_snapshot_repository)
):
    """List snapshots for a printer."""
    printer_id_str = str(printer_id)

    snapshots = await snapshot_repository.list(
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
    snapshot_repository: SnapshotRepository = Depends(get_snapshot_repository)
):
    """Download a snapshot file."""
    snapshot = await snapshot_repository.get(snapshot_id)

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