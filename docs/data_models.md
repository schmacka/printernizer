# Printernizer Data Models & DTOs

## Overview

This document defines the data models, Data Transfer Objects (DTOs), and API contracts for the Printernizer Phase 1 system. These models ensure type safety, validation, and clear contracts between frontend and backend components.

## Data Model Categories

### 1. **Core Domain Models**
Internal representations of business entities

### 2. **API Request DTOs**
Data structures for incoming API requests

### 3. **API Response DTOs**
Data structures for outgoing API responses

### 4. **Integration Models**
Data structures for external printer APIs

### 5. **Database Models**
SQLAlchemy ORM models for database operations

---

## Core Domain Models

### Printer Models

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal

class PrinterType(Enum):
    BAMBU_LAB = "bambu_lab"
    PRUSA = "prusa"

class PrinterStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"
    UNKNOWN = "unknown"

class ConnectionStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    TESTING = "testing"
    ERROR = "error"

@dataclass
class PrinterCapabilities:
    """Printer hardware capabilities"""
    has_camera: bool = False
    has_ams: bool = False
    supports_remote_control: bool = False
    max_print_volume: Optional[Dict[str, float]] = None  # {"x": 256, "y": 256, "z": 256}
    supported_materials: List[str] = None

@dataclass
class Temperature:
    """Temperature reading with current and target values"""
    current: float
    target: float
    
    @property
    def is_heating(self) -> bool:
        return abs(self.current - self.target) > 2.0

@dataclass
class PrinterTemperatures:
    """Complete temperature state of printer"""
    nozzle: Optional[Temperature] = None
    bed: Optional[Temperature] = None
    chamber: Optional[Temperature] = None

@dataclass
class PrinterStatistics:
    """Printer usage statistics"""
    total_jobs: int = 0
    successful_jobs: int = 0
    failed_jobs: int = 0
    total_print_time: int = 0  # seconds
    material_used_total: Decimal = Decimal('0.0')  # grams
    
    @property
    def success_rate(self) -> float:
        if self.total_jobs == 0:
            return 0.0
        return self.successful_jobs / self.total_jobs

@dataclass
class Printer:
    """Core printer domain model"""
    id: str
    name: str
    type: PrinterType
    model: Optional[str] = None
    ip_address: str = ""
    port: Optional[int] = None
    
    # Authentication
    api_key: Optional[str] = None
    access_code: Optional[str] = None
    serial_number: Optional[str] = None
    
    # Status
    status: PrinterStatus = PrinterStatus.UNKNOWN
    connection_status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    is_active: bool = True
    last_seen: Optional[datetime] = None
    firmware_version: Optional[str] = None
    
    # Current state
    temperatures: Optional[PrinterTemperatures] = None
    current_job_id: Optional[int] = None
    
    # Capabilities and metadata
    capabilities: PrinterCapabilities = None
    statistics: Optional[PrinterStatistics] = None
    
    # Timestamps
    created_at: datetime = None
    updated_at: datetime = None
```

### Job Models

```python
class JobStatus(Enum):
    QUEUED = "queued"
    PREPARING = "preparing"
    PRINTING = "printing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class MaterialType(Enum):
    PLA = "PLA"
    PETG = "PETG"
    ABS = "ABS"
    TPU = "TPU"
    ASA = "ASA"
    PC = "PC"

class QualityRating(Enum):
    EXCELLENT = 5
    GOOD = 4
    FAIR = 3
    POOR = 2
    VERY_POOR = 1

@dataclass
class MaterialInfo:
    """Material information for a print job"""
    type: MaterialType
    brand: Optional[str] = None
    color: Optional[str] = None
    estimated_usage: Optional[Decimal] = None  # grams
    actual_usage: Optional[Decimal] = None  # grams
    cost_per_gram: Optional[Decimal] = None  # EUR

@dataclass
class PrintSettings:
    """Print configuration settings"""
    layer_height: Optional[float] = None  # mm
    infill_percentage: Optional[int] = None
    print_speed: Optional[int] = None  # mm/min
    nozzle_temperature: Optional[int] = None  # Celsius
    bed_temperature: Optional[int] = None  # Celsius
    supports_used: bool = False

@dataclass
class FileInfo:
    """File information for a job"""
    filename: str
    size: int  # bytes
    path: Optional[str] = None
    hash: Optional[str] = None
    uploaded_at: Optional[datetime] = None

@dataclass
class CostBreakdown:
    """Cost calculation breakdown"""
    material_cost: Decimal = Decimal('0.0')
    power_cost: Decimal = Decimal('0.0')
    labor_cost: Decimal = Decimal('0.0')
    
    @property
    def total_cost(self) -> Decimal:
        return self.material_cost + self.power_cost + self.labor_cost

@dataclass
class CustomerInfo:
    """Customer information for business jobs"""
    order_id: Optional[str] = None
    customer_name: Optional[str] = None
    email: Optional[str] = None

@dataclass
class QualityMetrics:
    """Job quality assessment"""
    rating: Optional[QualityRating] = None
    first_layer_adhesion: Optional[str] = None  # excellent, good, fair, poor
    surface_finish: Optional[str] = None  # excellent, good, fair, poor
    dimensional_accuracy: Optional[float] = None  # mm deviation

@dataclass
class Job:
    """Core job domain model"""
    id: int
    printer_id: str
    job_name: str
    job_id_on_printer: Optional[str] = None
    
    # Status and progress
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0  # 0.0 to 100.0
    layer_current: int = 0
    layer_total: Optional[int] = None
    
    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # seconds
    actual_duration: Optional[int] = None  # seconds
    estimated_completion: Optional[datetime] = None
    
    # Material and settings
    material_info: Optional[MaterialInfo] = None
    print_settings: Optional[PrintSettings] = None
    file_info: Optional[FileInfo] = None
    
    # Costs and business
    costs: CostBreakdown = None
    is_business: bool = False
    customer_info: Optional[CustomerInfo] = None
    
    # Quality and outcome
    quality_metrics: Optional[QualityMetrics] = None
    notes: Optional[str] = None
    failure_reason: Optional[str] = None
    
    # Timestamps
    created_at: datetime = None
    updated_at: datetime = None
```

### File Models

```python
class FileStatus(Enum):
    AVAILABLE = "available"  # On printer, not downloaded
    DOWNLOADING = "downloading"  # Currently downloading
    DOWNLOADED = "downloaded"  # Successfully downloaded
    LOCAL = "local"  # Local file only
    ERROR = "error"  # Download failed
    DELETED = "deleted"  # Marked as deleted

class FileType(Enum):
    THREE_MF = ".3mf"
    STL = ".stl"
    GCODE = ".gcode"
    OBJ = ".obj"

@dataclass
class FileMetadata:
    """Extracted file metadata from 3MF/GCODE files"""
    estimated_print_time: Optional[int] = None  # seconds
    layer_count: Optional[int] = None
    layer_height: Optional[float] = None  # mm
    infill_percentage: Optional[int] = None
    material_type: Optional[str] = None
    nozzle_temperature: Optional[int] = None
    bed_temperature: Optional[int] = None
    support_material: Optional[bool] = None

@dataclass
class File:
    """Core file domain model"""
    id: str
    printer_id: Optional[str] = None  # None for local files
    filename: str = ""
    original_filename: Optional[str] = None
    file_type: FileType = FileType.STL
    file_size: int = 0
    
    # Paths
    printer_path: Optional[str] = None
    local_path: Optional[str] = None
    
    # Status
    download_status: FileStatus = FileStatus.AVAILABLE
    download_attempts: int = 0
    downloaded_at: Optional[datetime] = None
    last_download_attempt: Optional[datetime] = None
    download_error: Optional[str] = None
    
    # Verification
    checksum_md5: Optional[str] = None
    checksum_sha256: Optional[str] = None
    
    # Metadata
    metadata: Optional[FileMetadata] = None
    
    # Access tracking
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    
    # Related jobs
    related_job_ids: List[int] = None
    
    # Timestamps
    created_at: datetime = None
    updated_at: datetime = None
    created_on_printer: Optional[datetime] = None
    
    @property
    def status_icon(self) -> str:
        """Get emoji icon for current status"""
        icons = {
            FileStatus.AVAILABLE: "📁",
            FileStatus.DOWNLOADING: "⏬",
            FileStatus.DOWNLOADED: "✓",
            FileStatus.LOCAL: "💾",
            FileStatus.ERROR: "❌",
            FileStatus.DELETED: "🗑️"
        }
        return icons.get(self.download_status, "❓")
```

---

## API Request DTOs

### Printer Request DTOs

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any

class CreatePrinterRequest(BaseModel):
    """Request to add new printer"""
    id: str = Field(..., min_length=1, max_length=50, regex=r'^[a-zA-Z0-9_-]+$')
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., regex=r'^(bambu_lab|prusa)$')
    model: Optional[str] = Field(None, max_length=50)
    ip_address: str = Field(..., regex=r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    port: Optional[int] = Field(None, ge=1, le=65535)
    api_key: Optional[str] = Field(None, min_length=8, max_length=100)
    access_code: Optional[str] = Field(None, min_length=8, max_length=20)
    serial_number: Optional[str] = Field(None, min_length=5, max_length=30)
    is_active: bool = Field(True)
    
    @validator('api_key', 'access_code')
    def validate_auth_fields(cls, v, values, field):
        printer_type = values.get('type')
        if printer_type == 'prusa' and field.name == 'api_key' and not v:
            raise ValueError('API key required for Prusa printers')
        if printer_type == 'bambu_lab' and field.name == 'access_code' and not v:
            raise ValueError('Access code required for Bambu Lab printers')
        return v

class UpdatePrinterRequest(BaseModel):
    """Request to update printer configuration"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    ip_address: Optional[str] = Field(None, regex=r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    port: Optional[int] = Field(None, ge=1, le=65535)
    api_key: Optional[str] = Field(None, min_length=8, max_length=100)
    access_code: Optional[str] = Field(None, min_length=8, max_length=20)
    is_active: Optional[bool] = None

class PrinterFilters(BaseModel):
    """Filters for printer list queries"""
    active: Optional[bool] = None
    type: Optional[str] = Field(None, regex=r'^(bambu_lab|prusa)$')
    status: Optional[str] = Field(None, regex=r'^(online|offline|busy|error|unknown)$')
```

### Job Request DTOs

```python
class JobFilters(BaseModel):
    """Filters for job list queries"""
    printer_id: Optional[str] = Field(None, min_length=1, max_length=50)
    status: Optional[str] = Field(None, regex=r'^(queued|preparing|printing|paused|completed|failed|cancelled)$')
    is_business: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    material_type: Optional[str] = None
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        start_date = values.get('start_date')
        if start_date and v and v < start_date:
            raise ValueError('end_date must be after start_date')
        return v

class UpdateJobRequest(BaseModel):
    """Request to update job information"""
    is_business: Optional[bool] = None
    material_cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    labor_cost: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    customer_order_id: Optional[str] = Field(None, max_length=50)
    customer_name: Optional[str] = Field(None, max_length=100)
    customer_email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$')
    quality_rating: Optional[int] = Field(None, ge=1, le=5)
    notes: Optional[str] = Field(None, max_length=1000)

class Pagination(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1)
    limit: int = Field(50, ge=1, le=100)
    order_by: Optional[str] = Field("created_at")
    order_dir: str = Field("desc", regex=r'^(asc|desc)$')
```

### File Request DTOs

```python
class FileFilters(BaseModel):
    """Filters for file list queries"""
    printer_id: Optional[str] = Field(None, min_length=1, max_length=50)
    status: Optional[str] = Field(None, regex=r'^(available|downloading|downloaded|local|error|deleted)$')
    file_type: Optional[str] = Field(None, regex=r'^(\.(3mf|stl|gcode|obj))$')
    search: Optional[str] = Field(None, min_length=1, max_length=100)
    min_size: Optional[int] = Field(None, ge=0)
    max_size: Optional[int] = Field(None, ge=0)

class CleanupCriteria(BaseModel):
    """Criteria for file cleanup operations"""
    older_than_days: int = Field(30, ge=1, le=365)
    min_size_mb: Optional[int] = Field(None, ge=1)
    unused_only: bool = Field(True)
    file_types: Optional[List[str]] = Field(None)
    exclude_business_files: bool = Field(True)

class CleanupRequest(BaseModel):
    """Request to perform file cleanup"""
    file_ids: List[str] = Field(..., min_items=1, max_items=100)
    confirm: bool = Field(False)
    
    @validator('confirm')
    def must_confirm_cleanup(cls, v):
        if not v:
            raise ValueError('Must confirm cleanup operation')
        return v
```

---

## API Response DTOs

### System Response DTOs

```python
class HealthResponse(BaseModel):
    """System health check response"""
    status: str = "healthy"
    timestamp: datetime
    version: str
    database: str = "connected"
    active_printers: int
    uptime_seconds: int

class SystemInfo(BaseModel):
    """System information response"""
    system: Dict[str, Any]
    database: Dict[str, Any]
    features: Dict[str, bool]

class ApiError(BaseModel):
    """Standard API error response"""
    error: Dict[str, Any]
    
    @classmethod
    def create(cls, code: str, message: str, details: Dict = None, request_id: str = None):
        return cls(error={
            "code": code,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id
        })
```

### Printer Response DTOs

```python
class PrinterTemperaturesResponse(BaseModel):
    """Temperature response"""
    nozzle: Optional[float] = None
    nozzle_target: Optional[float] = None
    bed: Optional[float] = None
    bed_target: Optional[float] = None
    chamber: Optional[float] = None

class CurrentJobResponse(BaseModel):
    """Current job information in printer response"""
    id: int
    name: str
    status: str
    progress: float
    layer_current: Optional[int] = None
    layer_total: Optional[int] = None
    estimated_remaining: Optional[int] = None  # seconds
    started_at: Optional[datetime] = None

class PrinterCapabilitiesResponse(BaseModel):
    """Printer capabilities response"""
    has_camera: bool = False
    has_ams: bool = False
    supports_remote_control: bool = False
    max_print_volume: Optional[Dict[str, float]] = None
    supported_materials: List[str] = []

class PrinterStatisticsResponse(BaseModel):
    """Printer statistics response"""
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    total_print_time: int
    material_used_total: float
    success_rate: float

class PrinterResponse(BaseModel):
    """Single printer response"""
    id: str
    name: str
    type: str
    model: Optional[str] = None
    ip_address: str
    status: str
    connection_status: str
    current_job: Optional[CurrentJobResponse] = None
    temperatures: Optional[PrinterTemperaturesResponse] = None
    capabilities: Optional[PrinterCapabilitiesResponse] = None
    statistics: Optional[PrinterStatisticsResponse] = None
    is_active: bool
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class PrinterListResponse(BaseModel):
    """Printer list response with pagination"""
    printers: List[PrinterResponse]
    total_count: int
    active_count: int
```

### Job Response DTOs

```python
class MaterialInfoResponse(BaseModel):
    """Material information response"""
    type: str
    brand: Optional[str] = None
    color: Optional[str] = None
    estimated_usage: Optional[float] = None
    actual_usage: Optional[float] = None
    cost_per_gram: Optional[float] = None

class FileInfoResponse(BaseModel):
    """File information response"""
    filename: str
    size: int
    path: Optional[str] = None
    hash: Optional[str] = None
    uploaded_at: Optional[datetime] = None

class PrintSettingsResponse(BaseModel):
    """Print settings response"""
    layer_height: Optional[float] = None
    infill: Optional[int] = None
    print_speed: Optional[int] = None
    nozzle_temp: Optional[int] = None
    bed_temp: Optional[int] = None

class CostBreakdownResponse(BaseModel):
    """Cost breakdown response"""
    material_cost: float
    power_cost: float
    labor_cost: float
    total_cost: float

class CustomerInfoResponse(BaseModel):
    """Customer information response"""
    order_id: Optional[str] = None
    customer_name: Optional[str] = None

class QualityMetricsResponse(BaseModel):
    """Quality metrics response"""
    first_layer_adhesion: Optional[str] = None
    surface_finish: Optional[str] = None
    dimensional_accuracy: Optional[float] = None

class JobResponse(BaseModel):
    """Single job response"""
    id: int
    printer_id: str
    printer_name: str
    job_name: str
    status: str
    progress: float
    layer_current: Optional[int] = None
    layer_total: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    estimated_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    estimated_completion: Optional[datetime] = None
    material_info: Optional[MaterialInfoResponse] = None
    file_info: Optional[FileInfoResponse] = None
    print_settings: Optional[PrintSettingsResponse] = None
    costs: Optional[CostBreakdownResponse] = None
    is_business: bool
    customer_info: Optional[CustomerInfoResponse] = None
    quality_metrics: Optional[QualityMetricsResponse] = None
    created_at: datetime
    updated_at: datetime

class PaginationResponse(BaseModel):
    """Pagination metadata response"""
    page: int
    limit: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool

class JobSummaryResponse(BaseModel):
    """Job summary statistics"""
    active_jobs: int
    queued_jobs: int
    completed_today: int
    failed_today: int

class JobListResponse(BaseModel):
    """Job list response with pagination"""
    jobs: List[JobResponse]
    pagination: PaginationResponse
    summary: JobSummaryResponse
```

### File Response DTOs

```python
class FileMetadataResponse(BaseModel):
    """File metadata response"""
    estimated_print_time: Optional[int] = None
    layer_count: Optional[int] = None
    layer_height: Optional[float] = None
    infill: Optional[int] = None
    support_material: Optional[bool] = None
    material_type: Optional[str] = None
    nozzle_temperature: Optional[int] = None
    bed_temperature: Optional[int] = None

class RelatedJobResponse(BaseModel):
    """Related job information in file response"""
    id: int
    status: str
    completed_at: Optional[datetime] = None

class FileResponse(BaseModel):
    """Single file response"""
    id: str
    printer_id: Optional[str] = None
    printer_name: Optional[str] = None
    filename: str
    original_filename: Optional[str] = None
    file_size: int
    file_type: str
    status: str
    status_icon: str
    printer_path: Optional[str] = None
    local_path: Optional[str] = None
    created_on_printer: Optional[datetime] = None
    downloaded_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    download_url: Optional[str] = None
    preview_url: Optional[str] = None
    metadata: Optional[FileMetadataResponse] = None
    related_jobs: List[RelatedJobResponse] = []

class FileSummaryResponse(BaseModel):
    """File summary statistics"""
    available_count: int
    downloaded_count: int
    local_count: int
    total_size: int
    download_success_rate: float

class FileListResponse(BaseModel):
    """File list response with pagination"""
    files: List[FileResponse]
    pagination: PaginationResponse
    summary: FileSummaryResponse

class DownloadStatusResponse(BaseModel):
    """File download status response"""
    download_id: str
    file_id: str
    status: str
    progress: float
    bytes_downloaded: int
    bytes_total: int
    speed_mbps: float
    estimated_remaining: int  # seconds
    started_at: datetime
    error: Optional[str] = None

class CleanupCandidateResponse(BaseModel):
    """File cleanup candidate response"""
    id: str
    filename: str
    file_size: int
    downloaded_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    age_days: int
    space_savings_mb: int

class CleanupCandidatesResponse(BaseModel):
    """Cleanup candidates list response"""
    cleanup_candidates: List[CleanupCandidateResponse]
    total_candidates: int
    total_space_savings_mb: int

class CleanupResultResponse(BaseModel):
    """Cleanup operation result"""
    cleaned_files: int
    space_freed_mb: int
    failed_cleanups: List[str] = []
    completed_at: datetime
```

---

## Integration Models

### Bambu Lab Integration Models

```python
class BambuLabStatus(BaseModel):
    """Bambu Lab printer status from MQTT"""
    gcode_state: str  # IDLE, PREPARE, RUNNING, PAUSE, COMPLETE, FAILED
    print_percent: int  # 0-100
    layer_num: int
    total_layer_num: int
    nozzle_temper: float
    nozzle_target_temper: float
    bed_temper: float
    bed_target_temper: float
    chamber_temper: float
    
    def to_printer_status(self) -> PrinterStatus:
        """Convert to internal printer status"""
        status_mapping = {
            "IDLE": PrinterStatus.ONLINE,
            "PREPARE": PrinterStatus.BUSY,
            "RUNNING": PrinterStatus.BUSY,
            "PAUSE": PrinterStatus.BUSY,
            "COMPLETE": PrinterStatus.ONLINE,
            "FAILED": PrinterStatus.ERROR
        }
        return status_mapping.get(self.gcode_state, PrinterStatus.UNKNOWN)

class BambuLabFile(BaseModel):
    """Bambu Lab file information from MQTT"""
    name: str
    size: int
    time: str  # timestamp
    
    def to_file(self, printer_id: str) -> File:
        """Convert to internal file model"""
        return File(
            id=f"bambu_{printer_id}_{self.name}",
            printer_id=printer_id,
            filename=self.name,
            file_size=self.size,
            file_type=FileType(Path(self.name).suffix.lower()),
            printer_path=f"/cache/{self.name}",
            created_on_printer=datetime.fromisoformat(self.time)
        )
```

### Prusa Integration Models

```python
class PrusaJobInfo(BaseModel):
    """Prusa job information from API"""
    id: int
    name: str
    state: str  # Idle, Printing, Paused, Finished, Stopped, Error
    progress: float  # 0.0-1.0
    time_printing: Optional[int] = None  # seconds
    time_remaining: Optional[int] = None  # seconds
    
    def to_job_status(self) -> JobStatus:
        """Convert to internal job status"""
        status_mapping = {
            "Idle": JobStatus.QUEUED,
            "Printing": JobStatus.PRINTING,
            "Paused": JobStatus.PAUSED,
            "Finished": JobStatus.COMPLETED,
            "Stopped": JobStatus.CANCELLED,
            "Error": JobStatus.FAILED
        }
        return status_mapping.get(self.state, JobStatus.QUEUED)

class PrusaTemperature(BaseModel):
    """Prusa temperature from API"""
    actual: float
    target: float
    offset: Optional[float] = None

class PrusaStatus(BaseModel):
    """Prusa printer status from API"""
    printer: Dict[str, str]
    job: Optional[PrusaJobInfo] = None
    temperature: Dict[str, PrusaTemperature]
    
    def to_printer_status(self) -> PrinterStatus:
        """Convert to internal printer status"""
        state = self.printer.get("state", "").lower()
        if "operational" in state:
            return PrinterStatus.ONLINE
        elif "printing" in state or "paused" in state:
            return PrinterStatus.BUSY
        elif "error" in state:
            return PrinterStatus.ERROR
        else:
            return PrinterStatus.UNKNOWN

class PrusaFileInfo(BaseModel):
    """Prusa file information from API"""
    name: str
    path: str
    size: int
    date: int  # Unix timestamp
    
    def to_file(self, printer_id: str) -> File:
        """Convert to internal file model"""
        return File(
            id=f"prusa_{printer_id}_{self.name}",
            printer_id=printer_id,
            filename=self.name,
            file_size=self.size,
            file_type=FileType(Path(self.name).suffix.lower()),
            printer_path=self.path,
            created_on_printer=datetime.fromtimestamp(self.date)
        )
```

---

## Database ORM Models

### SQLAlchemy Models

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Numeric, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class PrinterORM(Base):
    """SQLAlchemy ORM model for printers table"""
    __tablename__ = "printers"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)
    model = Column(String(50))
    ip_address = Column(String(15), nullable=False)
    port = Column(Integer)
    api_key = Column(String(100))
    access_code = Column(String(20))
    serial_number = Column(String(30))
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(String(20), default="unknown")
    last_seen = Column(DateTime)
    firmware_version = Column(String(50))
    has_camera = Column(Boolean, default=False)
    has_ams = Column(Boolean, default=False)
    supports_remote_control = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Relationships
    jobs = relationship("JobORM", back_populates="printer", cascade="all, delete-orphan")
    files = relationship("FileORM", back_populates="printer")

class JobORM(Base):
    """SQLAlchemy ORM model for jobs table"""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    printer_id = Column(String(50), ForeignKey("printers.id"), nullable=False)
    job_name = Column(String(200), nullable=False)
    job_id_on_printer = Column(String(100))
    file_path = Column(String(500))
    status = Column(String(20), nullable=False, default="queued")
    progress = Column(Numeric(5, 2), default=0.0)
    layer_current = Column(Integer, default=0)
    layer_total = Column(Integer)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    estimated_duration = Column(Integer)
    actual_duration = Column(Integer)
    estimated_completion = Column(DateTime)
    material_type = Column(String(20))
    material_brand = Column(String(50))
    material_color = Column(String(30))
    material_estimated_usage = Column(Numeric(8, 3))
    material_actual_usage = Column(Numeric(8, 3))
    material_cost_per_gram = Column(Numeric(6, 4))
    layer_height = Column(Numeric(4, 2))
    infill_percentage = Column(Integer)
    print_speed = Column(Integer)
    nozzle_temperature = Column(Integer)
    bed_temperature = Column(Integer)
    supports_used = Column(Boolean, default=False)
    file_size = Column(Integer)
    file_hash = Column(String(64))
    material_cost = Column(Numeric(10, 2), default=0.0)
    power_cost = Column(Numeric(10, 2), default=0.0)
    labor_cost = Column(Numeric(10, 2), default=0.0)
    is_business = Column(Boolean, default=False, nullable=False)
    customer_order_id = Column(String(50))
    customer_name = Column(String(100))
    quality_rating = Column(Integer)
    first_layer_adhesion = Column(String(20))
    surface_finish = Column(String(20))
    dimensional_accuracy = Column(Numeric(5, 3))
    notes = Column(Text)
    failure_reason = Column(Text)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # Relationships
    printer = relationship("PrinterORM", back_populates="jobs")

class FileORM(Base):
    """SQLAlchemy ORM model for files table"""
    __tablename__ = "files"
    
    id = Column(String(100), primary_key=True)
    printer_id = Column(String(50), ForeignKey("printers.id"))
    filename = Column(String(200), nullable=False)
    original_filename = Column(String(200))
    file_type = Column(String(10), nullable=False)
    file_size = Column(Integer, nullable=False)
    printer_path = Column(String(500))
    local_path = Column(String(500))
    download_status = Column(String(20), default="available")
    download_attempts = Column(Integer, default=0)
    downloaded_at = Column(DateTime)
    last_download_attempt = Column(DateTime)
    download_error = Column(Text)
    checksum_md5 = Column(String(32))
    checksum_sha256 = Column(String(64))
    estimated_print_time = Column(Integer)
    layer_count = Column(Integer)
    layer_height = Column(Numeric(4, 2))
    infill_percentage = Column(Integer)
    material_type = Column(String(20))
    nozzle_temperature = Column(Integer)
    bed_temperature = Column(Integer)
    support_material = Column(Boolean)
    last_accessed = Column(DateTime)
    access_count = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    created_on_printer = Column(DateTime)
    
    # Relationships
    printer = relationship("PrinterORM", back_populates="files")
```

---

## Validation Rules

### Field Validation

```python
from pydantic import validator
import re

class PrinterValidation:
    @staticmethod
    @validator('ip_address')
    def validate_ip_address(cls, v):
        """Validate IPv4 address format"""
        if not re.match(r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', v):
            raise ValueError('Invalid IP address format')
        return v
    
    @staticmethod
    @validator('serial_number')
    def validate_serial_number(cls, v, values):
        """Validate serial number format for Bambu Lab printers"""
        printer_type = values.get('type')
        if printer_type == 'bambu_lab' and v and not re.match(r'^[A-Z]{2}\d{8}$', v):
            raise ValueError('Invalid Bambu Lab serial number format (expected: AA12345678)')
        return v

class JobValidation:
    @staticmethod
    @validator('progress')
    def validate_progress(cls, v):
        """Ensure progress is between 0 and 100"""
        if v < 0.0 or v > 100.0:
            raise ValueError('Progress must be between 0.0 and 100.0')
        return v
    
    @staticmethod
    @validator('layer_current')
    def validate_layer_current(cls, v, values):
        """Ensure current layer doesn't exceed total layers"""
        layer_total = values.get('layer_total')
        if layer_total and v > layer_total:
            raise ValueError('Current layer cannot exceed total layers')
        return v

class FileValidation:
    @staticmethod
    @validator('file_size')
    def validate_file_size(cls, v):
        """Ensure file size is reasonable (max 500MB)"""
        max_size = 500 * 1024 * 1024  # 500MB
        if v > max_size:
            raise ValueError(f'File size cannot exceed {max_size} bytes')
        return v
    
    @staticmethod
    @validator('filename')
    def sanitize_filename(cls, v):
        """Sanitize filename for security"""
        # Remove path separators and dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', v)
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        return sanitized
```

---

## Type Conversion Utilities

```python
from typing import Optional, Dict, Any
from datetime import datetime

class ModelConverter:
    """Utility class for converting between different model types"""
    
    @staticmethod
    def orm_to_domain_printer(orm: PrinterORM) -> Printer:
        """Convert ORM printer to domain model"""
        return Printer(
            id=orm.id,
            name=orm.name,
            type=PrinterType(orm.type),
            model=orm.model,
            ip_address=orm.ip_address,
            port=orm.port,
            api_key=orm.api_key,
            access_code=orm.access_code,
            serial_number=orm.serial_number,
            status=PrinterStatus(orm.status),
            is_active=orm.is_active,
            last_seen=orm.last_seen,
            firmware_version=orm.firmware_version,
            capabilities=PrinterCapabilities(
                has_camera=orm.has_camera,
                has_ams=orm.has_ams,
                supports_remote_control=orm.supports_remote_control
            ),
            created_at=orm.created_at,
            updated_at=orm.updated_at
        )
    
    @staticmethod
    def domain_to_response_printer(domain: Printer, include_stats: bool = False) -> PrinterResponse:
        """Convert domain printer to API response"""
        response = PrinterResponse(
            id=domain.id,
            name=domain.name,
            type=domain.type.value,
            model=domain.model,
            ip_address=domain.ip_address,
            status=domain.status.value,
            connection_status=domain.connection_status.value,
            is_active=domain.is_active,
            last_seen=domain.last_seen,
            created_at=domain.created_at,
            updated_at=domain.updated_at
        )
        
        if domain.temperatures:
            response.temperatures = PrinterTemperaturesResponse(
                nozzle=domain.temperatures.nozzle.current if domain.temperatures.nozzle else None,
                nozzle_target=domain.temperatures.nozzle.target if domain.temperatures.nozzle else None,
                bed=domain.temperatures.bed.current if domain.temperatures.bed else None,
                bed_target=domain.temperatures.bed.target if domain.temperatures.bed else None,
                chamber=domain.temperatures.chamber.current if domain.temperatures.chamber else None
            )
        
        if domain.capabilities:
            response.capabilities = PrinterCapabilitiesResponse(
                has_camera=domain.capabilities.has_camera,
                has_ams=domain.capabilities.has_ams,
                supports_remote_control=domain.capabilities.supports_remote_control,
                max_print_volume=domain.capabilities.max_print_volume,
                supported_materials=domain.capabilities.supported_materials or []
            )
        
        if include_stats and domain.statistics:
            response.statistics = PrinterStatisticsResponse(
                total_jobs=domain.statistics.total_jobs,
                successful_jobs=domain.statistics.successful_jobs,
                failed_jobs=domain.statistics.failed_jobs,
                total_print_time=domain.statistics.total_print_time,
                material_used_total=float(domain.statistics.material_used_total),
                success_rate=domain.statistics.success_rate
            )
        
        return response
```

This comprehensive data model specification provides type-safe, validated data structures for all aspects of the Printernizer Phase 1 system, ensuring consistent API contracts and reliable data handling throughout the application.