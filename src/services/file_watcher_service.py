"""
File Watcher Service for monitoring local folders for 3D print files.
Implements cross-platform file system monitoring using watchdog.
"""

import os
import asyncio
import threading
from typing import Dict, List, Set, Optional, Callable, Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

import structlog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from services.event_service import EventService
from services.config_service import ConfigService

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


class PrintFileHandler(FileSystemEventHandler):
    """File system event handler for 3D print files."""
    
    SUPPORTED_EXTENSIONS = {'.stl', '.3mf', '.gcode', '.obj', '.ply'}
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
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation events."""
        if not event.is_directory and self.should_process_file(event.src_path):
            if self._debounce_event(event.src_path):
                logger.info("New print file detected", file_path=event.src_path)
                asyncio.create_task(self.file_watcher._handle_file_created(event.src_path))
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if not event.is_directory and self.should_process_file(event.src_path):
            if self._debounce_event(event.src_path):
                logger.debug("Print file modified", file_path=event.src_path)
                asyncio.create_task(self.file_watcher._handle_file_modified(event.src_path))
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion events."""
        if not event.is_directory and self.should_process_file(event.src_path):
            logger.info("Print file deleted", file_path=event.src_path)
            asyncio.create_task(self.file_watcher._handle_file_deleted(event.src_path))
    
    def on_moved(self, event: FileSystemEvent):
        """Handle file move/rename events."""
        if hasattr(event, 'dest_path'):
            if not event.is_directory and self.should_process_file(event.dest_path):
                logger.info("Print file moved", 
                          old_path=event.src_path, new_path=event.dest_path)
                asyncio.create_task(
                    self.file_watcher._handle_file_moved(event.src_path, event.dest_path)
                )


class FileWatcherService:
    """Service for watching local folders for 3D print files."""
    
    def __init__(self, config_service: ConfigService, event_service: EventService):
        """Initialize file watcher service."""
        self.config_service = config_service
        self.event_service = event_service
        
        self._observer: Optional[Observer] = None
        self._watched_folders: Dict[str, Any] = {}  # folder_path -> watch descriptor
        self._local_files: Dict[str, LocalFile] = {}  # file_id -> LocalFile
        self._is_running = False
        self._lock = threading.Lock()
        
        # Initialize file handler
        self._file_handler = PrintFileHandler(self)
    
    async def start(self):
        """Start file watcher service."""
        if self._is_running:
            logger.warning("File watcher service already running")
            return
        
        if not self.config_service.is_watch_folders_enabled():
            logger.info("Watch folders disabled in configuration")
            return
        
        try:
            # Initialize observer
            self._observer = Observer()
            
            # Add watch folders
            watch_folders = self.config_service.get_watch_folders()
            recursive = self.config_service.is_recursive_watching_enabled()
            
            for folder_path in watch_folders:
                await self._add_watch_folder(folder_path, recursive)
            
            # Start observer
            self._observer.start()
            self._is_running = True
            
            logger.info("File watcher service started", 
                       watched_folders=len(self._watched_folders),
                       recursive=recursive)
            
            # Perform initial scan
            await self._initial_scan()
            
        except Exception as e:
            logger.error("Failed to start file watcher service", error=str(e))
            await self.stop()
            raise
    
    async def stop(self):
        """Stop file watcher service."""
        if not self._is_running:
            return
        
        try:
            with self._lock:
                if self._observer:
                    self._observer.stop()
                    self._observer.join(timeout=5.0)
                    self._observer = None
                
                self._watched_folders.clear()
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
            
            # Add to observer
            if self._observer:
                watch = self._observer.schedule(
                    self._file_handler, 
                    str(path), 
                    recursive=recursive
                )
                
                self._watched_folders[folder_path] = {
                    'watch': watch,
                    'path': path,
                    'recursive': recursive
                }
                
                logger.info("Added watch folder", 
                          folder_path=folder_path, recursive=recursive)
        
        except Exception as e:
            logger.error("Failed to add watch folder", 
                       folder_path=folder_path, error=str(e))
    
    async def _initial_scan(self):
        """Perform initial scan of all watched folders."""
        logger.info("Starting initial scan of watch folders")
        
        for folder_path, folder_info in self._watched_folders.items():
            try:
                await self._scan_folder(folder_info['path'], folder_info['recursive'])
                
            except Exception as e:
                logger.error("Error during initial scan", 
                           folder_path=folder_path, error=str(e))
        
        logger.info("Initial scan completed", discovered_files=len(self._local_files))
    
    async def _scan_folder(self, folder_path: Path, recursive: bool = True):
        """Scan a folder for existing 3D print files."""
        try:
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for file_path in folder_path.glob(pattern):
                if file_path.is_file() and self._file_handler.should_process_file(str(file_path)):
                    await self._process_discovered_file(str(file_path))
                    
        except Exception as e:
            logger.error("Error scanning folder", 
                       folder_path=str(folder_path), error=str(e))
    
    async def _process_discovered_file(self, file_path: str):
        """Process a discovered file and add to local files."""
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
            
            # Generate file ID
            file_id = f"local_{abs(hash(file_path))}"
            
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
            
            # Emit file discovered event
            await self._emit_file_event('file_discovered', local_file)
            
            logger.debug("Processed local file", 
                        filename=local_file.filename, file_id=file_id)
                        
        except Exception as e:
            logger.error("Error processing discovered file", 
                       file_path=file_path, error=str(e))
    
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
    
    async def _handle_file_created(self, file_path: str):
        """Handle file creation event."""
        await self._process_discovered_file(file_path)
    
    async def _handle_file_modified(self, file_path: str):
        """Handle file modification event."""
        # Find existing file
        for local_file in self._local_files.values():
            if local_file.file_path == file_path:
                # Update file information
                try:
                    path = Path(file_path)
                    if path.exists():
                        stat = path.stat()
                        local_file.file_size = stat.st_size
                        local_file.modified_time = datetime.fromtimestamp(stat.st_mtime)
                        
                        await self._emit_file_event('file_modified', local_file)
                        
                        logger.debug("Updated local file", 
                                   filename=local_file.filename)
                except Exception as e:
                    logger.error("Error updating file info", 
                               file_path=file_path, error=str(e))
                break
    
    async def _handle_file_deleted(self, file_path: str):
        """Handle file deletion event."""
        # Find and remove file
        for file_id, local_file in list(self._local_files.items()):
            if local_file.file_path == file_path:
                del self._local_files[file_id]
                
                await self._emit_file_event('file_deleted', local_file)
                
                logger.debug("Removed local file", 
                           filename=local_file.filename, file_id=file_id)
                break
    
    async def _handle_file_moved(self, old_path: str, new_path: str):
        """Handle file move/rename event."""
        # Update file path in local files
        for local_file in self._local_files.values():
            if local_file.file_path == old_path:
                # Update file information
                path = Path(new_path)
                local_file.file_path = str(path)
                local_file.filename = path.name
                
                # Update relative path
                watch_folder_path = self._find_watch_folder_for_file(new_path)
                if watch_folder_path:
                    watch_path = Path(watch_folder_path)
                    try:
                        relative_path = path.relative_to(watch_path)
                        local_file.relative_path = str(relative_path)
                    except ValueError:
                        local_file.relative_path = path.name
                
                await self._emit_file_event('file_moved', local_file)
                
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
                'status': 'local',
                'source': 'local_watch'
            })
        
        return result
    
    def get_watch_status(self) -> Dict[str, Any]:
        """Get file watcher service status."""
        return {
            'is_running': self._is_running,
            'watched_folders': list(self._watched_folders.keys()),
            'local_files_count': len(self._local_files),
            'supported_extensions': list(self._file_handler.SUPPORTED_EXTENSIONS)
        }
    
    async def reload_watch_folders(self):
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