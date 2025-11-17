"""
Search service for unified cross-site search.
Handles local file search, idea search, and external platform integration.
"""
import uuid
import time
import math
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog

from src.config.constants import file_url
from src.database.database import Database
from src.database.repositories import FileRepository, LibraryRepository, IdeaRepository
from src.models.search import (
    SearchSource, SearchFilters, SearchResult, SearchResultGroup,
    SearchResults, SearchHistoryEntry, ResultType, SearchSuggestion
)

logger = structlog.get_logger()


class SearchCache:
    """Three-layer caching system for search results."""

    def __init__(self, results_ttl: int = 300, external_ttl: int = 3600):
        """
        Initialize search cache.

        Args:
            results_ttl: TTL for search results in seconds (default: 5 minutes)
            external_ttl: TTL for external API results in seconds (default: 1 hour)
        """
        # Layer 1: Search results (5 min TTL)
        self.results_cache: Dict[str, tuple[SearchResults, float]] = {}
        self.results_ttl = results_ttl

        # Layer 2: External API responses (1 hour TTL)
        self.external_cache: Dict[str, tuple[List[SearchResult], float]] = {}
        self.external_ttl = external_ttl

        # Layer 3: Metadata cache (no TTL, invalidate on update)
        self.metadata_cache: Dict[str, Dict] = {}

    def get_search_results(self, cache_key: str) -> Optional[SearchResults]:
        """Get cached search results."""
        if cache_key in self.results_cache:
            results, timestamp = self.results_cache[cache_key]
            if time.time() - timestamp < self.results_ttl:
                # Mark as cached
                results.cached = True
                return results
            else:
                del self.results_cache[cache_key]
        return None

    def set_search_results(self, cache_key: str, results: SearchResults) -> None:
        """Cache search results."""
        self.results_cache[cache_key] = (results, time.time())

    def invalidate_file(self, file_id: str) -> None:
        """Invalidate caches when file is updated/deleted."""
        # Clear results cache (contains this file)
        self.results_cache.clear()

        # Clear metadata cache for this file
        if file_id in self.metadata_cache:
            del self.metadata_cache[file_id]

    def invalidate_idea(self, idea_id: str) -> None:
        """Invalidate caches when idea is updated/deleted."""
        # Clear results cache
        self.results_cache.clear()

    def clear_all(self) -> None:
        """Clear all caches."""
        self.results_cache.clear()
        self.external_cache.clear()
        self.metadata_cache.clear()


class SearchService:
    """Service for unified cross-site search."""

    def __init__(self, database: Database, file_service=None, idea_service=None):
        """
        Initialize search service.

        Args:
            database: Database instance
            file_service: FileService instance (optional)
            idea_service: IdeaService instance (optional)
        """
        self.database = database
        # Initialize repositories for domain-specific operations
        self.file_repo = FileRepository(database._connection)
        self.library_repo = LibraryRepository(database._connection)
        self.idea_repo = IdeaRepository(database._connection)
        self.file_service = file_service
        self.idea_service = idea_service
        self.cache = SearchCache()

    async def unified_search(
        self,
        query: str,
        sources: List[SearchSource],
        filters: SearchFilters,
        limit: int = 50,
        page: int = 1
    ) -> SearchResults:
        """
        Unified search across multiple sources.

        Args:
            query: Search query string
            sources: List of sources to search
            filters: Advanced filters
            limit: Results per page
            page: Page number

        Returns:
            SearchResults with grouped and ranked results
        """
        start_time = time.time()

        # Generate cache key
        cache_key = self._generate_cache_key(query, sources, filters, limit, page)

        # Check cache
        cached_results = self.cache.get_search_results(cache_key)
        if cached_results:
            logger.info("Search cache hit", query=query)
            return cached_results

        # Search each source
        groups = []
        sources_failed = []

        for source in sources:
            try:
                if source == SearchSource.LOCAL_FILES:
                    results = await self._search_local_files(query, filters, limit)
                    if results:
                        groups.append(SearchResultGroup(
                            source=source,
                            results=results[:limit],
                            total_count=len(results),
                            has_more=len(results) > limit
                        ))

                elif source == SearchSource.IDEAS:
                    results = await self._search_ideas(query, filters, limit)
                    if results:
                        groups.append(SearchResultGroup(
                            source=source,
                            results=results[:limit],
                            total_count=len(results),
                            has_more=len(results) > limit
                        ))

            except Exception as e:
                logger.error("Search failed for source", source=source, error=str(e))
                sources_failed.append(source.value)

        # Calculate totals
        total_results = sum(group.total_count for group in groups)

        # Build results
        search_time_ms = int((time.time() - start_time) * 1000)

        search_results = SearchResults(
            query=query,
            filters=filters,
            groups=groups,
            total_results=total_results,
            search_time_ms=search_time_ms,
            page=page,
            limit=limit,
            sources_searched=sources,
            sources_failed=sources_failed,
            cached=False
        )

        # Cache results
        self.cache.set_search_results(cache_key, search_results)

        # Add to search history
        await self._add_to_history(query, filters, total_results, sources)

        logger.info("Search completed", query=query, total_results=total_results,
                   search_time_ms=search_time_ms)

        return search_results

    async def _search_local_files(
        self,
        query: str,
        filters: SearchFilters,
        limit: int = 50
    ) -> List[SearchResult]:
        """Search local files using FTS5."""
        try:
            # Use FTS5 for full-text search
            fts_results = await self.database.search_files_fts(query, limit * 2)  # Get more for filtering

            if not fts_results:
                return []

            # Get full file data
            file_ids = [r['file_id'] for r in fts_results]
            files = []

            for file_id in file_ids:
                # Get file from database
                file_data = await self.file_repo.get(file_id)
                if file_data:
                    files.append(dict(file_data))

                # Also try library
                if not file_data:
                    file_data = await self.library_repo.get_file(file_id)
                    if file_data:
                        files.append(dict(file_data))

            # Convert to SearchResult objects
            search_results = []
            for file_data in files:
                result = self._file_to_search_result(file_data, query)
                search_results.append(result)

            # Apply filters
            filtered_results = self._apply_filters(search_results, filters)

            # Sort by relevance score
            filtered_results.sort(key=lambda x: x.relevance_score, reverse=True)

            return filtered_results

        except Exception as e:
            logger.error("Local file search failed", error=str(e), query=query)
            return []

    async def _search_ideas(
        self,
        query: str,
        filters: SearchFilters,
        limit: int = 50
    ) -> List[SearchResult]:
        """Search ideas using FTS5."""
        try:
            # Use FTS5 for full-text search
            fts_results = await self.database.search_ideas_fts(query, limit * 2)

            if not fts_results:
                return []

            # Get full idea data
            idea_ids = [r['idea_id'] for r in fts_results]
            ideas = []

            for idea_id in idea_ids:
                idea_data = await self.idea_repo.get(idea_id)
                if idea_data:
                    ideas.append(dict(idea_data))

            # Convert to SearchResult objects
            search_results = []
            for idea_data in ideas:
                result = self._idea_to_search_result(idea_data, query)
                search_results.append(result)

            # Apply filters
            filtered_results = self._apply_filters(search_results, filters)

            # Sort by relevance score
            filtered_results.sort(key=lambda x: x.relevance_score, reverse=True)

            return filtered_results

        except Exception as e:
            logger.error("Idea search failed", error=str(e), query=query)
            return []

    def _file_to_search_result(self, file_data: Dict[str, Any], query: str) -> SearchResult:
        """Convert file data to SearchResult."""
        # Parse metadata
        metadata = file_data.get('metadata', {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}

        # Extract enhanced metadata fields
        physical_props = metadata.get('physical_properties', {})
        material_reqs = metadata.get('material_requirements', {})
        cost_breakdown = metadata.get('cost_breakdown', {})
        print_settings = metadata.get('print_settings', {})

        # Calculate relevance score
        relevance_score = self._calculate_relevance_score(
            title=file_data.get('filename', ''),
            description=file_data.get('display_name', ''),
            tags=[],
            metadata=metadata,
            query=query,
            source=SearchSource.LOCAL_FILES
        )

        # Determine match highlights
        match_highlights = []
        query_lower = query.lower()
        if query_lower in file_data.get('filename', '').lower():
            match_highlights.append('filename')
        if file_data.get('display_name') and query_lower in file_data.get('display_name', '').lower():
            match_highlights.append('display_name')

        return SearchResult(
            id=file_data.get('id', ''),
            source=SearchSource.LOCAL_FILES,
            result_type=ResultType.FILE,
            title=file_data.get('filename', 'Unknown'),
            description=file_data.get('display_name'),
            thumbnail_url=file_url(file_data.get('id'), 'thumbnail') if file_data.get('id') else None,
            metadata=metadata,
            relevance_score=relevance_score,
            match_highlights=match_highlights,
            file_size=file_data.get('file_size'),
            file_path=file_data.get('file_path'),
            print_time_minutes=print_settings.get('estimated_time_minutes'),
            material_weight_grams=material_reqs.get('total_weight'),
            cost_eur=cost_breakdown.get('total_cost'),
            created_at=self._parse_datetime(file_data.get('created_at')),
            modified_at=self._parse_datetime(file_data.get('modified_time'))
        )

    def _idea_to_search_result(self, idea_data: Dict[str, Any], query: str) -> SearchResult:
        """Convert idea data to SearchResult."""
        # Parse metadata
        metadata = idea_data.get('metadata', {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}

        # Get tags
        tags = idea_data.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',')]

        # Calculate relevance score
        relevance_score = self._calculate_relevance_score(
            title=idea_data.get('title', ''),
            description=idea_data.get('description', ''),
            tags=tags,
            metadata=metadata,
            query=query,
            source=SearchSource.IDEAS
        )

        # Determine match highlights
        match_highlights = []
        query_lower = query.lower()
        if query_lower in idea_data.get('title', '').lower():
            match_highlights.append('title')
        if idea_data.get('description') and query_lower in idea_data.get('description', '').lower():
            match_highlights.append('description')
        if any(query_lower in tag.lower() for tag in tags):
            match_highlights.append('tags')

        return SearchResult(
            id=idea_data.get('id', ''),
            source=SearchSource.IDEAS,
            result_type=ResultType.IDEA,
            title=idea_data.get('title', 'Untitled'),
            description=idea_data.get('description'),
            thumbnail_url=idea_data.get('thumbnail_path'),
            metadata={
                'status': idea_data.get('status'),
                'category': idea_data.get('category'),
                'priority': idea_data.get('priority'),
                'is_business': idea_data.get('is_business'),
                'source_type': idea_data.get('source_type'),
                'tags': tags,
                **metadata
            },
            relevance_score=relevance_score,
            match_highlights=match_highlights,
            external_url=idea_data.get('source_url'),
            created_at=self._parse_datetime(idea_data.get('created_at')),
            modified_at=self._parse_datetime(idea_data.get('updated_at'))
        )

    def _calculate_relevance_score(
        self,
        title: str,
        description: Optional[str],
        tags: List[str],
        metadata: Dict[str, Any],
        query: str,
        source: SearchSource
    ) -> float:
        """
        Calculate relevance score for a search result.

        Scoring formula:
        - Exact match: +20
        - Title match: +10
        - Tag match: +6
        - Description match: +4
        - Metadata match: +3
        - Source boost (local): +2
        """
        score = 0.0
        query_lower = query.lower()

        # Exact match bonus
        if query_lower == title.lower():
            score += 20

        # Title match
        if query_lower in title.lower():
            score += 10
            # Position bonus (earlier = better)
            pos = title.lower().find(query_lower)
            score += max(0, 5 - pos / 10)

        # Description match
        if description and query_lower in description.lower():
            score += 4

        # Tag matches
        for tag in tags:
            if query_lower in tag.lower():
                score += 6
                if query_lower == tag.lower():
                    score += 3  # Exact tag match bonus

        # Metadata match
        metadata_text = json.dumps(metadata).lower()
        if query_lower in metadata_text:
            score += 3

        # Source boost (local files faster to access)
        if source == SearchSource.LOCAL_FILES:
            score += 2

        return min(100.0, score)  # Cap at 100

    def _apply_filters(
        self,
        results: List[SearchResult],
        filters: SearchFilters
    ) -> List[SearchResult]:
        """
        Apply advanced filters to search results.

        This function implements a sequential filtering pipeline that progressively
        narrows down search results. Each filter is applied in order, with each step
        reducing the result set further.

        Complexity: F-41 (Cyclomatic Complexity)
        - 10+ different filter types
        - Multiple conditional branches
        - Nested helper method calls
        - Null-safe metadata checking

        Design Rationale:
            Sequential filtering (not parallel) because:
            1. Early filters reduce data set for later filters (performance)
            2. Short-circuit evaluation stops processing eliminated results
            3. Simpler to debug and test than complex boolean expressions
            4. Order matters: cheap filters first, expensive filters last

        Performance Characteristics:
            - Worst case: O(n * m) where n=results, m=filters
            - Best case: O(n) if early filters eliminate most results
            - Average: O(n * 3-5) as most searches use 3-5 filters
            - Memory: O(n) for intermediate filtered lists

        Filter Application Order (optimized for performance):
            1. File type (fast dict lookup)
            2. Business flag (fast boolean check)
            3. Date range (fast datetime comparison)
            4. Idea status (fast enum check)
            5. Print time range (numeric comparison)
            6. Cost range (numeric comparison)
            7. Material types (list iteration)
            8. Dimensions (nested property access)

        Args:
            results: Search results from initial query (pre-filtered by search terms)
            filters: Filter criteria from user's advanced search options

        Returns:
            Filtered list of SearchResult objects matching ALL filter criteria

        Example:
            >>> results = [result1, result2, result3]  # 100 results
            >>> filters = SearchFilters(file_types=['3mf'], min_cost=5.0)
            >>> filtered = self._apply_filters(results, filters)
            >>> len(filtered)  # 23 results after filtering
            23
        """
        # Start with all results, progressively narrow down
        filtered = results

        # ==================== FILE TYPE FILTER ====================
        # Filter by file extension (.3mf, .stl, .gcode, etc.)
        # Fastest filter - simple dict lookup, should be first
        # Typical reduction: 30-50% (e.g., exclude .gcode files)
        if filters.file_types:
            filtered = [
                r for r in filtered
                if r.metadata and r.metadata.get('file_type') in filters.file_types
            ]

        # ==================== DIMENSION FILTERS ====================
        # Filter by physical model dimensions (width, height, depth)
        # Used to find models that fit specific printer build volumes
        # Example: "Models that fit on Bambu A1 (256x256x256mm)"

        # Width filter: X-axis dimension in millimeters
        # Common use: Exclude models wider than printer bed
        if filters.min_width or filters.max_width:
            filtered = [
                r for r in filtered
                if self._check_dimension_filter(
                    r.metadata, 'width', filters.min_width, filters.max_width
                )
            ]

        # Height filter: Z-axis dimension in millimeters
        # Common use: Exclude tall models that exceed printer height
        # Note: Height is most common limiting factor for consumer printers
        if filters.min_height or filters.max_height:
            filtered = [
                r for r in filtered
                if self._check_dimension_filter(
                    r.metadata, 'height', filters.min_height, filters.max_height
                )
            ]

        # ==================== MATERIAL TYPE FILTER ====================
        # Filter by filament material types (PLA, PETG, ABS, TPU, etc.)
        # Allows users to find models compatible with materials they have in stock
        # Supports multi-material models: match if ANY material matches filter
        # Example: Filter for "PLA" matches models using ["PLA"], ["PLA", "PETG"], etc.
        if filters.material_types:
            filtered = [
                r for r in filtered
                if self._check_material_filter(r.metadata, filters.material_types)
            ]

        # ==================== PRINT TIME FILTER ====================
        # Filter by estimated print time in minutes
        # Helps users find quick prints vs long prints
        # Common ranges:
        #   - Quick prints: < 60 minutes
        #   - Medium prints: 60-240 minutes (1-4 hours)
        #   - Long prints: > 240 minutes (4+ hours)
        #   - Overnight: > 480 minutes (8+ hours)
        if filters.min_print_time or filters.max_print_time:
            filtered = [
                r for r in filtered
                if self._check_range_filter(
                    r.print_time_minutes,
                    filters.min_print_time,
                    filters.max_print_time
                )
            ]

        # ==================== COST FILTER ====================
        # Filter by estimated material cost in EUR
        # Cost calculated from: filament_weight * material_cost_per_kg
        # Helps users find budget-friendly models or track expenses
        # Typical ranges:
        #   - Budget: < 1 EUR (small prints)
        #   - Medium: 1-5 EUR (standard models)
        #   - Expensive: > 5 EUR (large/complex models)
        if filters.min_cost or filters.max_cost:
            filtered = [
                r for r in filtered
                if self._check_range_filter(
                    r.cost_eur,
                    filters.min_cost,
                    filters.max_cost
                )
            ]

        # ==================== BUSINESS FILTER ====================
        # Filter for business orders vs personal/hobby prints
        # Critical for users running 3D printing businesses
        # Enables separate tracking of:
        #   - Business prints: customer orders, paid jobs
        #   - Personal prints: prototypes, samples, hobby projects
        # Used for tax reporting and business analytics
        if filters.is_business is not None:
            filtered = [
                r for r in filtered
                if r.metadata and r.metadata.get('is_business') == filters.is_business
            ]

        # ==================== IDEA STATUS FILTER ====================
        # Filter ideas by workflow status (considering, in_progress, printed, rejected)
        # Only applies to ResultType.IDEA entries (not files or jobs)
        # Enables workflow management: "Show me all models I'm considering printing"
        # Status transitions: considering → in_progress → printed
        #                    considering → rejected
        if filters.idea_status:
            filtered = [
                r for r in filtered
                if r.result_type == ResultType.IDEA and
                r.metadata and r.metadata.get('status') in filters.idea_status
            ]

        # ==================== DATE RANGE FILTERS ====================
        # Filter by creation/import date
        # Common use cases:
        #   - "Models added this week"
        #   - "Jobs from last month"
        #   - "Ideas created in Q1 2025"
        # Performance: Fast datetime comparison, typically eliminates 60-80% of results

        # Created after: Find recent additions
        # Example: created_after=datetime(2025, 1, 1) → only 2025 entries
        if filters.created_after:
            filtered = [
                r for r in filtered
                if r.created_at and r.created_at >= filters.created_after
            ]

        # Created before: Find historical entries
        # Example: created_before=datetime(2024, 12, 31) → only 2024 and earlier
        if filters.created_before:
            filtered = [
                r for r in filtered
                if r.created_at and r.created_at <= filters.created_before
            ]

        return filtered

    def _check_dimension_filter(
        self,
        metadata: Optional[Dict[str, Any]],
        dimension: str,
        min_val: Optional[float],
        max_val: Optional[float]
    ) -> bool:
        """Check if dimension is within filter range."""
        if not metadata:
            return False

        physical_props = metadata.get('physical_properties', {})
        value = physical_props.get(dimension)

        if value is None:
            return False

        if min_val is not None and value < min_val:
            return False
        if max_val is not None and value > max_val:
            return False

        return True

    def _check_material_filter(
        self,
        metadata: Optional[Dict[str, Any]],
        material_types: List[str]
    ) -> bool:
        """Check if material matches filter."""
        if not metadata:
            return False

        material_reqs = metadata.get('material_requirements', {})
        file_materials = material_reqs.get('material_types', [])

        if not file_materials:
            return False

        return any(mat in file_materials for mat in material_types)

    def _check_range_filter(
        self,
        value: Optional[float],
        min_val: Optional[float],
        max_val: Optional[float]
    ) -> bool:
        """Check if value is within range."""
        if value is None:
            return False

        if min_val is not None and value < min_val:
            return False
        if max_val is not None and value > max_val:
            return False

        return True

    def _generate_cache_key(
        self,
        query: str,
        sources: List[SearchSource],
        filters: SearchFilters,
        limit: int,
        page: int
    ) -> str:
        """Generate cache key for search parameters."""
        # Create a hash of the search parameters
        key_data = {
            'query': query,
            'sources': [s.value for s in sources],
            'filters': filters.dict(exclude_none=True),
            'limit': limit,
            'page': page
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def _add_to_history(
        self,
        query: str,
        filters: SearchFilters,
        results_count: int,
        sources: List[SearchSource]
    ):
        """Add search to history."""
        try:
            history_entry = {
                'id': str(uuid.uuid4()),
                'query': query,
                'filters': filters.dict(exclude_none=True),
                'results_count': results_count,
                'sources': [s.value for s in sources],
                'searched_at': datetime.now().isoformat()
            }
            await self.database.add_search_history(history_entry)
        except Exception as e:
            logger.error("Failed to add search to history", error=str(e))

    async def get_search_history(self, limit: int = 20) -> List[SearchHistoryEntry]:
        """Get recent search history."""
        try:
            history_data = await self.database.get_search_history(limit)
            return [
                SearchHistoryEntry(
                    id=entry['id'],
                    query=entry['query'],
                    filters=entry.get('filters'),
                    results_count=entry['results_count'],
                    sources=[SearchSource(s) for s in entry.get('sources', [])],
                    searched_at=self._parse_datetime(entry['searched_at'])
                )
                for entry in history_data
            ]
        except Exception as e:
            logger.error("Failed to get search history", error=str(e))
            return []

    async def delete_search_history(self, search_id: str) -> bool:
        """Delete a search history entry."""
        return await self.database.delete_search_history(search_id)

    async def get_search_suggestions(self, query: str, limit: int = 10) -> List[SearchSuggestion]:
        """
        Get search suggestions based on:
        - Search history
        - Popular searches
        - File/idea titles
        """
        suggestions = []

        try:
            # Get from search history
            history = await self.database.get_search_history(limit * 2)
            for entry in history:
                if query.lower() in entry['query'].lower():
                    suggestions.append(SearchSuggestion(
                        text=entry['query'],
                        source=None,
                        type='history',
                        relevance=0.9 if entry['query'].lower().startswith(query.lower()) else 0.7
                    ))

            # Sort by relevance and limit
            suggestions.sort(key=lambda x: x.relevance, reverse=True)
            return suggestions[:limit]

        except Exception as e:
            logger.error("Failed to get search suggestions", error=str(e))
            return []

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string."""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
