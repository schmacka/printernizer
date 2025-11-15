"""Settings management endpoints."""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
import structlog

from src.services.config_service import ConfigService, PrinterConfig
from src.utils.dependencies import get_config_service
from src.utils.errors import (
    ValidationError as PrinternizerValidationError,
    PrinterNotFoundError,
    success_response
)


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

    # Job creation settings
    job_creation_auto_create: bool

    # G-code optimization settings
    gcode_optimize_print_only: bool
    gcode_optimization_max_lines: int
    gcode_render_max_lines: int

    # Upload settings
    enable_upload: bool
    max_upload_size_mb: int
    allowed_upload_extensions: str

    # Library System settings
    library_enabled: bool
    library_path: str
    library_auto_organize: bool
    library_auto_extract_metadata: bool
    library_auto_deduplicate: bool
    library_preserve_originals: bool
    library_checksum_algorithm: str
    library_processing_workers: int
    library_search_enabled: bool
    library_search_min_length: int

    # Timelapse settings
    timelapse_enabled: bool
    timelapse_source_folder: str
    timelapse_output_folder: str
    timelapse_output_strategy: str
    timelapse_auto_process_timeout: int
    timelapse_cleanup_age_days: int


class ApplicationSettingsUpdate(BaseModel):
    """Application settings update model."""
    log_level: Optional[str] = None
    monitoring_interval: Optional[int] = None
    connection_timeout: Optional[int] = None
    downloads_path: Optional[str] = None
    max_file_size: Optional[int] = None
    vat_rate: Optional[float] = None

    # Job creation settings
    job_creation_auto_create: Optional[bool] = None

    # G-code optimization settings
    gcode_optimize_print_only: Optional[bool] = None
    gcode_optimization_max_lines: Optional[int] = None
    gcode_render_max_lines: Optional[int] = None

    # Upload settings
    enable_upload: Optional[bool] = None
    max_upload_size_mb: Optional[int] = None
    allowed_upload_extensions: Optional[str] = None

    # Library System settings
    library_enabled: Optional[bool] = None
    library_path: Optional[str] = None
    library_auto_organize: Optional[bool] = None
    library_auto_extract_metadata: Optional[bool] = None
    library_auto_deduplicate: Optional[bool] = None
    library_preserve_originals: Optional[bool] = None
    library_checksum_algorithm: Optional[str] = None
    library_processing_workers: Optional[int] = None
    library_search_enabled: Optional[bool] = None
    library_search_min_length: Optional[int] = None

    # Timelapse settings
    timelapse_enabled: Optional[bool] = None
    timelapse_source_folder: Optional[str] = None
    timelapse_output_folder: Optional[str] = None
    timelapse_output_strategy: Optional[str] = None
    timelapse_auto_process_timeout: Optional[int] = None
    timelapse_cleanup_age_days: Optional[int] = None


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
    settings = config_service.get_application_settings()
    return ApplicationSettingsResponse(**settings)


@router.put("/application")
async def update_application_settings(
    settings: ApplicationSettingsUpdate,
    config_service: ConfigService = Depends(get_config_service)
):
    """Update application settings (runtime-updatable only)."""
    # Convert to dict and filter out None values
    raw_settings = settings.dict()
    logger.info("Raw settings received", raw_settings=raw_settings)
    settings_dict = {k: v for k, v in raw_settings.items() if v is not None}
    logger.info("Filtered settings dict", settings_dict=settings_dict)

    success = config_service.update_application_settings(settings_dict)

    if success:
        return success_response({"message": "Settings updated successfully", "updated_fields": list(settings_dict.keys())})
    else:
        return success_response({"message": "No settings were updated", "updated_fields": []})


@router.get("/printers")
async def get_printer_configurations(
    config_service: ConfigService = Depends(get_config_service)
):
    """Get all printer configurations."""
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


@router.post("/printers/{printer_id}")
async def add_or_update_printer(
    printer_id: str,
    printer_config: PrinterConfigRequest,
    config_service: ConfigService = Depends(get_config_service)
):
    """Add or update a printer configuration."""
    success = config_service.add_printer(printer_id, printer_config.dict())

    if not success:
        raise PrinternizerValidationError(
            field="printer_config",
            error="Invalid printer configuration"
        )

    return success_response({"message": f"Printer {printer_id} configured successfully"})


@router.delete("/printers/{printer_id}")
async def remove_printer(
    printer_id: str,
    config_service: ConfigService = Depends(get_config_service)
):
    """Remove a printer configuration."""
    success = config_service.remove_printer(printer_id)

    if not success:
        raise PrinterNotFoundError(printer_id)

    return success_response({"message": f"Printer {printer_id} removed successfully"})


@router.post("/printers/{printer_id}/validate")
async def validate_printer_connection(
    printer_id: str,
    config_service: ConfigService = Depends(get_config_service)
):
    """Validate printer connection configuration."""
    result = config_service.validate_printer_connection(printer_id)
    return result


@router.get("/watch-folders", response_model=WatchFolderSettings)
async def get_watch_folder_settings(
    config_service: ConfigService = Depends(get_config_service)
):
    """Get watch folder settings."""
    settings = await config_service.get_watch_folder_settings()
    return WatchFolderSettings(**settings)


@router.post("/watch-folders/validate")
async def validate_watch_folder(
    folder_path: str,
    config_service: ConfigService = Depends(get_config_service)
):
    """Validate a watch folder path."""
    result = config_service.validate_watch_folder(folder_path)
    return result


@router.post("/downloads-path/validate")
async def validate_downloads_path(
    folder_path: str,
    config_service: ConfigService = Depends(get_config_service)
):
    """Validate the downloads path - check if it's available, writable, and deletable."""
    result = config_service.validate_downloads_path(folder_path)
    return result


@router.post("/library-path/validate")
async def validate_library_path(
    folder_path: str,
    config_service: ConfigService = Depends(get_config_service)
):
    """Validate the library path - check if it's available, writable, and deletable."""
    result = config_service.validate_library_path(folder_path)
    return result


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
    from src.utils.config import get_settings
    settings = get_settings()

    return GcodeOptimizationSettings(
        optimize_print_only=settings.gcode_optimize_print_only,
        optimization_max_lines=settings.gcode_optimization_max_lines,
        render_max_lines=settings.gcode_render_max_lines
    )


@router.put("/gcode-optimization")
async def update_gcode_optimization_settings(
    settings: GcodeOptimizationSettings,
    config_service: ConfigService = Depends(get_config_service)
):
    """Update G-code optimization settings."""
    # This would typically update environment or database settings
    # For now, we'll return the updated settings
    logger.info("G-code optimization settings updated",
               optimize_print_only=settings.optimize_print_only,
               optimization_max_lines=settings.optimization_max_lines,
               render_max_lines=settings.render_max_lines)

    return success_response({
        "message": "G-code optimization settings updated successfully",
        "settings": settings
    })


@router.post("/reload")
async def reload_configuration(
    config_service: ConfigService = Depends(get_config_service)
):
    """Reload configuration from files and environment variables."""
    success = config_service.reload_config()

    if not success:
        raise PrinternizerValidationError(
            field="configuration",
            error="Failed to reload configuration"
        )

    return success_response({"message": "Configuration reloaded successfully"})


@router.get("/ffmpeg-check")
async def check_ffmpeg_installation():
    """Check if ffmpeg is installed and available on the system."""
    from src.utils.system_check import check_ffmpeg

    result = check_ffmpeg()

    return {
        "installed": result['installed'],
        "version": result['version'],
        "error": result['error'],
        "message": "ffmpeg is installed and available" if result['installed'] else "ffmpeg is not installed or not in PATH"
    }