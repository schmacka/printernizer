# Printernizer Service Layer Architecture

## Overview

The Printernizer service architecture follows a modular, layered design that separates concerns and provides clear boundaries between different system components. This design enables maintainable, testable, and scalable code while supporting enterprise-grade features.

## Architecture Principles

### 1. **Separation of Concerns**
- Each service has a single responsibility
- Clear boundaries between business logic and data access
- API layer separated from business logic
- Printer-specific implementations isolated

### 2. **Dependency Injection**
- Services depend on abstractions, not implementations
- Configuration injected at startup
- Easy testing with mock implementations
- Runtime service discovery

### 3. **Event-Driven Architecture**
- Asynchronous communication between services
- Real-time updates via event streaming
- Loose coupling between components
- Scalable monitoring system

### 4. **Enterprise Patterns**
- Repository pattern for data access
- Service pattern for business logic
- Factory pattern for printer implementations
- Observer pattern for status monitoring

---

## Service Layer Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    Web API Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   REST API      │  │   WebSocket     │  │  Web UI      │ │
│  │   Controllers   │  │   Handlers      │  │  Routes      │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                  Business Service Layer                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Printer        │  │  Job            │  │  File        │ │
│  │  Service        │  │  Service        │  │  Service     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Analytics      │  │  Event          │  │  Config      │ │
│  │  Service        │  │  Service        │  │  Service     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                Integration Layer                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Bambu Lab      │  │  Prusa          │  │  File System │ │
│  │  Integration    │  │  Integration    │  │  Manager     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                 Data Access Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Database       │  │  Repository     │  │  Cache       │ │
│  │  Connection     │  │  Implementations│  │  Manager     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Services

### 1. Printer Service
**Responsibility**: Printer management, status monitoring, and communication coordination

```python
class PrinterService:
    """
    Central service for printer management and monitoring
    """
    
    async def get_all_printers() -> List[PrinterStatus]
    async def get_printer_by_id(printer_id: str) -> PrinterStatus
    async def add_printer(config: PrinterConfig) -> PrinterStatus
    async def update_printer(printer_id: str, updates: dict) -> PrinterStatus
    async def remove_printer(printer_id: str) -> bool
    async def test_connection(printer_id: str) -> ConnectionResult
    async def start_monitoring(printer_id: str) -> bool
    async def stop_monitoring(printer_id: str) -> bool
```

**Dependencies**:
- `PrinterRepository` - Data persistence
- `PrinterIntegrationFactory` - Printer-specific implementations
- `EventService` - Status change notifications
- `ConfigService` - Configuration management

**Integration Points**:
- Coordinates with `JobService` for active job tracking
- Publishes events to `EventService` for real-time updates
- Uses `AnalyticsService` for performance metrics

### 2. Job Service
**Responsibility**: Print job lifecycle management and tracking

```python
class JobService:
    """
    Service for managing print jobs across all printers
    """
    
    async def get_jobs(filters: JobFilters, pagination: Pagination) -> JobListResponse
    async def get_job_by_id(job_id: int) -> JobDetails
    async def create_job(job_data: CreateJobRequest) -> Job
    async def update_job(job_id: int, updates: dict) -> Job
    async def cancel_job(job_id: int) -> CancelResult
    async def get_active_jobs() -> List[Job]
    async def calculate_costs(job_id: int) -> CostBreakdown
```

**Dependencies**:
- `JobRepository` - Data persistence
- `PrinterService` - Printer status validation
- `AnalyticsService` - Cost calculations
- `EventService` - Job status notifications

**Business Rules**:
- Job status transitions validation
- Cost calculation based on material and power consumption
- Business vs private job categorization
- German timezone handling for business hours

### 3. File Service
**Responsibility**: File management, downloads, and organization (Drucker-Dateien system)

```python
class FileService:
    """
    Service for the Drucker-Dateien file management system
    """
    
    async def get_files(filters: FileFilters) -> FileListResponse
    async def get_file_by_id(file_id: str) -> FileDetails
    async def download_file(file_id: str) -> DownloadResult
    async def get_download_status(download_id: str) -> DownloadStatus
    async def cleanup_files(criteria: CleanupCriteria) -> CleanupResult
    async def get_cleanup_candidates(criteria: CleanupCriteria) -> List[FileCleanupCandidate]
```

**Dependencies**:
- `FileRepository` - Metadata persistence
- `FileSystemManager` - Local file operations
- `PrinterService` - Remote file access
- `DownloadManager` - Download coordination

**Features**:
- Unified view of local and remote files
- Smart download organization by printer/date
- Status tracking with visual indicators
- Automatic cleanup management

### 4. Analytics Service
**Responsibility**: Business analytics, cost calculations, and reporting

```python
class AnalyticsService:
    """
    Service for business analytics and cost calculations
    """
    
    async def get_overview_stats(period: TimePeriod) -> OverviewStats
    async def get_printer_stats(printer_id: str, period: TimePeriod) -> PrinterStats
    async def calculate_job_costs(job: Job) -> CostBreakdown
    async def get_material_usage(period: TimePeriod) -> MaterialUsageReport
    async def export_business_data(format: str, period: TimePeriod) -> ExportResult
```

**Dependencies**:
- `JobRepository` - Historical job data
- `ConfigService` - Cost configuration (material rates, power costs)
- `PrinterService` - Utilization metrics

**Business Features**:
- German business requirements compliance
- EUR currency calculations with VAT
- Material cost tracking per gram
- Power consumption calculations

### 5. Event Service
**Responsibility**: Real-time event distribution and WebSocket management

```python
class EventService:
    """
    Central event distribution service for real-time updates
    """
    
    async def publish_event(event: SystemEvent) -> bool
    async def subscribe_to_events(event_types: List[str], callback: Callable) -> str
    async def unsubscribe(subscription_id: str) -> bool
    async def get_websocket_manager() -> WebSocketManager
    async def broadcast_to_clients(message: dict) -> int
```

**Event Types**:
- `printer_status_changed` - Printer online/offline status
- `job_progress_updated` - Job progress updates
- `file_download_completed` - File download status
- `system_alert` - System notifications

**Integration**:
- All services publish events through this service
- WebSocket clients receive real-time updates
- Event history stored for debugging

### 6. Config Service
**Responsibility**: Configuration management and system settings

```python
class ConfigService:
    """
    Service for system configuration and settings
    """
    
    async def get_config(key: str, default=None) -> Any
    async def set_config(key: str, value: Any) -> bool
    async def get_config_by_category(category: str) -> dict
    async def validate_config(key: str, value: Any) -> ValidationResult
    async def reload_config() -> bool
```

**Configuration Categories**:
- `system` - Core system settings
- `business` - Business-specific configuration
- `monitoring` - Polling intervals and timeouts
- `files` - File management settings
- `costs` - Cost calculation parameters

---

## Integration Layer Services

### 1. Printer Integration Factory
**Responsibility**: Abstract printer communication and provide unified interface

```python
class PrinterIntegrationFactory:
    """
    Factory for creating printer-specific integration instances
    """
    
    def create_integration(printer_type: str, config: dict) -> BasePrinterIntegration
    def get_supported_types() -> List[str]
    def validate_config(printer_type: str, config: dict) -> ValidationResult
```

### 2. Base Printer Integration
**Responsibility**: Common interface for all printer types

```python
class BasePrinterIntegration(ABC):
    """
    Abstract base class for printer integrations
    """
    
    @abstractmethod
    async def connect() -> ConnectionResult
    
    @abstractmethod
    async def disconnect() -> bool
    
    @abstractmethod
    async def get_status() -> PrinterStatus
    
    @abstractmethod
    async def get_current_job() -> Optional[JobStatus]
    
    @abstractmethod
    async def list_files() -> List[RemoteFile]
    
    @abstractmethod
    async def download_file(file_path: str) -> bytes
    
    @abstractmethod
    async def cancel_job() -> CancelResult
```

### 3. Bambu Lab Integration
**Responsibility**: MQTT-based communication with Bambu Lab printers

```python
class BambuLabIntegration(BasePrinterIntegration):
    """
    Bambu Lab printer integration using MQTT protocol
    """
    
    # MQTT connection management
    async def _connect_mqtt() -> bool
    async def _subscribe_to_topics() -> bool
    async def _handle_mqtt_message(topic: str, payload: dict) -> None
    
    # Real-time status updates via MQTT callbacks
    async def _on_print_progress(data: dict) -> None
    async def _on_temperature_update(data: dict) -> None
    async def _on_job_complete(data: dict) -> None
```

**Key Features**:
- Event-driven MQTT callbacks
- Real-time temperature monitoring
- AMS (Automatic Material System) support
- Camera stream access (future enhancement)

### 4. Prusa Integration
**Responsibility**: HTTP API communication with Prusa printers

```python
class PrusaIntegration(BasePrinterIntegration):
    """
    Prusa printer integration using PrusaLink HTTP API
    """
    
    # HTTP API communication
    async def _make_request(method: str, endpoint: str, data=None) -> dict
    async def _poll_status() -> PrinterStatus
    async def _start_polling() -> None
    async def _stop_polling() -> None
```

**Key Features**:
- 30-second polling intervals
- RESTful API communication
- File upload/download support
- Historical job data access

---

## Data Access Layer

### 1. Repository Pattern Implementation

```python
class BaseRepository(ABC):
    """
    Base repository with common database operations
    """
    
    @abstractmethod
    async def get_by_id(self, id: Any) -> Optional[Model]
    
    @abstractmethod
    async def get_all(self, filters: dict = None) -> List[Model]
    
    @abstractmethod
    async def create(self, data: dict) -> Model
    
    @abstractmethod
    async def update(self, id: Any, data: dict) -> Model
    
    @abstractmethod
    async def delete(self, id: Any) -> bool

class PrinterRepository(BaseRepository):
    """Repository for printer data operations"""
    
    async def get_active_printers() -> List[Printer]
    async def get_by_type(printer_type: str) -> List[Printer]
    async def update_last_seen(printer_id: str) -> bool

class JobRepository(BaseRepository):
    """Repository for job data operations"""
    
    async def get_active_jobs() -> List[Job]
    async def get_jobs_by_printer(printer_id: str) -> List[Job]
    async def get_business_jobs(start_date: datetime, end_date: datetime) -> List[Job]
    async def update_progress(job_id: int, progress: float) -> bool

class FileRepository(BaseRepository):
    """Repository for file data operations"""
    
    async def get_by_download_status(status: str) -> List[File]
    async def get_cleanup_candidates(days_old: int) -> List[File]
    async def update_download_status(file_id: str, status: str) -> bool
```

### 2. Database Connection Management

```python
class DatabaseManager:
    """
    Database connection and transaction management
    """
    
    async def get_connection() -> sqlite3.Connection
    async def execute_query(query: str, params: tuple) -> Any
    async def execute_transaction(operations: List[Callable]) -> bool
    async def migrate_schema() -> bool
    async def health_check() -> bool
```

---

## Service Communication Patterns

### 1. Synchronous Service Calls
Used for immediate data retrieval and validation:

```python
# Example: Getting printer status for job validation
printer_status = await printer_service.get_printer_by_id(printer_id)
if printer_status.status != "online":
    raise PrinterOfflineError(f"Printer {printer_id} is offline")
```

### 2. Asynchronous Event Publishing
Used for loosely coupled notifications:

```python
# Example: Publishing job completion event
await event_service.publish_event(JobCompletedEvent(
    job_id=job.id,
    printer_id=job.printer_id,
    status="completed",
    duration=job.actual_duration
))
```

### 3. Background Task Processing
Used for long-running operations:

```python
# Example: File download processing
async def download_file_background(file_id: str) -> None:
    file_service = get_file_service()
    result = await file_service.download_file(file_id)
    await event_service.publish_event(FileDownloadCompletedEvent(
        file_id=file_id,
        status=result.status,
        local_path=result.local_path
    ))
```

---

## Error Handling Strategy

### 1. Service-Level Exceptions
```python
class PrinterServiceException(Exception):
    """Base exception for printer service errors"""

class PrinterOfflineError(PrinterServiceException):
    """Printer is not reachable"""

class InvalidPrinterConfigError(PrinterServiceException):
    """Printer configuration is invalid"""

class JobServiceException(Exception):
    """Base exception for job service errors"""

class JobNotFoundError(JobServiceException):
    """Requested job does not exist"""
```

### 2. Graceful Degradation
- Printer offline: Continue monitoring other printers
- Database unavailable: Cache operations and retry
- File download failed: Mark for retry and notify user
- API rate limit: Implement exponential backoff

### 3. Circuit Breaker Pattern
For external integrations (printer APIs):

```python
class CircuitBreaker:
    """
    Circuit breaker for printer API calls
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
```

---

## Testing Strategy

### 1. Unit Testing
- Each service tested in isolation
- Mock dependencies using interfaces
- Test business logic thoroughly
- Achieve >90% code coverage

### 2. Integration Testing
- Test service interactions
- Database operations with test database
- Printer API communication with mock servers
- File system operations with temporary directories

### 3. End-to-End Testing
- Full workflow testing via API
- WebSocket communication testing
- Real printer integration testing (manual)
- Performance testing under load

---

## Performance Considerations

### 1. Caching Strategy
- Printer status cached for 5 seconds
- Configuration cached until restart
- File metadata cached for 1 minute
- Analytics results cached for 15 minutes

### 2. Database Optimization
- Connection pooling for concurrent access
- Indexed queries for common operations
- Pagination for large result sets
- Bulk operations for data imports

### 3. Asynchronous Processing
- Non-blocking I/O for all network operations
- Background tasks for long-running operations
- Event-driven architecture for real-time updates
- Connection pooling for external APIs

---

## Security Considerations

### 1. API Security
- Rate limiting per client IP
- Input validation and sanitization
- SQL injection prevention
- CORS configuration for web clients

### 2. Printer Communication Security
- Encrypted credentials storage
- Network timeouts and retries
- Certificate validation for HTTPS
- Access code rotation (manual)

### 3. File System Security
- Restricted download directories
- File name sanitization
- Size limits for downloads
- Checksum verification

---

This service architecture provides a robust foundation for the Printernizer Phase 1 implementation, with clear separation of concerns, enterprise patterns, and extensibility for future enhancements.