"""
Trending repository for managing trending 3D model cache database operations.

This module provides data access methods for caching trending 3D models from external
platforms (Thingiverse, Printables, etc.). The cache reduces API calls, improves
performance, and provides a unified interface for browsing trending models across
multiple platforms.

Key Capabilities:
    - Trending model caching with expiration
    - Multi-platform support (Thingiverse, Printables, etc.)
    - Automatic expiration and cleanup
    - Thumbnail caching (URL and local path)
    - Popularity tracking (downloads, likes)
    - Category-based filtering
    - Platform statistics

Database Schema:
    The trending_cache table stores cached trending models:
    - id (TEXT PRIMARY KEY): Unique cache entry ID (platform_modelid)
    - platform (TEXT): Source platform ('thingiverse', 'printables', etc.)
    - model_id (TEXT): Model ID on the platform
    - title (TEXT): Model title
    - url (TEXT): URL to model page
    - thumbnail_url (TEXT): URL to thumbnail image
    - thumbnail_local_path (TEXT): Local cached thumbnail path
    - downloads (INTEGER): Number of downloads
    - likes (INTEGER): Number of likes/favorites
    - creator (TEXT): Model creator/author
    - category (TEXT): Model category
    - expires_at (DATETIME): When cache entry expires
    - cached_at (DATETIME): When entry was cached

    Indexes:
    - idx_trending_platform: Fast filtering by platform
    - idx_trending_expires: Fast expiration queries

Usage Examples:
    ```python
    from src.database.repositories import TrendingRepository
    from datetime import datetime, timedelta

    # Initialize
    trending_repo = TrendingRepository(db.connection)

    # Cache a trending model
    trending_data = {
        'id': 'thingiverse_12345',
        'platform': 'thingiverse',
        'model_id': '12345',
        'title': 'Articulated Dragon',
        'url': 'https://www.thingiverse.com/thing:12345',
        'thumbnail_url': 'https://cdn.thingiverse.com/renders/12345.jpg',
        'downloads': 15000,
        'likes': 2500,
        'creator': 'DesignerName',
        'category': 'Toys & Games',
        'expires_at': (datetime.now() + timedelta(hours=6)).isoformat()
    }
    await trending_repo.upsert(trending_data)

    # Get all trending models (not expired)
    all_trending = await trending_repo.list()

    # Get trending from specific platform
    thingiverse_trending = await trending_repo.list(platform='thingiverse')

    # Get trending by category
    toys_trending = await trending_repo.list(category='Toys & Games')

    # Get platform statistics
    stats = await trending_repo.count_by_platform()
    print(f"Thingiverse: {stats.get('thingiverse', 0)} models")
    print(f"Printables: {stats.get('printables', 0)} models")

    # Clean up expired entries (run periodically)
    await trending_repo.clean_expired()
    ```

Caching Strategy:
    - Models are cached for configurable duration (typically 6-24 hours)
    - Cache entries expire automatically via expires_at timestamp
    - expired entries are excluded from queries
    - Periodic cleanup removes expired entries from database
    - Upsert logic allows cache refresh without duplicates

Expiration Management:
    - expires_at field stores expiration timestamp
    - Queries automatically filter out expired entries
    - clean_expired() method removes old entries
    - Should be called periodically (e.g., hourly cron job)
    - Prevents database bloat from stale cache data

Multi-Platform Support:
    - Supports any platform with trending/popular models API
    - platform field distinguishes sources
    - Enables unified trending view across platforms
    - Platform-specific filtering available

Popularity Sorting:
    - Models sorted by likes DESC, then downloads DESC
    - Provides consistent popularity ranking
    - Cross-platform popularity comparison
    - Enables "most popular" features

Thumbnail Caching:
    - thumbnail_url stores original platform URL
    - thumbnail_local_path stores locally cached copy
    - Reduces external requests for images
    - Improves loading performance

Error Handling:
    - All database errors logged with context
    - Upsert (INSERT OR REPLACE) prevents duplicates
    - Retry logic inherited from BaseRepository
    - Failed cache updates don't break functionality

See Also:
    - src/services/trending_service.py - Trending model fetching
    - src/services/library_service.py - Model import from trending
    - src/api/routers/trending.py - Trending API endpoints
"""
from typing import Optional, List, Dict, Any
import structlog

from .base_repository import BaseRepository

logger = structlog.get_logger()


class TrendingRepository(BaseRepository):
    """
    Repository for trending model cache database operations.

    Manages the trending_cache table which stores temporarily cached trending 3D
    models from external platforms. Reduces API calls and improves performance by
    caching models with automatic expiration.

    Key Features:
        - Trending model caching with expiration
        - Multi-platform support (Thingiverse, Printables)
        - Automatic expiration and cleanup
        - Thumbnail caching (URL and local paths)
        - Popularity tracking and sorting
        - Platform statistics

    Thread Safety:
        Operations are atomic but the repository is not thread-safe.
        Use connection pooling for concurrent access.
    """

    async def upsert(self, trending_data: Dict[str, Any]) -> bool:
        """
        Insert or update trending cache entry.

        Args:
            trending_data: Dictionary containing trending model information
                Required: id, platform, model_id, title, url, expires_at
                Optional: thumbnail_url, thumbnail_local_path, downloads, likes,
                         creator, category

        Returns:
            True if upsert was successful, False otherwise
        """
        try:
            await self._execute_write(
                """INSERT OR REPLACE INTO trending_cache
                (id, platform, model_id, title, url, thumbnail_url, thumbnail_local_path,
                 downloads, likes, creator, category, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    trending_data['id'],
                    trending_data['platform'],
                    trending_data['model_id'],
                    trending_data['title'],
                    trending_data['url'],
                    trending_data.get('thumbnail_url'),
                    trending_data.get('thumbnail_local_path'),
                    trending_data.get('downloads'),
                    trending_data.get('likes'),
                    trending_data.get('creator'),
                    trending_data.get('category'),
                    trending_data['expires_at']
                )
            )
            logger.debug("Trending entry upserted",
                        platform=trending_data['platform'],
                        model_id=trending_data['model_id'],
                        title=trending_data['title'])
            return True

        except Exception as e:
            logger.error("Failed to upsert trending",
                        error=str(e),
                        trending_data=trending_data,
                        exc_info=True)
            return False

    async def list(self, platform: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get trending items from cache that haven't expired.

        Args:
            platform: Filter by platform (e.g., 'thingiverse', 'printables') (optional)
            category: Filter by category (optional)

        Returns:
            List of trending item dictionaries, ordered by popularity (likes, then downloads)
        """
        try:
            query = "SELECT * FROM trending_cache WHERE expires_at > datetime('now')"
            params = []

            if platform:
                query += " AND platform = ?"
                params.append(platform)
            if category:
                query += " AND category = ?"
                params.append(category)

            query += " ORDER BY likes DESC, downloads DESC"

            rows = await self._fetch_all(query, params)
            return [dict(r) for r in rows]

        except Exception as e:
            logger.error("Failed to get trending",
                        error=str(e),
                        platform=platform,
                        category=category,
                        exc_info=True)
            return []

    async def clean_expired(self) -> bool:
        """
        Remove expired trending cache entries.

        This should be called periodically to clean up old cached data that is
        past its expiration time.

        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            await self._execute_write(
                "DELETE FROM trending_cache WHERE expires_at < datetime('now')",
                ()
            )
            logger.info("Expired trending entries cleaned")
            return True

        except Exception as e:
            logger.error("Failed to clean expired trending",
                        error=str(e),
                        exc_info=True)
            return False

    async def get(self, trending_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single trending entry by ID.

        Args:
            trending_id: Trending entry ID

        Returns:
            Trending item dictionary or None if not found
        """
        try:
            result = await self._fetch_one(
                "SELECT * FROM trending_cache WHERE id = ?",
                [trending_id]
            )
            return dict(result) if result else None

        except Exception as e:
            logger.error("Failed to get trending entry",
                        error=str(e),
                        trending_id=trending_id,
                        exc_info=True)
            return None

    async def delete(self, trending_id: str) -> bool:
        """
        Delete a trending cache entry.

        Args:
            trending_id: Trending entry ID to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            await self._execute_write(
                "DELETE FROM trending_cache WHERE id = ?",
                (trending_id,)
            )
            logger.info("Trending entry deleted", trending_id=trending_id)
            return True

        except Exception as e:
            logger.error("Failed to delete trending entry",
                        error=str(e),
                        trending_id=trending_id,
                        exc_info=True)
            return False

    async def exists(self, trending_id: str) -> bool:
        """
        Check if a trending entry exists.

        Args:
            trending_id: Trending entry ID to check

        Returns:
            True if entry exists, False otherwise
        """
        try:
            result = await self._fetch_one(
                "SELECT 1 FROM trending_cache WHERE id = ?",
                [trending_id]
            )
            return result is not None

        except Exception as e:
            logger.error("Failed to check trending entry existence",
                        error=str(e),
                        trending_id=trending_id,
                        exc_info=True)
            return False

    async def count_by_platform(self) -> Dict[str, int]:
        """
        Get count of trending entries by platform.

        Returns:
            Dictionary mapping platform names to entry counts
        """
        try:
            rows = await self._fetch_all(
                """SELECT platform, COUNT(*) as count
                   FROM trending_cache
                   WHERE expires_at > datetime('now')
                   GROUP BY platform""",
                []
            )
            return {row['platform']: row['count'] for row in rows}

        except Exception as e:
            logger.error("Failed to count trending by platform",
                        error=str(e),
                        exc_info=True)
            return {}
