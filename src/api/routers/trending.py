"""
Trending Discovery API endpoints.
Provides REST API for trending 3D models from external platforms.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, Query, Body
from pydantic import BaseModel, Field

from src.services.trending_service import TrendingService
from src.utils.dependencies import get_trending_service
from src.utils.errors import (
    ValidationError as PrinternizerValidationError,
    NotFoundError,
    success_response
)


router = APIRouter(prefix="/ideas/trending", tags=["Trending"])


class TrendingModel(BaseModel):
    """Response model for trending items."""
    id: str
    platform: str
    model_id: str
    title: str
    url: str
    thumbnail_url: Optional[str]
    thumbnail_local_path: Optional[str]
    downloads: int
    likes: int
    creator: Optional[str]
    category: str
    cached_at: datetime
    expires_at: datetime
    metadata: Dict[str, Any]


class SaveTrendingRequest(BaseModel):
    """Request model for saving trending item as idea."""
    notes: Optional[str] = Field(None, max_length=1000, description="Optional notes for the idea")


class TrendingStats(BaseModel):
    """Statistics for trending cache."""
    total_cached: int
    valid_items: int
    by_platform: Dict[str, int]
    last_refresh: Dict[str, str]
    refresh_interval_hours: float


@router.get("", response_model=List[TrendingModel])
async def get_trending(
    platform: Optional[str] = Query(None, description="Filter by platform (makerworld, printables)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of items to return"),
    trending_service: TrendingService = Depends(get_trending_service)
):
    """Get trending models from cache."""
    items = await trending_service.get_trending(
        platform=platform,
        category=category,
        limit=limit
    )

    return [
        TrendingModel(
            id=item['id'],
            platform=item['platform'],
            model_id=item['model_id'],
            title=item['title'],
            url=item['url'],
            thumbnail_url=item.get('thumbnail_url'),
            thumbnail_local_path=item.get('thumbnail_local_path'),
            downloads=item.get('downloads', 0),
            likes=item.get('likes', 0),
            creator=item.get('creator'),
            category=item.get('category', 'general'),
            cached_at=datetime.fromisoformat(item['cached_at']),
            expires_at=datetime.fromisoformat(item['expires_at']),
            metadata=item.get('metadata', {}) if isinstance(item.get('metadata'), dict) else {}
        )
        for item in items
    ]


@router.get("/platforms")
async def get_supported_platforms():
    """Get list of supported platforms for trending discovery."""
    return {
        "platforms": [
            {
                "id": "makerworld",
                "name": "MakerWorld",
                "website": "https://makerworld.com",
                "description": "Bambu Lab's official model sharing platform"
            },
            {
                "id": "printables",
                "name": "Printables",
                "website": "https://www.printables.com",
                "description": "Prusa's model sharing platform"
            }
        ]
    }


@router.get("/stats", response_model=TrendingStats)
async def get_trending_stats(
    trending_service: TrendingService = Depends(get_trending_service)
):
    """Get trending cache statistics."""
    stats = await trending_service.get_statistics()
    return TrendingStats(**stats)


@router.post("/refresh", status_code=202)
async def refresh_trending(
    platform: Optional[str] = Query(None, description="Specific platform to refresh (optional)"),
    trending_service: TrendingService = Depends(get_trending_service)
):
    """Force refresh trending cache for all or specific platform."""
    if platform:
        # Refresh specific platform (would need platform-specific methods)
        if platform == "makerworld":
            items = await trending_service.fetch_makerworld_trending()
            await trending_service.save_trending_items(items, platform)
        elif platform == "printables":
            items = await trending_service.fetch_printables_trending()
            await trending_service.save_trending_items(items, platform)
        else:
            raise PrinternizerValidationError(
                field="platform",
                error=f"Unsupported platform: {platform}"
            )

        return {
            "message": f"Refresh initiated for {platform}",
            "items_cached": len(items) if 'items' in locals() else 0
        }
    else:
        # Refresh all platforms
        await trending_service.refresh_all_platforms()
        return {"message": "Refresh initiated for all platforms"}


@router.post("/{trending_id}/save", response_model=dict, status_code=201)
async def save_trending_as_idea(
    trending_id: str,
    request: SaveTrendingRequest,
    trending_service: TrendingService = Depends(get_trending_service)
):
    """Save a trending item as a personal idea."""
    try:
        idea_id = await trending_service.save_as_idea(
            trending_id=trending_id,
            user_notes=request.notes
        )

        return success_response({
            "message": "Trending item saved as idea successfully",
            "idea_id": idea_id,
            "trending_id": trending_id
        })

    except ValueError as e:
        raise NotFoundError(resource_type="trending_item", resource_id=trending_id)


@router.get("/{platform}")
async def get_platform_trending(
    platform: str,
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    trending_service: TrendingService = Depends(get_trending_service)
):
    """Get trending models for a specific platform."""
    supported_platforms = ["makerworld", "printables"]

    if platform not in supported_platforms:
        raise PrinternizerValidationError(
            field="platform",
            error=f"Unsupported platform. Supported: {supported_platforms}"
        )

    items = await trending_service.get_trending(
        platform=platform,
        category=category,
        limit=limit
    )

    return {
        "platform": platform,
        "total_items": len(items),
        "items": [
            {
                "id": item['id'],
                "model_id": item['model_id'],
                "title": item['title'],
                "url": item['url'],
                "creator": item.get('creator'),
                "downloads": item.get('downloads', 0),
                "likes": item.get('likes', 0),
                "category": item.get('category', 'general'),
                "cached_at": item['cached_at']
            }
            for item in items
        ]
    }


@router.delete("/cleanup", status_code=204)
async def cleanup_expired(
    trending_service: TrendingService = Depends(get_trending_service)
):
    """Clean up expired trending cache entries."""
    await trending_service.cleanup_expired()


@router.get("/categories/list")
async def get_trending_categories(
    platform: Optional[str] = Query(None),
    trending_service: TrendingService = Depends(get_trending_service)
):
    """Get available categories for trending items."""
    # This could be enhanced to get actual categories from the database
    default_categories = [
        "general",
        "functional",
        "artistic",
        "toys",
        "tools",
        "miniatures",
        "household",
        "automotive",
        "jewelry",
        "electronics"
    ]

    return {
        "categories": default_categories,
        "platform": platform
    }