# Refactoring Roadmap

**Document Version**: 1.0
**Created**: 2025-11-17
**Last Updated**: 2025-11-17

---

## Executive Summary

This roadmap outlines a strategic approach to addressing the ~130 technical debt issues identified in the Printernizer codebase. The plan is organized into 4 phases over an estimated 35-50 days of development effort.

### Key Principles
1. **Safety First** - Fix critical bugs before major refactoring
2. **Incremental Progress** - Small, testable changes over big bang rewrites
3. **Test Coverage** - Add tests before and during refactoring
4. **Business Value** - Prioritize issues impacting users and reliability

---

## Timeline Overview

```
Phase 1: CRITICAL Issues     [████████░░░░░░░░░░░░] Weeks 1-4  (19-25 days)
Phase 2: HIGH Priority       [░░░░░░░░████████░░░░] Weeks 5-7  (12-17 days)
Phase 3: MEDIUM Priority     [░░░░░░░░░░░░████████] Weeks 8-9  (7-11 days)
Phase 4: LOW Priority        [░░░░░░░░░░░░░░░░░░░░] Ongoing
```

**Total Estimated Effort**: 35-50 days
**Recommended Team Size**: 2-3 developers
**Target Completion**: 9-12 weeks

---

## PHASE 1: CRITICAL ISSUES (Weeks 1-4)

**Goal**: Fix critical stability and functionality issues
**Effort**: 19-25 days
**Impact**: High - Improves stability, fixes broken features

### Week 1: Error Handling Cleanup (5 days)

#### Days 1-3: Fix Bare Except Blocks
**Issues**: 34 bare `except:` statements
**Priority**: P0
**Files**: `bambu_lab.py`, `library.py`, `camera_snapshot_service.py`

**Tasks**:
1. Create error handling pattern document
2. Fix bambu_lab.py (8 bare excepts)
   - Lines 383, 390, 397, 412, 423, 431, 442, 452
   - Replace with specific exception types
   - Add proper logging
3. Fix library.py (2 bare excepts)
   - Lines 573, 610 (JSON parsing)
4. Fix camera_snapshot_service.py (1 bare except)
   - Line 228
5. Add tests for each exception handler

**Success Criteria**:
- ✅ Zero bare `except:` statements in production code
- ✅ All exceptions logged with proper context
- ✅ Tests verify exception handling
- ✅ No regression in functionality

**Deliverables**:
- PR: "fix: Replace bare except blocks with specific exception handling"
- Documentation: Error handling guidelines

---

#### Days 4-5: Improve Prusa Exception Handlers
**Issues**: 16 broad exception handlers in `prusa.py`
**Priority**: P0

**Tasks**:
1. Create `@handle_printer_errors` decorator
2. Replace 16 `except Exception as e:` blocks
3. Add specific exception types
4. Improve logging (include stack traces)
5. Add tests for error scenarios

**Success Criteria**:
- ✅ Specific exception types used
- ✅ All errors logged with details
- ✅ Decorator reusable across printer implementations

**Deliverables**:
- PR: "fix: Improve error handling in Prusa printer integration"

---

### Week 2-3: Analytics Service Implementation (10 days)

**Issues**: 5 TODO stubs, all methods return fake data
**Priority**: P0
**File**: `analytics_service.py`

#### Days 6-8: Core Analytics (3 days)
**Tasks**:
1. **Day 6**: Implement `get_dashboard_stats()`
   - Total jobs query
   - Active printers query
   - Today's stats (completed/failed)
   - Total print time calculation
   - Material usage calculation
   - Add caching (5-minute TTL)
   - Unit tests

2. **Day 7**: Implement `get_printer_usage()`
   - Usage per printer
   - Success rate calculation
   - Print time per printer
   - Material per printer
   - Date range filtering
   - Unit tests

3. **Day 8**: Implement `get_material_consumption()`
   - Total consumption
   - Group by material type
   - Group by printer
   - Trend analysis
   - Unit tests

**Success Criteria**:
- ✅ All queries return real data
- ✅ Performance < 500ms per query
- ✅ Caching reduces database load
- ✅ 100% test coverage for new code

---

#### Days 9-12: Advanced Analytics (4 days)
**Tasks**:
1. **Day 9**: Implement `get_time_analytics()`
   - Time-based grouping (daily/weekly/monthly)
   - Trend calculations
   - Anomaly detection
   - Unit tests

2. **Day 10**: Implement `get_business_report()`
   - Business vs private split
   - Cost calculations
   - Profitability metrics
   - Custom date ranges
   - Unit tests

3. **Day 11**: Implement data export
   - CSV export
   - Excel export (using openpyxl)
   - PDF reports (using reportlab)
   - Add API endpoints

4. **Day 12**: Integration testing
   - End-to-end API tests
   - Performance benchmarking
   - Load testing (1000+ jobs)
   - Documentation update

**Success Criteria**:
- ✅ All TODO comments removed
- ✅ Analytics dashboard functional
- ✅ Export formats working
- ✅ API documentation updated

**Deliverables**:
- PR: "feat: Implement complete analytics service"
- Documentation: Analytics API guide
- Performance report

---

#### Days 13-15: Testing & Documentation (3 days)
**Tasks**:
1. **Day 13**: Comprehensive testing
   - Edge case testing
   - Error scenario testing
   - Data validation testing
   - Integration tests

2. **Day 14**: Performance optimization
   - Query optimization
   - Index creation
   - Caching strategy
   - Benchmark results

3. **Day 15**: Documentation
   - API documentation
   - User guide
   - Analytics dashboard guide
   - Release notes

---

### Week 4: Database Refactoring - Phase 1 (5 days)

**Issues**: Monolithic database class (2,344 LOC)
**Priority**: P0
**Goal**: Setup foundation for repository pattern

#### Days 16-17: Repository Pattern Setup (2 days)
**Tasks**:
1. **Day 16**: Design and create infrastructure
   - Create `src/database/repositories/` package
   - Create `base_repository.py`
   - Define BaseRepository abstract class
   - Add common CRUD methods
   - Add connection management
   - Write documentation

2. **Day 17**: Initial implementation
   - Implement BaseRepository
   - Add transaction support
   - Add batch operations
   - Unit tests for base functionality

**Deliverables**:
- Repository pattern framework
- Base repository with tests
- Documentation

---

#### Days 18-20: JobRepository Extraction (3 days)
**Tasks**:
1. **Day 18**: Create JobRepository
   - Create `job_repository.py` (~400 LOC)
   - Migrate job CRUD methods
   - Migrate job query methods
   - Migrate job status methods

2. **Day 19**: Testing and integration
   - Unit tests for JobRepository
   - Integration tests with database
   - Update JobService to use repository
   - Verify all functionality

3. **Day 20**: Cleanup and documentation
   - Remove old job methods from Database
   - Update all imports
   - Run regression tests
   - Update documentation

**Success Criteria**:
- ✅ All job operations use JobRepository
- ✅ Zero regressions
- ✅ 100% test coverage
- ✅ Documentation complete

**Deliverables**:
- PR: "refactor: Extract JobRepository from monolithic Database class"

---

## PHASE 2: HIGH PRIORITY ISSUES (Weeks 5-7)

**Goal**: Reduce code duplication and improve maintainability
**Effort**: 12-17 days
**Impact**: Medium-High - Improves code quality, reduces bugs

### Week 5: Database Refactoring - Phase 2 (5 days)

#### Days 21-22: FileRepository Extraction (2 days)
**Tasks**:
1. Create `file_repository.py` (~350 LOC)
2. Migrate file operations
3. Add search optimization
4. Add deduplication logic
5. Update FileService
6. Tests and documentation

**Deliverables**:
- PR: "refactor: Extract FileRepository"

---

#### Days 23-24: Additional Repositories (2 days)
**Tasks**:
1. **Day 23**:
   - Extract IdeaRepository (~300 LOC)
   - Extract SnapshotRepository (~250 LOC)

2. **Day 24**:
   - Extract MaterialRepository (~250 LOC)
   - Update services
   - Integration testing

**Deliverables**:
- PR: "refactor: Extract Idea, Snapshot, and Material repositories"

---

#### Day 25: Final Repository Extraction (1 day)
**Tasks**:
1. Extract TrendingRepository (~300 LOC)
2. Extract AnalyticsRepository (~200 LOC)
3. Update Database class (reduce to connection management only)
4. Full regression testing
5. Update all documentation

**Success Criteria**:
- ✅ Database.py < 300 LOC
- ✅ All repositories < 500 LOC each
- ✅ All tests passing
- ✅ No performance regression

**Deliverables**:
- PR: "refactor: Complete database repository extraction"
- Architecture documentation

---

### Week 6: Bambu Lab Refactoring (5 days)

#### Days 26-28: Download Method Consolidation (3 days)
**Issues**: 5 download methods with 60% code duplication

**Tasks**:
1. **Day 26**: Design strategy pattern
   - Create DownloadStrategy interface
   - Create DownloadHandler base class
   - Define retry/fallback logic
   - Design progress tracking

2. **Day 27**: Implement strategies
   - FTPDownloadStrategy
   - HTTPDownloadStrategy
   - MQTTDownloadStrategy
   - Unified error handling
   - Unified progress tracking

3. **Day 28**: Integration and testing
   - Replace old download methods
   - Test each strategy
   - Test fallback mechanism
   - Performance testing
   - Documentation

**Success Criteria**:
- ✅ Code duplication < 20%
- ✅ All download methods working
- ✅ Proper fallback handling
- ✅ Improved maintainability

**Deliverables**:
- PR: "refactor: Consolidate Bambu Lab download methods using strategy pattern"

---

#### Days 29-30: Status Method Refactoring (2 days)
**Issues**: Large status methods with duplication

**Tasks**:
1. **Day 29**: Create StatusExtractor class
   - `extract_temperature_data()`
   - `extract_progress_data()`
   - `extract_state_data()`
   - Safe extraction methods
   - Unit tests

2. **Day 30**: Refactor status methods
   - Refactor `_get_status_bambu_api()` (reduce from 330 to <100 lines)
   - Refactor `_get_status_mqtt()`
   - Share extraction logic
   - Integration tests
   - Documentation

**Success Criteria**:
- ✅ `_get_status_bambu_api()` < 100 LOC
- ✅ Shared extraction logic
- ✅ Improved testability
- ✅ No regression

**Deliverables**:
- PR: "refactor: Extract status extraction logic from Bambu Lab methods"

---

### Week 7: API & Service Improvements (5 days)

#### Days 31-32: API Query Optimization (2 days)
**Issues**: Pagination fetches all records to count

**Tasks**:
1. **Day 31**: Implement efficient pagination
   - Add `get_files_paginated()` to FileService
   - Add `get_jobs_paginated()` to JobService
   - Separate COUNT(*) queries
   - Update API endpoints
   - Unit tests

2. **Day 32**: Testing and benchmarking
   - Performance testing
   - Load testing with 10,000 records
   - Compare before/after
   - Documentation

**Success Criteria**:
- ✅ 99% reduction in data transfer for counts
- ✅ API response time < 200ms
- ✅ Handles 10,000+ records efficiently

**Deliverables**:
- PR: "perf: Optimize API pagination queries"
- Performance report

---

#### Days 33-35: Library Service Refactoring (3 days)
**Issues**: Large service (1,081 LOC), missing color extraction

**Tasks**:
1. **Day 33**: Implement color extraction
   - Create filament color mapping
   - Implement `extract_filament_colors()`
   - Add caching
   - Tests

2. **Day 34**: Split service
   - Create `file_metadata_extractor.py`
   - Create `file_deduplicator.py`
   - Create `library_manager.py`

3. **Day 35**: Integration
   - Update library_service.py (orchestration only)
   - Update all imports
   - Integration tests
   - Documentation

**Success Criteria**:
- ✅ Color extraction working
- ✅ Each file < 400 LOC
- ✅ Clear separation of concerns
- ✅ All tests passing

**Deliverables**:
- PR: "feat: Implement filament color extraction"
- PR: "refactor: Split library service into focused modules"

---

## PHASE 3: MEDIUM PRIORITY ISSUES (Weeks 8-9)

**Goal**: Improve code quality and security
**Effort**: 7-11 days
**Impact**: Medium - Better maintainability, security

### Week 8: Configuration & Frontend (5 days)

#### Days 36-37: Configuration Extraction (2 days)
**Issues**: 15+ hardcoded values

**Tasks**:
1. **Day 36**: Create configuration module
   - Create `src/config/constants.py`
   - Define PollingIntervals
   - Define API constants
   - Create helper functions

2. **Day 37**: Replace hardcoded values
   - Extract sleep durations (event_service.py)
   - Extract API URLs (5+ files)
   - Update tests
   - Documentation

**Deliverables**:
- PR: "refactor: Extract hardcoded configuration values"

---

#### Days 38-40: Frontend Improvements (3 days)
**Issues**: 40+ console statements, 20+ XSS risks

**Tasks**:
1. **Day 38**: Create logging utility
   - Create `logger.js`
   - Implement log levels
   - Add debug mode support
   - Replace console statements

2. **Day 39**: Fix XSS risks
   - Create `escapeHtml()` utility
   - Audit innerHTML usage
   - Fix vulnerabilities
   - Add CSP headers

3. **Day 40**: Testing and validation
   - Security testing
   - Performance testing
   - Documentation

**Success Criteria**:
- ✅ No console.log in production
- ✅ All user input escaped
- ✅ CSP headers configured
- ✅ Security tests passing

**Deliverables**:
- PR: "refactor: Replace console statements with proper logging"
- PR: "security: Fix XSS vulnerabilities in frontend"

---

### Week 9: Infrastructure Improvements (4 days)

#### Days 41-42: Async Task Management (2 days)
**Issues**: Tasks not retained, no cleanup

**Tasks**:
1. **Day 41**: Implement task management
   - Store task references
   - Add shutdown method
   - Add to application lifecycle

2. **Day 42**: Testing
   - Test task cancellation
   - Test graceful shutdown
   - Integration tests
   - Documentation

**Deliverables**:
- PR: "fix: Properly manage async tasks lifecycle"

---

#### Days 43-46: Database Connection Pooling (4 days)
**Issues**: Single connection, no pooling

**Tasks**:
1. **Day 43**: Design connection pool
   - Define pool architecture
   - Choose pool size strategy
   - Design connection lifecycle

2. **Day 44**: Implement pool
   - Create pool using asyncio.Queue
   - Add acquire/release methods
   - Add context manager
   - Unit tests

3. **Day 45**: Integration
   - Update Database class
   - Update all queries
   - Migration guide

4. **Day 46**: Testing and benchmarking
   - Performance testing
   - Concurrent access testing
   - Load testing
   - Documentation

**Success Criteria**:
- ✅ Connection pooling working
- ✅ Handles concurrent requests
- ✅ Performance improved
- ✅ No deadlocks

**Deliverables**:
- PR: "feat: Implement database connection pooling"
- Performance report

---

## PHASE 4: LOW PRIORITY ISSUES (Ongoing)

**Goal**: Continuous improvement
**Effort**: Ongoing
**Impact**: Low - Quality of life improvements

### Type Hints Improvement
**Timeline**: Ongoing
**Effort**: 1-2 hours per week

**Tasks**:
- Add missing return types (10+ functions)
- Document type ignores
- Enable mypy --strict
- Create TypedDicts for complex structures

**Success Criteria**:
- ✅ Mypy passes with --strict
- ✅ All public methods have type hints
- ✅ IDE autocomplete improved

---

### Code Documentation
**Timeline**: During refactoring
**Effort**: Include in each PR

**Tasks**:
- Add docstrings to all public methods
- Add code comments for complex logic
- Update README and guides
- Create architecture diagrams

**Success Criteria**:
- ✅ All public APIs documented
- ✅ Architecture clearly explained
- ✅ Examples for common use cases

---

### Test Coverage Expansion
**Timeline**: Ongoing
**Effort**: Include in each PR

**Tasks**:
- Maintain 80% coverage minimum
- Add integration tests
- Add E2E tests for critical workflows
- Enable coverage reporting in CI

**Success Criteria**:
- ✅ 80% overall coverage
- ✅ 100% coverage for critical paths
- ✅ CI fails if coverage drops

---

## Resource Planning

### Team Structure

**Recommended Team**: 2-3 developers

**Developer 1 - Backend Focus**:
- Phase 1: Error handling, Analytics service
- Phase 2: Database refactoring, Bambu Lab refactoring
- Phase 3: Configuration, async improvements

**Developer 2 - Full Stack**:
- Phase 1: Analytics service, Database setup
- Phase 2: API optimization, Library service
- Phase 3: Frontend improvements, connection pooling

**Developer 3 - QA/Testing** (optional):
- Test coverage for all phases
- Performance testing
- Security testing
- Documentation review

---

## Risk Management

### High Risk Areas

#### 1. Database Refactoring (Phase 1-2)
**Risk**: Breaking existing functionality
**Mitigation**:
- Extensive test coverage before refactoring
- Incremental changes (one repository at a time)
- Feature flags for gradual rollout
- Comprehensive regression testing

#### 2. Bambu Lab Printer Integration (Phase 2)
**Risk**: Breaking printer communication
**Mitigation**:
- Test with real hardware
- Maintain backward compatibility
- Gradual rollout per download method
- Easy rollback plan

#### 3. Frontend XSS Fixes (Phase 3)
**Risk**: Breaking UI functionality
**Mitigation**:
- Comprehensive manual testing
- Automated UI tests
- Staged deployment
- Security audit

---

## Success Metrics

### Phase 1 Success Criteria
- ✅ Zero bare except statements
- ✅ Analytics service 100% functional
- ✅ JobRepository extracted and tested
- ✅ All tests passing
- ✅ No production incidents

### Phase 2 Success Criteria
- ✅ Database < 300 LOC
- ✅ All repositories < 500 LOC
- ✅ Code duplication < 20%
- ✅ API response time improved 50%+

### Phase 3 Success Criteria
- ✅ Zero hardcoded magic values
- ✅ Zero console.log in production
- ✅ Zero XSS vulnerabilities
- ✅ Connection pooling working

### Overall Success Criteria
- ✅ All critical issues resolved
- ✅ Test coverage > 80%
- ✅ No performance regression
- ✅ Documentation complete
- ✅ Team velocity improved (measured by feature delivery speed)

---

## Maintenance Plan

### After Completion

**Weekly**:
- Review new TODOs/FIXMEs
- Monitor error logs
- Review test coverage

**Monthly**:
- Code quality review
- Performance benchmarking
- Technical debt assessment

**Quarterly**:
- Architecture review
- Refactoring retrospective
- Update roadmap

---

## Appendix A: Estimation Methodology

### Effort Estimates Based On:
1. **Lines of Code**: Complexity from LOC count
2. **Dependencies**: Number of affected files
3. **Testing**: Test coverage requirements
4. **Risk**: Potential for breaking changes

### Assumptions:
- 1 developer day = 6 hours productive coding
- Includes time for testing and documentation
- Includes time for code review
- Excludes meetings and interruptions

---

## Appendix B: Quick Wins

**Want immediate impact? Start here:**

### Week 1 Quick Wins (Days 1-3)
1. Fix bare except blocks (2-3 days)
   - High impact
   - Low risk
   - Immediate stability improvement

2. Extract configuration constants (1 day)
   - Easy change
   - Improves maintainability

3. Add API pagination optimization (1 day)
   - Immediate performance boost
   - User-visible improvement

**Total**: 4-5 days for significant improvements

---

## Document Control

**Version History**:
- v1.0 (2025-11-17): Initial roadmap created

**Review Schedule**:
- Weekly during active development
- After each phase completion
- Monthly for ongoing maintenance

**Approval**:
- [ ] Technical Lead
- [ ] Product Owner
- [ ] Development Team

---

**Next Steps**:
1. Review roadmap with team
2. Assign developers to phases
3. Create sprint backlog from Phase 1
4. Set up progress tracking
5. Begin Week 1 tasks

**Questions? See**:
- [analysis-report.md](./analysis-report.md) - Detailed issue analysis
- [detailed-issues.md](./detailed-issues.md) - File-by-file breakdown
- [progress-tracker.md](./progress-tracker.md) - Track completion
