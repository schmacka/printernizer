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
from database.database import Database
from services.event_service import EventService
from services.file_watcher_service import FileWatcherService
from utils.exceptions import NotFoundError
from utils.gcode_parser import parse_gcode_file
from models.file import ThumbnailData, FileMetadata

logger = structlog.get_logger()


class FileService:
    """Service for managing 3D files and downloads."""
    
    def __init__(self, database: Database, event_service: EventService, 
                 file_watcher: Optional[FileWatcherService] = None, 
                 printer_service=None):
        """Initialize file service."""
        self.database = database
        self.event_service = event_service
        self.file_watcher = file_watcher
        self.printer_service = printer_service
        self.download_progress = {}
        self.download_status = {}
        
    async def get_files(self, printer_id: Optional[str] = None, 
                       include_local: bool = True) -> List[Dict[str, Any]]:
        """Get list of available files from printers and local folders."""
        files = []
        
        # Get printer files from database
        try:
            printer_files = await self.database.list_files(
                printer_id=printer_id if printer_id != 'local' else None,
                source='printer'
            )
            
            # Convert database rows to file format
            for file_data in printer_files:
                file_dict = dict(file_data)
                file_dict['source'] = 'printer'
                files.append(file_dict)
                
            logger.debug("Retrieved printer files from database", count=len(printer_files))
            
        except Exception as e:
            logger.error("Error retrieving printer files from database", error=str(e))
        
        # Get local files from file watcher if enabled and available
        if include_local and self.file_watcher:
            try:
                local_files = self.file_watcher.get_local_files()
                files.extend(local_files)
                logger.debug("Retrieved local files", count=len(local_files))
            except Exception as e:
                logger.error("Error retrieving local files", error=str(e))
        
        # Filter by printer_id if specified (only applies to printer files)
        if printer_id and printer_id != 'local':
            files = [f for f in files if f.get('printer_id') == printer_id or f.get('source') == 'local_watch']
        
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
                downloads_dir = Path("downloads") / printer_id
                downloads_dir.mkdir(parents=True, exist_ok=True)
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
                # Extract thumbnails and metadata from downloaded file
                thumbnail_data = None
                parsed_metadata = None
                
                try:
                    parse_result = await self._extract_file_metadata(destination_path)
                    thumbnail_data = parse_result.get('thumbnails')
                    parsed_metadata = parse_result.get('metadata')
                except Exception as e:
                    logger.warning("Failed to extract file metadata", 
                                 filename=filename, error=str(e))
                
                # Update database with download info and metadata
                update_data = {
                    'status': 'downloaded',
                    'file_path': destination_path,
                    'downloaded_at': datetime.now().isoformat(),
                    'download_progress': 100
                }
                
                # Add thumbnail and metadata if extracted
                if thumbnail_data:
                    update_data['thumbnails'] = [thumb.dict() if hasattr(thumb, 'dict') else thumb 
                                                for thumb in thumbnail_data]
                if parsed_metadata:
                    update_data['parsed_metadata'] = parsed_metadata.dict() if hasattr(parsed_metadata, 'dict') else parsed_metadata
                
                await self.database.update_file(file_id, update_data)
                
                self.download_progress[file_id] = 100
                self.download_status[file_id] = "completed"
                
                # Emit download complete event
                await self.event_service.emit_event("file_download_complete", {
                    "printer_id": printer_id,
                    "filename": filename,
                    "file_id": file_id,
                    "local_path": destination_path,
                    "has_thumbnails": bool(thumbnail_data),
                    "has_metadata": bool(parsed_metadata)
                })
                
                logger.info("File download completed", printer_id=printer_id, filename=filename,
                           has_thumbnails=bool(thumbnail_data), has_metadata=bool(parsed_metadata))
                
                return {
                    "status": "success",
                    "message": "File downloaded successfully",
                    "local_path": destination_path,
                    "file_id": file_id,
                    "thumbnails": thumbnail_data,
                    "metadata": parsed_metadata
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
            files = await self.get_files()
            
            # Calculate statistics
            total_files = len(files)
            local_files = [f for f in files if f.get('source') == 'local_watch']
            printer_files = [f for f in files if f.get('source') != 'local_watch']
            
            total_size = sum(f.get('file_size', 0) for f in files)
            
            # Count by status
            available_count = len([f for f in files if f.get('status') in ['available', 'local']])
            downloaded_count = len([f for f in files if f.get('status') == 'downloaded'])
            failed_count = len([f for f in files if f.get('status') == 'failed'])
            local_count = len(local_files)
            
            # Calculate download success rate
            total_download_attempts = downloaded_count + failed_count
            download_success_rate = downloaded_count / total_download_attempts if total_download_attempts > 0 else 1.0
            
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
            logger.error("Error calculating file statistics", error=str(e))
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
    
    async def get_file_by_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file information by ID."""
        try:
            files = await self.database.list_files()
            for file_data in files:
                if file_data['id'] == file_id:
                    return dict(file_data)
            return None
        except Exception as e:
            logger.error("Failed to get file by ID", file_id=file_id, error=str(e))
            return None
    
    async def delete_file(self, file_id: str) -> bool:
        """Delete a file record (for local files, also delete physical file)."""
        try:
            file_data = await self.get_file_by_id(file_id)
            if not file_data:
                raise NotFoundError("File", file_id)
            
            # If it's a local file, delete the physical file too
            if file_data.get('source') == 'local_watch' and file_data.get('file_path'):
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
                # For printer files, mark as deleted rather than removing
                success = await self.database.update_file(file_id, {'status': 'deleted'})
            
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
    
    async def _extract_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract thumbnails and metadata from a file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Dictionary with thumbnails and metadata
        """
        try:
            # Only process files that might contain thumbnails/metadata
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in ['.gcode', '.bgcode', '.3mf']:
                return {'thumbnails': [], 'metadata': {}}
            
            # Run G-code parsing in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            parse_result = await loop.run_in_executor(None, parse_gcode_file, file_path)
            
            # Convert raw results to Pydantic models
            thumbnails = []
            if parse_result.get('thumbnails'):
                for thumb_data in parse_result['thumbnails']:
                    try:
                        thumbnail = ThumbnailData(**thumb_data)
                        thumbnails.append(thumbnail)
                    except Exception as e:
                        logger.warning("Failed to create thumbnail model", error=str(e))
            
            metadata = None
            if parse_result.get('metadata'):
                try:
                    metadata = FileMetadata(**parse_result['metadata'])
                except Exception as e:
                    logger.warning("Failed to create metadata model", error=str(e))
            
            return {
                'thumbnails': thumbnails,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error("Failed to extract file metadata", file_path=file_path, error=str(e))
            return {'thumbnails': [], 'metadata': {}}
    
    async def get_file_thumbnail(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get thumbnail data for a specific file.
        
        Args:
            file_id: File identifier
            
        Returns:
            Thumbnail data or None if not available
        """
        try:
            file_data = await self.get_file_by_id(file_id)
            if not file_data:
                return None
            
            # Check if thumbnails are already stored
            if file_data.get('thumbnails'):
                # Return the first/best thumbnail
                thumbnails = file_data['thumbnails']
                if isinstance(thumbnails, list) and thumbnails:
                    return thumbnails[0]
                return thumbnails
            
            # If no thumbnails stored but file exists locally, try to extract them
            if file_data.get('file_path') and Path(file_data['file_path']).exists():
                parse_result = await self._extract_file_metadata(file_data['file_path'])
                if parse_result.get('thumbnails'):
                    # Store the thumbnails for future use
                    thumbnail_data = [thumb.dict() if hasattr(thumb, 'dict') else thumb 
                                    for thumb in parse_result['thumbnails']]
                    await self.database.update_file(file_id, {'thumbnails': thumbnail_data})
                    
                    return thumbnail_data[0] if thumbnail_data else None
            
            return None
            
        except Exception as e:
            logger.error("Failed to get file thumbnail", file_id=file_id, error=str(e))
            return None