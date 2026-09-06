"""
Printernizer Connect API.

Endpoints for the Printernizer Connect desktop companion, which links a
PrusaSlicer installation to this server. Every endpoint here requires an API
key; the rest of the API is unauthenticated (see spec section 8.1).
"""
import json
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, Request
from fastapi import File as FastAPIFile, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict, ValidationError

from src.api.auth import require_api_key
from src.services.file_service import FileService
from src.services.printer_service import PrinterService
from src.utils.dependencies import get_file_service, get_printer_service
from src.utils.errors import PrinternizerError, success_response

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


# Formats a slicer can hand us. `.bgcode` is Prusa's binary G-code, the Core
# One's default export.
ALLOWED_EXPORT_EXTENSIONS = (".gcode", ".bgcode", ".3mf")


class ExportMetadata(BaseModel):
    """
    Metadata accompanying an export.

    Deliberately narrow: unknown fields are rejected rather than dropped, so a
    client is never told something was stored when it was not. M3 widens this
    alongside the migration that backs the extra fields.
    """
    model_config = ConfigDict(extra="forbid")

    is_business: bool = False
    notes: Optional[str] = None


@router.post("/exports", status_code=status.HTTP_201_CREATED)
async def create_export(
    file: UploadFile = FastAPIFile(..., description="Exported G-code or project"),
    metadata: str = Form("{}", description="JSON metadata for the export"),
    key=Depends(require_api_key),
    file_service: FileService = Depends(get_file_service),
):
    """
    Receive an export from Printernizer Connect and add it to the library.

    Delegates to the shared upload path, so thumbnails, metadata extraction and
    deduplication all behave exactly as they do for a browser upload.
    """
    if not file_service.settings.enable_upload:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="File uploads are disabled on this server",
        )

    filename = file.filename or ""
    if not filename.lower().endswith(ALLOWED_EXPORT_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(f"Unsupported export type: {filename}. "
                    f"Expected one of {', '.join(ALLOWED_EXPORT_EXTENSIONS)}"),
        )

    try:
        # model_validate, not ExportMetadata(**...): a JSON body of `[]`, `null`
        # or `"x"` would make the ** unpack raise TypeError and surface as a 500.
        parsed = ExportMetadata.model_validate(json.loads(metadata))
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Malformed metadata JSON: {exc}",
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid metadata: {exc}",
        )

    logger.info("Connect export received", filename=filename,
                key_id=key["id"], is_business=parsed.is_business)

    result = await file_service.upload_files(
        files=[file],
        is_business=parsed.is_business,
        notes=parsed.notes,
    )

    if result["success_count"] == 0:
        # PrinternizerError keeps `message` a string and puts the detail under
        # `details`, matching the project's error envelope. Passing a dict as
        # HTTPException.detail would put an object in `message`.
        raise PrinternizerError(
            message="Export upload failed",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="EXPORT_UPLOAD_FAILED",
            details={"failed_files": result["failed_files"]},
        )

    # Build the response from named fields rather than passing the uploader's
    # internal dict through: that dict carries `file_path`, an absolute
    # server-side filesystem path that has no business reaching a network
    # client, and its shape is free to change without notice.
    uploaded = result["uploaded_files"][0]
    return success_response(
        data={"file": {
            "file_id": uploaded.get("file_id"),
            "filename": uploaded.get("filename"),
            "file_size": uploaded.get("file_size"),
            "file_type": uploaded.get("file_type"),
            # The library's primary key. None when the library system is
            # disabled or ingestion failed — the file is stored either way.
            "checksum": uploaded.get("checksum"),
        }},
        status_code=status.HTTP_201_CREATED,
        message="Export added to library",
    )
