# Printernizer Phase 1 Test Suite

Comprehensive test suite for the Printernizer 3D print management system, covering backend APIs, frontend components, German business logic, and system performance.

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

#### Complete Test Suite
```bash
python tests/test_runner.py --full-suite
```

#### Backend Tests Only
```bash
python tests/test_runner.py --backend
```

#### Frontend Tests Only
```bash
python tests/test_runner.py --frontend
```

#### Specific Test Categories
```bash
# German business logic tests
python tests/test_runner.py --backend --type german

# Integration tests
python tests/test_runner.py --backend --type integration

# Performance benchmarks
python tests/test_runner.py --performance

# Error handling tests
python tests/test_runner.py --backend --type errors
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
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared fixtures and configuration
├── test_runner.py              # Main test execution script
├── requirements-test.txt       # Python test dependencies
├── backend/                    # Backend Python tests
│   ├── __init__.py
│   ├── test_api_printers.py    # Printer management API tests
│   ├── test_api_jobs.py        # Job management API tests
│   ├── test_api_files.py       # File management API tests
│   ├── test_database.py        # Database operation tests
│   ├── test_websocket.py       # WebSocket communication tests
│   ├── test_integration.py     # Integration workflow tests
│   ├── test_end_to_end.py      # Complete user workflow tests
│   ├── test_german_business.py # German business logic tests
│   ├── test_performance.py     # Performance and load tests
│   └── test_error_handling.py  # Error scenarios and edge cases
└── frontend/                   # Frontend JavaScript tests
    ├── package.json            # Node.js dependencies and scripts
    ├── setup.js                # Jest test environment setup
    ├── api.test.js             # API service layer tests
    ├── dashboard.test.js       # Dashboard component tests
    └── websocket.test.js       # WebSocket integration tests
```

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
2. Coverage thresholds must be met
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