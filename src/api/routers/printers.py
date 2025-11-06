"""Printer management endpoints."""

import os
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from fastapi.responses import RedirectResponse
import base64
from pydantic import BaseModel
import structlog

from src.models.printer import Printer, PrinterType, PrinterStatus
from src.services.printer_service import PrinterService
from src.utils.dependencies import get_printer_service

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


class PrinterResponse(BaseModel):
    """Response model for printer data."""
    id: UUID
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
    created_at: str
    updated_at: str


def _printer_to_response(printer: Printer, printer_service: PrinterService = None) -> PrinterResponse:
    """Convert a Printer model to PrinterResponse."""
    
    # Extract job information and temperatures from printer service if available
    current_job = None
    temperatures = None
    
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
        },
        location=getattr(printer, 'location', None),
        description=getattr(printer, 'description', None),
        is_enabled=printer.is_active,
        last_seen=printer.last_seen.isoformat() if printer.last_seen else None,
        current_job=current_job,
        temperatures=temperatures,
        created_at=printer.created_at.isoformat(),
        updated_at=printer.created_at.isoformat()  # Use created_at as fallback
    )


@router.get("", response_model=List[PrinterResponse])
async def list_printers(
    printer_service: PrinterService = Depends(get_printer_service)
):
    """List all configured printers."""
    try:
        printers = await printer_service.list_printers()
        return [_printer_to_response(printer, printer_service) for printer in printers]
    except Exception as e:
        logger.error("Failed to list printers", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve printers"
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
    try:
        # Check if discovery is available
        if not DISCOVERY_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Printer discovery unavailable (netifaces not installed)"
            )

        # Check if discovery is enabled
        discovery_enabled = os.getenv("DISCOVERY_ENABLED", "true").lower() == "true"
        if not discovery_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Printer discovery is disabled"
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

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Printer discovery failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Printer discovery failed: {str(e)}"
        )


@router.get("/discover/interfaces")
async def list_network_interfaces():
    """
    List available network interfaces for discovery.

    Returns list of network interfaces with their IP addresses.
    Useful for allowing users to select which network to scan.
    """
    try:
        # Check if discovery is available
        if not DISCOVERY_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Network interface discovery unavailable (netifaces not installed)"
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
    except Exception as e:
        logger.error("Failed to list network interfaces", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve network interfaces"
        )


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


@router.post("", response_model=PrinterResponse, status_code=status.HTTP_201_CREATED)
async def create_printer(
    printer_data: PrinterCreateRequest,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Create a new printer configuration."""
    try:
        printer = await printer_service.create_printer(
            name=printer_data.name,
            printer_type=printer_data.printer_type,
            connection_config=printer_data.connection_config,
            location=printer_data.location,
            description=printer_data.description
        )
        logger.info("Created printer", printer_type=type(printer).__name__, printer_dict=printer.__dict__)
        response = _printer_to_response(printer, printer_service)
        logger.info("Converted to response", response_dict=response.model_dump())
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to create printer", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create printer"
        )


@router.get("/{printer_id}", response_model=PrinterResponse)
async def get_printer(
    printer_id: UUID,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Get printer details by ID."""
    try:
        printer = await printer_service.get_printer(str(printer_id))
        if not printer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Printer not found"
            )
        return _printer_to_response(printer, printer_service)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get printer", printer_id=str(printer_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve printer"
        )


@router.put("/{printer_id}", response_model=PrinterResponse)
async def update_printer(
    printer_id: UUID,
    printer_data: PrinterUpdateRequest,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Update printer configuration."""
    try:
        printer = await printer_service.update_printer(printer_id, **printer_data.model_dump(exclude_unset=True))
        if not printer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Printer not found"
            )
        return _printer_to_response(printer, printer_service)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to update printer", printer_id=str(printer_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update printer"
        )


@router.delete("/{printer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_printer(
    printer_id: UUID,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Delete a printer configuration."""
    try:
        success = await printer_service.delete_printer(printer_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Printer not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete printer", printer_id=str(printer_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete printer"
        )


@router.post("/{printer_id}/connect")
async def connect_printer(
    printer_id: UUID,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Connect to printer."""
    try:
        success = await printer_service.connect_printer(printer_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to connect to printer"
            )
        return {"status": "connected"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to connect printer", printer_id=str(printer_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect to printer"
        )


@router.post("/{printer_id}/disconnect")
async def disconnect_printer(
    printer_id: UUID,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Disconnect from printer."""
    try:
        await printer_service.disconnect_printer(printer_id)
        return {"status": "disconnected"}
    except Exception as e:
        logger.error("Failed to disconnect printer", printer_id=str(printer_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect from printer"
        )


@router.post("/{printer_id}/pause")
async def pause_printer(
    printer_id: UUID,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Pause the current print job."""
    try:
        printer_id_str = str(printer_id)
        success = await printer_service.pause_printer(printer_id_str)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to pause print job"
            )
        return {"status": "paused"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to pause printer", printer_id=str(printer_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pause print job"
        )


@router.post("/{printer_id}/resume")
async def resume_printer(
    printer_id: UUID,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Resume the paused print job."""
    try:
        printer_id_str = str(printer_id)
        success = await printer_service.resume_printer(printer_id_str)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to resume print job"
            )
        return {"status": "resumed"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to resume printer", printer_id=str(printer_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resume print job"
        )


@router.post("/{printer_id}/stop")
async def stop_printer(
    printer_id: UUID,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Stop/cancel the current print job."""
    try:
        printer_id_str = str(printer_id)
        success = await printer_service.stop_printer(printer_id_str)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to stop print job"
            )
        return {"status": "stopped"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to stop printer", printer_id=str(printer_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop print job"
        )


@router.post("/{printer_id}/download-current-job")
async def download_current_job_file(
    printer_id: UUID,
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
    try:
        result = await printer_service.download_current_job_file(str(printer_id))
        # Map service result directly; ensure a status key exists
        if not isinstance(result, dict):
            return {"status": "error", "message": "Unexpected service response"}
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to download current job file", printer_id=str(printer_id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process current job file")


@router.get("/{printer_id}/files")
async def get_printer_files(
    printer_id: UUID,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Get files from a specific printer."""
    try:
        printer_id_str = str(printer_id)
        files = await printer_service.get_printer_files(printer_id_str)
        return {"files": files}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get printer files", printer_id=str(printer_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve printer files"
        )


@router.post("/{printer_id}/monitoring/start")
async def start_printer_monitoring(
    printer_id: UUID,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Start monitoring for a specific printer."""
    try:
        printer_id_str = str(printer_id)
        success = await printer_service.start_printer_monitoring(printer_id_str)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to start printer monitoring"
            )
        return {"status": "monitoring_started"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start printer monitoring", printer_id=str(printer_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start printer monitoring"
        )


@router.post("/{printer_id}/monitoring/stop")
async def stop_printer_monitoring(
    printer_id: UUID,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Stop monitoring for a specific printer."""
    try:
        printer_id_str = str(printer_id)
        success = await printer_service.stop_printer_monitoring(printer_id_str)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to stop printer monitoring"
            )
        return {"status": "monitoring_stopped"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to stop printer monitoring", printer_id=str(printer_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop printer monitoring"
        )


@router.post("/{printer_id}/files/{filename}/download")
async def download_printer_file(
    printer_id: UUID,
    filename: str,
    printer_service: PrinterService = Depends(get_printer_service)
):
    """Download a specific file from printer to local storage."""
    try:
        printer_id_str = str(printer_id)
        success = await printer_service.download_printer_file(printer_id_str, filename)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to download file from printer"
            )
        return {"status": "downloaded", "filename": filename}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to download printer file", printer_id=str(printer_id), filename=filename, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file from printer"
        )


@router.get("/{printer_id}/thumbnail")
async def get_printer_current_thumbnail(
    printer_id: UUID,
    printer_service: PrinterService = Depends(get_printer_service),
):
    """Return the current job thumbnail image for a printer (if available).

    This is a convenience wrapper so clients can simply hit a printer-specific
    endpoint instead of first resolving the file_id. If a thumbnail exists it
    returns the raw image bytes with proper content type. 404 if not present.
    """
    try:
        printer = await printer_service.get_printer(str(printer_id))
        if not printer:
            raise HTTPException(status_code=404, detail="Printer not found")

        instance = printer_service.printer_instances.get(printer.id)
        if not instance or not getattr(instance, 'last_status', None):
            raise HTTPException(status_code=404, detail="No status available for printer")

        status_obj = instance.last_status
        file_id = getattr(status_obj, 'current_job_file_id', None)
        has_thumbnail_flag = getattr(status_obj, 'current_job_has_thumbnail', False)
        if not file_id or not has_thumbnail_flag:
            raise HTTPException(status_code=404, detail="Printer has no current job thumbnail")

        # Access file service (set on printer_service during startup)
        file_service = getattr(printer_service, 'file_service', None)
        if not file_service:
            raise HTTPException(status_code=500, detail="File service unavailable")

        file_record = await file_service.get_file_by_id(file_id)
        if not file_record:
            raise HTTPException(status_code=404, detail="File record for current job not found")

        if not file_record.get('has_thumbnail') or not file_record.get('thumbnail_data'):
            raise HTTPException(status_code=404, detail="File has no thumbnail data")

        # Decode and stream
        try:
            raw = base64.b64decode(file_record['thumbnail_data'])
        except Exception:
            raise HTTPException(status_code=500, detail="Corrupt thumbnail data")

        fmt = file_record.get('thumbnail_format', 'png')
        return Response(
            content=raw,
            media_type=f"image/{fmt}",
            headers={
                "Cache-Control": "no-cache, max-age=0",  # always fresh for active job
                "Content-Disposition": f"inline; filename=printer_{printer_id}_current_thumbnail.{fmt}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get printer thumbnail", printer_id=str(printer_id), error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve printer thumbnail")