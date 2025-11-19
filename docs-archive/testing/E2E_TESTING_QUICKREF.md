# Printernizer E2E Testing Quick Reference

## Quick Start

1. **Install dependencies:**
   ```powershell
   pip install -r requirements-test.txt
   playwright install
   ```

2. **Start server:**
   ```powershell
   .\run.bat
   ```

3. **Run tests:**
   ```powershell
   pytest tests/e2e/
   ```

## Common Commands

```powershell
# Run all E2E tests
pytest tests/e2e/

# Run specific test file
pytest tests/e2e/test_dashboard.py

# Run with visible browser (headed mode)
$env:PLAYWRIGHT_HEADLESS="false"; pytest tests/e2e/

# Run with slow motion for debugging
$env:PLAYWRIGHT_SLOW_MO="1000"; pytest tests/e2e/

# Run tests with specific marker
pytest -m "e2e and not slow"
pytest -m "german"

# Run on specific browser
pytest tests/e2e/ --browser chromium
pytest tests/e2e/ --browser firefox

# Run with custom base URL
pytest tests/e2e/ --base-url http://localhost:9000

# Run with coverage
pytest tests/e2e/ --cov=frontend

# Run and save HTML report
pytest tests/e2e/ --html=test-reports/playwright/report.html

# Interactive script
.\run-e2e-tests.ps1
```

## Test Structure

```
tests/e2e/
├── conftest.py              # Fixtures and helpers
├── pages/                   # Page Object Models
│   ├── dashboard_page.py
│   ├── printers_page.py
│   ├── jobs_page.py
│   └── materials_page.py
├── test_dashboard.py        # Dashboard tests
├── test_printers.py         # Printer management tests
├── test_jobs.py             # Job tests
├── test_materials.py        # Materials tests
└── test_integration.py      # API/WebSocket tests
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PLAYWRIGHT_BASE_URL` | `http://localhost:8000` | Base URL for tests |
| `PLAYWRIGHT_HEADLESS` | `true` | Run in headless mode |
| `PLAYWRIGHT_SLOW_MO` | `0` | Slow down by N milliseconds |

## Test Markers

- `@pytest.mark.e2e` - E2E tests
- `@pytest.mark.playwright` - Playwright tests
- `@pytest.mark.network` - Requires backend
- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.german` - German compliance
- `@pytest.mark.websocket` - WebSocket tests
- `@pytest.mark.performance` - Performance tests

## Debugging

### View test in browser
```powershell
$env:PLAYWRIGHT_HEADLESS="false"; pytest tests/e2e/test_dashboard.py::test_dashboard_loads
```

### Take screenshots on failure (default)
Screenshots saved to: `test-reports/playwright/screenshots/`

### View trace
```powershell
playwright show-trace test-reports/playwright/traces/trace.zip
```

### Run with verbose output
```powershell
pytest tests/e2e/ -vv -s
```

## Writing Tests

### Basic test template
```python
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.pages import DashboardPage

@pytest.mark.e2e
@pytest.mark.playwright
def test_example(app_page: Page, base_url: str):
    """Test description"""
    page_obj = DashboardPage(app_page)
    page_obj.navigate(base_url)
    
    # Your test code here
    assert page_obj.is_loaded()
```

### Using page objects
```python
from tests.e2e.pages import PrintersPage

def test_add_printer(app_page: Page, base_url: str):
    printers = PrintersPage(app_page)
    printers.navigate(base_url)
    printers.add_printer("Test Printer", "192.168.1.100")
    printers.expect_printer_in_list("Test Printer")
```

### Assertions
```python
# Playwright expect assertions
expect(page.locator(".element")).to_be_visible()
expect(page).to_have_title("Printernizer")
expect(element).to_have_text("Expected text")

# Python assertions
assert page.is_loaded()
assert len(items) > 0
```

## Troubleshooting

### "Playwright not installed"
```powershell
playwright install
```

### "Server not running"
```powershell
.\run.bat
```

### Port conflict
```powershell
pytest tests/e2e/ --base-url http://localhost:9000
```

### Timeouts
Increase timeout in test:
```python
page.wait_for_selector(".element", timeout=10000)
```

### Browser not closing
Kill manually:
```powershell
Stop-Process -Name "chrome", "firefox", "webkit" -ErrorAction SilentlyContinue
```

## CI/CD

For continuous integration:
```yaml
- name: Install dependencies
  run: |
    pip install -r requirements-test.txt
    playwright install --with-deps chromium

- name: Run E2E tests
  run: |
    pytest tests/e2e/ --browser chromium
  env:
    PLAYWRIGHT_HEADLESS: true
    CI: true
```

## Resources

- [Full Documentation](tests/e2e/README.md)
- [Playwright Docs](https://playwright.dev/python/)
- [pytest-playwright](https://github.com/microsoft/playwright-pytest)
