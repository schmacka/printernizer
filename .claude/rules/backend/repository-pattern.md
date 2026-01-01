---
paths: src/database/**/*.py, src/services/**/*.py
---

# Repository Pattern (Migration in Progress)

## Current State

The database layer is undergoing **Phase 1 refactoring** to the Repository pattern.

## New Approach (Preferred)

Use repository classes from `src/database/repositories/`:

```python
from src.database.repositories import PrinterRepository

async def get_printer(connection, printer_id: str):
    repo = PrinterRepository(connection)
    return await repo.get_printer(printer_id)
```

## Available Repositories

| Repository | Purpose |
|------------|---------|
| `PrinterRepository` | Printer CRUD operations |
| `JobRepository` | Job CRUD operations |
| `FileRepository` | File CRUD operations |
| `SnapshotRepository` | Camera snapshots |
| `TrendingRepository` | Trending analytics |
| `IdeaRepository` | Print ideas |
| `LibraryRepository` | File library |
| `UsageStatisticsRepository` | Usage stats |

## Legacy Approach (Deprecated)

Direct database methods in `src/database/database.py` are still available for backward compatibility but should not be used in new code.

```python
# Deprecated - do not use in new code
from src.database.database import Database
db = Database()
printer = await db.get_printer(printer_id)
```

## Migration Guidelines

1. **New code**: Always use Repository classes
2. **Existing code**: Migrate to Repository pattern when touching the code
3. **Do not add** new methods to `database.py`
4. **BaseRepository**: All repositories inherit from `BaseRepository`

## BaseRepository Features

Located at `src/database/repositories/base_repository.py`:

- Connection management
- Common CRUD operations
- Query building utilities
- Error handling

## References

- Repository base: `src/database/repositories/base_repository.py`
- Legacy database: `src/database/database.py`
