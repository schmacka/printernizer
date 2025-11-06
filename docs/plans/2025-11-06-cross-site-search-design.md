# Cross-Site Search Feature - Design Document

**Date**: 2025-11-06
**Status**: Planning - Awaiting Approval
**Phase**: A - Unified Search Foundation
**Estimated Effort**: 12-16 hours

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Design Decisions](#design-decisions)
4. [Backend Architecture](#backend-architecture)
5. [Frontend UI Design](#frontend-ui-design)
6. [External API Integration](#external-api-integration)
7. [Data Flow](#data-flow)
8. [Search Algorithm](#search-algorithm)
9. [Caching Strategy](#caching-strategy)
10. [Error Handling](#error-handling)
11. [Implementation Details](#implementation-details)
12. [Testing Strategy](#testing-strategy)
13. [Future Phases](#future-phases)

---

## Executive Summary

### Problem
Printernizer users currently manage files across multiple locations:
- **Local library files** (uploaded or organized)
- **Printer files** (discovered from Bambu/Prusa printers)
- **Ideas** (personal project ideas)
- **External platforms** (Makerworld, Printables via trending/bookmarks)

Each source requires separate navigation and search. Users cannot:
- Search across all sources simultaneously
- Discover models from external platforms without leaving the app
- Find files by rich metadata (dimensions, materials, print time)
- Compare local files with trending/popular models

### Solution
**Unified Cross-Site Search** that aggregates results from:
1. **Local Sources**: Library files, printer files, watch folders
2. **Personal Content**: Ideas, bookmarks, projects
3. **External Platforms**: Makerworld, Printables, Thingiverse, Cults3D

**Key Features**:
- Single search interface with real-time results
- Result grouping by source (Local Files, Ideas, Makerworld, Printables, etc.)
- Rich metadata search (dimensions, materials, costs, print time)
- Relevance scoring and ranking
- Import/bookmark external models directly from results
- Search history and quick filters

### Goals
- **Unified Discovery**: One search box to find any model, anywhere
- **Rich Metadata Search**: Leverage existing enhanced metadata extraction
- **External Integration**: Discover trending/popular models from major platforms
- **Performance**: Sub-second search with caching and pagination
- **Scalability**: Handle 10,000+ local files + external API results

### Non-Goals (Future Phases)
- AI-powered search suggestions → Phase B
- Visual similarity search → Phase C
- Community search (shared libraries) → Phase D
- Integration with slicers → Future

---

## Current State Analysis

### Existing Search Capabilities

#### 1. File Search (Basic)
**Location**: `src/services/file_service.py:43-152`

```python
# Current implementation: In-memory substring matching
if search:
    search_lower = search.lower()
    files = [f for f in files if search_lower in f.get('filename', '').lower()]
```

**Characteristics**:
- ❌ Only searches filename field
- ❌ No metadata search (dimensions, materials, costs)
- ❌ No relevance ranking
- ❌ Client-side filtering (loads all files first)
- ✅ Case-insensitive
- ✅ Partial matching

**API Endpoint**: `GET /api/v1/files?search=query`

---

#### 2. Ideas Search (Multi-field)
**Location**: `src/services/idea_service.py:332-349`

```python
# Searches title, description, tags
for idea in ideas:
    if (query_lower in idea['title'].lower() or
        (idea.get('description') and query_lower in idea['description'].lower()) or
        any(query_lower in tag.lower() for tag in idea.get('tags', []))):
```

**Characteristics**:
- ✅ Multi-field search (title, description, tags)
- ✅ Supports filters (status, business, category)
- ❌ No relevance ranking
- ❌ Client-side filtering
- ❌ No external platform search

**API Endpoint**: `GET /api/v1/ideas/search?q=query`

---

#### 3. Library Search (Filename Only)
**Location**: `src/api/routers/library.py:142-224`

**Characteristics**:
- ❌ Only searches filename
- ✅ Combines with filters (file_type, manufacturer, printer_model)
- ✅ Pagination support
- ❌ No metadata search despite rich metadata available

**API Endpoint**: `GET /library/files?search=query`

---

#### 4. External Platform Integration (Partial)
**Location**: `src/api/routers/ideas.py` (Trending endpoints)

**Current Capabilities**:
- ✅ Fetch trending models from Makerworld and Printables
- ✅ Cache trending results (TTL-based)
- ✅ Parse model metadata from URLs
- ❌ No search functionality (only trending lists)
- ❌ No unified results

**API Endpoints**:
```
GET /api/v1/ideas/trending/makerworld
GET /api/v1/ideas/trending/printables
```

---

### Existing Infrastructure to Leverage

#### Rich Metadata Fields (Already Extracted)
From `src/models/file.py` and library schema:

**Physical Properties**:
- Width, depth, height (mm)
- Volume (cm³), surface area (cm²)
- Object count, bounding box

**Print Settings**:
- Layer height, nozzle diameter, wall thickness
- Infill density/pattern, support usage
- Print time estimate, temperatures

**Material Requirements**:
- Filament weight (g), length (m)
- Filament colors, material types (PLA, PETG, TPU, etc.)
- Multi-material flag

**Cost Analysis**:
- Material cost, energy cost, total cost (EUR)
- Cost per gram breakdown

**Quality Metrics**:
- Complexity score (1-10)
- Difficulty level (Beginner/Intermediate/Advanced/Expert)
- Success probability (0-100%)
- Overhang percentage

**Compatibility**:
- Compatible printer models
- Slicer name/version
- Bed type requirements

#### Services to Integrate
1. **FileService** - Local/printer files
2. **LibraryService** - Unified library with checksums
3. **IdeaService** - Personal ideas and bookmarks
4. **UrlParserService** - Parse external model URLs
5. **BambuParser** - Metadata extraction (already powerful)

---

## Design Decisions

### Architecture Pattern: Unified Search Service

**Decision**: Create a new `SearchService` that aggregates results from multiple sources.

**Rationale**:
- Separation of concerns (search logic separate from data services)
- Single entry point for all search operations
- Enables advanced features (ranking, caching, filtering)
- Can be extended without modifying existing services

**Alternative Considered**: Extend existing services
- ❌ Would duplicate search logic across services
- ❌ Difficult to implement unified ranking
- ❌ Hard to add external platform search

---

### Search Scope: Hybrid (Local + External)

**Decision**: Search both local content and external platforms simultaneously with configurable sources.

**Rationale**:
- Users want comprehensive discovery
- External platforms have valuable community content
- Can be toggled on/off per search
- Results clearly labeled by source

**Phases**:
- **Phase A**: Local files, ideas, cached trending
- **Phase B**: Live external API search (Makerworld, Printables)
- **Phase C**: Additional platforms (Thingiverse, Cults3D, Thangs)

---

### Search Algorithm: Weighted Multi-Field

**Decision**: Score results based on field matches with weights.

**Scoring Formula**:
```
Score = (filename_match * 10) +
        (title_match * 8) +
        (description_match * 4) +
        (tag_match * 6) +
        (metadata_match * 3) +
        (exact_match_bonus * 20) +
        (source_boost * 2)
```

**Rationale**:
- Filename matches most important (user knows what they want)
- Tags important for categorization
- Metadata provides context
- Exact matches ranked highest
- Local files slightly boosted (faster access)

---

### Caching Strategy: Multi-Layer

**Decision**: Three-layer caching system

1. **Layer 1 - Search Results Cache** (5 minutes TTL)
   - Cache full search results for identical queries
   - Key: `search:{query}:{filters_hash}`

2. **Layer 2 - External Platform Cache** (1 hour TTL)
   - Cache external API responses
   - Reduces API rate limit issues
   - Key: `external:{platform}:{search_query}`

3. **Layer 3 - Metadata Cache** (indefinite, invalidate on update)
   - Cache enriched file metadata
   - Key: `metadata:{file_id}`

**Rationale**:
- Fast response times (<100ms for cached queries)
- Reduces external API calls (rate limits)
- Balances freshness vs performance

---

### Result Presentation: Grouped by Source

**Decision**: Group results by source type with expandable sections.

**Groups**:
1. Local Files (Library + Printer + Watch Folders)
2. Ideas (Personal projects)
3. Makerworld (External)
4. Printables (External)
5. Thingiverse (Phase C)
6. Cults3D (Phase C)

**Rationale**:
- Clear source attribution
- Users can focus on specific sources
- Easy to expand/collapse sections
- Shows result counts per source

---

### External API Integration: Rate-Limited + Cached

**Decision**: Implement rate limiting, caching, and fallback mechanisms.

**Rate Limits**:
- Makerworld: 60 requests/minute (estimated)
- Printables: 100 requests/minute (estimated)
- Fallback to cached results if rate limited

**Error Handling**:
- Network errors: Show cached results + error toast
- API errors: Skip that source, continue with others
- Timeout (5s): Abort external search, show local results

---

## Backend Architecture

### New Service: SearchService

**Location**: `src/services/search_service.py`

**Responsibilities**:
- Aggregate results from multiple sources
- Apply relevance scoring and ranking
- Manage search caching
- Handle external API integration
- Filter and paginate unified results

**Key Methods**:

```python
class SearchService:
    async def unified_search(
        self,
        query: str,
        sources: List[SearchSource],
        filters: SearchFilters,
        limit: int = 50,
        page: int = 1
    ) -> SearchResults:
        """
        Unified search across all sources.

        Args:
            query: Search query string
            sources: List of sources to search (local, ideas, makerworld, etc.)
            filters: Advanced filters (file_type, dimensions, materials, etc.)
            limit: Results per page
            page: Page number

        Returns:
            SearchResults with grouped and ranked results
        """

    async def search_local_files(self, query: str, filters: SearchFilters) -> List[SearchResult]
    async def search_ideas(self, query: str, filters: SearchFilters) -> List[SearchResult]
    async def search_makerworld(self, query: str, limit: int) -> List[SearchResult]
    async def search_printables(self, query: str, limit: int) -> List[SearchResult]

    def calculate_relevance_score(self, result: SearchResult, query: str) -> float
    def merge_and_rank_results(self, results: List[List[SearchResult]]) -> List[SearchResult]

    async def import_external_model(self, url: str, save_to_ideas: bool = True) -> Idea
```

---

### Enhanced Database Queries

#### Full-Text Search (SQLite FTS5)

**Decision**: Use SQLite FTS5 for fast full-text search.

**New Tables**:

```sql
-- Full-text search index for files
CREATE VIRTUAL TABLE fts_files USING fts5(
    file_id UNINDEXED,
    filename,
    description,
    tags,
    material_types,
    printer_models,
    content=files,
    content_rowid=rowid
);

-- Full-text search index for ideas
CREATE VIRTUAL TABLE fts_ideas USING fts5(
    idea_id UNINDEXED,
    title,
    description,
    tags,
    category,
    content=ideas,
    content_rowid=rowid
);

-- Search history
CREATE TABLE search_history (
    id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    filters TEXT, -- JSON
    results_count INTEGER,
    sources TEXT, -- JSON array
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_context TEXT -- Future: multi-user support
);

-- Search result clicks (analytics)
CREATE TABLE search_analytics (
    id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    result_id TEXT NOT NULL,
    result_source TEXT NOT NULL,
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    position INTEGER -- Position in results
);
```

**Triggers** (Keep FTS in sync):

```sql
-- Trigger: files insert
CREATE TRIGGER files_fts_insert AFTER INSERT ON files BEGIN
    INSERT INTO fts_files(file_id, filename, description, tags, material_types, printer_models)
    VALUES (new.id, new.filename, new.display_name, new.metadata, ...);
END;

-- Trigger: files update
CREATE TRIGGER files_fts_update AFTER UPDATE ON files BEGIN
    UPDATE fts_files SET
        filename = new.filename,
        description = new.display_name,
        tags = new.metadata
    WHERE file_id = new.id;
END;

-- Trigger: files delete
CREATE TRIGGER files_fts_delete AFTER DELETE ON files BEGIN
    DELETE FROM fts_files WHERE file_id = old.id;
END;

-- Similar triggers for ideas table
```

---

### New Models

**Location**: `src/models/search.py`

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

class SearchSource(str, Enum):
    """Search sources"""
    LOCAL_FILES = "local_files"
    IDEAS = "ideas"
    MAKERWORLD = "makerworld"
    PRINTABLES = "printables"
    THINGIVERSE = "thingiverse"  # Phase C
    CULTS3D = "cults3d"          # Phase C

class ResultType(str, Enum):
    """Result type"""
    FILE = "file"
    IDEA = "idea"
    EXTERNAL_MODEL = "external_model"

@dataclass
class SearchFilters:
    """Advanced search filters"""
    # File type
    file_types: Optional[List[str]] = None  # ["stl", "3mf", "gcode"]

    # Dimensions (mm)
    min_width: Optional[float] = None
    max_width: Optional[float] = None
    min_depth: Optional[float] = None
    max_depth: Optional[float] = None
    min_height: Optional[float] = None
    max_height: Optional[float] = None

    # Print time (minutes)
    min_print_time: Optional[int] = None
    max_print_time: Optional[int] = None

    # Materials
    material_types: Optional[List[str]] = None  # ["PLA", "PETG", "TPU"]
    material_weight_min: Optional[float] = None  # grams
    material_weight_max: Optional[float] = None

    # Costs (EUR)
    min_cost: Optional[float] = None
    max_cost: Optional[float] = None

    # Printer compatibility
    printer_models: Optional[List[str]] = None  # ["A1", "Core One"]
    requires_support: Optional[bool] = None

    # Quality/Difficulty
    difficulty_levels: Optional[List[str]] = None  # ["Beginner", "Intermediate"]
    min_complexity_score: Optional[int] = None  # 1-10
    min_success_probability: Optional[int] = None  # 0-100%

    # Business/Private
    is_business: Optional[bool] = None

    # Status (for ideas)
    idea_status: Optional[List[str]] = None  # ["planned", "in_progress"]

    # Date ranges
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

@dataclass
class SearchResult:
    """Individual search result"""
    id: str
    source: SearchSource
    result_type: ResultType

    # Core fields
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = None

    # Relevance
    relevance_score: float = 0.0
    match_highlights: List[str] = None  # ["filename", "description"]

    # External model fields
    external_url: Optional[str] = None
    author: Optional[str] = None
    likes_count: Optional[int] = None
    downloads_count: Optional[int] = None

    # Local file fields
    file_size: Optional[int] = None
    file_path: Optional[str] = None
    print_time_minutes: Optional[int] = None
    material_weight_grams: Optional[float] = None
    cost_eur: Optional[float] = None

    # Timestamps
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None

@dataclass
class SearchResultGroup:
    """Group of results from one source"""
    source: SearchSource
    results: List[SearchResult]
    total_count: int  # Total available (may be > len(results))
    has_more: bool

@dataclass
class SearchResults:
    """Complete search results"""
    query: str
    filters: SearchFilters

    # Grouped results
    groups: List[SearchResultGroup]

    # Aggregates
    total_results: int
    search_time_ms: int

    # Pagination
    page: int
    limit: int

    # Metadata
    sources_searched: List[SearchSource]
    sources_failed: List[str]  # Sources that errored
    cached: bool

class SearchHistoryEntry(BaseModel):
    """Search history entry"""
    id: str
    query: str
    filters: Optional[Dict[str, Any]] = None
    results_count: int
    sources: List[SearchSource]
    searched_at: datetime
```

---

### New API Router

**Location**: `src/api/routers/search.py`

```python
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from src.services.search_service import SearchService
from src.models.search import *

router = APIRouter(prefix="/api/v1/search", tags=["search"])

@router.get("", response_model=SearchResults)
async def unified_search(
    q: str = Query(..., min_length=2, description="Search query"),

    # Sources
    sources: Optional[str] = Query(
        None,
        description="Comma-separated sources (local_files,ideas,makerworld,printables)"
    ),

    # File filters
    file_types: Optional[str] = Query(None, description="Comma-separated: stl,3mf,gcode"),

    # Dimension filters
    min_width: Optional[float] = Query(None, ge=0),
    max_width: Optional[float] = Query(None, ge=0),
    min_height: Optional[float] = Query(None, ge=0),
    max_height: Optional[float] = Query(None, ge=0),

    # Material filters
    material_types: Optional[str] = Query(None, description="Comma-separated: PLA,PETG,TPU"),
    min_material_weight: Optional[float] = Query(None, ge=0),
    max_material_weight: Optional[float] = Query(None, ge=0),

    # Print time filters
    min_print_time: Optional[int] = Query(None, ge=0, description="Minutes"),
    max_print_time: Optional[int] = Query(None, ge=0, description="Minutes"),

    # Cost filters
    min_cost: Optional[float] = Query(None, ge=0, description="EUR"),
    max_cost: Optional[float] = Query(None, ge=0, description="EUR"),

    # Printer compatibility
    printer_models: Optional[str] = Query(None, description="Comma-separated printer models"),
    requires_support: Optional[bool] = Query(None),

    # Quality/Difficulty
    difficulty_levels: Optional[str] = Query(None),
    min_complexity: Optional[int] = Query(None, ge=1, le=10),
    min_success_probability: Optional[int] = Query(None, ge=0, le=100),

    # Business filter
    is_business: Optional[bool] = Query(None),

    # Pagination
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),

    # Service
    search_service: SearchService = Depends(get_search_service)
):
    """
    Unified search across all sources.

    Searches:
    - Local files (library, printer files, watch folders)
    - Personal ideas and bookmarks
    - External platforms (Makerworld, Printables, etc.)

    Results are grouped by source and ranked by relevance.
    """
    # Parse sources
    source_list = [SearchSource(s.strip()) for s in sources.split(",")] if sources else [
        SearchSource.LOCAL_FILES,
        SearchSource.IDEAS,
        SearchSource.MAKERWORLD,
        SearchSource.PRINTABLES
    ]

    # Build filters
    filters = SearchFilters(
        file_types=file_types.split(",") if file_types else None,
        min_width=min_width,
        max_width=max_width,
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
        is_business=is_business
    )

    # Execute search
    results = await search_service.unified_search(
        query=q,
        sources=source_list,
        filters=filters,
        limit=limit,
        page=page
    )

    return results

@router.get("/history", response_model=List[SearchHistoryEntry])
async def get_search_history(
    limit: int = Query(20, ge=1, le=100),
    search_service: SearchService = Depends(get_search_service)
):
    """Get recent search history"""
    return await search_service.get_search_history(limit=limit)

@router.delete("/history/{search_id}")
async def delete_search_history(
    search_id: str,
    search_service: SearchService = Depends(get_search_service)
):
    """Delete a search history entry"""
    await search_service.delete_search_history(search_id)
    return {"status": "deleted"}

@router.post("/import")
async def import_external_model(
    url: str = Query(..., description="External model URL"),
    save_to_ideas: bool = Query(True, description="Save to Ideas"),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Import an external model (from Makerworld, Printables, etc.).
    Optionally saves to Ideas for tracking.
    """
    idea = await search_service.import_external_model(url, save_to_ideas)
    return idea

@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Partial query"),
    limit: int = Query(10, ge=1, le=50),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Get search suggestions based on:
    - Search history
    - Popular searches
    - File/idea titles
    """
    suggestions = await search_service.get_search_suggestions(q, limit)
    return {"suggestions": suggestions}
```

---

### External Platform API Clients

**Location**: `src/integrations/external_search/`

#### Base Client

```python
# src/integrations/external_search/base.py

from abc import ABC, abstractmethod
from typing import List, Optional
from src.models.search import SearchResult

class ExternalPlatformClient(ABC):
    """Base class for external platform search clients"""

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """Search platform for models"""
        pass

    @abstractmethod
    async def get_trending(self, limit: int = 20) -> List[SearchResult]:
        """Get trending models"""
        pass

    @abstractmethod
    async def parse_model_url(self, url: str) -> SearchResult:
        """Parse model from URL"""
        pass
```

#### Makerworld Client

```python
# src/integrations/external_search/makerworld.py

import aiohttp
from typing import List
from src.models.search import SearchResult, SearchSource, ResultType
from .base import ExternalPlatformClient

class MakerworldClient(ExternalPlatformClient):
    BASE_URL = "https://api.makerworld.com/v1"

    def __init__(self, cache_ttl: int = 3600):
        self.cache = {}
        self.cache_ttl = cache_ttl

    async def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """
        Search Makerworld for models.

        API Endpoint: GET /search/models?q={query}&limit={limit}
        """
        cache_key = f"makerworld:search:{query}:{limit}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        async with aiohttp.ClientSession() as session:
            params = {"q": query, "limit": limit}
            async with session.get(f"{self.BASE_URL}/search/models", params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = self._parse_search_results(data)
                    self.cache[cache_key] = results
                    return results
                else:
                    # Log error and return empty
                    return []

    async def get_trending(self, limit: int = 20) -> List[SearchResult]:
        """Get trending models from Makerworld"""
        # Leverage existing trending endpoint
        # src/api/routers/ideas.py already implements this
        pass

    def _parse_search_results(self, data: dict) -> List[SearchResult]:
        """Parse API response to SearchResult objects"""
        results = []
        for item in data.get("models", []):
            result = SearchResult(
                id=item["id"],
                source=SearchSource.MAKERWORLD,
                result_type=ResultType.EXTERNAL_MODEL,
                title=item["name"],
                description=item.get("description"),
                thumbnail_url=item.get("thumbnail_url"),
                external_url=f"https://makerworld.com/models/{item['id']}",
                author=item.get("designer", {}).get("name"),
                likes_count=item.get("likes_count", 0),
                downloads_count=item.get("downloads_count", 0),
                created_at=item.get("created_at"),
                metadata={
                    "tags": item.get("tags", []),
                    "category": item.get("category"),
                    "license": item.get("license")
                }
            )
            results.append(result)
        return results
```

#### Printables Client

```python
# src/integrations/external_search/printables.py

import aiohttp
from typing import List
from src.models.search import SearchResult, SearchSource, ResultType
from .base import ExternalPlatformClient

class PrintablesClient(ExternalPlatformClient):
    BASE_URL = "https://api.printables.com/v1"

    async def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """
        Search Printables for models.

        API Endpoint: GET /search?q={query}&limit={limit}
        """
        # Implementation similar to Makerworld
        # Use existing trending infrastructure from src/api/routers/ideas.py
        pass

    def _parse_search_results(self, data: dict) -> List[SearchResult]:
        """Parse Printables API response"""
        results = []
        for item in data.get("items", []):
            result = SearchResult(
                id=item["id"],
                source=SearchSource.PRINTABLES,
                result_type=ResultType.EXTERNAL_MODEL,
                title=item["name"],
                description=item.get("summary"),
                thumbnail_url=item.get("images", [{}])[0].get("url"),
                external_url=f"https://www.printables.com/model/{item['id']}",
                author=item.get("user", {}).get("name"),
                likes_count=item.get("like_count", 0),
                downloads_count=item.get("download_count", 0),
                created_at=item.get("published_at"),
                metadata={
                    "tags": [t["name"] for t in item.get("tags", [])],
                    "category": item.get("category", {}).get("name"),
                    "license": item.get("license", {}).get("name")
                }
            )
            results.append(result)
        return results
```

---

## Frontend UI Design

### 1. Global Search Bar Component

**Location**: `frontend/src/components/search/GlobalSearchBar.tsx`

**Features**:
- Fixed top bar (always visible)
- Auto-complete suggestions
- Quick filters (dropdown)
- Search history (recent searches)
- Keyboard shortcuts (Ctrl+K / Cmd+K)

**UI Mockup**:

```
┌─────────────────────────────────────────────────────────────────┐
│  🔍  Search files, ideas, Makerworld, Printables...   [⚙️ Filters]│
│                                                                   │
│  Suggestions:                                                     │
│  📄 benchy.stl (Local File)                                      │
│  💡 Enclosure for Raspberry Pi (Idea)                           │
│  🌐 Benchy - Makerworld                                          │
│  🌐 3DBenchy - Printables                                        │
│                                                                   │
│  Recent Searches:                                                │
│  • benchy                                                        │
│  • raspberry pi case                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

### 2. Search Results Page

**Location**: `frontend/src/pages/SearchResults.tsx`

**Layout**:
- Left sidebar: Advanced filters (collapsible)
- Main area: Grouped results
- Right sidebar: Quick actions (optional)

**Grouped Results Display**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Search results for "benchy" (127 results in 0.12s)                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─ 📁 Local Files (45 results) ──────────────────────────── [View All]│
│  │                                                                      │
│  │  [Thumbnail]  benchy.stl                    🕐 2h print  💰 €0.45  │
│  │               Dimensions: 60x60x45mm         🎨 PLA       🔧 A1    │
│  │               Score: 95%  |  Modified: 2 days ago                   │
│  │                                                                      │
│  │  [Thumbnail]  3DBenchy_v2.3mf              🕐 2.5h      💰 €0.52   │
│  │               Dimensions: 65x60x48mm         🎨 PETG      🔧 Core One│
│  │               Score: 88%  |  Modified: 1 week ago                   │
│  │                                                                      │
│  └─ [Show 43 more...]                                                  │
│                                                                         │
│  ┌─ 💡 Ideas (3 results) ───────────────────────────────── [View All] │
│  │                                                                      │
│  │  [Thumbnail]  Benchy Army Project                                   │
│  │               Status: In Progress  |  Business: No                  │
│  │               Print 50 benchies for testing material quality        │
│  │                                                                      │
│  └─ [Show 2 more...]                                                   │
│                                                                         │
│  ┌─ 🌐 Makerworld (47 results) ────────────────────────── [View All]  │
│  │                                                                      │
│  │  [Thumbnail]  3DBenchy - The jolly 3D printing torture-test        │
│  │               by CreativeTools  |  ⭐ 12.4k  |  📥 2.1M downloads   │
│  │               [View on Makerworld] [Bookmark] [Import]              │
│  │                                                                      │
│  │  [Thumbnail]  Benchy Multi-Color Edition                            │
│  │               by DesignStudio    |  ⭐ 3.2k   |  📥 450k downloads  │
│  │               [View on Makerworld] [Bookmark] [Import]              │
│  │                                                                      │
│  └─ [Show 45 more...]                                                  │
│                                                                         │
│  ┌─ 🌐 Printables (32 results) ────────────────────────── [View All]  │
│  │                                                                      │
│  │  [Thumbnail]  #3DBenchy - The jolly 3D printing torture-test       │
│  │               by CreativeTools  |  👍 8.9k   |  📥 1.8M downloads   │
│  │               [View on Printables] [Bookmark] [Import]              │
│  │                                                                      │
│  └─ [Show 31 more...]                                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 3. Advanced Filters Sidebar

**Location**: `frontend/src/components/search/AdvancedFilters.tsx`

**Filter Categories**:

```
┌── Advanced Filters ────────────┐
│                                │
│  🔍 Search In:                 │
│  ☑ Local Files                 │
│  ☑ Ideas                       │
│  ☑ Makerworld                  │
│  ☑ Printables                  │
│  ☐ Thingiverse (Coming Soon)   │
│                                │
│  📄 File Type:                 │
│  ☐ STL                         │
│  ☐ 3MF                         │
│  ☐ G-Code                      │
│  ☐ STEP                        │
│                                │
│  📏 Dimensions (mm):           │
│  Width:  [min] - [max]         │
│  Depth:  [min] - [max]         │
│  Height: [min] - [max]         │
│                                │
│  🕐 Print Time:                │
│  [ 0 ] ───────────── [ 24h ]  │
│                                │
│  🎨 Materials:                 │
│  ☐ PLA  ☐ PETG  ☐ TPU          │
│  ☐ ABS  ☐ ASA   ☐ Other        │
│  Weight: [min] - [max] g       │
│                                │
│  💰 Cost (EUR):                │
│  [ 0 ] ───────────── [ 50 ]   │
│                                │
│  🔧 Printer:                   │
│  ☐ Bambu A1                    │
│  ☐ Prusa Core One              │
│  ☐ Any Printer                 │
│                                │
│  🏢 Business:                  │
│  ⚪ All                        │
│  ⚪ Business Only              │
│  ⚪ Private Only               │
│                                │
│  📊 Quality:                   │
│  Difficulty:                   │
│  ☐ Beginner  ☐ Intermediate    │
│  ☐ Advanced  ☐ Expert          │
│                                │
│  Complexity: [ 1 ] ─── [ 10 ]  │
│                                │
│  [Reset Filters]  [Apply]      │
│                                │
└────────────────────────────────┘
```

---

### 4. Result Card Component

**Location**: `frontend/src/components/search/ResultCard.tsx`

**Card Types**:

#### Local File Card
```
┌─────────────────────────────────────────┐
│ [Thumbnail Image]                       │
│                                         │
│ benchy.stl                              │
│ 📁 Local File                           │
│                                         │
│ 60×60×45mm  |  2h print  |  €0.45      │
│ 🎨 PLA (35g)  |  🔧 Bambu A1           │
│                                         │
│ [Download] [Open Folder] [Delete]       │
└─────────────────────────────────────────┘
```

#### External Model Card
```
┌─────────────────────────────────────────┐
│ [Thumbnail Image]                       │
│                                         │
│ 3DBenchy - Torture Test                 │
│ 🌐 Makerworld                           │
│                                         │
│ by CreativeTools                        │
│ ⭐ 12.4k likes  |  📥 2.1M downloads    │
│                                         │
│ [View Online] [Bookmark] [Import]       │
└─────────────────────────────────────────┘
```

#### Idea Card
```
┌─────────────────────────────────────────┐
│ [Thumbnail Image]                       │
│                                         │
│ Benchy Army Project                     │
│ 💡 Idea                                 │
│                                         │
│ Status: In Progress                     │
│ Business: No                            │
│                                         │
│ Print 50 benchies for testing...       │
│                                         │
│ [View Details] [Edit] [Start Print]     │
└─────────────────────────────────────────┘
```

---

### 5. Quick Import Modal

**Location**: `frontend/src/components/search/ImportModal.tsx`

**Purpose**: Import external model to Ideas

```
┌─── Import Model ────────────────────────────┐
│                                             │
│  Model: 3DBenchy - Torture Test             │
│  Source: Makerworld                         │
│  Author: CreativeTools                      │
│                                             │
│  [Thumbnail]                                │
│                                             │
│  Save to Ideas?                             │
│  ☑ Yes, save as a new idea                  │
│                                             │
│  Title: [3DBenchy - Torture Test      ]     │
│                                             │
│  Category: [Testing/Calibration ▼]          │
│                                             │
│  Tags: [benchy, torture-test, calibration]  │
│                                             │
│  Business: ☐ Mark as business order         │
│                                             │
│  Priority:  ⚪ Low  ⚪ Medium  ⚪ High       │
│                                             │
│  Notes:                                     │
│  ┌─────────────────────────────────────┐   │
│  │ For testing new PLA filament quality│   │
│  │                                     │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  [Cancel]              [Import]             │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Data Flow

### Search Request Flow

```
┌─────────────┐
│   Frontend  │
│  SearchBar  │
└──────┬──────┘
       │ 1. User types query
       │ 2. GET /api/v1/search?q=benchy&sources=local_files,makerworld
       ↓
┌─────────────┐
│  FastAPI    │
│   Router    │
│ (search.py) │
└──────┬──────┘
       │ 3. Parse query + filters
       │ 4. Call SearchService
       ↓
┌──────────────────────────────────────────┐
│         SearchService                    │
│  (unified_search)                        │
└──────┬───────────────────────────────────┘
       │
       ├─ 5a. Check cache → ⚡ Return if hit
       │
       ├─ 5b. If cache miss, search all sources in parallel:
       │
       ├─────┬─────────────────────────────────────────────┐
       │     │                                             │
       ↓     ↓                                             ↓
  ┌─────────┐  ┌─────────┐  ┌──────────────┐  ┌──────────────┐
  │  File   │  │  Idea   │  │  Makerworld  │  │  Printables  │
  │ Service │  │ Service │  │   Client     │  │   Client     │
  └────┬────┘  └────┬────┘  └──────┬───────┘  └──────┬───────┘
       │            │              │                  │
       │ 6a. FTS    │ 6b. FTS      │ 6c. HTTP API    │ 6d. HTTP API
       │ Query      │ Query        │ Request         │ Request
       ↓            ↓              ↓                  ↓
  ┌─────────┐  ┌─────────┐  ┌──────────────┐  ┌──────────────┐
  │ SQLite  │  │ SQLite  │  │  Makerworld  │  │  Printables  │
  │   DB    │  │   DB    │  │     API      │  │     API      │
  └────┬────┘  └────┬────┘  └──────┬───────┘  └──────┬───────┘
       │            │              │                  │
       │ 7. Results │              │                  │
       └────────────┴──────────────┴──────────────────┘
                              │
       ┌──────────────────────┘
       │
       ↓
┌──────────────────────────────────────────┐
│  SearchService                           │
│  - Calculate relevance scores            │
│  - Merge and rank results                │
│  - Group by source                       │
│  - Apply pagination                      │
│  - Cache results                         │
└──────┬───────────────────────────────────┘
       │
       │ 8. Return SearchResults
       ↓
┌─────────────┐
│   Frontend  │
│   Renders   │
│   Groups    │
└─────────────┘
```

---

## Search Algorithm

### Relevance Scoring Logic

**Scoring Formula**:

```python
def calculate_relevance_score(result: SearchResult, query: str) -> float:
    """
    Calculate relevance score (0-100).

    Scoring components:
    - Exact match: +20
    - Field matches (weighted):
        - Filename: 10x
        - Title: 8x
        - Tags: 6x
        - Description: 4x
        - Metadata: 3x
    - Partial match bonus: +0-5 based on match position
    - Source boost: Local files +2
    - Popularity boost (external): log(likes + downloads) * 0.5
    - Recency boost: Up to +5 for recent files
    """
    score = 0.0
    query_lower = query.lower()

    # 1. Exact match bonus
    if query_lower == result.title.lower():
        score += 20

    # 2. Field matches
    if result.result_type == ResultType.FILE:
        # Filename match
        if query_lower in result.title.lower():
            score += 10
            # Position bonus (earlier = better)
            pos = result.title.lower().index(query_lower)
            score += max(0, 5 - pos / 10)

    elif result.result_type == ResultType.IDEA:
        # Title match
        if query_lower in result.title.lower():
            score += 8

        # Description match
        if result.description and query_lower in result.description.lower():
            score += 4

    elif result.result_type == ResultType.EXTERNAL_MODEL:
        # Title match
        if query_lower in result.title.lower():
            score += 8

        # Popularity boost
        if result.likes_count and result.downloads_count:
            popularity = math.log10(result.likes_count + result.downloads_count + 1)
            score += popularity * 0.5

    # 3. Tag matches
    if result.metadata and 'tags' in result.metadata:
        for tag in result.metadata['tags']:
            if query_lower in tag.lower():
                score += 6
                if query_lower == tag.lower():
                    score += 3  # Exact tag match bonus

    # 4. Metadata matches (dimensions, materials, etc.)
    metadata_text = json.dumps(result.metadata).lower()
    if query_lower in metadata_text:
        score += 3

    # 5. Source boost (local files faster to access)
    if result.source == SearchSource.LOCAL_FILES:
        score += 2

    # 6. Recency boost (last 7 days)
    if result.created_at:
        days_old = (datetime.now() - result.created_at).days
        if days_old <= 7:
            score += max(0, 5 - days_old)

    return min(100, score)  # Cap at 100
```

---

### Filter Application

```python
def apply_filters(results: List[SearchResult], filters: SearchFilters) -> List[SearchResult]:
    """
    Apply advanced filters to search results.
    """
    filtered = results

    # File type filter
    if filters.file_types:
        filtered = [r for r in filtered if r.metadata.get('file_type') in filters.file_types]

    # Dimension filters
    if filters.min_width or filters.max_width:
        filtered = [r for r in filtered if
                   (filters.min_width is None or r.metadata.get('width', 0) >= filters.min_width) and
                   (filters.max_width is None or r.metadata.get('width', 999999) <= filters.max_width)]

    # Material filters
    if filters.material_types:
        filtered = [r for r in filtered if
                   any(mat in r.metadata.get('materials', []) for mat in filters.material_types)]

    # Print time filter
    if filters.min_print_time or filters.max_print_time:
        filtered = [r for r in filtered if
                   (filters.min_print_time is None or r.print_time_minutes >= filters.min_print_time) and
                   (filters.max_print_time is None or r.print_time_minutes <= filters.max_print_time)]

    # Cost filter
    if filters.min_cost or filters.max_cost:
        filtered = [r for r in filtered if
                   (filters.min_cost is None or r.cost_eur >= filters.min_cost) and
                   (filters.max_cost is None or r.cost_eur <= filters.max_cost)]

    # Printer compatibility
    if filters.printer_models:
        filtered = [r for r in filtered if
                   any(printer in r.metadata.get('compatible_printers', [])
                       for printer in filters.printer_models)]

    # Business filter
    if filters.is_business is not None:
        filtered = [r for r in filtered if r.metadata.get('is_business') == filters.is_business]

    # Difficulty filter
    if filters.difficulty_levels:
        filtered = [r for r in filtered if
                   r.metadata.get('difficulty_level') in filters.difficulty_levels]

    return filtered
```

---

## Caching Strategy

### Implementation

**Location**: `src/services/search_service.py`

```python
import time
from typing import Dict, Optional

class SearchCache:
    """Three-layer caching for search results"""

    def __init__(self):
        # Layer 1: Search results (5 min TTL)
        self.results_cache: Dict[str, tuple[SearchResults, float]] = {}
        self.results_ttl = 300  # 5 minutes

        # Layer 2: External API responses (1 hour TTL)
        self.external_cache: Dict[str, tuple[List[SearchResult], float]] = {}
        self.external_ttl = 3600  # 1 hour

        # Layer 3: Metadata cache (no TTL, invalidate on update)
        self.metadata_cache: Dict[str, Dict] = {}

    def get_search_results(self, cache_key: str) -> Optional[SearchResults]:
        """Get cached search results"""
        if cache_key in self.results_cache:
            results, timestamp = self.results_cache[cache_key]
            if time.time() - timestamp < self.results_ttl:
                results.cached = True
                return results
            else:
                del self.results_cache[cache_key]
        return None

    def set_search_results(self, cache_key: str, results: SearchResults):
        """Cache search results"""
        self.results_cache[cache_key] = (results, time.time())

    def get_external_results(self, platform: str, query: str) -> Optional[List[SearchResult]]:
        """Get cached external platform results"""
        cache_key = f"{platform}:{query}"
        if cache_key in self.external_cache:
            results, timestamp = self.external_cache[cache_key]
            if time.time() - timestamp < self.external_ttl:
                return results
            else:
                del self.external_cache[cache_key]
        return None

    def set_external_results(self, platform: str, query: str, results: List[SearchResult]):
        """Cache external platform results"""
        cache_key = f"{platform}:{query}"
        self.external_cache[cache_key] = (results, time.time())

    def invalidate_file(self, file_id: str):
        """Invalidate caches when file is updated/deleted"""
        # Clear results cache (contains this file)
        self.results_cache.clear()

        # Clear metadata cache for this file
        if file_id in self.metadata_cache:
            del self.metadata_cache[file_id]

    def clear_all(self):
        """Clear all caches"""
        self.results_cache.clear()
        self.external_cache.clear()
        self.metadata_cache.clear()
```

---

## Error Handling

### Error Scenarios & Handling

| Error | Cause | Handling Strategy |
|-------|-------|-------------------|
| **External API Timeout** | Makerworld/Printables API slow | 5s timeout → Skip that source, continue with local |
| **External API Rate Limit** | Too many requests | Return cached results + warning toast |
| **External API Error** | 4xx/5xx status | Log error, skip source, show warning |
| **Network Error** | No internet connection | Show only local results, display offline mode banner |
| **Invalid Query** | Empty or too short (<2 chars) | Return validation error, suggest longer query |
| **Database Error** | SQLite locked or corrupted | Retry 3 times with exponential backoff, then error |
| **No Results** | Query matches nothing | Show "No results" + suggestions for similar searches |
| **Partial Results** | Some sources succeeded, some failed | Show available results + warning about failed sources |

---

### Error Response Format

```python
class SearchError(Exception):
    """Base search error"""
    pass

class ExternalAPIError(SearchError):
    """External API failed"""
    def __init__(self, platform: str, status_code: int, message: str):
        self.platform = platform
        self.status_code = status_code
        self.message = message

class RateLimitError(SearchError):
    """Rate limit exceeded"""
    def __init__(self, platform: str, retry_after: int):
        self.platform = platform
        self.retry_after = retry_after

# Error handling in SearchService
async def search_makerworld(self, query: str, limit: int) -> List[SearchResult]:
    try:
        client = MakerworldClient()
        results = await asyncio.wait_for(
            client.search(query, limit),
            timeout=5.0  # 5 second timeout
        )
        return results

    except asyncio.TimeoutError:
        logger.warning(f"Makerworld search timed out for query: {query}")
        # Return cached results if available
        cached = self.cache.get_external_results("makerworld", query)
        return cached or []

    except RateLimitError as e:
        logger.warning(f"Makerworld rate limit hit: {e.retry_after}s")
        # Return cached results
        cached = self.cache.get_external_results("makerworld", query)
        if cached:
            return cached
        raise  # Re-raise to notify user

    except ExternalAPIError as e:
        logger.error(f"Makerworld API error: {e.status_code} - {e.message}")
        return []  # Skip this source

    except Exception as e:
        logger.error(f"Unexpected error searching Makerworld: {e}")
        return []
```

---

## Implementation Details

### Phase A Implementation Steps

#### Backend (8-10 hours)

1. **Create Models** (`src/models/search.py`) - 1.5 hours
   - SearchSource, ResultType enums
   - SearchFilters, SearchResult, SearchResults dataclasses
   - Pydantic models for API validation

2. **Database Schema** - 1 hour
   - Create FTS5 tables (fts_files, fts_ideas)
   - Add triggers to keep FTS in sync
   - Create search_history and search_analytics tables
   - Migration script

3. **SearchService** (`src/services/search_service.py`) - 4 hours
   - Implement unified_search()
   - Implement search_local_files() using FTS5
   - Implement search_ideas() using FTS5
   - Implement calculate_relevance_score()
   - Implement merge_and_rank_results()
   - Add caching layer

4. **External Clients** (`src/integrations/external_search/`) - 2 hours
   - Base client class
   - MakerworldClient (leverage existing trending code)
   - PrintablesClient (leverage existing trending code)
   - Implement search() methods with caching

5. **API Router** (`src/api/routers/search.py`) - 1.5 hours
   - GET /api/v1/search endpoint
   - GET /api/v1/search/history endpoint
   - POST /api/v1/search/import endpoint
   - GET /api/v1/search/suggestions endpoint
   - Register router in main.py

6. **Testing** - 1 hour
   - Unit tests for SearchService
   - Integration tests for API endpoints
   - Test caching behavior

---

#### Frontend (6-8 hours)

1. **API Client** (`frontend/src/services/api/search.ts`) - 0.5 hours
   - TypeScript interfaces for search models
   - API client functions

2. **Global Search Bar** (`frontend/src/components/search/GlobalSearchBar.tsx`) - 2 hours
   - Search input with auto-complete
   - Search suggestions dropdown
   - Recent searches display
   - Keyboard shortcuts (Ctrl+K)

3. **Search Results Page** (`frontend/src/pages/SearchResults.tsx`) - 2 hours
   - Layout with sidebar filters
   - Grouped results display
   - Pagination
   - Loading states

4. **Result Cards** (`frontend/src/components/search/ResultCard.tsx`) - 1.5 hours
   - Local file card
   - Idea card
   - External model card
   - Action buttons (view, import, bookmark)

5. **Advanced Filters** (`frontend/src/components/search/AdvancedFilters.tsx`) - 1.5 hours
   - Filter form with all fields
   - Apply/reset functionality
   - Collapsible sections
   - Persist filter state

6. **Import Modal** (`frontend/src/components/search/ImportModal.tsx`) - 1 hour
   - Modal to import external models
   - Form for idea details
   - Integration with IdeaService

7. **Navigation Integration** - 0.5 hours
   - Add search bar to top navigation
   - Route configuration

---

### Configuration

**Location**: `.env` or `src/config.py`

```bash
# Search Configuration
SEARCH_ENABLE_EXTERNAL=true
SEARCH_CACHE_TTL_RESULTS=300        # 5 minutes
SEARCH_CACHE_TTL_EXTERNAL=3600      # 1 hour
SEARCH_EXTERNAL_TIMEOUT=5           # seconds
SEARCH_MAX_RESULTS_PER_SOURCE=50

# External Platform APIs
MAKERWORLD_API_KEY=optional_api_key
PRINTABLES_API_KEY=optional_api_key

# Rate Limiting
SEARCH_RATE_LIMIT_ENABLED=true
SEARCH_RATE_LIMIT_REQUESTS=60       # per minute
```

---

## Testing Strategy

### Unit Tests

**Location**: `tests/test_search_service.py`

```python
import pytest
from src.services.search_service import SearchService
from src.models.search import SearchFilters, SearchSource

@pytest.mark.asyncio
async def test_search_local_files():
    """Test local file search"""
    service = SearchService()
    results = await service.search_local_files("benchy", SearchFilters())
    assert len(results) > 0
    assert results[0].source == SearchSource.LOCAL_FILES

@pytest.mark.asyncio
async def test_relevance_scoring():
    """Test relevance score calculation"""
    service = SearchService()
    result = SearchResult(
        id="test",
        title="benchy.stl",
        source=SearchSource.LOCAL_FILES,
        result_type=ResultType.FILE
    )
    score = service.calculate_relevance_score(result, "benchy")
    assert score > 10  # Should have filename match

@pytest.mark.asyncio
async def test_unified_search_caching():
    """Test search result caching"""
    service = SearchService()

    # First search (cache miss)
    results1 = await service.unified_search("benchy", [SearchSource.LOCAL_FILES], SearchFilters())
    assert not results1.cached

    # Second search (cache hit)
    results2 = await service.unified_search("benchy", [SearchSource.LOCAL_FILES], SearchFilters())
    assert results2.cached

@pytest.mark.asyncio
async def test_filter_application():
    """Test advanced filters"""
    service = SearchService()
    filters = SearchFilters(
        material_types=["PLA"],
        min_cost=0.0,
        max_cost=1.0
    )
    results = await service.unified_search("", [SearchSource.LOCAL_FILES], filters)

    # All results should be PLA and cost <= 1.0 EUR
    for group in results.groups:
        for result in group.results:
            assert "PLA" in result.metadata.get("materials", [])
            assert result.cost_eur <= 1.0
```

---

### Integration Tests

**Location**: `tests/integration/test_search_api.py`

```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_search_endpoint():
    """Test unified search API endpoint"""
    response = client.get("/api/v1/search", params={"q": "benchy"})
    assert response.status_code == 200
    data = response.json()
    assert "groups" in data
    assert "total_results" in data
    assert len(data["groups"]) > 0

def test_search_with_filters():
    """Test search with advanced filters"""
    response = client.get("/api/v1/search", params={
        "q": "benchy",
        "material_types": "PLA,PETG",
        "min_width": 50,
        "max_width": 100
    })
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] >= 0

def test_search_history():
    """Test search history endpoint"""
    # Perform a search
    client.get("/api/v1/search", params={"q": "test"})

    # Get history
    response = client.get("/api/v1/search/history")
    assert response.status_code == 200
    history = response.json()
    assert len(history) > 0
    assert history[0]["query"] == "test"
```

---

### External API Mock Tests

**Location**: `tests/test_external_clients.py`

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.integrations.external_search.makerworld import MakerworldClient

@pytest.mark.asyncio
async def test_makerworld_search():
    """Test Makerworld search with mocked API"""
    mock_response = {
        "models": [
            {
                "id": "123",
                "name": "Test Model",
                "description": "Test description",
                "thumbnail_url": "http://example.com/thumb.jpg",
                "likes_count": 100,
                "downloads_count": 500
            }
        ]
    }

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value.status = 200
        mock_get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)

        client = MakerworldClient()
        results = await client.search("test", limit=10)

        assert len(results) == 1
        assert results[0].title == "Test Model"
        assert results[0].source == SearchSource.MAKERWORLD
```

---

## Future Phases

### Phase B: AI-Powered Search (4-6 weeks)

**Features**:
- Semantic search using embeddings
- Search by natural language ("small box for Raspberry Pi under €1")
- Image-based search (upload image, find similar models)
- Smart suggestions based on user history
- Auto-tagging using AI

**Tech Stack**:
- OpenAI/Anthropic embeddings API
- Vector database (ChromaDB or Pinecone)
- Image recognition (CLIP model)

---

### Phase C: Visual Similarity Search (3-4 weeks)

**Features**:
- Find models visually similar to a selected model
- Search by uploading a photo/screenshot
- 3D model shape matching
- Preview generation for all models

**Tech Stack**:
- PyVista for 3D preview generation
- CLIP or custom CNN for image similarity
- Vector similarity search

---

### Phase D: Community & Collaboration (6-8 weeks)

**Features**:
- Shared libraries (organization-level)
- Collaborative collections
- Model recommendations based on team usage
- Private model hosting
- Team analytics (most used models, cost tracking)

**Tech Stack**:
- Multi-tenant database architecture
- User authentication & authorization
- S3-compatible storage for shared files

---

## Open Questions

1. **External API Keys**: Do we need API keys for Makerworld/Printables search, or can we use public endpoints?
   - **Action**: Research API documentation and rate limits

2. **Rate Limiting**: What are the actual rate limits for external platforms?
   - **Action**: Test and document limits, implement adaptive rate limiting

3. **Search Analytics**: Should we track search queries for analytics/trending?
   - **Decision**: Yes, but make it opt-out for privacy

4. **Multi-Language Support**: Should search support non-English queries?
   - **Decision**: Phase B (requires embeddings/translation)

5. **Search Shortcuts**: What keyboard shortcuts should we support?
   - **Proposal**: Ctrl+K (Cmd+K) to open search, Esc to close, arrows to navigate

6. **Mobile UI**: How should search work on mobile/tablet?
   - **Decision**: Responsive design, collapsible filters

---

## Success Metrics

### KPIs for Phase A

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Search Response Time** | <500ms (cached), <2s (uncached) | Log search_time_ms |
| **Cache Hit Rate** | >60% | Track cache hits vs misses |
| **User Adoption** | >50% of users try search in first week | Usage analytics |
| **External API Success Rate** | >95% | Track failed vs successful API calls |
| **Search Satisfaction** | >80% find what they're looking for | Optional feedback prompt |

---

## Deployment Checklist

### Pre-Deployment

- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Database migration tested (rollback plan ready)
- [ ] External API credentials configured
- [ ] Rate limiting configured
- [ ] Caching tested (TTL behavior verified)
- [ ] Error handling tested (offline mode, API failures)
- [ ] Performance benchmarks meet targets
- [ ] Security review completed (SQL injection, XSS)
- [ ] Documentation updated (API docs, user guide)

### Post-Deployment

- [ ] Monitor error logs for first 24 hours
- [ ] Check external API rate limit usage
- [ ] Verify cache hit rates
- [ ] Monitor search response times
- [ ] Collect user feedback
- [ ] Fix any critical bugs within 48 hours

---

## Appendix: API Examples

### Example 1: Basic Search

**Request**:
```http
GET /api/v1/search?q=benchy&limit=20&page=1
```

**Response**:
```json
{
  "query": "benchy",
  "filters": {},
  "groups": [
    {
      "source": "local_files",
      "results": [
        {
          "id": "file_abc123",
          "source": "local_files",
          "result_type": "file",
          "title": "benchy.stl",
          "description": null,
          "thumbnail_url": "/api/v1/files/abc123/thumbnail",
          "relevance_score": 95.5,
          "match_highlights": ["filename"],
          "file_size": 2457600,
          "file_path": "/models/benchy.stl",
          "print_time_minutes": 120,
          "material_weight_grams": 35.2,
          "cost_eur": 0.45,
          "metadata": {
            "width": 60,
            "height": 45,
            "depth": 60,
            "materials": ["PLA"],
            "compatible_printers": ["Bambu A1"]
          },
          "created_at": "2025-11-01T10:30:00Z"
        }
      ],
      "total_count": 45,
      "has_more": true
    },
    {
      "source": "makerworld",
      "results": [
        {
          "id": "mw_xyz789",
          "source": "makerworld",
          "result_type": "external_model",
          "title": "3DBenchy - The jolly 3D printing torture-test",
          "description": "3DBenchy is a 3D model specifically designed for testing...",
          "thumbnail_url": "https://makerworld.com/...",
          "relevance_score": 88.2,
          "match_highlights": ["title"],
          "external_url": "https://makerworld.com/models/xyz789",
          "author": "CreativeTools",
          "likes_count": 12400,
          "downloads_count": 2100000,
          "metadata": {
            "tags": ["benchy", "torture-test", "calibration"],
            "category": "Tools",
            "license": "CC BY"
          },
          "created_at": "2024-01-15T08:00:00Z"
        }
      ],
      "total_count": 47,
      "has_more": true
    }
  ],
  "total_results": 127,
  "search_time_ms": 142,
  "page": 1,
  "limit": 20,
  "sources_searched": ["local_files", "ideas", "makerworld", "printables"],
  "sources_failed": [],
  "cached": false
}
```

---

### Example 2: Advanced Search with Filters

**Request**:
```http
GET /api/v1/search?q=box&material_types=PLA&min_width=50&max_width=100&min_cost=0&max_cost=1&printer_models=Bambu%20A1
```

**Response**:
```json
{
  "query": "box",
  "filters": {
    "material_types": ["PLA"],
    "min_width": 50,
    "max_width": 100,
    "min_cost": 0,
    "max_cost": 1,
    "printer_models": ["Bambu A1"]
  },
  "groups": [
    {
      "source": "local_files",
      "results": [
        {
          "id": "file_def456",
          "title": "storage_box_80mm.3mf",
          "relevance_score": 82.3,
          "metadata": {
            "width": 80,
            "height": 50,
            "depth": 80,
            "materials": ["PLA"],
            "material_weight": 42.5,
            "compatible_printers": ["Bambu A1"]
          },
          "cost_eur": 0.68,
          ...
        }
      ],
      "total_count": 18,
      "has_more": false
    }
  ],
  "total_results": 18,
  "search_time_ms": 89,
  "cached": false
}
```

---

### Example 3: Search History

**Request**:
```http
GET /api/v1/search/history?limit=10
```

**Response**:
```json
[
  {
    "id": "hist_001",
    "query": "benchy",
    "filters": null,
    "results_count": 127,
    "sources": ["local_files", "ideas", "makerworld", "printables"],
    "searched_at": "2025-11-06T14:30:00Z"
  },
  {
    "id": "hist_002",
    "query": "raspberry pi case",
    "filters": {
      "material_types": ["PLA"],
      "max_cost": 2.0
    },
    "results_count": 34,
    "sources": ["local_files", "makerworld"],
    "searched_at": "2025-11-06T13:15:00Z"
  }
]
```

---

### Example 4: Import External Model

**Request**:
```http
POST /api/v1/search/import
Content-Type: application/json

{
  "url": "https://makerworld.com/models/123456",
  "save_to_ideas": true
}
```

**Response**:
```json
{
  "id": "idea_new789",
  "title": "3DBenchy - Torture Test",
  "description": "Imported from Makerworld",
  "source_type": "external",
  "source_url": "https://makerworld.com/models/123456",
  "status": "planned",
  "category": "Testing",
  "tags": ["benchy", "torture-test", "imported"],
  "created_at": "2025-11-06T15:00:00Z"
}
```

---

## References

### Existing Code to Leverage

1. **Trending Service** (`src/api/routers/ideas.py:287-312`)
   - Already fetches trending from Makerworld/Printables
   - Has caching implemented
   - URL parsing logic

2. **Enhanced Metadata Extraction** (`src/services/file_service.py`)
   - Physical properties, print settings, materials, costs
   - All metadata available for search filters

3. **Database Utilities** (`src/database/database.py`)
   - Table creation, query methods
   - Can extend for FTS5 tables

4. **Event Service** (`src/services/event_service.py`)
   - Use for search analytics events
   - Track popular searches, imports

---

## Conclusion

This design document provides a comprehensive plan for implementing a unified cross-site search feature in Printernizer. The feature will:

✅ **Unify discovery** across local files, ideas, and external platforms
✅ **Leverage existing infrastructure** (metadata extraction, trending service)
✅ **Provide rich filtering** using enhanced metadata fields
✅ **Scale efficiently** with multi-layer caching and FTS5
✅ **Handle errors gracefully** with fallbacks and cached results
✅ **Deliver fast results** (<500ms cached, <2s uncached)

**Estimated Total Effort**: 12-16 hours (Phase A)
- Backend: 8-10 hours
- Frontend: 6-8 hours

**Next Steps**:
1. Review and approve design
2. Set up development branch
3. Implement backend (FTS5, SearchService, API router)
4. Implement frontend (search bar, results page, filters)
5. Test thoroughly (unit, integration, external API mocks)
6. Deploy and monitor

---

**Questions or feedback?** Please comment on this design document or reach out to discuss specific implementation details.
