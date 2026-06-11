# Detailed Technical Debt by File

**Analysis Date**: 2025-11-17
**Purpose**: File-by-file breakdown with specific line numbers and code examples

---

## CRITICAL ISSUES - Immediate Action Required

### 1. src/printers/bambu_lab.py (1,867 LOC)
**Criticality**: ⚠️ CRITICAL
**Total Issues**: 14
**Estimated Effort**: 6-8 days

#### 1.1 Bare Except Blocks (8 occurrences) - CRITICAL
**Priority**: P0 (Fix immediately)
**Effort**: 2-3 days

| Line | Context | Current Code | Issue |
|------|---------|--------------|-------|
| 383 | `_get_status_bambu_api()` | `except:` | Catches all exceptions including KeyboardInterrupt |
| 390 | `_get_status_bambu_api()` | `except:` | Catches all exceptions including SystemExit |
| 397 | `_get_status_bambu_api()` | `except:` | Masks genuine errors |
| 412 | `_get_status_bambu_api()` | `except:` | No error logging |
| 423 | `_get_status_bambu_api()` | `except:` | Silent failure |
| 431 | `_get_status_bambu_api()` | `except:` | Silent failure |
| 442 | `_get_status_bambu_api()` | `except:` | Silent failure |
| 452 | `_get_status_bambu_api()` | `except:` | Silent failure |

**Example - Line 383**:
```python
# CURRENT (BAD):
try:
    state = self.bambu_client.get_state()
    alternative_status.name = state if state else 'UNKNOWN'
except:  # DANGEROUS!
    alternative_status.name = 'UNKNOWN'

# RECOMMENDED FIX:
try:
    state = self.bambu_client.get_state()
    alternative_status.name = state if state else 'UNKNOWN'
except (ConnectionError, TimeoutError, AttributeError) as e:
    logger.warning(f"Failed to get printer state: {e}")
    alternative_status.name = 'UNKNOWN'
except Exception as e:
    logger.error(f"Unexpected error getting printer state: {e}", exc_info=True)
    alternative_status.name = 'UNKNOWN'
```

**Testing Requirements**:
- Add test for each exception type
- Verify logging occurs
- Ensure graceful degradation

---

#### 1.2 Code Duplication - Download Methods (5 methods) - HIGH
**Priority**: P1
**Effort**: 4-6 days

| Method | Lines | LOC | Overlap |
|--------|-------|-----|---------|
| `_download_file_direct_ftp()` | 1374-1436 | 63 | 60% |
| `_download_file_bambu_api()` | 1437-1497 | 61 | 60% |
| `_download_file_mqtt()` | 1498-1504 | 7 | 40% |
| `_download_via_ftp()` | 1505-1672 | 168 | 70% |
| `_download_via_http()` | 1673-1867 | 195 | 50% |

**Common Pattern** (repeated 5 times):
```python
# Pattern in all methods:
try:
    # 1. Connection/authentication logic
    # 2. File download with progress tracking
    # 3. File validation
    # 4. Cleanup
except Exception as e:
    logger.error(f"Download failed: {e}")
    return False
finally:
    # Cleanup resources
```

**Suggested Refactoring**:
```python
# Extract common logic to base class
class DownloadHandler:
    """Base class for file download operations."""

    async def download_with_retry(
        self,
        strategy: DownloadStrategy,
        file_path: str,
        destination: Path,
        max_retries: int = 3
    ) -> bool:
        """Download file using specified strategy with retry logic."""
        for attempt in range(max_retries):
            try:
                return await strategy.download(file_path, destination)
            except RetryableError as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                logger.error(f"Download failed after {max_retries} attempts: {e}")
                return False
            except FatalError as e:
                logger.error(f"Fatal download error: {e}")
                return False

# Implement strategy pattern
class FTPDownloadStrategy(DownloadStrategy):
    async def download(self, file_path: str, destination: Path) -> bool:
        # FTP-specific implementation only
        pass

class HTTPDownloadStrategy(DownloadStrategy):
    async def download(self, file_path: str, destination: Path) -> bool:
        # HTTP-specific implementation only
        pass
```

---

#### 1.3 Large Method - `_get_status_bambu_api()` (330 lines) - HIGH
**Priority**: P1
**Effort**: 3-4 days
**Lines**: 359-688

**Issue**: Single method with 8 nested try-except blocks doing too much

**Current Structure**:
```
_get_status_bambu_api() (330 LOC)
├── Try block 1: Get printer state (lines 383-385)
├── Try block 2: Get bed temperature (lines 390-392)
├── Try block 3: Get nozzle temperature (lines 397-399)
├── Try block 4: Get filename (lines 412-414)
├── Try block 5: Get layer info (lines 423-425)
├── Try block 6: Get speed info (lines 431-433)
├── Try block 7: Get progress (lines 442-444)
└── Try block 8: Get job details (lines 452-454)
```

**Suggested Refactoring**:
```python
# Split into focused methods
class StatusExtractor:
    """Extract status information from Bambu API."""

    def extract_temperature_data(self, client) -> TemperatureData:
        """Extract all temperature-related data."""
        return TemperatureData(
            bed_temp=self._safe_get_temp(client.get_bed_temperature),
            nozzle_temp=self._safe_get_temp(client.get_nozzle_temperature),
        )

    def extract_progress_data(self, client) -> ProgressData:
        """Extract all progress-related data."""
        return ProgressData(
            current_layer=self._safe_get_int(client.get_current_layer),
            total_layers=self._safe_get_int(client.get_total_layers),
            percent_complete=self._safe_get_float(client.get_progress),
        )

    def _safe_get_temp(self, getter_func) -> float:
        """Safely get temperature with proper error handling."""
        try:
            return getter_func() or 0.0
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Temperature retrieval failed: {e}")
            return 0.0

# Main method becomes simpler:
def _get_status_bambu_api(self) -> PrinterStatus:
    """Get printer status from Bambu API."""
    status = PrinterStatus()
    extractor = StatusExtractor()

    status.temperatures = extractor.extract_temperature_data(self.bambu_client)
    status.progress = extractor.extract_progress_data(self.bambu_client)
    status.state = extractor.extract_state_data(self.bambu_client)

    return status
```

**Benefits**:
- Each method < 20 lines
- Easy to test individually
- Clear separation of concerns
- Reusable extractors

---

#### 1.4 Broad Exception Handlers (3 cases) - MEDIUM
**Priority**: P2
**Effort**: 1 day

| Line | Method | Issue |
|------|--------|-------|
| 548 | `_handle_mqtt_message()` | `except Exception as e:` - minimal context |
| 616 | `_list_files_mqtt()` | `except Exception as e:` - minimal context |
| 700 | `_get_status_mqtt()` | `except Exception as e:` - minimal context |

**Example - Line 548**:
```python
# CURRENT:
try:
    # ... complex processing
except Exception as e:
    logger.error(f"MQTT message handling failed: {e}")  # No stack trace!

# RECOMMENDED:
try:
    # ... complex processing
except json.JSONDecodeError as e:
    logger.warning(f"Invalid JSON in MQTT message: {e}")
except KeyError as e:
    logger.warning(f"Missing expected field in MQTT message: {e}")
except Exception as e:
    logger.error(f"Unexpected MQTT error: {e}", exc_info=True)  # Include stack trace
```

---

### 2. src/database/database.py (2,344 LOC)
**Criticality**: ⚠️ CRITICAL
**Total Issues**: 8
**Estimated Effort**: 8-10 days

#### 2.1 Monolithic Class Design - CRITICAL
**Priority**: P0
**Effort**: 8-10 days

**Current Structure**:
```
Database (2,344 LOC)
├── Connection Management (50 LOC)
├── Job Operations (400 LOC)
│   ├── create_job()
│   ├── get_job()
│   ├── update_job()
│   ├── delete_job()
│   ├── get_jobs()
│   └── ... 15 more job methods
├── File Operations (350 LOC)
│   ├── add_file()
│   ├── get_file()
│   ├── update_file()
│   ├── delete_file()
│   └── ... 12 more file methods
├── Idea Operations (300 LOC)
├── Snapshot Operations (250 LOC)
├── Material Operations (250 LOC)
├── Trending Operations (300 LOC)
├── Analytics Operations (200 LOC)
└── Migration Operations (244 LOC)
```

**Issues**:
1. **Violates Single Responsibility Principle** - Does 8+ different things
2. **Hard to Test** - Must mock entire database for any test
3. **Tight Coupling** - Services depend on entire Database class
4. **Poor Maintainability** - Finding methods is difficult
5. **No Parallel Development** - Merge conflicts common

**Recommended Refactoring Plan**:

**Phase 1: Create Repository Pattern** (Days 1-2)
```python
# Create base repository
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, connection: aiosqlite.Connection):
        self._connection = connection

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        pass

    @abstractmethod
    async def create(self, entity: T) -> str:
        pass

    @abstractmethod
    async def update(self, entity: T) -> bool:
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        pass
```

**Phase 2: Extract JobRepository** (Days 3-4)
```python
# src/database/repositories/job_repository.py
from .base_repository import BaseRepository
from ..models import Job

class JobRepository(BaseRepository[Job]):
    """Repository for job-related database operations."""

    async def get_by_id(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        sql = "SELECT * FROM jobs WHERE id = ?"
        async with self._connection.execute(sql, (job_id,)) as cursor:
            row = await cursor.fetchone()
            return Job.from_row(row) if row else None

    async def get_active_jobs(self, printer_id: Optional[str] = None) -> List[Job]:
        """Get all active jobs, optionally filtered by printer."""
        sql = """
            SELECT * FROM jobs
            WHERE status IN ('printing', 'paused')
        """
        params = []
        if printer_id:
            sql += " AND printer_id = ?"
            params.append(printer_id)

        async with self._connection.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [Job.from_row(row) for row in rows]

    # ... other job-specific methods
```

**Phase 3: Extract FileRepository** (Days 5-6)
```python
# src/database/repositories/file_repository.py
class FileRepository(BaseRepository[File]):
    """Repository for file-related database operations."""

    async def get_by_hash(self, file_hash: str) -> Optional[File]:
        """Find file by content hash (for deduplication)."""
        sql = "SELECT * FROM files WHERE file_hash = ?"
        async with self._connection.execute(sql, (file_hash,)) as cursor:
            row = await cursor.fetchone()
            return File.from_row(row) if row else None

    async def search(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[File], int]:
        """Search files with pagination."""
        # Build dynamic query
        conditions = []
        params = []

        if query:
            conditions.append("(name LIKE ? OR description LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%"])

        if tags:
            placeholders = ",".join("?" * len(tags))
            conditions.append(f"tags IN ({placeholders})")
            params.extend(tags)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Get total count
        count_sql = f"SELECT COUNT(*) FROM files WHERE {where_clause}"
        async with self._connection.execute(count_sql, params) as cursor:
            total = (await cursor.fetchone())[0]

        # Get paginated results
        sql = f"""
            SELECT * FROM files
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        async with self._connection.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            files = [File.from_row(row) for row in rows]

        return files, total
```

**Phase 4: Update Services** (Days 7-8)
```python
# src/services/job_service.py
class JobService:
    """Service for job management."""

    def __init__(self, db: Database):
        self._db = db
        self._job_repo = JobRepository(db.connection)
        self._file_repo = FileRepository(db.connection)

    async def create_job(self, job_data: Dict[str, Any]) -> Job:
        """Create new print job."""
        # Validate file exists
        file = await self._file_repo.get_by_id(job_data['file_id'])
        if not file:
            raise ValueError(f"File not found: {job_data['file_id']}")

        # Create job
        job = Job(**job_data)
        job_id = await self._job_repo.create(job)
        job.id = job_id

        return job
```

**Phase 5: Add Tests** (Days 9-10)
```python
# tests/database/repositories/test_job_repository.py
import pytest
from src.database.repositories import JobRepository
from src.database.models import Job

@pytest.fixture
async def job_repository(test_db):
    """Create job repository with test database."""
    return JobRepository(test_db.connection)

async def test_create_job(job_repository):
    """Test creating a job."""
    job = Job(
        printer_id="printer1",
        file_id="file1",
        status="pending"
    )
    job_id = await job_repository.create(job)
    assert job_id is not None

    retrieved = await job_repository.get_by_id(job_id)
    assert retrieved.printer_id == "printer1"
    assert retrieved.status == "pending"

async def test_get_active_jobs(job_repository):
    """Test retrieving active jobs."""
    # Create test jobs
    await job_repository.create(Job(status="printing", printer_id="p1"))
    await job_repository.create(Job(status="completed", printer_id="p1"))
    await job_repository.create(Job(status="paused", printer_id="p2"))

    # Get active jobs
    active = await job_repository.get_active_jobs()
    assert len(active) == 2  # printing and paused

    # Filter by printer
    p1_active = await job_repository.get_active_jobs(printer_id="p1")
    assert len(p1_active) == 1
    assert p1_active[0].status == "printing"
```

**Benefits**:
- Each repository < 400 LOC
- Easy to test in isolation
- Clear separation of concerns
- Parallel development possible
- Better IDE navigation

---

#### 2.2 Missing Connection Pooling - MEDIUM
**Priority**: P2
**Effort**: 3-4 days

**Current Implementation**:
```python
class Database:
    def __init__(self, db_path: str):
        self._db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None  # Single connection!
```

**Issues**:
- Concurrent requests serialize on single connection
- No connection reuse optimization
- Performance bottleneck under load

**Suggested Implementation**:
```python
from asyncio import Queue, Semaphore

class Database:
    """Database with connection pooling."""

    def __init__(self, db_path: str, pool_size: int = 5):
        self._db_path = db_path
        self._pool_size = pool_size
        self._pool: Queue[aiosqlite.Connection] = Queue(maxsize=pool_size)
        self._semaphore = Semaphore(pool_size)
        self._initialized = False

    async def initialize(self):
        """Initialize connection pool."""
        for _ in range(self._pool_size):
            conn = await aiosqlite.connect(self._db_path)
            conn.row_factory = aiosqlite.Row
            await self._pool.put(conn)
        self._initialized = True

    async def acquire(self) -> aiosqlite.Connection:
        """Get connection from pool."""
        await self._semaphore.acquire()
        return await self._pool.get()

    async def release(self, conn: aiosqlite.Connection):
        """Return connection to pool."""
        await self._pool.put(conn)
        self._semaphore.release()

    @asynccontextmanager
    async def connection(self):
        """Context manager for connection pooling."""
        conn = await self.acquire()
        try:
            yield conn
        finally:
            await self.release(conn)

# Usage:
async with db.connection() as conn:
    cursor = await conn.execute("SELECT * FROM jobs")
    rows = await cursor.fetchall()
```

---

#### 2.3 Type Ignore Comment - LOW
**Priority**: P3
**Effort**: 1 hour

**Line 351**:
```python
# CURRENT:
async with self._connection.execute(sql, params or ()):  # type: ignore[arg-type]

# BETTER (document why):
# Type ignore needed: aiosqlite expects tuple but params may be None
async with self._connection.execute(sql, params or ()):  # type: ignore[arg-type]
```

---

### 3. src/services/analytics_service.py (~100 LOC)
**Criticality**: ⚠️ CRITICAL
**Total Issues**: 5 TODO stubs
**Estimated Effort**: 5-7 days

#### 3.1 Complete Service Implementation - CRITICAL
**Priority**: P0
**Effort**: 5-7 days

**Current State**: All methods return hardcoded empty/zero data

| Method | Line | Returns | Should Return |
|--------|------|---------|---------------|
| `get_dashboard_stats()` | 22 | Hardcoded zeros | Real aggregated stats |
| `get_printer_usage()` | 35 | Empty list | Usage data per printer |
| `get_material_consumption()` | 40 | Empty dict | Actual material usage |
| `get_time_analytics()` | 50 | Empty dict | Time-based analytics |
| `get_business_report()` | 264 | Mock data | Real business metrics |

**Line 20-31: Dashboard Stats**
```python
# CURRENT (BROKEN):
async def get_dashboard_stats(self) -> Dict[str, Any]:
    """Get main dashboard statistics."""
    # TODO: Implement actual analytics calculations
    return {
        "total_jobs": 0,
        "active_printers": 0,
        "completed_today": 0,
        "failed_today": 0,
        "total_print_time": 0,
        "material_used": 0.0
    }

# SHOULD BE:
async def get_dashboard_stats(self) -> Dict[str, Any]:
    """Get main dashboard statistics."""
    db = self._db

    # Get total jobs
    total_jobs = await db.execute_scalar(
        "SELECT COUNT(*) FROM jobs"
    )

    # Get active printers
    active_printers = await db.execute_scalar(
        """
        SELECT COUNT(DISTINCT printer_id)
        FROM jobs
        WHERE status IN ('printing', 'paused')
        """
    )

    # Get today's stats
    today_start = datetime.now().replace(hour=0, minute=0, second=0)
    completed_today = await db.execute_scalar(
        """
        SELECT COUNT(*) FROM jobs
        WHERE status = 'completed'
        AND completed_at >= ?
        """,
        (today_start,)
    )

    failed_today = await db.execute_scalar(
        """
        SELECT COUNT(*) FROM jobs
        WHERE status = 'failed'
        AND updated_at >= ?
        """,
        (today_start,)
    )

    # Get total print time (in seconds)
    total_print_time = await db.execute_scalar(
        """
        SELECT COALESCE(SUM(
            CAST((julianday(completed_at) - julianday(started_at)) * 86400 AS INTEGER)
        ), 0)
        FROM jobs
        WHERE status = 'completed'
        """
    )

    # Get material used
    material_used = await db.execute_scalar(
        """
        SELECT COALESCE(SUM(filament_used_g), 0.0)
        FROM jobs
        WHERE status = 'completed'
        """
    )

    return {
        "total_jobs": total_jobs,
        "active_printers": active_printers,
        "completed_today": completed_today,
        "failed_today": failed_today,
        "total_print_time": total_print_time,
        "material_used": material_used
    }
```

**Line 33-36: Printer Usage**
```python
# CURRENT (BROKEN):
async def get_printer_usage(self, days: int = 30) -> List[Dict[str, Any]]:
    """Get printer usage statistics."""
    # TODO: Implement printer usage tracking
    return []

# SHOULD BE:
async def get_printer_usage(self, days: int = 30) -> List[Dict[str, Any]]:
    """Get printer usage statistics for the last N days."""
    start_date = datetime.now() - timedelta(days=days)

    sql = """
        SELECT
            printer_id,
            COUNT(*) as total_jobs,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_jobs,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_jobs,
            COALESCE(SUM(
                CASE
                    WHEN status = 'completed'
                    THEN CAST((julianday(completed_at) - julianday(started_at)) * 86400 AS INTEGER)
                    ELSE 0
                END
            ), 0) as total_print_time,
            COALESCE(SUM(filament_used_g), 0.0) as material_used
        FROM jobs
        WHERE created_at >= ?
        GROUP BY printer_id
        ORDER BY total_jobs DESC
    """

    rows = await self._db.execute_query(sql, (start_date,))

    return [
        {
            "printer_id": row["printer_id"],
            "total_jobs": row["total_jobs"],
            "completed_jobs": row["completed_jobs"],
            "failed_jobs": row["failed_jobs"],
            "success_rate": (row["completed_jobs"] / row["total_jobs"] * 100)
                           if row["total_jobs"] > 0 else 0,
            "total_print_time": row["total_print_time"],
            "material_used": row["material_used"]
        }
        for row in rows
    ]
```

**Testing Requirements**:
```python
# tests/services/test_analytics_service.py
async def test_dashboard_stats(analytics_service, test_db):
    """Test dashboard statistics calculation."""
    # Create test jobs
    await test_db.create_job(status="completed", completed_at=datetime.now())
    await test_db.create_job(status="printing")
    await test_db.create_job(status="failed", updated_at=datetime.now())

    stats = await analytics_service.get_dashboard_stats()

    assert stats["total_jobs"] == 3
    assert stats["completed_today"] == 1
    assert stats["failed_today"] == 1
    assert stats["active_printers"] == 1

async def test_printer_usage(analytics_service, test_db):
    """Test printer usage statistics."""
    # Create test jobs for different printers
    await test_db.create_job(printer_id="p1", status="completed", filament_used_g=100)
    await test_db.create_job(printer_id="p1", status="failed")
    await test_db.create_job(printer_id="p2", status="completed", filament_used_g=150)

    usage = await analytics_service.get_printer_usage(days=30)

    assert len(usage) == 2
    p1_stats = next(u for u in usage if u["printer_id"] == "p1")
    assert p1_stats["total_jobs"] == 2
    assert p1_stats["completed_jobs"] == 1
    assert p1_stats["material_used"] == 100
```

---

## HIGH PRIORITY ISSUES

### 4. src/api/routers/files.py (1,136 LOC)
**Criticality**: ⚠️ HIGH
**Total Issues**: 3
**Estimated Effort**: 2-3 days

#### 4.1 Query Optimization - Missing Count-Only Query
**Priority**: P1
**Effort**: 1 day

**Line 102**:
```python
# CURRENT (INEFFICIENT):
# TODO: Optimize by adding count-only query to avoid fetching all records
paginated_files = await file_service.get_files(
    query=search_query,
    limit=limit,
    offset=offset
)
total_count = len(paginated_files)  # Fetches ALL files just to count!

# OPTIMIZED:
files, total_count = await file_service.get_files_paginated(
    query=search_query,
    limit=limit,
    offset=offset
)
```

**Implementation in FileService**:
```python
# src/services/library_service.py
async def get_files_paginated(
    self,
    query: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 50,
    offset: int = 0
) -> Tuple[List[Dict[str, Any]], int]:
    """Get paginated files with total count (optimized)."""

    # Build where clause
    conditions = []
    params = []

    if query:
        conditions.append("(name LIKE ? OR description LIKE ?)")
        params.extend([f"%{query}%", f"%{query}%"])

    if tags:
        placeholders = ",".join("?" * len(tags))
        conditions.append(f"tags IN ({placeholders})")
        params.extend(tags)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Get total count (efficient - no data fetching)
    count_sql = f"SELECT COUNT(*) FROM files WHERE {where_clause}"
    total_count = await self._db.execute_scalar(count_sql, params)

    # Get paginated data
    sql = f"""
        SELECT * FROM files
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    files = await self._db.execute_query(sql, params)

    return files, total_count
```

**Performance Impact**:
- **Before**: Fetches 10,000 records to count them (wasteful)
- **After**: Single COUNT(*) query (efficient)
- **Savings**: ~99% reduction in data transfer for large datasets

---

#### 4.2 Hardcoded API URLs
**Priority**: P2
**Effort**: 1 day

**Lines**: 505, 596, 719
```python
# CURRENT:
thumbnail_url = f"/api/v1/files/{file_id}/thumbnail"

# BETTER:
from src.api.constants import api_url
thumbnail_url = api_url(f"files/{file_id}/thumbnail")
```

**Create constants file**:
```python
# src/api/constants.py
API_VERSION = "v1"

def api_url(endpoint: str) -> str:
    """Generate API URL with current version."""
    return f"/api/{API_VERSION}/{endpoint.lstrip('/')}"
```

---

### 5. src/api/routers/library.py (803 LOC)
**Criticality**: ⚠️ HIGH
**Total Issues**: 2
**Estimated Effort**: 1 day

#### 5.1 Bare Except Blocks - JSON Parsing
**Priority**: P1
**Effort**: 1 hour

**Line 573**:
```python
# CURRENT (BAD):
try:
    material_reqs['material_types'] = json.loads(file_record['material_types'])
except:  # DANGEROUS!
    material_reqs['material_types'] = [file_record['material_types']]

# RECOMMENDED:
try:
    material_reqs['material_types'] = json.loads(file_record['material_types'])
except json.JSONDecodeError:
    # Single value, not array
    material_reqs['material_types'] = [file_record['material_types']]
except (TypeError, AttributeError) as e:
    logger.warning(f"Invalid material_types format: {e}")
    material_reqs['material_types'] = []
```

**Line 610** - Same issue, same fix

---

### 6. src/services/library_service.py (1,081 LOC)
**Criticality**: ⚠️ HIGH
**Total Issues**: 2
**Estimated Effort**: 3-4 days

#### 6.1 TODO - Color Extraction
**Priority**: P2
**Effort**: 1-2 days

**Line 738**:
```python
# TODO: Implement color extraction from filament ID database
# Would need mapping table: filament_id → color_name
```

**Suggested Implementation**:
```python
# Create filament database
FILAMENT_COLOR_MAP = {
    "GFL00": "Black",
    "GFL01": "White",
    "GFL02": "Red",
    # ... load from database or config file
}

def extract_filament_colors(self, filament_ids: List[str]) -> List[str]:
    """Extract color names from filament IDs."""
    colors = []
    for fid in filament_ids:
        color = FILAMENT_COLOR_MAP.get(fid, f"Unknown ({fid})")
        colors.append(color)
    return colors

# Usage:
if 'filament_ids' in parser_metadata:
    ids = parser_metadata['filament_ids']
    colors = self.extract_filament_colors(ids)
    db_fields['filament_colors'] = json.dumps(colors)
```

---

#### 6.2 Large Service File - Needs Refactoring
**Priority**: P2
**Effort**: 3-4 days

**Current**: 1,081 LOC handling multiple concerns

**Suggested Split**:
```
library_service.py (1,081 LOC) → Split into:
├── metadata/
│   └── file_metadata_extractor.py  (~300 LOC)
│       - Extract 3D file metadata
│       - Parse 3MF/STL/GCODE files
├── deduplication/
│   └── file_deduplicator.py        (~200 LOC)
│       - Hash calculation
│       - Duplicate detection
├── library_manager.py              (~300 LOC)
│   - File organization
│   - Tagging and categorization
└── library_service.py              (~281 LOC)
    - Orchestration only
    - High-level API
```

---

### 7. src/printers/prusa.py (864 LOC)
**Criticality**: ⚠️ HIGH
**Total Issues**: 5
**Estimated Effort**: 2-3 days

#### 7.1 Broad Exception Handlers (16 cases)
**Priority**: P1
**Effort**: 2-3 days

**Common Pattern** (lines 67, 84, 91, 124, 245, etc.):
```python
# CURRENT (VAGUE):
try:
    response = await self._make_api_call(endpoint)
    return response.json()
except Exception as e:
    logger.info("API call failed")  # No details!
    return None

# RECOMMENDED (SPECIFIC):
try:
    response = await self._make_api_call(endpoint)
    return response.json()
except aiohttp.ClientConnectorError as e:
    logger.warning(f"Cannot connect to printer: {e}")
    return None
except aiohttp.ClientTimeout as e:
    logger.warning(f"Printer request timeout: {e}")
    return None
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON response from printer: {e}", exc_info=True)
    return None
except Exception as e:
    logger.error(f"Unexpected printer error: {e}", exc_info=True)
    return None
```

**Create Error Handling Decorator**:
```python
# src/printers/utils.py
def handle_printer_errors(func):
    """Decorator for standardized printer error handling."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except aiohttp.ClientConnectorError as e:
            logger.warning(f"Connection error in {func.__name__}: {e}")
            return None
        except aiohttp.ClientTimeout as e:
            logger.warning(f"Timeout in {func.__name__}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {func.__name__}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise
    return wrapper

# Usage:
@handle_printer_errors
async def get_status(self) -> Optional[PrinterStatus]:
    """Get printer status."""
    response = await self._make_api_call("/api/status")
    return PrinterStatus(**response.json())
```

---

## MEDIUM PRIORITY ISSUES

### 8. Frontend JavaScript Files
**Criticality**: ⚠️ MEDIUM
**Total Issues**: 60+
**Estimated Effort**: 2-3 days

#### 8.1 Console Logging (40+ statements)
**Priority**: P2
**Effort**: 2-3 days

**Files**: `download-logger.js`, `theme-switcher.js`, `jobs.js`, `settings.js`, etc.

**Example - download-logger.js:26**:
```javascript
// CURRENT:
console.log('📝 Initializing Download Logger');
console.log(`Loaded ${logs.length} download logs from storage`);
console.error('Failed to load logs:', error);

// RECOMMENDED:
// Create logging utility
const Logger = {
    _isDebug: () => window.DEBUG_MODE || localStorage.getItem('debug') === 'true',

    debug(msg, ...args) {
        if (this._isDebug()) {
            console.log(`[DEBUG] ${msg}`, ...args);
        }
    },

    info(msg, ...args) {
        if (this._isDebug()) {
            console.info(`[INFO] ${msg}`, ...args);
        }
    },

    warn(msg, ...args) {
        console.warn(`[WARN] ${msg}`, ...args);
    },

    error(msg, ...args) {
        console.error(`[ERROR] ${msg}`, ...args);
        // Could also send to error tracking service
    }
};

// Usage:
Logger.debug('Initializing Download Logger');
Logger.debug(`Loaded ${logs.length} download logs from storage`);
Logger.error('Failed to load logs:', error);
```

---

#### 8.2 innerHTML Security Risk (20+ cases)
**Priority**: P2
**Effort**: 2 days

**Files**: `jobs.js`, `library.js`, `dashboard.js`

**Example**:
```javascript
// CURRENT (RISKY):
jobsTable.innerHTML = `
    <tr>
        <td>${job.name}</td>
        <td>${job.status}</td>
    </tr>
`;  // If job.name contains <script>, XSS!

// SAFER:
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

jobsTable.innerHTML = `
    <tr>
        <td>${escapeHtml(job.name)}</td>
        <td>${escapeHtml(job.status)}</td>
    </tr>
`;

// BEST (use DOM methods):
const row = document.createElement('tr');
const nameCell = document.createElement('td');
nameCell.textContent = job.name;  // Auto-escaped!
const statusCell = document.createElement('td');
statusCell.textContent = job.status;
row.appendChild(nameCell);
row.appendChild(statusCell);
jobsTable.appendChild(row);
```

---

### 9. src/services/event_service.py
**Criticality**: ⚠️ MEDIUM
**Total Issues**: 1
**Estimated Effort**: 1 day

#### 9.1 Async Task Management
**Priority**: P2
**Effort**: 1 day

**Lines 56-58**:
```python
# CURRENT (RISKY):
asyncio.create_task(self._printer_monitoring_task())  # Not stored!
asyncio.create_task(self._job_status_task())
asyncio.create_task(self._file_discovery_task())

# RECOMMENDED:
self._monitoring_task = asyncio.create_task(self._printer_monitoring_task())
self._job_task = asyncio.create_task(self._job_status_task())
self._file_task = asyncio.create_task(self._file_discovery_task())

# Add cleanup
async def shutdown(self):
    """Gracefully shutdown all background tasks."""
    logger.info("Shutting down event service...")

    tasks = [
        self._monitoring_task,
        self._job_task,
        self._file_task
    ]

    for task in tasks:
        if task and not task.done():
            task.cancel()

    # Wait for cancellation
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Event service shutdown complete")
```

---

### 10. Hardcoded Configuration Values
**Criticality**: ⚠️ MEDIUM
**Total Issues**: 15+
**Estimated Effort**: 1-2 days

#### 10.1 Sleep Durations
**File**: `src/services/event_service.py`
**Priority**: P2
**Effort**: 1 day

**Lines**: 118, 212, 218, 229, 323, 329, 340, 442, 448

```python
# CURRENT:
await asyncio.sleep(30)   # Hardcoded
await asyncio.sleep(60)
await asyncio.sleep(300)

# RECOMMENDED:
# src/config/constants.py
class PollingIntervals:
    """Configurable polling intervals for event service."""
    PRINTER_STATUS_SECONDS = 30
    PRINTER_STATUS_ERROR_BACKOFF_SECONDS = 60
    JOB_STATUS_SECONDS = 10
    FILE_DISCOVERY_SECONDS = 300
    FILE_DISCOVERY_ERROR_BACKOFF_SECONDS = 600

# Usage:
from src.config.constants import PollingIntervals

await asyncio.sleep(PollingIntervals.PRINTER_STATUS_SECONDS)
```

---

#### 10.2 API URLs
**Multiple Files**
**Priority**: P2
**Effort**: 1 day

```python
# CURRENT (scattered):
f"/api/v1/files/{file_id}/thumbnail"
f"/api/v1/printers/{printer_id}"
f"/api/v1/jobs/{job_id}"

# RECOMMENDED:
# src/api/constants.py
API_VERSION = "v1"

def api_url(endpoint: str) -> str:
    """Generate versioned API URL."""
    return f"/api/{API_VERSION}/{endpoint.lstrip('/')}"

# Usage:
api_url(f"files/{file_id}/thumbnail")
api_url(f"printers/{printer_id}")
api_url(f"jobs/{job_id}")
```

---

## SUMMARY BY FILE

| File | LOC | Issues | Priority | Effort | Status |
|------|-----|--------|----------|--------|--------|
| `database.py` | 2,344 | 8 | P0 | 8-10d | ⏳ Not Started |
| `bambu_lab.py` | 1,867 | 14 | P0 | 6-8d | ⏳ Not Started |
| `analytics_service.py` | ~100 | 5 | P0 | 5-7d | ⏳ Not Started |
| `files.py` | 1,136 | 3 | P1 | 2-3d | ⏳ Not Started |
| `library.py` | 803 | 2 | P1 | 1d | ⏳ Not Started |
| `library_service.py` | 1,081 | 2 | P1 | 3-4d | ⏳ Not Started |
| `prusa.py` | 864 | 5 | P1 | 2-3d | ⏳ Not Started |
| `event_service.py` | 500+ | 1 | P2 | 1d | ⏳ Not Started |
| Frontend files | ~25K | 60+ | P2 | 2-3d | ⏳ Not Started |
| Configuration | - | 15+ | P2 | 1-2d | ⏳ Not Started |
| **TOTAL** | **36,575** | **~130** | **-** | **35-50d** | **0% Complete** |

---

## NEXT STEPS

1. **Review with team** - Prioritize based on business impact
2. **Create feature branches** - One per major refactoring
3. **Start with P0 issues** - Critical bugs and missing features
4. **Add tests first** - Test-driven refactoring
5. **Update progress tracker** - Track completion

---

**Last Updated**: 2025-11-17
**Next Review**: After Phase 1 completion
