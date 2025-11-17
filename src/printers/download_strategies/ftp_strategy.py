"""
FTP download strategy for Bambu Lab printers.

Supports both direct FTP service and bambulabs_api FTP client.
"""

from typing import Optional, List, Callable
from pathlib import Path

from .base import (
    DownloadStrategy,
    DownloadResult,
    DownloadOptions,
    RetryableDownloadError,
    FatalDownloadError
)


class FTPDownloadStrategy(DownloadStrategy):
    """Download files via FTP using bambulabs_api or direct FTP service."""

    def __init__(
        self,
        printer_id: str,
        printer_ip: str,
        ftp_client=None,
        ftp_service=None
    ):
        """Initialize FTP download strategy.

        Args:
            printer_id: Unique identifier for the printer
            printer_ip: IP address of the printer
            ftp_client: bambulabs_api FTP client instance
            ftp_service: Direct FTP service instance (BambuFTPService)
        """
        super().__init__(printer_id, printer_ip)
        self.ftp_client = ftp_client
        self.ftp_service = ftp_service

    @property
    def name(self) -> str:
        """Return the name of this strategy."""
        return "FTP"

    async def is_available(self) -> bool:
        """Check if FTP download is available.

        Returns:
            True if either FTP client or service is available
        """
        return self.ftp_client is not None or self.ftp_service is not None

    async def download(self, options: DownloadOptions) -> DownloadResult:
        """Download file via FTP.

        Args:
            options: Download configuration options

        Returns:
            DownloadResult with success status and details

        Raises:
            RetryableDownloadError: If download fails but can be retried
            FatalDownloadError: If download fails permanently
        """
        self._ensure_directory(options.local_path)

        # Try bambulabs_api FTP client first
        if self.ftp_client:
            result = await self._download_via_bambu_ftp(options)
            if result.success:
                return result

        # Fall back to direct FTP service
        if self.ftp_service:
            result = await self._download_via_ftp_service(options)
            if result.success:
                return result

        return DownloadResult(
            success=False,
            file_path=options.local_path,
            error="FTP client and service both unavailable or failed"
        )

    async def _download_via_bambu_ftp(self, options: DownloadOptions) -> DownloadResult:
        """Download using bambulabs_api FTP client with path discovery.

        This method tries multiple paths and uses fuzzy matching to find files.

        Args:
            options: Download options

        Returns:
            DownloadResult
        """
        # Generate candidate paths to try
        paths_to_try = self._generate_ftp_paths(options.filename, options.remote_paths)

        # Try each path
        for remote_path in paths_to_try:
            try:
                self.logger.debug(
                    "Attempting FTP download",
                    remote_path=remote_path,
                    filename=options.filename
                )

                # Download file using bambulabs_api
                file_data_io = self.ftp_client.download_file(remote_path)

                if file_data_io:
                    file_data = file_data_io.getvalue()

                    if file_data and len(file_data) > 0:
                        # Write to local file
                        bytes_written = self._write_file_chunk(
                            options.local_path,
                            file_data
                        )

                        self.logger.info(
                            "FTP download successful",
                            filename=options.filename,
                            remote_path=remote_path,
                            size=bytes_written
                        )

                        return DownloadResult(
                            success=True,
                            file_path=options.local_path,
                            size_bytes=bytes_written,
                            remote_path=remote_path
                        )
                    else:
                        self.logger.debug(
                            "FTP returned empty data",
                            remote_path=remote_path
                        )

            except Exception as e:
                self.logger.debug(
                    "FTP download failed for path",
                    remote_path=remote_path,
                    error=str(e)
                )
                continue

        # Try enhanced search with directory scanning
        discovered_result = await self._enhanced_ftp_search(options)
        if discovered_result.success:
            return discovered_result

        return DownloadResult(
            success=False,
            file_path=options.local_path,
            error=f"File not found via FTP: {options.filename}"
        )

    async def _enhanced_ftp_search(self, options: DownloadOptions) -> DownloadResult:
        """Enhanced FTP search with directory scanning and fuzzy matching.

        Args:
            options: Download options

        Returns:
            DownloadResult
        """
        try:
            target_lower = options.filename.lower()
            discovered = []  # (dir, name, path_component)

            # Directories to scan
            scan_dirs = ['', 'cache', 'model', 'timelapse', 'sdcard', 'usb', 'USB', 'gcodes']

            # Helper to safely list directory
            def _safe_list(dir_path: str) -> list:
                methods = ['list_dir', 'listdir', 'listfiles', 'list_files']
                for method in methods:
                    if hasattr(self.ftp_client, method):
                        try:
                            return getattr(self.ftp_client, method)(dir_path)
                        except Exception:
                            continue
                return []

            # Scan directories
            for d in scan_dirs:
                try:
                    entries = _safe_list(d) if d != '' else _safe_list('.')
                    if not entries:
                        continue

                    for entry in entries:
                        if isinstance(entry, dict):
                            name = entry.get('name') or entry.get('filename') or ''
                            path_component = entry.get('path') or name
                        else:
                            name = str(entry)
                            path_component = name

                        if not name:
                            continue

                        discovered.append((d, name, path_component))

                except Exception as e:
                    self.logger.debug(
                        "Directory scan failed",
                        directory=d,
                        error=str(e)
                    )
                    continue

            # Try exact case-insensitive match
            exact_match = next(
                (item for item in discovered if item[1].lower() == target_lower),
                None
            )

            if exact_match:
                return await self._try_discovered_file(exact_match, options, "exact match")

            # Try fuzzy match (substring without extension)
            base_no_ext = target_lower.rsplit('.', 1)[0]
            fuzzy_candidates = [
                (d, name, path)
                for d, name, path in discovered
                if base_no_ext in name.lower()
            ]

            if fuzzy_candidates:
                # Rank candidates
                def rank(item):
                    _, name, _ = item
                    n_lower = name.lower()
                    score = 0
                    if n_lower.endswith('.3mf'):
                        score += 3
                    if n_lower.endswith('.gcode'):
                        score += 2
                    if n_lower.startswith(base_no_ext):
                        score += 1
                    if base_no_ext in n_lower:
                        score += 0.5
                    return -score  # Smallest first (best match)

                fuzzy_candidates.sort(key=rank)
                best = fuzzy_candidates[0]
                return await self._try_discovered_file(best, options, "fuzzy match")

            # Provide suggestions if we found similar files
            if discovered:
                similar = [
                    name for _, name, _ in discovered
                    if target_lower.split('.')[0] in name.lower()
                ][:10]
                self.logger.warning(
                    "File not found via FTP enhanced search",
                    filename=options.filename,
                    similar=similar,
                    scanned_dirs=scan_dirs
                )

            return DownloadResult(
                success=False,
                file_path=options.local_path,
                error="File not found after enhanced search"
            )

        except Exception as e:
            self.logger.debug(
                "Enhanced FTP search failed",
                filename=options.filename,
                error=str(e)
            )
            return DownloadResult(
                success=False,
                file_path=options.local_path,
                error=f"Enhanced search error: {str(e)}"
            )

    async def _try_discovered_file(
        self,
        discovered_item: tuple,
        options: DownloadOptions,
        match_type: str
    ) -> DownloadResult:
        """Try downloading a discovered file.

        Args:
            discovered_item: (dir, name, path) tuple
            options: Download options
            match_type: Description of match type for logging

        Returns:
            DownloadResult
        """
        dir_part, name_part, path_component = discovered_item
        remote_path = (
            f"{dir_part}/{name_part}"
            if dir_part and not path_component.startswith(dir_part)
            else path_component
        )

        try:
            self.logger.debug(
                f"Attempting FTP download ({match_type})",
                remote_path=remote_path
            )

            file_data_io = self.ftp_client.download_file(remote_path)
            if file_data_io:
                data = file_data_io.getvalue()
                if data:
                    bytes_written = self._write_file_chunk(options.local_path, data)

                    self.logger.info(
                        f"FTP download successful ({match_type})",
                        requested=options.filename,
                        matched=name_part,
                        remote_path=remote_path,
                        size=bytes_written
                    )

                    return DownloadResult(
                        success=True,
                        file_path=options.local_path,
                        size_bytes=bytes_written,
                        remote_path=remote_path
                    )

        except Exception as e:
            self.logger.debug(
                f"{match_type.capitalize()} download failed",
                remote_path=remote_path,
                error=str(e)
            )

        return DownloadResult(
            success=False,
            file_path=options.local_path,
            error=f"Download failed for discovered file: {name_part}"
        )

    async def _download_via_ftp_service(self, options: DownloadOptions) -> DownloadResult:
        """Download using direct FTP service.

        Args:
            options: Download options

        Returns:
            DownloadResult
        """
        try:
            # Try downloading from cache directory
            success = await self.ftp_service.download_file(
                options.filename,
                options.local_path,
                "/cache"
            )

            if success:
                size = self._get_file_size(options.local_path)
                self.logger.info(
                    "FTP service download successful",
                    filename=options.filename,
                    size=size
                )

                return DownloadResult(
                    success=True,
                    file_path=options.local_path,
                    size_bytes=size,
                    remote_path=f"/cache/{options.filename}"
                )

        except Exception as e:
            self.logger.debug(
                "FTP service download failed",
                filename=options.filename,
                error=str(e)
            )

        return DownloadResult(
            success=False,
            file_path=options.local_path,
            error="FTP service download failed"
        )

    def _generate_ftp_paths(
        self,
        filename: str,
        custom_paths: Optional[List[str]] = None
    ) -> List[str]:
        """Generate list of FTP paths to try.

        Args:
            filename: Name of file to download
            custom_paths: Optional custom paths to try first

        Returns:
            List of paths to try in order
        """
        paths = []

        # Add custom paths first
        if custom_paths:
            paths.extend(custom_paths)

        # Add standard Bambu Lab paths
        paths.extend([
            f"cache/{filename}",
            filename,
            f"model/{filename}",
            f"timelapse/{filename}",
            f"sdcard/{filename}",
            f"usb/{filename}",
            f"USB/{filename}",
            f"gcodes/{filename}",
        ])

        return paths
