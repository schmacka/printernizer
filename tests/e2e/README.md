# Playwright E2E Testing for Printernizer

This directory contains End-to-End (E2E) tests for the Printernizer frontend using Playwright.

## Overview

Playwright provides reliable end-to-end testing by automating real browser interactions. These tests verify that the Printernizer web interface works correctly from a user's perspective.

## Setup

### 1. Install Dependencies

First, install the Python test dependencies:

```powershell
pip install -r requirements-test.txt
```

### 2. Install Playwright Browsers

Playwright requires browser binaries to be installed:

```powershell
playwright install
```

This will download Chromium, Firefox, and WebKit browsers. To install only specific browsers:

```powershell
playwright install chromium
playwright install firefox
playwright install webkit
```

### 3. Start the Printernizer Server

E2E tests require the Printernizer backend to be running:

```powershell
.\run.bat
```

The server should be running at `http://localhost:8000` (default).

## Running Tests

### Run All E2E Tests

```powershell
pytest tests/e2e/
```

### Run Specific Test File

```powershell
pytest tests/e2e/test_dashboard.py
```

### Run Tests in Headed Mode (See Browser)

```powershell
$env:PLAYWRIGHT_HEADLESS="false"; pytest tests/e2e/
```

### Run Tests with Slow Motion (Debugging)

```powershell
$env:PLAYWRIGHT_SLOW_MO="1000"; pytest tests/e2e/
```

### Run Tests on Specific Browser

```powershell
pytest tests/e2e/ --browser chromium
pytest tests/e2e/ --browser firefox
pytest tests/e2e/ --browser webkit
```

### Run with Custom Base URL

```powershell
pytest tests/e2e/ --base-url http://localhost:9000
```

## Test Structure

### Page Objects

Tests use the Page Object Model (POM) pattern for maintainability:

- `pages/dashboard_page.py` - Dashboard page interactions
- `pages/printers_page.py` - Printers management page
- `pages/jobs_page.py` - Jobs page interactions
- `pages/materials_page.py` - Materials/inventory page

### Test Files

- `test_dashboard.py` - Dashboard functionality tests
- `test_printers.py` - Printer management tests
- `test_jobs.py` - Job creation and management tests
- `test_materials.py` - Material inventory tests

### Fixtures

Common fixtures are defined in `conftest.py`:

- `app_page` - Provides a fresh browser page for each test
- `authenticated_page` - Pre-authenticated page (currently same as app_page)
- `helpers` - Helper functions for common test operations

## Test Markers

Tests are organized with pytest markers:

- `@pytest.mark.e2e` - All E2E tests
- `@pytest.mark.playwright` - Playwright-specific tests
- `@pytest.mark.network` - Tests requiring backend API
- `@pytest.mark.slow` - Tests that take longer to execute
- `@pytest.mark.german` - German compliance features (VAT, etc.)

Run tests by marker:

```powershell
pytest -m "e2e and not slow"
pytest -m "german"
pytest -m "not network"  # Skip tests requiring backend
```

## Configuration

### Environment Variables

- `PLAYWRIGHT_BASE_URL` - Base URL for the application (default: `http://localhost:8000`)
- `PLAYWRIGHT_HEADLESS` - Run in headless mode (default: `true`)
- `PLAYWRIGHT_SLOW_MO` - Slow down operations by N milliseconds (default: `0`)

### Playwright Configuration

Edit `playwright.config.py` to customize:

- Browser settings
- Timeout values
- Screenshot/video recording
- Viewport size

## Test Artifacts

Test artifacts are saved to `test-reports/playwright/`:

- **Screenshots** - Captured on test failure
- **Videos** - Recorded for failed tests
- **Traces** - Full test execution traces for debugging

### Viewing Traces

```powershell
playwright show-trace test-reports/playwright/traces/trace.zip
```

## Writing New Tests

### Example Test

```python
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.pages import DashboardPage

@pytest.mark.e2e
@pytest.mark.playwright
def test_example(app_page: Page, base_url: str):
    """Example test description"""
    dashboard = DashboardPage(app_page)
    dashboard.navigate(base_url)
    
    # Verify page loaded
    assert dashboard.is_loaded()
    
    # Interact with page
    dashboard.click_add_printer()
    
    # Assert expectations
    expect(app_page.locator(".modal")).to_be_visible()
```

### Best Practices

1. **Use Page Objects** - Keep selectors and interactions in page object classes
2. **Wait for Elements** - Use `wait_for_selector()` or `expect()` instead of `time.sleep()`
3. **Use Descriptive Assertions** - Use Playwright's `expect()` for clear error messages
4. **Mock When Possible** - Use API mocking for tests that don't need full backend
5. **Mark Appropriately** - Add markers (`@pytest.mark.network`, etc.) for test filtering

## Troubleshooting

### Browser Installation Issues

If playwright browsers aren't found:

```powershell
python -m playwright install
```

### Port Already in Use

If the test server port is in use, set a different port:

```powershell
pytest tests/e2e/ --base-url http://localhost:9000
```

### Timeouts

Increase timeout in `playwright.config.py` or individual tests:

```python
page.wait_for_selector(".element", timeout=10000)  # 10 seconds
```

### Debug Mode

Run with verbose output and screenshots:

```powershell
pytest tests/e2e/ -vv --screenshot on
```

## CI/CD Integration

For CI environments, set:

```bash
export PLAYWRIGHT_HEADLESS=true
export CI=true
pytest tests/e2e/ --video retain-on-failure
```

## Additional Resources

- [Playwright Python Documentation](https://playwright.dev/python/)
- [pytest-playwright Plugin](https://github.com/microsoft/playwright-pytest)
- [Best Practices](https://playwright.dev/python/docs/best-practices)
