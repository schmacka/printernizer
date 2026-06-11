# Documentation Guide

**Version**: 1.0
**Last Updated**: 2025-11-17
**Purpose**: Standards and guidelines for code documentation in Printernizer

---

## Table of Contents

1. [Overview](#overview)
2. [Documentation Standards](#documentation-standards)
3. [Module-Level Documentation](#module-level-documentation)
4. [Class Documentation](#class-documentation)
5. [Method Documentation](#method-documentation)
6. [Code Comments](#code-comments)
7. [Examples and Usage](#examples-and-usage)
8. [Documentation Tools](#documentation-tools)

---

## Overview

This guide defines the documentation standards for the Printernizer codebase. Following these standards ensures:

- **Consistency**: Uniform documentation style across the codebase
- **Maintainability**: Easy to understand and update code
- **Onboarding**: New developers can quickly understand the system
- **API Clarity**: Clear interfaces for all public methods
- **Type Safety**: Complete type hints for better IDE support

### Documentation Philosophy

- **Explain "Why" not "What"**: Code shows what it does, comments explain why
- **Examples Over Theory**: Provide practical usage examples
- **Context Matters**: Include implementation history and design decisions
- **Keep it Current**: Update docs when code changes

---

## Documentation Standards

### General Principles

1. **All public APIs must be documented** - No exceptions
2. **Type hints are mandatory** - All function signatures must include types
3. **Use Google-style docstrings** - Consistent formatting
4. **Include examples** - At least one usage example per class/module
5. **Link related code** - Use "See Also" sections

### Documentation Hierarchy

```
Module-level docstring (file.py)
  ↓
Class docstring
  ↓
Method docstrings
  ↓
Inline comments (for complex logic)
```

---

## Module-Level Documentation

Every Python module (.py file) should start with a comprehensive module-level docstring.

### Template

```python
"""
Module title - Brief one-line description.

Detailed description explaining:
- What this module provides
- Key features and capabilities
- When to use it
- How it fits into the larger architecture

Design Principles:
    - Principle 1: Explanation
    - Principle 2: Explanation

Architecture:
    Explain how this module relates to other modules.
    Include ASCII diagrams if helpful.

Usage Example:
    ```python
    # Practical code example showing typical usage
    from module import Class

    instance = Class()
    result = instance.method()
    ```

Implementation History:
    - Date: What changed and why
    - Date: What changed and why

See Also:
    - related_module.py - Description
    - docs/guide.md - Documentation reference
"""
```

### Real Example

See [`src/database/repositories/base_repository.py`](../src/database/repositories/base_repository.py) for a complete example.

**Key Elements**:
- Brief overview paragraph
- Detailed feature list with bullets
- Architecture diagram showing relationships
- Complete usage example with imports and instantiation
- Implementation history for context
- Cross-references to related code

---

## Class Documentation

Every class should have a docstring explaining its purpose, attributes, and key features.

### Template

```python
class ServiceName:
    """
    Brief one-line description of the class purpose.

    Detailed description of what the class does and when to use it.
    Explain the responsibilities and key features.

    Key Features:
        - Feature 1: Description
        - Feature 2: Description
        - Feature 3: Description

    Attributes:
        attribute_name (type): Description of the attribute
        another_attribute (type): Description

    Example:
        ```python
        service = ServiceName(dependency)
        result = service.do_something()
        ```

    Thread Safety:
        Describe thread safety characteristics if relevant.

    Performance Notes:
        Any performance considerations users should know about.

    See Also:
        - RelatedClass - What it does
        - related_module - Where to find more
    """
```

### Real Example

```python
class JobRepository(BaseRepository):
    """
    Repository for job-related database operations.

    Provides CRUD operations and specialized queries for 3D print jobs.
    Handles duplicate detection, status tracking, and job analytics.

    Key Features:
        - Duplicate job detection via UNIQUE constraint
        - Flexible filtering (by printer, status, business flag)
        - Efficient count queries for pagination
        - Date range queries for analytics
        - Job statistics and success rate calculation

    Thread Safety:
        Operations are atomic but the repository is not thread-safe.
        Use connection pooling for concurrent access.
    """
```

---

## Method Documentation

All public methods (and complex private methods) need comprehensive docstrings.

### Template

```python
async def method_name(self, param1: str, param2: int = 0) -> Dict[str, Any]:
    """
    Brief one-line description of what the method does.

    Detailed explanation of the method's behavior, including:
    - What it does
    - When to use it
    - Any important side effects

    Args:
        param1: Description of first parameter
        param2: Description of second parameter (default: 0)

    Returns:
        Description of return value. For complex returns, use structure:
            Dictionary containing:
                - key1 (type): Description
                - key2 (type): Description

    Raises:
        ExceptionType: When this exception is raised
        AnotherException: When this other exception is raised

    Example:
        ```python
        result = await obj.method_name("value", param2=5)
        print(result['key1'])
        ```

    Performance:
        Any performance notes (e.g., "O(n) complexity", "Loads all in memory")

    Note:
        Any additional important information.

    See Also:
        - related_method(): Description of when to use instead
    """
```

### Real Example

```python
async def get_dashboard_stats(self) -> Dict[str, Any]:
    """
    Get main dashboard statistics for the overview page.

    Calculates comprehensive statistics across all jobs and printers including:
    - Total job count (business vs. private)
    - Active printer count
    - Total runtime across all completed jobs
    - Total material consumption (in kg)
    - Estimated costs (material + power)

    Returns:
        Dictionary containing:
            - total_jobs (int): Total number of jobs
            - active_printers (int): Number of currently active printers
            - total_runtime (int): Total print time in minutes
            - material_used (float): Total material used in kg
            - estimated_costs (float): Total estimated costs in EUR
            - business_jobs (int): Count of business jobs
            - private_jobs (int): Count of private jobs

        On error, returns all values as 0 to prevent frontend crashes.

    Performance:
        Loads all jobs into memory. For large datasets (>10,000 jobs),
        consider implementing caching or pagination.

    Example:
        ```python
        stats = await analytics.get_dashboard_stats()

        print(f"Total jobs: {stats['total_jobs']}")
        print(f"Material used: {stats['material_used']:.2f} kg")
        ```

    See Also:
        - get_printer_usage(): For per-printer statistics
        - get_material_consumption(): For detailed material breakdown
    """
```

---

## Code Comments

### When to Use Comments

**DO use comments for**:
- Complex algorithms that aren't immediately obvious
- Workarounds for known issues
- Performance optimizations that look unusual
- Business logic that requires explanation
- TODO/FIXME markers with context

**DON'T use comments for**:
- Obvious code (e.g., `i += 1  # Increment i`)
- Repeating what the code already says
- Commented-out code (use git history instead)

### Comment Style

```python
# Good: Explains WHY, not WHAT
# Use WAL mode for better concurrent read performance with connection pooling
await conn.execute("PRAGMA journal_mode=WAL")

# Bad: Explains WHAT (already obvious from code)
# Set journal mode to WAL
await conn.execute("PRAGMA journal_mode=WAL")

# Good: Complex business logic
# Material costs vary by type: PLA (€20/kg) is cheapest,
# Nylon (€40/kg) is most expensive. Using market averages.
cost_per_kg = MATERIAL_COSTS.get(material_type, 25.0)

# Good: Workaround with explanation
# WORKAROUND: SQLite doesn't support DROP COLUMN, so we create a new table
# and copy data. This is safe because we're in a transaction.
await self._execute_write("ALTER TABLE jobs RENAME TO jobs_old")
```

### TODO/FIXME Comments

Always include context and date:

```python
# TODO(2025-11-17): Add caching to reduce database queries
# Currently loads all jobs on every call. Should cache for 5 minutes.

# FIXME(2025-11-17): Race condition in job status updates
# Two concurrent updates can cause status to be incorrect.
# Need to implement optimistic locking with version field.

# HACK(2025-11-17): Temporary workaround for bambu_lab API bug
# API sometimes returns None for temperature. Fall back to 0.
# Remove when API is fixed (tracked in issue #123)
temp = response.get('temperature') or 0
```

---

## Examples and Usage

### Module Example Pattern

Every module should have at least one complete, runnable example:

```python
"""
Usage Example:
    ```python
    # All necessary imports shown
    from src.database.database import Database
    from src.services.job_service import JobService

    # Complete initialization
    db = Database("printernizer.db")
    await db.connect()
    job_service = JobService(db)

    # Typical usage flow
    jobs = await job_service.list_active_jobs()
    for job in jobs:
        print(f"{job.name}: {job.status}")

    # Cleanup
    await db.close()
    ```
"""
```

### Method Example Pattern

Methods should show realistic usage with expected inputs and outputs:

```python
"""
Example:
    ```python
    # Create a job with required fields
    job_data = {
        'id': 'job_123',
        'printer_id': 'bambu_a1_001',
        'job_name': 'test_print.gcode',
        'status': 'pending'
    }
    success = await repo.create(job_data)
    if success:
        print("Job created successfully")

    # Update job status
    await repo.update('job_123', {
        'status': 'printing',
        'progress': 50
    })

    # Query with filters
    printing_jobs = await repo.list(
        printer_id='bambu_a1_001',
        status='printing'
    )
    ```
"""
```

---

## Documentation Tools

### Type Hints

**Always use type hints** for all function signatures:

```python
from typing import List, Dict, Any, Optional, Union, Tuple

# Good: Complete type hints
async def get_jobs(
    self,
    printer_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    ...

# Bad: No type hints
async def get_jobs(self, printer_id=None, status=None, limit=50):
    ...
```

### Docstring Format

Use Google-style docstrings with proper indentation:

```python
def function(arg1: str, arg2: int) -> bool:
    """
    Summary line.

    Extended description paragraph.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ValueError: When validation fails

    Example:
        ```python
        result = function("test", 42)
        ```
    """
```

### Documentation Generation

Future: Consider using Sphinx or MkDocs for auto-generating documentation:

```bash
# Sphinx setup (planned)
pip install sphinx sphinx-rtd-theme
sphinx-quickstart docs/
sphinx-build -b html docs/ docs/_build/

# MkDocs setup (planned)
pip install mkdocs mkdocs-material
mkdocs new .
mkdocs serve
```

---

## Best Practices

### 1. Keep Documentation Close to Code

- Document at the point of implementation
- Update docs when changing code
- Review docs during code reviews

### 2. Be Specific

```python
# Bad: Vague
"""Get data from database."""

# Good: Specific
"""
Get all active jobs from the database, filtered by printer and status.

Returns empty list if no jobs match the criteria.
"""
```

### 3. Include Edge Cases

```python
"""
Get job by ID.

Args:
    job_id: Unique job identifier

Returns:
    Job dictionary if found, None if not found.
    Returns None (not error) for invalid ID format.

Note:
    Empty string job_id returns None, not an error.
"""
```

### 4. Document Assumptions

```python
"""
Calculate printer utilization percentage.

Assumptions:
    - Printers are available 24/7 (no scheduled downtime)
    - Only completed jobs count toward utilization
    - Assumes 200W average power consumption per printer

Returns:
    Utilization percentage (0-100). Can exceed 100% if
    jobs overlap (multiple jobs per printer).
"""
```

### 5. Cross-Reference Related Code

```python
"""
Create a new print job.

See Also:
    - update_job(): For modifying existing jobs
    - get_job(): For retrieving job details
    - JobRepository.create(): Underlying database operation
    - docs/api/jobs.md: API endpoint documentation
"""
```

---

## Documentation Checklist

Use this checklist when adding or reviewing documentation:

### Module Level
- [ ] Module docstring present
- [ ] Brief overview included
- [ ] Key features listed
- [ ] Architecture explanation (if applicable)
- [ ] Usage example with imports
- [ ] "See Also" references

### Class Level
- [ ] Class docstring present
- [ ] Purpose clearly stated
- [ ] Key features listed
- [ ] Attributes documented
- [ ] Usage example included
- [ ] Thread safety notes (if relevant)

### Method Level
- [ ] Method docstring present
- [ ] Parameters documented with types
- [ ] Return value documented with structure
- [ ] Exceptions documented
- [ ] Usage example included
- [ ] Performance notes (if relevant)
- [ ] "See Also" references for alternatives

### Code Quality
- [ ] Type hints for all parameters and returns
- [ ] Docstring formatting consistent (Google style)
- [ ] Examples are runnable
- [ ] No obvious typos or grammar errors
- [ ] Documentation matches actual code behavior

---

## Examples from Codebase

### Excellent Examples

1. **`src/database/repositories/base_repository.py`**
   - Comprehensive module docstring with architecture diagram
   - Detailed method documentation with examples
   - Clear explanation of retry logic and error handling

2. **`src/database/repositories/job_repository.py`**
   - Complete database schema documentation
   - Usage examples for common operations
   - Error handling explained

3. **`src/services/analytics_service.py`**
   - Detailed cost estimation formulas
   - Performance considerations documented
   - Multiple usage examples

### Templates to Follow

When documenting new code, use these as templates:
- Repository: `base_repository.py`
- Service: `analytics_service.py`
- Complex logic: `bambu_lab.py` (status extraction methods)

---

## Future Improvements

### Planned Enhancements

1. **API Documentation**
   - OpenAPI/Swagger specs for all endpoints
   - Interactive API explorer
   - Request/response examples

2. **Architecture Diagrams**
   - System architecture diagrams
   - Database schema diagrams
   - Sequence diagrams for complex flows

3. **Generated Documentation**
   - Sphinx or MkDocs setup
   - Auto-generated API docs
   - Searchable documentation site

4. **Testing Documentation**
   - Test coverage reports
   - Testing guidelines
   - Example test cases

---

## Questions?

- Review existing code for examples
- Check [CONTRIBUTING.md](../CONTRIBUTING.md) for general guidelines
- See [technical-debt/](technical-debt/) for implementation notes

---

**Maintained by**: Development Team
**Last Review**: 2025-11-17
**Next Review**: Quarterly or when standards change
