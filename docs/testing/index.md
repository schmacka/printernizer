# Testing

Comprehensive testing documentation for Printernizer. This section covers all aspects of testing, from unit tests to end-to-end testing strategies.

## Testing Overview

Printernizer maintains high code quality through:

- **Unit Tests** - Individual component testing
- **Integration Tests** - Service and API testing
- **End-to-End Tests** - Full workflow testing
- **Coverage Reporting** - Code coverage tracking

## Quick Start

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_printer_service.py

# Run with detailed output
pytest -v

# Generate HTML coverage report
pytest --cov=src --cov-report=html tests/
```

## Available Documentation

- **[Automated Job Creation Testing](automated-job-creation-testing.md)** - Testing automated job creation workflows
- **[E2E Test Architecture](E2E_ARCHITECTURE.md)** - End-to-end testing architecture and structure
- **[E2E Testing Quick Reference](E2E_TESTING_QUICKREF.md)** - Quick reference for E2E testing
- **[E2E Test Analysis](E2E_TEST_ANALYSIS.md)** - Analysis of E2E test results
- **[Coverage Report Guide](COVERAGE_REPORT_GUIDE.md)** - Generating and understanding coverage reports
- **[Playwright Setup](PLAYWRIGHT_SETUP_COMPLETE.md)** - Playwright setup documentation
- **[Testing Guide](TESTING_GUIDE.md)** - Comprehensive testing guide for auto-download system

## Test Structure

```
tests/
├── unit/                   # Unit tests
│   ├── test_services/     # Service tests
│   ├── test_models/       # Model tests
│   └── test_printers/     # Printer integration tests
├── integration/           # Integration tests
│   ├── test_api/         # API endpoint tests
│   └── test_workflows/   # Full workflow tests
├── e2e/                   # End-to-end tests
│   └── test_scenarios/   # Complete user scenarios
└── conftest.py           # Pytest configuration
```

## Testing Philosophy

### Test Pyramid

```
       /\\
      /E2E\\        Few comprehensive end-to-end tests
     /------\\
    /  INT   \\     More integration tests
   /----------\\
  /    UNIT    \\   Many focused unit tests
 /--------------\\
```

### Best Practices

1. **Write tests first** (TDD where appropriate)
2. **Test behavior, not implementation**
3. **Keep tests independent**
4. **Use descriptive test names**
5. **Mock external dependencies**
6. **Aim for >80% coverage**

## Running Tests

### Basic Commands

```bash
# All tests
pytest

# Specific test file
pytest tests/test_printer_service.py

# Specific test function
pytest tests/test_printer_service.py::test_add_printer

# With coverage
pytest --cov=src tests/

# Generate coverage reports
pytest --cov=src --cov-report=html --cov-report=term tests/
```

### Watch Mode

```bash
# Install pytest-watch
pip install pytest-watch

# Run tests on file changes
ptw tests/
```

## Writing Tests

### Unit Test Example

```python
import pytest
from src.services.printer_service import PrinterService

@pytest.mark.asyncio
async def test_add_printer():
    """Test adding a new printer."""
    service = PrinterService()

    printer_data = {
        "id": "test123",
        "name": "Test Printer",
        "type": "bambu_lab"
    }

    printer = await service.add_printer(printer_data)

    assert printer.id == "test123"
    assert printer.name == "Test Printer"
    assert printer.type == "bambu_lab"
```

### Integration Test Example

```python
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_get_printers_endpoint():
    """Test GET /api/v1/printers endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/printers")

    assert response.status_code == 200
    assert "printers" in response.json()
```

## Test Fixtures

Common fixtures are available in `tests/conftest.py`:

```python
@pytest.fixture
async def test_printer():
    """Provide a test printer instance."""
    return BambuLabPrinter(
        printer_id="test123",
        name="Test Printer",
        ip="192.168.1.100"
    )

@pytest.fixture
async def test_client():
    """Provide a test HTTP client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

## Coverage Goals

| Component | Target Coverage |
|-----------|-----------------|
| Services | >90% |
| Models | >85% |
| API Routes | >80% |
| Utilities | >75% |
| **Overall** | **>80%** |

## Continuous Integration

Tests run automatically on:

- Every push to `development`
- Every pull request
- Before merging to `master`

See `.github/workflows/ci-cd.yml` for CI configuration.

## Debugging Tests

### Enable Logging

```bash
pytest -v --log-cli-level=DEBUG
```

### Run Single Test

```bash
pytest tests/test_file.py::test_function -v
```

### Use Debugger

```python
import pdb; pdb.set_trace()  # Add to test
pytest tests/test_file.py --pdb
```

## Performance Testing

### Load Testing

```bash
# Using locust (if installed)
locust -f tests/performance/locustfile.py
```

### Profiling

```bash
# Profile test execution
pytest --profile tests/
```

## Test Reports

### HTML Coverage Report

```bash
pytest --cov=src --cov-report=html tests/
open htmlcov/index.html
```

### JSON Report

```bash
pytest --json-report --json-report-file=report.json
```

### HTML Test Report

```bash
pytest --html=report.html --self-contained-html
```

## Mocking

### Mock External Services

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_printer_connection():
    with patch('src.printers.bambu_lab.mqtt.Client') as mock_mqtt:
        mock_mqtt.return_value = AsyncMock()
        # Test code here
```

## Test Data

Test data and fixtures are located in `tests/fixtures/`:

```
tests/fixtures/
├── printers/          # Sample printer configurations
├── jobs/              # Sample job data
├── files/             # Sample file metadata
└── responses/         # Mock API responses
```

## Additional Resources

- [E2E Test Architecture](E2E_ARCHITECTURE.md)
- [E2E Testing Quick Reference](E2E_TESTING_QUICKREF.md)
- [Coverage Report Guide](COVERAGE_REPORT_GUIDE.md)
- [pytest Documentation](https://docs.pytest.org/)

## Contributing Tests

When contributing:

1. Add tests for all new features
2. Maintain or improve coverage
3. Follow existing test patterns
4. Update test documentation

See the [CONTRIBUTING.md](https://github.com/schmacka/printernizer/blob/master/CONTRIBUTING.md) guide for more details.
