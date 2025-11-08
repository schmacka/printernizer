# Phase 2 Remaining Work - Continuation Prompt

**Date:** November 8, 2025
**Branch:** `claude/phase2-fileservice-refactor-011CUvXYwUhqVL3DQFf4Yq5h`
**Current Progress:** 81% Complete (47/58 hours)
**Remaining Work:** 11 hours (2 tasks)

---

## Context

You are continuing Phase 2 (High Priority) technical debt reduction for the Printernizer project. Phase 2 has achieved significant progress with major refactorings completed:

### ✅ Completed Phase 2 Work (47 hours)
1. **Code duplication in data transformation** (4 hours) - Fixed in commit 2d30066
2. **FileService God Class refactoring** (16 hours) - Completed in commit fa581bc
   - Split into 4 specialized services: FileDiscoveryService, FileDownloadService, FileThumbnailService, FileMetadataService
   - See `FILESERVICE_REFACTORING_SUMMARY.md` for details
3. **PrinterService God Class refactoring** (12 hours) - Completed in commit 2172e02
   - Split into 3 specialized services: PrinterConnectionService, PrinterMonitoringService, PrinterControlService
   - See `PRINTERSERVICE_REFACTORING_SUMMARY.md` for details
4. **Bare exception handlers (core services)** (5 hours) - Fixed in commit b1396b7
5. **Inconsistent pagination** (6 hours) - Fixed in commit 2d30066
6. **Missing async task cleanup** (4 hours) - Fixed in commit 3ed321b

### 🔄 Remaining Phase 2 Work (11 hours)

## Task 1: Circular Dependency Resolution (8 hours)

**Status:** PARTIALLY DONE (Late binding and events implemented)

**Objective:** Complete documentation of event-driven architecture and eliminate any remaining tight coupling between services.

### What's Already Done
- FileService and PrinterService use late binding via setter methods
- Event-driven communication implemented in both refactored services
- EventService used for decoupling monitoring, downloads, thumbnails

### What's Needed

#### 1.1 Document Event Contracts (3 hours)

Create comprehensive documentation for all events in the system:

**File:** `docs/EVENT_CONTRACTS.md` (create new)

**Content should include:**
- Complete list of all events emitted in the system
- Event name, emitter service, payload schema, subscribers
- Event flow diagrams (text-based using ASCII or mermaid)
- Event ordering and timing guarantees
- Error handling in event subscribers
- Best practices for adding new events

**Events to document:**

**FileService Events:**
```python
# FileDiscoveryService
- "files_discovered"
- "file_sync_complete"

# FileDownloadService
- "file_download_started"
- "file_download_complete"
- "file_download_failed"
- "file_needs_thumbnail_processing"

# FileThumbnailService
- "file_thumbnails_processed"
- "thumbnail_processing_failed"

# FileMetadataService
- "file_metadata_extracted"
- "metadata_extraction_failed"
```

**PrinterService Events:**
```python
# PrinterConnectionService
- "printer_connected"
- "printer_disconnected"
- "printer_connection_progress"

# PrinterMonitoringService
- "printer_status_update"
- "printer_monitoring_started"
- "printer_monitoring_stopped"
- "auto_download_triggered"
- "auto_download_failed"

# PrinterControlService
- "print_paused"
- "print_resumed"
- "print_stopped"
```

**JobService Events:**
```python
- "job_started"
- "job_completed"
- "job_failed"
- "job_updated"
```

**Other Service Events:**
Review and document events from:
- LibraryService
- ConfigService
- TimelapseService
- Any other services emitting events

#### 1.2 Create Event Flow Diagrams (2 hours)

**File:** `docs/EVENT_FLOWS.md` (create new)

**Content should include:**

1. **File Download Workflow:**
```
PrinterMonitoringService (auto-download triggered)
    ↓ emits: "auto_download_triggered"
EventService
    ↓ notifies
FileDownloadService
    ↓ emits: "file_download_started"
    ↓ downloads file
    ↓ emits: "file_download_complete"
    ↓ emits: "file_needs_thumbnail_processing"
EventService
    ↓ notifies
FileThumbnailService
    ↓ processes thumbnails
    ↓ emits: "file_thumbnails_processed"
```

2. **Printer Connection Workflow:**
3. **Job Monitoring Workflow:**
4. **File Metadata Extraction Workflow:**

Use ASCII diagrams or mermaid syntax for clarity.

#### 1.3 Audit Remaining Direct Dependencies (2 hours)

**Objective:** Find and document any remaining tight coupling between services.

**Tasks:**
1. Search for direct service-to-service method calls (excluding late-bound setters)
2. Identify candidates for event-driven refactoring
3. Document why direct calls are acceptable (if they are) or create plan to refactor
4. Update service initialization in `main.py` if needed

**Files to audit:**
```bash
src/services/job_service.py
src/services/library_service.py
src/services/timelapse_service.py
src/services/config_service.py
src/services/analytics_service.py
```

**Look for patterns like:**
```python
# Direct service calls that might be candidates for events
self.other_service.some_method()

# vs event-driven
await self.event_service.emit_event("something_happened", {...})
```

**Create audit report:** `docs/CIRCULAR_DEPENDENCY_AUDIT.md`

Include:
- Services audited
- Direct dependencies found
- Justification for keeping direct calls OR refactoring plan
- Priority ranking (high/medium/low) for any remaining issues

#### 1.4 Update Architecture Documentation (1 hour)

**File:** `.claude/skills/printernizer-architecture.md`

Update to reflect:
- Event-driven architecture patterns
- Service decomposition patterns established by FileService and PrinterService
- Late binding pattern for resolving circular dependencies
- Best practices for adding new services

### Deliverables for Task 1
- [ ] `docs/EVENT_CONTRACTS.md` - Complete event documentation
- [ ] `docs/EVENT_FLOWS.md` - Event flow diagrams
- [ ] `docs/CIRCULAR_DEPENDENCY_AUDIT.md` - Dependency audit report
- [ ] Updated `.claude/skills/printernizer-architecture.md`
- [ ] Updated `TECHNICAL_DEBT_QUICK_REFERENCE.md`

---

## Task 2: Exception Handling in Non-Core Services (3 hours)

**Status:** PENDING (Core services completed in b1396b7)

**Objective:** Replace all remaining bare `except:` clauses with specific exception types.

### Background

Phase 2 already fixed bare exception handlers in core services (FileService, PrinterService, JobService). The remaining bare exceptions are in:
- FTP service
- Background monitoring services
- Trending/analytics services

### What's Needed

#### 2.1 Identify Remaining Bare Exceptions (30 minutes)

**Search for patterns:**
```bash
# Find bare except clauses
grep -rn "except:" src/services/ --include="*.py" | grep -v "except Exception" | grep -v "except OSError"

# Also search for overly broad catches
grep -rn "except Exception:" src/services/ --include="*.py"
```

**Expected locations (based on previous assessment):**
- FTP monitoring/sync services
- Background monitoring tasks
- Trending data aggregation
- Analytics calculation
- Any scheduled/periodic tasks

#### 2.2 Replace Bare Exceptions (2 hours)

**For each bare exception, follow this pattern:**

**Before:**
```python
try:
    result = await some_operation()
except:
    logger.error("Operation failed")
    return None
```

**After:**
```python
try:
    result = await some_operation()
except (ConnectionError, TimeoutError) as e:
    logger.error("Network operation failed", error=str(e), operation="some_operation")
    return None
except FileNotFoundError as e:
    logger.error("File not found", error=str(e), path=file_path)
    return None
except Exception as e:
    logger.error("Unexpected error in some_operation", error=str(e), exc_info=True)
    return None
```

**Guidelines:**
1. **Identify specific exceptions** that can be caught (IOError, ConnectionError, ValueError, etc.)
2. **Use specific catches first**, then `except Exception` as fallback
3. **Add structured logging** with context (operation name, relevant IDs, paths)
4. **Include exc_info=True** for unexpected errors to get stack traces
5. **Consider retry logic** for transient failures (network, database)
6. **Document why** exceptions are caught (in code comments if not obvious)

**Common exception types to use:**
- `ConnectionError`, `TimeoutError` - Network operations
- `FileNotFoundError`, `PermissionError` - File operations
- `ValueError`, `KeyError`, `TypeError` - Data validation
- `asyncio.CancelledError` - Task cancellation (re-raise these!)
- `sqlite3.Error` - Database operations
- `json.JSONDecodeError` - JSON parsing

#### 2.3 Add Retry Logic Where Appropriate (30 minutes)

For transient failures (network, database), consider adding retry logic:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def fetch_printer_status(printer_id: str):
    """Fetch status with automatic retry for transient failures."""
    try:
        return await self.printer_api.get_status(printer_id)
    except ConnectionError as e:
        logger.warning("Connection failed, will retry",
                      printer_id=printer_id, error=str(e))
        raise  # tenacity will retry
```

**Files likely needing retry logic:**
- Printer API calls
- Database operations in background tasks
- File download operations
- FTP sync operations

#### 2.4 Update Tests (if they exist)

If unit tests exist for the modified services, ensure they:
- Test specific exception paths
- Verify error logging
- Test retry behavior (if added)

### Deliverables for Task 2
- [ ] All bare `except:` clauses replaced with specific exceptions
- [ ] Structured logging added with context
- [ ] Retry logic added where appropriate
- [ ] Code comments explaining exception handling strategy
- [ ] Updated `TECHNICAL_DEBT_QUICK_REFERENCE.md`
- [ ] Commit with clear description of changes

---

## Development Guidelines

### Branch Strategy
- Continue working on: `claude/phase2-fileservice-refactor-011CUvXYwUhqVL3DQFf4Yq5h`
- All changes should be committed to this branch
- Keep commits focused and well-documented

### Code Location (CRITICAL)
- **ALWAYS edit in `/src/` and `/frontend/`**
- **NEVER edit in `/printernizer/src/` or `/printernizer/frontend/`**
- Pre-commit hook automatically syncs changes

### Commit Message Format

Follow the pattern from previous Phase 2 commits:

```
type: Brief description (Phase 2)

Detailed explanation of changes made.

Key improvements:
- Point 1
- Point 2
- Point 3

Technical debt impact:
- Phase 2 progress: X% → Y% (Z/58 hours completed)

See FILENAME.md for detailed documentation.
```

**Types:** `docs:` for documentation, `refactor:` for exception handling

### Testing
After each task:
1. Validate syntax: `python -m py_compile <modified_files>`
2. Check imports work
3. Run existing tests if available: `pytest tests/`
4. Manual testing in development environment (if possible)

### Documentation Updates

**Always update:**
- `TECHNICAL_DEBT_QUICK_REFERENCE.md` - Progress tracking
- Any relevant files in `.claude/skills/` - Architecture patterns
- Commit messages - Clear descriptions

**Consider creating:**
- Summary documents for major changes (like previous refactorings)

---

## Success Criteria

### Task 1 Complete When:
- [ ] All events documented with complete payload schemas
- [ ] Event flow diagrams created for main workflows
- [ ] Dependency audit completed with justifications or plans
- [ ] Architecture documentation updated with patterns
- [ ] No unexplained circular dependencies remain
- [ ] All changes committed and pushed

### Task 2 Complete When:
- [ ] Zero bare `except:` clauses remain in codebase
- [ ] All exception handlers use specific exception types
- [ ] Structured logging added with appropriate context
- [ ] Retry logic added for transient failures
- [ ] Code is well-commented explaining exception strategy
- [ ] All changes committed and pushed

### Phase 2 Complete When:
- [ ] Both tasks completed
- [ ] `TECHNICAL_DEBT_QUICK_REFERENCE.md` shows 100% Phase 2 completion
- [ ] All documentation up to date
- [ ] All changes committed and pushed
- [ ] Ready to begin Phase 3

---

## Estimated Timeline

**Task 1: Circular Dependency Resolution (8 hours)**
- Event contracts documentation: 3 hours
- Event flow diagrams: 2 hours
- Dependency audit: 2 hours
- Architecture docs update: 1 hour

**Task 2: Exception Handling (3 hours)**
- Identify remaining exceptions: 0.5 hours
- Replace bare exceptions: 2 hours
- Add retry logic: 0.5 hours

**Total: 11 hours**

---

## Reference Documentation

### Completed Work References
- `TECHNICAL_DEBT_ASSESSMENT.md` - Original assessment
- `TECHNICAL_DEBT_QUICK_REFERENCE.md` - Progress tracker
- `FILESERVICE_REFACTORING_SUMMARY.md` - FileService refactoring details
- `PRINTERSERVICE_REFACTORING_SUMMARY.md` - PrinterService refactoring details
- `CLAUDE.md` - Development guidelines
- `.claude/skills/printernizer-*.md` - Architecture and feature documentation

### Recent Commits
- `8cdbb1c` - Phase 1: Critical bug fixes
- `2d30066` - Phase 2: Code quality & pagination
- `3ed321b` - Phase 2: Async task cleanup
- `b1396b7` - Phase 2: Exception handling (core services)
- `fa581bc` - Phase 2: FileService god class refactoring
- `13859b2` - Phase 2: FileService documentation
- `2172e02` - Phase 2: PrinterService god class refactoring (current)

### Key Files to Review

**Service Files:**
```
src/services/
├── file_service.py                    # Coordinator (refactored)
├── file_discovery_service.py          # New
├── file_download_service.py           # New
├── file_thumbnail_service.py          # New
├── file_metadata_service.py           # New
├── printer_service.py                 # Coordinator (refactored)
├── printer_connection_service.py      # New
├── printer_monitoring_service.py      # New
├── printer_control_service.py         # New
├── job_service.py                     # May have bare exceptions
├── library_service.py                 # Check dependencies
├── timelapse_service.py               # Check dependencies
├── config_service.py                  # Review
├── analytics_service.py               # Check dependencies
└── event_service.py                   # Core event system
```

**Documentation Files:**
```
docs/
├── architecture.md                    # May need updates
├── api.md                            # API reference
└── deployment.md                     # Deployment info

.claude/skills/
├── printernizer-architecture.md      # Update with patterns
├── printernizer-development-workflow.md
├── printernizer-features.md
└── printernizer-deployment.md
```

---

## Next Phase Preview

After Phase 2 completion (100%), Phase 3 (Medium Priority) includes:
- Missing docstrings (6.1)
- Hardcoded magic numbers (5.2)
- Test coverage gaps (4.1-4.2)
- Inconsistent error handling patterns (3.1)
- Missing settings validation (5.1)
- Complex logic without comments (6.2)

**Estimated:** 30-40 hours total

---

## Getting Started

1. **Read this prompt thoroughly**
2. **Review recent commits** to understand refactoring patterns
3. **Review reference documentation** (refactoring summaries, technical debt docs)
4. **Start with Task 1** (Event Contracts Documentation)
5. **Create TODO list** to track progress
6. **Work systematically** through each subtask
7. **Commit frequently** with clear messages
8. **Update documentation** as you go

---

## Questions to Consider

Before starting, ensure you understand:
- [ ] Event-driven architecture pattern used in FileService/PrinterService
- [ ] Late binding pattern for circular dependency resolution
- [ ] Current event system (EventService implementation)
- [ ] Why specific exceptions are better than bare catches
- [ ] How to structure retry logic
- [ ] Documentation standards for the project

If anything is unclear, review the refactoring summary documents and recent commits for examples.

---

**Ready to complete Phase 2! Let's finish the final 11 hours of high-priority technical debt reduction.**
