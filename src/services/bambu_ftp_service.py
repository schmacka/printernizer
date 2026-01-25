"""
Bambu Lab FTP Service

This module provides direct FTP connectivity to Bambu Lab printers using Python's built-in
ftplib with implicit TLS encryption. This replaces the bambulabs-api dependency for
file operations.

Connection Parameters:
- Port: 990 (implicit TLS)
- Username: bblp
- Password: Bambu Lab access code
- Protocol: FTP with implicit TLS
- Directory: /cache (primary location for 3D files)
"""

import ftplib
import ssl
import socket
import asyncio
import time
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, AsyncGenerator
from datetime import datetime
import structlog
from contextlib import asynccontextmanager

from src.constants import PortConstants, NetworkConstants

logger = structlog.get_logger()


class BambuFTPFile:
    """Represents a file on the Bambu Lab printer's FTP server."""

    def __init__(self, name: str, size: int = 0, permissions: str = '',
                 modified: Optional[datetime] = None, raw_line: str = ''):
        self.name = name
        self.size = size
        self.permissions = permissions
        self.modified = modified
        self.raw_line = raw_line
        self.file_type = self._determine_file_type()

    def _determine_file_type(self) -> str:
        """Determine file type from filename extension.

        Returns:
            File type string (3mf, stl, gcode, image, video, or unknown).
        """
        ext = Path(self.name).suffix.lower()
        type_map = {
            '.3mf': '3mf',
            '.stl': 'stl',
            '.obj': 'obj',
            '.gcode': 'gcode',
            '.bgcode': 'bgcode',
            '.ply': 'ply',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.mp4': 'video',
            '.avi': 'video'
        }
        return type_map.get(ext, 'unknown')

    @property
    def is_3d_file(self) -> bool:
        """Check if this is a 3D printing file."""
        return self.file_type in ['3mf', 'stl', 'obj', 'gcode', 'bgcode', 'ply']

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'name': self.name,
            'size': self.size,
            'permissions': self.permissions,
            'modified': self.modified.isoformat() if self.modified else None,
            'file_type': self.file_type,
            'is_3d_file': self.is_3d_file,
            'raw_line': self.raw_line
        }


class BambuFTPService:
    """Service for FTP operations with Bambu Lab printers."""

    def __init__(self, ip_address: str, access_code: str, port: int = PortConstants.BAMBU_FTP_PORT):
        """
        Initialize Bambu FTP service.

        Args:
            ip_address: Printer IP address
            access_code: Bambu Lab access code (used as password)
            port: FTP port (default 990 for implicit TLS)
        """
        self.ip_address = ip_address
        self.access_code = access_code
        self.port = port
        self.username = "bblp"  # Fixed username for Bambu Lab printers

        # Connection settings
        self.timeout = NetworkConstants.CONNECTION_TIMEOUT_SECONDS
        self.retry_count = NetworkConstants.FTP_RETRY_COUNT
        self.retry_delay = NetworkConstants.FTP_RETRY_DELAY_SECONDS
        self.retry_backoff = NetworkConstants.FTP_RETRY_BACKOFF_MULTIPLIER
        self.retry_max_delay = NetworkConstants.FTP_RETRY_MAX_DELAY_SECONDS
        self.retry_jitter = NetworkConstants.FTP_RETRY_JITTER_FACTOR

        logger.info("Initialized Bambu FTP service",
                   ip=ip_address, port=port, username=self.username)

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for implicit TLS connection.

        Configures SSL context to accept self-signed certificates commonly
        used by Bambu Lab printers.

        Returns:
            Configured SSLContext instance for FTP_TLS connection.
        """
        ssl_context = ssl.create_default_context()
        # Bambu Lab printers typically use self-signed certificates
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context

    async def _test_socket_connectivity(self) -> bool:
        """Quick socket connectivity test before full FTP connection.

        Returns:
            True if socket connection succeeds, False otherwise
        """
        def _sync_test():
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5.0)  # Quick 5-second test
            try:
                test_socket.connect((self.ip_address, self.port))
                return True
            except (socket.timeout, ConnectionRefusedError, OSError):
                return False
            finally:
                try:
                    test_socket.close()
                except:
                    pass

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_test)

    async def _connect_ftp(self) -> ftplib.FTP_TLS:
        """
        Create and return a connected FTP_TLS instance using implicit TLS.

        Bambu Lab printers use implicit TLS on port 990, where SSL/TLS is
        established from the first byte of the connection, not via STARTTLS.

        Returns:
            Connected FTP_TLS instance

        Raises:
            ConnectionError: If connection fails
            PermissionError: If authentication fails
        """
        start_time = time.time()
        ssl_context = self._create_ssl_context()

        # Run FTP operations in thread pool since ftplib is synchronous
        def _sync_connect():
            # For implicit TLS, we need to wrap the socket with SSL before FTP
            raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_socket.settimeout(self.timeout)

            # Enable TCP keepalive to detect dead connections
            raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            try:
                # Connect raw socket first
                raw_socket.connect((self.ip_address, self.port))

                # Wrap with SSL (implicit TLS)
                ssl_socket = ssl_context.wrap_socket(
                    raw_socket,
                    server_hostname=self.ip_address
                )

                # Create FTP_TLS instance and use the SSL socket
                ftp = ftplib.FTP_TLS(context=ssl_context, timeout=self.timeout)
                ftp.sock = ssl_socket  # Use our pre-wrapped SSL socket
                ftp.file = ssl_socket.makefile('r', encoding='utf-8')
                ftp.af = socket.AF_INET  # Set address family for passive mode
                ftp.host = self.ip_address  # Set host for data connection SSL wrapping
                ftp.set_pasv(True)  # Use passive mode

                # Get welcome message
                ftp.welcome = ftp.getresp()

                # Authenticate
                ftp.login(self.username, self.access_code)

                # Switch to secure data connection
                ftp.prot_p()

                return ftp

            except ftplib.error_perm as e:
                try:
                    raw_socket.close()
                except:
                    pass
                raise PermissionError(f"FTP authentication failed: {e}")
            except (socket.timeout, ConnectionRefusedError, ssl.SSLError) as e:
                try:
                    raw_socket.close()
                except:
                    pass
                raise ConnectionError(f"FTP connection failed: {e}")
            except Exception as e:
                try:
                    raw_socket.close()
                except:
                    pass
                raise ConnectionError(f"Unexpected FTP error: {e}")

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, _sync_connect)
            duration = time.time() - start_time
            logger.info("[TIMING] FTP connection successful",
                       ip=self.ip_address,
                       duration_seconds=round(duration, 2),
                       status="success")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.warning("[TIMING] FTP connection failed",
                          ip=self.ip_address,
                          duration_seconds=round(duration, 2),
                          status="failure",
                          error=str(e))
            raise

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt using exponential backoff with jitter.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds with jitter applied
        """
        # Exponential backoff: base_delay * (multiplier ^ attempt)
        delay = self.retry_delay * (self.retry_backoff ** attempt)

        # Cap at maximum delay
        delay = min(delay, self.retry_max_delay)

        # Add jitter (±jitter_factor)
        jitter = delay * self.retry_jitter * (2 * random.random() - 1)
        delay = max(0.1, delay + jitter)  # Ensure minimum 100ms delay

        return delay

    @asynccontextmanager
    async def ftp_connection(self) -> AsyncGenerator[ftplib.FTP_TLS, None]:
        """
        Async context manager for FTP connections with automatic cleanup.

        Uses exponential backoff with jitter for retry attempts to improve
        connection stability and prevent thundering herd problems.

        Includes socket pre-warming to detect connectivity issues early.

        Usage:
            async with service.ftp_connection() as ftp:
                files = await service.list_files(ftp)
        """
        ftp = None
        last_error = None

        for attempt in range(self.retry_count):
            try:
                # Pre-warm: Quick socket test before full FTP connection
                # This helps detect connectivity issues early and reduces
                # the likelihood of slow timeout failures
                if attempt == 0:
                    socket_ok = await self._test_socket_connectivity()
                    if not socket_ok:
                        logger.warning("FTP socket pre-test failed, printer may be unavailable",
                                     ip=self.ip_address)
                        # Still try the full connection - printer might need a moment
                        await asyncio.sleep(0.5)

                ftp = await self._connect_ftp()
                logger.debug("FTP connection established",
                           ip=self.ip_address, attempt=attempt + 1)
                yield ftp
                return

            except (ConnectionError, PermissionError) as e:
                last_error = e
                retry_delay = self._calculate_retry_delay(attempt)

                logger.warning("FTP connection attempt failed",
                             ip=self.ip_address,
                             attempt=attempt + 1,
                             max_attempts=self.retry_count,
                             retry_delay_seconds=round(retry_delay, 2),
                             error=str(e),
                             error_type=type(e).__name__)

                if attempt == self.retry_count - 1:
                    logger.error("FTP connection failed after all retries",
                               ip=self.ip_address,
                               total_attempts=self.retry_count,
                               error=str(e),
                               error_type=type(e).__name__)
                    raise

                # Wait with exponential backoff before retry
                await asyncio.sleep(retry_delay)

            finally:
                if ftp:
                    try:
                        await asyncio.get_event_loop().run_in_executor(None, ftp.quit)
                    except (OSError, TimeoutError, Exception) as quit_error:
                        # Quit failed, try to close the connection
                        logger.debug("FTP quit failed, attempting close",
                                    error=str(quit_error))
                        try:
                            ftp.close()
                        except (OSError, Exception) as close_error:
                            # Best effort cleanup - log and continue
                            logger.debug("FTP close also failed during cleanup",
                                        error=str(close_error))

    async def list_files(self, directory: str = "/cache") -> List[BambuFTPFile]:
        """
        List files in the specified directory.

        Args:
            directory: Directory path to list (default: /cache)

        Returns:
            List of BambuFTPFile objects

        Raises:
            ConnectionError: If FTP connection fails
            PermissionError: If directory access is denied
        """
        logger.info("Listing files via FTP",
                   ip=self.ip_address, directory=directory)

        async with self.ftp_connection() as ftp:
            def _sync_list():
                try:
                    # Change to target directory
                    ftp.cwd(directory)

                    # Get detailed file listing
                    raw_lines = []
                    ftp.retrlines('LIST', raw_lines.append)

                    files = []
                    for line in raw_lines:
                        file_info = self._parse_ftp_line(line)
                        if file_info:
                            files.append(file_info)

                    return files

                except ftplib.error_perm as e:
                    if "550" in str(e):  # Directory not found
                        logger.warning("Directory not accessible",
                                     ip=self.ip_address, directory=directory, error=str(e))
                        return []
                    else:
                        raise PermissionError(f"FTP permission error: {e}")

            loop = asyncio.get_event_loop()
            files = await loop.run_in_executor(None, _sync_list)

            logger.info("FTP file listing complete",
                       ip=self.ip_address,
                       directory=directory,
                       file_count=len(files))

            return files

    def _parse_ftp_line(self, line: str) -> Optional[BambuFTPFile]:
        """
        Parse a single line from FTP LIST command.

        Args:
            line: Raw FTP LIST output line

        Returns:
            BambuFTPFile object or None if line couldn't be parsed
        """
        try:
            parts = line.strip().split()
            if len(parts) < 9:
                return None

            permissions = parts[0]

            # Skip directories and special entries
            if permissions.startswith('d') or parts[-1] in ['.', '..']:
                return None

            # Extract file information
            size = int(parts[4]) if parts[4].isdigit() else 0
            filename = ' '.join(parts[8:])  # Handle filenames with spaces

            # Try to parse modification time (best effort)
            modified = None
            try:
                # FTP time format varies, this is a basic attempt
                # Format: "Mon DD HH:MM" or "Mon DD YYYY"
                time_parts = parts[5:8]
                if len(time_parts) >= 3:
                    # This is a simplified parser - production code might want more robust parsing
                    pass
            except (ValueError, IndexError, AttributeError) as e:
                # Time parsing failed - not critical, leave as None
                logger.debug("Could not parse FTP file modification time",
                            line=line, error=str(e))

            return BambuFTPFile(
                name=filename,
                size=size,
                permissions=permissions,
                modified=modified,
                raw_line=line
            )

        except Exception as e:
            logger.debug("Failed to parse FTP line", line=line, error=str(e))
            return None

    async def download_file(self, remote_filename: str, local_path: str,
                          directory: str = "/cache") -> bool:
        """
        Download a file from the FTP server.

        Args:
            remote_filename: Name of file to download on the server
            local_path: Local path where file should be saved
            directory: Remote directory containing the file (default: /cache)

        Returns:
            True if download successful, False otherwise
        """
        logger.info("Downloading file via FTP",
                   ip=self.ip_address,
                   remote_file=remote_filename,
                   local_path=local_path,
                   directory=directory)

        try:
            # Ensure local directory exists
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)

            async with self.ftp_connection() as ftp:
                def _sync_download():
                    try:
                        # Change to target directory
                        ftp.cwd(directory)

                        # Download the file
                        with open(local_path, 'wb') as local_file:
                            ftp.retrbinary(f'RETR {remote_filename}', local_file.write)

                        return True

                    except ftplib.error_perm as e:
                        logger.error("FTP permission error during download",
                                   ip=self.ip_address,
                                   remote_file=remote_filename,
                                   error=str(e))
                        return False
                    except Exception as e:
                        logger.error("FTP download error",
                                   ip=self.ip_address,
                                   remote_file=remote_filename,
                                   error=str(e))
                        return False

                loop = asyncio.get_event_loop()
                success = await loop.run_in_executor(None, _sync_download)

                if success and Path(local_path).exists():
                    file_size = Path(local_path).stat().st_size
                    logger.info("FTP download successful",
                               ip=self.ip_address,
                               remote_file=remote_filename,
                               local_path=local_path,
                               size=file_size)
                    return True
                else:
                    logger.error("FTP download failed - file not created",
                               ip=self.ip_address,
                               remote_file=remote_filename)
                    return False

        except Exception as e:
            logger.error("FTP download operation failed",
                        ip=self.ip_address,
                        remote_file=remote_filename,
                        error=str(e))
            return False

    async def file_exists(self, filename: str, directory: str = "/cache") -> bool:
        """
        Check if a file exists on the FTP server.

        Args:
            filename: Name of file to check
            directory: Directory to check in (default: /cache)

        Returns:
            True if file exists, False otherwise
        """
        try:
            files = await self.list_files(directory)
            return any(f.name == filename for f in files)
        except Exception as e:
            logger.debug("Error checking file existence",
                        ip=self.ip_address,
                        filename=filename,
                        error=str(e))
            return False

    async def get_file_info(self, filename: str, directory: str = "/cache") -> Optional[BambuFTPFile]:
        """
        Get detailed information about a specific file.

        Args:
            filename: Name of file to get info for
            directory: Directory containing the file (default: /cache)

        Returns:
            BambuFTPFile object or None if file not found
        """
        try:
            files = await self.list_files(directory)
            return next((f for f in files if f.name == filename), None)
        except Exception as e:
            logger.debug("Error getting file info",
                        ip=self.ip_address,
                        filename=filename,
                        error=str(e))
            return None

    async def upload_file(self, local_path: str, remote_filename: str,
                          directory: str = "/cache") -> bool:
        """
        Upload a file to the FTP server.

        Args:
            local_path: Local path of the file to upload
            remote_filename: Name to use for the file on the server
            directory: Remote directory to upload to (default: /cache)

        Returns:
            True if upload successful, False otherwise
        """
        logger.info("Uploading file via FTP",
                   ip=self.ip_address,
                   local_path=local_path,
                   remote_file=remote_filename,
                   directory=directory)

        try:
            # Verify local file exists
            local_file = Path(local_path)
            if not local_file.exists():
                logger.error("Local file not found for upload",
                           local_path=local_path)
                return False

            file_size = local_file.stat().st_size

            async with self.ftp_connection() as ftp:
                def _sync_upload():
                    try:
                        # Change to target directory
                        ftp.cwd(directory)

                        # Upload the file
                        with open(local_path, 'rb') as local_file_handle:
                            ftp.storbinary(f'STOR {remote_filename}', local_file_handle)

                        return True

                    except ftplib.error_perm as e:
                        logger.error("FTP permission error during upload",
                                   ip=self.ip_address,
                                   remote_file=remote_filename,
                                   error=str(e))
                        return False
                    except Exception as e:
                        logger.error("FTP upload error",
                                   ip=self.ip_address,
                                   remote_file=remote_filename,
                                   error=str(e))
                        return False

                loop = asyncio.get_event_loop()
                success = await loop.run_in_executor(None, _sync_upload)

                if success:
                    logger.info("FTP upload successful",
                               ip=self.ip_address,
                               remote_file=remote_filename,
                               size=file_size)
                    return True
                else:
                    logger.error("FTP upload failed",
                               ip=self.ip_address,
                               remote_file=remote_filename)
                    return False

        except Exception as e:
            logger.error("FTP upload operation failed",
                        ip=self.ip_address,
                        local_path=local_path,
                        remote_file=remote_filename,
                        error=str(e))
            return False

    async def test_connection(self) -> Tuple[bool, str]:
        """
        Test the FTP connection without performing any operations.

        Returns:
            Tuple of (success: bool, message: str)
        """
        start_time = time.time()
        try:
            async with self.ftp_connection() as ftp:
                # Simple test - get current directory
                loop = asyncio.get_event_loop()
                current_dir = await loop.run_in_executor(None, ftp.pwd)

                duration = time.time() - start_time
                logger.info("[TIMING] FTP test connection successful",
                           ip=self.ip_address,
                           duration_seconds=round(duration, 2),
                           status="success")
                return True, f"Connection successful. Current directory: {current_dir}"

        except ConnectionError as e:
            duration = time.time() - start_time
            logger.warning("[TIMING] FTP test connection failed",
                          ip=self.ip_address,
                          duration_seconds=round(duration, 2),
                          status="failure",
                          error_type="ConnectionError")
            return False, f"Connection failed: {e}"
        except PermissionError as e:
            duration = time.time() - start_time
            logger.warning("[TIMING] FTP test connection failed",
                          ip=self.ip_address,
                          duration_seconds=round(duration, 2),
                          status="failure",
                          error_type="PermissionError")
            return False, f"Authentication failed: {e}"
        except Exception as e:
            duration = time.time() - start_time
            logger.warning("[TIMING] FTP test connection failed",
                          ip=self.ip_address,
                          duration_seconds=round(duration, 2),
                          status="failure",
                          error_type=type(e).__name__)
            return False, f"Unexpected error: {e}"


async def create_bambu_ftp_service(ip_address: str, access_code: str) -> BambuFTPService:
    """
    Factory function to create and test a Bambu FTP service.

    Args:
        ip_address: Printer IP address
        access_code: Bambu Lab access code

    Returns:
        BambuFTPService instance

    Raises:
        ConnectionError: If connection test fails
    """
    service = BambuFTPService(ip_address, access_code)

    # Test connection
    success, message = await service.test_connection()
    if not success:
        raise ConnectionError(f"Failed to connect to Bambu Lab printer at {ip_address}: {message}")

    logger.info("Bambu FTP service created and tested successfully",
               ip=ip_address, message=message)

    return service