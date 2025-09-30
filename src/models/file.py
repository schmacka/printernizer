"""
File models for Printernizer.
Pydantic models for 3D file data validation and serialization.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class FileStatus(str, Enum):
    """File status states."""
    AVAILABLE = "available"      # Available on printer for download
    DOWNLOADING = "downloading"  # Currently being downloaded
    DOWNLOADED = "downloaded"    # Successfully downloaded
    LOCAL = "local"             # Local file only (not on printer)
    ERROR = "error"             # Download or processing error
    DELETED = "deleted"          # Marked as deleted
    UNAVAILABLE = "unavailable"  # No longer available on printer


class FileSource(str, Enum):
    """File source types."""
    PRINTER = "printer"         # File discovered on printer
    LOCAL = "local"            # Local file upload
    IMPORTED = "imported"      # Imported from external source
    LOCAL_WATCH = "local_watch" # File discovered in watch folder


class File(BaseModel):
    """File model."""
    id: str = Field(..., description="Unique file identifier")
    printer_id: str = Field(..., description="Printer ID where file is located")
    filename: str = Field(..., description="Original filename")
    display_name: Optional[str] = Field(None, description="Display name for UI")
    file_path: Optional[str] = Field(None, description="Local file path if downloaded")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    file_type: Optional[str] = Field(None, description="File type (stl, 3mf, gcode)")
    status: FileStatus = Field(FileStatus.AVAILABLE, description="Current file status")
    source: FileSource = Field(FileSource.PRINTER, description="File source")
    download_progress: Optional[int] = Field(None, description="Download progress (0-100)")
    downloaded_at: Optional[datetime] = Field(None, description="Download completion time")
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional file metadata")
    
    # Thumbnail fields
    has_thumbnail: bool = Field(False, description="Whether file has thumbnail(s)")
    thumbnail_data: Optional[str] = Field(None, description="Base64 encoded thumbnail data")
    thumbnail_width: Optional[int] = Field(None, description="Thumbnail width in pixels")
    thumbnail_height: Optional[int] = Field(None, description="Thumbnail height in pixels")
    thumbnail_format: Optional[str] = Field(None, description="Thumbnail format (png, jpg)")
    
    # Watch folder specific fields
    watch_folder_path: Optional[str] = Field(None, description="Watch folder path for local files")
    relative_path: Optional[str] = Field(None, description="Relative path within watch folder")
    modified_time: Optional[datetime] = Field(None, description="File modification time")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FileDownload(BaseModel):
    """File download request model."""
    printer_id: str
    filename: str
    local_path: Optional[str] = None


class FileUpload(BaseModel):
    """File upload model."""
    printer_id: str
    filename: str
    file_size: int
    file_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FileFilter(BaseModel):
    """File filtering model."""
    printer_id: Optional[str] = None
    status: Optional[FileStatus] = None
    source: Optional[FileSource] = None
    file_type: Optional[str] = None
    watch_folder_path: Optional[str] = None


class WatchFolderConfig(BaseModel):
    """Watch folder configuration model."""
    path: str = Field(..., description="Folder path to watch")
    enabled: bool = Field(True, description="Whether watching is enabled")
    recursive: bool = Field(True, description="Watch subdirectories recursively")


class WatchFolderStatus(BaseModel):
    """Watch folder status model."""
    path: str
    enabled: bool
    recursive: bool
    is_accessible: bool
    file_count: int
    last_scan: Optional[datetime] = None
    error: Optional[str] = None


class WatchFolderItem(BaseModel):
    """Individual watch folder item model."""
    folder_path: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class WatchFolderSettings(BaseModel):
    """Watch folder settings response model."""
    watch_folders: List[WatchFolderItem]
    enabled: bool
    recursive: bool
    supported_extensions: List[str]