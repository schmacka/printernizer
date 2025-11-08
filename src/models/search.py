"""
Search models for unified cross-site search feature.
Supports searching across local files, ideas, and external platforms.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SearchSource(str, Enum):
    """Search source types."""
    LOCAL_FILES = "local_files"
    IDEAS = "ideas"
    # External platforms - for future phases
    MAKERWORLD = "makerworld"
    PRINTABLES = "printables"


class ResultType(str, Enum):
    """Result type classification."""
    FILE = "file"
    IDEA = "idea"
    EXTERNAL_MODEL = "external_model"


class SearchFilters(BaseModel):
    """Advanced search filters for refined results."""

    # File type filters
    file_types: Optional[List[str]] = Field(None, description="File types (stl, 3mf, gcode)")

    # Dimension filters (mm)
    min_width: Optional[float] = Field(None, ge=0, description="Minimum width in mm")
    max_width: Optional[float] = Field(None, ge=0, description="Maximum width in mm")
    min_depth: Optional[float] = Field(None, ge=0, description="Minimum depth in mm")
    max_depth: Optional[float] = Field(None, ge=0, description="Maximum depth in mm")
    min_height: Optional[float] = Field(None, ge=0, description="Minimum height in mm")
    max_height: Optional[float] = Field(None, ge=0, description="Maximum height in mm")

    # Print time filters (minutes)
    min_print_time: Optional[int] = Field(None, ge=0, description="Minimum print time in minutes")
    max_print_time: Optional[int] = Field(None, ge=0, description="Maximum print time in minutes")

    # Material filters
    material_types: Optional[List[str]] = Field(None, description="Material types (PLA, PETG, TPU)")
    min_material_weight: Optional[float] = Field(None, ge=0, description="Minimum material weight in grams")
    max_material_weight: Optional[float] = Field(None, ge=0, description="Maximum material weight in grams")

    # Cost filters (EUR)
    min_cost: Optional[float] = Field(None, ge=0, description="Minimum cost in EUR")
    max_cost: Optional[float] = Field(None, ge=0, description="Maximum cost in EUR")

    # Printer compatibility
    printer_models: Optional[List[str]] = Field(None, description="Compatible printer models")
    requires_support: Optional[bool] = Field(None, description="Filter by support requirement")

    # Quality/Difficulty
    difficulty_levels: Optional[List[str]] = Field(None, description="Difficulty levels")
    min_complexity_score: Optional[int] = Field(None, ge=1, le=10, description="Minimum complexity score")
    min_success_probability: Optional[int] = Field(None, ge=0, le=100, description="Minimum success probability")

    # Business/Private
    is_business: Optional[bool] = Field(None, description="Filter by business flag")

    # Status (for ideas)
    idea_status: Optional[List[str]] = Field(None, description="Idea status filter")

    # Date range filters
    created_after: Optional[datetime] = Field(None, description="Created after date")
    created_before: Optional[datetime] = Field(None, description="Created before date")


class SearchResult(BaseModel):
    """Individual search result from any source."""

    id: str = Field(..., description="Unique identifier")
    source: SearchSource = Field(..., description="Source of this result")
    result_type: ResultType = Field(..., description="Type of result")

    # Core fields
    title: str = Field(..., description="Title or filename")
    description: Optional[str] = Field(None, description="Description text")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL or path")

    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    # Relevance scoring
    relevance_score: float = Field(0.0, ge=0, le=100, description="Relevance score 0-100")
    match_highlights: Optional[List[str]] = Field(None, description="Fields that matched the query")

    # External model fields
    external_url: Optional[str] = Field(None, description="External platform URL")
    author: Optional[str] = Field(None, description="Author/creator name")
    likes_count: Optional[int] = Field(None, ge=0, description="Number of likes")
    downloads_count: Optional[int] = Field(None, ge=0, description="Number of downloads")

    # Local file fields
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    file_path: Optional[str] = Field(None, description="Local file path")
    print_time_minutes: Optional[int] = Field(None, ge=0, description="Print time in minutes")
    material_weight_grams: Optional[float] = Field(None, ge=0, description="Material weight in grams")
    cost_eur: Optional[float] = Field(None, ge=0, description="Cost in EUR")

    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    modified_at: Optional[datetime] = Field(None, description="Last modified timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class SearchResultGroup(BaseModel):
    """Group of results from one source."""

    source: SearchSource = Field(..., description="Source type")
    results: List[SearchResult] = Field(..., description="Results from this source")
    total_count: int = Field(..., ge=0, description="Total results available (may exceed results list)")
    has_more: bool = Field(..., description="Whether more results are available")


class SearchResults(BaseModel):
    """Complete search results response."""

    query: str = Field(..., description="Search query string")
    filters: SearchFilters = Field(..., description="Applied filters")

    # Grouped results
    groups: List[SearchResultGroup] = Field(..., description="Results grouped by source")

    # Aggregates
    total_results: int = Field(..., ge=0, description="Total results across all sources")
    search_time_ms: int = Field(..., ge=0, description="Search execution time in milliseconds")

    # Pagination
    page: int = Field(1, ge=1, description="Current page number")
    limit: int = Field(50, ge=1, le=200, description="Results per page")

    # Metadata
    sources_searched: List[SearchSource] = Field(..., description="Sources that were searched")
    sources_failed: List[str] = Field(default_factory=list, description="Sources that failed")
    cached: bool = Field(False, description="Whether results came from cache")


class SearchHistoryEntry(BaseModel):
    """Search history entry for tracking user searches."""

    id: str = Field(..., description="Unique identifier")
    query: str = Field(..., description="Search query")
    filters: Optional[Dict[str, Any]] = Field(None, description="Applied filters as JSON")
    results_count: int = Field(..., ge=0, description="Number of results returned")
    sources: List[SearchSource] = Field(..., description="Sources searched")
    searched_at: datetime = Field(..., description="Timestamp of search")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class SearchSuggestion(BaseModel):
    """Search suggestion/autocomplete entry."""

    text: str = Field(..., description="Suggestion text")
    source: Optional[SearchSource] = Field(None, description="Source of suggestion")
    type: str = Field(..., description="Type of suggestion (history, popular, title)")
    relevance: float = Field(0.0, ge=0, le=1.0, description="Relevance score 0-1")
