"""
Unit tests for SearchService.
Tests unified search, caching, filtering, and relevance scoring.

Sprint 2 Phase 2 - Feature Service Test Coverage.
"""
import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
import json

from src.services.search_service import SearchService, SearchCache
from src.models.search import SearchSource, SearchFilters, SearchResults, ResultType


class TestSearchCache:
    """Test SearchCache functionality."""

    def test_cache_initialization(self):
        """Test cache initializes with default TTLs."""
        cache = SearchCache()

        assert cache.results_ttl == 300  # 5 minutes
        assert cache.external_ttl == 3600  # 1 hour
        assert len(cache.results_cache) == 0
        assert len(cache.external_cache) == 0
        assert len(cache.metadata_cache) == 0

    def test_cache_custom_ttl(self):
        """Test cache with custom TTLs."""
        cache = SearchCache(results_ttl=60, external_ttl=600)

        assert cache.results_ttl == 60
        assert cache.external_ttl == 600

    def test_set_and_get_search_results(self):
        """Test setting and getting cached results."""
        cache = SearchCache()

        mock_results = MagicMock(spec=SearchResults)
        cache.set_search_results("test_key", mock_results)

        result = cache.get_search_results("test_key")

        assert result is mock_results
        assert result.cached is True

    def test_get_search_results_expired(self):
        """Test expired cache returns None."""
        cache = SearchCache(results_ttl=0)  # Expire immediately

        mock_results = MagicMock(spec=SearchResults)
        cache.set_search_results("test_key", mock_results)

        # Wait for expiry
        time.sleep(0.01)

        result = cache.get_search_results("test_key")

        assert result is None

    def test_get_search_results_not_found(self):
        """Test non-existent key returns None."""
        cache = SearchCache()

        result = cache.get_search_results("nonexistent")

        assert result is None

    def test_invalidate_file(self):
        """Test file invalidation clears caches."""
        cache = SearchCache()

        mock_results = MagicMock(spec=SearchResults)
        cache.set_search_results("test_key", mock_results)
        cache.metadata_cache["file_001"] = {"metadata": "data"}

        cache.invalidate_file("file_001")

        assert len(cache.results_cache) == 0
        assert "file_001" not in cache.metadata_cache

    def test_invalidate_idea(self):
        """Test idea invalidation clears results cache."""
        cache = SearchCache()

        mock_results = MagicMock(spec=SearchResults)
        cache.set_search_results("test_key", mock_results)

        cache.invalidate_idea("idea_001")

        assert len(cache.results_cache) == 0

    def test_clear_all(self):
        """Test clearing all caches."""
        cache = SearchCache()

        cache.set_search_results("key1", MagicMock(spec=SearchResults))
        cache.metadata_cache["file_001"] = {"data": "test"}
        cache.external_cache["external_key"] = ([], time.time())

        cache.clear_all()

        assert len(cache.results_cache) == 0
        assert len(cache.metadata_cache) == 0
        assert len(cache.external_cache) == 0


class TestSearchServiceInitialization:
    """Test SearchService initialization."""

    def test_initialization_with_database(self):
        """Test initialization with database."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()

        with patch('src.services.search_service.FileRepository'):
            with patch('src.services.search_service.LibraryRepository'):
                with patch('src.services.search_service.IdeaRepository'):
                    service = SearchService(mock_db)

        assert service.database is mock_db
        assert service.cache is not None
        assert service.file_service is None
        assert service.idea_service is None

    def test_initialization_with_optional_services(self):
        """Test initialization with optional services."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_file_service = MagicMock()
        mock_idea_service = MagicMock()

        with patch('src.services.search_service.FileRepository'):
            with patch('src.services.search_service.LibraryRepository'):
                with patch('src.services.search_service.IdeaRepository'):
                    service = SearchService(mock_db, mock_file_service, mock_idea_service)

        assert service.file_service is mock_file_service
        assert service.idea_service is mock_idea_service


class TestRelevanceScoring:
    """Test relevance score calculation."""

    def setup_method(self):
        """Set up service for testing."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()

        with patch('src.services.search_service.FileRepository'):
            with patch('src.services.search_service.LibraryRepository'):
                with patch('src.services.search_service.IdeaRepository'):
                    self.service = SearchService(mock_db)

    def test_exact_title_match_high_score(self):
        """Test exact title match gets high score."""
        score = self.service._calculate_relevance_score(
            title="benchy",
            description="A 3D print test",
            tags=[],
            metadata={},
            query="benchy",
            source=SearchSource.LOCAL_FILES
        )

        assert score >= 30  # Exact match + title match + source boost

    def test_partial_title_match(self):
        """Test partial title match."""
        score = self.service._calculate_relevance_score(
            title="benchy boat model",
            description="A 3D print test",
            tags=[],
            metadata={},
            query="benchy",
            source=SearchSource.LOCAL_FILES
        )

        assert score >= 10  # Title match + position bonus

    def test_tag_match_adds_score(self):
        """Test tag match adds to score."""
        score_with_tag = self.service._calculate_relevance_score(
            title="model",
            description="test",
            tags=["benchy", "3dprint"],
            metadata={},
            query="benchy",
            source=SearchSource.LOCAL_FILES
        )

        score_without_tag = self.service._calculate_relevance_score(
            title="model",
            description="test",
            tags=["other"],
            metadata={},
            query="benchy",
            source=SearchSource.LOCAL_FILES
        )

        assert score_with_tag > score_without_tag

    def test_description_match_adds_score(self):
        """Test description match adds to score."""
        score_with_desc = self.service._calculate_relevance_score(
            title="model",
            description="This is a benchy boat",
            tags=[],
            metadata={},
            query="benchy",
            source=SearchSource.LOCAL_FILES
        )

        score_without_desc = self.service._calculate_relevance_score(
            title="model",
            description="Something else",
            tags=[],
            metadata={},
            query="benchy",
            source=SearchSource.LOCAL_FILES
        )

        assert score_with_desc > score_without_desc

    def test_local_files_source_boost(self):
        """Test local files get source boost."""
        score_local = self.service._calculate_relevance_score(
            title="benchy",
            description="",
            tags=[],
            metadata={},
            query="benchy",
            source=SearchSource.LOCAL_FILES
        )

        score_ideas = self.service._calculate_relevance_score(
            title="benchy",
            description="",
            tags=[],
            metadata={},
            query="benchy",
            source=SearchSource.IDEAS
        )

        assert score_local > score_ideas

    def test_score_capped_at_100(self):
        """Test score is capped at 100."""
        score = self.service._calculate_relevance_score(
            title="benchy",
            description="benchy benchy benchy",
            tags=["benchy", "benchy_tag"],
            metadata={"key": "benchy"},
            query="benchy",
            source=SearchSource.LOCAL_FILES
        )

        assert score <= 100


class TestFilters:
    """Test search filter application."""

    def setup_method(self):
        """Set up service for testing."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()

        with patch('src.services.search_service.FileRepository'):
            with patch('src.services.search_service.LibraryRepository'):
                with patch('src.services.search_service.IdeaRepository'):
                    self.service = SearchService(mock_db)

    def test_filter_by_file_types(self):
        """Test filtering by file types."""
        results = [
            MagicMock(metadata={'file_type': '3mf'}, result_type=ResultType.FILE),
            MagicMock(metadata={'file_type': 'stl'}, result_type=ResultType.FILE),
            MagicMock(metadata={'file_type': 'gcode'}, result_type=ResultType.FILE),
        ]

        filters = SearchFilters(file_types=['3mf', 'stl'])
        filtered = self.service._apply_filters(results, filters)

        assert len(filtered) == 2

    def test_filter_by_business_flag(self):
        """Test filtering by business flag."""
        results = [
            MagicMock(metadata={'is_business': True}, result_type=ResultType.FILE),
            MagicMock(metadata={'is_business': False}, result_type=ResultType.FILE),
            MagicMock(metadata={'is_business': True}, result_type=ResultType.FILE),
        ]

        filters = SearchFilters(is_business=True)
        filtered = self.service._apply_filters(results, filters)

        assert len(filtered) == 2

    def test_filter_by_print_time_range(self):
        """Test filtering by print time range."""
        results = [
            MagicMock(metadata={}, print_time_minutes=30, result_type=ResultType.FILE),
            MagicMock(metadata={}, print_time_minutes=120, result_type=ResultType.FILE),
            MagicMock(metadata={}, print_time_minutes=240, result_type=ResultType.FILE),
        ]

        filters = SearchFilters(min_print_time=60, max_print_time=180)
        filtered = self.service._apply_filters(results, filters)

        assert len(filtered) == 1
        assert filtered[0].print_time_minutes == 120

    def test_filter_by_cost_range(self):
        """Test filtering by cost range."""
        results = [
            MagicMock(metadata={}, cost_eur=0.5, result_type=ResultType.FILE),
            MagicMock(metadata={}, cost_eur=2.5, result_type=ResultType.FILE),
            MagicMock(metadata={}, cost_eur=10.0, result_type=ResultType.FILE),
        ]

        filters = SearchFilters(min_cost=1.0, max_cost=5.0)
        filtered = self.service._apply_filters(results, filters)

        assert len(filtered) == 1
        assert filtered[0].cost_eur == 2.5

    def test_filter_by_created_date_range(self):
        """Test filtering by creation date range."""
        now = datetime.now()
        results = [
            MagicMock(metadata={}, created_at=now - timedelta(days=10), result_type=ResultType.FILE),
            MagicMock(metadata={}, created_at=now - timedelta(days=5), result_type=ResultType.FILE),
            MagicMock(metadata={}, created_at=now - timedelta(days=1), result_type=ResultType.FILE),
        ]

        filters = SearchFilters(
            created_after=now - timedelta(days=7),
            created_before=now - timedelta(days=2)
        )
        filtered = self.service._apply_filters(results, filters)

        assert len(filtered) == 1

    def test_filter_by_idea_status(self):
        """Test filtering by idea status."""
        results = [
            MagicMock(metadata={'status': 'considering'}, result_type=ResultType.IDEA),
            MagicMock(metadata={'status': 'printed'}, result_type=ResultType.IDEA),
            MagicMock(metadata={'status': 'rejected'}, result_type=ResultType.IDEA),
        ]

        filters = SearchFilters(idea_status=['considering', 'printed'])
        filtered = self.service._apply_filters(results, filters)

        assert len(filtered) == 2

    def test_empty_filters_returns_all(self):
        """Test empty filters returns all results."""
        results = [MagicMock(metadata={}, result_type=ResultType.FILE) for _ in range(5)]

        filters = SearchFilters()
        filtered = self.service._apply_filters(results, filters)

        assert len(filtered) == 5


class TestHelperMethods:
    """Test helper methods."""

    def setup_method(self):
        """Set up service for testing."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()

        with patch('src.services.search_service.FileRepository'):
            with patch('src.services.search_service.LibraryRepository'):
                with patch('src.services.search_service.IdeaRepository'):
                    self.service = SearchService(mock_db)

    def test_check_range_filter_within_range(self):
        """Test range filter passes for value in range."""
        result = self.service._check_range_filter(50, min_val=10, max_val=100)
        assert result is True

    def test_check_range_filter_below_min(self):
        """Test range filter fails for value below min."""
        result = self.service._check_range_filter(5, min_val=10, max_val=100)
        assert result is False

    def test_check_range_filter_above_max(self):
        """Test range filter fails for value above max."""
        result = self.service._check_range_filter(150, min_val=10, max_val=100)
        assert result is False

    def test_check_range_filter_none_value(self):
        """Test range filter fails for None value."""
        result = self.service._check_range_filter(None, min_val=10, max_val=100)
        assert result is False

    def test_check_range_filter_no_min(self):
        """Test range filter without minimum."""
        result = self.service._check_range_filter(50, min_val=None, max_val=100)
        assert result is True

    def test_check_range_filter_no_max(self):
        """Test range filter without maximum."""
        result = self.service._check_range_filter(50, min_val=10, max_val=None)
        assert result is True

    def test_check_dimension_filter_valid(self):
        """Test dimension filter for valid value."""
        metadata = {'physical_properties': {'width': 50}}
        result = self.service._check_dimension_filter(metadata, 'width', 10, 100)
        assert result is True

    def test_check_dimension_filter_no_metadata(self):
        """Test dimension filter with no metadata."""
        result = self.service._check_dimension_filter(None, 'width', 10, 100)
        assert result is False

    def test_check_dimension_filter_missing_property(self):
        """Test dimension filter with missing property."""
        metadata = {'physical_properties': {}}
        result = self.service._check_dimension_filter(metadata, 'width', 10, 100)
        assert result is False

    def test_check_material_filter_match(self):
        """Test material filter finds match."""
        metadata = {'material_requirements': {'material_types': ['PLA', 'PETG']}}
        result = self.service._check_material_filter(metadata, ['PLA'])
        assert result is True

    def test_check_material_filter_no_match(self):
        """Test material filter no match."""
        metadata = {'material_requirements': {'material_types': ['PLA']}}
        result = self.service._check_material_filter(metadata, ['ABS'])
        assert result is False

    def test_check_material_filter_no_metadata(self):
        """Test material filter with no metadata."""
        result = self.service._check_material_filter(None, ['PLA'])
        assert result is False

    def test_parse_datetime_valid(self):
        """Test parsing valid datetime string."""
        dt = self.service._parse_datetime("2025-01-15T10:30:00")
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 1

    def test_parse_datetime_with_z(self):
        """Test parsing datetime with Z suffix."""
        dt = self.service._parse_datetime("2025-01-15T10:30:00Z")
        assert dt is not None

    def test_parse_datetime_none(self):
        """Test parsing None returns None."""
        dt = self.service._parse_datetime(None)
        assert dt is None

    def test_parse_datetime_invalid(self):
        """Test parsing invalid string returns None."""
        dt = self.service._parse_datetime("not a date")
        assert dt is None


class TestCacheKeyGeneration:
    """Test cache key generation."""

    def setup_method(self):
        """Set up service for testing."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()

        with patch('src.services.search_service.FileRepository'):
            with patch('src.services.search_service.LibraryRepository'):
                with patch('src.services.search_service.IdeaRepository'):
                    self.service = SearchService(mock_db)

    def test_same_params_same_key(self):
        """Test same parameters produce same key."""
        filters = SearchFilters()
        sources = [SearchSource.LOCAL_FILES]

        key1 = self.service._generate_cache_key("test", sources, filters, 50, 1)
        key2 = self.service._generate_cache_key("test", sources, filters, 50, 1)

        assert key1 == key2

    def test_different_query_different_key(self):
        """Test different queries produce different keys."""
        filters = SearchFilters()
        sources = [SearchSource.LOCAL_FILES]

        key1 = self.service._generate_cache_key("test1", sources, filters, 50, 1)
        key2 = self.service._generate_cache_key("test2", sources, filters, 50, 1)

        assert key1 != key2

    def test_different_sources_different_key(self):
        """Test different sources produce different keys."""
        filters = SearchFilters()

        key1 = self.service._generate_cache_key("test", [SearchSource.LOCAL_FILES], filters, 50, 1)
        key2 = self.service._generate_cache_key("test", [SearchSource.IDEAS], filters, 50, 1)

        assert key1 != key2

    def test_different_page_different_key(self):
        """Test different pages produce different keys."""
        filters = SearchFilters()
        sources = [SearchSource.LOCAL_FILES]

        key1 = self.service._generate_cache_key("test", sources, filters, 50, 1)
        key2 = self.service._generate_cache_key("test", sources, filters, 50, 2)

        assert key1 != key2


class TestUnifiedSearch:
    """Test unified search functionality."""

    @pytest.mark.asyncio
    async def test_unified_search_with_cache_hit(self):
        """Test unified search returns cached results."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()

        with patch('src.services.search_service.FileRepository'):
            with patch('src.services.search_service.LibraryRepository'):
                with patch('src.services.search_service.IdeaRepository'):
                    service = SearchService(mock_db)

        # Pre-populate cache
        mock_results = MagicMock(spec=SearchResults)
        mock_results.cached = False
        cache_key = service._generate_cache_key(
            "test", [SearchSource.LOCAL_FILES], SearchFilters(), 50, 1
        )
        service.cache.set_search_results(cache_key, mock_results)

        result = await service.unified_search(
            query="test",
            sources=[SearchSource.LOCAL_FILES],
            filters=SearchFilters(),
            limit=50,
            page=1
        )

        assert result is mock_results
        assert result.cached is True

    @pytest.mark.asyncio
    async def test_unified_search_local_files(self):
        """Test unified search for local files."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_db.search_files_fts = AsyncMock(return_value=[{'file_id': 'file_001'}])
        mock_db.add_search_history = AsyncMock()

        mock_file_repo = MagicMock()
        mock_file_repo.get = AsyncMock(return_value={
            'id': 'file_001',
            'filename': 'test.stl',
            'metadata': '{}'
        })

        with patch('src.services.search_service.FileRepository', return_value=mock_file_repo):
            with patch('src.services.search_service.LibraryRepository'):
                with patch('src.services.search_service.IdeaRepository'):
                    service = SearchService(mock_db)

        result = await service.unified_search(
            query="test",
            sources=[SearchSource.LOCAL_FILES],
            filters=SearchFilters(),
            limit=50,
            page=1
        )

        assert result.query == "test"
        assert SearchSource.LOCAL_FILES in result.sources_searched
        assert result.search_time_ms >= 0

    @pytest.mark.asyncio
    async def test_unified_search_handles_source_errors(self):
        """Test unified search handles source errors gracefully - doesn't crash."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_db.search_files_fts = AsyncMock(side_effect=Exception("Database error"))
        mock_db.add_search_history = AsyncMock()

        with patch('src.services.search_service.FileRepository'):
            with patch('src.services.search_service.LibraryRepository'):
                with patch('src.services.search_service.IdeaRepository'):
                    service = SearchService(mock_db)

        # The service should not crash on errors
        result = await service.unified_search(
            query="test",
            sources=[SearchSource.LOCAL_FILES],
            filters=SearchFilters(),
            limit=50,
            page=1
        )

        # Verify search completed (graceful error handling)
        assert result is not None
        assert result.query == "test"
        # The error is logged and results are empty, but search completes
        assert result.total_results == 0


class TestSearchHistory:
    """Test search history functionality."""

    @pytest.mark.asyncio
    async def test_get_search_history(self):
        """Test getting search history."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_db.get_search_history = AsyncMock(return_value=[
            {
                'id': 'search_001',
                'query': 'benchy',
                'results_count': 10,
                'sources': ['local_files'],
                'searched_at': '2025-01-15T10:00:00'
            }
        ])

        with patch('src.services.search_service.FileRepository'):
            with patch('src.services.search_service.LibraryRepository'):
                with patch('src.services.search_service.IdeaRepository'):
                    service = SearchService(mock_db)

        history = await service.get_search_history(limit=20)

        assert len(history) == 1
        assert history[0].query == 'benchy'
        assert history[0].results_count == 10

    @pytest.mark.asyncio
    async def test_get_search_history_handles_errors(self):
        """Test search history handles errors gracefully."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_db.get_search_history = AsyncMock(side_effect=Exception("Database error"))

        with patch('src.services.search_service.FileRepository'):
            with patch('src.services.search_service.LibraryRepository'):
                with patch('src.services.search_service.IdeaRepository'):
                    service = SearchService(mock_db)

        history = await service.get_search_history()

        assert history == []

    @pytest.mark.asyncio
    async def test_delete_search_history(self):
        """Test deleting search history entry."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_db.delete_search_history = AsyncMock(return_value=True)

        with patch('src.services.search_service.FileRepository'):
            with patch('src.services.search_service.LibraryRepository'):
                with patch('src.services.search_service.IdeaRepository'):
                    service = SearchService(mock_db)

        result = await service.delete_search_history("search_001")

        assert result is True
        mock_db.delete_search_history.assert_called_once_with("search_001")


class TestSearchSuggestions:
    """Test search suggestions functionality."""

    @pytest.mark.asyncio
    async def test_get_search_suggestions(self):
        """Test getting search suggestions."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_db.get_search_history = AsyncMock(return_value=[
            {'query': 'benchy boat', 'results_count': 10},
            {'query': 'benchy model', 'results_count': 5},
            {'query': 'cube', 'results_count': 3}
        ])

        with patch('src.services.search_service.FileRepository'):
            with patch('src.services.search_service.LibraryRepository'):
                with patch('src.services.search_service.IdeaRepository'):
                    service = SearchService(mock_db)

        suggestions = await service.get_search_suggestions("bench", limit=10)

        # Should only return suggestions matching query
        assert len(suggestions) == 2
        assert all('bench' in s.text.lower() for s in suggestions)

    @pytest.mark.asyncio
    async def test_get_search_suggestions_sorted_by_relevance(self):
        """Test suggestions are sorted by relevance."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_db.get_search_history = AsyncMock(return_value=[
            {'query': 'benchy boat model', 'results_count': 10},
            {'query': 'benchy', 'results_count': 5}
        ])

        with patch('src.services.search_service.FileRepository'):
            with patch('src.services.search_service.LibraryRepository'):
                with patch('src.services.search_service.IdeaRepository'):
                    service = SearchService(mock_db)

        suggestions = await service.get_search_suggestions("benchy", limit=10)

        # Both should be returned and sorted (exact/prefix match first)
        assert len(suggestions) == 2
        # The one starting with 'benchy' exactly should have higher relevance
        relevance_values = [s.relevance for s in suggestions]
        assert relevance_values == sorted(relevance_values, reverse=True)

    @pytest.mark.asyncio
    async def test_get_search_suggestions_handles_errors(self):
        """Test suggestions handle errors gracefully."""
        mock_db = MagicMock()
        mock_db._connection = MagicMock()
        mock_db.get_search_history = AsyncMock(side_effect=Exception("Database error"))

        with patch('src.services.search_service.FileRepository'):
            with patch('src.services.search_service.LibraryRepository'):
                with patch('src.services.search_service.IdeaRepository'):
                    service = SearchService(mock_db)

        suggestions = await service.get_search_suggestions("test")

        assert suggestions == []
