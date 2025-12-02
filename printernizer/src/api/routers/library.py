"""
Library API Router - Unified file management endpoints.
Provides REST API for library operations (list, get, reprocess, delete).
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path as PathParam, Depends
from pydantic import BaseModel, Field
import structlog
import asyncio

from src.utils.errors import (
    LibraryItemNotFoundError,
    ServiceUnavailableError,
    FileProcessingError,
    ValidationError as PrinternizerValidationError,
    success_response
)
from src.services.file_thumbnail_service import FileThumbnailService
from src.utils.dependencies import get_thumbnail_service

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
    last_accessed: Optional[str] = None
    last_analyzed: Optional[str] = None
    has_thumbnail: bool = False

    # Enhanced metadata (optional)
    model_width: Optional[float] = None
    model_depth: Optional[float] = None
    model_height: Optional[float] = None
    model_volume: Optional[float] = None
    surface_area: Optional[float] = None
    object_count: Optional[int] = None
    layer_height: Optional[float] = None
    first_layer_height: Optional[float] = None
    nozzle_diameter: Optional[float] = None
    wall_count: Optional[int] = None
    wall_thickness: Optional[float] = None
    infill_density: Optional[float] = None
    infill_pattern: Optional[str] = None
    support_used: Optional[bool] = None
    nozzle_temperature: Optional[int] = None
    bed_temperature: Optional[int] = None
    print_speed: Optional[float] = None
    total_layer_count: Optional[int] = None
    total_filament_weight: Optional[float] = None
    filament_length: Optional[float] = None
    filament_colors: Optional[str] = None
    material_types: Optional[str] = None
    material_cost: Optional[float] = None
    energy_cost: Optional[float] = None
    total_cost: Optional[float] = None
    complexity_score: Optional[int] = None
    difficulty_level: Optional[str] = None
    success_probability: Optional[float] = None
    overhang_percentage: Optional[float] = None
    compatible_printers: Optional[str] = None
    slicer_name: Optional[str] = None
    slicer_version: Optional[str] = None
    profile_name: Optional[str] = None
    bed_type: Optional[str] = None

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


class LibraryMetadataResponse(BaseModel):
    """Enhanced metadata response for library files."""
    # Physical properties
    physical_properties: Optional[Dict[str, Any]] = None
    # Print settings
    print_settings: Optional[Dict[str, Any]] = None
    # Material requirements
    material_requirements: Optional[Dict[str, Any]] = None
    # Cost analysis
    cost_analysis: Optional[Dict[str, Any]] = None
    # Quality metrics
    quality_metrics: Optional[Dict[str, Any]] = None
    # Compatibility
    compatibility: Optional[Dict[str, Any]] = None
    # Thumbnail information
    thumbnail: Optional[Dict[str, Any]] = None
    # Metadata status
    has_metadata: bool = False
    last_analyzed: Optional[str] = None


# Dependency to get library service
async def get_library_service():
    """Get library service from application state."""
    from src.main import app
    if not hasattr(app.state, 'library_service'):
        raise ServiceUnavailableError("Library service not available")
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
    sort_by: Optional[str] = Query('created_at', description="Sort by field (created_at, filename, file_size, last_modified)"),
    sort_order: Optional[str] = Query('desc', description="Sort order (asc, desc)"),
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
    - `sort_by`: Sort by field (created_at, filename, file_size, last_modified) - default: created_at
    - `sort_order`: Sort order (asc, desc) - default: desc

    **Returns:**
    - `files`: Array of file objects
    - `pagination`: Pagination metadata (page, limit, total_items, total_pages)
    """
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
    if sort_by:
        filters['sort_by'] = sort_by
    if sort_order:
        filters['sort_order'] = sort_order

    # Get files from library service
    files, pagination = await library_service.list_files(filters, page, limit)

    return {
        'files': files,
        'pagination': pagination
    }


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
    file_record = await library_service.get_file_by_checksum(checksum)

    if not file_record:
        raise LibraryItemNotFoundError(checksum)

    return file_record


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
    # Check file exists
    file_record = await library_service.get_file_by_checksum(checksum)
    if not file_record:
        raise LibraryItemNotFoundError(checksum)

    # Schedule reprocessing
    success = await library_service.reprocess_file(checksum)

    if not success:
        raise FileProcessingError(
            filename=checksum,
            operation="reprocess",
            reason="Failed to schedule file reprocessing"
        )

    return success_response({
        'success': True,
        'checksum': checksum,
        'message': 'Metadata extraction scheduled'
    })


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
    # Check file exists
    file_record = await library_service.get_file_by_checksum(checksum)
    if not file_record:
        raise LibraryItemNotFoundError(checksum)

    # Delete file
    success = await library_service.delete_file(checksum, delete_physical=delete_physical)

    if not success:
        raise FileProcessingError(
            filename=checksum,
            operation="delete",
            reason="Failed to delete file from library"
        )

    return success_response({
        'success': True,
        'checksum': checksum,
        'message': 'File deleted successfully' if delete_physical else 'File record deleted (physical file preserved)'
    })


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


@router.get("/files/{checksum}/metadata", response_model=LibraryMetadataResponse)
async def get_library_file_metadata(
    checksum: str = PathParam(..., description="File checksum (SHA-256)"),
    force_refresh: bool = Query(False, description="Force re-extraction of metadata"),
    library_service = Depends(get_library_service)
):
    """
    Get comprehensive metadata for a library file.

    This endpoint provides detailed information extracted from the file including:
    - **Physical properties**: Dimensions, volume, object count
    - **Print settings**: Layer height, nozzle settings, infill, supports
    - **Material requirements**: Filament weight, length, types, colors
    - **Cost analysis**: Material and energy costs
    - **Quality metrics**: Complexity score, difficulty level, success probability
    - **Compatibility**: Compatible printers, slicer information
    - **Thumbnail**: Embedded thumbnail image data

    **Parameters:**
    - `checksum`: File checksum (SHA-256 hash)
    - `force_refresh`: Force re-extraction of metadata (default: false)

    **Returns:**
    - Structured metadata organized by category
    - Empty categories if metadata not available for that aspect

    **File Type Support:**
    - **3MF files**: Full metadata extraction
    - **G-code files**: Full metadata extraction
    - **STL files**: Limited or no metadata
    - **Other formats**: No metadata extraction

    **Status Codes:**
    - `200`: Metadata retrieved successfully
    - `404`: File not found
    - `500`: Error retrieving metadata
    """
    logger.info("Getting library file metadata", checksum=checksum[:16], force_refresh=force_refresh)

    # Get file record
    file_record = await library_service.get_file_by_checksum(checksum)
    if not file_record:
        raise LibraryItemNotFoundError(checksum)

    # Force re-extraction if requested
    if force_refresh:
        logger.info("Forcing metadata re-extraction", checksum=checksum[:16])
        await library_service.reprocess_file(checksum)
        # Wait a moment for processing to start
        import asyncio
        await asyncio.sleep(0.5)
        # Get updated record
        file_record = await library_service.get_file_by_checksum(checksum)

    # Build structured metadata response
    response = {
        'has_metadata': file_record.get('last_analyzed') is not None,
        'last_analyzed': file_record.get('last_analyzed')
    }

    # Physical properties
    physical_props = {}
    if file_record.get('model_width'):
        physical_props['width_mm'] = file_record['model_width']
    if file_record.get('model_depth'):
        physical_props['depth_mm'] = file_record['model_depth']
    if file_record.get('model_height'):
        physical_props['height_mm'] = file_record['model_height']
    if file_record.get('model_volume'):
        physical_props['volume_cm3'] = file_record['model_volume']
    if file_record.get('surface_area'):
        physical_props['surface_area_cm2'] = file_record['surface_area']
    if file_record.get('object_count'):
        physical_props['object_count'] = file_record['object_count']
    if physical_props:
        response['physical_properties'] = physical_props

    # Print settings
    print_settings = {}
    if file_record.get('layer_height'):
        print_settings['layer_height_mm'] = file_record['layer_height']
    if file_record.get('first_layer_height'):
        print_settings['first_layer_height_mm'] = file_record['first_layer_height']
    if file_record.get('nozzle_diameter'):
        print_settings['nozzle_diameter_mm'] = file_record['nozzle_diameter']
    if file_record.get('wall_count'):
        print_settings['wall_count'] = file_record['wall_count']
    if file_record.get('infill_density'):
        print_settings['infill_density_percent'] = file_record['infill_density']
    if file_record.get('infill_pattern'):
        print_settings['infill_pattern'] = file_record['infill_pattern']
    if file_record.get('support_used') is not None:
        print_settings['supports_used'] = bool(file_record['support_used'])
    if file_record.get('nozzle_temperature'):
        print_settings['nozzle_temperature_c'] = file_record['nozzle_temperature']
    if file_record.get('bed_temperature'):
        print_settings['bed_temperature_c'] = file_record['bed_temperature']
    if file_record.get('print_speed'):
        print_settings['print_speed_mm_s'] = file_record['print_speed']
    if file_record.get('total_layer_count'):
        print_settings['layer_count'] = file_record['total_layer_count']
    if print_settings:
        response['print_settings'] = print_settings

    # Material requirements
    material_reqs = {}
    if file_record.get('total_filament_weight'):
        material_reqs['filament_weight_g'] = file_record['total_filament_weight']
    if file_record.get('filament_length'):
        material_reqs['filament_length_m'] = file_record['filament_length']
    if file_record.get('material_types'):
        import json
        try:
            material_reqs['material_types'] = json.loads(file_record['material_types'])
        except json.JSONDecodeError:
            # Single value, not JSON array
            material_reqs['material_types'] = [file_record['material_types']]
        except (TypeError, AttributeError) as e:
            logger.warning(f"Invalid material_types format: {e}")
            material_reqs['material_types'] = []
    if file_record.get('multi_material'):
        material_reqs['multi_material'] = bool(file_record['multi_material'])
    if material_reqs:
        response['material_requirements'] = material_reqs

    # Cost analysis
    cost_analysis = {}
    if file_record.get('material_cost'):
        cost_analysis['material_cost'] = file_record['material_cost']
    if file_record.get('energy_cost'):
        cost_analysis['energy_cost'] = file_record['energy_cost']
    if file_record.get('total_cost'):
        cost_analysis['total_cost'] = file_record['total_cost']
    if cost_analysis:
        response['cost_analysis'] = cost_analysis

    # Quality metrics
    quality_metrics = {}
    if file_record.get('complexity_score'):
        quality_metrics['complexity_score'] = file_record['complexity_score']
    if file_record.get('difficulty_level'):
        quality_metrics['difficulty_level'] = file_record['difficulty_level']
    if file_record.get('success_probability'):
        quality_metrics['success_probability'] = file_record['success_probability']
    if file_record.get('overhang_percentage'):
        quality_metrics['overhang_percentage'] = file_record['overhang_percentage']
    if quality_metrics:
        response['quality_metrics'] = quality_metrics

    # Compatibility
    compatibility = {}
    if file_record.get('compatible_printers'):
        import json
        try:
            compatibility['compatible_printers'] = json.loads(file_record['compatible_printers'])
        except json.JSONDecodeError:
            # Single value, not JSON array
            compatibility['compatible_printers'] = [file_record['compatible_printers']]
        except (TypeError, AttributeError) as e:
            logger.warning(f"Invalid compatible_printers format: {e}")
            compatibility['compatible_printers'] = []
    if file_record.get('slicer_name'):
        compatibility['slicer_name'] = file_record['slicer_name']
    if file_record.get('slicer_version'):
        compatibility['slicer_version'] = file_record['slicer_version']
    if file_record.get('profile_name'):
        compatibility['profile_name'] = file_record['profile_name']
    if file_record.get('bed_type'):
        compatibility['bed_type'] = file_record['bed_type']
    if compatibility:
        response['compatibility'] = compatibility

    # Thumbnail
    if file_record.get('has_thumbnail'):
        thumbnail = {
            'has_thumbnail': True,
            'width': file_record.get('thumbnail_width'),
            'height': file_record.get('thumbnail_height'),
            'format': file_record.get('thumbnail_format', 'png'),
            'data': file_record.get('thumbnail_data')  # Base64 encoded
        }
        response['thumbnail'] = thumbnail

    logger.info("Metadata retrieved successfully",
               checksum=checksum[:16],
               has_metadata=response['has_metadata'])

    return response


@router.get("/files/{checksum}/thumbnail/animated")
async def get_library_file_animated_thumbnail(
    checksum: str = PathParam(..., description="File checksum (SHA-256)"),
    library_service = Depends(get_library_service),
    thumbnail_service: FileThumbnailService = Depends(get_thumbnail_service)
):
    """
    Get animated GIF thumbnail for a library file (multi-angle preview).

    Returns a rotating animated GIF showing the 3D model from multiple angles.
    Only supported for STL and 3MF files.

    **Parameters:**
    - `checksum`: File checksum (SHA-256 hash)

    **Returns:**
    - GIF image data (binary)
    - Content-Type: image/gif

    **Status Codes:**
    - `200`: Animated thumbnail returned successfully
    - `404`: File not found
    - `400`: File type not supported for animation
    - `500`: Error generating animated thumbnail
    """
    from fastapi.responses import Response

    # Get file record
    file_record = await library_service.get_file_by_checksum(checksum)
    if not file_record:
        raise LibraryItemNotFoundError(checksum)

    # Get file path and type
    file_path = file_record.get('file_path')
    file_type = file_record.get('file_type', '')

    if not file_path:
        raise LibraryItemNotFoundError(checksum, details={"reason": "no_file_path"})

    # Only support animated previews for STL and 3MF files
    if file_type.lower() not in ['stl', '3mf']:
        raise FileProcessingError(
            filename=checksum[:16],
            operation="generate_animated_thumbnail",
            reason=f"Animated thumbnails not supported for {file_type} files"
        )

    try:
        # Get or generate animated preview
        gif_bytes = await thumbnail_service.preview_render_service.get_or_generate_animated_preview(
            file_path,
            file_type,
            size=(200, 200)
        )

        if not gif_bytes:
            raise FileProcessingError(
                filename=checksum[:16],
                operation="generate_animated_thumbnail",
                reason="Failed to generate animated preview"
            )

        # Return GIF response
        return Response(
            content=gif_bytes,
            media_type="image/gif",
            headers={
                "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
                "Content-Disposition": f"inline; filename=thumbnail_animated_{checksum[:16]}.gif"
            }
        )

    except Exception as e:
        logger.error("Failed to get animated thumbnail",
                    checksum=checksum[:16],
                    error=str(e),
                    exc_info=True)
        raise FileProcessingError(
            filename=checksum[:16],
            operation="get_animated_thumbnail",
            reason=str(e)
        )


@router.get("/files/{checksum}/thumbnail")
async def get_library_file_thumbnail(
    checksum: str = PathParam(..., description="File checksum (SHA-256)"),
    library_service = Depends(get_library_service)
):
    """
    Get thumbnail image for a library file.

    Returns the embedded or generated thumbnail as a PNG image.

    **Parameters:**
    - `checksum`: File checksum (SHA-256 hash)

    **Returns:**
    - PNG image data (binary)
    - Content-Type: image/png

    **Status Codes:**
    - `200`: Thumbnail returned successfully
    - `404`: File not found or no thumbnail available
    - `500`: Error retrieving thumbnail
    """
    from fastapi.responses import Response
    import base64

    # Get file record
    file_record = await library_service.get_file_by_checksum(checksum)
    if not file_record:
        raise LibraryItemNotFoundError(checksum)

    # Check if thumbnail exists
    if not file_record.get('has_thumbnail') or not file_record.get('thumbnail_data'):
        raise LibraryItemNotFoundError(checksum, details={"reason": "no_thumbnail"})

    # Decode base64 thumbnail data
    try:
        thumbnail_base64 = file_record['thumbnail_data']
        # Remove data URL prefix if present
        if ',' in thumbnail_base64:
            thumbnail_base64 = thumbnail_base64.split(',', 1)[1]

        thumbnail_bytes = base64.b64decode(thumbnail_base64)

        return Response(
            content=thumbnail_bytes,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=3600",
                "Content-Disposition": f"inline; filename=\"{checksum[:16]}_thumbnail.png\""
            }
        )
    except Exception as e:
        logger.error("Failed to decode thumbnail data",
                    checksum=checksum[:16],
                    error=str(e))
        raise FileProcessingError(
            filename=checksum,
            operation="decode_thumbnail",
            reason="Failed to decode thumbnail data"
        )


@router.post("/reanalyze-all")
async def bulk_reanalyze_library(
    file_type: Optional[str] = Query(None, description="Filter by file type (.3mf, .gcode)"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of files to reanalyze"),
    library_service = Depends(get_library_service)
):
    """
    Bulk re-analyze all library files to extract metadata.

    This endpoint triggers metadata re-extraction for multiple files at once.
    Useful for updating metadata after system upgrades or fixing extraction issues.

    **Parameters:**
    - `file_type`: Only reanalyze specific file types (e.g., ".3mf", ".gcode")
    - `limit`: Maximum number of files to process (default: all files)

    **Process:**
    1. Query library files matching criteria
    2. Schedule metadata extraction for each file
    3. Return count of files scheduled for processing

    **Note:**
    - This operation runs asynchronously in the background
    - Files are processed one at a time to avoid overloading the system
    - Check individual file status to see when extraction completes

    **Returns:**
    - `success`: Whether operation started successfully
    - `files_scheduled`: Number of files scheduled for re-analysis
    - `file_types_included`: List of file types being processed
    - `message`: Status message

    **Example:**
    ```
    POST /library/reanalyze-all?file_type=.3mf&limit=100
    ```
    """
    logger.info("Starting bulk re-analysis", file_type=file_type, limit=limit)

    # Build filters for files to reanalyze
    filters = {}
    if file_type:
        filters['file_type'] = file_type

    # Get files to reanalyze
    files, pagination = await library_service.list_files(
        filters=filters,
        page=1,
        limit=limit or 10000  # Default to processing up to 10000 files
    )

    files_to_process = []
    file_types_set = set()

    # Filter to only files that can have metadata extracted
    for file in files:
        ft = file.get('file_type', '').lower()
        if ft in ['.3mf', '.gcode', '.bgcode']:
            files_to_process.append(file)
            file_types_set.add(ft)

    logger.info("Files found for re-analysis",
               total_files=len(files),
               processable_files=len(files_to_process),
               file_types=list(file_types_set))

    if not files_to_process:
        return success_response({
            'success': True,
            'files_scheduled': 0,
            'file_types_included': [],
            'message': 'No files found matching criteria or no files support metadata extraction'
        })

    # Schedule re-analysis for each file (fire and forget - don't await)
    scheduled_count = 0
    tasks = []
    for file in files_to_process:
        try:
            # Create task without awaiting to schedule all files quickly
            task = library_service.reprocess_file(file['checksum'])
            tasks.append(task)
        except Exception as e:
            logger.warning("Failed to create reprocessing task",
                         checksum=file['checksum'][:16],
                         error=str(e))

    # Await all scheduling tasks in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    scheduled_count = sum(1 for r in results if r is True)

    logger.info("Bulk re-analysis scheduled",
               files_scheduled=scheduled_count,
               file_types=list(file_types_set))

    return success_response({
        'success': True,
        'files_scheduled': scheduled_count,
        'file_types_included': list(file_types_set),
        'message': f'Scheduled {scheduled_count} files for metadata re-extraction. Processing will happen in the background.'
    })
