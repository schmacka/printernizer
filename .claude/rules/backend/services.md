---
paths: src/services/**/*.py
---

# Service Architecture Pattern

## BaseService Pattern

All services should inherit from `BaseService` for consistency.

```python
from src.services.base_service import BaseService

class MyNewService(BaseService):
    """Service for handling specific domain logic."""

    async def initialize(self):
        """Initialize the service."""
        await super().initialize()
        # Service-specific initialization

    async def cleanup(self):
        """Clean up service resources."""
        # Service-specific cleanup
        await super().cleanup()
```

## BaseService Features

Located at `src/services/base_service.py`:

- **Initialization tracking**: `_initialized` flag
- **Database access**: Common database operations
- **Lifecycle management**: Initialize/cleanup hooks
- **Logging**: Built-in logger

## Key Services

| Service | Purpose |
|---------|---------|
| `PrinterService` | Printer management |
| `JobService` | Job tracking |
| `FileService` | File management |
| `ConfigService` | Configuration |
| `AnalyticsService` | Business analytics |
| `MaterialService` | Material tracking |
| `TimelapseService` | Timelapse generation |
| `LibraryService` | File library |

## Best Practices

1. **Single Responsibility**: Each service handles one domain
2. **Dependency Injection**: Services receive dependencies via constructor
3. **Async Operations**: Use `async/await` for I/O operations
4. **Error Handling**: Use domain-specific exceptions from `src/utils/errors.py`
5. **Logging**: Use the inherited logger for debugging

## Service vs Router

- **Router**: HTTP endpoint definitions, request/response handling
- **Service**: Business logic, data processing, external integrations

Keep routers thin - delegate logic to services.
