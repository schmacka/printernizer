"""
File service for managing 3D files and downloads.
Handles both printer files (via APIs) and local files (via folder watching).
"""
from typing import List, Dict, Any, Optional
import structlog
from database.database import Database
from services.event_service import EventService
from services.file_watcher_service import FileWatcherService

logger = structlog.get_logger()


class FileService:
    """Service for managing 3D files and downloads."""
    
    def __init__(self, database: Database, event_service: EventService, 
                 file_watcher: Optional[FileWatcherService] = None):
        """Initialize file service."""
        self.database = database
        self.event_service = event_service
        self.file_watcher = file_watcher
        
    async def get_files(self, printer_id: Optional[str] = None, 
                       include_local: bool = True) -> List[Dict[str, Any]]:
        """Get list of available files from printers and local folders."""
        files = []
        
        # Get printer files from database (TODO: implement database queries)
        # For now, return empty list for printer files
        printer_files = []
        
        # Get local files from file watcher if enabled and available
        if include_local and self.file_watcher:
            try:
                local_files = self.file_watcher.get_local_files()
                files.extend(local_files)
                logger.debug("Retrieved local files", count=len(local_files))
            except Exception as e:
                logger.error("Error retrieving local files", error=str(e))
        
        # Combine and return all files
        files.extend(printer_files)
        
        # Filter by printer_id if specified (only applies to printer files)
        if printer_id:
            files = [f for f in files if f.get('printer_id') == printer_id or f.get('source') == 'local_watch']
        
        return files
        
    async def get_printer_files(self, printer_id: str) -> List[Dict[str, Any]]:
        """Get files available on specific printer."""
        # TODO: Implement printer file discovery
        return []
        
    async def download_file(self, printer_id: str, filename: str) -> Dict[str, Any]:
        """Download file from printer."""
        # TODO: Implement actual file download
        logger.info("Downloading file (placeholder)", printer_id=printer_id, filename=filename)
        return {
            "status": "success",
            "message": "File download not yet implemented",
            "local_path": None
        }
        
    async def get_download_status(self, file_id: str) -> Dict[str, Any]:
        """Get download status of a file."""
        # TODO: Implement download status tracking
        return {
            "file_id": file_id,
            "status": "unknown",
            "progress": 0
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
            local_count = len(local_files)
            
            return {
                "total_files": total_files,
                "local_files": len(local_files),
                "printer_files": len(printer_files),
                "available_count": available_count,
                "downloaded_count": downloaded_count,
                "local_count": local_count,
                "total_size": total_size,
                "download_success_rate": 1.0  # Placeholder
            }
            
        except Exception as e:
            logger.error("Error calculating file statistics", error=str(e))
            return {
                "total_files": 0,
                "local_files": 0,
                "printer_files": 0,
                "available_count": 0,
                "downloaded_count": 0,
                "local_count": 0,
                "total_size": 0,
                "download_success_rate": 0.0
            }