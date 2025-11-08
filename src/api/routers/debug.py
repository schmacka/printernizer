"""Temporary debug endpoints for development (thumbnail/status introspection).

Remove this file before production if not needed.
"""

from typing import Optional, List
from fastapi import APIRouter, Request, Query
import structlog

from src.utils.errors import (
    PrinterNotFoundError,
    FileNotFoundError,
    ServiceUnavailableError
)

logger = structlog.get_logger()

router = APIRouter()


@router.get("/printers/{printer_id}/thumbnail", tags=["Debug"], summary="Debug current printer thumbnail linkage")
async def debug_printer_thumbnail(
    request: Request,
    printer_id: str,
    include_file_record: bool = Query(False, description="Include full file record (excluding raw base64 data)"),
    include_base64_lengths: bool = Query(False, description="Include thumbnail base64 length if present"),
):
    """Return raw status + file record & derived thumbnail info for a printer.

    Helps verify why a dashboard thumbnail might not be appearing.
    """
    printer_service = request.app.state.printer_service
    file_service = getattr(request.app.state, 'file_service', None)

    instance = printer_service.printer_instances.get(printer_id)
    if not instance:
        raise PrinterNotFoundError(printer_id)

    status = getattr(instance, 'last_status', None)
    response = {
        "printer_id": printer_id,
        "is_connected": instance.is_connected,
        "status_available": bool(status),
        "reasons": []  # accumulate potential causes for missing thumbnail
    }

    file_record = None
    if status:
        status_dict = status.model_dump() if hasattr(status, 'model_dump') else status.__dict__
        response["status_raw"] = status_dict
        file_id = status_dict.get("current_job_file_id")
        response["current_job_file_id"] = file_id
        response["current_job_has_thumbnail"] = status_dict.get("current_job_has_thumbnail")
        response["current_job_thumbnail_url"] = status_dict.get("current_job_thumbnail_url")

        if file_id and file_service:
            file_record = await file_service.get_file_by_id(file_id)
            if not file_record:
                response["reasons"].append("File record not found for current_job_file_id")
            else:
                response["file_record_has_thumbnail"] = file_record.get("has_thumbnail")
                if not file_record.get("has_thumbnail"):
                    response["reasons"].append("File record exists but has_thumbnail is False")
                thumb_data = file_record.get("thumbnail_data")
                if include_base64_lengths and thumb_data:
                    response["thumbnail_base64_length"] = len(thumb_data)
        else:
            if not file_id:
                response["reasons"].append("Status has no current_job_file_id")
            if not status_dict.get("current_job_has_thumbnail"):
                response["reasons"].append("Status indicates no thumbnail")
    else:
        response["reasons"].append("Printer has no last_status yet")

    if include_file_record and file_record:
        # Exclude big base64 blob unless explicitly requested (we only send length above)
        redacted = {k: v for k, v in file_record.items() if k != "thumbnail_data"}
        response["file_record"] = redacted

    return response


@router.get("/files/{file_id}", tags=["Debug"], summary="Debug file record & thumbnail flags")
async def debug_file(
    request: Request,
    file_id: str,
    include_base64_length: bool = Query(False, description="Include base64 length instead of data")
):
    """Debug file record and thumbnail information.

    Returns file record with thumbnail metadata for debugging purposes.
    Excludes thumbnail data by default to reduce response size.

    Args:
        request: FastAPI request object.
        file_id: File identifier to inspect.
        include_base64_length: If True, includes length of base64 thumbnail data.

    Returns:
        File record dictionary with thumbnail metadata.

    Raises:
        FileNotFoundError: If file not found.
        ServiceUnavailableError: If file service unavailable.
    """
    file_service = getattr(request.app.state, 'file_service', None)
    if not file_service:
        raise ServiceUnavailableError("File service not available")

    record = await file_service.get_file_by_id(file_id)
    if not record:
        raise FileNotFoundError(file_id)

    resp = {k: v for k, v in record.items() if k != 'thumbnail_data'}
    if include_base64_length and record.get('thumbnail_data'):
        resp['thumbnail_base64_length'] = len(record['thumbnail_data'])
    return resp


@router.get("/thumbnail-processing-log", tags=["Debug"], summary="Get thumbnail processing status log")
async def get_thumbnail_processing_log(
    request: Request,
    limit: int = Query(20, description="Maximum number of log entries to return", ge=1, le=100)
):
    """Return recent thumbnail processing attempts with status and details.

    Helps debug why thumbnail extraction might be failing for specific files.
    Shows the last processing attempts with timestamps, file types, and error details.
    """
    from pathlib import Path

    file_service = getattr(request.app.state, 'file_service', None)
    if not file_service:
        raise ServiceUnavailableError("File service not available")

    log_entries = file_service.get_thumbnail_processing_log(limit)

    # Transform entries to match frontend expectations
    transformed_entries = []
    for entry in log_entries:
        status = entry.get('status', 'unknown')
        transformed = {
            'timestamp': entry.get('timestamp'),
            'success': status == 'success',
            'filename': Path(entry.get('file_path', '')).name,
            'file_type': entry.get('file_extension', 'unknown'),
            'file_id': entry.get('file_id'),
        }

        # Add error field only if failed
        if status == 'failed' and entry.get('details'):
            transformed['error'] = entry.get('details')

        transformed_entries.append(transformed)

    # Calculate summary statistics
    total_entries = len(log_entries)
    successful = sum(1 for e in log_entries if e.get('status') == 'success')
    failed = sum(1 for e in log_entries if e.get('status') == 'failed')
    success_rate = round((successful / total_entries * 100) if total_entries > 0 else 0, 1)

    # Count file types
    file_type_counts = {}
    for entry in log_entries:
        file_ext = entry.get('file_extension', 'unknown')
        file_type_counts[file_ext] = file_type_counts.get(file_ext, 0) + 1

    return {
        "summary": {
            "total_entries": total_entries,
            "successful": successful,
            "failed": failed,
            "success_rate": success_rate,
            "file_types": file_type_counts
        },
        "recent_attempts": transformed_entries
    }
