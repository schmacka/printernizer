# Phase 3 Remaining Work - Continuation Prompt

**Date:** November 8, 2025
**Previous Branch:** `claude/phase2-circular-deps-exceptions-011CUvdXK774raQC8dEGAzsC` (completed)
**Current Progress:** Phases 1 & 2 Complete (100%), Phase 3 Pending
**Remaining Work:** 30-40 hours (Medium Priority)

---

## Context

You are continuing technical debt reduction for the Printernizer project. **Phases 1 and 2 are now 100% complete.** Phase 3 focuses on **Medium Priority** improvements to code documentation, configuration management, and testing.

### ✅ Completed Work (Phases 1 & 2)

**Phase 1 - Critical Fixes (70 minutes):**
- Fixed `None.copy()` crash bug
- Removed hardcoded printer IDs
- Fixed path traversal vulnerabilities
- Implemented credential masking

**Phase 2 - High Priority (58 hours):**
- Refactored FileService (1,187 LOC → 4 specialized services)
- Refactored PrinterService (985 LOC → 3 specialized services)
- Eliminated all bare exception handlers
- Resolved circular dependencies with late binding
- Implemented event-driven architecture
- Standardized pagination across APIs
- Fixed async task cleanup
- Created comprehensive documentation

**Key Documentation Created in Phase 2:**
- `docs/EVENT_CONTRACTS.md` - 40+ events documented
- `docs/EVENT_FLOWS.md` - Visual workflow diagrams
- `docs/CIRCULAR_DEPENDENCY_AUDIT.md` - Dependency analysis
- `docs/EXCEPTION_HANDLING_AUDIT.md` - Exception handling audit
- `docs/PHASE2_COMPLETION_SUMMARY.md` - Complete Phase 2 summary
- `.claude/skills/printernizer-architecture.md` - Architecture patterns

**Current Codebase State:**
- ✅ Zero circular dependencies
- ✅ Zero bare exception handlers
- ✅ Event-driven architecture implemented
- ✅ Services properly decomposed
- ✅ Excellent exception handling
- ⏳ Documentation gaps remain (Phase 3)
- ⏳ Magic numbers hardcoded (Phase 3)
- ⏳ Test coverage incomplete (Phase 3)

---

## Phase 3 Overview

**Priority Level:** Medium
**Estimated Effort:** 30-40 hours
**Focus Areas:** Code documentation, configuration management, testing, and code clarity

**Objectives:**
1. Add comprehensive docstrings to all public APIs
2. Move magic numbers to configuration
3. Expand test coverage to >85%
4. Standardize error handling patterns
5. Add settings validation
6. Document complex logic with inline comments

---

## Phase 3 Tasks

### Task 1: Missing Docstrings (6 hours)

**Status:** PENDING

**Objective:** Add comprehensive docstrings to all public methods, classes, and modules.

#### 1.1 Service Documentation (3 hours)

**Target Files:**
```
src/services/
├── file_discovery_service.py
├── file_download_service.py
├── file_thumbnail_service.py
├── file_metadata_service.py
├── printer_connection_service.py
├── printer_monitoring_service.py
├── printer_control_service.py
├── job_service.py
├── library_service.py
├── material_service.py
├── trending_service.py
├── timelapse_service.py
├── file_watcher_service.py
├── analytics_service.py
└── config_service.py
```

**Docstring Format (Google Style):**
```python
def download_file(self, printer_id: str, filename: str) -> Dict[str, Any]:
    """
    Download a file from a printer to local storage.

    This method coordinates the file download process including:
    - Fetching the file from the printer via its API
    - Saving to local disk with proper organization
    - Updating database records
    - Emitting events for thumbnail processing

    Args:
        printer_id: Unique identifier for the printer
        filename: Name of the file on the printer to download

    Returns:
        Dictionary containing:
            - status (str): "success" or "error"
            - file_id (str): Database ID of downloaded file (if success)
            - file_path (str): Local path to downloaded file (if success)
            - message (str): Error message (if error)

    Raises:
        ConnectionError: If printer is unreachable
        FileNotFoundError: If file doesn't exist on printer
        PermissionError: If insufficient permissions

    Events Emitted:
        - file_download_started: When download begins
        - file_download_complete: On successful download
        - file_download_failed: On error
        - file_needs_thumbnail_processing: After successful download

    Example:
        >>> result = await file_service.download_file("bambu_001", "model.3mf")
        >>> print(result["status"])
        'success'

    See Also:
        - FileDownloadService: Handles the actual download logic
        - EVENT_CONTRACTS.md: Event payload schemas
    """
```

**Priorities:**
1. **High Priority (must have):**
   - All service public methods
   - All API router endpoints
   - All model classes

2. **Medium Priority (should have):**
   - Private methods with complex logic
   - Utility functions
   - Database methods

3. **Low Priority (nice to have):**
   - Simple getter/setter methods
   - Obvious helper functions

**Quality Standards:**
- Explain **what** the method does
- Explain **why** it's needed (if not obvious)
- Document all parameters with types
- Document return values with structure
- List exceptions that can be raised
- List events emitted (if applicable)
- Include usage examples for complex methods
- Add "See Also" references where helpful

**Tools:**
```bash
# Check docstring coverage
pip install interrogate
interrogate src/ --fail-under=85

# Generate documentation
pip install pdoc3
pdoc --html --output-dir docs/api src/
```

#### 1.2 API Router Documentation (2 hours)

**Target Files:**
```
src/api/routers/
├── printers.py
├── jobs.py
├── files.py
├── analytics.py
├── library.py
├── materials.py
├── trending.py
├── timelapses.py
└── search.py
```

**FastAPI Docstring Format:**
```python
@router.post("")
async def create_printer(
    printer: PrinterCreate,
    config_service: ConfigService = Depends(get_config_service)
):
    """
    Add a new printer to the system.

    Creates a new printer configuration and attempts to establish
    a connection. The printer will be added to the database and
    monitoring will begin automatically if connection succeeds.

    **Authentication:** None required

    **Rate Limiting:** 10 requests per minute

    **Request Body:**
    ```json
    {
        "name": "Bambu Lab A1",
        "type": "bambu_lab",
        "ip_address": "192.168.1.100",
        "access_code": "12345678",
        "serial_number": "ABC123"
    }
    ```

    **Response (Success - 201 Created):**
    ```json
    {
        "status": "success",
        "data": {
            "printer_id": "uuid-here",
            "name": "Bambu Lab A1",
            "type": "bambu_lab",
            "status": "connected"
        }
    }
    ```

    **Response (Error - 400 Bad Request):**
    ```json
    {
        "status": "error",
        "message": "Invalid printer configuration",
        "details": {
            "field": "ip_address",
            "error": "Invalid IP address format"
        }
    }
    ```

    **Possible Errors:**
    - 400: Invalid printer configuration
    - 409: Printer already exists (duplicate IP or serial)
    - 500: Internal server error

    **Events Emitted:**
    - `printer_connected`: If connection successful
    - `printer_connection_progress`: During connection attempt

    **See Also:**
    - DELETE /api/v1/printers/{printer_id} - Remove printer
    - GET /api/v1/printers - List all printers
    """
```

**Include:**
- Clear description of what endpoint does
- Authentication requirements
- Request body schema with example
- Response schemas for success and error cases
- Possible HTTP status codes
- Events emitted
- Related endpoints

#### 1.3 Model Documentation (1 hour)

**Target Files:**
```
src/models/
├── printer.py
├── job.py
├── file.py
├── material.py
├── timelapse.py
└── watch_folder.py
```

**Pydantic Model Docstring Format:**
```python
class PrinterCreate(BaseModel):
    """
    Schema for creating a new printer configuration.

    This model validates all required fields for adding a printer
    to the system. Different printer types have different required
    fields (e.g., Bambu Lab needs access_code, Prusa needs api_key).

    Attributes:
        name: Display name for the printer (shown in UI)
        type: Printer type - must be "bambu_lab" or "prusa_core"
        ip_address: IP address or hostname of the printer
        access_code: Bambu Lab access code (required for bambu_lab)
        api_key: PrusaLink API key (required for prusa_core)
        serial_number: Optional printer serial number

    Validation:
        - name: 1-100 characters
        - type: Must be valid printer type
        - ip_address: Valid IP address or hostname
        - access_code: 8 digits (if type is bambu_lab)
        - api_key: Non-empty (if type is prusa_core)

    Example:
        >>> printer = PrinterCreate(
        ...     name="My Bambu A1",
        ...     type="bambu_lab",
        ...     ip_address="192.168.1.100",
        ...     access_code="12345678"
        ... )

    See Also:
        - PrinterUpdate: For updating existing printers
        - PrinterResponse: For API responses
    """
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., pattern="^(bambu_lab|prusa_core)$")
    ip_address: str
    access_code: Optional[str] = None
    api_key: Optional[str] = None
    serial_number: Optional[str] = None

    @field_validator("ip_address")
    def validate_ip(cls, v):
        """Validate IP address format."""
        # ... validation logic
```

**Include:**
- Model purpose and usage
- Field descriptions
- Validation rules
- Usage examples
- Related models

---

### Task 2: Hardcoded Magic Numbers (4 hours)

**Status:** PENDING

**Objective:** Move hardcoded values to configuration files or constants.

#### 2.1 Identify Magic Numbers (1 hour)

**Search for magic numbers:**
```bash
# Common patterns to search for
grep -rn "sleep([0-9]" src/services/
grep -rn "timeout=[0-9]" src/services/
grep -rn "max_retries = [0-9]" src/services/
grep -rn "limit = [0-9]" src/api/
grep -rn "if .* > [0-9]" src/services/
```

**Common magic numbers found in Phase 2 assessment:**
- Retry counts (3, 5)
- Timeout values (30, 60, 120 seconds)
- Polling intervals (10s, 30s, 300s)
- Pagination limits (50, 100)
- Threshold percentages (20% for low stock)
- File size limits
- Background task intervals

**Create inventory:** `docs/MAGIC_NUMBERS_INVENTORY.md`

#### 2.2 Create Configuration Constants (2 hours)

**Create:** `src/config/constants.py`

```python
"""
Configuration constants for Printernizer.

This module contains all hardcoded values that were previously
scattered throughout the codebase. Values are organized by domain.

All values can be overridden via environment variables or settings.
"""

# Network & Connection
NETWORK_TIMEOUT_SECONDS = 30
NETWORK_MAX_RETRIES = 3
NETWORK_RETRY_DELAY_SECONDS = 2
FTP_CONNECTION_TIMEOUT = 30
FTP_MAX_RETRIES = 3

# Background Tasks
PRINTER_MONITORING_INTERVAL_SECONDS = 30
JOB_MONITORING_INTERVAL_SECONDS = 10
FILE_DISCOVERY_INTERVAL_SECONDS = 300  # 5 minutes
TIMELAPSE_FOLDER_SCAN_INTERVAL = 30

# Pagination
DEFAULT_PAGE_LIMIT = 50
MAX_PAGE_LIMIT = 1000
DEFAULT_PAGE_OFFSET = 0

# Thresholds
MATERIAL_LOW_STOCK_THRESHOLD_PERCENT = 20
JOB_PROGRESS_UPDATE_THRESHOLD_PERCENT = 10  # Emit event every 10%

# File Operations
MAX_FILE_SIZE_MB = 500
THUMBNAIL_MAX_SIZE_PX = 512
THUMBNAIL_QUALITY_PERCENT = 85
THUMBNAIL_CACHE_DAYS = 30

# Retry Behavior
TRANSIENT_ERROR_RETRY_COUNT = 3
TRANSIENT_ERROR_BACKOFF_BASE = 2  # Exponential backoff multiplier
TRANSIENT_ERROR_BACKOFF_MIN = 2   # Min wait seconds
TRANSIENT_ERROR_BACKOFF_MAX = 10  # Max wait seconds

# Database
DATABASE_QUERY_TIMEOUT = 30
DATABASE_CONNECTION_POOL_SIZE = 5

# Security
MAX_LOGIN_ATTEMPTS = 5
SESSION_TIMEOUT_MINUTES = 60
API_RATE_LIMIT_PER_MINUTE = 100


def get_constant(name: str, default: Any = None) -> Any:
    """
    Get a constant value with optional environment variable override.

    Args:
        name: Constant name (e.g., "NETWORK_TIMEOUT_SECONDS")
        default: Default value if not found

    Returns:
        Constant value from module or environment variable

    Example:
        >>> timeout = get_constant("NETWORK_TIMEOUT_SECONDS", 30)
    """
    import os
    # Check environment variable first (with prefix)
    env_name = f"PRINTERNIZER_{name}"
    if env_name in os.environ:
        value = os.environ[env_name]
        # Try to cast to same type as default
        if default is not None:
            return type(default)(value)
        return value

    # Return module constant
    return globals().get(name, default)
```

**Also update:** `src/utils/config.py` to include these constants

#### 2.3 Replace Magic Numbers (1 hour)

**Pattern:**

Before:
```python
await asyncio.sleep(30)  # Magic number!
```

After:
```python
from src.config.constants import PRINTER_MONITORING_INTERVAL_SECONDS

await asyncio.sleep(PRINTER_MONITORING_INTERVAL_SECONDS)
```

**Search and replace examples:**
```python
# Timeouts
timeout=30 → timeout=NETWORK_TIMEOUT_SECONDS

# Retry counts
max_retries = 3 → max_retries = NETWORK_MAX_RETRIES

# Polling intervals
await asyncio.sleep(30) → await asyncio.sleep(PRINTER_MONITORING_INTERVAL_SECONDS)

# Pagination
limit = 50 → limit = DEFAULT_PAGE_LIMIT

# Thresholds
if percentage < 20 → if percentage < MATERIAL_LOW_STOCK_THRESHOLD_PERCENT
```

**Files to update (high priority):**
- `src/services/event_service.py` - Background task intervals
- `src/services/printer_monitoring_service.py` - Monitoring intervals
- `src/services/bambu_ftp_service.py` - FTP timeouts/retries
- `src/services/material_service.py` - Low stock threshold
- `src/api/routers/*.py` - Pagination defaults

---

### Task 3: Test Coverage Expansion (12-15 hours)

**Status:** PENDING

**Current Coverage:** Unknown
**Target Coverage:** >85%

#### 3.1 Set Up Test Infrastructure (2 hours)

**Install dependencies:**
```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

**Create:** `pytest.ini`
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow-running tests
    network: Tests requiring network access
```

**Create:** `tests/conftest.py`
```python
"""
Pytest configuration and fixtures for Printernizer tests.
"""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from src.database.database import Database
from src.services.event_service import EventService
from src.services.config_service import ConfigService


@pytest.fixture
async def database():
    """Create test database."""
    db = Database(":memory:")
    await db.initialize()
    yield db
    await db.close()


@pytest.fixture
def event_service():
    """Create event service."""
    return EventService()


@pytest.fixture
async def config_service(database):
    """Create config service."""
    return ConfigService(database)


@pytest.fixture
def mock_printer():
    """Create mock printer instance."""
    printer = AsyncMock()
    printer.name = "Test Printer"
    printer.is_connected = True
    printer.get_status = AsyncMock(return_value={
        "status": "idle",
        "temperature": {"nozzle": 25, "bed": 25}
    })
    return printer


# Add more fixtures as needed
```

#### 3.2 Unit Tests for Services (6 hours)

**Priority order:**
1. **Critical services (3 hours):**
   - FileDownloadService
   - PrinterConnectionService
   - JobService

2. **Domain services (2 hours):**
   - LibraryService
   - MaterialService
   - TrendingService

3. **Support services (1 hour):**
   - ThumbnailService
   - FileWatcherService

**Example test structure:**

Create: `tests/services/test_file_download_service.py`
```python
"""
Unit tests for FileDownloadService.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from src.services.file_download_service import FileDownloadService


@pytest.fixture
async def download_service(database, event_service):
    """Create FileDownloadService instance."""
    return FileDownloadService(database, event_service)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_download_file_success(download_service):
    """Test successful file download."""
    # Arrange
    printer_id = "test_printer"
    filename = "model.3mf"

    # Mock printer instance
    mock_printer = AsyncMock()
    mock_printer.download_file = AsyncMock(return_value=b"file contents")

    # Mock get_printer_instance
    with patch.object(download_service, 'get_printer_instance',
                     return_value=mock_printer):
        # Act
        result = await download_service.download_file(printer_id, filename)

        # Assert
        assert result["status"] == "success"
        assert "file_id" in result
        assert Path(result["file_path"]).exists()

        # Verify events were emitted
        # (would need to capture events from mock event_service)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_download_file_not_found(download_service):
    """Test download when file doesn't exist."""
    # Arrange
    printer_id = "test_printer"
    filename = "nonexistent.3mf"

    mock_printer = AsyncMock()
    mock_printer.download_file = AsyncMock(
        side_effect=FileNotFoundError("File not found")
    )

    with patch.object(download_service, 'get_printer_instance',
                     return_value=mock_printer):
        # Act
        result = await download_service.download_file(printer_id, filename)

        # Assert
        assert result["status"] == "error"
        assert "File not found" in result["message"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_download_file_connection_error(download_service):
    """Test download when printer is unreachable."""
    # Arrange
    printer_id = "test_printer"
    filename = "model.3mf"

    mock_printer = AsyncMock()
    mock_printer.download_file = AsyncMock(
        side_effect=ConnectionError("Printer offline")
    )

    with patch.object(download_service, 'get_printer_instance',
                     return_value=mock_printer):
        # Act
        result = await download_service.download_file(printer_id, filename)

        # Assert
        assert result["status"] == "error"
        assert "connection" in result["message"].lower()


# Add more test cases:
# - Test with invalid printer_id
# - Test with various file types
# - Test event emissions
# - Test database updates
# - Test concurrent downloads
```

**Test Coverage Goals:**
- Happy path (success case)
- Error paths (all exception types)
- Edge cases (empty files, large files, special characters)
- Concurrent operations
- Event emissions
- Database operations

#### 3.3 Integration Tests (3-4 hours)

**Create:** `tests/integration/test_file_workflow.py`

```python
"""
Integration tests for complete file workflows.
"""
import pytest
from pathlib import Path

from src.services.file_service import FileService
from src.services.printer_service import PrinterService


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_file_download_workflow(
    database, event_service, config_service, tmp_path
):
    """
    Test complete workflow: discover -> download -> thumbnails -> metadata.

    This integration test verifies that:
    1. File discovery finds files on printer
    2. Download service downloads the file
    3. Thumbnail service extracts thumbnails
    4. Metadata service extracts metadata
    5. All events are emitted correctly
    6. Database is updated correctly
    """
    # Setup services
    printer_service = PrinterService(database, event_service, config_service)
    file_service = FileService(
        database, event_service, None,
        printer_service, config_service, None
    )

    # Track events
    events_emitted = []

    def capture_event(event_type):
        def handler(data):
            events_emitted.append({"type": event_type, "data": data})
        return handler

    event_service.subscribe("file_download_started", capture_event("file_download_started"))
    event_service.subscribe("file_download_complete", capture_event("file_download_complete"))
    event_service.subscribe("file_thumbnails_processed", capture_event("file_thumbnails_processed"))

    # Act: Discover and download file
    # (Would need mock printer or test fixture)

    # Assert: Verify complete workflow
    assert len(events_emitted) >= 3
    assert events_emitted[0]["type"] == "file_download_started"
    assert events_emitted[-1]["type"] == "file_thumbnails_processed"
```

**Integration test areas:**
1. Complete file download workflow
2. Printer connection → monitoring → control
3. Job creation → updates → completion
4. Material usage tracking
5. Library file management
6. Event-driven service communication

#### 3.4 API Tests (1-2 hours)

**Create:** `tests/api/test_printers_endpoints.py`

```python
"""
API endpoint tests for printers router.
"""
import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_list_printers(client):
    """Test GET /api/v1/printers."""
    response = client.get("/api/v1/printers")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "data" in data
    assert isinstance(data["data"], list)


def test_create_printer_valid(client):
    """Test POST /api/v1/printers with valid data."""
    printer_data = {
        "name": "Test Printer",
        "type": "bambu_lab",
        "ip_address": "192.168.1.100",
        "access_code": "12345678"
    }

    response = client.post("/api/v1/printers", json=printer_data)

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert "printer_id" in data["data"]


def test_create_printer_invalid_type(client):
    """Test POST /api/v1/printers with invalid type."""
    printer_data = {
        "name": "Test Printer",
        "type": "invalid_type",
        "ip_address": "192.168.1.100"
    }

    response = client.post("/api/v1/printers", json=printer_data)

    assert response.status_code == 400
```

**Test all endpoints:**
- GET, POST, PUT, DELETE for each resource
- Query parameters
- Pagination
- Error cases (400, 404, 500)
- Authentication (if applicable)

#### 3.5 Generate Coverage Report (1 hour)

```bash
# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Check coverage threshold
pytest --cov=src --cov-fail-under=85
```

**Create:** `docs/TEST_COVERAGE_REPORT.md` with:
- Current coverage percentage
- Coverage by module
- Uncovered lines
- Recommendations for additional tests

---

### Task 4: Inconsistent Error Handling Patterns (4 hours)

**Status:** PENDING

**Objective:** Standardize error response formats and error handling patterns across all API endpoints.

#### 4.1 Audit Current Error Handling (1 hour)

**Search for error response patterns:**
```bash
# Find different error response formats
grep -rn "return.*error" src/api/routers/
grep -rn "raise HTTPException" src/api/routers/
grep -rn "JSONResponse" src/api/routers/
```

**Document patterns found:** `docs/ERROR_HANDLING_PATTERNS.md`

**Common inconsistencies:**
- Some endpoints return `{"error": "message"}`
- Some return `{"status": "error", "message": "..."}`
- Some raise HTTPException directly
- Some return different status codes for same error type

#### 4.2 Create Error Handling Standards (1 hour)

**Create:** `src/utils/errors.py`

```python
"""
Standardized error handling for Printernizer API.

This module provides consistent error response formats and
exception classes for all API endpoints.
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse


class PrinternizerError(Exception):
    """Base exception for Printernizer errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class PrinterNotFoundError(PrinternizerError):
    """Printer not found."""

    def __init__(self, printer_id: str):
        super().__init__(
            message=f"Printer not found: {printer_id}",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"printer_id": printer_id}
        )


class FileNotFoundError(PrinternizerError):
    """File not found."""

    def __init__(self, file_id: str):
        super().__init__(
            message=f"File not found: {file_id}",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"file_id": file_id}
        )


class PrinterConnectionError(PrinternizerError):
    """Printer connection failed."""

    def __init__(self, printer_id: str, reason: str):
        super().__init__(
            message=f"Failed to connect to printer: {reason}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"printer_id": printer_id, "reason": reason}
        )


def error_response(
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Create a standardized error response.

    Args:
        message: Error message
        status_code: HTTP status code
        details: Additional error details

    Returns:
        JSONResponse with standardized error format

    Example:
        >>> return error_response("Printer not found", 404, {"printer_id": "123"})
    """
    content = {
        "status": "error",
        "message": message,
        "details": details or {}
    }
    return JSONResponse(status_code=status_code, content=content)


def success_response(
    data: Any,
    status_code: int = status.HTTP_200_OK,
    message: Optional[str] = None
) -> JSONResponse:
    """
    Create a standardized success response.

    Args:
        data: Response data
        status_code: HTTP status code
        message: Optional success message

    Returns:
        JSONResponse with standardized success format

    Example:
        >>> return success_response({"printer_id": "123"}, 201, "Printer created")
    """
    content = {
        "status": "success",
        "data": data
    }
    if message:
        content["message"] = message
    return JSONResponse(status_code=status_code, content=content)


# Exception handler for FastAPI
async def printernizer_exception_handler(request, exc: PrinternizerError):
    """Global exception handler for Printernizer errors."""
    return error_response(
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details
    )
```

**Add to main.py:**
```python
from src.utils.errors import PrinternizerError, printernizer_exception_handler

app.add_exception_handler(PrinternizerError, printernizer_exception_handler)
```

#### 4.3 Update All API Endpoints (2 hours)

**Pattern:**

Before:
```python
@router.get("/{printer_id}")
async def get_printer(printer_id: str):
    printer = await printer_service.get_printer(printer_id)
    if not printer:
        return {"error": "Printer not found"}  # Inconsistent!
    return {"data": printer}
```

After:
```python
from src.utils.errors import PrinterNotFoundError, success_response

@router.get("/{printer_id}")
async def get_printer(printer_id: str):
    printer = await printer_service.get_printer(printer_id)
    if not printer:
        raise PrinterNotFoundError(printer_id)
    return success_response(printer)
```

**Update all routers:**
- `src/api/routers/printers.py`
- `src/api/routers/jobs.py`
- `src/api/routers/files.py`
- `src/api/routers/library.py`
- `src/api/routers/materials.py`
- `src/api/routers/analytics.py`
- `src/api/routers/trending.py`
- `src/api/routers/timelapses.py`

---

### Task 5: Settings Validation (3 hours)

**Status:** PENDING

**Objective:** Add comprehensive validation for all configuration settings.

#### 5.1 Configuration Validation Schema (1 hour)

**Update:** `src/utils/config.py`

```python
from pydantic import BaseSettings, Field, validator, root_validator
from pathlib import Path
from typing import Optional, List
import ipaddress


class Settings(BaseSettings):
    """Application settings with comprehensive validation."""

    # Database
    database_path: Path = Field(
        default=Path("./data/printernizer.db"),
        description="Path to SQLite database file"
    )

    @validator("database_path")
    def validate_database_path(cls, v):
        """Ensure database directory exists or can be created."""
        v = Path(v)
        v.parent.mkdir(parents=True, exist_ok=True)
        return v

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(
        default=8000,
        ge=1024,  # Greater than or equal to 1024
        le=65535,  # Less than or equal to 65535
        description="Server port"
    )

    @validator("host")
    def validate_host(cls, v):
        """Validate host is valid IP or hostname."""
        if v not in ["0.0.0.0", "localhost"]:
            try:
                ipaddress.ip_address(v)
            except ValueError:
                # Check if valid hostname
                if not v.replace(".", "").replace("-", "").isalnum():
                    raise ValueError(f"Invalid host: {v}")
        return v

    # File paths
    download_path: Path = Field(
        default=Path("./data/downloads"),
        description="Path for downloaded files"
    )
    library_path: Path = Field(
        default=Path("./data/library"),
        description="Path for library files"
    )

    @validator("download_path", "library_path")
    def validate_paths(cls, v):
        """Ensure paths exist or can be created."""
        v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v

    # Feature flags
    watch_folders_enabled: bool = Field(
        default=False,
        description="Enable automatic file watching"
    )
    timelapse_enabled: bool = Field(
        default=True,
        description="Enable timelapse video creation"
    )

    # Limits
    max_file_size_mb: int = Field(
        default=500,
        ge=1,
        le=5000,
        description="Maximum file size in MB"
    )
    max_concurrent_downloads: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum concurrent downloads"
    )

    class Config:
        env_prefix = "PRINTERNIZER_"
        case_sensitive = False

    @root_validator
    def validate_settings_combination(cls, values):
        """Validate combinations of settings."""
        # Example: If watch folders enabled, ensure library is enabled
        if values.get("watch_folders_enabled"):
            if not values.get("library_path"):
                raise ValueError(
                    "watch_folders_enabled requires library_path to be set"
                )
        return values
```

#### 5.2 Printer Configuration Validation (1 hour)

**Update:** `src/services/config_service.py`

Add comprehensive validation for printer configurations:

```python
def validate_printer_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate printer configuration.

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Type validation
    printer_type = config.get("type")
    if printer_type not in ["bambu_lab", "prusa_core"]:
        return False, f"Invalid printer type: {printer_type}"

    # IP address validation
    ip_address = config.get("ip_address")
    if not ip_address:
        return False, "IP address is required"

    try:
        ipaddress.ip_address(ip_address)
    except ValueError:
        return False, f"Invalid IP address: {ip_address}"

    # Type-specific validation
    if printer_type == "bambu_lab":
        access_code = config.get("access_code")
        if not access_code:
            return False, "Bambu Lab printers require access_code"
        if not access_code.isdigit() or len(access_code) != 8:
            return False, "access_code must be 8 digits"

    elif printer_type == "prusa_core":
        api_key = config.get("api_key")
        if not api_key:
            return False, "Prusa printers require api_key"
        if len(api_key) < 16:
            return False, "api_key must be at least 16 characters"

    return True, ""
```

#### 5.3 Runtime Validation Tests (1 hour)

**Create:** `tests/test_config_validation.py`

```python
"""
Tests for configuration validation.
"""
import pytest
from src.utils.config import Settings


def test_valid_settings():
    """Test valid settings."""
    settings = Settings(
        database_path="./data/test.db",
        host="127.0.0.1",
        port=8000
    )
    assert settings.port == 8000


def test_invalid_port_too_low():
    """Test port validation - too low."""
    with pytest.raises(ValueError):
        Settings(port=80)  # Below 1024


def test_invalid_port_too_high():
    """Test port validation - too high."""
    with pytest.raises(ValueError):
        Settings(port=99999)  # Above 65535


def test_invalid_host():
    """Test host validation - invalid format."""
    with pytest.raises(ValueError):
        Settings(host="invalid host!")


def test_paths_created():
    """Test that paths are created automatically."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        settings = Settings(download_path=f"{tmpdir}/downloads")
        assert settings.download_path.exists()
```

---

### Task 6: Complex Logic Comments (6 hours)

**Status:** PENDING

**Objective:** Add inline comments to complex algorithms and business logic.

#### 6.1 Identify Complex Logic (2 hours)

**Criteria for "complex":**
- Cyclomatic complexity > 10
- Nested loops/conditionals > 3 levels
- Non-obvious algorithms
- Business logic with multiple rules
- Regex patterns
- Mathematical calculations

**Use tool to identify:**
```bash
pip install radon
radon cc src/services/ -s -a  # Cyclomatic complexity
radon mi src/services/ -s     # Maintainability index
```

**Create inventory:** `docs/COMPLEX_LOGIC_INVENTORY.md`

**Common complex areas:**
- Auto-download filename matching logic (PrinterMonitoringService)
- Thumbnail extraction from 3MF files
- FTP file listing parsing
- Job status state machine logic
- File metadata parsing (GCODE)
- Trending algorithm calculations

#### 6.2 Add Inline Comments (3 hours)

**Pattern:**

Before:
```python
def _attempt_download_variants(self, filename):
    simple = filename.replace('(', '').replace(')', '').replace(',', '').replace('  ', ' ').strip()
    underscore = simple.replace(' ', '_')
    variants = [filename, simple, underscore]
    for v in variants:
        if self._try_download(v):
            return True
    return False
```

After:
```python
def _attempt_download_variants(self, filename):
    """
    Try downloading file with multiple filename variants.

    Bambu Lab printers sometimes report filenames differently than
    they're stored in the cache directory. This method tries common
    transformations to find the correct filename.

    Transformations attempted:
    1. Exact filename as reported
    2. Remove special characters: ( ) ,
    3. Replace spaces with underscores
    """
    # Remove problematic characters that may be stripped by printer
    # (parentheses and commas are often removed from filenames)
    simple = filename.replace('(', '').replace(')', '').replace(',', '')

    # Normalize multiple spaces to single space
    simple = simple.replace('  ', ' ').strip()

    # Try underscore version (some systems convert spaces to underscores)
    underscore = simple.replace(' ', '_')

    # Build list of variants to try, in order of likelihood
    variants = [
        filename,      # Original as reported (most likely)
        simple,        # Without special chars (second most likely)
        underscore     # With underscores (least likely but possible)
    ]

    # Try each variant until one succeeds
    for variant in variants:
        if self._try_download(variant):
            logger.info("Download succeeded with variant",
                       original=filename,
                       variant=variant)
            return True

    # All variants failed
    logger.warning("All filename variants failed",
                  original=filename,
                  variants_tried=len(variants))
    return False
```

**Comment Guidelines:**
- Explain **why**, not **what** (code shows what)
- Document non-obvious business rules
- Explain tradeoffs and decisions
- Reference related code/docs
- Add TODO/FIXME for known issues
- Use docstrings for public APIs, inline comments for implementation

#### 6.3 Document Algorithms (1 hour)

**Create:** `docs/ALGORITHMS.md`

Document key algorithms:
```markdown
# Algorithms Reference

## Auto-Download Filename Matching

**Location:** `PrinterMonitoringService._attempt_download_current_job()`

**Problem:** Bambu Lab printers report current job filename via MQTT,
but the actual file in the cache may have a different name due to:
- Special characters being stripped
- Spaces converted to underscores
- Filename truncation
- Case differences

**Algorithm:**
1. Try exact filename match first (fastest path)
2. Get list of files from printer cache via FTP
3. Case-insensitive matching against printer files
4. Generate variants:
   - Remove parentheses, commas
   - Replace spaces with underscores
   - Normalize multiple spaces
5. Try each variant until success

**Complexity:** O(n) where n = number of variants * number of files
**Success Rate:** ~95% based on production logs

## Thumbnail Extraction from 3MF

**Location:** `FileThumbnailService.extract_thumbnails()`

**Problem:** 3MF files contain embedded PNG thumbnails in ZIP archive.
Need to extract, validate, and resize for UI display.

**Algorithm:**
1. Open 3MF as ZIP archive
2. Search for Metadata/thumbnail.png
3. Extract and validate PNG format
4. Generate 3 sizes: small (128px), medium (256px), large (512px)
5. Save with quality optimization
6. Store paths in database

**Performance:** ~200ms for typical 3MF file
```

---

## Deliverables

### Documentation Files
- [ ] Docstrings added to all services (>85% coverage)
- [ ] Docstrings added to all API endpoints
- [ ] Docstrings added to all models
- [ ] `docs/MAGIC_NUMBERS_INVENTORY.md`
- [ ] `src/config/constants.py` created
- [ ] `docs/ERROR_HANDLING_PATTERNS.md`
- [ ] `src/utils/errors.py` created
- [ ] `docs/TEST_COVERAGE_REPORT.md`
- [ ] `docs/COMPLEX_LOGIC_INVENTORY.md`
- [ ] `docs/ALGORITHMS.md`

### Code Changes
- [ ] All magic numbers moved to constants
- [ ] Test coverage >85%
- [ ] Error handling standardized
- [ ] Settings validation implemented
- [ ] Complex logic commented

### Test Files
- [ ] `tests/conftest.py` - Test fixtures
- [ ] `tests/services/test_*.py` - Service tests
- [ ] `tests/integration/test_*.py` - Integration tests
- [ ] `tests/api/test_*.py` - API tests
- [ ] `tests/test_config_validation.py` - Config tests

---

## Development Guidelines

### Branch Strategy
- Create new branch: `claude/phase3-documentation-testing-<session-id>`
- Keep commits focused and well-documented
- Commit frequently with clear messages

### Code Location (CRITICAL)
- **ALWAYS edit in `/src/` and `/frontend/`**
- **NEVER edit in `/printernizer/src/` or `/printernizer/frontend/`**
- Pre-commit hook automatically syncs changes

### Commit Message Format

```
type: Brief description (Phase 3)

Detailed explanation of changes made.

Key improvements:
- Point 1
- Point 2
- Point 3

Technical debt impact:
- Phase 3 progress: X% (Y/40 hours completed)

Coverage improvement: X% → Y%

See docs/FILENAME.md for detailed documentation.
```

**Types:** `docs:`, `test:`, `refactor:`, `feat:`

### Testing After Changes
```bash
# Run tests
pytest

# Check coverage
pytest --cov=src --cov-fail-under=85

# Check docstring coverage
interrogate src/ --fail-under=85

# Lint code
flake8 src/
black src/ --check
```

---

## Success Criteria

### Phase 3 Complete When:
- [ ] Docstring coverage >85%
- [ ] Test coverage >85%
- [ ] All magic numbers in constants.py
- [ ] Error responses standardized
- [ ] Settings validation comprehensive
- [ ] Complex logic documented
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Changes committed and pushed

---

## Estimated Timeline

**Task 1: Docstrings (6 hours)**
- Service docs: 3 hours
- API docs: 2 hours
- Model docs: 1 hour

**Task 2: Magic Numbers (4 hours)**
- Identify: 1 hour
- Create constants: 2 hours
- Replace: 1 hour

**Task 3: Test Coverage (12-15 hours)**
- Infrastructure: 2 hours
- Unit tests: 6 hours
- Integration tests: 3-4 hours
- API tests: 1-2 hours
- Coverage report: 1 hour

**Task 4: Error Handling (4 hours)**
- Audit: 1 hour
- Standards: 1 hour
- Update endpoints: 2 hours

**Task 5: Settings Validation (3 hours)**
- Validation schema: 1 hour
- Printer validation: 1 hour
- Tests: 1 hour

**Task 6: Complex Logic Comments (6 hours)**
- Identify: 2 hours
- Add comments: 3 hours
- Document algorithms: 1 hour

**Total: 35-38 hours**

---

## Reference Documentation

### Phase 2 Documentation
- `docs/EVENT_CONTRACTS.md` - Event system reference
- `docs/EVENT_FLOWS.md` - Workflow diagrams
- `docs/CIRCULAR_DEPENDENCY_AUDIT.md` - Dependency analysis
- `docs/EXCEPTION_HANDLING_AUDIT.md` - Exception patterns
- `docs/PHASE2_COMPLETION_SUMMARY.md` - Phase 2 summary
- `.claude/skills/printernizer-architecture.md` - Architecture

### Original Assessment
- `TECHNICAL_DEBT_ASSESSMENT.md` - Full technical debt analysis
- `TECHNICAL_DEBT_QUICK_REFERENCE.md` - Progress tracker
- `FILESERVICE_REFACTORING_SUMMARY.md` - FileService refactoring
- `PRINTERSERVICE_REFACTORING_SUMMARY.md` - PrinterService refactoring

### Development Guides
- `CLAUDE.md` - Development guidelines
- `README.md` - User documentation
- `CONTRIBUTING.md` - Contribution guidelines

---

## Getting Started

1. **Read this prompt thoroughly**
2. **Review Phase 2 documentation** (especially architecture and event contracts)
3. **Create new branch** with session ID
4. **Start with Task 1** (Docstrings) or **Task 3** (Testing) - highest impact
5. **Create TODO list** to track progress
6. **Work systematically** through each task
7. **Commit frequently** with clear messages
8. **Update progress** in TECHNICAL_DEBT_QUICK_REFERENCE.md

---

## Questions to Consider

Before starting, ensure you understand:
- [ ] Phase 2 architectural patterns (coordinator, events, late binding)
- [ ] Event-driven architecture (see EVENT_CONTRACTS.md)
- [ ] Service decomposition patterns
- [ ] Testing best practices (fixtures, mocks, coverage)
- [ ] Docstring standards (Google style)
- [ ] Git workflow and commit format

If anything is unclear, review Phase 2 documentation first.

---

**Ready to begin Phase 3 - Medium Priority improvements!**

Let's improve documentation, testing, and code clarity to create a highly maintainable codebase. 🚀
