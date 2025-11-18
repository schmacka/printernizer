"""
Idea service for managing print ideas and external model bookmarks.
"""
import uuid
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import structlog

from src.database.database import Database
from src.database.repositories import IdeaRepository, TrendingRepository
from src.models.idea import Idea, TrendingItem
from src.services.url_parser_service import UrlParserService

logger = structlog.get_logger()


class IdeaService:
    """Service for managing ideas and trending models."""

    def __init__(self, db: Database, idea_repository: Optional[IdeaRepository] = None,
                 trending_repository: Optional[TrendingRepository] = None):
        self.db = db
        # Use provided repositories or create new ones from database connection
        self.idea_repo = idea_repository or IdeaRepository(db._connection)
        self.trending_repo = trending_repository or TrendingRepository(db._connection)
        self.url_parser = UrlParserService()

    async def create_idea(self, idea_data: Dict[str, Any]) -> Optional[str]:
        """Create a new idea."""
        try:
            # Generate ID if not provided
            if 'id' not in idea_data:
                idea_data['id'] = str(uuid.uuid4())

            # Validate required fields
            if not idea_data.get('title'):
                raise ValueError("Title is required")

            # Create idea object and validate
            idea = Idea.from_dict(idea_data)
            if not idea.validate():
                raise ValueError("Invalid idea data")

            # Prepare data for database
            db_data = idea.to_dict()

            # Handle metadata JSON serialization
            if db_data.get('metadata'):
                db_data['metadata'] = json.dumps(db_data['metadata'])

            # Create idea in database
            success = await self.idea_repo.create(db_data)
            if not success:
                raise RuntimeError("Failed to create idea in database")

            # Add tags if provided
            if idea_data.get('tags'):
                await self.idea_repo.add_tags(idea.id, idea_data['tags'])

            logger.info("Idea created", idea_id=idea.id, title=idea.title)
            return idea.id

        except Exception as e:
            logger.error("Failed to create idea", error=str(e))
            return None

    async def get_idea(self, idea_id: str) -> Optional[Idea]:
        """Get idea by ID."""
        try:
            # Get idea from database
            idea_data = await self.idea_repo.get(idea_id)
            if not idea_data:
                return None

            # Parse metadata JSON
            if idea_data.get('metadata'):
                try:
                    idea_data['metadata'] = json.loads(idea_data['metadata'])
                except (json.JSONDecodeError, TypeError):
                    idea_data['metadata'] = None

            # Get tags
            tags = await self.idea_repo.get_tags(idea_id)
            idea_data['tags'] = tags

            return Idea.from_dict(idea_data)

        except Exception as e:
            logger.error("Failed to get idea", idea_id=idea_id, error=str(e))
            return None

    async def list_ideas(self, filters: Optional[Dict[str, Any]] = None,
                        page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """List ideas with filtering and pagination."""
        try:
            filters = filters or {}
            offset = (page - 1) * page_size

            # Get ideas from database
            ideas_data = await self.idea_repo.list(
                status=filters.get('status'),
                is_business=filters.get('is_business'),
                category=filters.get('category'),
                source_type=filters.get('source_type'),
                limit=page_size,
                offset=offset
            )

            ideas = []
            for idea_data in ideas_data:
                # Parse metadata JSON
                if idea_data.get('metadata'):
                    try:
                        idea_data['metadata'] = json.loads(idea_data['metadata'])
                    except (json.JSONDecodeError, TypeError):
                        idea_data['metadata'] = None

                # Get tags for each idea
                tags = await self.idea_repo.get_tags(idea_data['id'])
                idea_data['tags'] = tags

                ideas.append(Idea.from_dict(idea_data))

            # Convert to dictionaries for API response
            ideas_dict = [idea.to_dict() for idea in ideas]

            return {
                'ideas': ideas_dict,
                'page': page,
                'page_size': page_size,
                'has_more': len(ideas_dict) == page_size
            }

        except Exception as e:
            logger.error("Failed to list ideas", error=str(e))
            return {'ideas': [], 'page': page, 'page_size': page_size, 'has_more': False}

    async def update_idea(self, idea_id: str, updates: Dict[str, Any]) -> bool:
        """Update an idea."""
        try:
            # Handle metadata serialization
            if 'metadata' in updates and updates['metadata']:
                updates['metadata'] = json.dumps(updates['metadata'])

            # Handle tags separately
            tags = updates.pop('tags', None)

            # Update idea in database
            success = await self.idea_repo.update(idea_id, updates)
            if not success:
                return False

            # Update tags if provided
            if tags is not None:
                # Remove existing tags and add new ones
                existing_tags = await self.idea_repo.get_tags(idea_id)
                if existing_tags:
                    await self.idea_repo.remove_tags(idea_id, existing_tags)
                if tags:
                    await self.idea_repo.add_tags(idea_id, tags)

            logger.info("Idea updated", idea_id=idea_id)
            return True

        except Exception as e:
            logger.error("Failed to update idea", idea_id=idea_id, error=str(e))
            return False

    async def delete_idea(self, idea_id: str) -> bool:
        """Delete an idea."""
        try:
            success = await self.idea_repo.delete(idea_id)
            if success:
                logger.info("Idea deleted", idea_id=idea_id)
            return success

        except Exception as e:
            logger.error("Failed to delete idea", idea_id=idea_id, error=str(e))
            return False

    async def update_idea_status(self, idea_id: str, status: str) -> bool:
        """Update idea status."""
        try:
            success = await self.idea_repo.update_status(idea_id, status)
            if success:
                logger.info("Idea status updated", idea_id=idea_id, status=status)
            return success

        except Exception as e:
            logger.error("Failed to update idea status", idea_id=idea_id, error=str(e))
            return False

    async def get_all_tags(self) -> List[Dict[str, Any]]:
        """Get all available tags with usage counts."""
        try:
            return await self.idea_repo.get_all_tags()
        except Exception as e:
            logger.error("Failed to get all tags", error=str(e))
            return []

    async def get_statistics(self) -> Dict[str, Any]:
        """Get idea statistics."""
        try:
            return await self.idea_repo.get_statistics()
        except Exception as e:
            logger.error("Failed to get idea statistics", error=str(e))
            return {}

    async def import_from_url(self, url: str, additional_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Import an idea from an external URL."""
        try:
            # Extract platform and metadata from URL
            metadata = await self._extract_url_metadata(url)
            if not metadata:
                raise ValueError("Unable to extract metadata from URL")

            # Create idea data
            idea_data = {
                'title': metadata.get('title', 'Imported Model'),
                'description': metadata.get('description'),
                'source_type': metadata.get('platform', 'manual'),
                'source_url': url,
                'thumbnail_path': metadata.get('thumbnail_path'),
                'metadata': metadata
            }

            # Add any additional data provided
            if additional_data:
                idea_data.update(additional_data)

            return await self.create_idea(idea_data)

        except Exception as e:
            logger.error("Failed to import from URL", url=url, error=str(e))
            return None

    async def _extract_url_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract metadata from external platform URLs."""
        try:
            return await self.url_parser.parse_url(url)
        except Exception as e:
            logger.error("Failed to extract URL metadata", url=url, error=str(e))
            return None

    # Trending Models Management
    async def cache_trending(self, platform: str, models: List[Dict[str, Any]],
                           cache_duration_hours: int = 6) -> bool:
        """Cache trending models from external platforms."""
        try:
            expires_at = datetime.now() + timedelta(hours=cache_duration_hours)

            for model in models:
                trending_data = {
                    'id': f"{platform}_{model.get('model_id', uuid.uuid4())}",
                    'platform': platform,
                    'model_id': str(model.get('model_id', uuid.uuid4())),
                    'title': model['title'],
                    'url': model['url'],
                    'thumbnail_url': model.get('thumbnail_url'),
                    'downloads': model.get('downloads'),
                    'likes': model.get('likes'),
                    'creator': model.get('creator'),
                    'category': model.get('category'),
                    'expires_at': expires_at.isoformat()
                }

                await self.trending_repo.upsert(trending_data)

            logger.info("Trending models cached", platform=platform, count=len(models))
            return True

        except Exception as e:
            logger.error("Failed to cache trending models", platform=platform, error=str(e))
            return False

    async def get_trending(self, platform: Optional[str] = None,
                          category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get trending models from cache."""
        try:
            trending_data = await self.trending_repo.list(platform, category)
            return [TrendingItem.from_dict(item).to_dict() for item in trending_data]

        except Exception as e:
            logger.error("Failed to get trending models", error=str(e))
            return []

    async def save_trending_as_idea(self, trending_id: str,
                                   additional_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Save a trending model as a personal idea."""
        try:
            # Get trending item
            trending_items = await self.trending_repo.list()
            trending_item = next((item for item in trending_items if item['id'] == trending_id), None)

            if not trending_item:
                raise ValueError("Trending item not found")

            # Create idea from trending item
            idea_data = {
                'title': trending_item['title'],
                'description': f"Saved from {trending_item['platform']}",
                'source_type': trending_item['platform'],
                'source_url': trending_item['url'],
                'thumbnail_path': trending_item.get('thumbnail_local_path'),
                'metadata': {
                    'original_trending_id': trending_id,
                    'platform_model_id': trending_item['model_id'],
                    'creator': trending_item.get('creator'),
                    'downloads': trending_item.get('downloads'),
                    'likes': trending_item.get('likes')
                }
            }

            # Add any additional data
            if additional_data:
                idea_data.update(additional_data)

            return await self.create_idea(idea_data)

        except Exception as e:
            logger.error("Failed to save trending as idea", trending_id=trending_id, error=str(e))
            return None

    async def cleanup_expired_trending(self) -> bool:
        """Clean up expired trending cache entries."""
        try:
            success = await self.trending_repo.clean_expired()
            if success:
                logger.info("Expired trending items cleaned up")
            return success

        except Exception as e:
            logger.error("Failed to cleanup expired trending", error=str(e))
            return False

    async def search_ideas(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search ideas by title and description."""
        try:
            # Get all ideas with filters
            all_ideas = await self.list_ideas(filters)
            ideas = all_ideas['ideas']

            # Simple text search (can be enhanced with full-text search later)
            query_lower = query.lower()
            filtered_ideas = []

            for idea in ideas:
                if (query_lower in idea['title'].lower() or
                    (idea.get('description') and query_lower in idea['description'].lower()) or
                    any(query_lower in tag.lower() for tag in idea.get('tags', []))):
                    filtered_ideas.append(idea)

            return filtered_ideas

        except Exception as e:
            logger.error("Failed to search ideas", query=query, error=str(e))
            return []