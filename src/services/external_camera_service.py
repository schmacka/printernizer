"""
External Camera Service.

Handles fetching frames from external webcam URLs (HTTP snapshots and RTSP streams).
Supports URL-embedded credentials for authentication.

Features:
- HTTP snapshot URL support (JPEG/PNG)
- RTSP stream frame extraction (server-side via ffmpeg)
- URL credential parsing and masking for logs
- Graceful error handling with timeouts
"""

import asyncio
import os
import tempfile
import subprocess
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlparse, urlunparse

import aiohttp
import structlog

logger = structlog.get_logger(__name__)


def mask_url_credentials(url: str) -> str:
    """
    Mask credentials in URL for safe logging.

    Args:
        url: URL that may contain embedded credentials

    Returns:
        URL with credentials replaced by ***:***

    Example:
        >>> mask_url_credentials("http://admin:secret@192.168.1.100/snap.jpg")
        'http://***:***@192.168.1.100/snap.jpg'
    """
    if not url:
        return url
    try:
        parsed = urlparse(url)
        if parsed.username:
            # Rebuild URL with masked credentials
            masked_netloc = f"***:***@{parsed.hostname}"
            if parsed.port:
                masked_netloc += f":{parsed.port}"
            return urlunparse((
                parsed.scheme,
                masked_netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
        return url
    except Exception:
        return url


def detect_url_type(url: str) -> str:
    """
    Detect URL type from scheme.

    Args:
        url: URL to analyze

    Returns:
        'http_snapshot' for HTTP/HTTPS URLs
        'rtsp' for RTSP/RTSPS URLs
        'unknown' for unsupported schemes
    """
    if not url:
        return 'unknown'
    try:
        parsed = urlparse(url)
        if parsed.scheme in ('http', 'https'):
            return 'http_snapshot'
        elif parsed.scheme in ('rtsp', 'rtsps'):
            return 'rtsp'
        return 'unknown'
    except Exception:
        return 'unknown'


class ExternalCameraService:
    """
    Service for fetching frames from external webcam URLs.

    Supports both HTTP snapshot endpoints and RTSP video streams.
    For RTSP, uses system ffmpeg to extract frames server-side.
    """

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._logger = logger.bind(service="external_camera")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with timeout configuration."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close the HTTP session and cleanup resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def fetch_snapshot(
        self,
        webcam_url: str,
        printer_id: str
    ) -> Tuple[Optional[bytes], str]:
        """
        Fetch a snapshot from an external webcam URL.

        Automatically detects URL type and uses appropriate method:
        - HTTP/HTTPS: Direct GET request for image
        - RTSP: Frame extraction via ffmpeg

        Args:
            webcam_url: External webcam URL (HTTP or RTSP)
            printer_id: Printer ID for logging context

        Returns:
            Tuple of (image_bytes, content_type) or (None, '') on failure
        """
        if not webcam_url:
            return None, ''

        url_type = detect_url_type(webcam_url)
        masked_url = mask_url_credentials(webcam_url)

        self._logger.debug(
            "Fetching external webcam snapshot",
            printer_id=printer_id,
            url_type=url_type,
            url=masked_url
        )

        if url_type == 'http_snapshot':
            return await self._fetch_http_snapshot(webcam_url, printer_id)
        elif url_type == 'rtsp':
            return await self._extract_rtsp_frame(webcam_url, printer_id)
        else:
            self._logger.warning(
                "Unsupported webcam URL scheme",
                printer_id=printer_id,
                url=masked_url
            )
            return None, ''

    async def _fetch_http_snapshot(
        self,
        url: str,
        printer_id: str
    ) -> Tuple[Optional[bytes], str]:
        """
        Fetch snapshot from HTTP/HTTPS URL.

        Args:
            url: HTTP snapshot URL
            printer_id: Printer ID for logging

        Returns:
            Tuple of (image_bytes, content_type) or (None, '') on failure
        """
        masked_url = mask_url_credentials(url)

        try:
            session = await self._get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    # Get content type from response or default to JPEG
                    content_type = response.content_type or 'image/jpeg'

                    # Normalize content type
                    if content_type.startswith('image/'):
                        pass  # Keep as is
                    elif 'jpeg' in content_type.lower() or 'jpg' in content_type.lower():
                        content_type = 'image/jpeg'
                    elif 'png' in content_type.lower():
                        content_type = 'image/png'
                    else:
                        content_type = 'image/jpeg'  # Default fallback

                    data = await response.read()

                    if len(data) == 0:
                        self._logger.warning(
                            "HTTP snapshot returned empty response",
                            printer_id=printer_id,
                            url=masked_url
                        )
                        return None, ''

                    self._logger.info(
                        "HTTP snapshot fetched successfully",
                        printer_id=printer_id,
                        size_bytes=len(data),
                        content_type=content_type
                    )
                    return data, content_type
                else:
                    self._logger.warning(
                        "HTTP snapshot request failed",
                        printer_id=printer_id,
                        status=response.status,
                        url=masked_url
                    )
                    return None, ''

        except asyncio.TimeoutError:
            self._logger.warning(
                "HTTP snapshot request timeout",
                printer_id=printer_id,
                url=masked_url
            )
            return None, ''
        except aiohttp.ClientError as e:
            self._logger.warning(
                "HTTP snapshot client error",
                printer_id=printer_id,
                url=masked_url,
                error=str(e)
            )
            return None, ''
        except Exception as e:
            self._logger.error(
                "HTTP snapshot unexpected error",
                printer_id=printer_id,
                url=masked_url,
                error=str(e)
            )
            return None, ''

    async def _extract_rtsp_frame(
        self,
        url: str,
        printer_id: str
    ) -> Tuple[Optional[bytes], str]:
        """
        Extract a single frame from RTSP stream using ffmpeg.

        Args:
            url: RTSP stream URL
            printer_id: Printer ID for logging

        Returns:
            Tuple of (image_bytes as JPEG, 'image/jpeg') or (None, '') on failure

        Note:
            Requires ffmpeg to be installed on the system.
            Frame extraction is done in a thread executor to avoid blocking.
        """
        masked_url = mask_url_credentials(url)
        tmp_path = None

        try:
            # Create temp file for output
            fd, tmp_path = tempfile.mkstemp(suffix='.jpg')
            os.close(fd)

            # Build ffmpeg command
            # -rtsp_transport tcp: Use TCP for more reliable RTSP
            # -frames:v 1: Extract only 1 frame
            # -q:v 2: High quality JPEG (scale 2-31, lower is better)
            # -y: Overwrite output file
            cmd = [
                'ffmpeg',
                '-rtsp_transport', 'tcp',
                '-i', url,
                '-frames:v', '1',
                '-q:v', '2',
                '-y',
                tmp_path
            ]

            # Run ffmpeg in executor with timeout
            loop = asyncio.get_event_loop()

            def run_ffmpeg():
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        timeout=15  # 15 second timeout for RTSP connection + frame
                    )
                    return result.returncode, result.stderr
                except subprocess.TimeoutExpired:
                    return -1, b'Timeout'
                except Exception as e:
                    return -1, str(e).encode()

            returncode, stderr = await loop.run_in_executor(None, run_ffmpeg)

            if returncode == 0 and os.path.exists(tmp_path):
                with open(tmp_path, 'rb') as f:
                    data = f.read()

                if len(data) > 0:
                    self._logger.info(
                        "RTSP frame extracted successfully",
                        printer_id=printer_id,
                        size_bytes=len(data)
                    )
                    return data, 'image/jpeg'
                else:
                    self._logger.warning(
                        "RTSP frame extraction produced empty file",
                        printer_id=printer_id,
                        url=masked_url
                    )
                    return None, ''
            else:
                self._logger.warning(
                    "RTSP frame extraction failed",
                    printer_id=printer_id,
                    url=masked_url,
                    returncode=returncode,
                    stderr=stderr.decode('utf-8', errors='ignore')[:200] if stderr else None
                )
                return None, ''

        except FileNotFoundError:
            self._logger.error(
                "ffmpeg not found - required for RTSP support. "
                "Install with: apt-get install ffmpeg",
                printer_id=printer_id
            )
            return None, ''
        except Exception as e:
            self._logger.error(
                "RTSP frame extraction error",
                printer_id=printer_id,
                url=masked_url,
                error=str(e)
            )
            return None, ''
        finally:
            # Cleanup temp file
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    async def test_url(self, webcam_url: str) -> dict:
        """
        Test if a webcam URL is accessible and returns valid image data.

        Args:
            webcam_url: URL to test

        Returns:
            Dict with test results:
            {
                'success': bool,
                'url_type': str,  # 'http_snapshot', 'rtsp', or 'unknown'
                'image_size': int,  # Only if success
                'error_message': str  # Only if failure
            }
        """
        url_type = detect_url_type(webcam_url)
        masked_url = mask_url_credentials(webcam_url)

        if url_type == 'unknown':
            return {
                'success': False,
                'url_type': url_type,
                'error_message': 'Unsupported URL scheme. Use http://, https://, or rtsp://'
            }

        self._logger.info(
            "Testing webcam URL",
            url=masked_url,
            url_type=url_type
        )

        data, content_type = await self.fetch_snapshot(webcam_url, 'test')

        if data and len(data) > 0:
            return {
                'success': True,
                'url_type': url_type,
                'content_type': content_type,
                'image_size': len(data)
            }
        else:
            error_msg = f'Failed to fetch snapshot from {masked_url}'
            if url_type == 'rtsp':
                error_msg += ' (ensure ffmpeg is installed)'
            return {
                'success': False,
                'url_type': url_type,
                'error_message': error_msg
            }


# Global service instance for dependency injection
_external_camera_service: Optional[ExternalCameraService] = None


def get_external_camera_service() -> ExternalCameraService:
    """Get or create the global ExternalCameraService instance."""
    global _external_camera_service
    if _external_camera_service is None:
        _external_camera_service = ExternalCameraService()
    return _external_camera_service
