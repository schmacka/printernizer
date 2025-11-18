# Printernizer E2E Test Architecture

## Project Structure

```
printernizer/
├── playwright.config.py          # Playwright configuration
├── requirements-test.txt         # Test dependencies (includes Playwright)
├── pytest.ini                    # Pytest configuration with E2E markers
├── run-e2e-tests.ps1            # Interactive test runner (PowerShell)
├── setup-e2e-tests.bat          # Setup script (Batch)
├── E2E_TESTING_QUICKREF.md      # Quick reference guide
├── PLAYWRIGHT_SETUP_COMPLETE.md # Setup completion summary
│
└── tests/
    └── e2e/                      # E2E test directory
        ├── __init__.py
        ├── conftest.py           # Fixtures and helpers
        ├── README.md             # Comprehensive documentation
        │
        ├── pages/                # Page Object Models
        │   ├── __init__.py
        │   ├── dashboard_page.py # Dashboard interactions
        │   ├── printers_page.py  # Printer management
        │   ├── jobs_page.py      # Job workflows
        │   └── materials_page.py # Material inventory
        │
        └── tests/                # Test suites
            ├── test_dashboard.py     # Dashboard tests (6 tests)
            ├── test_printers.py      # Printer tests (6 tests)
            ├── test_jobs.py          # Job tests (7 tests)
            ├── test_materials.py     # Material tests (7 tests)
            ├── test_integration.py   # API/WebSocket tests (8 tests)
            └── test_examples.py      # Example tests (8 tests)
```

## Test Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     User Runs Tests                          │
│   pytest tests/e2e/  or  .\run-e2e-tests.ps1               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  pytest-playwright Plugin                    │
│  - Loads configuration from playwright.config.py            │
│  - Sets up browser contexts                                 │
│  - Provides fixtures (page, context, browser)               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Test Execution                            │
│  1. conftest.py provides custom fixtures                    │
│  2. Page objects encapsulate UI interactions                │
│  3. Tests use page objects to interact with frontend        │
│  4. Assertions verify expected behavior                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Browser Automation                         │
│  - Playwright launches browser (Chromium/Firefox/WebKit)    │
│  - Navigates to pages                                       │
│  - Interacts with elements (click, type, etc.)              │
│  - Captures screenshots/videos on failure                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Test Results                              │
│  - Pass/Fail status                                         │
│  - Screenshots in test-reports/playwright/screenshots/      │
│  - Videos in test-reports/playwright/videos/                │
│  - Traces in test-reports/playwright/traces/                │
└─────────────────────────────────────────────────────────────┘
```

## Page Object Model Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                        Test File                             │
│  test_dashboard.py                                          │
│  ┌────────────────────────────────────────────────┐        │
│  │ def test_dashboard_loads(app_page):            │        │
│  │     dashboard = DashboardPage(app_page)        │        │
│  │     dashboard.navigate(base_url)               │────────┼──┐
│  │     assert dashboard.is_loaded()               │        │  │
│  └────────────────────────────────────────────────┘        │  │
└─────────────────────────────────────────────────────────────┘  │
                                                                  │
                                                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Page Object                                  │
│  pages/dashboard_page.py                                       │
│  ┌──────────────────────────────────────────────────┐         │
│  │ class DashboardPage:                             │         │
│  │     def __init__(self, page):                    │         │
│  │         self.page = page                         │         │
│  │         self.selectors = {...}                   │         │
│  │                                                   │         │
│  │     def navigate(self, url):                     │         │
│  │         self.page.goto(url)                      │─────────┼──┐
│  │                                                   │         │  │
│  │     def is_loaded(self):                         │         │  │
│  │         return self.page.locator(...).visible()  │         │  │
│  └──────────────────────────────────────────────────┘         │  │
└─────────────────────────────────────────────────────────────────┘  │
                                                                     │
                                                                     ▼
┌────────────────────────────────────────────────────────────────────┐
│                         Playwright API                              │
│  - page.goto()                                                     │
│  - page.locator()                                                  │
│  - page.click()                                                    │
│  - page.fill()                                                     │
│  - expect().to_be_visible()                                        │
└────────────────────────────┬───────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                         Browser                                     │
│  Chromium / Firefox / WebKit                                       │
│  - Executes actions on real web pages                              │
│  - Returns results to Playwright                                   │
└────────────────────────────────────────────────────────────────────┘
```

## Test Lifecycle

```
Test Start
    │
    ├─→ Browser Launch
    │       └─→ Context Creation
    │               └─→ Page Creation
    │
    ├─→ Fixture Setup (conftest.py)
    │       ├─→ app_page: Fresh page instance
    │       ├─→ authenticated_page: Navigated page
    │       └─→ helpers: Utility functions
    │
    ├─→ Test Execution
    │       ├─→ Page Object Instantiation
    │       ├─→ Navigate to URL
    │       ├─→ Interact with Elements
    │       ├─→ Verify Behavior
    │       └─→ Assertions
    │
    ├─→ Result Recording
    │       ├─→ Pass: Clean up
    │       └─→ Fail: 
    │           ├─→ Screenshot
    │           ├─→ Video
    │           └─→ Trace
    │
    └─→ Browser Cleanup
            └─→ Context Disposal
                    └─→ Browser Close
```

## Test Markers & Filtering

```
All Tests (42 total)
    │
    ├─→ @pytest.mark.e2e (42 tests)
    │       └─→ End-to-end frontend tests
    │
    ├─→ @pytest.mark.playwright (42 tests)
    │       └─→ Playwright-specific tests
    │
    ├─→ @pytest.mark.network (8 tests)
    │       └─→ Requires backend API
    │
    ├─→ @pytest.mark.slow (2 tests)
    │       └─→ Long-running tests
    │
    ├─→ @pytest.mark.german (3 tests)
    │       └─→ German compliance features
    │
    └─→ @pytest.mark.websocket (2 tests)
            └─→ WebSocket functionality
```

## Integration with Printernizer

```
┌─────────────────────────────────────────────────────────────┐
│                   Printernizer Backend                       │
│                   (FastAPI + Python)                         │
│                   Port: 8000                                 │
│   ┌─────────────────────────────────────────────┐          │
│   │ API Endpoints                                │          │
│   │ - /api/v1/printers                          │          │
│   │ - /api/v1/jobs                              │          │
│   │ - /api/v1/materials                         │          │
│   │ - /api/v1/health                            │          │
│   └─────────────────────────────────────────────┘          │
│   ┌─────────────────────────────────────────────┐          │
│   │ WebSocket                                    │          │
│   │ - /ws (Real-time updates)                   │          │
│   └─────────────────────────────────────────────┘          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP/WS
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   Printernizer Frontend                      │
│                   (Vanilla JS + HTML/CSS)                    │
│   ┌─────────────────────────────────────────────┐          │
│   │ Pages                                        │          │
│   │ - index.html (Dashboard)                    │          │
│   │ - printers.html                             │          │
│   │ - jobs.html                                 │          │
│   │ - materials.html                            │          │
│   └─────────────────────────────────────────────┘          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ Browser Automation
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Playwright E2E Tests                      │
│                    (Python + pytest)                         │
│   ┌─────────────────────────────────────────────┐          │
│   │ Page Objects                                 │          │
│   │ - DashboardPage                             │          │
│   │ - PrintersPage                              │          │
│   │ - JobsPage                                  │          │
│   │ - MaterialsPage                             │          │
│   └─────────────────────────────────────────────┘          │
│   ┌─────────────────────────────────────────────┐          │
│   │ Tests (42 total)                            │          │
│   │ - UI interactions                           │          │
│   │ - Form validation                           │          │
│   │ - API integration                           │          │
│   │ - Real-time updates                         │          │
│   └─────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## Benefits of This Architecture

1. **Separation of Concerns**
   - Tests focus on behavior
   - Page objects handle UI details
   - Fixtures manage setup/teardown

2. **Maintainability**
   - Change UI selectors in one place
   - Reusable page object methods
   - Clear test structure

3. **Reliability**
   - Auto-waiting for elements
   - Retry mechanisms
   - Isolated test execution

4. **Debugging**
   - Screenshots on failure
   - Video recordings
   - Execution traces
   - Console monitoring

5. **Scalability**
   - Easy to add new tests
   - Parallel execution support
   - Multiple browser support
   - CI/CD ready
