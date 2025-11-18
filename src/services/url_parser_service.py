"""
URL Parser service for extracting metadata from external platform URLs.
This service provides basic URL parsing without relying on APIs.
"""
import re
import urllib.parse
from typing import Optional, Dict, Any
from datetime import datetime
import structlog
import aiohttp
from bs4 import BeautifulSoup

logger = structlog.get_logger()


class UrlParserService:
    """Service for parsing URLs from external 3D printing platforms."""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self.session is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self.session

    async def close(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None

    def detect_platform(self, url: str) -> Optional[str]:
        """Detect the platform from URL."""
        url_lower = url.lower()

        if 'makerworld.com' in url_lower:
            return 'makerworld'
        elif 'printables.com' in url_lower:
            return 'printables'
        elif 'thingiverse.com' in url_lower:
            return 'thingiverse'
        elif 'myminifactory.com' in url_lower:
            return 'myminifactory'
        elif 'cults3d.com' in url_lower:
            return 'cults3d'

        return None

    def extract_model_id(self, url: str, platform: str) -> Optional[str]:
        """Extract model ID from URL based on platform."""
        try:
            if platform == 'makerworld':
                # MakerWorld URLs: https://makerworld.com/en/models/123456
                match = re.search(r'/models/(\d+)', url)
                return match.group(1) if match else None

            elif platform == 'printables':
                # Printables URLs: https://www.printables.com/model/123456-model-name
                match = re.search(r'/model/(\d+)', url)
                return match.group(1) if match else None

            elif platform == 'thingiverse':
                # Thingiverse URLs: https://www.thingiverse.com/thing:123456
                match = re.search(r'/thing:(\d+)', url)
                return match.group(1) if match else None

            elif platform == 'myminifactory':
                # MyMiniFactory URLs: https://www.myminifactory.com/object/3d-print-model-name-123456
                match = re.search(r'/object/3d-print-.*-(\d+)', url)
                return match.group(1) if match else None

            elif platform == 'cults3d':
                # Cults3D URLs: https://cults3d.com/en/3d-model/game/model-name
                # Model ID extraction is more complex for Cults3D, use URL path
                parsed = urllib.parse.urlparse(url)
                return parsed.path.split('/')[-1] if parsed.path else None

        except Exception as e:
            logger.warning("Failed to extract model ID", url=url, platform=platform, error=str(e))

        return None

    async def fetch_page_title(self, url: str) -> Optional[str]:
        """Fetch the page title from URL."""
        try:
            session = await self._get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')

                    title_tag = soup.find('title')
                    if title_tag:
                        title = title_tag.get_text().strip()
                        # Clean up common suffixes
                        title = self._clean_title(title)
                        return title

        except Exception as e:
            logger.warning("Failed to fetch page title", url=url, error=str(e))

        return None

    def _clean_title(self, title: str) -> str:
        """Clean up page title by removing platform-specific suffixes."""
        # Common patterns to remove
        patterns_to_remove = [
            r' - MakerWorld$',
            r' by .* - Printables\.com$',
            r' - Thingiverse$',
            r' by .* \| Download free STL model \| Printables\.com$',
            r' \| Free 3D model \| STL file$',
            r' \| 3D model \| Download STL$',
            r' \| Download free STL model \| Printables\.com$'
        ]

        cleaned_title = title
        for pattern in patterns_to_remove:
            cleaned_title = re.sub(pattern, '', cleaned_title, flags=re.IGNORECASE)

        return cleaned_title.strip()

    def extract_creator_from_title(self, title: str, platform: str) -> Optional[str]:
        """Extract creator name from page title if available."""
        try:
            if platform == 'printables':
                # "Model Name by CreatorName - Printables.com"
                match = re.search(r' by ([^-]+) -', title)
                return match.group(1).strip() if match else None

            # Add more platform-specific creator extraction patterns as needed

        except Exception as e:
            logger.warning("Failed to extract creator from title", title=title, error=str(e))

        return None

    async def parse_url(self, url: str) -> Dict[str, Any]:
        """Parse URL and extract available metadata."""
        try:
            # Validate URL
            parsed_url = urllib.parse.urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid URL format")

            # Detect platform
            platform = self.detect_platform(url)
            if not platform:
                # Generic external URL
                platform = 'external'

            # Extract model ID
            model_id = self.extract_model_id(url, platform) if platform != 'external' else None

            # Fetch page title
            page_title = await self.fetch_page_title(url)

            # Clean title and extract creator if possible
            title = page_title
            creator = None
            if page_title:
                title = self._clean_title(page_title)
                creator = self.extract_creator_from_title(page_title, platform)

            # Build metadata
            metadata = {
                'platform': platform,
                'url': url,
                'model_id': model_id,
                'title': title or f"Model from {platform.title()}",
                'creator': creator,
                'original_title': page_title,
                'parsed_at': datetime.now().isoformat(),
                'domain': parsed_url.netloc
            }

            logger.info("URL parsed successfully", url=url, platform=platform, title=title)
            return metadata

        except Exception as e:
            logger.error("Failed to parse URL", url=url, error=str(e))

            # Return minimal metadata on failure
            return {
                'platform': 'external',
                'url': url,
                'title': 'External Model',
                'error': str(e),
                'parsed_at': datetime.now().isoformat()
            }

    def get_platform_info(self, platform: str) -> Dict[str, Any]:
        """Get information about a specific platform."""
        platform_info = {
            'makerworld': {
                'name': 'MakerWorld',
                'website': 'https://makerworld.com',
                'description': 'Bambu Lab\'s official model sharing platform',
                'supports_api': False,
                'url_pattern': r'makerworld\.com/.*?/models/\d+'
            },
            'printables': {
                'name': 'Printables',
                'website': 'https://www.printables.com',
                'description': 'Prusa\'s model sharing platform',
                'supports_api': False,
                'url_pattern': r'printables\.com/model/\d+'
            },
            'thingiverse': {
                'name': 'Thingiverse',
                'website': 'https://www.thingiverse.com',
                'description': 'Popular 3D printing model repository',
                'supports_api': True,  # Thingiverse has an API
                'url_pattern': r'thingiverse\.com/thing:\d+'
            },
            'myminifactory': {
                'name': 'MyMiniFactory',
                'website': 'https://www.myminifactory.com',
                'description': 'High-quality 3D models platform',
                'supports_api': False,
                'url_pattern': r'myminifactory\.com/object/3d-print-.*-\d+'
            },
            'cults3d': {
                'name': 'Cults3D',
                'website': 'https://cults3d.com',
                'description': '3D models marketplace',
                'supports_api': False,
                'url_pattern': r'cults3d\.com/.*/3d-model/'
            }
        }

        return platform_info.get(platform, {
            'name': platform.title(),
            'supports_api': False
        })

    def validate_url(self, url: str) -> bool:
        """Validate if URL is from a supported platform."""
        try:
            parsed = urllib.parse.urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False

            platform = self.detect_platform(url)
            return platform is not None

        except (ValueError, TypeError, AttributeError):
            # Invalid URL format
            return False

    def get_supported_platforms(self) -> list[str]:
        """Get list of supported platforms."""
        return ['makerworld', 'printables', 'thingiverse', 'myminifactory', 'cults3d']