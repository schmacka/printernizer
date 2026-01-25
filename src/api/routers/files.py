"""File management endpoints - Drucker-Dateien system."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File as FastAPIFile, Form
from fastapi.responses import Response
from pydantic import BaseModel
import structlog
import base64

from src.models.file import File, FileStatus, FileSource, WatchFolderSettings, WatchFolderStatus, WatchFolderItem
from src.services.file_service import FileService
from src.services.config_service import ConfigService
from src.services.printer_service import PrinterService
from src.models.printer import PrinterType
from src.utils.dependencies import get_file_service, get_config_service, get_printer_service
from src.utils.errors import (
    FileNotFoundError as PrinternizerFileNotFoundError,
    FileDownloadError,
    FileProcessingError,
    NotFoundError,
    ValidationError as PrinternizerValidationError,
    success_response
)


logger = structlog.get_logger()
router = APIRouter()


# Printer capabilities by type (bed size in mm)
PRINTER_CAPABILITIES = {
    PrinterType.BAMBU_LAB: {
        'bed_size_x': 256,
        'bed_size_y': 256,
        'bed_size_z': 256,
        'name': 'Bambu Lab A1'
    },
    PrinterType.PRUSA_CORE: {
        'bed_size_x': 250,
        'bed_size_y': 220,
        'bed_size_z': 220,
        'name': 'Prusa Core One'
    }
}


def get_printer_capabilities(printer_type: PrinterType) -> Dict[str, Any]:
    """
    Get printer capabilities based on printer type.

    Args:
        printer_type: Type of printer

    Returns:
        Dictionary with printer capabilities including bed dimensions
    """
    return PRINTER_CAPABILITIES.get(
        printer_type,
        {
            'bed_size_x': 200,
            'bed_size_y': 200,
            'bed_size_z': 200,
            'name': 'Unknown'
        }
    )


class FileResponse(BaseModel):
    """Response model for file data."""
    id: str
    printer_id: Optional[str] = None
    filename: str
    source: FileSource
    status: FileStatus
    file_size: Optional[int] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    downloaded_at: Optional[str] = None
    created_at: Optional[str] = None
    watch_folder_path: Optional[str] = None
    relative_path: Optional[str] = None
    modified_time: Optional[str] = None
    
    # Thumbnail fields
    has_thumbnail: bool = False
    thumbnail_width: Optional[int] = None
    thumbnail_height: Optional[int] = None
    thumbnail_format: Optional[str] = None


class PaginationResponse(BaseModel):
    """Pagination information."""
    page: int
    limit: int
    total_items: int
    total_pages: int


class FileListResponse(BaseModel):
    """Response model for file list with pagination."""
    files: List[FileResponse]
    total_count: int
    pagination: PaginationResponse


@router.get("", response_model=FileListResponse)
async def list_files(
    printer_id: Optional[str] = Query(None, description="Filter by printer ID"),
    status: Optional[FileStatus] = Query(None, description="Filter by file status"),
    source: Optional[FileSource] = Query(None, description="Filter by file source"),
    has_thumbnail: Optional[bool] = Query(None, description="Filter by thumbnail availability"),
    search: Optional[str] = Query(None, description="Search by filename"),
    limit: Optional[int] = Query(50, description="Limit number of results"),
    order_by: Optional[str] = Query("created_at", description="Order by field"),
    order_dir: Optional[str] = Query("desc", description="Order direction (asc/desc)"),
    page: Optional[int] = Query(1, description="Page number"),
    file_service: FileService = Depends(get_file_service)
):
    """List files from printers and local storage."""
    logger.info("Listing files", printer_id=printer_id, status=status, source=source,
               has_thumbnail=has_thumbnail, search=search, limit=limit, page=page)

    # Get paginated files with total count (optimized to avoid fetching all records twice)
    paginated_files, total_items = await file_service.get_files_with_count(
        printer_id=printer_id,
        status=status,
        source=source,
        has_thumbnail=has_thumbnail,
        search=search,
        limit=limit,
        order_by=order_by,
        order_dir=order_dir,
        page=page
    )
    total_pages = max(1, (total_items + limit - 1) // limit) if limit else 1

    logger.info("Got files from service", total=total_items, page_count=len(paginated_files))

    # VERIFICATION: Check for missing file_type and add fallback
    import os
    missing_file_type = [f for f in paginated_files if not f.get('file_type')]
    if missing_file_type:
        logger.warning("Files missing file_type field",
                      count=len(missing_file_type),
                      file_ids=[f.get('id') for f in missing_file_type[:5]])

    # Ensure all files have file_type before serialization (final safety net)
    for file_data in paginated_files:
        if not file_data.get('file_type') and file_data.get('filename'):
            _, ext = os.path.splitext(file_data['filename'])
            file_data['file_type'] = ext.lstrip('.').lower() if ext else None
            logger.debug("Added missing file_type",
                        file_id=file_data.get('id'),
                        file_type=file_data['file_type'])

    file_list = [FileResponse.model_validate(file) for file in paginated_files]

    logger.info("Validated files", count=len(file_list))

    # Log sample for verification (only in debug mode)
    if file_list:
        sample = file_list[0]
        logger.debug("Sample file response",
                    file_id=sample.id,
                    file_type=sample.file_type,
                    filename=sample.filename)

    return {
        "files": file_list,
        "total_count": total_items,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_items": total_items,
            "total_pages": total_pages
        }
    }


@router.get("/statistics")
async def get_file_statistics(
    file_service: FileService = Depends(get_file_service)
):
    """Get file management statistics."""
    stats = await file_service.get_file_statistics()
    return success_response({
        "statistics": stats,
        "timestamp": "2025-09-26T18:55:00Z"
    })


@router.get("/downloads/{download_id}/progress")
async def get_download_progress(
    download_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """
    Get download progress for an active or recent download.

    Args:
        download_id: The download ID (file_id format: {printer_id}_{filename})

    Returns:
        Download progress information including:
        - download_id: The download identifier
        - progress: Percentage complete (0-100)
        - status: Current status (starting/downloading/completed/failed)
        - bytes_downloaded: Bytes transferred so far
        - total_bytes: Total expected bytes

    Raises:
        NotFoundError: If download_id is not found in active or recent downloads
    """
    logger.info("Getting download progress", download_id=download_id)

    status_info = await file_service.get_download_status(download_id)

    if status_info.get("status") == "not_found":
        raise NotFoundError(
            resource_type="download",
            resource_id=download_id,
            details={"reason": "Download not found or expired"}
        )

    return success_response({
        "download_id": download_id,
        "progress": status_info.get("progress", 0),
        "status": status_info.get("status", "unknown"),
        "bytes_downloaded": status_info.get("bytes_downloaded", 0),
        "total_bytes": status_info.get("total_bytes", 0)
    })


@router.get("/{file_id}", response_model=FileResponse)
async def get_file_by_id(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """Get file information by ID."""
    file_data = await file_service.get_file_by_id(file_id)
    if not file_data:
        raise PrinternizerFileNotFoundError(file_id)
    return FileResponse.model_validate(file_data)


@router.post("/{file_id}/download")
async def download_file(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """Download a file from printer to local storage."""
    # Parse file_id to extract printer_id and filename
    # file_id format: "{printer_id}_{filename}"
    if "_" not in file_id:
        raise PrinternizerValidationError(
            field="file_id",
            error="Invalid file_id format - expected format: {printer_id}_{filename}"
        )

    # Split on the first underscore to separate printer_id from filename
    parts = file_id.split("_", 1)
    printer_id = parts[0]
    filename = parts[1]

    logger.info("Downloading file",
               file_id=file_id, printer_id=printer_id, filename=filename)

    result = await file_service.download_file(printer_id, filename)

    if result.get('status') != 'success':
        raise FileDownloadError(
            filename=filename,
            printer_id=printer_id,
            reason=result.get('message', 'Download operation failed')
        )
    return success_response({"status": "downloaded", "local_path": result.get('local_path')})


@router.post("/sync")
async def sync_printer_files(
    printer_id: Optional[str] = Query(None, description="Sync specific printer, or all if not specified"),
    file_service: FileService = Depends(get_file_service)
):
    """Synchronize file list with printers."""
    await file_service.sync_printer_files(printer_id)
    return success_response({"status": "synced"})


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_files(
    files: List[UploadFile] = FastAPIFile(..., description="Files to upload"),
    is_business: bool = Form(False, description="Mark files as business orders"),
    notes: Optional[str] = Form(None, description="Optional notes for uploaded files"),
    file_service: FileService = Depends(get_file_service)
):
    """
    Upload files to the library via drag-and-drop or file picker.

    Accepts multiple files and validates:
    - File type (must be .3mf, .stl, .gcode, .obj, or .ply)
    - File size (max configurable via MAX_UPLOAD_SIZE_MB)
    - Duplicate filenames (rejects if exists)

    After upload, automatically:
    - Extracts thumbnails
    - Extracts metadata
    - Adds to library

    Returns:
        Upload results with successful and failed files
    """
    logger.info(
        "Upload request received",
        file_count=len(files),
        is_business=is_business,
        has_notes=notes is not None
    )

    # Validate that uploads are enabled
    if not file_service.settings.enable_upload:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="File uploads are disabled on this server"
        )

    # Call file service to handle upload
    result = await file_service.upload_files(
        files=files,
        is_business=is_business,
        notes=notes
    )

    # Check if any files were uploaded successfully
    if result["success_count"] == 0:
        # All uploads failed
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "All file uploads failed",
                "failed_files": result["failed_files"]
            }
        )

    # Return results (partial success is OK)
    return {
        "message": f"Uploaded {result['success_count']} of {result['total_count']} files",
        "uploaded_files": result["uploaded_files"],
        "failed_files": result["failed_files"],
        "success_count": result["success_count"],
        "failure_count": result["failure_count"]
    }


@router.get("/{file_id}/thumbnail")
async def get_file_thumbnail(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """Get thumbnail image for a file."""
    file_data = await file_service.get_file_by_id(file_id)

    if not file_data:
        raise PrinternizerFileNotFoundError(file_id)

    if not file_data.get('has_thumbnail') or not file_data.get('thumbnail_data'):
        raise PrinternizerFileNotFoundError(file_id, details={"reason": "no_thumbnail"})

    # Decode base64 thumbnail data
    try:
        thumbnail_data = base64.b64decode(file_data['thumbnail_data'])
    except Exception as e:
        logger.error("Failed to decode thumbnail data", file_id=file_id, error=str(e))
        raise FileProcessingError(
            filename=file_id,
            operation="decode_thumbnail",
            reason="Invalid thumbnail data"
        )

    # Determine content type
    thumbnail_format = file_data.get('thumbnail_format', 'png')
    content_type = f"image/{thumbnail_format}"

    # Return image response
    return Response(
        content=thumbnail_data,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
            "Content-Disposition": f"inline; filename=thumbnail_{file_id}.{thumbnail_format}"
        }
    )


@router.get("/{file_id}/thumbnail/animated")
async def get_file_animated_thumbnail(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """Get animated GIF thumbnail for a file (multi-angle preview)."""
    file_data = await file_service.get_file_by_id(file_id)

    if not file_data:
        raise PrinternizerFileNotFoundError(file_id)

    file_path = file_data.get('file_path')
    file_type = file_data.get('file_type', '')

    if not file_path:
        raise PrinternizerFileNotFoundError(file_id, details={"reason": "no_file_path"})

    # Only support animated previews for STL and 3MF files
    # File types in database include the dot prefix (e.g., '.stl', '.3mf')
    if file_type.lower() not in ['.stl', '.3mf']:
        raise FileProcessingError(
            filename=file_id,
            operation="generate_animated_thumbnail",
            reason=f"Animated thumbnails not supported for {file_type} files"
        )

    try:
        # Get or generate animated preview using file service's thumbnail service
        # Remove leading dot from file_type for preview service
        file_type_clean = file_type.lstrip('.')
        
        gif_bytes = await file_service.thumbnail.preview_render_service.get_or_generate_animated_preview(
            file_path,
            file_type_clean,
            size=(200, 200)
        )

        if not gif_bytes:
            raise FileProcessingError(
                filename=file_id,
                operation="generate_animated_thumbnail",
                reason="Failed to generate animated preview"
            )

        # Return GIF response
        return Response(
            content=gif_bytes,
            media_type="image/gif",
            headers={
                "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
                "Content-Disposition": f"inline; filename=thumbnail_animated_{file_id}.gif"
            }
        )

    except Exception as e:
        logger.error("Failed to get animated thumbnail",
                    file_id=file_id,
                    error=str(e),
                    exc_info=True)
        raise FileProcessingError(
            filename=file_id,
            operation="get_animated_thumbnail",
            reason=str(e)
        )


@router.get("/{file_id}/metadata")
async def get_file_metadata(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """Get metadata for a file."""
    file_data = await file_service.get_file_by_id(file_id)

    if not file_data:
        raise PrinternizerFileNotFoundError(file_id)

    # Return metadata along with basic file info
    metadata = file_data.get('metadata') or {}

    # Add basic file information to metadata response
    response_data = {
        "file_id": file_id,
        "filename": file_data.get('filename'),
        "file_size": file_data.get('file_size'),
        "file_type": file_data.get('file_type'),
        "created_at": file_data.get('created_at'),
        "has_thumbnail": file_data.get('has_thumbnail', False),
        "metadata": metadata
    }

    return response_data


@router.post("/{file_id}/process-thumbnails")
async def process_file_thumbnails(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """Manually trigger thumbnail processing for a file."""
    file_data = await file_service.get_file_by_id(file_id)

    if not file_data:
        raise PrinternizerFileNotFoundError(file_id)

    file_path = file_data.get('file_path')
    if not file_path:
        raise PrinternizerValidationError(
            field="file_path",
            error="File not available locally for processing"
        )

    success = await file_service.process_file_thumbnails(file_path, file_id)

    if success:
        return success_response({"status": "success", "message": "Thumbnails processed successfully"})
    else:
        raise FileProcessingError(
            filename=file_id,
            operation="process_thumbnails",
            reason="Failed to process thumbnails"
        )


@router.post("/{file_id}/thumbnail/extract")
async def extract_file_thumbnail(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """
    Extract embedded thumbnail from file (3MF, BGCode, G-code).

    This endpoint specifically extracts thumbnails that are embedded in the file
    itself, such as those in 3MF or BGCode files. It does not generate thumbnails.

    Supported formats:
    - 3MF files (embedded PNG thumbnails)
    - BGCode files (embedded thumbnails)
    - G-code files (Base64 encoded thumbnails in comments)
    """
    file_data = await file_service.get_file_by_id(file_id)

    if not file_data:
        raise PrinternizerFileNotFoundError(file_id)

    file_path = file_data.get('file_path')
    if not file_path:
        raise PrinternizerValidationError(
            field="file_path",
            error="File not available locally for thumbnail extraction"
        )

    # Get the thumbnail service from file service
    thumbnail_service = file_service.thumbnail_service
    if not thumbnail_service:
        raise FileProcessingError(
            filename=file_id,
            operation="extract_thumbnail",
            reason="Thumbnail service not available"
        )

    # Use the BambuParser to extract embedded thumbnails
    try:
        from src.services.bambu_parser import BambuParser
        parser = BambuParser()
        parse_result = await parser.parse_file(file_path)

        if not parse_result['success']:
            raise FileProcessingError(
                filename=file_id,
                operation="extract_thumbnail",
                reason=parse_result.get('error', 'Failed to parse file')
            )

        thumbnails = parse_result['thumbnails']

        if not thumbnails:
            return success_response({
                "success": False,
                "method": "extracted",
                "message": "No embedded thumbnails found in file"
            })

        # Get best thumbnail and update database
        best_thumbnail = parser.get_thumbnail_by_size(thumbnails, (200, 200))

        if best_thumbnail:
            update_data = {
                'has_thumbnail': True,
                'thumbnail_data': best_thumbnail['data'],
                'thumbnail_width': best_thumbnail['width'],
                'thumbnail_height': best_thumbnail['height'],
                'thumbnail_format': best_thumbnail.get('format', 'png'),
                'thumbnail_source': 'embedded'
            }

            await file_service.database.update_file(file_id, update_data)

            return success_response({
                "success": True,
                "method": "extracted",
                "thumbnail_url": f"/api/v1/files/{file_id}/thumbnail",
                "thumbnail_count": len(thumbnails),
                "dimensions": {
                    "width": best_thumbnail['width'],
                    "height": best_thumbnail['height']
                },
                "message": f"Successfully extracted {len(thumbnails)} thumbnail(s) from file"
            })
        else:
            raise FileProcessingError(
                filename=file_id,
                operation="extract_thumbnail",
                reason="Failed to select best thumbnail from extracted thumbnails"
            )

    except Exception as e:
        logger.error("Failed to extract thumbnail", file_id=file_id, error=str(e))
        raise FileProcessingError(
            filename=file_id,
            operation="extract_thumbnail",
            reason=str(e)
        )


@router.post("/{file_id}/thumbnail/generate")
async def generate_file_thumbnail(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """
    Generate thumbnail for 3D model files (STL, OBJ).

    This endpoint generates a rendered preview thumbnail for 3D model files
    that don't have embedded thumbnails. Uses 3D rendering to create a preview.

    Supported formats:
    - STL files (3D mesh rendering)
    - OBJ files (3D mesh rendering)
    """
    file_data = await file_service.get_file_by_id(file_id)

    if not file_data:
        raise PrinternizerFileNotFoundError(file_id)

    file_path = file_data.get('file_path')
    if not file_path:
        raise PrinternizerValidationError(
            field="file_path",
            error="File not available locally for thumbnail generation"
        )

    # Get the thumbnail service from file service
    thumbnail_service = file_service.thumbnail_service
    if not thumbnail_service:
        raise FileProcessingError(
            filename=file_id,
            operation="generate_thumbnail",
            reason="Thumbnail service not available"
        )

    # Generate preview thumbnail
    try:
        from pathlib import Path
        file_path_obj = Path(file_path)

        # Check file type
        file_ext = file_path_obj.suffix.lower()
        if file_ext not in ['.stl', '.obj']:
            raise PrinternizerValidationError(
                field="file_type",
                error=f"Thumbnail generation not supported for {file_ext} files. Supported: .stl, .obj"
            )

        # Use preview render service to generate thumbnail
        thumbnail_result = await thumbnail_service._generate_preview_thumbnail(file_path)

        if thumbnail_result:
            update_data = {
                'has_thumbnail': True,
                'thumbnail_data': thumbnail_result['data'],
                'thumbnail_width': thumbnail_result['width'],
                'thumbnail_height': thumbnail_result['height'],
                'thumbnail_format': thumbnail_result['format'],
                'thumbnail_source': 'generated'
            }

            await file_service.database.update_file(file_id, update_data)

            return success_response({
                "success": True,
                "method": "generated",
                "thumbnail_url": f"/api/v1/files/{file_id}/thumbnail",
                "dimensions": {
                    "width": thumbnail_result['width'],
                    "height": thumbnail_result['height']
                },
                "message": "Successfully generated thumbnail from 3D model"
            })
        else:
            raise FileProcessingError(
                filename=file_id,
                operation="generate_thumbnail",
                reason="Preview rendering returned no thumbnail"
            )

    except PrinternizerValidationError:
        raise
    except Exception as e:
        logger.error("Failed to generate thumbnail", file_id=file_id, error=str(e))
        raise FileProcessingError(
            filename=file_id,
            operation="generate_thumbnail",
            reason=str(e)
        )


@router.post("/{file_id}/analyze/gcode")
async def analyze_gcode_file(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """
    Analyze G-code file to extract metadata and print settings.

    This endpoint parses G-code files to extract comprehensive metadata including:
    - Print settings (layer height, infill, speeds)
    - Material requirements (filament type, weight, length)
    - Time estimates
    - Machine settings
    - Slicer information

    Supported formats:
    - G-code files (.gcode, .gco)
    - BGCode files (Prusa binary G-code)
    """
    file_data = await file_service.get_file_by_id(file_id)

    if not file_data:
        raise PrinternizerFileNotFoundError(file_id)

    file_path = file_data.get('file_path')
    if not file_path:
        raise PrinternizerValidationError(
            field="file_path",
            error="File not available locally for G-code analysis"
        )

    # Get the thumbnail service from file service
    thumbnail_service = file_service.thumbnail_service
    if not thumbnail_service:
        raise FileProcessingError(
            filename=file_id,
            operation="analyze_gcode",
            reason="Thumbnail service not available"
        )

    # Parse G-code for metadata
    try:
        from src.services.bambu_parser import BambuParser
        from pathlib import Path

        parser = BambuParser()
        file_path_obj = Path(file_path)

        # Check file type
        file_ext = file_path_obj.suffix.lower()
        if file_ext not in ['.gcode', '.gco', '.bgcode']:
            raise PrinternizerValidationError(
                field="file_type",
                error=f"G-code analysis not supported for {file_ext} files. Supported: .gcode, .gco, .bgcode"
            )

        parse_result = await parser.parse_file(file_path)

        if not parse_result['success']:
            raise FileProcessingError(
                filename=file_id,
                operation="analyze_gcode",
                reason=parse_result.get('error', 'Failed to parse G-code file')
            )

        metadata = parse_result['metadata']
        thumbnails = parse_result['thumbnails']

        # Update file record with metadata
        update_data = {'metadata': metadata}

        # If thumbnails were found during analysis, store them too
        if thumbnails:
            best_thumbnail = parser.get_thumbnail_by_size(thumbnails, (200, 200))
            if best_thumbnail:
                update_data.update({
                    'has_thumbnail': True,
                    'thumbnail_data': best_thumbnail['data'],
                    'thumbnail_width': best_thumbnail['width'],
                    'thumbnail_height': best_thumbnail['height'],
                    'thumbnail_format': best_thumbnail.get('format', 'png'),
                    'thumbnail_source': 'embedded'
                })

        await file_service.database.update_file(file_id, update_data)

        response_data = {
            "success": True,
            "method": "analyzed",
            "metadata": metadata,
            "metadata_keys": list(metadata.keys()),
            "metadata_count": len(metadata),
            "message": f"Successfully analyzed G-code file and extracted {len(metadata)} metadata fields"
        }

        # Add thumbnail info if found
        if thumbnails:
            response_data["thumbnails_found"] = len(thumbnails)
            response_data["thumbnail_url"] = f"/api/v1/files/{file_id}/thumbnail"

        return success_response(response_data)

    except PrinternizerValidationError:
        raise
    except Exception as e:
        logger.error("Failed to analyze G-code", file_id=file_id, error=str(e))
        raise FileProcessingError(
            filename=file_id,
            operation="analyze_gcode",
            reason=str(e)
        )


# Watch Folder Management Endpoints

@router.get("/watch-folders/settings", response_model=WatchFolderSettings)
async def get_watch_folder_settings(
    config_service: ConfigService = Depends(get_config_service)
):
    """Get watch folder settings."""
    settings = await config_service.get_watch_folder_settings()
    # Also get inactive folders to show all folders with activation status
    all_folders = await config_service.watch_folder_db.get_all_watch_folders(active_only=False)
    settings['watch_folders'] = [wf.to_dict() for wf in all_folders]
    return WatchFolderSettings(**settings)


@router.get("/watch-folders/status")
async def get_watch_folder_status(
    file_service: FileService = Depends(get_file_service),
    config_service: ConfigService = Depends(get_config_service)
):
    """Get watch folder status."""
    status_info = await file_service.get_watch_status()
    return status_info


@router.get("/local")
async def list_local_files(
    watch_folder_path: Optional[str] = Query(None, description="Filter by watch folder path"),
    file_service: FileService = Depends(get_file_service)
):
    """List local files from watch folders."""
    files = await file_service.get_local_files()

    # Filter by watch folder path if specified
    if watch_folder_path:
        files = [f for f in files if f.get('watch_folder_path') == watch_folder_path]

    return {"files": files}


@router.post("/watch-folders/reload")
async def reload_watch_folders(
    file_service: FileService = Depends(get_file_service)
):
    """Reload watch folders configuration."""
    result = await file_service.reload_watch_folders()
    return result


@router.post("/watch-folders/validate")
async def validate_watch_folder(
    folder_path: str = Query(..., description="Folder path to validate"),
    config_service: ConfigService = Depends(get_config_service)
):
    """Validate a watch folder path."""
    validation = config_service.validate_watch_folder(folder_path)
    return validation


@router.post("/watch-folders/add")
async def add_watch_folder(
    folder_path: str = Query(..., description="Folder path to add"),
    config_service: ConfigService = Depends(get_config_service),
    file_service: FileService = Depends(get_file_service)
):
    """Add a new watch folder."""
    # First validate the folder
    validation = config_service.validate_watch_folder(folder_path)
    if not validation["valid"]:
        raise PrinternizerValidationError(
            field="folder_path",
            error=validation["error"]
        )

    # Add folder to configuration
    success = await config_service.add_watch_folder(folder_path)
    if not success:
        raise PrinternizerValidationError(
            field="folder_path",
            error="Watch folder already exists or could not be added"
        )

    # Reload watch folders in file service
    await file_service.reload_watch_folders()

    return success_response({"status": "added", "folder_path": folder_path})


@router.delete("/watch-folders/remove")
async def remove_watch_folder(
    folder_path: str = Query(..., description="Folder path to remove"),
    config_service: ConfigService = Depends(get_config_service),
    file_service: FileService = Depends(get_file_service)
):
    """Remove a watch folder."""
    # Remove folder from configuration
    success = await config_service.remove_watch_folder(folder_path)
    if not success:
        raise PrinternizerValidationError(
            field="folder_path",
            error="Watch folder not found"
        )

    # Reload watch folders in file service
    await file_service.reload_watch_folders()

    return success_response({"status": "removed", "folder_path": folder_path})


@router.patch("/watch-folders/update")
async def update_watch_folder(
    folder_path: str = Query(..., description="Folder path to update"),
    is_active: bool = Query(..., description="Whether to activate or deactivate the folder"),
    config_service: ConfigService = Depends(get_config_service),
    file_service: FileService = Depends(get_file_service)
):
    """Update watch folder activation status."""
    # First get the watch folder by path to get its ID
    await config_service._ensure_env_migration()
    folder = await config_service.watch_folder_db.get_watch_folder_by_path(folder_path)

    if not folder:
        raise PrinternizerValidationError(
            field="folder_path",
            error="Watch folder not found"
        )

    # Update the folder's active status
    success = await config_service.watch_folder_db.update_watch_folder(
        folder.id,
        {"is_active": is_active}
    )

    if not success:
        raise FileProcessingError(
            filename=folder_path,
            operation="update_watch_folder",
            reason="Failed to update watch folder"
        )

    # Reload watch folders in file service to apply changes
    await file_service.reload_watch_folders()

    status_text = "activated" if is_active else "deactivated"
    return success_response({
        "status": "updated",
        "folder_path": folder_path,
        "is_active": is_active,
        "message": f"Watch folder {status_text} successfully"
    })


@router.delete("/cleanup")
async def cleanup_files(
    dry_run: bool = Query(True, description="If True, only report what would be deleted without actually deleting"),
    deleted_days: int = Query(30, description="Remove files marked deleted older than this many days"),
    failed_days: int = Query(7, description="Remove files marked failed older than this many days"),
    file_service: FileService = Depends(get_file_service)
):
    """
    Clean up old file records from the database.

    This endpoint removes file records that are:
    - Marked as 'deleted' and older than deleted_days (default: 30 days)
    - Marked as 'failed' and older than failed_days (default: 7 days)

    This is a conservative cleanup that only removes database records,
    not physical files. Physical file deletion should be handled separately.

    By default, this endpoint runs in dry_run mode (dry_run=True), which only
    reports what would be deleted without actually deleting anything.
    Set dry_run=False to perform the actual cleanup.

    Returns:
        Dictionary with cleanup statistics:
        - old_deleted_removed: Count of deleted file records removed
        - failed_downloads_removed: Count of failed file records removed
        - dry_run: Whether this was a dry run
    """
    logger.info(
        "File cleanup requested",
        dry_run=dry_run,
        deleted_days=deleted_days,
        failed_days=failed_days
    )

    result = await file_service.cleanup_files(
        dry_run=dry_run,
        deleted_days=deleted_days,
        failed_days=failed_days
    )

    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File cleanup failed: {result['error']}"
        )

    action = "would remove" if dry_run else "removed"
    total = result["old_deleted_removed"] + result["failed_downloads_removed"]

    return success_response({
        "status": "completed",
        "message": f"Cleanup {action} {total} file records",
        "statistics": result
    })


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """Delete a file (for local files, also deletes physical file)."""
    success = await file_service.delete_file(file_id)

    if not success:
        raise PrinternizerFileNotFoundError(
            file_id=file_id,
            details={"reason": "File not found or could not be deleted"}
        )

    return success_response({"status": "deleted", "file_id": file_id})


# Enhanced Metadata Endpoints (Issue #43 - METADATA-001)

@router.get("/{file_id}/metadata/enhanced")
async def get_enhanced_metadata(
    file_id: str,
    force_refresh: bool = Query(False, description="Force re-analysis of file"),
    file_service: FileService = Depends(get_file_service)
):
    """
    Get comprehensive enhanced metadata for a file.
    
    This endpoint provides detailed information including:
    - Physical properties (dimensions, volume, objects)
    - Print settings (layer height, nozzle, infill)
    - Material requirements (filament weight, colors)
    - Cost analysis (material and energy costs)
    - Quality metrics (complexity score, difficulty level)
    - Compatibility information (printers, slicer info)
    """
    try:
        from src.models.file import EnhancedFileMetadata
        
        logger.info("Getting enhanced metadata", file_id=file_id, force_refresh=force_refresh)
        
        # Get file record
        file_record = await file_service.get_file(file_id)
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_id}"
            )
        
        # Check if we need to analyze the file
        needs_analysis = force_refresh or file_record.last_analyzed is None
        
        if needs_analysis and file_record.file_path:
            # Extract enhanced metadata
            metadata = await file_service.extract_enhanced_metadata(file_id)
            if not metadata:
                logger.warning("Could not extract enhanced metadata", file_id=file_id)
                # Return empty metadata structure
                return EnhancedFileMetadata()
        
        # Return enhanced metadata from file record
        if file_record.enhanced_metadata:
            return file_record.enhanced_metadata
        else:
            # Return empty metadata structure if not yet analyzed
            return EnhancedFileMetadata()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get enhanced metadata", file_id=file_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get enhanced metadata: {str(e)}"
        )


@router.get("/{file_id}/analysis")
async def analyze_file(
    file_id: str,
    include_recommendations: bool = Query(True, description="Include optimization recommendations"),
    file_service: FileService = Depends(get_file_service)
):
    """
    Get detailed file analysis with optimization recommendations.
    
    Provides actionable insights about:
    - Printability score and success probability
    - Risk factors and potential issues
    - Optimization suggestions for speed, quality, or cost
    - Printer compatibility recommendations
    """
    try:
        logger.info("Analyzing file", file_id=file_id, include_recommendations=include_recommendations)
        
        # Get enhanced metadata first
        metadata = await get_enhanced_metadata(file_id, force_refresh=False, file_service=file_service)
        
        # Calculate analysis
        analysis = {
            'file_id': file_id,
            'printability_score': 0,
            'optimization_suggestions': [],
            'risk_factors': [],
            'estimated_success_rate': None
        }
        
        # Extract quality metrics
        if metadata.quality_metrics:
            analysis['printability_score'] = metadata.quality_metrics.complexity_score or 5
            analysis['estimated_success_rate'] = metadata.quality_metrics.success_probability
        
        # Generate recommendations if requested
        if include_recommendations:
            suggestions = []
            risks = []
            
            # Check for speed optimization opportunities
            if metadata.print_settings:
                if metadata.print_settings.infill_density and metadata.print_settings.infill_density > 50:
                    suggestions.append({
                        'category': 'speed',
                        'message': 'Consider reducing infill density to 20-30% for faster printing',
                        'potential_savings': '20-40% time reduction'
                    })
                
                if metadata.print_settings.layer_height and metadata.print_settings.layer_height < 0.15:
                    suggestions.append({
                        'category': 'speed',
                        'message': 'Increase layer height to 0.2mm for faster printing',
                        'potential_savings': '30-50% time reduction'
                    })
            
            # Check for cost optimization
            if metadata.cost_breakdown and metadata.cost_breakdown.total_cost:
                if metadata.cost_breakdown.total_cost > 5.0:
                    suggestions.append({
                        'category': 'cost',
                        'message': 'High material usage detected. Consider optimizing infill and wall count',
                        'potential_savings': f'Could save €{metadata.cost_breakdown.total_cost * 0.2:.2f}'
                    })
            
            # Identify risk factors
            if metadata.print_settings and metadata.print_settings.support_used:
                risks.append({
                    'severity': 'medium',
                    'factor': 'Supports required',
                    'mitigation': 'Ensure proper support settings and allow extra time for cleanup'
                })
            
            if metadata.quality_metrics and metadata.quality_metrics.complexity_score:
                if metadata.quality_metrics.complexity_score >= 8:
                    risks.append({
                        'severity': 'high',
                        'factor': 'High complexity print',
                        'mitigation': 'Monitor first layers closely and ensure proper bed adhesion'
                    })
            
            if metadata.material_requirements and metadata.material_requirements.multi_material:
                risks.append({
                    'severity': 'medium',
                    'factor': 'Multi-material print',
                    'mitigation': 'Verify filament compatibility and purge tower settings'
                })
            
            analysis['optimization_suggestions'] = suggestions
            analysis['risk_factors'] = risks
        
        return analysis
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to analyze file", file_id=file_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze file: {str(e)}"
        )


@router.get("/{file_id}/compatibility/{printer_id}")
async def check_printer_compatibility(
    file_id: str,
    printer_id: str,
    file_service: FileService = Depends(get_file_service),
    printer_service: PrinterService = Depends(get_printer_service)
):
    """
    Check if file is compatible with specific printer.

    Analyzes:
    - Print bed size requirements
    - Material compatibility
    - Required printer features
    - Slicer profile compatibility
    """
    try:
        logger.info("Checking compatibility", file_id=file_id, printer_id=printer_id)

        # Get enhanced metadata
        metadata = await get_enhanced_metadata(file_id, force_refresh=False, file_service=file_service)

        # Get actual printer capabilities from printer service
        printer = await printer_service.get_printer(printer_id)
        if not printer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Printer {printer_id} not found"
            )

        # Get capabilities based on printer type
        capabilities = get_printer_capabilities(printer.type)

        compatibility = {
            'file_id': file_id,
            'printer_id': printer_id,
            'printer_name': printer.name,
            'printer_type': printer.type.value,
            'compatible': True,  # Default to compatible
            'issues': [],
            'warnings': [],
            'recommendations': [],
            'printer_capabilities': {
                'bed_size_x': capabilities['bed_size_x'],
                'bed_size_y': capabilities['bed_size_y'],
                'bed_size_z': capabilities['bed_size_z']
            }
        }

        # Check physical dimensions against actual printer capabilities
        if metadata.physical_properties:
            if metadata.physical_properties.width and metadata.physical_properties.width > capabilities['bed_size_x']:
                compatibility['compatible'] = False
                compatibility['issues'].append({
                    'type': 'size',
                    'message': f'Model width ({metadata.physical_properties.width}mm) exceeds printer bed size ({capabilities["bed_size_x"]}mm)'
                })

            if metadata.physical_properties.depth and metadata.physical_properties.depth > capabilities['bed_size_y']:
                compatibility['compatible'] = False
                compatibility['issues'].append({
                    'type': 'size',
                    'message': f'Model depth ({metadata.physical_properties.depth}mm) exceeds printer bed size ({capabilities["bed_size_y"]}mm)'
                })

            if metadata.physical_properties.height and metadata.physical_properties.height > capabilities['bed_size_z']:
                compatibility['compatible'] = False
                compatibility['issues'].append({
                    'type': 'size',
                    'message': f'Model height ({metadata.physical_properties.height}mm) exceeds printer build height ({capabilities["bed_size_z"]}mm)'
                })
        
        # Check if printer is in compatible printers list
        if metadata.compatibility_info and metadata.compatibility_info.compatible_printers:
            printers_list = [p.lower() for p in metadata.compatibility_info.compatible_printers]
            # Simple name matching - could be improved
            if not any(printer_id.lower() in p or 'bambu' in p or 'prusa' in p for p in printers_list):
                compatibility['warnings'].append({
                    'type': 'profile',
                    'message': 'File was sliced for different printer model'
                })
        
        return compatibility
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to check compatibility", file_id=file_id, printer_id=printer_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check compatibility: {str(e)}"
        )