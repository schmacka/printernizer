"""
Library API Router - Unified file management endpoints.
Provides REST API for library operations (list, get, reprocess, delete).
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path as PathParam, Depends
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()

# Create router
router = APIRouter(prefix="/library", tags=["library"])


# Pydantic models for request/response validation
class LibraryFileResponse(BaseModel):
    """Library file response model."""
    id: str
    checksum: str
    filename: str
    display_name: Optional[str]
    library_path: str
    file_size: int
    file_type: str
    status: str
    added_to_library: str
    last_modified: Optional[str]
    last_accessed: Optional[str]
    has_thumbnail: bool = False

    # Enhanced metadata (optional)
    model_width: Optional[float] = None
    model_depth: Optional[float] = None
    model_height: Optional[float] = None
    total_filament_weight: Optional[float] = None
    material_cost: Optional[float] = None

    # Source information
    sources: Optional[str] = None  # JSON string

    class Config:
        from_attributes = True


class LibraryFileListResponse(BaseModel):
    """Library file list response with pagination."""
    files: list[LibraryFileResponse]
    pagination: Dict[str, Any]


class LibraryStatsResponse(BaseModel):
    """Library statistics response."""
    total_files: int = 0
    total_size: int = 0
    files_with_thumbnails: int = 0
    files_analyzed: int = 0
    available_files: int = 0
    processing_files: int = 0
    error_files: int = 0
    unique_file_types: int = 0
    avg_file_size: float = 0
    total_material_cost: float = 0


class ReprocessResponse(BaseModel):
    """Reprocess operation response."""
    success: bool
    checksum: str
    message: str


class DeleteResponse(BaseModel):
    """Delete operation response."""
    success: bool
    checksum: str
    message: str


# Dependency to get library service
async def get_library_service():
    """Get library service from application state."""
    from src.main import app
    if not hasattr(app.state, 'library_service'):
        raise HTTPException(status_code=503, detail="Library service not available")
    return app.state.library_service


@router.get("/files", response_model=LibraryFileListResponse)
async def list_library_files(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    source_type: Optional[str] = Query(None, description="Filter by source type (printer, watch_folder, upload)"),
    file_type: Optional[str] = Query(None, description="Filter by file extension (.3mf, .stl, .gcode)"),
    status: Optional[str] = Query(None, description="Filter by status (available, processing, ready, error)"),
    search: Optional[str] = Query(None, min_length=2, description="Search in filename"),
    has_thumbnail: Optional[bool] = Query(None, description="Filter by thumbnail presence"),
    has_metadata: Optional[bool] = Query(None, description="Filter by metadata analysis"),
    manufacturer: Optional[str] = Query(None, description="Filter by manufacturer (bambu_lab, prusa_research)"),
    printer_model: Optional[str] = Query(None, description="Filter by printer model (A1, Core One, etc.)"),
    show_duplicates: Optional[bool] = Query(True, description="Show duplicate files (default: true)"),
    only_duplicates: Optional[bool] = Query(False, description="Show only duplicate files (default: false)"),
    library_service = Depends(get_library_service)
):
    """
    List library files with filters and pagination.

    **Filters:**
    - `source_type`: Filter by where file came from (printer/watch_folder/upload)
    - `file_type`: Filter by file extension (.3mf, .stl, etc.)
    - `status`: Filter by processing status
    - `search`: Search in filename (case-insensitive)
    - `has_thumbnail`: Only files with/without thumbnails
    - `has_metadata`: Only files with/without extracted metadata
    - `manufacturer`: Filter by printer manufacturer (bambu_lab, prusa_research)
    - `printer_model`: Filter by printer model (A1, P1P, Core One, MK4, etc.)

    **Pagination:**
    - `page`: Page number (starts at 1)
    - `limit`: Items per page (default 50, max 200)

    **Sorting:**
    - Files are sorted by date added (newest first)

    **Returns:**
    - `files`: Array of file objects
    - `pagination`: Pagination metadata (page, limit, total_items, total_pages)
    """
    try:
        # Build filters
        filters = {}
        if source_type:
            filters['source_type'] = source_type
        if file_type:
            filters['file_type'] = file_type
        if status:
            filters['status'] = status
        if search:
            filters['search'] = search
        if has_thumbnail is not None:
            filters['has_thumbnail'] = has_thumbnail
        if has_metadata is not None:
            filters['has_metadata'] = has_metadata
        if manufacturer:
            filters['manufacturer'] = manufacturer
        if printer_model:
            filters['printer_model'] = printer_model
        if show_duplicates is not None:
            filters['show_duplicates'] = show_duplicates
        if only_duplicates is not None:
            filters['only_duplicates'] = only_duplicates

        # Get files from library service
        files, pagination = await library_service.list_files(filters, page, limit)

        return {
            'files': files,
            'pagination': pagination
        }

    except Exception as e:
        logger.error("Failed to list library files", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.get("/files/{checksum}", response_model=LibraryFileResponse)
async def get_library_file(
    checksum: str = PathParam(..., description="File checksum (SHA-256)"),
    library_service = Depends(get_library_service)
):
    """
    Get library file details by checksum.

    **Parameters:**
    - `checksum`: File SHA-256 checksum (hexadecimal)

    **Returns:**
    - Complete file record with all metadata
    - Sources (where file was discovered)
    - Enhanced metadata (dimensions, materials, costs)

    **Error Responses:**
    - `404`: File not found in library
    - `500`: Internal server error
    """
    try:
        file_record = await library_service.get_file_by_checksum(checksum)

        if not file_record:
            raise HTTPException(
                status_code=404,
                detail=f"File with checksum '{checksum[:16]}...' not found in library"
            )

        return file_record

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get library file", checksum=checksum[:16], error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get file: {str(e)}")


@router.post("/files/{checksum}/reprocess", response_model=ReprocessResponse)
async def reprocess_library_file(
    checksum: str = PathParam(..., description="File checksum (SHA-256)"),
    library_service = Depends(get_library_service)
):
    """
    Reprocess file metadata extraction.

    Triggers metadata re-extraction for a file. Useful when:
    - Metadata extraction failed previously
    - New metadata extractors are available
    - File was updated but metadata is stale

    **Parameters:**
    - `checksum`: File SHA-256 checksum

    **Process:**
    1. File status set to 'processing'
    2. Metadata extraction scheduled asynchronously
    3. Thumbnails regenerated
    4. Status updated to 'ready' or 'error'

    **Returns:**
    - `success`: Whether reprocessing was scheduled
    - `checksum`: File checksum
    - `message`: Status message

    **Error Responses:**
    - `404`: File not found
    - `500`: Failed to schedule reprocessing
    """
    try:
        # Check file exists
        file_record = await library_service.get_file_by_checksum(checksum)
        if not file_record:
            raise HTTPException(
                status_code=404,
                detail=f"File with checksum '{checksum[:16]}...' not found"
            )

        # Schedule reprocessing
        success = await library_service.reprocess_file(checksum)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to schedule file reprocessing"
            )

        return {
            'success': True,
            'checksum': checksum,
            'message': 'Metadata extraction scheduled'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to reprocess file", checksum=checksum[:16], error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to reprocess: {str(e)}")


@router.delete("/files/{checksum}", response_model=DeleteResponse)
async def delete_library_file(
    checksum: str = PathParam(..., description="File checksum (SHA-256)"),
    delete_physical: bool = Query(True, description="Also delete physical file from disk"),
    library_service = Depends(get_library_service)
):
    """
    Delete file from library.

    **Parameters:**
    - `checksum`: File SHA-256 checksum
    - `delete_physical`: Whether to delete physical file (default: true)

    **Warning:** This operation cannot be undone!

    **Process:**
    1. Remove file record from database
    2. Remove all source associations
    3. Optionally delete physical file from library folder
    4. Delete thumbnails and previews

    **Returns:**
    - `success`: Whether deletion succeeded
    - `checksum`: File checksum
    - `message`: Status message

    **Error Responses:**
    - `404`: File not found
    - `500`: Deletion failed
    """
    try:
        # Check file exists
        file_record = await library_service.get_file_by_checksum(checksum)
        if not file_record:
            raise HTTPException(
                status_code=404,
                detail=f"File with checksum '{checksum[:16]}...' not found"
            )

        # Delete file
        success = await library_service.delete_file(checksum, delete_physical=delete_physical)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete file from library"
            )

        return {
            'success': True,
            'checksum': checksum,
            'message': 'File deleted successfully' if delete_physical else 'File record deleted (physical file preserved)'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete file", checksum=checksum[:16], error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")


@router.get("/statistics", response_model=LibraryStatsResponse)
async def get_library_statistics(
    library_service = Depends(get_library_service)
):
    """
    Get library statistics.

    **Returns:**
    - `total_files`: Total number of files in library
    - `total_size`: Total size of all files (bytes)
    - `files_with_thumbnails`: Files with generated thumbnails
    - `files_analyzed`: Files with extracted metadata
    - `available_files`: Files ready for use
    - `processing_files`: Files being processed
    - `error_files`: Files with errors
    - `unique_file_types`: Number of different file types
    - `avg_file_size`: Average file size (bytes)
    - `total_material_cost`: Sum of all material costs (EUR)

    **Use Cases:**
    - Dashboard widgets
    - Storage management
    - Library health monitoring
    """
    try:
        stats = await library_service.get_library_statistics()

        # Convert to response model (handle missing fields)
        return LibraryStatsResponse(
            total_files=stats.get('total_files', 0),
            total_size=stats.get('total_size', 0),
            files_with_thumbnails=stats.get('files_with_thumbnails', 0),
            files_analyzed=stats.get('files_analyzed', 0),
            available_files=stats.get('available_files', 0),
            processing_files=stats.get('processing_files', 0),
            error_files=stats.get('error_files', 0),
            unique_file_types=stats.get('unique_file_types', 0),
            avg_file_size=stats.get('avg_file_size', 0),
            total_material_cost=stats.get('total_material_cost', 0)
        )

    except Exception as e:
        logger.error("Failed to get library statistics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/health")
async def library_health_check(library_service = Depends(get_library_service)):
    """
    Library service health check.

    **Returns:**
    - `status`: Service status (healthy/degraded/unhealthy)
    - `enabled`: Whether library is enabled
    - `library_path`: Configured library path
    - `message`: Status message

    **Status Codes:**
    - `healthy`: Library operational
    - `degraded`: Library has issues but functional
    - `unhealthy`: Library not operational
    """
    try:
        # Check if library is enabled
        if not library_service.enabled:
            return {
                'status': 'disabled',
                'enabled': False,
                'library_path': str(library_service.library_path),
                'message': 'Library system is disabled in configuration'
            }

        # Check if library path exists and is writable
        if not library_service.library_path.exists():
            return {
                'status': 'unhealthy',
                'enabled': True,
                'library_path': str(library_service.library_path),
                'message': 'Library path does not exist'
            }

        # Try to get stats (validates database access)
        stats = await library_service.get_library_statistics()

        return {
            'status': 'healthy',
            'enabled': True,
            'library_path': str(library_service.library_path),
            'total_files': stats.get('total_files', 0),
            'message': 'Library operational'
        }

    except Exception as e:
        logger.error("Library health check failed", error=str(e))
        return {
            'status': 'degraded',
            'enabled': library_service.enabled if library_service else False,
            'library_path': str(library_service.library_path) if library_service else None,
            'message': f'Health check failed: {str(e)}'
        }
