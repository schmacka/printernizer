"""
Trending Discovery Service for Printernizer.
Fetches and caches trending 3D models from various platforms.
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import uuid4

import aiofiles
import aiohttp
import structlog
from bs4 import BeautifulSoup

from database.database import Database
from services.event_service import EventService


logger = structlog.get_logger(__name__)


class TrendingService:
    """Service for discovering and caching trending 3D models."""

    def __init__(self, db: Database, event_service: EventService):
        """Initialize trending service."""
        self.db = db
        self.event_service = event_service
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache_dir = Path("data/thumbnails/trending")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._refresh_task = None
        self._refresh_interval = 6 * 3600  # 6 hours in seconds

    async def initialize(self):
        """Initialize trending service and create tables."""
        try:
            await self._create_tables()
            await self._start_refresh_task()
            logger.info("Trending service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize trending service: {e}")
            raise

    async def _create_tables(self):
        """Create trending-related database tables."""
        async with self.db.get_connection() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS trending_cache (
                    id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    thumbnail_url TEXT,
                    thumbnail_local_path TEXT,
                    downloads INTEGER,
                    likes INTEGER,
                    creator TEXT,
                    category TEXT,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    metadata JSON,
                    UNIQUE(platform, model_id)
                )
            ''')

            # Create indexes
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_trending_platform ON trending_cache(platform)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_trending_expires ON trending_cache(expires_at)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_trending_category ON trending_cache(category)')

            await conn.commit()

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self.session is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self.session

    async def _start_refresh_task(self):
        """Start background task for periodic refresh."""
        if self._refresh_task is None:
            self._refresh_task = asyncio.create_task(self._refresh_loop())

    async def _refresh_loop(self):
        """Background loop for refreshing trending data."""
        while True:
            try:
                # Check if cache needs refresh
                if await self._needs_refresh():
                    await self.refresh_all_platforms()

                # Sleep for refresh interval
                await asyncio.sleep(self._refresh_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in refresh loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def _needs_refresh(self) -> bool:
        """Check if trending cache needs refresh."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute('''
                SELECT COUNT(*) as count, MIN(expires_at) as earliest_expiry
                FROM trending_cache
                WHERE expires_at > datetime('now')
            ''')
            row = await cursor.fetchone()

            if row['count'] == 0:
                return True  # No valid cache entries

            if row['earliest_expiry']:
                earliest = datetime.fromisoformat(row['earliest_expiry'])
                if earliest < datetime.now():
                    return True

        return False

    async def fetch_makerworld_trending(self) -> List[Dict[str, Any]]:
        """Fetch trending models from MakerWorld."""
        trending_items = []

        try:
            session = await self._get_session()

            # MakerWorld doesn't have a public API, so we'll scrape the trending page
            url = "https://makerworld.com/en/models?sort=trend"

            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')

                    # Parse model cards (structure may change)
                    model_cards = soup.find_all('div', class_='model-card', limit=50)

                    for card in model_cards:
                        try:
                            # Extract data from card
                            title_elem = card.find('h3', class_='model-title')
                            link_elem = card.find('a', href=True)
                            creator_elem = card.find('span', class_='creator-name')
                            downloads_elem = card.find('span', class_='download-count')

                            if title_elem and link_elem:
                                model_url = f"https://makerworld.com{link_elem['href']}"
                                model_id = self._extract_id_from_url(model_url, 'makerworld')

                                trending_items.append({
                                    'platform': 'makerworld',
                                    'model_id': model_id or str(uuid4()),
                                    'title': title_elem.text.strip(),
                                    'url': model_url,
                                    'creator': creator_elem.text.strip() if creator_elem else None,
                                    'downloads': self._parse_count(downloads_elem.text) if downloads_elem else 0,
                                    'category': 'general'
                                })
                        except Exception as e:
                            logger.warning(f"Failed to parse MakerWorld model card: {e}")

        except Exception as e:
            logger.error(f"Failed to fetch MakerWorld trending: {e}")

        return trending_items

    async def fetch_printables_trending(self) -> List[Dict[str, Any]]:
        """Fetch trending models from Printables."""
        trending_items = []

        try:
            session = await self._get_session()

            # Printables has a more structured page
            url = "https://www.printables.com/model?ordering=-popularity_score"

            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')

                    # Parse model listings
                    model_items = soup.find_all('div', class_='model-list-item', limit=50)

                    for item in model_items:
                        try:
                            title_elem = item.find('h3', class_='model-name')
                            link_elem = item.find('a', href=True)
                            creator_elem = item.find('a', class_='author-name')
                            likes_elem = item.find('span', class_='likes-count')
                            downloads_elem = item.find('span', class_='downloads-count')

                            if title_elem and link_elem:
                                model_url = f"https://www.printables.com{link_elem['href']}"
                                model_id = self._extract_id_from_url(model_url, 'printables')

                                trending_items.append({
                                    'platform': 'printables',
                                    'model_id': model_id or str(uuid4()),
                                    'title': title_elem.text.strip(),
                                    'url': model_url,
                                    'creator': creator_elem.text.strip() if creator_elem else None,
                                    'likes': self._parse_count(likes_elem.text) if likes_elem else 0,
                                    'downloads': self._parse_count(downloads_elem.text) if downloads_elem else 0,
                                    'category': 'general'
                                })
                        except Exception as e:
                            logger.warning(f"Failed to parse Printables model item: {e}")

        except Exception as e:
            logger.error(f"Failed to fetch Printables trending: {e}")

        return trending_items

    def _extract_id_from_url(self, url: str, platform: str) -> Optional[str]:
        """Extract model ID from URL."""
        import re

        if platform == 'makerworld':
            match = re.search(r'/models/(\d+)', url)
            return match.group(1) if match else None
        elif platform == 'printables':
            match = re.search(r'/model/(\d+)', url)
            return match.group(1) if match else None

        return None

    def _parse_count(self, text: str) -> int:
        """Parse count from text (handles K, M suffixes)."""
        if not text:
            return 0

        text = text.strip().upper()

        try:
            if 'K' in text:
                return int(float(text.replace('K', '')) * 1000)
            elif 'M' in text:
                return int(float(text.replace('M', '')) * 1000000)
            else:
                # Remove any non-numeric characters
                import re
                numbers = re.findall(r'\d+', text)
                return int(numbers[0]) if numbers else 0
        except:
            return 0

    async def save_trending_items(self, items: List[Dict[str, Any]], platform: str):
        """Save trending items to cache."""
        expires_at = datetime.now() + timedelta(hours=6)

        async with self.db.get_connection() as conn:
            for item in items:
                try:
                    cache_id = str(uuid4())

                    # Check if item already exists
                    cursor = await conn.execute('''
                        SELECT id FROM trending_cache
                        WHERE platform = ? AND model_id = ?
                    ''', (platform, item['model_id']))

                    existing = await cursor.fetchone()

                    if existing:
                        # Update existing entry
                        await conn.execute('''
                            UPDATE trending_cache
                            SET title = ?, url = ?, downloads = ?, likes = ?,
                                creator = ?, category = ?, cached_at = ?,
                                expires_at = ?, metadata = ?
                            WHERE platform = ? AND model_id = ?
                        ''', (
                            item['title'], item['url'],
                            item.get('downloads', 0), item.get('likes', 0),
                            item.get('creator'), item.get('category', 'general'),
                            datetime.now().isoformat(), expires_at.isoformat(),
                            json.dumps(item.get('metadata', {})),
                            platform, item['model_id']
                        ))
                    else:
                        # Insert new entry
                        await conn.execute('''
                            INSERT INTO trending_cache (
                                id, platform, model_id, title, url,
                                thumbnail_url, thumbnail_local_path,
                                downloads, likes, creator, category,
                                cached_at, expires_at, metadata
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            cache_id, platform, item['model_id'], item['title'],
                            item['url'], item.get('thumbnail_url'),
                            item.get('thumbnail_local_path'),
                            item.get('downloads', 0), item.get('likes', 0),
                            item.get('creator'), item.get('category', 'general'),
                            datetime.now().isoformat(), expires_at.isoformat(),
                            json.dumps(item.get('metadata', {}))
                        ))

                except Exception as e:
                    logger.warning(f"Failed to save trending item: {e}")

            await conn.commit()

    async def get_trending(self, platform: Optional[str] = None,
                          category: Optional[str] = None,
                          limit: int = 50) -> List[Dict[str, Any]]:
        """Get trending models from cache."""
        query = '''
            SELECT * FROM trending_cache
            WHERE expires_at > datetime('now')
        '''

        params = []

        if platform:
            query += ' AND platform = ?'
            params.append(platform)

        if category:
            query += ' AND category = ?'
            params.append(category)

        query += ' ORDER BY downloads DESC, likes DESC LIMIT ?'
        params.append(limit)

        async with self.db.get_connection() as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()

        return [dict(row) for row in rows]

    async def refresh_all_platforms(self):
        """Refresh trending data for all platforms."""
        logger.info("Starting trending refresh for all platforms")

        try:
            # Fetch from each platform
            makerworld_items = await self.fetch_makerworld_trending()
            printables_items = await self.fetch_printables_trending()

            # Save to cache
            if makerworld_items:
                await self.save_trending_items(makerworld_items, 'makerworld')
                logger.info(f"Cached {len(makerworld_items)} MakerWorld trending items")

            if printables_items:
                await self.save_trending_items(printables_items, 'printables')
                logger.info(f"Cached {len(printables_items)} Printables trending items")

            # Clean up expired entries
            await self.cleanup_expired()

            # Emit event
            await self.event_service.emit('trending_updated', {
                'platforms': ['makerworld', 'printables'],
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Failed to refresh trending data: {e}")

    async def cleanup_expired(self):
        """Remove expired cache entries."""
        async with self.db.get_connection() as conn:
            # Delete expired entries
            await conn.execute('''
                DELETE FROM trending_cache
                WHERE expires_at < datetime('now')
            ''')

            # Clean up orphaned thumbnails
            cursor = await conn.execute('SELECT thumbnail_local_path FROM trending_cache')
            valid_paths = {row['thumbnail_local_path'] for row in await cursor.fetchall()
                          if row['thumbnail_local_path']}

            # Remove thumbnails not in database
            for thumbnail_file in self.cache_dir.glob("*.jpg"):
                if str(thumbnail_file) not in valid_paths:
                    try:
                        thumbnail_file.unlink()
                    except:
                        pass

            await conn.commit()

    async def save_as_idea(self, trending_id: str, user_notes: Optional[str] = None) -> str:
        """Save a trending item as an idea."""
        async with self.db.get_connection() as conn:
            # Get trending item
            cursor = await conn.execute('''
                SELECT * FROM trending_cache WHERE id = ?
            ''', (trending_id,))

            item = await cursor.fetchone()
            if not item:
                raise ValueError(f"Trending item {trending_id} not found")

            # Create idea from trending item
            idea_id = str(uuid4())

            await conn.execute('''
                INSERT INTO ideas (
                    id, title, description, source_type, source_url,
                    thumbnail_path, category, priority, status,
                    is_business, created_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                idea_id, item['title'],
                user_notes or f"Trending model from {item['platform']}",
                item['platform'], item['url'],
                item['thumbnail_local_path'], 'trending',
                3, 'idea', False, datetime.now().isoformat(),
                json.dumps({
                    'creator': item['creator'],
                    'downloads': item['downloads'],
                    'likes': item['likes'],
                    'imported_from': 'trending',
                    'trending_id': trending_id
                })
            ))

            await conn.commit()

        # Emit event
        await self.event_service.emit('idea_created_from_trending', {
            'idea_id': idea_id,
            'trending_id': trending_id,
            'platform': item['platform']
        })

        return idea_id

    async def get_statistics(self) -> Dict[str, Any]:
        """Get trending cache statistics."""
        async with self.db.get_connection() as conn:
            # Total cached items
            cursor = await conn.execute('SELECT COUNT(*) as count FROM trending_cache')
            total = (await cursor.fetchone())['count']

            # Valid (non-expired) items
            cursor = await conn.execute('''
                SELECT COUNT(*) as count FROM trending_cache
                WHERE expires_at > datetime('now')
            ''')
            valid = (await cursor.fetchone())['count']

            # By platform
            cursor = await conn.execute('''
                SELECT platform, COUNT(*) as count
                FROM trending_cache
                WHERE expires_at > datetime('now')
                GROUP BY platform
            ''')
            by_platform = {row['platform']: row['count'] for row in await cursor.fetchall()}

            # Last refresh times
            cursor = await conn.execute('''
                SELECT platform, MAX(cached_at) as last_refresh
                FROM trending_cache
                GROUP BY platform
            ''')
            last_refresh = {row['platform']: row['last_refresh']
                          for row in await cursor.fetchall()}

        return {
            'total_cached': total,
            'valid_items': valid,
            'by_platform': by_platform,
            'last_refresh': last_refresh,
            'refresh_interval_hours': self._refresh_interval / 3600
        }

    async def cleanup(self):
        """Clean up trending service resources."""
        if self._refresh_task:
            self._refresh_task.cancel()

        if self.session:
            await self.session.close()

        logger.info("Trending service cleaned up")