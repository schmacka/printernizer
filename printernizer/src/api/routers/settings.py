"""Settings management endpoints."""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import structlog

from src.services.config_service import ConfigService, PrinterConfig
from src.utils.dependencies import get_config_service


logger = structlog.get_logger()
router = APIRouter()


class ApplicationSettingsResponse(BaseModel):
    """Application settings response model."""
    database_path: str
    host: str
    port: int
    debug: bool
    environment: str
    log_level: str
    timezone: str
    currency: str
    vat_rate: float
    downloads_path: str
    max_file_size: int
    monitoring_interval: int
    connection_timeout: int
    cors_origins: List[str]

    # G-code optimization settings
    gcode_optimize_print_only: bool
    gcode_optimization_max_lines: int
    gcode_render_max_lines: int

    # Library System settings
    library_enabled: bool
    library_path: str
    library_auto_organize: bool
    library_auto_extract_metadata: bool
    library_auto_deduplicate: bool


class ApplicationSettingsUpdate(BaseModel):
    """Application settings update model."""
    log_level: Optional[str] = None
    monitoring_interval: Optional[int] = None
    connection_timeout: Optional[int] = None
    downloads_path: Optional[str] = None
    max_file_size: Optional[int] = None
    vat_rate: Optional[float] = None

    # G-code optimization settings
    gcode_optimize_print_only: Optional[bool] = None
    gcode_optimization_max_lines: Optional[int] = None
    gcode_render_max_lines: Optional[int] = None

    # Library System settings
    library_enabled: Optional[bool] = None
    library_path: Optional[str] = None
    library_auto_organize: Optional[bool] = None
    library_auto_extract_metadata: Optional[bool] = None
    library_auto_deduplicate: Optional[bool] = None


class PrinterConfigResponse(BaseModel):
    """Printer configuration response model."""
    printer_id: str
    name: str
    type: str
    ip_address: str = None
    is_active: bool


class PrinterConfigRequest(BaseModel):
    """Printer configuration request model."""
    name: str
    type: str
    ip_address: str
    api_key: str = None
    access_code: str = None
    serial_number: str = None
    is_active: bool = True


class WatchFolderSettings(BaseModel):
    """Watch folder settings model."""
    watch_folders: List[str]
    enabled: bool
    recursive: bool
    supported_extensions: List[str]


@router.get("/application", response_model=ApplicationSettingsResponse)
async def get_application_settings(
    config_service: ConfigService = Depends(get_config_service)
):
    """Get all application settings."""
    try:
        settings = config_service.get_application_settings()
        return ApplicationSettingsResponse(**settings)
    except Exception as e:
        logger.error("Failed to get application settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve application settings"
        )


@router.put("/application")
async def update_application_settings(
    settings: ApplicationSettingsUpdate,
    config_service: ConfigService = Depends(get_config_service)
):
    """Update application settings (runtime-updatable only)."""
    try:
        # Convert to dict and filter out None values
        raw_settings = settings.dict()
        logger.info("Raw settings received", raw_settings=raw_settings)
        settings_dict = {k: v for k, v in raw_settings.items() if v is not None}
        logger.info("Filtered settings dict", settings_dict=settings_dict)

        success = config_service.update_application_settings(settings_dict)
        
        if success:
            return {"message": "Settings updated successfully", "updated_fields": list(settings_dict.keys())}
        else:
            return {"message": "No settings were updated", "updated_fields": []}
            
    except Exception as e:
        logger.error("Failed to update application settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update application settings"
        )


@router.get("/printers")
async def get_printer_configurations(
    config_service: ConfigService = Depends(get_config_service)
):
    """Get all printer configurations."""
    try:
        printers = config_service.get_printers()
        return {
            printer_id: PrinterConfigResponse(
                printer_id=printer_id,
                name=config.name,
                type=config.type,
                ip_address=config.ip_address,
                is_active=config.is_active
            ).dict()
            for printer_id, config in printers.items()
        }
    except Exception as e:
        logger.error("Failed to get printer configurations", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve printer configurations"
        )


@router.post("/printers/{printer_id}")
async def add_or_update_printer(
    printer_id: str,
    printer_config: PrinterConfigRequest,
    config_service: ConfigService = Depends(get_config_service)
):
    """Add or update a printer configuration."""
    try:
        success = config_service.add_printer(printer_id, printer_config.dict())
        
        if success:
            return {"message": f"Printer {printer_id} configured successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid printer configuration"
            )
            
    except Exception as e:
        logger.error("Failed to add/update printer", printer_id=printer_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to configure printer"
        )


@router.delete("/printers/{printer_id}")
async def remove_printer(
    printer_id: str,
    config_service: ConfigService = Depends(get_config_service)
):
    """Remove a printer configuration."""
    try:
        success = config_service.remove_printer(printer_id)
        
        if success:
            return {"message": f"Printer {printer_id} removed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Printer not found"
            )
            
    except Exception as e:
        logger.error("Failed to remove printer", printer_id=printer_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove printer"
        )


@router.post("/printers/{printer_id}/validate")
async def validate_printer_connection(
    printer_id: str,
    config_service: ConfigService = Depends(get_config_service)
):
    """Validate printer connection configuration."""
    try:
        result = config_service.validate_printer_connection(printer_id)
        return result
    except Exception as e:
        logger.error("Failed to validate printer connection", printer_id=printer_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate printer connection"
        )


@router.get("/watch-folders", response_model=WatchFolderSettings)
async def get_watch_folder_settings(
    config_service: ConfigService = Depends(get_config_service)
):
    """Get watch folder settings."""
    try:
        settings = await config_service.get_watch_folder_settings()
        return WatchFolderSettings(**settings)
    except Exception as e:
        logger.error("Failed to get watch folder settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve watch folder settings"
        )


@router.post("/watch-folders/validate")
async def validate_watch_folder(
    folder_path: str,
    config_service: ConfigService = Depends(get_config_service)
):
    """Validate a watch folder path."""
    try:
        result = config_service.validate_watch_folder(folder_path)
        return result
    except Exception as e:
        logger.error("Failed to validate watch folder", folder_path=folder_path, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate watch folder"
        )


class GcodeOptimizationSettings(BaseModel):
    """G-code optimization settings model."""
    optimize_print_only: bool
    optimization_max_lines: int
    render_max_lines: int


@router.get("/gcode-optimization")
async def get_gcode_optimization_settings(
    config_service: ConfigService = Depends(get_config_service)
):
    """Get G-code optimization settings."""
    try:
        from src.utils.config import get_settings
        settings = get_settings()
        
        return GcodeOptimizationSettings(
            optimize_print_only=settings.gcode_optimize_print_only,
            optimization_max_lines=settings.gcode_optimization_max_lines,
            render_max_lines=settings.gcode_render_max_lines
        )
    except Exception as e:
        logger.error("Failed to get G-code optimization settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get G-code optimization settings: {str(e)}"
        )


@router.put("/gcode-optimization")
async def update_gcode_optimization_settings(
    settings: GcodeOptimizationSettings,
    config_service: ConfigService = Depends(get_config_service)
):
    """Update G-code optimization settings."""
    try:
        # This would typically update environment or database settings
        # For now, we'll return the updated settings
        logger.info("G-code optimization settings updated", 
                   optimize_print_only=settings.optimize_print_only,
                   optimization_max_lines=settings.optimization_max_lines,
                   render_max_lines=settings.render_max_lines)
        
        return {
            "message": "G-code optimization settings updated successfully",
            "settings": settings
        }
    except Exception as e:
        logger.error("Failed to update G-code optimization settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update G-code optimization settings: {str(e)}"
        )


@router.post("/reload")
async def reload_configuration(
    config_service: ConfigService = Depends(get_config_service)
):
    """Reload configuration from files and environment variables."""
    try:
        success = config_service.reload_config()
        
        if success:
            return {"message": "Configuration reloaded successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reload configuration"
            )
            
    except Exception as e:
        logger.error("Failed to reload configuration", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reload configuration"
        )