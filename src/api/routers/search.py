"""
Search API endpoints for unified cross-site search.
Supports local files, ideas, and external platforms.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
import structlog

from src.models.search import (
    SearchSource, SearchFilters, SearchResults,
    SearchHistoryEntry, SearchSuggestion
)
from src.services.search_service import SearchService
from src.utils.dependencies import get_search_service
from src.utils.errors import (
    ValidationError as PrinternizerValidationError,
    NotFoundError,
    success_response
)

logger = structlog.get_logger()
router = APIRouter()


@router.get("", response_model=SearchResults)
async def unified_search(
    q: str = Query(..., min_length=1, description="Search query"),

    # Sources
    sources: Optional[str] = Query(
        None,
        description="Comma-separated sources (local_files,ideas). Default: all"
    ),

    # File filters
    file_types: Optional[str] = Query(None, description="Comma-separated: stl,3mf,gcode"),

    # Dimension filters (mm)
    min_width: Optional[float] = Query(None, ge=0, description="Minimum width in mm"),
    max_width: Optional[float] = Query(None, ge=0, description="Maximum width in mm"),
    min_depth: Optional[float] = Query(None, ge=0, description="Minimum depth in mm"),
    max_depth: Optional[float] = Query(None, ge=0, description="Maximum depth in mm"),
    min_height: Optional[float] = Query(None, ge=0, description="Minimum height in mm"),
    max_height: Optional[float] = Query(None, ge=0, description="Maximum height in mm"),

    # Material filters
    material_types: Optional[str] = Query(None, description="Comma-separated: PLA,PETG,TPU"),
    min_material_weight: Optional[float] = Query(None, ge=0, description="Min material weight in grams"),
    max_material_weight: Optional[float] = Query(None, ge=0, description="Max material weight in grams"),

    # Print time filters (minutes)
    min_print_time: Optional[int] = Query(None, ge=0, description="Minimum print time in minutes"),
    max_print_time: Optional[int] = Query(None, ge=0, description="Maximum print time in minutes"),

    # Cost filters (EUR)
    min_cost: Optional[float] = Query(None, ge=0, description="Minimum cost in EUR"),
    max_cost: Optional[float] = Query(None, ge=0, description="Maximum cost in EUR"),

    # Printer compatibility
    printer_models: Optional[str] = Query(None, description="Comma-separated printer models"),
    requires_support: Optional[bool] = Query(None, description="Filter by support requirement"),

    # Quality/Difficulty
    difficulty_levels: Optional[str] = Query(None, description="Comma-separated difficulty levels"),
    min_complexity: Optional[int] = Query(None, ge=1, le=10, description="Minimum complexity score"),
    min_success_probability: Optional[int] = Query(None, ge=0, le=100, description="Minimum success probability"),

    # Business filter
    is_business: Optional[bool] = Query(None, description="Filter by business flag"),

    # Idea filters
    idea_status: Optional[str] = Query(None, description="Comma-separated idea statuses"),

    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Results per page"),

    # Service
    search_service: SearchService = Depends(get_search_service)
):
    """
    Unified search across all sources.

    Searches:
    - Local files (library, printer files, watch folders)
    - Personal ideas and bookmarks
    - External platforms (future: Makerworld, Printables, etc.)

    Results are grouped by source and ranked by relevance.
    """
    try:
        # Parse sources
        if sources:
            source_list = [SearchSource(s.strip()) for s in sources.split(",")]
        else:
            # Default to local sources only
            source_list = [SearchSource.LOCAL_FILES, SearchSource.IDEAS]

        # Build filters
        filters = SearchFilters(
            file_types=file_types.split(",") if file_types else None,
            min_width=min_width,
            max_width=max_width,
            min_depth=min_depth,
            max_depth=max_depth,
            min_height=min_height,
            max_height=max_height,
            material_types=material_types.split(",") if material_types else None,
            min_material_weight=min_material_weight,
            max_material_weight=max_material_weight,
            min_print_time=min_print_time,
            max_print_time=max_print_time,
            min_cost=min_cost,
            max_cost=max_cost,
            printer_models=printer_models.split(",") if printer_models else None,
            requires_support=requires_support,
            difficulty_levels=difficulty_levels.split(",") if difficulty_levels else None,
            min_complexity_score=min_complexity,
            min_success_probability=min_success_probability,
            is_business=is_business,
            idea_status=idea_status.split(",") if idea_status else None
        )

        # Execute search
        results = await search_service.unified_search(
            query=q,
            sources=source_list,
            filters=filters,
            limit=limit,
            page=page
        )

        logger.info("Search completed", query=q, total_results=results.total_results,
                   search_time_ms=results.search_time_ms, cached=results.cached)

        return results

    except ValueError as e:
        raise PrinternizerValidationError(field="search_parameters", error=str(e))


@router.get("/history", response_model=List[SearchHistoryEntry])
async def get_search_history(
    limit: int = Query(20, ge=1, le=100, description="Number of history entries"),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Get recent search history.

    Returns the most recent searches with metadata about results count
    and sources searched.
    """
    history = await search_service.get_search_history(limit=limit)
    return history


@router.delete("/history/{search_id}")
async def delete_search_history(
    search_id: str,
    search_service: SearchService = Depends(get_search_service)
):
    """
    Delete a search history entry.

    Args:
        search_id: ID of the search history entry to delete
    """
    success = await search_service.delete_search_history(search_id)
    if not success:
        raise NotFoundError(resource_type="search_history", resource_id=search_id)

    return success_response({"status": "deleted", "id": search_id})


@router.get("/suggestions", response_model=List[SearchSuggestion])
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Partial query for suggestions"),
    limit: int = Query(10, ge=1, le=50, description="Number of suggestions"),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Get search suggestions based on:
    - Search history
    - Popular searches
    - File/idea titles (future)

    Args:
        q: Partial query string
        limit: Maximum number of suggestions
    """
    suggestions = await search_service.get_search_suggestions(q, limit)
    return suggestions
