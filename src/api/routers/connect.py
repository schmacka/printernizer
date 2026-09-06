"""
Printernizer Connect API.

Endpoints for the Printernizer Connect desktop companion, which links a
PrusaSlicer installation to this server. Every endpoint here requires an API
key; the rest of the API is unauthenticated (see spec section 8.1).
"""
from typing import Any, Dict, List

import structlog
from fastapi import APIRouter, Depends, Request

from src.api.auth import require_api_key
from src.services.printer_service import PrinterService
from src.utils.dependencies import get_printer_service
from src.utils.errors import success_response

logger = structlog.get_logger()
router = APIRouter()

# Oldest Printernizer Connect release this server will talk to.
MIN_CONNECT_VERSION = "0.1.0"


@router.get("/info")
async def get_connect_info(
    request: Request,
    key=Depends(require_api_key),
    printer_service: PrinterService = Depends(get_printer_service),
):
    """
    Report server capabilities and the printer fleet.

    Connect calls this before every command to check version compatibility and
    to resolve printer ids.
    """
    printers: List[Dict[str, Any]] = []
    for printer in await printer_service.list_printers():
        printer_type = getattr(printer.type, "value", printer.type)
        printers.append({
            "id": printer.id,
            "name": printer.name,
            "type": printer_type,
            "is_active": printer.is_active,
        })

    return success_response(data={
        "server_version": request.app.version,
        "min_connect_version": MIN_CONNECT_VERSION,
        "capabilities": {
            "exports": True,
            "profiles": False,   # M4
            "printhost": False,  # M5
        },
        "printers": printers,
    })
