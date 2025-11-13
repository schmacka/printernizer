"""
Unit tests for Ideas service.
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.services.idea_service import IdeaService
from src.models.idea import Idea, TrendingItem
from tests.fixtures.ideas_fixtures import (
    create_sample_idea,
    create_sample_trending_item,
    IdeasTestFixtures
)


@pytest.fixture
def mock_database():
    """Create mock database for testing."""
    db = MagicMock()
    db.create_idea = AsyncMock(return_value=True)
    db.get_idea = AsyncMock()
    db.list_ideas = AsyncMock(return_value=[])
    db.update_idea = AsyncMock(return_value=True)
    db.delete_idea = AsyncMock(return_value=True)
    db.update_idea_status = AsyncMock(return_value=True)
    db.add_idea_tags = AsyncMock(return_value=True)
    db.remove_idea_tags = AsyncMock(return_value=True)
    db.get_idea_tags = AsyncMock(return_value=[])
    db.get_all_tags = AsyncMock(return_value=[])
    db.get_idea_statistics = AsyncMock(return_value={})
    db.upsert_trending = AsyncMock(return_value=True)
    db.get_trending = AsyncMock(return_value=[])
    db.clean_expired_trending = AsyncMock(return_value=True)
    return db


@pytest.fixture
def idea_service(mock_database):
    """Create IdeaService instance with mock database."""
    return IdeaService(mock_database)


class TestIdeaService:
    """Test cases for IdeaService."""

    @pytest.mark.asyncio
    async def test_create_idea_success(self, idea_service, mock_database):
        """Test successful idea creation."""
        idea_data = create_sample_idea(title="Test Idea")

        idea_id = await idea_service.create_idea(idea_data)

        assert idea_id is not None
        assert idea_id == idea_data['id']
        mock_database.create_idea.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_idea_with_tags(self, idea_service, mock_database):
        """Test idea creation with tags."""
        idea_data = create_sample_idea(
            title="Test Idea with Tags",
            tags=["prototype", "urgent"]
        )

        idea_id = await idea_service.create_idea(idea_data)

        assert idea_id is not None
        mock_database.create_idea.assert_called_once()
        mock_database.add_idea_tags.assert_called_once_with(idea_id, ["prototype", "urgent"])

    @pytest.mark.asyncio
    async def test_create_idea_missing_title(self, idea_service, mock_database):
        """Test idea creation with missing title."""
        idea_data = create_sample_idea()
        del idea_data['title']

        idea_id = await idea_service.create_idea(idea_data)

        assert idea_id is None
        mock_database.create_idea.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_idea_success(self, idea_service, mock_database):
        """Test successful idea retrieval."""
        idea_data = create_sample_idea(title="Retrieved Idea")
        mock_database.get_idea.return_value = idea_data
        mock_database.get_idea_tags.return_value = ["test", "prototype"]

        idea = await idea_service.get_idea(idea_data['id'])

        assert idea is not None
        assert isinstance(idea, Idea)
        assert idea.title == "Retrieved Idea"
        assert idea.tags == ["test", "prototype"]

    @pytest.mark.asyncio
    async def test_get_idea_not_found(self, idea_service, mock_database):
        """Test idea retrieval when not found."""
        mock_database.get_idea.return_value = None

        idea = await idea_service.get_idea("non-existent-id")

        assert idea is None

    @pytest.mark.asyncio
    async def test_list_ideas_with_filters(self, idea_service, mock_database):
        """Test listing ideas with filters."""
        sample_ideas = IdeasTestFixtures.get_sample_ideas()[:3]
        mock_database.list_ideas.return_value = sample_ideas
        mock_database.get_idea_tags.return_value = []

        filters = {'status': 'idea', 'is_business': False}
        result = await idea_service.list_ideas(filters, page=1, page_size=10)

        assert 'ideas' in result
        assert len(result['ideas']) == 3
        assert result['page'] == 1
        assert result['page_size'] == 10
        mock_database.list_ideas.assert_called_once_with(
            status='idea',
            is_business=False,
            category=None,
            source_type=None,
            limit=10,
            offset=0
        )

    @pytest.mark.asyncio
    async def test_update_idea_success(self, idea_service, mock_database):
        """Test successful idea update."""
        idea_id = str(uuid.uuid4())
        updates = {'title': 'Updated Title', 'priority': 5}

        success = await idea_service.update_idea(idea_id, updates)

        assert success is True
        mock_database.update_idea.assert_called_once_with(idea_id, updates)

    @pytest.mark.asyncio
    async def test_update_idea_with_tags(self, idea_service, mock_database):
        """Test idea update with tags."""
        idea_id = str(uuid.uuid4())
        updates = {'title': 'Updated Title', 'tags': ['new', 'tags']}
        mock_database.get_idea_tags.return_value = ['old', 'tags']

        success = await idea_service.update_idea(idea_id, updates)

        assert success is True
        mock_database.remove_idea_tags.assert_called_once_with(idea_id, ['old', 'tags'])
        mock_database.add_idea_tags.assert_called_once_with(idea_id, ['new', 'tags'])

    @pytest.mark.asyncio
    async def test_delete_idea_success(self, idea_service, mock_database):
        """Test successful idea deletion."""
        idea_id = str(uuid.uuid4())

        success = await idea_service.delete_idea(idea_id)

        assert success is True
        mock_database.delete_idea.assert_called_once_with(idea_id)

    @pytest.mark.asyncio
    async def test_update_idea_status(self, idea_service, mock_database):
        """Test idea status update."""
        idea_id = str(uuid.uuid4())
        new_status = 'completed'

        success = await idea_service.update_idea_status(idea_id, new_status)

        assert success is True
        mock_database.update_idea_status.assert_called_once_with(idea_id, new_status)

    @pytest.mark.asyncio
    async def test_get_statistics(self, idea_service, mock_database):
        """Test getting idea statistics."""
        expected_stats = {
            'total_ideas': 10,
            'idea_count': 5,
            'planned_count': 3,
            'completed_count': 2,
            'business_ideas': 4,
            'personal_ideas': 6
        }
        mock_database.get_idea_statistics.return_value = expected_stats

        stats = await idea_service.get_statistics()

        assert stats == expected_stats
        mock_database.get_idea_statistics.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_trending_success(self, idea_service, mock_database):
        """Test successful trending cache."""
        trending_items = IdeasTestFixtures.get_sample_trending_items()[:2]
        platform = "printables"

        success = await idea_service.cache_trending(platform, trending_items)

        assert success is True
        assert mock_database.upsert_trending.call_count == 2

    @pytest.mark.asyncio
    async def test_get_trending(self, idea_service, mock_database):
        """Test getting trending models."""
        trending_data = IdeasTestFixtures.get_sample_trending_items()
        mock_database.get_trending.return_value = trending_data

        result = await idea_service.get_trending(platform="printables")

        assert len(result) == len(trending_data)
        mock_database.get_trending.assert_called_once_with("printables", None)

    @pytest.mark.asyncio
    async def test_save_trending_as_idea(self, idea_service, mock_database):
        """Test saving trending item as idea."""
        trending_item = create_sample_trending_item()
        mock_database.get_trending.return_value = [trending_item]

        idea_id = await idea_service.save_trending_as_idea(trending_item['id'])

        assert idea_id is not None
        mock_database.create_idea.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_ideas(self, idea_service, mock_database):
        """Test searching ideas."""
        # Mock the list_ideas method to return sample data
        sample_ideas = [
            {
                'id': '1',
                'title': 'iPhone Case Design',
                'description': 'Custom case for iPhone',
                'tags': ['prototype', 'mobile']
            },
            {
                'id': '2',
                'title': 'Garden Tool Organizer',
                'description': 'Wall mounted organizer',
                'tags': ['functional', 'garden']
            },
            {
                'id': '3',
                'title': 'Phone Stand',
                'description': 'Adjustable phone stand',
                'tags': ['utility', 'mobile']
            }
        ]

        # Mock the list_ideas call that happens inside search_ideas
        idea_service.list_ideas = AsyncMock(return_value={'ideas': sample_ideas})

        # Test search by title
        results = await idea_service.search_ideas("iphone")
        assert len(results) == 1
        assert results[0]['title'] == 'iPhone Case Design'

        # Test search by description
        results = await idea_service.search_ideas("organizer")
        assert len(results) == 1
        assert results[0]['title'] == 'Garden Tool Organizer'

        # Test search by tag
        results = await idea_service.search_ideas("mobile")
        assert len(results) == 2

        # Test search with no matches
        results = await idea_service.search_ideas("nonexistent")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_trending(self, idea_service, mock_database):
        """Test cleanup of expired trending items."""
        success = await idea_service.cleanup_expired_trending()

        assert success is True
        mock_database.clean_expired_trending.assert_called_once()


class TestIdeaModel:
    """Test cases for Idea model."""

    def test_idea_creation_from_dict(self):
        """Test creating Idea from dictionary."""
        idea_data = create_sample_idea(title="Test Model Idea")
        idea = Idea.from_dict(idea_data)

        assert idea.title == "Test Model Idea"
        assert idea.priority == 3
        assert idea.status == "idea"
        assert idea.is_business is False

    def test_idea_to_dict(self):
        """Test converting Idea to dictionary."""
        idea_data = create_sample_idea(title="Test Dict Conversion")
        idea = Idea.from_dict(idea_data)
        result_dict = idea.to_dict()

        assert result_dict['title'] == "Test Dict Conversion"
        assert result_dict['priority'] == 3
        assert 'created_at' in result_dict

    def test_idea_validation_success(self):
        """Test successful idea validation."""
        idea_data = create_sample_idea(title="Valid Idea")
        idea = Idea.from_dict(idea_data)

        assert idea.validate() is True

    def test_idea_validation_missing_title(self):
        """Test idea validation with missing title."""
        idea_data = create_sample_idea()
        idea_data['title'] = ""
        idea = Idea.from_dict(idea_data)

        assert idea.validate() is False

    def test_idea_validation_invalid_priority(self):
        """Test idea validation with invalid priority."""
        idea_data = create_sample_idea(priority=6)
        idea = Idea.from_dict(idea_data)

        assert idea.validate() is False

    def test_idea_validation_invalid_status(self):
        """Test idea validation with invalid status."""
        idea_data = create_sample_idea(status="invalid_status")
        idea = Idea.from_dict(idea_data)

        assert idea.validate() is False

    def test_get_formatted_time(self):
        """Test formatted time display."""
        # Test hours and minutes
        idea = Idea.from_dict(create_sample_idea(estimated_print_time=150))
        assert idea.get_formatted_time() == "2h 30m"

        # Test minutes only
        idea = Idea.from_dict(create_sample_idea(estimated_print_time=45))
        assert idea.get_formatted_time() == "45m"

        # Test unknown time
        idea = Idea.from_dict(create_sample_idea(estimated_print_time=None))
        assert idea.get_formatted_time() == "Unknown"


class TestTrendingItemModel:
    """Test cases for TrendingItem model."""

    def test_trending_item_creation(self):
        """Test creating TrendingItem from dictionary."""
        trending_data = create_sample_trending_item(platform="printables")
        trending = TrendingItem.from_dict(trending_data)

        assert trending.platform == "printables"
        assert trending.title is not None
        assert trending.url is not None

    def test_trending_item_to_dict(self):
        """Test converting TrendingItem to dictionary."""
        trending_data = create_sample_trending_item()
        trending = TrendingItem.from_dict(trending_data)
        result_dict = trending.to_dict()

        assert 'platform' in result_dict
        assert 'title' in result_dict
        assert 'url' in result_dict

    def test_is_expired_false(self):
        """Test trending item that is not expired."""
        trending_data = create_sample_trending_item()  # Creates future expiry
        trending = TrendingItem.from_dict(trending_data)

        assert trending.is_expired() is False

    def test_is_expired_true(self):
        """Test trending item that is expired."""
        past_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        trending_data = create_sample_trending_item(
            expires_at=past_time.isoformat()
        )
        trending = TrendingItem.from_dict(trending_data)

        assert trending.is_expired() is True