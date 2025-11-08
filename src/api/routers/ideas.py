"""
Ideas API router for managing print ideas and external model bookmarks.
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

from src.utils.dependencies import get_database, get_idea_service
from src.services.idea_service import IdeaService
from src.services.url_parser_service import UrlParserService
from src.models.idea import IdeaStatus, IdeaSourceType
from src.utils.errors import (
    NotFoundError,
    ValidationError as PrinternizerValidationError,
    success_response
)

router = APIRouter(prefix="/ideas", tags=["ideas"])


# Pydantic models for API
class IdeaCreate(BaseModel):
    """
    Request model for creating a new idea.

    Attributes:
        title: Idea title (1-255 characters)
        description: Optional detailed description (up to 2000 characters)
        source_type: Type of source (default: "manual")
        source_url: Optional URL to external source
        category: Optional category classification
        priority: Priority level 1-5 (default: 3)
        is_business: Whether this is a business order (default: False)
        estimated_print_time: Estimated print time in minutes
        material_notes: Optional notes about materials needed
        customer_info: Optional customer information
        planned_date: Optional planned execution date
        tags: List of tags for categorization
        metadata: Additional metadata as key-value pairs
    """
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    source_type: str = Field(default="manual")
    source_url: Optional[HttpUrl] = None
    category: Optional[str] = Field(None, max_length=100)
    priority: int = Field(default=3, ge=1, le=5)
    is_business: bool = Field(default=False)
    estimated_print_time: Optional[int] = Field(None, ge=0)  # minutes
    material_notes: Optional[str] = Field(None, max_length=500)
    customer_info: Optional[str] = Field(None, max_length=500)
    planned_date: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


class IdeaUpdate(BaseModel):
    """
    Request model for updating an existing idea.

    All fields are optional. Only provided fields will be updated.

    Attributes:
        title: Updated title (1-255 characters)
        description: Updated description (up to 2000 characters)
        category: Updated category
        priority: Updated priority level 1-5
        is_business: Updated business flag
        estimated_print_time: Updated print time estimate in minutes
        material_notes: Updated material notes
        customer_info: Updated customer information
        planned_date: Updated planned date
        tags: Updated list of tags
        metadata: Updated metadata
    """
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=100)
    priority: Optional[int] = Field(None, ge=1, le=5)
    is_business: Optional[bool] = None
    estimated_print_time: Optional[int] = Field(None, ge=0)
    material_notes: Optional[str] = Field(None, max_length=500)
    customer_info: Optional[str] = Field(None, max_length=500)
    planned_date: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class IdeaStatusUpdate(BaseModel):
    """
    Request model for updating idea status.

    Attributes:
        status: New status (idea|planned|printing|completed|archived)
    """
    status: str = Field(..., pattern="^(idea|planned|printing|completed|archived)$")


class IdeaImport(BaseModel):
    """
    Request model for importing an idea from external platform URL.

    Attributes:
        url: URL to import from (MakerWorld, Printables, etc.)
        title: Optional override title
        description: Optional override description
        category: Optional category
        priority: Priority level 1-5 (default: 3)
        is_business: Whether this is a business order (default: False)
        tags: List of tags for categorization
    """
    url: HttpUrl = Field(..., description="URL to import from external platform")
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=100)
    priority: int = Field(default=3, ge=1, le=5)
    is_business: bool = Field(default=False)
    tags: List[str] = Field(default_factory=list)


class TrendingSave(BaseModel):
    """
    Request model for saving a trending model as a personal idea.

    Attributes:
        category: Optional category for the idea
        priority: Priority level 1-5 (default: 3)
        is_business: Whether this is a business order (default: False)
        tags: List of tags for categorization
    """
    category: Optional[str] = Field(None, max_length=100)
    priority: int = Field(default=3, ge=1, le=5)
    is_business: bool = Field(default=False)
    tags: List[str] = Field(default_factory=list)


# API endpoints
@router.post("", response_model=Dict[str, str])
async def create_idea(
    idea_data: IdeaCreate,
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Create a new idea."""
    try:
        idea_id = await idea_service.create_idea(idea_data.dict())
        if not idea_id:
            raise PrinternizerValidationError(
                field="idea_data",
                error="Failed to create idea"
            )

        return success_response({"id": idea_id, "message": "Idea created successfully"})

    except ValueError as e:
        raise PrinternizerValidationError(field="idea_data", error=str(e))


@router.get("", response_model=Dict[str, Any])
async def list_ideas(
    status: Optional[str] = Query(None, pattern="^(idea|planned|printing|completed|archived)$"),
    is_business: Optional[bool] = Query(None),
    category: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None, pattern="^(manual|makerworld|printables)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    idea_service: IdeaService = Depends(get_idea_service)
):
    """List ideas with filtering and pagination."""
    filters = {}
    if status:
        filters['status'] = status
    if is_business is not None:
        filters['is_business'] = is_business
    if category:
        filters['category'] = category
    if source_type:
        filters['source_type'] = source_type

    result = await idea_service.list_ideas(filters, page, page_size)
    return result


@router.get("/{idea_id}", response_model=Dict[str, Any])
async def get_idea(
    idea_id: str,
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Get a specific idea by ID."""
    idea = await idea_service.get_idea(idea_id)
    if not idea:
        raise NotFoundError(resource_type="idea", resource_id=idea_id)

    return idea.to_dict()


@router.put("/{idea_id}", response_model=Dict[str, str])
async def update_idea(
    idea_id: str,
    idea_data: IdeaUpdate,
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Update an existing idea."""
    # Check if idea exists
    existing_idea = await idea_service.get_idea(idea_id)
    if not existing_idea:
        raise NotFoundError(resource_type="idea", resource_id=idea_id)

    # Update only provided fields
    updates = idea_data.dict(exclude_unset=True)
    success = await idea_service.update_idea(idea_id, updates)

    if not success:
        raise PrinternizerValidationError(
            field="idea_data",
            error="Failed to update idea"
        )

    return success_response({"message": "Idea updated successfully"})


@router.delete("/{idea_id}", response_model=Dict[str, str])
async def delete_idea(
    idea_id: str,
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Delete an idea."""
    # Check if idea exists
    existing_idea = await idea_service.get_idea(idea_id)
    if not existing_idea:
        raise NotFoundError(resource_type="idea", resource_id=idea_id)

    success = await idea_service.delete_idea(idea_id)
    if not success:
        raise PrinternizerValidationError(
            field="idea",
            error="Failed to delete idea"
        )

    return success_response({"message": "Idea deleted successfully"})


@router.patch("/{idea_id}/status", response_model=Dict[str, str])
async def update_idea_status(
    idea_id: str,
    status_data: IdeaStatusUpdate,
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Update idea status."""
    # Check if idea exists
    existing_idea = await idea_service.get_idea(idea_id)
    if not existing_idea:
        raise NotFoundError(resource_type="idea", resource_id=idea_id)

    success = await idea_service.update_idea_status(idea_id, status_data.status)
    if not success:
        raise PrinternizerValidationError(
            field="status",
            error="Failed to update idea status"
        )

    return success_response({"message": f"Idea status updated to {status_data.status}"})


@router.post("/import", response_model=Dict[str, str])
async def import_idea_from_url(
    import_data: IdeaImport,
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Import an idea from external platform URL."""
    additional_data = import_data.dict(exclude={'url'})
    idea_id = await idea_service.import_from_url(str(import_data.url), additional_data)

    if not idea_id:
        raise PrinternizerValidationError(
            field="url",
            error="Failed to import idea from URL"
        )

    return success_response({"id": idea_id, "message": "Idea imported successfully"})


@router.get("/tags/all", response_model=List[Dict[str, Any]])
async def get_all_tags(
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Get all available tags with usage counts."""
    return await idea_service.get_all_tags()


@router.get("/stats/overview", response_model=Dict[str, Any])
async def get_idea_statistics(
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Get idea statistics."""
    return await idea_service.get_statistics()


@router.get("/search", response_model=List[Dict[str, Any]])
async def search_ideas(
    q: str = Query(..., min_length=1, description="Search query"),
    status: Optional[str] = Query(None, pattern="^(idea|planned|printing|completed|archived)$"),
    is_business: Optional[bool] = Query(None),
    category: Optional[str] = Query(None),
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Search ideas by title, description, and tags."""
    filters = {}
    if status:
        filters['status'] = status
    if is_business is not None:
        filters['is_business'] = is_business
    if category:
        filters['category'] = category

    return await idea_service.search_ideas(q, filters)


# Trending models endpoints
@router.get("/trending/{platform}", response_model=List[Dict[str, Any]])
async def get_trending_models(
    platform: str,
    category: Optional[str] = Query(None),
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Get trending models from external platforms."""
    if platform not in ['makerworld', 'printables', 'all']:
        raise PrinternizerValidationError(
            field="platform",
            error="Invalid platform. Must be 'makerworld', 'printables', or 'all'"
        )

    platform_filter = None if platform == 'all' else platform
    return await idea_service.get_trending(platform_filter, category)


@router.post("/trending/{trending_id}/save", response_model=Dict[str, str])
async def save_trending_as_idea(
    trending_id: str,
    save_data: TrendingSave,
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Save a trending model as a personal idea."""
    idea_id = await idea_service.save_trending_as_idea(trending_id, save_data.dict())

    if not idea_id:
        raise PrinternizerValidationError(
            field="trending_id",
            error="Failed to save trending model as idea"
        )

    return success_response({"id": idea_id, "message": "Trending model saved as idea"})


@router.post("/trending/refresh", response_model=Dict[str, str])
async def refresh_trending_cache(
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Force refresh of trending cache (admin endpoint)."""
    # This would typically trigger background jobs to refresh trending data
    # For now, just clean expired entries
    success = await idea_service.cleanup_expired_trending()

    if not success:
        raise PrinternizerValidationError(
            field="trending_cache",
            error="Failed to refresh trending cache"
        )

    return success_response({"message": "Trending cache refreshed"})