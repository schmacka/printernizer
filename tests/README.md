# Printernizer Phase 1 Test Suite

Comprehensive test suite for the Printernizer 3D print management system, covering backend APIs, frontend components, German business logic, and system performance.

> **📝 Recent Update (Nov 2025):** Test organization improved!
> - ✅ Service tests moved to `tests/services/`
> - ✅ Integration tests moved to `tests/integration/`  
> - ✅ Redundant tests removed (test_essential_config.py, test_working_core.py, test_essential_integration.py)
> - See [Test Organization Analysis](../docs/TEST_ORGANIZATION_ANALYSIS.md) for details.

## 🎯 Test Coverage Overview

### Backend Tests (Python/pytest)
- **API Endpoints**: Complete CRUD operations for printers, jobs, and files
- **Integration Tests**: End-to-end workflows and database operations
- **German Business Logic**: EUR currency, VAT calculations, timezone handling
- **Performance Tests**: Load testing, concurrent operations, memory optimization
- **Error Handling**: Network failures, invalid data, security edge cases

### Frontend Tests (JavaScript/Jest)
- **Component Tests**: Dashboard, printer management, job monitoring
- **API Integration**: HTTP client, error handling, data validation
- **WebSocket Tests**: Real-time updates, connection management, high-frequency messaging
- **User Workflows**: Complete end-to-end user interactions

## 🚀 Quick Start

### Prerequisites

#### Python Dependencies
```bash
pip install -r requirements-test.txt
```

#### Node.js Dependencies (for frontend tests)
```bash
cd tests/frontend
npm install
```

### Running Tests

#### Complete Test Suite (Matches CI/CD)
```bash
# Run all backend/service/integration Python tests (same as CI/CD)
python -m pytest tests/ --ignore=tests/e2e --ignore=tests/frontend \
  --cov=src --cov-report=html --cov-report=term-missing -v

# Or run specific directories
python -m pytest tests/backend/ tests/services/ tests/integration/ -v
```

#### Using Test Runner (Legacy)
```bash
# Note: test_runner.py only runs tests/backend/ - use pytest directly for full coverage
python tests/test_runner.py --full-suite
```

#### Backend Tests Only
```bash
python -m pytest tests/backend/ -v
```

#### Service Layer Tests
```bash
python -m pytest tests/services/ -v
```

#### Integration Tests
```bash
python -m pytest tests/integration/ -v
```

#### Frontend Tests Only
```bash
cd tests/frontend
npm test
```

#### Specific Test Categories
```bash
# German business logic tests
python -m pytest tests/backend/test_german_business.py -v

# Performance benchmarks
python -m pytest tests/backend/test_performance.py -v

# Error handling tests
python -m pytest tests/backend/test_error_handling.py -v

# Auto-job creation logic
python -m pytest tests/services/test_auto_job_creation.py -v
```

## 📊 Coverage Requirements

### Minimum Coverage Thresholds
- **Backend API**: 90%+ code coverage
- **German Business Logic**: 100% coverage (critical for compliance)
- **Frontend Components**: 85%+ coverage
- **Integration Workflows**: Complete user journey testing
- **Error Scenarios**: 80%+ edge case coverage

### Coverage Reports
```bash
# Generate coverage reports
python tests/test_runner.py --coverage-only

# View HTML reports
open coverage/backend/index.html
open coverage/frontend/index.html
```

## 🇩🇪 German Business Logic Testing

### Currency and VAT Testing
- EUR formatting with German locale (1.234,56 EUR)
- 19% VAT calculation accuracy
- VAT-exempt transaction handling
- Business vs. private job distinctions

### Compliance Testing
- **HGB**: German Commercial Code compliance
- **GoBD**: German Digital Records Act requirements
- **ELSTER**: Electronic tax filing format validation
- **Invoice Numbering**: Consecutive numbering requirements

### Timezone and Localization
- Europe/Berlin timezone handling
- Daylight saving time transitions
- German date formatting (DD.MM.YYYY)
- Business hours validation

## ⚡ Performance Benchmarks

### Database Performance Targets
- Large dataset queries (1000+ jobs): < 1 second
- Concurrent operations: 95%+ success rate
- Complex reporting queries: < 2 seconds

### API Performance Targets
- Concurrent requests: 50+ requests/second
- Standard response times: < 200ms
- Large payloads: < 500ms generation

### WebSocket Performance Targets
- High-frequency updates: 100+ messages/second
- Connection latency: < 100ms
- Reconnection recovery: < 5 seconds

## 🏗️ Test Architecture

### Directory Structure
```
tests/
├── __init__.py                          # Test package initialization
├── conftest.py                          # Shared fixtures and configuration
├── test_runner.py                       # Legacy test execution script
├── requirements-test.txt                # Python test dependencies
├── backend/                             # Backend API tests (259 tests)
│   ├── __init__.py
│   ├── test_api_printers.py             # Printer management API (26 tests)
│   ├── test_api_jobs.py                 # Job management API (29 tests)
│   ├── test_api_files.py                # File management API (24 tests)
│   ├── test_api_health.py               # Health check endpoints (9 tests)
│   ├── test_database.py                 # Database operations (18 tests)
│   ├── test_websocket.py                # WebSocket communication (21 tests)
│   ├── test_integration.py              # Integration workflow (16 tests)
│   ├── test_end_to_end.py               # Complete workflows (9 tests)
│   ├── test_german_business.py          # German compliance (21 tests)
│   ├── test_performance.py              # Performance benchmarks (11 tests)
│   ├── test_error_handling.py           # Error scenarios (28 tests)
│   ├── test_auto_job_performance.py     # Auto-job performance (13 tests)
│   ├── test_job_null_fix.py             # Job null handling (5 tests)
│   └── test_library_service.py          # Library/file storage (29 tests)
├── services/                            # Service layer tests (~130 tests)
│   ├── __init__.py
│   ├── test_auto_job_creation.py        # Auto-job logic (28 tests)
│   ├── test_file_download_service.py    # File downloads (17 tests)
│   ├── test_printer_connection_service.py # Connections (18 tests)
│   ├── test_ideas_service.py            # Ideas/trending service (27 tests)
│   ├── test_url_parser_service.py       # URL parsing (21 tests)
│   └── test_gcode_analyzer.py           # G-code analysis (23 tests)
├── integration/                         # Integration tests (~20 tests)
│   ├── __init__.py
│   ├── test_auto_job_integration.py     # Auto-job workflows (14 tests)
│   ├── test_printer_interface_conformance.py # Interface compliance (3 tests)
│   └── test_sync_consistency.py         # Code sync validation (8 tests)
├── test_essential_models.py             # Data models (16 tests) - Lightweight model validation
├── test_essential_printer_api.py        # Printer API validation (11 tests) - Milestone 1.2
├── test_essential_printer_drivers.py    # Printer drivers (11 tests) - Milestone 1.2  
├── test_infrastructure.py               # Test fixtures validation (5 tests)
├── test_runner.py                       # Legacy test execution script (utility)
└── frontend/                            # Frontend tests (JavaScript/Jest)
    ├── package.json                     # Node.js dependencies
    ├── setup.js                         # Jest environment setup
    ├── api.test.js                      # API service layer
    ├── dashboard.test.js                # Dashboard components
    ├── websocket.test.js                # WebSocket integration
    ├── test_essential_forms.js          # Form validation
    └── test_essential_printer_monitoring.js # Printer monitoring UI
```

**Total: 419 tests** (397 Python + ~22 JavaScript)

### Test Fixtures and Mocks

#### Database Fixtures (`conftest.py`)
- Temporary SQLite databases for testing
- Sample printer data (Bambu Lab A1, Prusa Core One)
- Job data with German business fields
- File management test scenarios

#### Mock Services
- **Bambu Lab MQTT API**: Simulated printer status and file operations
- **Prusa PrusaLink API**: HTTP API simulation with realistic responses
- **WebSocket Connections**: Mock real-time communication
- **File System Operations**: Safe file handling for tests

## 🔧 Test Configuration

### Environment Variables
```bash
# Test database configuration
TEST_DATABASE_URL=sqlite:///test_printernizer.db

# API endpoints for testing
TEST_API_BASE_URL=http://localhost:8000/api/v1
TEST_WEBSOCKET_URL=ws://localhost:8000/ws

# German business configuration
TEST_TIMEZONE=Europe/Berlin
TEST_CURRENCY=EUR
TEST_VAT_RATE=0.19
```

### pytest Configuration (`pytest.ini`)
```ini
[tool:pytest]
testpaths = tests/backend
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov-report=term-missing
    --cov-report=html
    --cov-report=json
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    german: German business logic tests
    slow: Slow running tests
```

### Jest Configuration (Frontend)
```json
{
  "testEnvironment": "jsdom",
  "setupFilesAfterEnv": ["<rootDir>/setup.js"],
  "collectCoverageFrom": [
    "../../frontend/js/**/*.js",
    "!../../frontend/js/config.js"
  ],
  "coverageThreshold": {
    "global": {
      "branches": 80,
      "functions": 85,
      "lines": 85,
      "statements": 85
    }
  }
}
```

## 🐛 Debugging Tests

### Running Individual Tests
```bash
# Run specific test file
python -m pytest tests/backend/test_german_business.py -v

# Run specific test method
python -m pytest tests/backend/test_api_printers.py::TestPrinterAPI::test_get_printers_with_data -v

# Run with debugger
python -m pytest tests/backend/test_integration.py --pdb
```

### Frontend Test Debugging
```bash
cd tests/frontend

# Run specific test file
npm test -- dashboard.test.js

# Run in watch mode
npm test -- --watch

# Debug mode
npm run test:debug
```

### Common Issues and Solutions

#### Database Connection Issues
```bash
# Reset test database
rm -f test_printernizer.db
python -c "from tests.conftest import temp_database; temp_database()"
```

#### Mock Service Issues
```bash
# Verify mock printer APIs
python -c "from tests.conftest import mock_bambu_api, mock_prusa_api; print('Mocks loaded')"
```

#### Coverage Report Issues
```bash
# Clean and regenerate coverage
rm -rf coverage/
python tests/test_runner.py --coverage-only
```

## 📈 Continuous Integration

### CI/CD Test Coverage

The CI/CD workflow (`.github/workflows/ci-cd.yml`) runs **all 419 tests** organized into three jobs:

#### Backend Test Job (`test-backend`)
Runs **397 Python tests** with coverage:
```bash
python -m pytest tests/backend/ tests/services/ tests/integration/ \
  tests/test_essential_config.py \
  tests/test_essential_integration.py \
  tests/test_essential_models.py \
  tests/test_infrastructure.py \
  tests/test_printer_interface_conformance.py \
  tests/test_sync_consistency.py \
  --cov=src --cov-report=xml --cov-report=html
```

**Coverage Requirements:**
- Minimum: 85% overall code coverage
- Critical modules: 90%+ (printer service, job service)
- German business logic: 100%

**Quality Gates:**
- Pass rate threshold: 45% minimum (baseline)
- Max failures: 20 (fail-fast)
- Test timeout: 300 seconds

#### Frontend Test Job (`test-frontend`)
Runs JavaScript tests with Jest:
```bash
cd tests/frontend
npm run test:coverage -- --ci
```

**Quality Gates:**
- Pass rate threshold: 95% minimum
- Coverage: 85%+ for functions, lines, statements

#### Printer Integration Test Job (`printer-integration-test`)
Runs on non-PR builds only (redundant validation):
- test_essential_printer_drivers.py
- test_essential_printer_api.py
- test_api_printers.py

**Note:** These tests are already included in the main backend test job. This job provides extra validation on pushes to main/develop branches.

For complete CI/CD test documentation, see: [`docs/CI_CD_TEST_COVERAGE.md`](../docs/CI_CD_TEST_COVERAGE.md)

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

### CI Pipeline Requirements
1. All tests must pass (exit code 0)
2. Coverage thresholds must be met (85% overall)
3. German business logic tests are mandatory
4. Performance benchmarks within acceptable limits
5. Security validation tests must pass

### Deployment Gates
- End-to-end workflow tests pass
- German compliance tests verified
- Performance regression checks
- Documentation generation successful

## 🔒 Security Testing

### Input Validation Tests
- SQL injection prevention
- XSS attack prevention
- Path traversal protection
- Input sanitization verification

### API Security Tests
- Authentication validation
- Authorization checks
- Rate limiting verification
- Request validation

## 📋 Test Maintenance

### Regular Maintenance Tasks
- Update test data to match production patterns
- Synchronize mock services with real API changes
- Review and adjust performance baselines
- Update German regulation compliance tests

### Performance Monitoring
- Track test execution time trends
- Monitor coverage percentage changes
- Alert on performance regressions
- German compliance test status monitoring

## 🆘 Support and Troubleshooting

### Common Commands
```bash
# Reset entire test environment
rm -rf test_*.db coverage/ test-reports/
python tests/test_runner.py --full-suite

# Generate test documentation
python tests/test_runner.py --docs-only

# Run only fast tests (skip performance)
python tests/test_runner.py --full-suite --skip-performance
```

### Getting Help
1. Check test logs in `test-reports/` directory
2. Review coverage reports in `coverage/` directory
3. Verify test configuration in `conftest.py`
4. Check German business logic in `test_german_business.py`

### Contributing to Tests
1. Follow existing test patterns and naming conventions
2. Include German business logic validation where applicable
3. Add performance benchmarks for new features
4. Update documentation for new test categories
5. Ensure all tests are deterministic and isolated

---

**Note**: This test suite is specifically designed for the German 3D printing service market and includes comprehensive German business logic testing to ensure regulatory compliance and local business practice adherence.