"""
File models for Printernizer.
Pydantic models for 3D file data validation and serialization.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from decimal import Decimal


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
    UPLOAD = "upload"          # File uploaded via drag-and-drop


# Enhanced metadata models for Issue #43
class PhysicalProperties(BaseModel):
    """Physical properties of the 3D model."""
    width: Optional[float] = Field(None, description="Model width in mm")
    depth: Optional[float] = Field(None, description="Model depth in mm") 
    height: Optional[float] = Field(None, description="Model height in mm")
    volume: Optional[float] = Field(None, description="Model volume in cm³")
    surface_area: Optional[float] = Field(None, description="Surface area in cm²")
    object_count: int = Field(1, description="Number of objects in the model")
    bounding_box: Optional[Dict[str, float]] = Field(None, description="3D bounding box coordinates")


class PrintSettings(BaseModel):
    """Print configuration settings."""
    layer_height: Optional[float] = Field(None, description="Layer height in mm")
    first_layer_height: Optional[float] = Field(None, description="First layer height in mm")
    nozzle_diameter: Optional[float] = Field(None, description="Nozzle diameter in mm")
    wall_count: Optional[int] = Field(None, description="Number of perimeter walls")
    wall_thickness: Optional[float] = Field(None, description="Total wall thickness in mm")
    infill_density: Optional[float] = Field(None, description="Infill density percentage")
    infill_pattern: Optional[str] = Field(None, description="Infill pattern type")
    support_used: Optional[bool] = Field(None, description="Whether supports are required")
    nozzle_temperature: Optional[int] = Field(None, description="Nozzle temperature in °C")
    bed_temperature: Optional[int] = Field(None, description="Bed temperature in °C")
    print_speed: Optional[float] = Field(None, description="Print speed in mm/s")
    total_layer_count: Optional[int] = Field(None, description="Total number of layers")


class MaterialRequirements(BaseModel):
    """Material usage and requirements."""
    total_weight: Optional[float] = Field(None, description="Total filament weight in grams")
    filament_length: Optional[float] = Field(None, description="Total filament length in meters")
    filament_colors: Optional[List[str]] = Field(None, description="Filament color codes")
    material_types: Optional[List[str]] = Field(None, description="Material types (PLA, PETG, etc.)")
    waste_weight: Optional[float] = Field(None, description="Estimated waste material in grams")
    multi_material: bool = Field(False, description="Whether multi-material printing is used")


class CostBreakdown(BaseModel):
    """Detailed cost analysis."""
    material_cost: Optional[float] = Field(None, description="Material cost in EUR")
    energy_cost: Optional[float] = Field(None, description="Energy cost in EUR")
    total_cost: Optional[float] = Field(None, description="Total estimated cost in EUR")
    cost_per_gram: Optional[float] = Field(None, description="Cost per gram in EUR")
    breakdown: Optional[Dict[str, float]] = Field(None, description="Detailed cost components")


class QualityMetrics(BaseModel):
    """Print quality and difficulty assessment."""
    complexity_score: Optional[int] = Field(None, description="Complexity score 1-10", ge=1, le=10)
    difficulty_level: Optional[str] = Field(None, description="Beginner, Intermediate, Advanced, Expert")
    success_probability: Optional[float] = Field(None, description="Estimated success rate 0-100", ge=0, le=100)
    overhang_percentage: Optional[float] = Field(None, description="Percentage of overhanging surfaces")
    recommended_settings: Optional[Dict[str, Any]] = Field(None, description="Optimization suggestions")


class CompatibilityInfo(BaseModel):
    """Printer and software compatibility."""
    compatible_printers: Optional[List[str]] = Field(None, description="List of compatible printer models")
    slicer_name: Optional[str] = Field(None, description="Slicer software name")
    slicer_version: Optional[str] = Field(None, description="Slicer software version")
    profile_name: Optional[str] = Field(None, description="Print profile name")
    bed_type: Optional[str] = Field(None, description="Required bed surface type")
    required_features: Optional[List[str]] = Field(None, description="Required printer features")


class EnhancedFileMetadata(BaseModel):
    """Comprehensive file metadata (Issue #43 - METADATA-001)."""
    physical_properties: Optional[PhysicalProperties] = None
    print_settings: Optional[PrintSettings] = None
    material_requirements: Optional[MaterialRequirements] = None
    cost_breakdown: Optional[CostBreakdown] = None
    quality_metrics: Optional[QualityMetrics] = None
    compatibility_info: Optional[CompatibilityInfo] = None


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
    
    # Enhanced metadata (Issue #43 - METADATA-001)
    enhanced_metadata: Optional[EnhancedFileMetadata] = Field(None, description="Comprehensive metadata")
    last_analyzed: Optional[datetime] = Field(None, description="When metadata was last extracted")
    
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


# =====================================================
# TAG MODELS
# =====================================================

class FileTag(BaseModel):
    """File tag model."""
    id: str = Field(..., description="Unique tag identifier")
    name: str = Field(..., description="Tag name (unique, case-insensitive)")
    color: str = Field(default="#6b7280", description="Hex color for visual display")
    description: Optional[str] = Field(None, description="Tag description")
    usage_count: int = Field(default=0, description="Number of files using this tag")
    created_at: Optional[datetime] = Field(None, description="Tag creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Tag update timestamp")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class FileTagCreate(BaseModel):
    """Model for creating a new tag."""
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    color: str = Field(default="#6b7280", description="Hex color code")
    description: Optional[str] = Field(None, max_length=200, description="Tag description")


class FileTagUpdate(BaseModel):
    """Model for updating a tag."""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="New tag name")
    color: Optional[str] = Field(None, description="New hex color code")
    description: Optional[str] = Field(None, max_length=200, description="New description")


class FileTagAssignment(BaseModel):
    """Model for tag assignment to a file."""
    file_checksum: str = Field(..., description="File checksum")
    tag_id: str = Field(..., description="Tag ID")
    assigned_at: Optional[datetime] = Field(None, description="Assignment timestamp")


class TagListResponse(BaseModel):
    """Response model for tag list."""
    tags: List[FileTag]
    total_count: int