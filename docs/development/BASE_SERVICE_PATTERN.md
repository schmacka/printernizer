# BaseService Pattern

**Purpose**: Standardize service initialization and lifecycle management
**Date**: 2025-10-04
**Status**: Recommended Pattern (Opt-in)

## Overview

The `BaseService` class provides a standardized pattern for Printernizer services.

## Usage

### Creating a New Service

```python
from src.services.base_service import BaseService
from src.database.database import Database

class MyService(BaseService):
    """My custom service."""

    def __init__(self, database: Database, additional_dep):
        super().__init__(database)
        self.additional_dep = additional_dep

    async def initialize(self):
        """Initialize service resources."""
        await super().initialize()  # Marks as initialized
        
        # Service-specific initialization
        await self._create_tables()
        await self._load_data()

    async def shutdown(self):
        """Cleanup resources."""
        # Service-specific cleanup
        await self._cleanup()
        
        await super().shutdown()  # Marks as shutdown
```

## Benefits

- ✅ Standardized initialization pattern
- ✅ Prevents double-initialization
- ✅ Common database access
- ✅ Lifecycle management
- ✅ Consistent logging

## Migration

Existing services can optionally adopt this pattern in future refactorings.

**Priority**: LOW (optional enhancement)

Last updated: 2025-10-04
