"""File management endpoints - Drucker-Dateien system."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from pydantic import BaseModel
import structlog
import base64

from src.models.file import File, FileStatus, FileSource, WatchFolderSettings, WatchFolderStatus, WatchFolderItem
from src.services.file_service import FileService
from src.services.config_service import ConfigService
from src.utils.dependencies import get_file_service, get_config_service


logger = structlog.get_logger()
router = APIRouter()


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
    try:
        logger.info("Listing files", printer_id=printer_id, status=status, source=source,
                   has_thumbnail=has_thumbnail, search=search, limit=limit, page=page)

        # Get all files matching filters (without pagination)
        all_files = await file_service.get_files(
            printer_id=printer_id,
            status=status,
            source=source,
            has_thumbnail=has_thumbnail,
            search=search,
            limit=None,  # Get all files first
            order_by=order_by,
            order_dir=order_dir,
            page=1
        )

        total_items = len(all_files)
        total_pages = max(1, (total_items + limit - 1) // limit) if limit else 1

        # Apply pagination
        start_idx = (page - 1) * limit if limit and page > 1 else 0
        end_idx = start_idx + limit if limit else total_items
        paginated_files = all_files[start_idx:end_idx]

        logger.info("Got files from service", total=total_items, page_count=len(paginated_files))

        file_list = [FileResponse.model_validate(file) for file in paginated_files]

        logger.info("Validated files", count=len(file_list))

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
    except Exception as e:
        logger.error("Failed to list files", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve files: {str(e)}"
        )


@router.get("/statistics")
async def get_file_statistics(
    file_service: FileService = Depends(get_file_service)
):
    """Get file management statistics."""
    try:
        stats = await file_service.get_file_statistics()
        return {
            "statistics": stats,
            "timestamp": "2025-09-26T18:55:00Z"
        }
    except Exception as e:
        logger.error("Failed to get file statistics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate file statistics"
        )


@router.get("/{file_id}", response_model=FileResponse)
async def get_file_by_id(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """Get file information by ID."""
    try:
        file_data = await file_service.get_file_by_id(file_id)
        if not file_data:
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        return FileResponse.model_validate(file_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get file by ID", file_id=file_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve file"
        )


@router.post("/{file_id}/download")
async def download_file(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """Download a file from printer to local storage."""
    try:
        # Parse file_id to extract printer_id and filename
        # file_id format: "{printer_id}_{filename}"
        if "_" not in file_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file_id format"
            )

        # Split on the first underscore to separate printer_id from filename
        parts = file_id.split("_", 1)
        printer_id = parts[0]
        filename = parts[1]

        logger.info("Downloading file",
                   file_id=file_id, printer_id=printer_id, filename=filename)

        result = await file_service.download_file(printer_id, filename)

        if not result.get('success', False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to download file"
            )
        return {"status": "downloaded"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to download file", file_id=str(file_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file"
        )


@router.post("/sync")
async def sync_printer_files(
    printer_id: Optional[str] = Query(None, description="Sync specific printer, or all if not specified"),
    file_service: FileService = Depends(get_file_service)
):
    """Synchronize file list with printers."""
    try:
        await file_service.sync_printer_files(printer_id)
        return {"status": "synced"}
    except Exception as e:
        logger.error("Failed to sync files", printer_id=str(printer_id) if printer_id else "all", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync files"
        )


@router.get("/{file_id}/thumbnail")
async def get_file_thumbnail(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """Get thumbnail image for a file."""
    try:
        file_data = await file_service.get_file_by_id(file_id)
        
        if not file_data:
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
        if not file_data.get('has_thumbnail') or not file_data.get('thumbnail_data'):
            raise HTTPException(
                status_code=404,
                detail="No thumbnail available for this file"
            )
        
        # Decode base64 thumbnail data
        try:
            thumbnail_data = base64.b64decode(file_data['thumbnail_data'])
        except Exception as e:
            logger.error("Failed to decode thumbnail data", file_id=file_id, error=str(e))
            raise HTTPException(
                status_code=500,
                detail="Invalid thumbnail data"
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get thumbnail", file_id=file_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve thumbnail"
        )


@router.get("/{file_id}/metadata")
async def get_file_metadata(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """Get metadata for a file."""
    try:
        file_data = await file_service.get_file_by_id(file_id)
        
        if not file_data:
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get file metadata", file_id=file_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve file metadata"
        )


@router.post("/{file_id}/process-thumbnails")
async def process_file_thumbnails(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """Manually trigger thumbnail processing for a file."""
    try:
        file_data = await file_service.get_file_by_id(file_id)
        
        if not file_data:
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )
        
        file_path = file_data.get('file_path')
        if not file_path:
            raise HTTPException(
                status_code=400,
                detail="File not available locally for processing"
            )
        
        success = await file_service.process_file_thumbnails(file_path, file_id)
        
        if success:
            return {"status": "success", "message": "Thumbnails processed successfully"}
        else:
            return {"status": "failed", "message": "Failed to process thumbnails"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to process thumbnails", file_id=file_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to process thumbnails"
        )



# Watch Folder Management Endpoints

@router.get("/watch-folders/settings", response_model=WatchFolderSettings)
async def get_watch_folder_settings(
    config_service: ConfigService = Depends(get_config_service)
):
    """Get watch folder settings."""
    try:
        settings = await config_service.get_watch_folder_settings()
        # Also get inactive folders to show all folders with activation status
        all_folders = await config_service.watch_folder_db.get_all_watch_folders(active_only=False)
        settings['watch_folders'] = [wf.to_dict() for wf in all_folders]
        return WatchFolderSettings(**settings)
    except Exception as e:
        logger.error("Failed to get watch folder settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get watch folder settings"
        )


@router.get("/watch-folders/status")
async def get_watch_folder_status(
    file_service: FileService = Depends(get_file_service),
    config_service: ConfigService = Depends(get_config_service)
):
    """Get watch folder status."""
    try:
        status_info = await file_service.get_watch_status()
        return status_info
    except Exception as e:
        logger.error("Failed to get watch folder status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get watch folder status"
        )


@router.get("/local")
async def list_local_files(
    watch_folder_path: Optional[str] = Query(None, description="Filter by watch folder path"),
    file_service: FileService = Depends(get_file_service)
):
    """List local files from watch folders."""
    try:
        files = await file_service.get_local_files()
        
        # Filter by watch folder path if specified
        if watch_folder_path:
            files = [f for f in files if f.get('watch_folder_path') == watch_folder_path]
        
        return {"files": files}
    except Exception as e:
        logger.error("Failed to list local files", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list local files"
        )


@router.post("/watch-folders/reload")
async def reload_watch_folders(
    file_service: FileService = Depends(get_file_service)
):
    """Reload watch folders configuration."""
    try:
        result = await file_service.reload_watch_folders()
        return result
    except Exception as e:
        logger.error("Failed to reload watch folders", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reload watch folders"
        )


@router.post("/watch-folders/validate")
async def validate_watch_folder(
    folder_path: str = Query(..., description="Folder path to validate"),
    config_service: ConfigService = Depends(get_config_service)
):
    """Validate a watch folder path."""
    try:
        validation = config_service.validate_watch_folder(folder_path)
        return validation
    except Exception as e:
        logger.error("Failed to validate watch folder", folder_path=folder_path, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate watch folder"
        )


@router.post("/watch-folders/add")
async def add_watch_folder(
    folder_path: str = Query(..., description="Folder path to add"),
    config_service: ConfigService = Depends(get_config_service),
    file_service: FileService = Depends(get_file_service)
):
    """Add a new watch folder."""
    try:
        # First validate the folder
        validation = config_service.validate_watch_folder(folder_path)
        if not validation["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation["error"]
            )
        
        # Add folder to configuration
        success = await config_service.add_watch_folder(folder_path)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Watch folder already exists or could not be added"
            )
        
        # Reload watch folders in file service
        await file_service.reload_watch_folders()
        
        return {"status": "added", "folder_path": folder_path}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to add watch folder", folder_path=folder_path, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add watch folder"
        )


@router.delete("/watch-folders/remove")
async def remove_watch_folder(
    folder_path: str = Query(..., description="Folder path to remove"),
    config_service: ConfigService = Depends(get_config_service),
    file_service: FileService = Depends(get_file_service)
):
    """Remove a watch folder."""
    try:
        # Remove folder from configuration
        success = await config_service.remove_watch_folder(folder_path)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Watch folder not found"
            )
        
        # Reload watch folders in file service
        await file_service.reload_watch_folders()
        
        return {"status": "removed", "folder_path": folder_path}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to remove watch folder", folder_path=folder_path, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove watch folder"
        )


@router.patch("/watch-folders/update")
async def update_watch_folder(
    folder_path: str = Query(..., description="Folder path to update"),
    is_active: bool = Query(..., description="Whether to activate or deactivate the folder"),
    config_service: ConfigService = Depends(get_config_service),
    file_service: FileService = Depends(get_file_service)
):
    """Update watch folder activation status."""
    try:
        # First get the watch folder by path to get its ID
        await config_service._ensure_env_migration()
        folder = await config_service.watch_folder_db.get_watch_folder_by_path(folder_path)

        if not folder:
            raise HTTPException(
                status_code=404,
                detail="Watch folder not found"
            )

        # Update the folder's active status
        success = await config_service.watch_folder_db.update_watch_folder(
            folder.id,
            {"is_active": is_active}
        )

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to update watch folder"
            )

        # Reload watch folders in file service to apply changes
        await file_service.reload_watch_folders()

        status_text = "activated" if is_active else "deactivated"
        return {
            "status": "updated",
            "folder_path": folder_path,
            "is_active": is_active,
            "message": f"Watch folder {status_text} successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update watch folder", folder_path=folder_path, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to update watch folder"
        )


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    file_service: FileService = Depends(get_file_service)
):
    """Delete a file (for local files, also deletes physical file)."""
    try:
        success = await file_service.delete_file(file_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found or could not be deleted"
            )

        return {"status": "deleted", "file_id": file_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete file", file_id=file_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


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
    file_service: FileService = Depends(get_file_service)
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
        
        # TODO: Get actual printer capabilities from printer service
        # For now, provide basic compatibility check
        
        compatibility = {
            'file_id': file_id,
            'printer_id': printer_id,
            'compatible': True,  # Default to compatible
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Check physical dimensions if available
        if metadata.physical_properties:
            # Bambu Lab A1 bed size: 256 x 256 x 256 mm
            # This is a simplified check - should get actual printer specs
            max_bed_size = 256
            
            if metadata.physical_properties.width and metadata.physical_properties.width > max_bed_size:
                compatibility['compatible'] = False
                compatibility['issues'].append({
                    'type': 'size',
                    'message': f'Model width ({metadata.physical_properties.width}mm) exceeds printer bed size'
                })
            
            if metadata.physical_properties.depth and metadata.physical_properties.depth > max_bed_size:
                compatibility['compatible'] = False
                compatibility['issues'].append({
                    'type': 'size',
                    'message': f'Model depth ({metadata.physical_properties.depth}mm) exceeds printer bed size'
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