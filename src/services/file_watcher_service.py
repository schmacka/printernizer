"""
File Watcher Service for monitoring local folders for 3D print files.
Implements cross-platform file system monitoring using watchdog.
"""

import os
import sys
import asyncio
import hashlib
import threading
from typing import Dict, List, Set, Optional, Callable, Any, Coroutine, TYPE_CHECKING
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

import structlog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers.polling import PollingObserver

if TYPE_CHECKING:
    from watchdog.observers import Observer as ObserverType

from src.services.event_service import EventService
from src.services.config_service import ConfigService

logger = structlog.get_logger()


@dataclass
class LocalFile:
    """Represents a local 3D print file."""
    file_id: str
    filename: str
    file_path: str
    file_size: int
    file_type: str
    modified_time: datetime
    watch_folder_path: str
    relative_path: str
    checksum: Optional[str] = None


class PrintFileHandler(FileSystemEventHandler):
    """File system event handler for 3D print files.

    Note: watchdog invokes these callbacks on its own observer thread,
    so all async work must be handed to the main event loop via
    FileWatcherService._schedule_from_thread().
    """

    SUPPORTED_EXTENSIONS = {'.stl', '.3mf', '.gcode', '.bgcode', '.obj', '.ply'}
    IGNORED_PATTERNS = {'*.tmp', '*.temp', '.*', '*~', '*.lock'}

    def __init__(self, file_watcher: 'FileWatcherService'):
        """Initialize file handler."""
        super().__init__()
        self.file_watcher = file_watcher
        self._debounce_events = {}  # File path -> event time for debouncing
        self._debounce_delay = 1.0  # 1 second debounce delay

    def should_process_file(self, file_path: str) -> bool:
        """Check if file should be processed based on extension and patterns."""
        path = Path(file_path)

        # Check extension
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return False

        # Check ignored patterns
        for pattern in self.IGNORED_PATTERNS:
            if pattern.startswith('*'):
                if path.name.endswith(pattern[1:]):
                    return False
            elif pattern.startswith('.'):
                if path.name.startswith('.'):
                    return False

        return True

    def _debounce_event(self, file_path: str) -> bool:
        """Debounce file events to avoid duplicate processing."""
        now = datetime.now()

        if file_path in self._debounce_events:
            last_event = self._debounce_events[file_path]
            if (now - last_event).total_seconds() < self._debounce_delay:
                return False  # Skip this event

        self._debounce_events[file_path] = now
        return True

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if not event.is_directory and self.should_process_file(event.src_path):
            if self._debounce_event(event.src_path):
                logger.info("New print file detected", file_path=event.src_path)
                self.file_watcher._schedule_from_thread(
                    self.file_watcher._handle_file_created(event.src_path)
                )

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if not event.is_directory and self.should_process_file(event.src_path):
            if self._debounce_event(event.src_path):
                logger.debug("Print file modified", file_path=event.src_path)
                self.file_watcher._schedule_from_thread(
                    self.file_watcher._handle_file_modified(event.src_path)
                )

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events."""
        if not event.is_directory and self.should_process_file(event.src_path):
            logger.info("Print file deleted", file_path=event.src_path)
            self.file_watcher._schedule_from_thread(
                self.file_watcher._handle_file_deleted(event.src_path)
            )

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file move/rename events."""
        if hasattr(event, 'dest_path'):
            if not event.is_directory and self.should_process_file(event.dest_path):
                logger.info("Print file moved",
                          old_path=event.src_path, new_path=event.dest_path)
                self.file_watcher._schedule_from_thread(
                    self.file_watcher._handle_file_moved(event.src_path, event.dest_path)
                )


class FileWatcherService:
    """Service for watching local folders for 3D print files."""

    # Seconds between size/mtime probes when waiting for a file to finish
    # being written, and the cap on how long to wait (large files copied
    # over the network can take minutes).
    STABILITY_CHECK_INTERVAL = 0.5
    STABILITY_TIMEOUT = 300.0

    # Rescan cadence when the watchdog observer could not be started
    # (fallback mode has no real-time events).
    FALLBACK_RESCAN_INTERVAL = 300.0

    def __init__(self, config_service: ConfigService, event_service: EventService, library_service=None):
        """Initialize file watcher service."""
        self.config_service = config_service
        self.event_service = event_service
        self.library_service = library_service  # Optional library integration

        self._observer = None
        self._watched_folders: Dict[str, Any] = {}  # folder_path -> watch descriptor
        self._local_files: Dict[str, LocalFile] = {}  # file_id -> LocalFile
        self._is_running = False
        self._lock = threading.Lock()

        # Event loop the service was started on; watchdog callbacks run on
        # the observer thread and must schedule coroutines onto this loop.
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # Paths currently being stabilized/ingested (suppresses duplicate
        # created/modified bursts while a copy is still in progress).
        self._processing_paths: Set[str] = set()

        self._fallback_scan_task: Optional[asyncio.Task] = None

        # Slicing services for auto-slice workflows; injected after startup
        # via set_slicing_services() (they are constructed after the watcher).
        self._slicing_queue = None
        self._slicer_service = None

        # Initialize file handler
        self._file_handler = PrintFileHandler(self)

    def set_slicing_services(self, slicing_queue, slicer_service) -> None:
        """Inject slicing services for the auto-slice workflow (Phase 7c)."""
        self._slicing_queue = slicing_queue
        self._slicer_service = slicer_service

    @staticmethod
    def _make_file_id(file_path: str) -> str:
        """Deterministic file ID for a path (stable across restarts)."""
        return f"local_{hashlib.sha1(file_path.encode('utf-8')).hexdigest()[:16]}"

    def _schedule_from_thread(self, coro: Coroutine) -> None:
        """Schedule a coroutine from any thread onto the service's event loop.

        Watchdog handlers run on the observer thread where no event loop is
        running, so plain asyncio.create_task() would raise RuntimeError.
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            loop = self._loop
            if loop is not None and not loop.is_closed():
                asyncio.run_coroutine_threadsafe(coro, loop)
            else:
                coro.close()
                logger.warning("Dropped file event: no event loop available")
            return
        # Already on a loop thread (e.g. direct calls in tests)
        asyncio.create_task(coro)

    async def start(self) -> None:
        """Start file watcher service."""
        if self._is_running:
            logger.warning("File watcher service already running")
            return

        logger.debug("FileWatcher debug", config_service_type=type(self.config_service).__name__, event_service_type=type(self.event_service).__name__)

        if not self.config_service.is_watch_folders_enabled():
            logger.info("Watch folders disabled in configuration")
            return

        self._loop = asyncio.get_running_loop()

        try:
            # Initialize observer with platform-specific handling
            # Use PollingObserver on Windows to avoid threading issues
            if sys.platform == "win32":
                self._observer = PollingObserver()
                logger.info("Using PollingObserver for Windows compatibility")
            else:
                self._observer = Observer()
                logger.debug("Using native Observer for file watching")

            # Add watch folders
            watch_folders = await self.config_service.get_watch_folders()
            recursive = self.config_service.is_recursive_watching_enabled()

            for folder_path in watch_folders:
                await self._add_watch_folder(folder_path, recursive)

            # Start observer
            try:
                # Start observer in the main thread (Windows compatible)
                # Watchdog Observer creates its own threads internally
                self._observer.start()
                self._is_running = True

                logger.info("File watcher service started",
                           watched_folders=len(self._watched_folders),
                           recursive=recursive,
                           observer_type=type(self._observer).__name__)
            except Exception as e:
                logger.warning("Failed to start watchdog observer, running in fallback mode",
                             error=str(e),
                             observer_type=type(self._observer).__name__ if self._observer else "None",
                             platform=sys.platform)
                # Fallback mode - file watcher API still works, but no real-time watching
                if self._observer:
                    try:
                        self._observer.stop()
                    except (RuntimeError, OSError) as stop_error:
                        logger.debug("Failed to stop observer during cleanup",
                                    error=str(stop_error))
                self._observer = None
                self._is_running = True  # Mark as running so API endpoints work

            # Perform initial scan
            await self._initial_scan()

            # Without an observer there are no real-time events, so poll
            # the folders periodically instead of silently going blind.
            if self._observer is None and self._watched_folders:
                self._fallback_scan_task = asyncio.create_task(self._fallback_rescan_loop())
                logger.info("Started periodic fallback rescan",
                           interval_seconds=self.FALLBACK_RESCAN_INTERVAL)

        except Exception as e:
            logger.error("Failed to start file watcher service", error=str(e))
            # Still mark as running in fallback mode
            self._is_running = True
            logger.info("File watcher running in fallback mode (API only, no real-time monitoring)")

    async def stop(self):
        """Stop file watcher service."""
        if not self._is_running:
            return

        try:
            if self._fallback_scan_task:
                self._fallback_scan_task.cancel()
                self._fallback_scan_task = None

            with self._lock:
                if self._observer:
                    try:
                        # Stop observer gracefully
                        self._observer.stop()

                        # Wait for observer thread to finish with timeout
                        if hasattr(self._observer, 'is_alive') and self._observer.is_alive():
                            # Run join in executor to avoid blocking async loop
                            loop = asyncio.get_running_loop()
                            await loop.run_in_executor(
                                None,
                                lambda: self._observer.join(timeout=5.0)
                            )

                            # Force stop if still alive
                            if hasattr(self._observer, 'is_alive') and self._observer.is_alive():
                                logger.warning("Observer thread did not stop gracefully, forcing termination")

                    except Exception as e:
                        logger.warning("Error stopping observer", error=str(e))
                    finally:
                        self._observer = None

                self._watched_folders.clear()
                self._processing_paths.clear()
                self._is_running = False

            logger.info("File watcher service stopped")

        except Exception as e:
            logger.error("Error stopping file watcher service", error=str(e))

    async def _add_watch_folder(self, folder_path: str, recursive: bool = True):
        """Add a folder to watch list."""
        try:
            path = Path(folder_path)

            # Validate folder
            validation = self.config_service.validate_watch_folder(str(path))
            if not validation["valid"]:
                logger.error("Cannot watch folder",
                           folder_path=folder_path, error=validation["error"])
                return

            # Always add to watched_folders dict, even in fallback mode
            # This ensures _initial_scan() can find folders to scan
            watch = None
            if self._observer:
                # Add to observer for real-time monitoring
                watch = self._observer.schedule(
                    self._file_handler,
                    str(path),
                    recursive=recursive
                )
                logger.info("Added watch folder with real-time monitoring",
                          folder_path=folder_path, recursive=recursive)
            else:
                logger.info("Added watch folder in fallback mode (no real-time monitoring)",
                          folder_path=folder_path, recursive=recursive)

            # Store folder info regardless of observer status
            self._watched_folders[folder_path] = {
                'watch': watch,
                'path': path,
                'recursive': recursive
            }

        except Exception as e:
            logger.error("Failed to add watch folder",
                       folder_path=folder_path, error=str(e))

    async def _initial_scan(self):
        """Perform initial scan of all watched folders."""
        logger.info("Starting initial scan of watch folders")

        for folder_path, folder_info in self._watched_folders.items():
            try:
                file_count = await self._scan_folder(folder_info['path'], folder_info['recursive'])
                await self._update_folder_stats(folder_path, file_count)

            except Exception as e:
                logger.error("Error during initial scan",
                           folder_path=folder_path, error=str(e))

        logger.info("Initial scan completed", discovered_files=len(self._local_files))

    async def _scan_folder(self, folder_path: Path, recursive: bool = True) -> int:
        """Scan a folder for existing 3D print files. Returns number of files found."""
        file_count = 0
        try:
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"

            for file_path in folder_path.glob(pattern):
                if file_path.is_file() and self._file_handler.should_process_file(str(file_path)):
                    await self._process_discovered_file(str(file_path))
                    file_count += 1

        except Exception as e:
            logger.error("Error scanning folder",
                       folder_path=str(folder_path), error=str(e))
        return file_count

    async def _update_folder_stats(self, folder_path: str, file_count: int) -> None:
        """Persist per-folder scan statistics (file count, last scan time)."""
        watch_folder_db = getattr(self.config_service, 'watch_folder_db', None)
        if watch_folder_db is None:
            return
        try:
            await watch_folder_db.update_folder_statistics(folder_path, file_count)
        except Exception as e:
            logger.debug("Could not update watch folder statistics",
                        folder_path=folder_path, error=str(e))

    async def rescan_folder(self, folder_path: str) -> Dict[str, Any]:
        """Rescan a single watch folder on demand.

        Raises:
            ValueError: If the folder is not currently being watched.
        """
        folder_info = self._watched_folders.get(folder_path)
        if not folder_info:
            raise ValueError(f"Folder is not being watched: {folder_path}")

        known_before = {
            f.file_path for f in self._local_files.values()
            if f.watch_folder_path == folder_path
        }

        file_count = await self._scan_folder(folder_info['path'], folder_info['recursive'])
        await self._update_folder_stats(folder_path, file_count)

        known_after = {
            f.file_path for f in self._local_files.values()
            if f.watch_folder_path == folder_path
        }

        result = {
            'folder_path': folder_path,
            'files_found': file_count,
            'new_files': len(known_after - known_before)
        }
        logger.info("Rescanned watch folder", **result)
        return result

    async def _fallback_rescan_loop(self) -> None:
        """Periodically rescan folders when real-time watching is unavailable."""
        while True:
            await asyncio.sleep(self.FALLBACK_RESCAN_INTERVAL)
            for folder_path, folder_info in list(self._watched_folders.items()):
                try:
                    file_count = await self._scan_folder(folder_info['path'], folder_info['recursive'])
                    await self._update_folder_stats(folder_path, file_count)
                except Exception as e:
                    logger.error("Error during fallback rescan",
                               folder_path=folder_path, error=str(e))

    async def _wait_for_file_stable(self, path: Path) -> bool:
        """Wait until a file's size/mtime stop changing (write finished).

        Protects against ingesting a file that is still being copied into
        the watch folder, which would store a truncated copy with a wrong
        checksum in the library.

        Returns True once stable, False if the file vanished or the
        stability timeout was exceeded.
        """
        try:
            last_stat = path.stat()
        except OSError:
            return False

        deadline = asyncio.get_running_loop().time() + self.STABILITY_TIMEOUT
        while True:
            await asyncio.sleep(self.STABILITY_CHECK_INTERVAL)
            try:
                current_stat = path.stat()
            except OSError:
                return False  # Deleted/moved while waiting

            if (current_stat.st_size, current_stat.st_mtime) == (last_stat.st_size, last_stat.st_mtime):
                return True

            last_stat = current_stat
            if asyncio.get_running_loop().time() > deadline:
                logger.warning("File did not stabilize within timeout, skipping",
                             file_path=str(path), timeout=self.STABILITY_TIMEOUT)
                return False

    async def _process_discovered_file(self, file_path: str):
        """Process a discovered file and add to local files and library."""
        try:
            path = Path(file_path)

            if not path.exists():
                return

            stat = path.stat()

            # Find which watch folder this file belongs to
            watch_folder_path = self._find_watch_folder_for_file(file_path)
            if not watch_folder_path:
                logger.warning("File not in any watch folder", file_path=file_path)
                return

            # Create relative path
            watch_path = Path(watch_folder_path)
            try:
                relative_path = path.relative_to(watch_path)
            except ValueError:
                relative_path = Path(path.name)

            # Generate deterministic file ID (stable across restarts)
            file_id = self._make_file_id(file_path)

            # Create LocalFile object
            local_file = LocalFile(
                file_id=file_id,
                filename=path.name,
                file_path=str(path),
                file_size=stat.st_size,
                file_type=path.suffix.lower(),
                modified_time=datetime.fromtimestamp(stat.st_mtime),
                watch_folder_path=watch_folder_path,
                relative_path=str(relative_path)
            )

            # Store file
            self._local_files[file_id] = local_file

            # Whether this content is new to the library (vs a duplicate of
            # an existing file); workflows only run for new content.
            is_new_library_file = False

            # Add to library if library service is available and enabled
            if self.library_service and self.library_service.enabled:
                try:
                    # Calculate checksum to check for duplicates
                    checksum = await self.library_service.calculate_checksum(path)
                    local_file.checksum = checksum

                    # Check if file already exists in library (by checksum)
                    existing_file = await self.library_service.get_file_by_checksum(checksum)

                    if existing_file:
                        # File already in library - skip copy but add watch folder as additional source
                        logger.info("File already in library, skipping copy",
                                   filename=path.name,
                                   checksum=checksum[:16],
                                   existing_filename=existing_file.get('filename'))

                        # Add watch folder as additional source
                        source_info = {
                            'type': 'watch_folder',
                            'folder_path': watch_folder_path,
                            'relative_path': str(relative_path),
                            'discovered_at': datetime.now().isoformat()
                        }

                        await self.library_service.add_file_source(checksum, source_info)

                        logger.debug("Added watch folder as additional source",
                                    filename=path.name,
                                    checksum=checksum[:16])
                    else:
                        # New file - copy to library
                        is_new_library_file = True
                        source_info = {
                            'type': 'watch_folder',
                            'folder_path': watch_folder_path,
                            'relative_path': str(relative_path),
                            'discovered_at': datetime.now().isoformat()
                        }

                        # Add file to library (will copy to library folder)
                        await self.library_service.add_file_to_library(
                            source_path=path,
                            source_info=source_info,
                            copy_file=True  # Copy, don't move (preserve original)
                        )

                        logger.info("Added new watch folder file to library",
                                   filename=path.name,
                                   checksum=checksum[:16],
                                   watch_folder=watch_folder_path)

                except Exception as e:
                    logger.error("Failed to add file to library",
                                filename=path.name,
                                error=str(e))
                    # Continue anyway - file still tracked locally

                # Apply per-folder processing rules (auto-tags, classification,
                # auto-slice for new content)
                if local_file.checksum:
                    await self._apply_folder_rules(local_file, is_new_file=is_new_library_file)

            # Emit file discovered event
            await self._emit_file_event('file_discovered', local_file)

            logger.debug("Processed local file",
                        filename=local_file.filename, file_id=file_id)

        except Exception as e:
            logger.error("Error processing discovered file",
                       file_path=file_path, error=str(e))

    async def _apply_folder_rules(self, local_file: LocalFile, is_new_file: bool = False) -> None:
        """Apply the watch folder's processing rules to an ingested file.

        Rules (configured per folder, migrations 038/039):
        - auto_tag: tag the file with its first-level subfolder name
          (e.g. ``vases/spiral.stl`` -> tag ``vases``).
        - classification: tag the file as ``business`` or ``private``.
        - auto_slice: queue new model files for slicing (never starts a print).
        """
        watch_folder_db = getattr(self.config_service, 'watch_folder_db', None)
        if watch_folder_db is None or not local_file.checksum:
            return

        try:
            folder = await watch_folder_db.get_watch_folder_by_path(local_file.watch_folder_path)
        except Exception as e:
            logger.debug("Could not load watch folder rules",
                        folder_path=local_file.watch_folder_path, error=str(e))
            return

        if folder is None:
            return

        tags = []

        if getattr(folder, 'auto_tag', False):
            parts = Path(local_file.relative_path).parts
            if len(parts) > 1:  # File sits in a subfolder
                tags.append(parts[0])

        classification = getattr(folder, 'classification', None)
        if classification in ('business', 'private'):
            tags.append(classification)

        for tag_name in tags:
            try:
                await self.library_service.assign_tag_by_name(local_file.checksum, tag_name)
            except Exception as e:
                logger.error("Failed to apply folder rule tag",
                            filename=local_file.filename, tag=tag_name, error=str(e))

        if tags:
            logger.info("Applied watch folder rules",
                       filename=local_file.filename,
                       folder_path=local_file.watch_folder_path,
                       tags=tags)

        # Auto-slice only fires the first time content enters the library,
        # so rescans and duplicate copies never re-queue slicing jobs.
        if is_new_file and getattr(folder, 'auto_slice', False):
            await self._maybe_auto_slice(local_file, folder)

    async def _maybe_auto_slice(self, local_file: LocalFile, folder) -> None:
        """Queue a slicing job for a newly ingested model file.

        Safety rule: watch-folder automation prepares gcode and notifies —
        it NEVER uploads to a printer or starts a print (auto_upload and
        auto_start are always False).
        """
        if self._slicing_queue is None or self._slicer_service is None:
            logger.debug("auto_slice enabled but slicing services not available",
                        folder_path=local_file.watch_folder_path)
            return

        profile_id = getattr(folder, 'default_profile_id', None)
        if not profile_id:
            logger.info("auto_slice enabled but no default profile configured, skipping",
                       folder_path=local_file.watch_folder_path,
                       filename=local_file.filename)
            return

        # Only slice source models (not gcode or already-sliced 3mf bundles)
        from src.services.file_role_classifier import classify_role, threemf_has_gcode
        has_gcode = None
        if local_file.file_type == '.3mf':
            has_gcode = threemf_has_gcode(Path(local_file.file_path))
        if classify_role(local_file.file_type, has_gcode) != 'model':
            return

        try:
            slicers = await self._slicer_service.list_slicers(available_only=True)
            if not slicers:
                logger.warning("auto_slice: no available slicer configured, skipping",
                             filename=local_file.filename)
                return

            from src.models.slicer import SlicingJobRequest
            request = SlicingJobRequest(
                file_checksum=local_file.checksum,
                slicer_id=slicers[0].id,
                profile_id=profile_id,
                target_printer_id=getattr(folder, 'default_printer_id', None),
                auto_upload=False,
                auto_start=False  # Watch-folder automation never starts prints
            )
            job = await self._slicing_queue.create_job(request)

            await self.event_service.emit_event('watch_folder.auto_slice_queued', {
                'job_id': job.id,
                'filename': local_file.filename,
                'checksum': local_file.checksum,
                'folder_path': local_file.watch_folder_path,
                'profile_id': profile_id,
                'target_printer_id': getattr(folder, 'default_printer_id', None)
            })

            logger.info("Queued auto-slice for watch folder file",
                       filename=local_file.filename,
                       job_id=job.id,
                       profile_id=profile_id)

        except Exception as e:
            logger.error("Failed to queue auto-slice",
                        filename=local_file.filename, error=str(e))

    def _find_watch_folder_for_file(self, file_path: str) -> Optional[str]:
        """Find which watch folder contains the given file."""
        file_path_obj = Path(file_path)

        for watch_folder_path in self._watched_folders.keys():
            watch_path = Path(watch_folder_path)

            try:
                file_path_obj.relative_to(watch_path)
                return watch_folder_path
            except ValueError:
                continue

        return None

    def _find_local_file_by_path(self, file_path: str) -> Optional[LocalFile]:
        """Find a tracked local file by its absolute path."""
        for local_file in self._local_files.values():
            if local_file.file_path == file_path:
                return local_file
        return None

    async def _remove_library_source(self, checksum: Optional[str], watch_folder_path: str) -> None:
        """Remove a watch-folder source from a library file, if possible."""
        if not checksum or not self.library_service or not self.library_service.enabled:
            return
        try:
            await self.library_service.remove_file_source(
                checksum, 'watch_folder', watch_folder_path
            )
        except Exception as e:
            logger.error("Failed to remove watch folder source from library",
                        checksum=checksum[:16], folder_path=watch_folder_path,
                        error=str(e))

    async def _handle_file_created(self, file_path: str):
        """Handle file creation event."""
        if file_path in self._processing_paths:
            return
        self._processing_paths.add(file_path)
        try:
            if not await self._wait_for_file_stable(Path(file_path)):
                logger.debug("File vanished or never stabilized, skipping",
                            file_path=file_path)
                return
            await self._process_discovered_file(file_path)
        finally:
            self._processing_paths.discard(file_path)

    async def _handle_file_modified(self, file_path: str):
        """Handle file modification event."""
        if file_path in self._processing_paths:
            return
        self._processing_paths.add(file_path)
        try:
            if not await self._wait_for_file_stable(Path(file_path)):
                return

            existing = self._find_local_file_by_path(file_path)
            old_checksum = existing.checksum if existing else None

            # Update in-memory file information
            if existing:
                try:
                    path = Path(file_path)
                    if path.exists():
                        stat = path.stat()
                        existing.file_size = stat.st_size
                        existing.modified_time = datetime.fromtimestamp(stat.st_mtime)

                        await self._emit_file_event('file_modified', existing)

                        logger.debug("Updated local file",
                                   filename=existing.filename)
                except Exception as e:
                    logger.error("Error updating file info",
                               file_path=file_path, error=str(e))

            # Re-ingest so changed content reaches the library
            await self._process_discovered_file(file_path)

            # If the content changed, the old library record no longer has
            # this path as a valid source
            updated = self._find_local_file_by_path(file_path)
            new_checksum = updated.checksum if updated else None
            if old_checksum and new_checksum and old_checksum != new_checksum and updated:
                await self._remove_library_source(old_checksum, updated.watch_folder_path)
        finally:
            self._processing_paths.discard(file_path)

    async def _handle_file_deleted(self, file_path: str):
        """Handle file deletion event."""
        # Find and remove file
        for file_id, local_file in list(self._local_files.items()):
            if local_file.file_path == file_path:
                del self._local_files[file_id]

                await self._emit_file_event('file_deleted', local_file)

                # The library keeps its copy, but this watch folder is no
                # longer a valid source for it
                await self._remove_library_source(
                    local_file.checksum, local_file.watch_folder_path
                )

                logger.debug("Removed local file",
                           filename=local_file.filename, file_id=file_id)
                break

    async def _handle_file_moved(self, old_path: str, new_path: str):
        """Handle file move/rename event."""
        # Update file path in local files
        for local_file in self._local_files.values():
            if local_file.file_path == old_path:
                old_watch_folder = local_file.watch_folder_path

                # Update file information
                path = Path(new_path)
                local_file.file_path = str(path)
                local_file.filename = path.name

                # Update relative path
                watch_folder_path = self._find_watch_folder_for_file(new_path)
                if watch_folder_path:
                    watch_path = Path(watch_folder_path)
                    local_file.watch_folder_path = watch_folder_path
                    try:
                        relative_path = path.relative_to(watch_path)
                        local_file.relative_path = str(relative_path)
                    except ValueError:
                        local_file.relative_path = path.name

                await self._emit_file_event('file_moved', local_file)

                # Moved to a different watch folder: swap the library source
                if watch_folder_path and watch_folder_path != old_watch_folder and local_file.checksum:
                    await self._remove_library_source(local_file.checksum, old_watch_folder)
                    if self.library_service and self.library_service.enabled:
                        try:
                            await self.library_service.add_file_source(local_file.checksum, {
                                'type': 'watch_folder',
                                'folder_path': watch_folder_path,
                                'relative_path': local_file.relative_path,
                                'discovered_at': datetime.now().isoformat()
                            })
                        except Exception as e:
                            logger.error("Failed to add new watch folder source after move",
                                        checksum=local_file.checksum[:16], error=str(e))

                logger.debug("Updated file path",
                           old_path=old_path, new_path=new_path,
                           filename=local_file.filename)
                break

    async def _emit_file_event(self, event_type: str, local_file: LocalFile):
        """Emit file event through event service."""
        try:
            event_data = {
                'event_type': event_type,
                'file_id': local_file.file_id,
                'filename': local_file.filename,
                'file_path': local_file.file_path,
                'file_size': local_file.file_size,
                'file_type': local_file.file_type,
                'modified_time': local_file.modified_time.isoformat(),
                'watch_folder_path': local_file.watch_folder_path,
                'relative_path': local_file.relative_path,
                'checksum': local_file.checksum,
                'source': 'local_watch'
            }

            await self.event_service.emit_event('file_watcher', event_data)

        except Exception as e:
            logger.error("Error emitting file event",
                       event_type=event_type, error=str(e))

    def get_local_files(self) -> List[Dict[str, Any]]:
        """Get list of all discovered local files."""
        result = []

        for local_file in self._local_files.values():
            result.append({
                'id': local_file.file_id,
                'filename': local_file.filename,
                'file_path': local_file.file_path,
                'file_size': local_file.file_size,
                'file_type': local_file.file_type,
                'modified_time': local_file.modified_time.isoformat(),
                'watch_folder_path': local_file.watch_folder_path,
                'relative_path': local_file.relative_path,
                'checksum': local_file.checksum,
                'status': 'local',
                'source': 'local_watch'
            })

        return result

    def get_watch_status(self) -> Dict[str, Any]:
        """Get file watcher service status."""
        return {
            'is_running': self._is_running,
            'realtime_monitoring': self._observer is not None,
            'watched_folders': list(self._watched_folders.keys()),
            'local_files_count': len(self._local_files),
            'supported_extensions': list(self._file_handler.SUPPORTED_EXTENSIONS)
        }

    async def reload_watch_folders(self) -> None:
        """Reload watch folders from configuration."""
        if not self._is_running:
            logger.warning("Cannot reload: file watcher not running")
            return

        try:
            # Stop current watching
            await self.stop()

            # Restart with new configuration
            await self.start()

            logger.info("Reloaded watch folders configuration")

        except Exception as e:
            logger.error("Error reloading watch folders", error=str(e))
            raise
