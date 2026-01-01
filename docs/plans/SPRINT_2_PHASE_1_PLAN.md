# Sprint 2 Phase 1 - Core Service Test Coverage
**Date**: 2026-01-01
**Session**: `claude/continue-masterplan-zD4wr`
**Based on**: docs/MASTERPLAN.md Sprint 2 Phase 1
**Previous Sprint**: Sprint 1B - COMPLETE ✅

---

## Executive Summary

Sprint 2 Phase 1 focuses on adding test coverage for **4 critical services** that currently have **0% test coverage**. These services are core infrastructure components that handle WebSocket events, printer monitoring, configuration, and business calculations.

### Objectives

1. ✅ Create comprehensive test suites for 4 critical services
2. ✅ Achieve 80%+ code coverage for each service
3. ✅ Test both happy paths and error conditions
4. ✅ Use proper async testing patterns
5. ✅ Follow existing test patterns from codebase

### Services to Test

| Service | File | Current Coverage | Target | Priority |
|---------|------|------------------|--------|----------|
| EventService | `event_service.py` | 0% | 80%+ | CRITICAL |
| PrinterMonitoringService | `printer_monitoring_service.py` | 0% | 80%+ | CRITICAL |
| ConfigService | `config_service.py` | 0% | 80%+ | CRITICAL |
| BusinessService | `business_service.py` | 0% | 80%+ | CRITICAL |

**Estimated Effort**: 8-10 hours (per masterplan)

---

## Service 1: EventService

**Priority**: CRITICAL
**Impact**: WebSocket event broadcasting for real-time UI updates
**Location**: `src/services/event_service.py`
**Estimated Effort**: 2-3 hours

### Current Implementation Review

Need to review:
- Event emission methods
- Subscription management
- Event delivery mechanisms
- WebSocket integration
- Event history/caching

### Tests to Implement

**File**: `tests/services/test_event_service.py`

```python
import pytest
from src.services.event_service import EventService

class TestEventService:
    """Test EventService event broadcasting"""

    @pytest.fixture
    def event_service(self):
        """Create EventService instance for testing"""
        return EventService()

    async def test_emit_event(self, event_service):
        """Test emitting an event"""
        # Test basic event emission
        pass

    async def test_subscribe_to_event(self, event_service):
        """Test subscribing to events"""
        # Test subscription registration
        pass

    async def test_unsubscribe_from_event(self, event_service):
        """Test unsubscribing from events"""
        # Test subscription removal
        pass

    async def test_event_delivery(self, event_service):
        """Test event delivery to subscribers"""
        # Test that events reach subscribers
        pass

    async def test_concurrent_subscribers(self, event_service):
        """Test multiple concurrent subscribers"""
        # Test multiple subscribers receiving same event
        pass

    async def test_event_history(self, event_service):
        """Test event history tracking"""
        # Test event history/caching if implemented
        pass

    async def test_event_filtering(self, event_service):
        """Test event filtering by type"""
        # Test subscribers only receive relevant events
        pass

    async def test_error_handling(self, event_service):
        """Test error handling in event delivery"""
        # Test that errors in one subscriber don't affect others
        pass
```

### Success Criteria
- ✅ 8+ test cases
- ✅ All critical paths tested
- ✅ Async testing properly implemented
- ✅ All tests passing

---

## Service 2: PrinterMonitoringService

**Priority**: CRITICAL
**Impact**: Real-time printer status polling and updates
**Location**: `src/services/printer_monitoring_service.py`
**Estimated Effort**: 3-4 hours

### Current Implementation Review

Need to review:
- Monitoring start/stop mechanisms
- Status polling logic
- Status change detection
- Monitoring intervals
- Error recovery
- Integration with printer instances

### Tests to Implement

**File**: `tests/services/test_printer_monitoring_service.py`

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.printer_monitoring_service import PrinterMonitoringService

class TestPrinterMonitoringService:
    """Test PrinterMonitoringService monitoring functionality"""

    @pytest.fixture
    def monitoring_service(self, mock_database, mock_event_service):
        """Create PrinterMonitoringService instance"""
        return PrinterMonitoringService(
            database=mock_database,
            event_service=mock_event_service,
            file_service=None,
            connection_service=None
        )

    async def test_start_monitoring(self, monitoring_service):
        """Test starting printer monitoring"""
        # Test monitoring initialization
        pass

    async def test_stop_monitoring(self, monitoring_service):
        """Test stopping printer monitoring"""
        # Test monitoring cleanup
        pass

    async def test_poll_printer_status(self, monitoring_service):
        """Test polling printer status"""
        # Test status polling logic
        pass

    async def test_status_change_detection(self, monitoring_service):
        """Test detection of status changes"""
        # Test status change events
        pass

    async def test_monitoring_interval(self, monitoring_service):
        """Test monitoring interval timing"""
        # Test polling frequency
        pass

    async def test_error_recovery(self, monitoring_service):
        """Test error recovery during monitoring"""
        # Test resilience to errors
        pass

    async def test_concurrent_monitoring(self, monitoring_service):
        """Test monitoring multiple printers"""
        # Test concurrent printer monitoring
        pass

    async def test_monitoring_pause_resume(self, monitoring_service):
        """Test pausing and resuming monitoring"""
        # Test pause/resume functionality
        pass
```

### Success Criteria
- ✅ 8+ test cases
- ✅ Monitoring lifecycle tested
- ✅ Error scenarios covered
- ✅ All tests passing

---

## Service 3: ConfigService

**Priority**: CRITICAL
**Impact**: Configuration loading and validation for entire application
**Location**: `src/services/config_service.py`
**Estimated Effort**: 2-3 hours

### Current Implementation Review

Need to review:
- Configuration loading from files
- Environment variable overrides
- Configuration validation
- Default value handling
- Configuration reload mechanisms
- Printer configuration management

### Tests to Implement

**File**: `tests/services/test_config_service.py`

```python
import pytest
from src.services.config_service import ConfigService

class TestConfigService:
    """Test ConfigService configuration management"""

    @pytest.fixture
    def config_service(self, tmp_path):
        """Create ConfigService instance with temp config"""
        config_file = tmp_path / "config.yaml"
        return ConfigService(config_path=str(config_file))

    def test_load_config(self, config_service):
        """Test loading configuration from file"""
        # Test config file loading
        pass

    def test_validate_config(self, config_service):
        """Test configuration validation"""
        # Test config validation logic
        pass

    def test_invalid_config_raises_error(self, config_service):
        """Test that invalid config raises appropriate error"""
        # Test error handling for bad config
        pass

    def test_default_values(self, config_service):
        """Test default configuration values"""
        # Test defaults when config missing
        pass

    def test_environment_overrides(self, config_service, monkeypatch):
        """Test environment variable overrides"""
        # Test env var precedence
        pass

    def test_config_reload(self, config_service):
        """Test configuration reloading"""
        # Test dynamic config reload
        pass

    def test_get_printer_config(self, config_service):
        """Test retrieving printer configuration"""
        # Test printer-specific config
        pass

    def test_add_printer_config(self, config_service):
        """Test adding printer configuration"""
        # Test config modification
        pass

    def test_remove_printer_config(self, config_service):
        """Test removing printer configuration"""
        # Test config removal
        pass
```

### Success Criteria
- ✅ 9+ test cases
- ✅ Config loading tested
- ✅ Validation tested
- ✅ All tests passing

---

## Service 4: BusinessService

**Priority**: CRITICAL
**Impact**: VAT calculations, pricing, financial accuracy (⚠️ BUSINESS CRITICAL)
**Location**: `src/services/business_service.py`
**Estimated Effort**: 2-3 hours

### Current Implementation Review

Need to review:
- VAT calculation methods
- Material cost calculations
- Power cost calculations
- Labor cost calculations
- Business report generation
- EUR formatting
- German business requirements

### Tests to Implement

**File**: `tests/services/test_business_service.py`

```python
import pytest
from decimal import Decimal
from src.services.business_service import BusinessService

class TestBusinessService:
    """Test BusinessService financial calculations"""

    @pytest.fixture
    def business_service(self, mock_database):
        """Create BusinessService instance"""
        return BusinessService(database=mock_database)

    def test_calculate_vat(self, business_service):
        """Test VAT calculation (German 19%)"""
        # Test VAT calculation accuracy
        subtotal = Decimal("100.00")
        vat = business_service.calculate_vat(subtotal, rate=0.19)
        assert vat == Decimal("19.00")

    def test_calculate_material_cost(self, business_service):
        """Test material cost calculation"""
        # Test material cost based on weight
        pass

    def test_calculate_power_cost(self, business_service):
        """Test power consumption cost"""
        # Test electricity cost calculation
        pass

    def test_calculate_labor_cost(self, business_service):
        """Test labor cost calculation"""
        # Test hourly labor costs
        pass

    async def test_generate_business_report(self, business_service):
        """Test business report generation"""
        # Test report generation
        pass

    async def test_export_accounting_data(self, business_service):
        """Test accounting data export"""
        # Test export functionality
        pass

    def test_eur_formatting(self, business_service):
        """Test EUR currency formatting"""
        # Test German currency format (1.234,56 €)
        pass

    def test_calculate_total_job_cost(self, business_service):
        """Test total job cost calculation"""
        # Test: material + power + labor + VAT
        pass

    def test_profit_margin_calculation(self, business_service):
        """Test profit margin calculation"""
        # Test profit margin logic
        pass

    def test_rounding_precision(self, business_service):
        """Test financial rounding (2 decimal places)"""
        # Test Decimal precision
        pass
```

### Success Criteria
- ✅ 10+ test cases
- ✅ Financial accuracy verified
- ✅ VAT calculations correct
- ✅ German business rules tested
- ✅ All tests passing

---

## Implementation Strategy

### Phase 1A: Investigation (1 hour)
1. Read each service implementation thoroughly
2. Understand dependencies and initialization
3. Identify critical methods to test
4. Note any complex logic or edge cases

### Phase 1B: Test Infrastructure (1 hour)
1. Create test files with proper structure
2. Set up fixtures for service initialization
3. Create mock dependencies (database, event service, etc.)
4. Verify test discovery works

### Phase 1C: Implementation (4-6 hours)
Implement tests service by service in priority order:

**Order**:
1. **ConfigService** (simplest, no async) - 2 hours
2. **BusinessService** (calculations, no async) - 2 hours
3. **EventService** (async, moderate complexity) - 2 hours
4. **PrinterMonitoringService** (async, complex) - 3 hours

### Phase 1D: Verification (1-2 hours)
1. Run all new tests
2. Check code coverage
3. Fix any failing tests
4. Add missing edge cases
5. Document any findings

---

## Testing Best Practices

### Async Testing
```python
import pytest

@pytest.mark.asyncio
async def test_async_method(service):
    result = await service.async_method()
    assert result is not None
```

### Mocking Dependencies
```python
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_database():
    db = MagicMock()
    db.connection = AsyncMock()
    return db
```

### Testing Error Conditions
```python
async def test_error_handling(service):
    with pytest.raises(ValueError, match="Expected error"):
        await service.method_that_should_fail()
```

### Decimal Precision for Financial Tests
```python
from decimal import Decimal

def test_financial_calculation():
    # Always use Decimal for money
    cost = Decimal("19.99")
    vat = Decimal("3.80")
    assert cost + vat == Decimal("23.79")
```

---

## Success Metrics

### Coverage Goals

| Service | Target Coverage | Minimum Tests |
|---------|----------------|---------------|
| EventService | 80%+ | 8 |
| PrinterMonitoringService | 80%+ | 8 |
| ConfigService | 80%+ | 9 |
| BusinessService | 80%+ | 10 |
| **Total** | **80%+** | **35+** |

### Quality Gates
- ✅ All tests pass
- ✅ No flaky tests
- ✅ Proper async handling
- ✅ Mocks used appropriately
- ✅ Error conditions tested
- ✅ Code coverage measured

---

## Risk Assessment

### Low Risk ✅
- ConfigService - Simple sync operations
- BusinessService - Stateless calculations

### Medium Risk ⚠️
- EventService - Async operations, WebSocket integration
- PrinterMonitoringService - Background tasks, timing-sensitive

### Mitigation Strategies
1. **Async Testing**: Use pytest-asyncio properly
2. **Timing Issues**: Use mock time or increase tolerances
3. **Complex Dependencies**: Create comprehensive mocks
4. **Flaky Tests**: Add retries for network-dependent tests

---

## Deliverables

### Test Files (4 new files)
- `tests/services/test_event_service.py`
- `tests/services/test_printer_monitoring_service.py`
- `tests/services/test_config_service.py`
- `tests/services/test_business_service.py`

### Documentation
- Sprint 2 Phase 1 Final Report
- Coverage report
- Any discovered bugs or improvements

---

## Timeline Estimate

| Task | Estimated Time |
|------|---------------|
| Investigation | 1 hour |
| Test Infrastructure | 1 hour |
| ConfigService Tests | 2 hours |
| BusinessService Tests | 2 hours |
| EventService Tests | 2 hours |
| PrinterMonitoringService Tests | 3 hours |
| Verification & Fixes | 1-2 hours |
| **Total** | **12-13 hours** |

**Note**: Masterplan estimated 8-10 hours, but after Sprint 1's pattern of underestimation, being conservative with 12-13 hours.

---

## Next Steps After Phase 1

Upon completion, proceed to:
- **Sprint 2 Phase 2**: Feature Services (6-8 hours)
  - FileWatcherService
  - FileUploadService
  - CameraSnapshotService
  - SearchService

**OR**

- **Sprint 3**: User-Facing Polish (9-12 hours)
  - Frontend improvements
  - Notification fixes
  - UI enhancements

---

**Status**: Ready to execute
**Next Action**: Begin Phase 1A (Investigation) - Read service implementations
**Branch**: `claude/continue-masterplan-zD4wr`
