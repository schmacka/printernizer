"""
Thumbnail caching service for Printernizer.
Manages downloading, caching, and serving of model thumbnails.
"""

import asyncio
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse

import aiofiles
import aiohttp
import structlog
from PIL import Image

from src.services.event_service import EventService


logger = structlog.get_logger(__name__)


class ThumbnailService:
    """Service for managing model thumbnails."""

    def __init__(self, event_service: EventService):
        """Initialize thumbnail service."""
        self.event_service = event_service
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache_dir = Path("data/thumbnails")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._max_size = (512, 512)  # Maximum thumbnail size
        self._quality = 85  # JPEG quality
        self._cache_duration = timedelta(days=30)  # Cache for 30 days

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session for downloading thumbnails.

        Returns:
            Configured aiohttp ClientSession instance.
        """
        if self.session is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self.session

    def _get_cache_path(self, url: str, source_type: str = "external") -> Path:
        """Generate cache file path for a URL."""
        # Create a hash of the URL for filename
        url_hash = hashlib.md5(url.encode()).hexdigest()

        # Extract file extension from URL if available
        parsed = urlparse(url)
        path_parts = parsed.path.split('.')
        if len(path_parts) > 1 and path_parts[-1].lower() in ['jpg', 'jpeg', 'png', 'webp']:
            original_ext = path_parts[-1].lower()
        else:
            original_ext = 'jpg'  # Default to jpg

        # Create subdirectory for source type
        source_dir = self.cache_dir / source_type
        source_dir.mkdir(exist_ok=True)

        return source_dir / f"{url_hash}.{original_ext}"

    async def download_thumbnail(self, url: str, source_type: str = "external",
                                force_refresh: bool = False) -> Optional[str]:
        """Download and cache a thumbnail from URL."""
        try:
            cache_path = self._get_cache_path(url, source_type)

            # Check if cached version exists and is fresh
            if not force_refresh and cache_path.exists():
                # Check if cache is still valid
                file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
                if file_age < self._cache_duration:
                    logger.debug(f"Using cached thumbnail: {cache_path}")
                    return str(cache_path)

            # Download the image
            session = await self._get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')

                    if not content_type.startswith('image/'):
                        logger.warning(f"URL does not point to an image: {url}")
                        return None

                    # Read image data
                    image_data = await response.read()

                    # Save and process the image
                    processed_path = await self._process_and_save_image(
                        image_data, cache_path, url
                    )

                    if processed_path:
                        logger.info(f"Downloaded and cached thumbnail: {url} -> {processed_path}")
                        return str(processed_path)

                else:
                    logger.warning(f"Failed to download thumbnail: {url} (status: {response.status})")

        except Exception as e:
            logger.error(f"Error downloading thumbnail from {url}: {e}")

        return None

    async def _process_and_save_image(self, image_data: bytes, cache_path: Path,
                                     original_url: str) -> Optional[Path]:
        """Process and save image data to cache."""
        try:
            # Create a temporary path for processing
            temp_path = cache_path.with_suffix('.tmp')

            # Save raw data first
            async with aiofiles.open(temp_path, 'wb') as f:
                await f.write(image_data)

            # Process image with PIL
            with Image.open(temp_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    # Create white background for transparency
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background

                # Resize if necessary
                if img.size[0] > self._max_size[0] or img.size[1] > self._max_size[1]:
                    img.thumbnail(self._max_size, Image.Resampling.LANCZOS)

                # Save as optimized JPEG
                final_path = cache_path.with_suffix('.jpg')
                img.save(final_path, 'JPEG', quality=self._quality, optimize=True)

            # Remove temporary file
            temp_path.unlink(missing_ok=True)

            # Emit event
            await self.event_service.emit_event('thumbnail_cached', {
                'url': original_url,
                'cache_path': str(final_path),
                'size': img.size,
                'file_size': final_path.stat().st_size
            })

            return final_path

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            # Clean up temporary file
            if 'temp_path' in locals():
                temp_path.unlink(missing_ok=True)
            return None

    async def get_thumbnail(self, url: str, source_type: str = "external",
                           auto_download: bool = True) -> Optional[str]:
        """Get thumbnail path, downloading if necessary."""
        cache_path = self._get_cache_path(url, source_type)

        # Check if already cached
        if cache_path.exists():
            return str(cache_path)

        # Try with .jpg extension
        jpg_path = cache_path.with_suffix('.jpg')
        if jpg_path.exists():
            return str(jpg_path)

        # Download if auto_download is enabled
        if auto_download:
            return await self.download_thumbnail(url, source_type)

        return None

    async def cache_multiple_thumbnails(self, url_list: list[Dict[str, str]],
                                      max_concurrent: int = 5) -> Dict[str, Optional[str]]:
        """Cache multiple thumbnails concurrently."""
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}

        async def download_single(item: Dict[str, str]) -> Tuple[str, Optional[str]]:
            async with semaphore:
                url = item['url']
                source_type = item.get('source_type', 'external')
                result = await self.download_thumbnail(url, source_type)
                return url, result

        # Create tasks for concurrent downloads
        tasks = [download_single(item) for item in url_list]

        # Execute all downloads
        completed = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in completed:
            if isinstance(result, Exception):
                logger.warning(f"Thumbnail download failed: {result}")
            else:
                url, path = result
                results[url] = path

        return results

    async def cleanup_expired(self) -> int:
        """Clean up expired thumbnail cache files."""
        removed_count = 0
        cutoff_time = datetime.now() - self._cache_duration

        try:
            for thumbnail_file in self.cache_dir.rglob("*"):
                if thumbnail_file.is_file():
                    file_time = datetime.fromtimestamp(thumbnail_file.stat().st_mtime)
                    if file_time < cutoff_time:
                        try:
                            thumbnail_file.unlink()
                            removed_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to remove expired thumbnail {thumbnail_file}: {e}")

            logger.info(f"Cleaned up {removed_count} expired thumbnails")

        except Exception as e:
            logger.error(f"Error during thumbnail cleanup: {e}")

        return removed_count

    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'by_source_type': {},
            'oldest_file': None,
            'newest_file': None
        }

        try:
            oldest_time = None
            newest_time = None
            total_size = 0

            for thumbnail_file in self.cache_dir.rglob("*"):
                if thumbnail_file.is_file():
                    stats['total_files'] += 1

                    # File size
                    file_size = thumbnail_file.stat().st_size
                    total_size += file_size

                    # Source type statistics
                    source_type = thumbnail_file.parent.name
                    if source_type not in stats['by_source_type']:
                        stats['by_source_type'][source_type] = {
                            'count': 0,
                            'size_mb': 0
                        }
                    stats['by_source_type'][source_type]['count'] += 1
                    stats['by_source_type'][source_type]['size_mb'] += file_size / (1024 * 1024)

                    # File times
                    file_time = datetime.fromtimestamp(thumbnail_file.stat().st_mtime)
                    if oldest_time is None or file_time < oldest_time:
                        oldest_time = file_time
                        stats['oldest_file'] = str(thumbnail_file)
                    if newest_time is None or file_time > newest_time:
                        newest_time = file_time
                        stats['newest_file'] = str(thumbnail_file)

            stats['total_size_mb'] = total_size / (1024 * 1024)

            # Round the sizes
            stats['total_size_mb'] = round(stats['total_size_mb'], 2)
            for source_stats in stats['by_source_type'].values():
                source_stats['size_mb'] = round(source_stats['size_mb'], 2)

        except Exception as e:
            logger.error(f"Error calculating cache statistics: {e}")

        return stats

    async def clear_cache(self, source_type: Optional[str] = None) -> int:
        """Clear thumbnail cache for all or specific source type."""
        removed_count = 0

        try:
            if source_type:
                # Clear specific source type
                source_dir = self.cache_dir / source_type
                if source_dir.exists():
                    for file in source_dir.iterdir():
                        if file.is_file():
                            file.unlink()
                            removed_count += 1
            else:
                # Clear all thumbnails
                for thumbnail_file in self.cache_dir.rglob("*"):
                    if thumbnail_file.is_file():
                        thumbnail_file.unlink()
                        removed_count += 1

            logger.info(f"Cleared {removed_count} thumbnails" +
                       (f" for {source_type}" if source_type else ""))

        except Exception as e:
            logger.error(f"Error clearing thumbnail cache: {e}")

        return removed_count

    async def cleanup(self) -> None:
        """Clean up thumbnail service resources."""
        if self.session:
            await self.session.close()
            self.session = None

        logger.info("Thumbnail service cleaned up")