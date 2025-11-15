# Testing Documentation

This directory contains all testing-related documentation for Printernizer.

## 📋 Quick Start

1. **Setup:** See [Playwright Setup](PLAYWRIGHT_SETUP_COMPLETE.md)
2. **Run Tests:** Check [Testing Guide](TESTING_GUIDE.md)
3. **Quick Reference:** Use [E2E Testing Quick Reference](E2E_TESTING_QUICKREF.md)

## 📚 Documentation

### Core Testing Guides

- **[Testing Guide](TESTING_GUIDE.md)** - Complete guide to running all tests
- **[E2E Testing Quick Reference](E2E_TESTING_QUICKREF.md)** - Quick commands and tips
- **[Coverage Report Guide](COVERAGE_REPORT_GUIDE.md)** - Understanding coverage reports

### Architecture & Setup

- **[E2E Architecture](E2E_ARCHITECTURE.md)** - End-to-end test architecture
- **[Playwright Setup](PLAYWRIGHT_SETUP_COMPLETE.md)** - Playwright configuration and setup

### Feature-Specific Testing

- **[Automated Job Creation Testing](automated-job-creation-testing.md)** - Testing automated job creation

### Analysis & Reports

- **[E2E Test Analysis](E2E_TEST_ANALYSIS.md)** - Test suite analysis
- **[E2E Test Failures Analysis](E2E_TEST_FAILURES_ANALYSIS.md)** - Common failures and solutions

## 🧪 Test Types

### Unit Tests
Location: `/tests/unit/`
- Fast, isolated tests
- Test individual functions and classes
- Mock external dependencies

### Integration Tests
Location: `/tests/integration/`
- Test service interactions
- Database integration
- API endpoint testing

### End-to-End Tests
Location: `/tests/e2e/`
- Full workflow testing
- Browser-based UI tests
- Real printer simulations

## 🚀 Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests
pytest tests/e2e/

# With coverage
pytest --cov=src tests/
```

## 📊 Coverage

Generate coverage reports:
```bash
pytest --cov=src --cov-report=html tests/
```

View reports in `htmlcov/index.html`

## 🔗 Related Documentation

- [Test Scripts](../../scripts/testing/) - Test utility scripts
- [Test Reports](../reports/) - Detailed test analysis reports
- [Development Guide](../development/) - Development workflow

---

**See also:** [Main Documentation Index](../README.md)
