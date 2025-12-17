"""Setup wizard endpoints for first-run configuration."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
import structlog

from src.utils.dependencies import (
    get_database,
    get_config_service,
    get_printer_service
)
from src.database.database import Database
from src.services.config_service import ConfigService
from src.services.printer_service import PrinterService
from src.utils.errors import success_response


logger = structlog.get_logger()
router = APIRouter()


class SetupStatusResponse(BaseModel):
    """Setup wizard status response."""
    should_show_wizard: bool
    setup_completed: bool
    has_printers: bool
    reason: str


class SetupCompleteRequest(BaseModel):
    """Request to mark setup as complete."""
    skip_wizard: bool = False


@router.get("/status")
async def get_setup_status(
    request: Request,
    database: Database = Depends(get_database),
    printer_service: PrinterService = Depends(get_printer_service)
) -> SetupStatusResponse:
    """
    Check if the setup wizard should be displayed.
    
    Wizard shows when ANY of these conditions are met:
    - No printers configured
    - setup_wizard_completed flag is false
    """
    try:
        # Check if wizard has been completed
        async with database._connection.execute(
            "SELECT value FROM settings WHERE key = 'setup_wizard_completed'"
        ) as cursor:
            row = await cursor.fetchone()
            setup_completed = row is not None and row[0].lower() == 'true'
        
        # Check if any printers are configured
        printers = await printer_service.get_all_printers()
        has_printers = len(printers) > 0
        
        # Determine if wizard should show
        if not setup_completed:
            should_show = True
            reason = "Setup wizard has not been completed"
        elif not has_printers:
            should_show = True
            reason = "No printers configured"
        else:
            should_show = False
            reason = "Setup already completed with printers configured"
        
        return SetupStatusResponse(
            should_show_wizard=should_show,
            setup_completed=setup_completed,
            has_printers=has_printers,
            reason=reason
        )
    except Exception as e:
        logger.error("Failed to get setup status", error=str(e))
        # Default to showing wizard on error (fresh install scenario)
        return SetupStatusResponse(
            should_show_wizard=True,
            setup_completed=False,
            has_printers=False,
            reason="Unable to determine status, assuming fresh install"
        )


@router.post("/complete")
async def complete_setup(
    request_body: SetupCompleteRequest,
    database: Database = Depends(get_database)
):
    """
    Mark the setup wizard as completed.
    
    This prevents the wizard from showing automatically on subsequent visits.
    """
    try:
        async with database._connection.execute(
            """
            INSERT INTO settings (key, value, category, description)
            VALUES ('setup_wizard_completed', 'true', 'system', 'Whether the initial setup wizard has been completed')
            ON CONFLICT(key) DO UPDATE SET value = 'true', updated_at = CURRENT_TIMESTAMP
            """
        ):
            pass
        await database._connection.commit()
        
        action = "skipped" if request_body.skip_wizard else "completed"
        logger.info(f"Setup wizard {action}")
        
        return success_response({
            "message": f"Setup wizard {action} successfully",
            "setup_completed": True
        })
    except Exception as e:
        logger.error("Failed to complete setup", error=str(e))
        raise


@router.post("/reset")
async def reset_setup(
    database: Database = Depends(get_database)
):
    """
    Reset the setup wizard so it can be run again.
    
    This sets setup_wizard_completed to false.
    """
    try:
        async with database._connection.execute(
            """
            INSERT INTO settings (key, value, category, description)
            VALUES ('setup_wizard_completed', 'false', 'system', 'Whether the initial setup wizard has been completed')
            ON CONFLICT(key) DO UPDATE SET value = 'false', updated_at = CURRENT_TIMESTAMP
            """
        ):
            pass
        await database._connection.commit()
        
        logger.info("Setup wizard reset")
        
        return success_response({
            "message": "Setup wizard reset successfully",
            "setup_completed": False
        })
    except Exception as e:
        logger.error("Failed to reset setup", error=str(e))
        raise


@router.get("/defaults")
async def get_setup_defaults(
    config_service: ConfigService = Depends(get_config_service)
) -> Dict[str, Any]:
    """
    Get default configuration values for the setup wizard.
    
    Returns environment-aware defaults for paths and settings.
    """
    from src.utils.config import get_settings
    import os
    
    settings = get_settings()
    
    # Detect deployment environment
    deployment_mode = os.getenv("DEPLOYMENT_MODE", "standalone")
    is_docker = os.path.exists("/.dockerenv")
    is_ha_addon = os.getenv("HASSIO_TOKEN") is not None
    
    # Determine environment type
    if is_ha_addon:
        environment = "home_assistant"
    elif is_docker:
        environment = "docker"
    else:
        environment = "standalone"
    
    return {
        "environment": environment,
        "paths": {
            "downloads": settings.downloads_path,
            "library": settings.library_path
        },
        "features": {
            "timelapse_enabled": settings.timelapse_enabled,
            "timelapse_source_folder": settings.timelapse_source_folder,
            "timelapse_output_folder": settings.timelapse_output_folder,
            "library_enabled": settings.library_enabled
        },
        "environment_info": {
            "is_docker": is_docker,
            "is_ha_addon": is_ha_addon,
            "deployment_mode": deployment_mode
        }
    }
