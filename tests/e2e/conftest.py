"""
Playwright fixtures and configuration for E2E tests
"""
import pytest
import re
from playwright.sync_api import Page, BrowserContext, expect
from typing import Generator, Dict, Callable, Any
import os

# Import all page objects
from tests.e2e.pages import (
    BasePage,
    DashboardPage,
    PrintersPage,
    JobsPage,
    MaterialsPage,
    SettingsPage,
    StatisticsPage,
    TimelapsesPage,
    FilesPage,
    LibraryPage,
    IdeasPage,
    DebugPage,
)


@pytest.fixture(scope="session")
def base_url() -> str:
    """Base URL for the application"""
    return os.getenv("PLAYWRIGHT_BASE_URL", "http://localhost:8000")


@pytest.fixture
def authenticated_page(page: Page, base_url: str) -> Generator[Page, None, None]:
    """
    Provides a page instance that's already navigated to the dashboard.
    Since Printernizer doesn't have authentication yet, this just navigates to the base URL.
    """
    page.goto(base_url)
    page.wait_for_load_state("networkidle")
    yield page


@pytest.fixture
def app_page(page: Page, base_url: str) -> Generator[Page, None, None]:
    """
    Provides a fresh page instance ready for testing.
    Alias for authenticated_page for clarity.
    """
    page.goto(base_url)
    page.wait_for_load_state("networkidle")
    yield page


@pytest.fixture
def mock_api_context(context: BrowserContext) -> BrowserContext:
    """
    Provides a context with API mocking capabilities.
    Useful for testing frontend behavior without backend.
    """
    # You can add route mocking here if needed
    # context.route("**/api/v1/**", lambda route: route.fulfill(...))
    return context


def wait_for_api_response(page: Page, endpoint: str, timeout: int = 5000):
    """
    Helper function to wait for specific API response.
    
    Args:
        page: Playwright page instance
        endpoint: API endpoint to wait for (e.g., "/api/v1/printers")
        timeout: Maximum time to wait in milliseconds
    """
    with page.expect_response(lambda response: endpoint in response.url, timeout=timeout):
        pass


def wait_for_element(page: Page, selector: str, timeout: int = 5000):
    """
    Helper function to wait for element to be visible.
    
    Args:
        page: Playwright page instance
        selector: CSS selector for the element
        timeout: Maximum time to wait in milliseconds
    """
    page.wait_for_selector(selector, state="visible", timeout=timeout)


def take_debug_screenshot(page: Page, name: str):
    """
    Take a screenshot for debugging purposes.
    
    Args:
        page: Playwright page instance
        name: Name for the screenshot file
    """
    screenshot_dir = "test-reports/playwright/screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    page.screenshot(path=f"{screenshot_dir}/{name}.png")


@pytest.fixture
def helpers():
    """
    Provides helper functions for tests.
    """
    return {
        "wait_for_api_response": wait_for_api_response,
        "wait_for_element": wait_for_element,
        "take_debug_screenshot": take_debug_screenshot,
    }


@pytest.fixture
def wait_for_page_load(page: Page):
    """Helper to wait for SPA page transitions"""
    def _wait(page_hash: str, timeout: int = 5000):
        page.wait_for_function(
            f"() => window.location.hash === '#{page_hash}' && window.app && window.app.currentPage === '{page_hash}'"
        )
        page.wait_for_selector(f"#{page_hash}.page.active, [id='{page_hash}'].page.active, #page-{page_hash}.active", timeout=timeout)
    return _wait


@pytest.fixture
def modal_helpers(page: Page) -> Dict[str, Callable]:
    """Provides modal interaction helpers"""
    def open_modal(modal_id: str, timeout: int = 5000):
        page.wait_for_selector(f"#{modal_id}", state="visible", timeout=timeout)

    def close_modal(modal_id: str, timeout: int = 5000):
        page.wait_for_selector(f"#{modal_id}", state="hidden", timeout=timeout)

    def is_modal_open(modal_id: str) -> bool:
        return page.locator(f"#{modal_id}").is_visible()

    def click_modal_close(modal_id: str):
        close_btn = page.locator(f"#{modal_id} .modal-close, #{modal_id} button:has-text('Schließen')").first
        if close_btn.is_visible():
            close_btn.click()

    return {
        "open_modal": open_modal,
        "close_modal": close_modal,
        "is_modal_open": is_modal_open,
        "click_modal_close": click_modal_close,
    }


@pytest.fixture
def api_response_waiter(page: Page):
    """Helper to wait for API responses"""
    def _wait(endpoint: str, method: str = "GET", timeout: int = 5000):
        with page.expect_response(
            lambda resp: endpoint in resp.url and resp.request.method == method,
            timeout=timeout
        ) as response_info:
            return response_info.value
    return _wait


@pytest.fixture
def toast_checker(page: Page):
    """Helper to check toast notifications"""
    def _check(expected_type: str = None, expected_text: str = None, timeout: int = 3000):
        toast = page.locator(".toast, .notification, .alert")
        try:
            toast.first.wait_for(state="visible", timeout=timeout)
            if expected_type:
                expect(toast.first).to_have_class(re.compile(f"(toast|notification|alert).*{expected_type}"))
            if expected_text:
                expect(toast.first).to_contain_text(expected_text)
            return True
        except:
            return False
    return _check


@pytest.fixture
def navigate_to_page(page: Page, base_url: str):
    """Helper to navigate to different pages"""
    def _navigate(page_hash: str, wait_for_load: bool = True):
        page.goto(f"{base_url}/#{page_hash}", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        if wait_for_load:
            page.wait_for_function("() => window.app && window.app.currentPage", timeout=10000)
            page.wait_for_selector(
                f"#{page_hash}.page.active, [id='{page_hash}'].page.active, #page-{page_hash}.page.active",
                state="visible",
                timeout=10000
            )
    return _navigate


@pytest.fixture
def click_nav_link(page: Page):
    """Helper to click navigation links"""
    def _click(page_name: str):
        nav_link = page.locator(f"a[data-page='{page_name}'], a[href='#{page_name}']").first
        nav_link.click()
        page.wait_for_timeout(500)
    return _click


# ============================================================================
# API Mocking Fixtures for E2E Tests
# ============================================================================

# Sample test data for API mocking
SAMPLE_PRINTERS = [
    {
        "id": "test-printer-1",
        "name": "Test Bambu Printer",
        "printer_type": "bambu_lab",
        "status": "idle",
        "ip_address": "192.168.1.100",
        "connection_config": {"access_code": "12345678", "serial_number": "ABC123"},
        "location": "Lab A",
        "description": "Test printer for E2E",
        "is_enabled": True,
        "last_seen": "2025-01-01T12:00:00Z",
        "current_job": None,
        "temperatures": {"bed": 25.0, "nozzle": 25.0},
        "filaments": [],
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T12:00:00Z"
    },
    {
        "id": "test-printer-2",
        "name": "Test Prusa Printer",
        "printer_type": "prusa_core",
        "status": "printing",
        "ip_address": "192.168.1.101",
        "connection_config": {"api_key": "test-api-key"},
        "location": "Lab B",
        "description": "Another test printer",
        "is_enabled": True,
        "last_seen": "2025-01-01T12:00:00Z",
        "current_job": {
            "name": "test_model.gcode",
            "status": "printing",
            "progress": 45,
            "started_at": "2025-01-01T10:00:00Z",
            "estimated_remaining": 3600,
            "layer_current": 50,
            "layer_total": 100
        },
        "temperatures": {"bed": 60.0, "nozzle": 210.0},
        "filaments": [],
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T12:00:00Z"
    }
]

SAMPLE_MATERIALS = [
    {
        "id": "test-material-1",
        "material_type": "PLA",
        "brand": "OVERTURE",
        "color": "Blue",
        "diameter": 1.75,
        "weight": 1000,
        "remaining_weight": 800,
        "remaining_percentage": 80.0,
        "cost_per_kg": "20.00",
        "remaining_value": "16.00",
        "vendor": "Amazon",
        "batch_number": "BATCH001",
        "notes": "Test material",
        "printer_id": None,
        "color_hex": "#0000FF",
        "location": "Shelf A1",
        "is_active": True,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T12:00:00Z"
    },
    {
        "id": "test-material-2",
        "material_type": "PETG",
        "brand": "Prusament",
        "color": "Orange",
        "diameter": 1.75,
        "weight": 1000,
        "remaining_weight": 500,
        "remaining_percentage": 50.0,
        "cost_per_kg": "30.00",
        "remaining_value": "15.00",
        "vendor": "Prusa",
        "batch_number": "BATCH002",
        "notes": "Second test material",
        "printer_id": None,
        "color_hex": "#FF8000",
        "location": "Shelf A2",
        "is_active": True,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T12:00:00Z"
    }
]

SAMPLE_JOBS = [
    {
        "id": "test-job-1",
        "name": "Test Print 1",
        "file_name": "benchy.gcode",
        "printer_id": "test-printer-1",
        "printer_name": "Test Bambu Printer",
        "status": "completed",
        "progress": 100,
        "is_business": False,
        "started_at": "2025-01-01T10:00:00Z",
        "completed_at": "2025-01-01T12:00:00Z",
        "created_at": "2025-01-01T09:00:00Z",
        "updated_at": "2025-01-01T12:00:00Z"
    },
    {
        "id": "test-job-2",
        "name": "Business Order 1",
        "file_name": "custom_part.gcode",
        "printer_id": "test-printer-2",
        "printer_name": "Test Prusa Printer",
        "status": "printing",
        "progress": 45,
        "is_business": True,
        "customer_name": "Test Customer",
        "started_at": "2025-01-01T10:00:00Z",
        "completed_at": None,
        "created_at": "2025-01-01T09:00:00Z",
        "updated_at": "2025-01-01T11:00:00Z"
    }
]


@pytest.fixture
def mock_printers_api(page: Page):
    """
    Fixture that mocks the printers API to return sample data.
    Useful for testing UI without backend connectivity.
    """
    import json

    def setup_mock():
        page.route("**/api/v1/printers", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(SAMPLE_PRINTERS)
        ))
        page.route("**/api/v1/printers/*", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(SAMPLE_PRINTERS[0])
        ))

    return setup_mock


@pytest.fixture
def mock_materials_api(page: Page):
    """
    Fixture that mocks the materials API to return sample data.
    """
    import json

    def setup_mock():
        page.route("**/api/v1/materials", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(SAMPLE_MATERIALS)
        ))
        page.route("**/api/v1/materials/*", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(SAMPLE_MATERIALS[0])
        ))

    return setup_mock


@pytest.fixture
def mock_jobs_api(page: Page):
    """
    Fixture that mocks the jobs API to return sample data.
    """
    import json

    def setup_mock():
        page.route("**/api/v1/jobs", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(SAMPLE_JOBS)
        ))
        page.route("**/api/v1/jobs/*", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(SAMPLE_JOBS[0])
        ))

    return setup_mock


@pytest.fixture
def mock_all_apis(page: Page):
    """
    Fixture that mocks all main APIs with sample data.
    Combines printers, materials, and jobs mocking.
    """
    import json

    def setup_mocks():
        # Mock printers
        page.route("**/api/v1/printers", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(SAMPLE_PRINTERS)
        ))

        # Mock materials
        page.route("**/api/v1/materials", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(SAMPLE_MATERIALS)
        ))

        # Mock jobs
        page.route("**/api/v1/jobs", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(SAMPLE_JOBS)
        ))

    return setup_mocks


@pytest.fixture
def page_with_mocked_printers(page: Page, base_url: str, mock_printers_api):
    """
    Provides a page with mocked printers API already set up.
    """
    mock_printers_api()
    page.goto(base_url)
    page.wait_for_load_state("networkidle")
    return page


@pytest.fixture
def page_with_mocked_materials(page: Page, base_url: str, mock_materials_api):
    """
    Provides a page with mocked materials API already set up.
    """
    mock_materials_api()
    page.goto(base_url)
    page.wait_for_load_state("networkidle")
    return page


@pytest.fixture
def page_with_all_mocks(page: Page, base_url: str, mock_all_apis):
    """
    Provides a page with all APIs mocked.
    """
    mock_all_apis()
    page.goto(base_url)
    page.wait_for_load_state("networkidle")
    return page


# ============================================================================
# Extended Timeout Configuration
# ============================================================================

# Default timeout for CI environments (30 seconds)
E2E_DEFAULT_TIMEOUT = 30000

# Extended timeout for slower operations
E2E_EXTENDED_TIMEOUT = 60000


@pytest.fixture
def extended_timeout():
    """Returns extended timeout value for slower operations"""
    return E2E_EXTENDED_TIMEOUT


# ============================================================================
# Modal Testing Helpers
# ============================================================================

@pytest.fixture
def wait_for_modal_visible(page: Page):
    """Helper to wait for modal to become visible (with .show class)"""
    def _wait(modal_id: str, timeout: int = E2E_DEFAULT_TIMEOUT):
        # Modals in Printernizer use .show class for visibility
        page.wait_for_selector(
            f"#{modal_id}.show, #{modal_id}:not([style*='display: none'])",
            state="visible",
            timeout=timeout
        )
    return _wait


@pytest.fixture
def wait_for_modal_hidden(page: Page):
    """Helper to wait for modal to be hidden"""
    def _wait(modal_id: str, timeout: int = E2E_DEFAULT_TIMEOUT):
        page.wait_for_selector(
            f"#{modal_id}",
            state="hidden",
            timeout=timeout
        )
    return _wait


@pytest.fixture
def click_and_wait_for_modal(page: Page):
    """Helper to click a button and wait for modal to open"""
    def _click(button_selector: str, modal_id: str, timeout: int = E2E_DEFAULT_TIMEOUT):
        page.click(button_selector)
        page.wait_for_timeout(300)  # Small delay for animation
        page.wait_for_selector(
            f"#{modal_id}.show, #{modal_id}:not([style*='display: none'])",
            state="visible",
            timeout=timeout
        )
    return _click


# ============================================================================
# API Seeding Fixtures for E2E Tests
# ============================================================================

import requests
import uuid


@pytest.fixture
def seeded_printers(base_url: str):
    """
    Create test printers via API before E2E tests.
    Cleans up created printers after the test.

    Yields:
        List of created printer data dictionaries
    """
    created_printers = []
    api_base = base_url.rstrip('/')

    # Create test printers
    test_printers = [
        {
            "name": f"E2E Test Bambu {uuid.uuid4().hex[:6]}",
            "printer_type": "bambu_lab",
            "ip_address": "192.168.1.200",
            "connection_config": {"access_code": "12345678", "serial_number": "E2ETEST1"},
            "location": "E2E Test Lab",
            "description": "E2E test printer - auto-created",
            "is_enabled": True
        },
        {
            "name": f"E2E Test Prusa {uuid.uuid4().hex[:6]}",
            "printer_type": "prusa_core",
            "ip_address": "192.168.1.201",
            "connection_config": {"api_key": "e2e-test-key"},
            "location": "E2E Test Lab",
            "description": "E2E test printer - auto-created",
            "is_enabled": True
        }
    ]

    for printer_data in test_printers:
        try:
            response = requests.post(
                f"{api_base}/api/v1/printers",
                json=printer_data,
                timeout=10
            )
            if response.status_code in [200, 201]:
                created_printer = response.json()
                created_printers.append(created_printer)
        except requests.RequestException:
            pass  # Silently continue if API not available

    yield created_printers

    # Cleanup: delete created printers
    for printer in created_printers:
        try:
            requests.delete(
                f"{api_base}/api/v1/printers/{printer['id']}",
                timeout=10
            )
        except requests.RequestException:
            pass  # Silently continue if cleanup fails


@pytest.fixture
def seeded_materials(base_url: str):
    """
    Create test materials via API before E2E tests.
    Cleans up created materials after the test.

    Yields:
        List of created material data dictionaries
    """
    created_materials = []
    api_base = base_url.rstrip('/')

    test_materials = [
        {
            "material_type": "PLA",
            "brand": "E2E Test Brand",
            "color": "Blue",
            "diameter": 1.75,
            "weight": 1000,
            "remaining_weight": 800,
            "cost_per_kg": "20.00",
            "vendor": "E2E Test Vendor",
            "notes": "E2E test material - auto-created",
            "color_hex": "#0000FF",
            "location": "E2E Test Shelf",
            "is_active": True
        },
        {
            "material_type": "PETG",
            "brand": "E2E Test Brand",
            "color": "Orange",
            "diameter": 1.75,
            "weight": 1000,
            "remaining_weight": 500,
            "cost_per_kg": "25.00",
            "vendor": "E2E Test Vendor",
            "notes": "E2E test material - auto-created",
            "color_hex": "#FF8000",
            "location": "E2E Test Shelf",
            "is_active": True
        }
    ]

    for material_data in test_materials:
        try:
            response = requests.post(
                f"{api_base}/api/v1/materials",
                json=material_data,
                timeout=10
            )
            if response.status_code in [200, 201]:
                created_material = response.json()
                created_materials.append(created_material)
        except requests.RequestException:
            pass  # Silently continue if API not available

    yield created_materials

    # Cleanup: delete created materials
    for material in created_materials:
        try:
            requests.delete(
                f"{api_base}/api/v1/materials/{material['id']}",
                timeout=10
            )
        except requests.RequestException:
            pass  # Silently continue if cleanup fails


@pytest.fixture
def seeded_jobs(base_url: str, seeded_printers):
    """
    Create test jobs via API before E2E tests.
    Requires seeded_printers fixture to get valid printer IDs.
    Cleans up created jobs after the test.

    Yields:
        List of created job data dictionaries
    """
    created_jobs = []
    api_base = base_url.rstrip('/')

    # Skip if no printers were created
    if not seeded_printers:
        yield []
        return

    printer_id = seeded_printers[0].get('id')
    if not printer_id:
        yield []
        return

    test_jobs = [
        {
            "printer_id": printer_id,
            "job_name": f"E2E Test Job {uuid.uuid4().hex[:6]}",
            "filename": "e2e_test_model.gcode",
            "material_type": "PLA",
            "is_business": False
        },
        {
            "printer_id": printer_id,
            "job_name": f"E2E Business Job {uuid.uuid4().hex[:6]}",
            "filename": "e2e_business_model.gcode",
            "material_type": "PETG",
            "is_business": True,
            "customer_name": "E2E Test Customer"
        }
    ]

    for job_data in test_jobs:
        try:
            response = requests.post(
                f"{api_base}/api/v1/jobs",
                json=job_data,
                timeout=10
            )
            if response.status_code in [200, 201]:
                created_job = response.json()
                created_jobs.append(created_job)
        except requests.RequestException:
            pass  # Silently continue if API not available

    yield created_jobs

    # Cleanup: delete created jobs
    for job in created_jobs:
        try:
            requests.delete(
                f"{api_base}/api/v1/jobs/{job['id']}",
                timeout=10
            )
        except requests.RequestException:
            pass  # Silently continue if cleanup fails


@pytest.fixture
def seeded_all_data(seeded_printers, seeded_materials, seeded_jobs):
    """
    Convenience fixture that creates printers, materials, and jobs.
    Use this when a test needs all types of data.

    Yields:
        Dictionary with 'printers', 'materials', and 'jobs' keys
    """
    yield {
        'printers': seeded_printers,
        'materials': seeded_materials,
        'jobs': seeded_jobs
    }
