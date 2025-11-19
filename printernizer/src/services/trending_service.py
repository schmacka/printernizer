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

from src.config.constants import PollingIntervals
from src.database.database import Database
from src.services.event_service import EventService


logger = structlog.get_logger(__name__)


# Retry configuration
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds
RETRY_MAX_DELAY = 30.0  # seconds


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

        # Metrics tracking
        self._metrics = {
            "total_requests": 0,
            "failed_requests": 0,
            "successful_fetches": 0,
            "last_fetch_time": None,
            "last_error": None,
            "cache_hits": 0,
            "cache_misses": 0
        }

    async def initialize(self) -> None:
        """Initialize trending service and create tables."""
        try:
            await self._create_tables()
            await self._start_refresh_task()
            logger.info("Trending service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize trending service: {e}")
            raise

    async def _create_tables(self) -> None:
        """Create trending-related database tables."""
        async with self.db.connection() as conn:
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

    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry function with exponential backoff and header-specific error handling."""
        last_exception = None

        for attempt in range(MAX_RETRIES):
            try:
                return await func(*args, **kwargs)
            except aiohttp.ClientResponseError as e:
                last_exception = e
                # Handle HTTP 400 errors that might be header-related
                if e.status == 400 and "header" in str(e).lower():
                    logger.warning(f"Header-related HTTP 400 error: {e}")
                    if attempt < MAX_RETRIES - 1:
                        # Recreate session with fresh headers
                        await self._close_session()
                if attempt < MAX_RETRIES - 1:
                    delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
                    logger.warning(
                        f"HTTP error {e.status}, retrying in {delay}s",
                        attempt=attempt + 1,
                        max_retries=MAX_RETRIES,
                        status=e.status,
                        error=str(e)
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"HTTP request failed after {MAX_RETRIES} attempts", 
                               status=e.status, error=str(e))
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                error_msg = str(e).lower()
                # Check for header size related errors
                if any(term in error_msg for term in ['header', 'field', 'line too long', 'too large']):
                    logger.error(f"Header size error detected: {e}")
                    # Try to recreate session with even larger limits
                    await self._close_session()
                    
                if attempt < MAX_RETRIES - 1:
                    delay = min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)
                    logger.warning(
                        f"Request failed, retrying in {delay}s",
                        attempt=attempt + 1,
                        max_retries=MAX_RETRIES,
                        error=str(e)
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Request failed after {MAX_RETRIES} attempts", error=str(e))
            except Exception as e:
                # Don't retry on non-network errors
                logger.error(f"Non-retryable error occurred: {e}")
                raise

        raise last_exception

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with proper error handling."""
        if self.session is None or self.session.closed:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                timeout = aiohttp.ClientTimeout(total=45, connect=15, sock_read=30)
                # Significantly increase header size limits to handle large responses from Printables
                # Printables can send very large headers with session data, cookies, and tracking info
                connector = aiohttp.TCPConnector(
                    limit=50,  # Reduce concurrent connections
                    limit_per_host=10,  # Be more conservative per host
                    ttl_dns_cache=300,  # DNS cache for 5 minutes
                    force_close=False,  # Keep connections alive
                    enable_cleanup_closed=True,
                    keepalive_timeout=30  # Keep connections alive longer
                )
                self.session = aiohttp.ClientSession(
                    headers=headers,
                    timeout=timeout,
                    connector=connector,
                    max_line_size=65536,  # 64KB - 4x larger for long response lines
                    max_field_size=32768  # 32KB - 2x larger for header fields
                )
                logger.debug("HTTP session created successfully")
            except Exception as e:
                logger.error(f"Failed to create HTTP session: {e}")
                raise
        return self.session

    async def _close_session(self) -> None:
        """Close and recreate HTTP session for error recovery."""
        if self.session and not self.session.closed:
            try:
                await self.session.close()
                logger.debug("HTTP session closed for recreation")
            except Exception as e:
                logger.warning(f"Error closing HTTP session: {e}")
        self.session = None

    async def _start_refresh_task(self) -> None:
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
                await asyncio.sleep(PollingIntervals.TRENDING_SERVICE_RETRY)  # Wait a minute before retrying

    async def _needs_refresh(self) -> bool:
        """Check if trending cache needs refresh."""
        async with self.db.connection() as conn:
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

    async def _fetch_url(self, url: str) -> str:
        """Fetch URL content with retry logic, chunked reading, and metrics tracking."""
        self._metrics["total_requests"] += 1

        async def _fetch():
            session = await self._get_session()
            
            # Use chunked reading for large responses to avoid memory issues
            async with session.get(url, chunked=True) as response:
                response.raise_for_status()

                # Check content length and handle large responses appropriately
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
                    logger.warning(f"Large response detected: {content_length} bytes from {url}")

                # Read response in chunks to handle large content
                chunks = []
                total_size = 0
                max_size = 50 * 1024 * 1024  # 50MB limit

                async for chunk in response.content.iter_chunked(8192):  # 8KB chunks
                    total_size += len(chunk)
                    if total_size > max_size:
                        raise aiohttp.ClientPayloadError(f"Response too large: {total_size} bytes")
                    chunks.append(chunk)

                # Decode response - try to detect encoding from content-type header
                content = b''.join(chunks)
                encoding = 'utf-8'  # Default

                # Try to get encoding from content-type header
                content_type = response.headers.get('content-type', '')
                if 'charset=' in content_type.lower():
                    try:
                        encoding = content_type.lower().split('charset=')[1].split(';')[0].strip()
                    except (IndexError, ValueError, AttributeError) as e:
                        # Malformed content-type header, use default
                        logger.debug("Could not parse charset from content-type",
                                    content_type=content_type, error=str(e))

                try:
                    return content.decode(encoding)
                except (UnicodeDecodeError, LookupError):
                    # Fallback to utf-8 with error handling
                    return content.decode('utf-8', errors='replace')

        try:
            result = await self._retry_with_backoff(_fetch)
            self._metrics["successful_fetches"] += 1
            self._metrics["last_fetch_time"] = datetime.now().isoformat()
            return result
        except Exception as e:
            self._metrics["failed_requests"] += 1
            self._metrics["last_error"] = str(e)
            raise

    async def fetch_makerworld_trending(self) -> List[Dict[str, Any]]:
        """Fetch trending models from MakerWorld with retry logic."""
        trending_items = []

        try:
            # MakerWorld doesn't have a public API, so we'll scrape the trending page
            url = "https://makerworld.com/en/models?sort=trend"

            content = await self._fetch_url(url)
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

            logger.info(f"Successfully fetched {len(trending_items)} MakerWorld trending items")

        except Exception as e:
            logger.error(f"Failed to fetch MakerWorld trending: {e}", exc_info=True)

        return trending_items

    async def fetch_printables_trending(self) -> List[Dict[str, Any]]:
        """Fetch trending models from Printables with retry logic."""
        trending_items = []

        try:
            # Printables has a more structured page
            url = "https://www.printables.com/model?ordering=-popularity_score"

            content = await self._fetch_url(url)
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

            logger.info(f"Successfully fetched {len(trending_items)} Printables trending items")

        except Exception as e:
            logger.error(f"Failed to fetch Printables trending: {e}", exc_info=True)

        return trending_items

    def _extract_id_from_url(self, url: str, platform: str) -> Optional[str]:
        """Extract model ID from platform URL.

        Args:
            url: Model URL to parse.
            platform: Platform identifier (makerworld or printables).

        Returns:
            Extracted model ID string, or None if not found.
        """
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
        except (ValueError, TypeError, IndexError, AttributeError) as e:
            # Could not parse count string, return 0
            logger.debug("Could not parse count from text",
                        text=text, error=str(e))
            return 0

    async def save_trending_items(self, items: List[Dict[str, Any]], platform: str) -> None:
        """Save trending items to cache."""
        expires_at = datetime.now() + timedelta(hours=6)

        async with self.db.connection() as conn:
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

        async with self.db.connection() as conn:
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
            await self.event_service.emit_event('trending_updated', {
                'platforms': ['makerworld', 'printables'],
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Failed to refresh trending data: {e}")

    async def cleanup_expired(self):
        """Remove expired cache entries."""
        async with self.db.connection() as conn:
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
                    except (OSError, PermissionError) as e:
                        # Best effort cleanup - log and continue
                        logger.debug("Could not delete orphaned thumbnail",
                                    file=str(thumbnail_file), error=str(e))

            await conn.commit()

    async def save_as_idea(self, trending_id: str, user_notes: Optional[str] = None) -> str:
        """Save a trending item as an idea."""
        async with self.db.connection() as conn:
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
        await self.event_service.emit_event('idea_created_from_trending', {
            'idea_id': idea_id,
            'trending_id': trending_id,
            'platform': item['platform']
        })

        return idea_id

    async def get_statistics(self) -> Dict[str, Any]:
        """Get trending cache statistics with performance metrics."""
        async with self.db.connection() as conn:
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

        # Calculate success rate
        total_requests = self._metrics["total_requests"]
        success_rate = (
            (self._metrics["successful_fetches"] / total_requests * 100)
            if total_requests > 0 else 0
        )

        return {
            'total_cached': total,
            'valid_items': valid,
            'by_platform': by_platform,
            'last_refresh': last_refresh,
            'refresh_interval_hours': self._refresh_interval / 3600,
            'performance_metrics': {
                'total_requests': self._metrics["total_requests"],
                'successful_fetches': self._metrics["successful_fetches"],
                'failed_requests': self._metrics["failed_requests"],
                'success_rate': f"{success_rate:.2f}%",
                'last_fetch_time': self._metrics["last_fetch_time"],
                'last_error': self._metrics["last_error"],
                'cache_hits': self._metrics["cache_hits"],
                'cache_misses': self._metrics["cache_misses"]
            }
        }

    async def cleanup(self):
        """Clean up trending service resources."""
        if self._refresh_task:
            self._refresh_task.cancel()

        if self.session:
            await self.session.close()

        logger.info("Trending service cleaned up")