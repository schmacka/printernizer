"""Printer management endpoints."""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import structlog

from src.models.printer import Printer, PrinterType, PrinterStatus
from src.services.printer_service import PrinterService
from src.utils.dependencies import get_printer_service


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


@router.get("/", response_model=List[PrinterResponse])
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


@router.post("/", response_model=PrinterResponse, status_code=status.HTTP_201_CREATED)
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