"""
Ideas API router for managing print ideas and external model bookmarks.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

from src.utils.dependencies import get_database, get_idea_service
from src.services.idea_service import IdeaService
from src.services.url_parser_service import UrlParserService
from src.models.idea import IdeaStatus, IdeaSourceType

router = APIRouter(prefix="/api/ideas", tags=["ideas"])


# Pydantic models for API
class IdeaCreate(BaseModel):
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
    status: str = Field(..., regex="^(idea|planned|printing|completed|archived)$")


class IdeaImport(BaseModel):
    url: HttpUrl = Field(..., description="URL to import from external platform")
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=100)
    priority: int = Field(default=3, ge=1, le=5)
    is_business: bool = Field(default=False)
    tags: List[str] = Field(default_factory=list)


class TrendingSave(BaseModel):
    category: Optional[str] = Field(None, max_length=100)
    priority: int = Field(default=3, ge=1, le=5)
    is_business: bool = Field(default=False)
    tags: List[str] = Field(default_factory=list)


# API endpoints
@router.post("/", response_model=Dict[str, str])
async def create_idea(
    idea_data: IdeaCreate,
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Create a new idea."""
    try:
        idea_id = await idea_service.create_idea(idea_data.dict())
        if not idea_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create idea"
            )

        return {"id": idea_id, "message": "Idea created successfully"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/", response_model=Dict[str, Any])
async def list_ideas(
    status: Optional[str] = Query(None, regex="^(idea|planned|printing|completed|archived)$"),
    is_business: Optional[bool] = Query(None),
    category: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None, regex="^(manual|makerworld|printables)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    idea_service: IdeaService = Depends(get_idea_service)
):
    """List ideas with filtering and pagination."""
    try:
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

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{idea_id}", response_model=Dict[str, Any])
async def get_idea(
    idea_id: str,
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Get a specific idea by ID."""
    try:
        idea = await idea_service.get_idea(idea_id)
        if not idea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Idea not found"
            )

        return idea.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{idea_id}", response_model=Dict[str, str])
async def update_idea(
    idea_id: str,
    idea_data: IdeaUpdate,
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Update an existing idea."""
    try:
        # Check if idea exists
        existing_idea = await idea_service.get_idea(idea_id)
        if not existing_idea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Idea not found"
            )

        # Update only provided fields
        updates = idea_data.dict(exclude_unset=True)
        success = await idea_service.update_idea(idea_id, updates)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update idea"
            )

        return {"message": "Idea updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/{idea_id}", response_model=Dict[str, str])
async def delete_idea(
    idea_id: str,
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Delete an idea."""
    try:
        # Check if idea exists
        existing_idea = await idea_service.get_idea(idea_id)
        if not existing_idea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Idea not found"
            )

        success = await idea_service.delete_idea(idea_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete idea"
            )

        return {"message": "Idea deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.patch("/{idea_id}/status", response_model=Dict[str, str])
async def update_idea_status(
    idea_id: str,
    status_data: IdeaStatusUpdate,
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Update idea status."""
    try:
        # Check if idea exists
        existing_idea = await idea_service.get_idea(idea_id)
        if not existing_idea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Idea not found"
            )

        success = await idea_service.update_idea_status(idea_id, status_data.status)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update idea status"
            )

        return {"message": f"Idea status updated to {status_data.status}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/import", response_model=Dict[str, str])
async def import_idea_from_url(
    import_data: IdeaImport,
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Import an idea from external platform URL."""
    try:
        additional_data = import_data.dict(exclude={'url'})
        idea_id = await idea_service.import_from_url(str(import_data.url), additional_data)

        if not idea_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to import idea from URL"
            )

        return {"id": idea_id, "message": "Idea imported successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/tags/all", response_model=List[Dict[str, Any]])
async def get_all_tags(
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Get all available tags with usage counts."""
    try:
        return await idea_service.get_all_tags()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/stats/overview", response_model=Dict[str, Any])
async def get_idea_statistics(
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Get idea statistics."""
    try:
        return await idea_service.get_statistics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/search", response_model=List[Dict[str, Any]])
async def search_ideas(
    q: str = Query(..., min_length=1, description="Search query"),
    status: Optional[str] = Query(None, regex="^(idea|planned|printing|completed|archived)$"),
    is_business: Optional[bool] = Query(None),
    category: Optional[str] = Query(None),
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Search ideas by title, description, and tags."""
    try:
        filters = {}
        if status:
            filters['status'] = status
        if is_business is not None:
            filters['is_business'] = is_business
        if category:
            filters['category'] = category

        return await idea_service.search_ideas(q, filters)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Trending models endpoints
@router.get("/trending/{platform}", response_model=List[Dict[str, Any]])
async def get_trending_models(
    platform: str,
    category: Optional[str] = Query(None),
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Get trending models from external platforms."""
    try:
        if platform not in ['makerworld', 'printables', 'all']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid platform. Must be 'makerworld', 'printables', or 'all'"
            )

        platform_filter = None if platform == 'all' else platform
        return await idea_service.get_trending(platform_filter, category)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/trending/{trending_id}/save", response_model=Dict[str, str])
async def save_trending_as_idea(
    trending_id: str,
    save_data: TrendingSave,
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Save a trending model as a personal idea."""
    try:
        idea_id = await idea_service.save_trending_as_idea(trending_id, save_data.dict())

        if not idea_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to save trending model as idea"
            )

        return {"id": idea_id, "message": "Trending model saved as idea"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/trending/refresh", response_model=Dict[str, str])
async def refresh_trending_cache(
    idea_service: IdeaService = Depends(get_idea_service)
):
    """Force refresh of trending cache (admin endpoint)."""
    try:
        # This would typically trigger background jobs to refresh trending data
        # For now, just clean expired entries
        success = await idea_service.cleanup_expired_trending()

        if success:
            return {"message": "Trending cache refreshed"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to refresh trending cache"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )