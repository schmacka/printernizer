"""
HTTP download strategy for Bambu Lab printers.

Downloads files via HTTP from the printer's web interface.
"""

from typing import Optional, List
import aiohttp

from src.constants import PortConstants, NetworkConstants, FileConstants
from .base import (
    DownloadStrategy,
    DownloadResult,
    DownloadOptions,
    RetryableDownloadError
)


class HTTPDownloadStrategy(DownloadStrategy):
    """Download files via HTTP from Bambu Lab printer web interface."""

    def __init__(
        self,
        printer_id: str,
        printer_ip: str,
        access_code: Optional[str] = None
    ):
        """Initialize HTTP download strategy.

        Args:
            printer_id: Unique identifier for the printer
            printer_ip: IP address of the printer
            access_code: Optional access code for authentication
        """
        super().__init__(printer_id, printer_ip)
        self.access_code = access_code

    @property
    def name(self) -> str:
        """Return the name of this strategy."""
        return "HTTP"

    async def is_available(self) -> bool:
        """Check if HTTP download is available.

        Returns:
            True (HTTP is always available if we have an IP)
        """
        return bool(self.printer_ip)

    async def download(self, options: DownloadOptions) -> DownloadResult:
        """Download file via HTTP.

        Args:
            options: Download configuration options

        Returns:
            DownloadResult with success status and details

        Raises:
            RetryableDownloadError: If download fails but can be retried
        """
        self._ensure_directory(options.local_path)

        # Generate HTTP URLs to try
        urls_to_try = self._generate_http_urls(options.filename, options.remote_paths)

        # Create timeout configuration
        timeout = aiohttp.ClientTimeout(
            total=options.timeout_seconds or NetworkConstants.HTTP_DOWNLOAD_TIMEOUT_SECONDS
        )

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for url in urls_to_try:
                    result = await self._try_download_url(
                        session,
                        url,
                        options
                    )

                    if result.success:
                        return result

        except aiohttp.ClientError as e:
            self.logger.error(
                "HTTP client error",
                filename=options.filename,
                error=str(e)
            )
            raise RetryableDownloadError(f"HTTP client error: {str(e)}")

        except Exception as e:
            self.logger.error(
                "HTTP download failed",
                filename=options.filename,
                error=str(e)
            )
            raise RetryableDownloadError(f"HTTP download error: {str(e)}")

        return DownloadResult(
            success=False,
            file_path=options.local_path,
            error=f"File not accessible via HTTP at any URL: {options.filename}"
        )

    async def _try_download_url(
        self,
        session: aiohttp.ClientSession,
        url: str,
        options: DownloadOptions
    ) -> DownloadResult:
        """Try downloading from a specific URL.

        Args:
            session: aiohttp session
            url: URL to download from
            options: Download options

        Returns:
            DownloadResult
        """
        try:
            self.logger.debug(
                "Attempting HTTP download",
                url=url,
                filename=options.filename
            )

            # Setup authentication if available
            auth = None
            if self.access_code:
                auth = aiohttp.BasicAuth('bblp', self.access_code)

            async with session.get(url, auth=auth) as response:
                if response.status == 200:
                    # Get file size for progress tracking
                    content_length = response.headers.get('Content-Length')
                    total_size = int(content_length) if content_length else None

                    # Download file in chunks
                    downloaded_size = 0
                    chunk_size = options.chunk_size_bytes or FileConstants.DOWNLOAD_CHUNK_SIZE_BYTES

                    with open(options.local_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            f.write(chunk)
                            downloaded_size += len(chunk)

                            # Log progress for large files (every MB)
                            if total_size and downloaded_size % (1024 * 1024) < chunk_size:
                                self._log_progress(
                                    downloaded_size,
                                    total_size,
                                    options.filename
                                )

                    self.logger.info(
                        "HTTP download successful",
                        filename=options.filename,
                        url=url,
                        size=downloaded_size
                    )

                    return DownloadResult(
                        success=True,
                        file_path=options.local_path,
                        size_bytes=downloaded_size,
                        remote_path=url
                    )

                elif response.status == 401:
                    self.logger.debug(
                        "HTTP 401 - authentication required",
                        url=url
                    )

                elif response.status == 404:
                    self.logger.debug(
                        "HTTP 404 - file not found",
                        url=url
                    )

                else:
                    self.logger.debug(
                        "HTTP error",
                        url=url,
                        status=response.status
                    )

        except aiohttp.ClientError as e:
            self.logger.debug(
                "HTTP client error",
                url=url,
                error=str(e)
            )

        except Exception as e:
            self.logger.debug(
                "HTTP download attempt failed",
                url=url,
                error=str(e)
            )

        return DownloadResult(
            success=False,
            file_path=options.local_path,
            error=f"HTTP download failed for URL: {url}"
        )

    def _generate_http_urls(
        self,
        filename: str,
        custom_urls: Optional[List[str]] = None
    ) -> List[str]:
        """Generate list of HTTP URLs to try.

        Args:
            filename: Name of file to download
            custom_urls: Optional custom URLs to try first

        Returns:
            List of URLs to try in order
        """
        urls = []

        # Add custom URLs first
        if custom_urls:
            urls.extend(custom_urls)

        # Add standard Bambu Lab HTTP endpoints
        # Try common paths on default HTTP port
        urls.extend([
            f"http://{self.printer_ip}/cache/{filename}",
            f"http://{self.printer_ip}/model/{filename}",
            f"http://{self.printer_ip}/files/{filename}",
        ])

        # Try camera port endpoints (some Bambu printers expose files here)
        if hasattr(PortConstants, 'BAMBU_CAMERA_PORT'):
            camera_port = PortConstants.BAMBU_CAMERA_PORT
            urls.extend([
                f"http://{self.printer_ip}:{camera_port}/cache/{filename}",
                f"http://{self.printer_ip}:{camera_port}/model/{filename}",
                f"http://{self.printer_ip}:{camera_port}/files/{filename}",
            ])

        return urls
