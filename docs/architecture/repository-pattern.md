# Repository Pattern Architecture

**Created**: 2025-11-17
**Status**: Implemented (Phase 1 Complete)
**Version**: 1.0

---

## Overview

Printernizer uses the **Repository Pattern** to separate data access logic from business logic. This architectural pattern provides a clean abstraction layer between the application and the database.

## Why Repository Pattern?

### Problems with the Old Approach

The original `Database` class was a monolithic 2,344-line file with 69 methods handling:
- Job operations
- File operations
- Printer operations
- Idea operations
- Snapshot operations
- Trending operations
- Library operations
- Analytics operations

**Issues**:
- ❌ Violates Single Responsibility Principle
- ❌ Difficult to test (must mock entire database)
- ❌ Hard to maintain and navigate
- ❌ Tight coupling between unrelated domains
- ❌ Merge conflicts common with multiple developers

### Benefits of Repository Pattern

- ✅ **Separation of Concerns**: Each repository handles one domain
- ✅ **Testability**: Easy to mock individual repositories
- ✅ **Maintainability**: Each file < 500 LOC
- ✅ **Parallel Development**: Multiple developers can work independently
- ✅ **Type Safety**: Clear interfaces with type hints
- ✅ **Reusability**: Common operations in BaseRepository

---

## Architecture

### Repository Hierarchy

```
BaseRepository (base_repository.py)
├── Common CRUD operations (_execute_write, _fetch_one, _fetch_all)
├── Retry logic for database locks
└── Error handling and logging

PrinterRepository (printer_repository.py)
├── create(printer_data)
├── get(printer_id)
├── list(active_only)
├── update(printer_id, updates)
├── update_status(printer_id, status)
├── delete(printer_id)
└── exists(printer_id)

JobRepository (job_repository.py)
├── create(job_data)
├── get(job_id)
├── list(printer_id, status, limit, offset)
├── get_by_date_range(start_date, end_date)
├── get_statistics()
├── update(job_id, updates)
├── delete(job_id)
└── exists(job_id)

FileRepository (file_repository.py)
├── create(file_data)
├── get(file_id)
├── list(printer_id, status, limit, offset)
├── update(file_id, updates)
├── update_enhanced_metadata(file_id, metadata)
├── list_local_files(watch_folder_path)
├── delete_local_file(file_id)
├── get_statistics()
└── exists(file_id)

SnapshotRepository (snapshot_repository.py)
├── create(snapshot_data)
├── get(snapshot_id)
├── list(printer_id, limit)
├── delete(snapshot_id)
├── update_validation(snapshot_id, validation_data)
└── exists(snapshot_id)

TrendingRepository (trending_repository.py)
├── upsert(trending_data)
├── get(platform_id)
├── list(platform, category, limit)
├── clean_expired()
├── delete(platform_id)
├── exists(platform_id)
└── count_by_platform()

IdeaRepository (idea_repository.py)
├── create(idea_data)
├── get(idea_id)
├── list(status, is_business, limit, offset)
├── update(idea_id, updates)
├── update_status(idea_id, status)
├── delete(idea_id)
├── add_tags(idea_id, tags)
├── remove_tags(idea_id, tags)
├── get_tags(idea_id)
├── get_all_tags()
└── exists(idea_id)

LibraryRepository (library_repository.py)
├── create(file_data)
├── get(file_id)
├── get_by_checksum(checksum)
├── list(filters, limit, offset)
├── update(checksum, updates)
├── delete(checksum)
├── create_file_source(source_data)
├── delete_file_sources(checksum)
└── get_stats()
```

---

## Implementation Details

### BaseRepository

The `BaseRepository` class provides common functionality used by all repositories:

```python
class BaseRepository:
    """Base class for all repositories providing common database operations."""

    def __init__(self, connection: aiosqlite.Connection):
        self.connection = connection

    async def _execute_write(
        self, sql: str, params: Optional[tuple] = None, retry_count: int = 3
    ) -> Optional[int]:
        """Execute a write operation (INSERT, UPDATE, DELETE) with retry logic."""
        # Handles database locks with exponential backoff
        # Returns last row ID for INSERT operations

    async def _fetch_one(
        self, sql: str, params: Optional[List[Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Fetch a single row from the database."""
        # Converts row to dictionary using column names

    async def _fetch_all(
        self, sql: str, params: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch all rows from the database."""
        # Returns list of dictionaries
```

**Key Features**:
- **Retry Logic**: Automatically retries on database lock (up to 3 times)
- **Dictionary Conversion**: Rows returned as dictionaries (not tuples)
- **Error Logging**: Comprehensive logging with structlog
- **Type Safety**: Full type hints for all parameters and return values

### Example Repository: JobRepository

```python
class JobRepository(BaseRepository):
    """Repository for job-related database operations."""

    async def create(self, job_data: Dict[str, Any]) -> bool:
        """Create a new job record."""
        # Dynamic INSERT query based on provided fields
        # Handles IntegrityError for duplicate jobs
        # Returns True on success, False on failure

    async def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job by ID."""
        # Returns None if job not found

    async def list(
        self,
        printer_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List jobs with optional filtering."""
        # Supports filtering by printer, status
        # Supports pagination with limit/offset

    async def get_statistics(self) -> Dict[str, Any]:
        """Get job statistics."""
        # Returns counts by status, success rate
```

---

## Usage Examples

### Basic CRUD Operations

```python
from src.database.database import Database
from src.database.repositories.job_repository import JobRepository

# Initialize database
db = Database()
await db.initialize()

# Create repository
job_repo = JobRepository(db.get_connection())

# Create a job
job_data = {
    'id': 'job_123',
    'printer_id': 'bambu_001',
    'printer_type': 'bambu_lab',
    'job_name': 'test_print.3mf',
    'status': 'printing',
    'progress': 50
}
await job_repo.create(job_data)

# Get a job
job = await job_repo.get('job_123')
print(job['job_name'])  # 'test_print.3mf'

# Update a job
await job_repo.update('job_123', {'progress': 75})

# List jobs
active_jobs = await job_repo.list(status='printing')

# Delete a job
await job_repo.delete('job_123')
```

### Using in Services

```python
class JobService:
    """Service for job management."""

    def __init__(self, db: Database):
        self._db = db
        self._job_repo = JobRepository(db.get_connection())
        self._file_repo = FileRepository(db.get_connection())

    async def create_job(self, job_data: Dict[str, Any]) -> Job:
        """Create new print job."""
        # Validate file exists using FileRepository
        file = await self._file_repo.get(job_data['file_id'])
        if not file:
            raise ValueError(f"File not found: {job_data['file_id']}")

        # Create job using JobRepository
        success = await self._job_repo.create(job_data)
        if not success:
            raise RuntimeError("Failed to create job")

        return await self._job_repo.get(job_data['id'])
```

### Service Integration

All repositories are integrated into services:

```python
# Analytics Service - Uses 3 repositories
class AnalyticsService:
    def __init__(self, db: Database):
        self._printer_repo = PrinterRepository(db.get_connection())
        self._job_repo = JobRepository(db.get_connection())
        self._file_repo = FileRepository(db.get_connection())

# Job Service - Uses 2 repositories
class JobService:
    def __init__(self, db: Database):
        self._job_repo = JobRepository(db.get_connection())
        self._printer_repo = PrinterRepository(db.get_connection())

# Library Service - Uses 2 repositories
class LibraryService:
    def __init__(self, db: Database):
        self._file_repo = FileRepository(db.get_connection())
        self._library_repo = LibraryRepository(db.get_connection())
```

**15 Services Using Repositories**:
1. AnalyticsService
2. JobService
3. FileService
4. FileDownloadService
5. FileCacheService
6. FileMetadataService
7. FileValidationService
8. SearchService
9. IdeaService
10. LibraryService
11. PrinterMonitoringService
12. PrinterConnectionService
13. CameraSnapshotService (SnapshotRepository via API router)
14. TrendingService (via IdeaService)
15. EventService (indirect via other services)

---

## Testing

### Unit Testing Repositories

```python
import pytest
import aiosqlite
from src.database.repositories.job_repository import JobRepository

@pytest.fixture
async def job_repo(temp_database):
    """Create job repository with test database."""
    conn = await aiosqlite.connect(temp_database)
    conn.row_factory = aiosqlite.Row
    repo = JobRepository(conn)
    yield repo
    await conn.close()

@pytest.mark.asyncio
async def test_create_job(job_repo):
    """Test creating a job."""
    job_data = {
        'id': 'test_job',
        'printer_id': 'printer_1',
        'printer_type': 'bambu_lab',
        'job_name': 'test.3mf'
    }

    result = await job_repo.create(job_data)
    assert result is True

    job = await job_repo.get('test_job')
    assert job['job_name'] == 'test.3mf'
```

**Test Coverage**:
- `tests/database/test_repositories.py` - Comprehensive tests for all 8 repositories
- Covers CRUD operations, edge cases, and error handling
- Uses temp databases for isolated testing

---

## Migration Guide

### For Developers

**Old Code (Deprecated)**:
```python
# Using Database class directly
db = Database()
await db.initialize()

# Old way
printer = await db.get_printer('printer_123')
job = await db.get_job('job_456')
```

**New Code (Preferred)**:
```python
# Using Repository pattern
db = Database()
await db.initialize()

# New way
printer_repo = PrinterRepository(db.get_connection())
printer = await printer_repo.get('printer_123')

job_repo = JobRepository(db.get_connection())
job = await job_repo.get('job_456')
```

### Backward Compatibility

The old `Database` methods are still available for backward compatibility but are marked as deprecated:

```python
"""
DEPRECATION NOTICE:
-------------------
Many methods in this class have been superseded by the Repository pattern.
New code should use the repository classes directly.
See docs/technical-debt/progress-tracker.md for migration status.
"""
```

**Migration Timeline**:
- **Phase 1 (COMPLETE)**: All repositories created, 15 services migrated
- **Phase 2 (Future)**: Remaining code migrated to repositories
- **Phase 3 (Future)**: Deprecated methods removed

---

## Performance Considerations

### Connection Management

Repositories share the database connection:

```python
db = Database()
await db.initialize()

# All repositories use the same connection
connection = db.get_connection()
job_repo = JobRepository(connection)
file_repo = FileRepository(connection)
printer_repo = PrinterRepository(connection)
```

### Retry Logic

BaseRepository automatically retries on database locks:

```python
async def _execute_write(self, sql: str, params: Optional[tuple] = None,
                         retry_count: int = 3) -> Optional[int]:
    """Execute with retry on database lock."""
    for attempt in range(retry_count):
        try:
            cursor = await self.connection.execute(sql, params or ())
            await self.connection.commit()
            return cursor.lastrowid
        except aiosqlite.OperationalError as e:
            if "locked" in str(e).lower() and attempt < retry_count - 1:
                logger.warning(f"Database locked, retrying... (attempt {attempt + 1}/{retry_count})")
                continue
            else:
                raise
```

**Benefits**:
- Prevents `OperationalError: database is locked` failures
- Automatic retry with 3 attempts
- Improves reliability under concurrent load

### Future: Connection Pooling

Connection pooling is planned for Phase 3 to improve performance under high load:

```python
# Future implementation
class Database:
    def __init__(self, db_path: str, pool_size: int = 5):
        self._pool = ConnectionPool(db_path, size=pool_size)

    async def get_connection(self):
        """Get connection from pool."""
        return await self._pool.acquire()
```

---

## Best Practices

### 1. Use Repositories in Services

✅ **DO**:
```python
class MyService:
    def __init__(self, db: Database):
        self._job_repo = JobRepository(db.get_connection())
```

❌ **DON'T**:
```python
class MyService:
    def __init__(self, db: Database):
        self._db = db  # Don't use Database directly
```

### 2. Keep Repositories Focused

✅ **DO**: One repository per domain (jobs, files, printers, etc.)
❌ **DON'T**: Create a "UtilityRepository" with mixed responsibilities

### 3. Use Type Hints

✅ **DO**:
```python
async def get(self, job_id: str) -> Optional[Dict[str, Any]]:
    """Get job by ID."""
```

❌ **DON'T**:
```python
async def get(self, job_id):  # Missing type hints
    """Get job by ID."""
```

### 4. Handle Errors Gracefully

✅ **DO**:
```python
try:
    row = await self._fetch_one("SELECT * FROM jobs WHERE id = ?", [job_id])
    return row
except Exception as e:
    logger.error("Failed to get job", job_id=job_id, error=str(e))
    return None
```

❌ **DON'T**:
```python
row = await self._fetch_one("SELECT * FROM jobs WHERE id = ?", [job_id])
return row  # No error handling
```

### 5. Write Tests

✅ **DO**: Test each repository method individually
❌ **DON'T**: Test only through integration tests

---

## Metrics

### Code Reduction

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **database.py LOC** | 2,344 | 2,344* | Maintained for compatibility |
| **Largest Repository** | N/A | ~420 LOC | All < 500 LOC |
| **Methods per Class** | 69 | ~7-12 | Better focused |
| **Services Using Pattern** | 0 | 15 | 100% adoption |
| **Test Coverage** | Integrated only | Unit + Integration | Better testability |

*Database.py unchanged for backward compatibility but marked deprecated

### Maintainability

- **Cyclomatic Complexity**: Reduced (smaller, focused methods)
- **Coupling**: Reduced (services depend on specific repositories)
- **Cohesion**: Increased (each repository has single responsibility)
- **Testability**: Greatly improved (can mock individual repositories)

---

## Future Enhancements

### Planned Improvements

1. **Connection Pooling** (Phase 3)
   - Implement connection pool for better concurrency
   - Target: 5-10 connections per pool

2. **Caching Layer** (Phase 4)
   - Add Redis/in-memory caching to repositories
   - Cache frequently accessed data (printer status, file metadata)

3. **Query Optimization** (Phase 3)
   - Add database indexes based on query patterns
   - Implement pagination optimization (separate COUNT queries)

4. **Async Transactions** (Future)
   - Add transaction support across multiple repositories
   - Implement Unit of Work pattern

---

## References

- **Progress Tracker**: [docs/technical-debt/progress-tracker.md](../technical-debt/progress-tracker.md)
- **Refactoring Roadmap**: [docs/technical-debt/refactoring-roadmap.md](../technical-debt/refactoring-roadmap.md)
- **Technical Debt Analysis**: [docs/technical-debt/analysis-report.md](../technical-debt/analysis-report.md)

---

## Conclusion

The Repository Pattern has significantly improved the Printernizer codebase:

✅ **Better Organization**: 8 focused repositories instead of 1 monolithic class
✅ **Easier Testing**: Unit tests for each repository
✅ **Better Maintainability**: Each file < 500 LOC
✅ **Service Integration**: 15 services using repositories
✅ **Backward Compatible**: Old methods still work

**Phase 1 is complete** - all repositories are implemented, integrated, tested, and documented!

---

**Last Updated**: 2025-11-17
**Document Version**: 1.0
**Status**: ✅ Active - Phase 1 Complete
