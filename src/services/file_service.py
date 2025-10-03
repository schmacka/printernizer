"""
File service for managing 3D files and downloads.
Handles both printer files (via APIs) and local files (via folder watching).
"""
from typing import List, Dict, Any, Optional
import structlog
import asyncio
import os
from pathlib import Path
from datetime import datetime
from src.database.database import Database
from src.services.event_service import EventService
from src.services.file_watcher_service import FileWatcherService
from src.services.bambu_parser import BambuParser
from src.services.preview_render_service import PreviewRenderService
from src.utils.exceptions import NotFoundError

logger = structlog.get_logger()


class FileService:
    """Service for managing 3D files and downloads."""

    def __init__(self, database: Database, event_service: EventService,
                 file_watcher: Optional[FileWatcherService] = None,
                 printer_service=None, config_service=None, library_service=None):
        """Initialize file service."""
        self.database = database
        self.event_service = event_service
        self.file_watcher = file_watcher
        self.printer_service = printer_service
        self.config_service = config_service
        self.library_service = library_service  # Optional library integration
        self.bambu_parser = BambuParser()
        self.preview_render_service = PreviewRenderService()
        self.download_progress = {}
        self.download_status = {}

        # Thumbnail processing status tracking
        self.thumbnail_processing_log = []  # List of recent thumbnail processing attempts
        self.max_log_entries = 50  # Keep last 50 attempts
        
    async def get_files(self, printer_id: Optional[str] = None,
                       include_local: bool = True,
                       status: Optional[str] = None,
                       source: Optional[str] = None,
                       has_thumbnail: Optional[bool] = None,
                       search: Optional[str] = None,
                       limit: Optional[int] = None,
                       order_by: Optional[str] = "created_at",
                       order_dir: Optional[str] = "desc",
                       page: Optional[int] = 1) -> List[Dict[str, Any]]:
        """Get list of available files from printers and local folders."""
        files = []
        
        # Get printer files from database
        try:
            printer_files = await self.database.list_files(
                printer_id=printer_id if printer_id != 'local' else None,
                source='printer'
            )

            # Get printer information for enriching file data
            printer_info_map = {}
            if self.printer_service:
                try:
                    printers = await self.printer_service.list_printers()
                    # list_printers() returns Printer objects, convert to dict for mapping
                    printer_info_map = {p.id: p for p in printers}
                except Exception as e:
                    logger.warning("Could not fetch printer information for file enrichment", error=str(e))

            # Convert database rows to file format and enrich with printer info
            for file_data in printer_files:
                file_dict = dict(file_data)
                file_dict['source'] = 'printer'

                # Add printer name and type information
                printer_id_val = file_dict.get('printer_id')
                if printer_id_val and printer_id_val in printer_info_map:
                    printer_info = printer_info_map[printer_id_val]
                    # printer_info is a Printer Pydantic model, access attributes directly
                    printer_name = printer_info.name
                    printer_type = printer_info.type.value if hasattr(printer_info.type, 'value') else str(printer_info.type)

                    file_dict['printer_name'] = printer_name
                    file_dict['printer_type'] = printer_type
                    file_dict['source_display'] = f"{printer_name} ({printer_type})"
                else:
                    file_dict['printer_name'] = 'Unknown'
                    file_dict['printer_type'] = 'unknown'
                    file_dict['source_display'] = 'Unknown Printer'

                files.append(file_dict)

            logger.debug("Retrieved printer files from database", count=len(printer_files))
            
        except Exception as e:
            logger.error("Error retrieving printer files from database", error=str(e))
        
        # Get local files from file watcher if enabled and available
        if include_local and self.file_watcher:
            try:
                local_files = self.file_watcher.get_local_files()

                # Enrich local files with source display information
                for local_file in local_files:
                    if local_file.get('source') == 'local_watch':
                        local_file['source_display'] = 'Local Watch Folder'
                        local_file['printer_name'] = None
                        local_file['printer_type'] = None

                files.extend(local_files)
                logger.debug("Retrieved local files", count=len(local_files))
            except Exception as e:
                logger.error("Error retrieving local files", error=str(e))
        
        # Apply filters
        if printer_id and printer_id != 'local':
            files = [f for f in files if f.get('printer_id') == printer_id or f.get('source') == 'local_watch']

        if status:
            files = [f for f in files if f.get('status') == status]

        if source:
            files = [f for f in files if f.get('source') == source]

        if has_thumbnail is not None:
            files = [f for f in files if bool(f.get('has_thumbnail', False)) == has_thumbnail]

        # Apply search filter (case-insensitive partial match on filename)
        if search:
            search_lower = search.lower()
            files = [f for f in files if search_lower in f.get('filename', '').lower()]

        # Sort files
        reverse_order = order_dir.lower() == 'desc'
        if order_by == 'downloaded_at':
            files = sorted(files, key=lambda x: x.get('downloaded_at') or x.get('created_at') or '', reverse=reverse_order)
        elif order_by == 'created_at':
            files = sorted(files, key=lambda x: x.get('created_at', ''), reverse=reverse_order)
        elif order_by == 'filename':
            files = sorted(files, key=lambda x: x.get('filename', ''), reverse=reverse_order)
        elif order_by == 'file_size':
            files = sorted(files, key=lambda x: x.get('file_size', 0), reverse=reverse_order)

        # Apply pagination
        if limit:
            start_idx = (page - 1) * limit if page > 1 else 0
            files = files[start_idx:start_idx + limit]

        return files
        
    async def get_printer_files(self, printer_id: str) -> List[Dict[str, Any]]:
        """Get files available on specific printer."""
        try:
            if not self.printer_service:
                logger.warning("Printer service not available for file discovery")
                return []
            
            # Get files directly from printer via printer service
            printer_files = await self.printer_service.get_printer_files(printer_id)
            
            # Store/update files in database
            stored_files = []
            for file_info in printer_files:
                file_data = {
                    'id': f"{printer_id}_{file_info['filename']}",
                    'printer_id': printer_id,
                    'filename': file_info['filename'],
                    'display_name': file_info['filename'],
                    'file_size': file_info.get('size', 0),
                    'file_type': self._get_file_type(file_info['filename']),
                    'status': 'available',
                    'source': 'printer',
                    'metadata': None,
                    'modified_time': file_info.get('modified')
                }
                
                # Store in database
                await self.database.create_file(file_data)
                stored_files.append(file_data)
                
            logger.info("Discovered printer files", printer_id=printer_id, count=len(stored_files))
            return stored_files
            
        except Exception as e:
            logger.error("Failed to discover printer files", printer_id=printer_id, error=str(e))
            # Fallback to database files
            return await self.database.list_files(printer_id=printer_id, source='printer')
        
    async def download_file(self, printer_id: str, filename: str, 
                           destination_path: Optional[str] = None) -> Dict[str, Any]:
        """Download file from printer."""
        try:
            if not self.printer_service:
                raise ValueError("Printer service not available")
            
            file_id = f"{printer_id}_{filename}"
            
            # Set up progress tracking
            self.download_progress[file_id] = 0
            self.download_status[file_id] = "starting"
            
            # Create destination path if not provided
            if not destination_path:
                # Get download path from configuration
                base_download_path = "downloads"  # fallback default
                if self.config_service:
                    try:
                        base_download_path = self.config_service.settings.downloads_path
                    except Exception as e:
                        logger.warning("Failed to get downloads path from config, using default",
                                     error=str(e))

                downloads_dir = Path(base_download_path) / printer_id
                try:
                    downloads_dir.mkdir(parents=True, exist_ok=True)
                    logger.debug("Created downloads directory", path=str(downloads_dir),
                                base_path=base_download_path)
                except Exception as e:
                    logger.error("Failed to create downloads directory",
                                path=str(downloads_dir), error=str(e))
                    raise ValueError(f"Cannot create downloads directory: {e}")
                destination_path = str(downloads_dir / filename)
            
            logger.info("Starting file download", printer_id=printer_id, filename=filename, 
                       destination=destination_path)
            
            # Update status to downloading
            self.download_status[file_id] = "downloading"
            
            # Perform actual download via printer service
            success = await self.printer_service.download_printer_file(
                printer_id, filename, destination_path
            )
            
            if success:
                try:
                    # Update database with download info
                    await self.database.update_file(file_id, {
                        'status': 'downloaded',
                        'file_path': destination_path,
                        'downloaded_at': datetime.now().isoformat(),
                        'download_progress': 100
                    })

                    self.download_progress[file_id] = 100
                    self.download_status[file_id] = "completed"

                    # Verify the file was actually downloaded
                    if not Path(destination_path).exists():
                        logger.error("Download reported success but file doesn't exist",
                                   file_id=file_id, destination=destination_path)
                        self.download_status[file_id] = "failed"
                        return {
                            "status": "error",
                            "message": "Download completed but file not found",
                            "local_path": None
                        }

                    file_size = Path(destination_path).stat().st_size
                    logger.info("File download verified",
                               printer_id=printer_id, filename=filename,
                               destination=destination_path, size=file_size)

                    # Process thumbnails for the downloaded file
                    logger.info("Processing thumbnails for downloaded file",
                               file_id=file_id, destination=destination_path)

                    # Process thumbnails asynchronously to not block download completion
                    asyncio.create_task(self.process_file_thumbnails(destination_path, file_id))

                    # Add to library if library service is available and enabled
                    if self.library_service and self.library_service.enabled:
                        try:
                            # Get printer info
                            printer = await self.printer_service.get_printer(printer_id)
                            printer_name = printer.get('name', 'unknown') if printer else 'unknown'

                            source_info = {
                                'type': 'printer',
                                'printer_id': printer_id,
                                'printer_name': printer_name,
                                'original_filename': filename,
                                'original_path': f'/cache/{filename}',  # Typical printer path
                                'discovered_at': datetime.now().isoformat()
                            }

                            # Add file to library (will copy to library folder)
                            await self.library_service.add_file_to_library(
                                source_path=Path(destination_path),
                                source_info=source_info,
                                copy_file=True  # Copy, preserve downloads folder
                            )

                            logger.info("Added downloaded file to library",
                                       filename=filename,
                                       printer_id=printer_id,
                                       printer_name=printer_name)

                        except Exception as e:
                            logger.error("Failed to add downloaded file to library",
                                        filename=filename,
                                        printer_id=printer_id,
                                        error=str(e))
                            # Continue anyway - download still successful

                    # Emit download complete event
                    try:
                        await self.event_service.emit_event("file_download_complete", {
                            "printer_id": printer_id,
                            "filename": filename,
                            "file_id": file_id,
                            "local_path": destination_path
                        })
                    except Exception as e:
                        logger.warning("Failed to emit download complete event", error=str(e))

                    logger.info("File download completed successfully",
                               printer_id=printer_id, filename=filename, size=file_size)

                    return {
                        "status": "success",
                        "message": "File downloaded successfully",
                        "local_path": destination_path,
                        "file_id": file_id,
                        "file_size": file_size
                    }
                except Exception as e:
                    logger.error("Error in download completion processing",
                                printer_id=printer_id, filename=filename, error=str(e))
                    self.download_status[file_id] = "failed"
                    return {
                        "status": "error",
                        "message": f"Download post-processing failed: {str(e)}",
                        "local_path": destination_path
                    }
            else:
                self.download_status[file_id] = "failed"
                return {
                    "status": "error",
                    "message": "Download failed",
                    "local_path": None
                }
                
        except Exception as e:
            logger.error("File download failed", printer_id=printer_id, filename=filename, error=str(e))
            if file_id in self.download_status:
                self.download_status[file_id] = "failed"
            return {
                "status": "error",
                "message": str(e),
                "local_path": None
            }
        
    async def get_download_status(self, file_id: str) -> Dict[str, Any]:
        """Get download status of a file."""
        try:
            # Check in-memory status first
            if file_id in self.download_status:
                return {
                    "file_id": file_id,
                    "status": self.download_status[file_id],
                    "progress": self.download_progress.get(file_id, 0)
                }
            
            # Check database for historical status
            file_data = await self.database.list_files()
            for file_info in file_data:
                if file_info['id'] == file_id:
                    return {
                        "file_id": file_id,
                        "status": file_info.get('status', 'unknown'),
                        "progress": file_info.get('download_progress', 0),
                        "downloaded_at": file_info.get('downloaded_at'),
                        "local_path": file_info.get('file_path')
                    }
            
            # File not found
            return {
                "file_id": file_id,
                "status": "not_found",
                "progress": 0
            }
            
        except Exception as e:
            logger.error("Failed to get download status", file_id=file_id, error=str(e))
            return {
                "file_id": file_id,
                "status": "error",
                "progress": 0,
                "error": str(e)
            }
        
    async def get_local_files(self) -> List[Dict[str, Any]]:
        """Get list of local files only."""
        if not self.file_watcher:
            return []
        
        try:
            return self.file_watcher.get_local_files()
        except Exception as e:
            logger.error("Error retrieving local files", error=str(e))
            return []
    
    async def scan_local_files(self) -> List[Dict[str, Any]]:
        """Scan local watch folders for new files (called by file discovery task)."""
        if not self.file_watcher:
            return []
        
        try:
            # Get current local files from file watcher
            current_files = self.file_watcher.get_local_files()
            
            # For file discovery task, we want to return files that may be new
            # This is the same as get_local_files for now, but could be enhanced
            # to track which files are "new" since last discovery
            logger.debug("Scanned local files", count=len(current_files))
            return current_files
        except Exception as e:
            logger.error("Error scanning local files", error=str(e))
            return []
    
    async def get_watch_status(self) -> Dict[str, Any]:
        """Get file watcher status."""
        if not self.file_watcher:
            return {"enabled": False, "message": "File watcher not available"}
        
        try:
            return self.file_watcher.get_watch_status()
        except Exception as e:
            logger.error("Error getting watch status", error=str(e))
            return {"enabled": False, "error": str(e)}
    
    async def reload_watch_folders(self) -> Dict[str, Any]:
        """Reload watch folders configuration."""
        if not self.file_watcher:
            return {"success": False, "message": "File watcher not available"}
        
        try:
            await self.file_watcher.reload_watch_folders()
            return {"success": True, "message": "Watch folders reloaded successfully"}
        except Exception as e:
            logger.error("Error reloading watch folders", error=str(e))
            return {"success": False, "error": str(e)}

    async def get_file_statistics(self) -> Dict[str, Any]:
        """Get file management statistics."""
        try:
            # Get all files without pagination
            files = await self.get_files(limit=None)

            # Calculate statistics
            total_files = len(files)

            # Separate by source
            local_files = [f for f in files if f.get('source') == 'local_watch']
            printer_files = [f for f in files if f.get('source') == 'printer']

            # Calculate total size
            total_size = sum(f.get('file_size', 0) or 0 for f in files)

            # Count by status for PRINTER files
            # available: Files on printer that haven't been downloaded yet
            available_count = len([f for f in printer_files if f.get('status') == 'available'])

            # downloaded: Files that were downloaded from printer to local storage
            downloaded_count = len([f for f in printer_files if f.get('status') == 'downloaded'])

            # failed: Download attempts that failed
            failed_count = len([f for f in printer_files if f.get('status') == 'failed'])

            # local: Files found in watch folders (local_watch source)
            local_count = len(local_files)

            # Calculate download success rate
            total_download_attempts = downloaded_count + failed_count
            download_success_rate = downloaded_count / total_download_attempts if total_download_attempts > 0 else 1.0

            logger.info("File statistics calculated",
                        total=total_files,
                        available=available_count,
                        downloaded=downloaded_count,
                        local_files_count=len(local_files),
                        local_count=local_count,
                        printer_files_count=len(printer_files),
                        failed=failed_count,
                        total_size_bytes=total_size)

            # Log some sample files for debugging
            if local_files:
                logger.debug("Sample local files",
                           sample_count=min(5, len(local_files)),
                           samples=[{
                               'id': f.get('id'),
                               'filename': f.get('filename'),
                               'source': f.get('source'),
                               'status': f.get('status')
                           } for f in local_files[:5]])

            return {
                "total_files": total_files,
                "local_files": len(local_files),
                "printer_files": len(printer_files),
                "available_count": available_count,
                "downloaded_count": downloaded_count,
                "failed_count": failed_count,
                "local_count": local_count,
                "total_size": total_size,
                "download_success_rate": download_success_rate
            }

        except Exception as e:
            logger.error("Error calculating file statistics", error=str(e), exc_info=True)
            return {
                "total_files": 0,
                "local_files": 0,
                "printer_files": 0,
                "available_count": 0,
                "downloaded_count": 0,
                "failed_count": 0,
                "local_count": 0,
                "total_size": 0,
                "download_success_rate": 0.0
            }
    
    def _get_file_type(self, filename: str) -> str:
        """Get file type from filename extension."""
        ext = Path(filename).suffix.lower()
        type_map = {
            '.stl': 'stl',
            '.3mf': '3mf',
            '.obj': 'obj',
            '.gcode': 'gcode',
            '.bgcode': 'bgcode',
            '.ply': 'ply'
        }
        return type_map.get(ext, 'unknown')
    
    async def sync_printer_files(self, printer_id: str) -> Dict[str, Any]:
        """Synchronize files from a specific printer."""
        try:
            logger.info("Starting file sync for printer", printer_id=printer_id)
            
            # Discover current files on printer
            current_files = await self.get_printer_files(printer_id)
            
            # Get existing files in database for this printer
            existing_files = await self.database.list_files(printer_id=printer_id, source='printer')
            existing_filenames = {f['filename'] for f in existing_files}
            current_filenames = {f['filename'] for f in current_files}
            
            # Find files that no longer exist on printer
            removed_files = existing_filenames - current_filenames
            added_files = current_filenames - existing_filenames
            
            # Remove files that no longer exist
            removed_count = 0
            for file_data in existing_files:
                if file_data['filename'] in removed_files:
                    # Mark as unavailable rather than deleting
                    await self.database.update_file(file_data['id'], {
                        'status': 'unavailable'
                    })
                    removed_count += 1
            
            logger.info("File sync completed", 
                       printer_id=printer_id, 
                       total_files=len(current_files),
                       added_files=len(added_files),
                       removed_files=removed_count)
            
            return {
                "success": True,
                "total_files": len(current_files),
                "added_files": len(added_files),
                "removed_files": removed_count,
                "sync_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("File sync failed", printer_id=printer_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "sync_time": datetime.now().isoformat()
            }
    
    async def discover_printer_files(self, printer_id: str) -> List[Dict[str, Any]]:
        """
        Discover files on a specific printer for the background discovery task.

        This method is called by the background file discovery task every 5 minutes.
        It discovers files on the printer and stores them in the database.

        Args:
            printer_id: The ID of the printer to discover files for

        Returns:
            List of file info dictionaries with filename, file_size, file_type
        """
        try:
            logger.info("Starting file discovery for printer", printer_id=printer_id)

            # Use existing get_printer_files method which discovers and stores files
            stored_files = await self.get_printer_files(printer_id)

            # Convert to format expected by background task
            discovered_files = []
            for file_data in stored_files:
                discovered_files.append({
                    'filename': file_data['filename'],
                    'file_size': file_data.get('file_size'),
                    'file_type': file_data.get('file_type'),
                    'id': file_data['id'],
                    'status': file_data.get('status', 'available')
                })

            logger.info("File discovery completed",
                       printer_id=printer_id,
                       files_found=len(discovered_files))

            return discovered_files

        except Exception as e:
            logger.error("File discovery failed", printer_id=printer_id, error=str(e))
            return []

    async def get_file_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file information by ID."""
        try:
            # Check printer files in database first
            files = await self.database.list_files()
            for file_data in files:
                if file_data['id'] == file_id:
                    return dict(file_data)
            
            # Check local files from file watcher if available
            if self.file_watcher:
                local_files = self.file_watcher.get_local_files()
                for file_data in local_files:
                    if file_data.get('id') == file_id:
                        return dict(file_data)
            
            return None
        except Exception as e:
            logger.error("Failed to get file by ID", file_id=file_id, error=str(e))
            return None

    async def find_file_by_name(self, filename: str, printer_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Find file by filename, optionally filtering by printer_id."""
        try:
            # Check printer files in database first
            files = await self.database.list_files(printer_id=printer_id)
            for file_data in files:
                if file_data.get('filename') == filename:
                    return dict(file_data)

            # Check local files from file watcher if available
            if self.file_watcher:
                local_files = self.file_watcher.get_local_files()
                for file_data in local_files:
                    if file_data.get('filename') == filename:
                        # Only return local files if no printer_id filter or if it matches
                        if printer_id is None or file_data.get('printer_id') == printer_id:
                            return dict(file_data)

            return None
        except Exception as e:
            logger.error("Failed to find file by name", filename=filename, printer_id=printer_id, error=str(e))
            return None

    async def delete_file(self, file_id: str) -> bool:
        """Delete a file record (for local files and downloaded files, also delete physical file)."""
        try:
            file_data = await self.get_file_by_id(file_id)
            if not file_data:
                raise NotFoundError("File", file_id)

            # Delete physical file if it exists locally
            should_delete_physical = (
                file_data.get('source') == 'local_watch' or
                (file_data.get('source') == 'printer' and file_data.get('status') == 'downloaded')
            )

            if should_delete_physical and file_data.get('file_path'):
                try:
                    file_path = Path(file_data['file_path'])
                    if file_path.exists():
                        file_path.unlink()
                        logger.info("Deleted physical file", path=str(file_path))
                except Exception as e:
                    logger.warning("Could not delete physical file", path=file_data['file_path'], error=str(e))

            # Delete from database
            if file_data.get('source') == 'local_watch':
                success = await self.database.delete_local_file(file_id)
            else:
                # For printer files, reset to available status so they can be downloaded again
                success = await self.database.update_file(file_id, {
                    'status': 'available',
                    'file_path': None,
                    'downloaded_at': None,
                    'download_progress': 0
                })

            if success:
                logger.info("File deleted successfully", file_id=file_id)

                # Emit file deleted event
                await self.event_service.emit_event("file_deleted", {
                    "file_id": file_id,
                    "filename": file_data.get('filename'),
                    "source": file_data.get('source')
                })

            return success

        except Exception as e:
            logger.error("Failed to delete file", file_id=file_id, error=str(e))
            return False
    
    async def cleanup_download_status(self, max_age_hours: int = 24):
        """Clean up old download status entries."""
        try:
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            
            # Clean up in-memory status for completed/failed downloads
            to_remove = []
            for file_id, status in self.download_status.items():
                if status in ['completed', 'failed']:
                    to_remove.append(file_id)
            
            for file_id in to_remove:
                if file_id in self.download_status:
                    del self.download_status[file_id]
                if file_id in self.download_progress:
                    del self.download_progress[file_id]
            
            logger.info("Cleaned up download status", removed_entries=len(to_remove))
        except Exception as e:
            logger.error("Failed to cleanup download status", error=str(e))
            
    async def process_file_thumbnails(self, file_path: str, file_id: str) -> bool:
        """
        Process a file to extract thumbnails and metadata using Bambu parser.
        
        Args:
            file_path: Local path to the file
            file_id: File ID in database
            
        Returns:
            True if processing was successful, False otherwise
        """
        start_time = datetime.utcnow()
        
        try:
            # Log the attempt
            self._log_thumbnail_processing(file_path, file_id, "started", None)
            
            if not os.path.exists(file_path):
                error_msg = "File not found for thumbnail processing"
                logger.warning(error_msg, file_path=file_path)
                self._log_thumbnail_processing(file_path, file_id, "failed", error_msg)
                return False
            
            # Parse file with Bambu parser
            parse_result = await self.bambu_parser.parse_file(file_path)
            
            if not parse_result['success']:
                error_msg = parse_result.get('error', 'Unknown parsing error')
                logger.info("File parsing failed or not applicable", 
                           file_path=file_path, error=error_msg)
                self._log_thumbnail_processing(file_path, file_id, "failed", error_msg)
                return False
            
            thumbnails = parse_result['thumbnails']
            metadata = parse_result['metadata']
            
            # Get best thumbnail for storage
            thumbnail_data = None
            thumbnail_width = None
            thumbnail_height = None
            thumbnail_format = None
            thumbnail_source = 'embedded'

            if thumbnails:
                # Prefer thumbnail closest to 200x200 for UI display
                best_thumbnail = self.bambu_parser.get_thumbnail_by_size(
                    thumbnails, (200, 200)
                )

                if best_thumbnail:
                    thumbnail_data = best_thumbnail['data']
                    thumbnail_width = best_thumbnail['width']
                    thumbnail_height = best_thumbnail['height']
                    thumbnail_format = best_thumbnail.get('format', 'png')
                    thumbnail_source = 'embedded'
            elif parse_result.get('needs_generation', False):
                # No embedded thumbnails - try Prusa printer API first, then generate preview

                # Try to download thumbnail from Prusa printer if this is a Prusa file
                if file_id.startswith('59dd18ca-b8c3-4a69-b00d-1931257ecbce'):  # Prusa printer ID
                    try:
                        import base64
                        # Extract filename from file_id (format: printer_id_filename)
                        filename = file_id.split('_', 1)[1] if '_' in file_id else os.path.basename(file_path)

                        logger.info("Attempting to download thumbnail from Prusa API",
                                   file_id=file_id, filename=filename)

                        # Get the Prusa printer instance
                        printer_instance = self.printer_service.printers.get('59dd18ca-b8c3-4a69-b00d-1931257ecbce')
                        if printer_instance and hasattr(printer_instance, 'download_thumbnail'):
                            prusa_thumb_bytes = await printer_instance.download_thumbnail(filename, size='l')

                            if prusa_thumb_bytes:
                                thumbnail_data = base64.b64encode(prusa_thumb_bytes).decode('utf-8')
                                # Try to extract dimensions from PNG header
                                if len(prusa_thumb_bytes) > 24 and prusa_thumb_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                                    try:
                                        import struct
                                        width, height = struct.unpack('>II', prusa_thumb_bytes[16:24])
                                        thumbnail_width = width
                                        thumbnail_height = height
                                    except Exception:
                                        thumbnail_width = 200
                                        thumbnail_height = 200
                                else:
                                    thumbnail_width = 200
                                    thumbnail_height = 200
                                thumbnail_format = 'png'
                                thumbnail_source = 'printer'
                                logger.info("Successfully downloaded thumbnail from Prusa API",
                                           file_path=file_path, size_bytes=len(prusa_thumb_bytes))
                    except Exception as e:
                        logger.warning("Failed to download thumbnail from Prusa API, will try generation",
                                     file_path=file_path, error=str(e))

                # If still no thumbnail, generate preview
                if not thumbnail_data:
                    try:
                        import base64
                        file_type = self._get_file_type(os.path.basename(file_path))
                        logger.info("Generating preview thumbnail for file",
                                   file_path=file_path, file_type=file_type)

                        preview_bytes = await self.preview_render_service.get_or_generate_preview(
                            file_path, file_type, size=(200, 200)
                        )

                        if preview_bytes:
                            thumbnail_data = base64.b64encode(preview_bytes).decode('utf-8')
                            thumbnail_width = 200
                            thumbnail_height = 200
                            thumbnail_format = 'png'
                            thumbnail_source = 'generated'
                            logger.info("Successfully generated preview thumbnail",
                                       file_path=file_path)
                        else:
                            logger.warning("Preview generation returned no data",
                                         file_path=file_path)
                    except Exception as e:
                        logger.error("Failed to generate preview thumbnail",
                                    file_path=file_path, error=str(e))
            
            # Update file record with thumbnail and metadata
            update_data = {
                'has_thumbnail': thumbnail_data is not None,
                'thumbnail_data': thumbnail_data,
                'thumbnail_width': thumbnail_width,
                'thumbnail_height': thumbnail_height,
                'thumbnail_format': thumbnail_format,
                'thumbnail_source': thumbnail_source,
            }
            
            # Merge parsed metadata with existing metadata
            existing_file = await self.get_file_by_id(file_id)
            if existing_file:
                existing_metadata = existing_file.get('metadata', {}) or {}
                merged_metadata = {**existing_metadata, **metadata}
                update_data['metadata'] = merged_metadata
            else:
                update_data['metadata'] = metadata
            
            success = await self.database.update_file(file_id, update_data)
            
            if success:
                success_msg = f"Successfully processed {len(thumbnails)} thumbnails"
                logger.info("Successfully processed file thumbnails",
                           file_path=file_path,
                           file_id=file_id,
                           thumbnail_count=len(thumbnails),
                           has_thumbnail=len(thumbnails) > 0,
                           metadata_keys=list(metadata.keys()))
                
                self._log_thumbnail_processing(file_path, file_id, "success", 
                                             f"{len(thumbnails)} thumbnails extracted")
                
                # Emit file updated event
                await self.event_service.emit_event("file_thumbnails_processed", {
                    "file_id": file_id,
                    "file_path": file_path,
                    "thumbnail_count": len(thumbnails),
                    "has_thumbnail": len(thumbnails) > 0,
                    "metadata": metadata
                })
                
                return True
            else:
                error_msg = "Failed to update file with thumbnail data"
                logger.error(error_msg, file_id=file_id)
                self._log_thumbnail_processing(file_path, file_id, "failed", error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Exception during processing: {str(e)}"
            logger.error("Failed to process file thumbnails", 
                        file_path=file_path, file_id=file_id, error=str(e))
            self._log_thumbnail_processing(file_path, file_id, "failed", error_msg)
            return False
    
    def _log_thumbnail_processing(self, file_path: str, file_id: str, 
                                status: str, details: Optional[str] = None):
        """Log a thumbnail processing attempt for debugging."""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'file_path': file_path,
            'file_id': file_id,
            'status': status,  # 'started', 'success', 'failed'
            'details': details,
            'file_extension': Path(file_path).suffix.lower()
        }
        
        # Add to the beginning of the list (most recent first)
        self.thumbnail_processing_log.insert(0, entry)
        
        # Keep only the last N entries
        if len(self.thumbnail_processing_log) > self.max_log_entries:
            self.thumbnail_processing_log = self.thumbnail_processing_log[:self.max_log_entries]
    
    def get_thumbnail_processing_log(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent thumbnail processing log entries."""
        if limit:
            return self.thumbnail_processing_log[:limit]
        return self.thumbnail_processing_log
    
    async def extract_enhanced_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract enhanced metadata from a file using BambuParser and ThreeMFAnalyzer.
        
        This method implements Phase 1 of Issue #43 - METADATA-001.
        It extracts comprehensive metadata including physical properties, print settings,
        material requirements, cost analysis, quality metrics, and compatibility info.
        
        Args:
            file_id: ID of the file to analyze
            
        Returns:
            Enhanced metadata dictionary or None if extraction failed
        """
        try:
            from src.services.threemf_analyzer import ThreeMFAnalyzer
            from src.models.file import (
                EnhancedFileMetadata, PhysicalProperties, PrintSettings,
                MaterialRequirements, CostBreakdown, QualityMetrics, CompatibilityInfo
            )
            
            logger.info("Extracting enhanced metadata", file_id=file_id)
            
            # Get file record
            file_record = await self.database.get_file(file_id)
            if not file_record:
                logger.error("File not found", file_id=file_id)
                return None
            
            file_path = file_record.get('file_path')
            if not file_path or not Path(file_path).exists():
                logger.warning("File path not found or does not exist", 
                             file_id=file_id, file_path=file_path)
                return None
            
            file_path = Path(file_path)
            file_type = file_path.suffix.lower()
            
            # Extract metadata based on file type
            enhanced_metadata = {}
            
            if file_type == '.3mf':
                # Use ThreeMFAnalyzer for 3MF files
                analyzer = ThreeMFAnalyzer()
                result = await analyzer.analyze_file(file_path)
                
                if result.get('success'):
                    enhanced_metadata = result
                else:
                    logger.warning("3MF analysis failed", file_id=file_id, 
                                 error=result.get('error'))
                    return None
            
            elif file_type in ['.gcode', '.g']:
                # Use BambuParser for G-code files
                result = await self.bambu_parser.parse_file(str(file_path))
                
                if result.get('success'):
                    metadata = result.get('metadata', {})
                    
                    # Convert parser output to enhanced metadata format
                    enhanced_metadata = {
                        'physical_properties': {
                            'width': metadata.get('model_width'),
                            'depth': metadata.get('model_depth'),
                            'height': metadata.get('model_height'),
                            'object_count': 1
                        },
                        'print_settings': {
                            'layer_height': metadata.get('layer_height'),
                            'first_layer_height': metadata.get('first_layer_height'),
                            'nozzle_diameter': metadata.get('nozzle_diameter'),
                            'wall_count': metadata.get('wall_loops'),
                            'wall_thickness': metadata.get('wall_thickness'),
                            'infill_density': metadata.get('infill_density') or metadata.get('sparse_infill_density'),
                            'infill_pattern': metadata.get('infill_pattern') or metadata.get('sparse_infill_pattern'),
                            'support_used': metadata.get('support_used') or metadata.get('enable_support'),
                            'nozzle_temperature': metadata.get('nozzle_temperature'),
                            'bed_temperature': metadata.get('bed_temperature'),
                            'print_speed': metadata.get('print_speed'),
                            'total_layer_count': metadata.get('total_layer_count')
                        },
                        'material_requirements': {
                            'total_weight': metadata.get('total_filament_weight_sum') or metadata.get('total_filament_used'),
                            'filament_length': metadata.get('filament_length_meters'),
                            'multi_material': isinstance(metadata.get('filament_used_grams', []), list) and 
                                            len(metadata.get('filament_used_grams', [])) > 1
                        },
                        'cost_breakdown': {
                            'material_cost': metadata.get('material_cost_estimate'),
                            'energy_cost': metadata.get('energy_cost_estimate'),
                            'total_cost': metadata.get('total_cost_estimate')
                        },
                        'quality_metrics': {
                            'complexity_score': metadata.get('complexity_score'),
                            'difficulty_level': metadata.get('difficulty_level'),
                            'success_probability': 100 - (metadata.get('complexity_score', 5) * 5) if metadata.get('complexity_score') else None
                        },
                        'compatibility_info': {
                            'compatible_printers': metadata.get('compatible_printers'),
                            'slicer_name': metadata.get('generator'),
                            'bed_type': metadata.get('curr_bed_type')
                        },
                        'success': True
                    }
                else:
                    logger.warning("G-code parsing failed", file_id=file_id)
                    return None
            
            else:
                logger.warning("Unsupported file type for enhanced metadata", 
                             file_id=file_id, file_type=file_type)
                return None
            
            # Convert to Pydantic models
            try:
                enhanced_model = EnhancedFileMetadata(
                    physical_properties=PhysicalProperties(**enhanced_metadata.get('physical_properties', {})) 
                        if enhanced_metadata.get('physical_properties') else None,
                    print_settings=PrintSettings(**enhanced_metadata.get('print_settings', {}))
                        if enhanced_metadata.get('print_settings') else None,
                    material_requirements=MaterialRequirements(**enhanced_metadata.get('material_requirements', {}))
                        if enhanced_metadata.get('material_requirements') else None,
                    cost_breakdown=CostBreakdown(**enhanced_metadata.get('cost_breakdown', {}))
                        if enhanced_metadata.get('cost_breakdown') else None,
                    quality_metrics=QualityMetrics(**enhanced_metadata.get('quality_metrics', {}))
                        if enhanced_metadata.get('quality_metrics') else None,
                    compatibility_info=CompatibilityInfo(**enhanced_metadata.get('compatibility_info', {}))
                        if enhanced_metadata.get('compatibility_info') else None
                )
                
                # Update file record with enhanced metadata
                await self.database.update_file_enhanced_metadata(
                    file_id=file_id,
                    enhanced_metadata=enhanced_model.model_dump(),
                    last_analyzed=datetime.now()
                )
                
                logger.info("Successfully extracted enhanced metadata", file_id=file_id)
                
                # Emit event
                await self.event_service.emit_event("file_metadata_extracted", {
                    "file_id": file_id,
                    "file_path": str(file_path),
                    "has_physical_properties": enhanced_model.physical_properties is not None,
                    "has_print_settings": enhanced_model.print_settings is not None,
                    "complexity_score": enhanced_model.quality_metrics.complexity_score if enhanced_model.quality_metrics else None
                })
                
                return enhanced_model.model_dump()
                
            except Exception as e:
                logger.error("Failed to create metadata models", file_id=file_id, error=str(e))
                return None
                
        except Exception as e:
            logger.error("Failed to extract enhanced metadata", file_id=file_id, error=str(e))
            return None.copy()