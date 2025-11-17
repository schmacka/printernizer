"""
Trending repository for managing trending 3D model cache database operations.
"""
from typing import Optional, List, Dict, Any
import structlog

from .base_repository import BaseRepository

logger = structlog.get_logger()


class TrendingRepository(BaseRepository):
    """
    Repository for trending model cache database operations.

    This repository manages the trending_cache table which stores temporarily cached
    trending 3D models from external platforms (Thingiverse, Printables, etc.) to reduce
    API calls and improve performance.
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
