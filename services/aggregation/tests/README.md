# Aggregation Service Tests

Comprehensive test suite for the Printernizer Usage Statistics Aggregation Service.

## Test Structure

```
tests/
├── __init__.py                 # Package initialization
├── conftest.py                 # Shared fixtures and test configuration
├── test_api.py                 # API endpoint tests (90+ tests)
├── test_auth.py                # Authentication tests (40+ tests)
├── test_database.py            # Database operations tests (50+ tests)
├── test_models.py              # Pydantic model validation tests (40+ tests)
├── test_rate_limiting.py       # Rate limiting tests (30+ tests)
└── README.md                   # This file
```

## Running Tests

### Install Dependencies

```bash
cd services/aggregation
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Files

```bash
# API tests only
pytest tests/test_api.py

# Authentication tests only
pytest tests/test_auth.py

# Database tests only
pytest tests/test_database.py

# Model validation tests only
pytest tests/test_models.py

# Rate limiting tests only
pytest tests/test_rate_limiting.py
```

### Run Specific Test Classes

```bash
# Run only health endpoint tests
pytest tests/test_api.py::TestHealthEndpoints

# Run only rate limit basics
pytest tests/test_rate_limiting.py::TestRateLimitBasics
```

### Run Specific Tests

```bash
# Run a single test
pytest tests/test_api.py::TestHealthEndpoints::test_root_endpoint
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=services/aggregation --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Output Capture Disabled

```bash
pytest -s
```

## Test Categories

### 1. API Endpoint Tests (`test_api.py`)

Tests all REST API endpoints:

- **Health Endpoints**: `/`, `/health`
- **Submit Endpoint**: `POST /submit`
- **Delete Endpoint**: `DELETE /installation/{id}`
- **Stats Summary**: `GET /stats/summary`
- **CORS Headers**: Cross-origin request handling
- **Error Handling**: Invalid requests, 404s, 405s

**Coverage**: 90+ tests covering all endpoints and edge cases

### 2. Authentication Tests (`test_auth.py`)

Tests API key authentication:

- **API Key Validation**: Valid, invalid, missing keys
- **Endpoint Protection**: All protected endpoints require auth
- **Error Responses**: Proper error formats and messages
- **Security**: No key leakage, bypass attempts fail
- **Integration**: Auth with rate limiting and errors

**Coverage**: 40+ tests ensuring robust security

### 3. Database Tests (`test_database.py`)

Tests database operations:

- **Schema**: Table structure, columns, indexes
- **CRUD Operations**: Create, read, update, delete
- **Queries**: Filtering, aggregation, sorting
- **Data Integrity**: Constraints, defaults, cascades
- **Performance**: Index usage, query efficiency
- **JSON Fields**: Complex data storage

**Coverage**: 50+ tests for database reliability

### 4. Model Validation Tests (`test_models.py`)

Tests Pydantic model validation:

- **Request Models**: AggregatedStatsModel, sub-models
- **Response Models**: SubmissionResponse, DeleteResponse
- **Validation**: Field types, required fields, defaults
- **Serialization**: JSON round-trips, edge cases
- **Edge Cases**: Large numbers, special characters, unicode

**Coverage**: 40+ tests ensuring data validity

### 5. Rate Limiting Tests (`test_rate_limiting.py`)

Tests rate limiting enforcement:

- **Basic Limiting**: 10 requests per hour per installation
- **Window Resets**: Time-based window expiration
- **Per-Installation**: Independent limits for each installation
- **Error Messages**: Clear rate limit feedback
- **Database**: Rate limit record management
- **Edge Cases**: Concurrent requests, old windows

**Coverage**: 30+ tests preventing abuse

## Test Fixtures

Shared fixtures are defined in `conftest.py`:

### Database Fixtures

- `db_engine`: In-memory SQLite database engine
- `db_session`: Database session for tests
- `client`: FastAPI test client with database override

### Authentication Fixtures

- `auth_headers`: Valid API key headers
- `invalid_auth_headers`: Invalid API key headers

### Data Fixtures

- `sample_installation_id`: Sample UUID
- `sample_stats_payload`: Complete valid statistics payload
- `multiple_stats_payloads`: Multiple payloads for bulk tests

### Factory Fixtures

- `create_submission()`: Create test submissions
- `create_rate_limit()`: Create rate limit records
- `clear_database()`: Clean up database between tests

## Writing New Tests

### Test Class Structure

```python
class TestFeatureName:
    """Tests for feature description."""

    def test_basic_behavior(self, client, auth_headers):
        """Test basic feature behavior."""
        response = client.get("/endpoint", headers=auth_headers)
        assert response.status_code == 200

    def test_edge_case(self, client, auth_headers):
        """Test edge case handling."""
        # Test implementation
        pass
```

### Using Fixtures

```python
def test_with_database(self, db_session, create_submission):
    """Test using database fixtures."""
    # Create test data
    submission = create_submission(installation_id="test-id")

    # Perform test
    assert submission.installation_id == "test-id"
```

### Testing API Endpoints

```python
def test_endpoint(self, client, auth_headers, sample_stats_payload):
    """Test API endpoint."""
    response = client.post(
        "/submit",
        json=sample_stats_payload,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
```

## Test Coverage Goals

- **Overall Coverage**: 90%+
- **Critical Paths**: 100% (auth, rate limiting, data storage)
- **Edge Cases**: Comprehensive coverage
- **Error Handling**: All error paths tested

## Current Coverage

Run `pytest --cov` to see current coverage:

```bash
pytest --cov=services/aggregation --cov-report=term-missing
```

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    cd services/aggregation
    pip install -r requirements.txt
    pytest --cov --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Troubleshooting

### Import Errors

If you get import errors, ensure you're in the right directory:

```bash
cd services/aggregation
export PYTHONPATH="${PYTHONPATH}:$(pwd)/.."
pytest
```

### Database Errors

Tests use in-memory SQLite. If you encounter database errors:

1. Check that `DATABASE_URL` environment variable is not set
2. Verify SQLAlchemy is installed: `pip install sqlalchemy`
3. Check conftest.py is properly setting up test database

### Async Errors

If async tests fail:

1. Ensure `pytest-asyncio` is installed
2. Check `asyncio_mode = auto` in pytest.ini
3. Use `async def` for async test functions

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Aim for 90%+ coverage
3. Test both happy paths and edge cases
4. Include error handling tests
5. Update this README if needed

## Test Statistics

- **Total Tests**: 250+
- **Test Files**: 5
- **Average Runtime**: ~5 seconds
- **Coverage**: 90%+ (target)

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
- [Pydantic Validation](https://docs.pydantic.dev/latest/concepts/validation/)
