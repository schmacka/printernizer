"""Printer management endpoints."""

import os
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from fastapi.responses import RedirectResponse
import base64
from pydantic import BaseModel
import structlog

from src.models.printer import Printer, PrinterType, PrinterStatus
from src.services.printer_service import PrinterService
from src.utils.dependencies import get_printer_service, get_database
from src.database.database import Database
from src.utils.errors import (
    PrinterNotFoundError,
    PrinterConnectionError,
    PrinterAlreadyExistsError,
    ServiceUnavailableError,
    ValidationError as PrinternizerValidationError,
    success_response
)

# Optional: Discovery service requires netifaces which may not be available on Windows
DISCOVERY_AVAILABLE = False
try:
    from src.services.discovery_service import DiscoveryService
    DISCOVERY_AVAILABLE = True
except ImportError:
    DiscoveryService = None
    # Discovery endpoints will return 503 errors when not available

logger = structlog.get_logger()
router = APIRouter()


class CurrentJobInfo(BaseModel):
    """Current job information embedded in printer response."""
    name: str
    status: str = "printing"
    progress: Optional[int] = None
    started_at: Optional[datetime] = None
    estimated_remaining: Optional[int] = None
    layer_current: Optional[int] = None
    layer_total: Optional[int] = None


class PrinterCreateRequest(BaseModel):
    """Request model for creating a new printer."""
    name: str
    printer_type: PrinterType
    connection_config: dict
    location: Optional[str] = None
    description: Optional[str] = None


class PrinterUpdateRequest(BaseModel):
    """Request model for updating printer configuration."""
    name: Optional[str] = None
    printer_type: Optional[PrinterType] = None
    connection_config: Optional[dict] = None
    location: Optional[str] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None


class PrinterTestConnectionRequest(BaseModel):
    """Request model for testing printer connection without creating."""
    printer_type: PrinterType
    connection_config: dict


class PaginationResponse(BaseModel):
    """Pagination information."""
    page: int
    limit: int
    total_items: int
    total_pages: int


class PrinterResponse(BaseModel):
    """Response model for printer data."""
    id: str
    name: str
    printer_type: PrinterType
    status: PrinterStatus
    ip_address: Optional[str]
    connection_config: Optional[dict]
    location: Optional[str]
    description: Optional[str]
    is_enabled: bool
    last_seen: Optional[str]
    current_job: Optional[CurrentJobInfo] = None
    temperatures: Optional[dict] = None
    filaments: Optional[list] = None
    created_at: str
    updated_at: str


class PrinterListResponse(BaseModel):
    """Response model for printer list with pagination."""
    printers: List[PrinterResponse]
    total_count: int
    pagination: PaginationResponse


def _printer_to_response(printer: Printer, printer_service: PrinterService = None) -> PrinterResponse:
    """Convert a Printer model to PrinterResponse."""
    
    # Extract job information, temperatures, and filaments from printer service if available
    current_job = None
    temperatures = None
    filaments = None

    if printer_service:
        # Try to get the printer instance to access last_status
        try:
            instance = printer_service.printer_instances.get(printer.id)
            if instance and instance.last_status:
                status = instance.last_status

                # Get current job info
                job_name = status.current_job
                if job_name and isinstance(job_name, str) and job_name.strip():
                    current_job = CurrentJobInfo(
                        name=job_name.strip(),
                        status="printing" if printer.status == PrinterStatus.PRINTING else "idle",
                        progress=status.progress,
                        started_at=status.timestamp
                    )

                # Get temperature info
                if status.temperature_bed is not None or status.temperature_nozzle is not None:
                    temperatures = {}
                    if status.temperature_bed is not None:
                        temperatures['bed'] = status.temperature_bed
                    if status.temperature_nozzle is not None:
                        temperatures['nozzle'] = status.temperature_nozzle

                # Get filament info
                if status.filaments:
                    filaments = [filament.dict() for filament in status.filaments]

        except Exception as e:
            logger.warning("Failed to get status details for printer",
                         printer_id=printer.id, error=str(e))
    
    return PrinterResponse(
        id=printer.id,
        name=printer.name,
        printer_type=printer.type,
        status=printer.status,
        ip_address=printer.ip_address,
        connection_config={
            "ip_address": printer.ip_address,
            "api_key": getattr(printer, "api_key", None),
            "access_code": getattr(printer, "access_code", None),
            "serial_number": getattr(printer, "serial_number", None),
            "webcam_url": getattr(printer, "webcam_url", None),
        },
        location=printer.location,
        description=printer.description,
        is_enabled=printer.is_active,
        last_seen=printer.last_seen.isoformat() if printer.last_seen else None,
        current_job=current_job,
        temperatures=temperatures,
        filaments=filaments,
        created_at=printer.created_at.isoformat(),
        updated_at=printer.created_at.isoformat()  # Use created_at as fallback
    )


@router.get("", response_model=PrinterListResponse)
async def list_printers(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    printer_type: Optional[PrinterType] = Query(None, description="Filter by printer type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    status: Optional[PrinterStatus] = Query(None, description="Filter by printer status"),
    printer_service: PrinterService = Depends(get_printer_service)
):
    """List all configured printers with optional filters and pagination."""
    # Global exception handler will catch any unexpected errors
    printers = await printer_service.list_printers()

    # Apply filters
    filtered_printers = printers
    if printer_type is not None:
        filtered_printers = [p for p in filtered_printers if p.type == printer_type]
    if is_active is not None:
        filtered_printers = [p for p in filtered_printers if p.is_active == is_active]
    if status is not None:
        filtered_printers = [p for p in filtered_printers if p.status == status]

    # Convert to response objects
    printer_responses = [_printer_to_response(printer, printer_service) for printer in filtered_printers]

    # Calculate pagination
    total_count = len(printer_responses)
    total_pages = (total_count + limit - 1) // limit if limit > 0 else 1

    # Apply pagination
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_printers = printer_responses[start_idx:end_idx]

    return PrinterListResponse(
        printers=paginated_printers,
        total_count=total_count,
        pagination=PaginationResponse(
            page=page,
            limit=limit,
            total_items=total_count,
            total_pages=total_pages
        )
    )


@router.get("/discover")
async def discover_printers(
    interface: Optional[str] = Query(None, description="Network interface to scan (auto-detect if not specified)"),
    timeout: Optional[int] = Query(None, description="Discovery timeout in seconds (default from config)"),
    scan_subnet: bool = Query(True, description="Enable subnet scanning for Prusa printers (slower but more reliable)"),
    printer_service: PrinterService = Depends(get_printer_service)
):
    """
    Discover printers on the local network.

    Searches for:
    - Bambu Lab printers via SSDP (ports 1990, 2021)
    - Prusa printers via mDNS/Bonjour and HTTP subnet scan

    Returns list of discovered printers with status indicating if they're already configured.

    Note: May require host networking mode in Docker/Home Assistant environments.
    Subnet scanning may take longer (20-30 seconds) but is more reliable for Prusa printers.
    """
    # Check if discovery is available
    if not DISCOVERY_AVAILABLE:
        raise ServiceUnavailableError(
            service="Printer Discovery",
            reason="netifaces library not installed"
        )

    # Check if discovery is enabled
    discovery_enabled = os.getenv("DISCOVERY_ENABLED", "true").lower() == "true"
    if not discovery_enabled:
        raise ServiceUnavailableError(
            service="Printer Discovery",
            reason="discovery is disabled in configuration"
        )

    # Get timeout from config if not provided
    if timeout is None:
        timeout = int(os.getenv("DISCOVERY_TIMEOUT_SECONDS", "10"))

    # Create discovery service
    discovery_service = DiscoveryService(timeout=timeout)

    # Get list of configured printer IPs for duplicate detection
    printers = await printer_service.list_printers()
    configured_ips = [p.ip_address for p in printers if p.ip_address]

    # Run discovery
    logger.info("Starting printer discovery", interface=interface, timeout=timeout, scan_subnet=scan_subnet)
    results = await discovery_service.discover_all(
        interface=interface,
        configured_ips=configured_ips,
        scan_subnet=scan_subnet
    )

    logger.info("Printer discovery completed",
               discovered_count=len(results['discovered']),
               duration_ms=results['scan_duration_ms'])

    # Global exception handler will catch any unexpected errors
    return results


@router.get("/discover/interfaces")
async def list_network_interfaces():
    """
    List available network interfaces for discovery.

    Returns list of network interfaces with their IP addresses.
    Useful for allowing users to select which network to scan.
    """
    # Check if discovery is available
    if not DISCOVERY_AVAILABLE:
        raise ServiceUnavailableError(
            service="Network Interface Discovery",
            reason="netifaces library not installed"
        )

    interfaces = DiscoveryService.get_network_interfaces()
    default_interface = DiscoveryService.get_default_interface()

    # Mark the default interface
    for iface in interfaces:
        if iface["name"] == default_interface:
            iface["is_default"] = True

    return {
        "interfaces": interfaces,
        "default": default_interface
    }


@router.get("/discover/startup")
async def get_startup_discovered_printers():
    """
    Get printers discovered during application startup.

    Returns the list of printers found during automatic discovery on startup
    (if DISCOVERY_RUN_ON_STARTUP is enabled). This allows the dashboard to
    display newly discovered printers without running a new scan.

    Returns empty list if startup discovery is disabled or no printers were found.
    """
    try:
        from fastapi import Request
        from src.main import app

        # Get discovered printers from app state
        discovered = getattr(app.state, 'startup_discovered_printers', [])

        return {
            "discovered": discovered,
            "count": len(discovered),
            "new_count": sum(1 for p in discovered if not p.get('already_added', False))
        }
    except Exception as e:
        logger.error("Failed to get startup discovered printers", error=str(e))
        # Return empty result instead of error for better UX
        return {
            "discovered": [],
            "count": 0,
            "new_count": 0
        }


@router.delete("/discover/startup")
async def clear_startup_discovered_printers():
    """
    Clear the list of printers discovered during startup.

    This endpoint allows the frontend to acknowledge that discovered printers
    have been handled (either added or dismissed by the user), so they won't
    be shown again until the next discovery run.
    """
    try:
        from src.main import app

        # Clear discovered printers from app state
        app.state.startup_discovered_printers = []

        return {
            "status": "cleared",
            "message": "Startup discovered printers cleared successfully"
        }
    except Exception as e:
        logger.error("Failed to clear startup discovered printers", error=str(e))
        return {
            "status": "error",
            "message": "Failed to clear discovered printers"
        }


@router.post("/test-connection")
async def test_printer_connection(
    test_request: PrinterTestConnectionRequest,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Test printer connection without creating the printer.

    This endpoint allows testing connection parameters before actually
    creating a printer configuration. Useful for setup wizards.
    """
    try:
        result = await printer_service.test_connection(
            test_request.printer_type,
            test_request.connection_config
        )
        response_data = {
            "success": result.get("success", False),
            "message": result.get("message", "Connection test completed"),
            "details": result.get("details", {})
        }
        # Include response_time_ms if provided by the service
        if "response_time_ms" in result:
            response_data["response_time_ms"] = result["response_time_ms"]
        return success_response(response_data)
    except Exception as e:
        logger.error("Connection test failed", error=str(e))
        return success_response({
            "success": False,
            "message": str(e)
        })


@router.post("", response_model=PrinterResponse, status_code=status.HTTP_201_CREATED)
async def create_printer(
    printer_data: PrinterCreateRequest,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Create a new printer configuration and automatically connect to it."""
    try:
        printer = await printer_service.create_printer(
            name=printer_data.name,
            printer_type=printer_data.printer_type,
            connection_config=printer_data.connection_config,
            location=printer_data.location,
            description=printer_data.description
        )
        logger.info("Created printer", printer_type=type(printer).__name__, printer_dict=printer.__dict__)

        # Automatically connect to the newly created printer
        try:
            connect_success = await printer_service.connect_printer(printer.id)
            if connect_success:
                logger.info("Auto-connected to newly created printer", printer_id=printer.id, printer_name=printer.name)
                # Start monitoring for the new printer
                await printer_service.start_monitoring(printer.id)
                logger.info("Started monitoring for newly created printer", printer_id=printer.id)
            else:
                logger.warning("Failed to auto-connect to newly created printer", printer_id=printer.id, printer_name=printer.name)
        except Exception as e:
            # Log the connection error but don't fail the creation
            logger.warning("Failed to auto-connect to newly created printer",
                         printer_id=printer.id,
                         printer_name=printer.name,
                         error=str(e))

        response = _printer_to_response(printer, printer_service)
        logger.info("Converted to response", response_dict=response.model_dump())
        return response
    except ValueError as e:
        # Convert service ValueError to standardized ValidationError
        raise PrinternizerValidationError(
            field="printer_config",
            error=str(e)
        )


@router.get("/{printer_id}", response_model=PrinterResponse)
async def get_printer(
    printer_id: str,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Get printer details by ID."""
    printer = await printer_service.get_printer(printer_id)
    if not printer:
        raise PrinterNotFoundError(printer_id)
    return _printer_to_response(printer, printer_service)


@router.put("/{printer_id}", response_model=PrinterResponse)
async def update_printer(
    printer_id: str,
    printer_data: PrinterUpdateRequest,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Update printer configuration."""
    # ValueError will be caught by global handler and converted to 400
    printer = await printer_service.update_printer(printer_id, **printer_data.model_dump(exclude_unset=True))
    if not printer:
        raise PrinterNotFoundError(printer_id)
    return _printer_to_response(printer, printer_service)


@router.delete("/{printer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_printer(
    printer_id: str,
    force: bool = Query(False, description="Force deletion even with active jobs"),
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Delete a printer configuration."""
    try:
        success = await printer_service.delete_printer(printer_id, force=force)
        if not success:
            raise PrinterNotFoundError(printer_id)
    except ValueError as e:
        # Handle active job deletion attempt
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.get("/{printer_id}/status")
async def get_printer_status(
    printer_id: str,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """
    Get lightweight printer status for real-time monitoring.

    Returns current status, job progress, and temperatures without full printer details.
    Optimized for frequent polling.
    """
    printer = await printer_service.get_printer(printer_id)
    if not printer:
        raise PrinterNotFoundError(printer_id)

    # Get current status from printer instance
    instance = printer_service.printer_instances.get(printer_id)

    response = {
        "id": printer.id,
        "name": printer.name,
        "status": printer.status.value,
        "current_job": None,
        "temperatures": None,
        "timestamp": datetime.now().isoformat()
    }

    if instance and instance.last_status:
        status = instance.last_status

        # Get current job info
        if status.current_job:
            response["current_job"] = {
                "name": status.current_job,
                "progress": status.progress,
                "remaining_time": status.remaining_time_minutes
            }

        # Get temperatures (model uses temperature_bed/temperature_nozzle)
        if status.temperature_bed is not None or status.temperature_nozzle is not None:
            response["temperatures"] = {
                "bed": {
                    "current": status.temperature_bed,
                    "target": getattr(status, 'bed_target_temperature', None)
                },
                "nozzle": {
                    "current": status.temperature_nozzle,
                    "target": getattr(status, 'nozzle_target_temperature', None)
                }
            }

    return response


@router.get("/{printer_id}/details")
async def get_printer_details(
    printer_id: str,
    printer_service: PrinterService = Depends(get_printer_service),
    db: Database = Depends(get_database)
):
    """
    Get comprehensive printer details for the printer details modal.

    Returns printer info, recent job history, statistics, and connection diagnostics.
    """
    printer = await printer_service.get_printer(printer_id)
    if not printer:
        raise PrinterNotFoundError(printer_id)
    instance = printer_service.printer_instances.get(printer_id)

    # Get recent jobs for this printer (last 10)
    recent_jobs = await db.fetch_all(
        """
        SELECT id, file_name, status, progress, started_at, ended_at,
               actual_print_time, material_used, material_cost
        FROM jobs
        WHERE printer_id = ?
        ORDER BY started_at DESC
        LIMIT 10
        """,
        (printer_id,)
    )

    # Get job statistics
    job_stats = await db.fetch_one(
        """
        SELECT
            COUNT(*) as total_jobs,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_jobs,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs,
            SUM(CASE WHEN status = 'completed' THEN actual_print_time ELSE 0 END) as total_print_time,
            SUM(CASE WHEN status = 'completed' THEN material_used ELSE 0 END) as total_material_used,
            AVG(CASE WHEN status = 'completed' THEN progress ELSE NULL END) as avg_completion
        FROM jobs
        WHERE printer_id = ?
        """,
        (printer_id,)
    )

    # Get connection diagnostics
    connection_info = {
        "is_connected": instance.is_connected if instance else False,
        "connection_type": printer.printer_type.value,
        "ip_address": printer.connection_config.get("ip_address", "N/A"),
        "last_seen": printer.last_seen.isoformat() if printer.last_seen else None,
        "firmware_version": None,
        "uptime": None
    }

    if instance and instance.last_status:
        status_data = instance.last_status
        connection_info["firmware_version"] = getattr(status_data, 'firmware_version', None)

    # Build response
    response = {
        "printer": {
            "id": printer.id,
            "name": printer.name,
            "type": printer.printer_type.value,
            "status": printer.status.value,
            "location": printer.location,
            "description": printer.description,
            "is_enabled": printer.is_enabled,
            "created_at": printer.created_at.isoformat() if printer.created_at else None,
            "last_seen": printer.last_seen.isoformat() if printer.last_seen else None
        },
        "connection": connection_info,
        "statistics": {
            "total_jobs": job_stats["total_jobs"] if job_stats else 0,
            "completed_jobs": job_stats["completed_jobs"] if job_stats else 0,
            "failed_jobs": job_stats["failed_jobs"] if job_stats else 0,
            "success_rate": round(
                (job_stats["completed_jobs"] / job_stats["total_jobs"] * 100)
                if job_stats and job_stats["total_jobs"] > 0 else 0, 1
            ),
            "total_print_time_hours": round(
                (job_stats["total_print_time"] or 0) / 60, 1
            ) if job_stats else 0,
            "total_material_kg": round(
                (job_stats["total_material_used"] or 0) / 1000, 2
            ) if job_stats else 0
        },
        "recent_jobs": [
            {
                "id": job["id"],
                "file_name": job["file_name"],
                "status": job["status"],
                "progress": job["progress"],
                "started_at": job["started_at"],
                "ended_at": job["ended_at"],
                "print_time_minutes": job["actual_print_time"],
                "material_used": job["material_used"]
            }
            for job in recent_jobs
        ] if recent_jobs else [],
        "current_status": None
    }

    # Add current status if available
    if instance and instance.last_status:
        status_data = instance.last_status
        response["current_status"] = {
            "current_job": status_data.current_job,
            "progress": status_data.progress,
            "remaining_time": status_data.remaining_time_minutes,
            "temperatures": {
                "bed": {"current": status_data.bed_temperature, "target": status_data.bed_target_temperature},
                "nozzle": {"current": status_data.nozzle_temperature, "target": status_data.nozzle_target_temperature}
            }
        }

    return response


@router.post("/{printer_id}/connect")
async def connect_printer(
    printer_id: str,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Connect to printer."""
    success = await printer_service.connect_printer(printer_id)
    if not success:
        raise PrinterConnectionError(
            printer_id=printer_id,
            reason="Connection failed"
        )
    return success_response({"status": "connected"})


@router.post("/{printer_id}/disconnect")
async def disconnect_printer(
    printer_id: str,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Disconnect from printer."""
    await printer_service.disconnect_printer(printer_id)
    return success_response({"status": "disconnected"})


@router.post("/{printer_id}/pause")
async def pause_printer(
    printer_id: str,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Pause the current print job."""
    success = await printer_service.pause_printer(printer_id)
    if not success:
        raise PrinterConnectionError(
            printer_id=printer_id,
            reason="Failed to pause print job - printer may not be printing or is unreachable"
        )
    return success_response({"status": "paused"})


@router.post("/{printer_id}/resume")
async def resume_printer(
    printer_id: str,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Resume the paused print job."""
    success = await printer_service.resume_printer(printer_id)
    if not success:
        raise PrinterConnectionError(
            printer_id=printer_id,
            reason="Failed to resume print job - printer may not be paused or is unreachable"
        )
    return success_response({"status": "resumed"})


@router.post("/{printer_id}/stop")
async def stop_printer(
    printer_id: str,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Stop/cancel the current print job."""
    success = await printer_service.stop_printer(printer_id)
    if not success:
        raise PrinterConnectionError(
            printer_id=printer_id,
            reason="Failed to stop print job - printer may not be printing or is unreachable"
        )
    return success_response({"status": "stopped"})


@router.post("/{printer_id}/download-current-job")
async def download_current_job_file(
    printer_id: str,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Explicitly trigger download + processing of the currently printing job file.

    Returns a JSON dict with a status field describing the outcome:
    - success: File downloaded (or already local) and thumbnail processing triggered/completed
    - exists_with_thumbnail: File already present locally with thumbnail
    - exists_no_thumbnail: File present but had no thumbnail extracted (non-print file or parsing failed)
    - not_printing: Printer not currently printing / no active job
    - printer_not_found: Unknown printer id
    - error: Unexpected failure (see message)
    """
    result = await printer_service.download_current_job_file(printer_id)
    # Map service result directly; ensure a status key exists
    if not isinstance(result, dict):
        return success_response({"status": "error", "message": "Unexpected service response"})
    return success_response(result)


@router.get("/{printer_id}/files")
async def get_printer_files(
    printer_id: str,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Get files from a specific printer."""
    files = await printer_service.get_printer_files(printer_id)
    return success_response({"files": files})


@router.post("/{printer_id}/monitoring/start")
async def start_printer_monitoring(
    printer_id: str,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Start monitoring for a specific printer."""
    success = await printer_service.start_printer_monitoring(printer_id)
    if not success:
        raise ServiceUnavailableError(
            service="Printer Monitoring",
            reason=f"Failed to start monitoring for printer {printer_id}"
        )
    return success_response({"status": "monitoring_started"})


@router.post("/{printer_id}/monitoring/stop")
async def stop_printer_monitoring(
    printer_id: str,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Stop monitoring for a specific printer."""
    success = await printer_service.stop_printer_monitoring(printer_id)
    if not success:
        raise ServiceUnavailableError(
            service="Printer Monitoring",
            reason=f"Failed to stop monitoring for printer {printer_id}"
        )
    return success_response({"status": "monitoring_stopped"})


@router.post("/{printer_id}/files/{filename}/download")
async def download_printer_file(
    printer_id: str,
    filename: str,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Download a specific file from printer to local storage."""
    success = await printer_service.download_printer_file(printer_id, filename)
    if not success:
        from src.utils.errors import FileDownloadError
        raise FileDownloadError(
            filename=filename,
            printer_id=printer_id,
            reason="Download operation failed - file may not exist or printer is unreachable"
        )
    return success_response({"status": "downloaded", "filename": filename})


@router.get("/{printer_id}/thumbnail")
async def get_printer_current_thumbnail(
    printer_id: str,
    printer_service: PrinterService = Depends(get_printer_service),
):
    """Return the current job thumbnail image for a printer (if available).

    This is a convenience wrapper so clients can simply hit a printer-specific
    endpoint instead of first resolving the file_id. If a thumbnail exists it
    returns the raw image bytes with proper content type. 404 if not present.
    """
    from src.utils.errors import FileNotFoundError as PrinternizerFileNotFoundError

    printer = await printer_service.get_printer(printer_id)
    if not printer:
        raise PrinterNotFoundError(printer_id)

    instance = printer_service.printer_instances.get(printer.id)
    if not instance or not getattr(instance, 'last_status', None):
        raise PrinternizerFileNotFoundError(
            file_id="current_job_thumbnail",
            details={"printer_id": printer_id, "reason": "No status available for printer"}
        )

    status_obj = instance.last_status
    file_id = getattr(status_obj, 'current_job_file_id', None)
    has_thumbnail_flag = getattr(status_obj, 'current_job_has_thumbnail', False)
    if not file_id or not has_thumbnail_flag:
        raise PrinternizerFileNotFoundError(
            file_id="current_job_thumbnail",
            details={"printer_id": printer_id, "reason": "Printer has no current job thumbnail"}
        )

    # Access file service (set on printer_service during startup)
    file_service = getattr(printer_service, 'file_service', None)
    if not file_service:
        raise ServiceUnavailableError(
            service="File Service",
            reason="File service unavailable during thumbnail lookup"
        )

    file_record = await file_service.get_file_by_id(file_id)
    if not file_record:
        raise PrinternizerFileNotFoundError(
            file_id=file_id,
            details={"printer_id": printer_id, "reason": "File record for current job not found"}
        )

    if not file_record.get('has_thumbnail') or not file_record.get('thumbnail_data'):
        raise PrinternizerFileNotFoundError(
            file_id=file_id,
            details={"printer_id": printer_id, "reason": "File has no thumbnail data"}
        )

    # Decode and stream
    try:
        raw = base64.b64decode(file_record['thumbnail_data'])
    except Exception:
        from src.utils.errors import FileProcessingError
        raise FileProcessingError(
            file_id=file_id,
            operation="decode thumbnail",
            reason="Corrupt or invalid thumbnail data"
        )

    fmt = file_record.get('thumbnail_format', 'png')
    return Response(
        content=raw,
        media_type=f"image/{fmt}",
        headers={
            "Cache-Control": "no-cache, max-age=0",  # always fresh for active job
            "Content-Disposition": f"inline; filename=printer_{printer_id}_current_thumbnail.{fmt}"
        }
    )