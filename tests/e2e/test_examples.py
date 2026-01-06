"""
Comprehensive example E2E test demonstrating Playwright features
This test shows various testing patterns and best practices
"""
import pytest
from playwright.sync_api import Page, expect, TimeoutError
from tests.e2e.pages import DashboardPage, PrintersPage, JobsPage

# Timeout for E2E tests (longer for CI)
E2E_TIMEOUT = 30000


@pytest.mark.e2e
@pytest.mark.playwright
class TestPrintWorkflow:
    """
    Example test suite demonstrating a complete print workflow
    from adding a printer to creating a job
    """

    def test_complete_workflow_example(self, app_page: Page, base_url: str):
        """
        Comprehensive workflow test showing:
        - Page navigation
        - Form interaction
        - API response waiting
        - Multiple page objects
        - Assertions
        """
        # Step 1: Check dashboard loads
        dashboard = DashboardPage(app_page)
        dashboard.navigate(base_url)
        assert dashboard.is_loaded(), "Dashboard should load"

        # Step 2: Navigate to printers page
        printers = PrintersPage(app_page)
        printers.navigate(base_url)

        # Step 3: Get initial printer count
        initial_count = len(printers.get_printer_list())

        # Step 4: Try to add printer (will work if backend is running)
        try:
            add_button = app_page.locator(printers.add_printer_button_selector)
            add_button.wait_for(state="visible", timeout=E2E_TIMEOUT)

            if add_button.is_visible():
                printers.open_add_printer_modal()

                # Fill form
                printers.fill_printer_form(
                    name="E2E Test Printer",
                    ip="192.168.1.200",
                    printer_type="bambu"
                )

                # Note: Don't submit in this example to avoid side effects
                # printers.submit_printer_form()

                # Close modal with Escape
                app_page.keyboard.press("Escape")
        except TimeoutError:
            # Modal might not be implemented yet
            pass

        # Step 5: Navigate to jobs page
        jobs = JobsPage(app_page)
        jobs.navigate(base_url)

        # Step 6: Verify jobs page loaded
        expect(app_page).to_have_url(f"{base_url}/#jobs", timeout=E2E_TIMEOUT)

        # Step 7: Check for create job button
        create_button = app_page.locator(jobs.create_job_button_selector)
        create_button.wait_for(state="visible", timeout=E2E_TIMEOUT)
        expect(create_button.first).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
def test_api_mocking_example(app_page: Page, base_url: str):
    """
    Example showing how to mock API responses for isolated frontend testing
    """
    # Mock the printers API endpoint
    def handle_printers_route(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body='{"printers": [{"id": 1, "name": "Mocked Printer", "status": "idle"}]}'
        )
    
    app_page.route("**/api/v1/printers", handle_printers_route)
    
    # Navigate to dashboard
    dashboard = DashboardPage(app_page)
    dashboard.navigate(base_url)
    
    # The page should load with mocked data
    assert dashboard.is_loaded()


@pytest.mark.e2e
@pytest.mark.playwright
@pytest.mark.slow
def test_console_and_network_monitoring_example(app_page: Page, base_url: str):
    """
    Example showing how to monitor console messages and network requests
    """
    console_messages = []
    network_requests = []
    
    # Listen for console messages
    def handle_console(msg):
        console_messages.append({
            "type": msg.type,
            "text": msg.text
        })
    
    app_page.on("console", handle_console)
    
    # Listen for network requests
    def handle_request(request):
        network_requests.append({
            "url": request.url,
            "method": request.method
        })
    
    app_page.on("request", handle_request)
    
    # Navigate to page
    app_page.goto(base_url)
    app_page.wait_for_load_state("networkidle")
    
    # Now we can analyze console and network activity
    print(f"\nConsole messages captured: {len(console_messages)}")
    print(f"Network requests captured: {len(network_requests)}")
    
    # Check for errors in console
    errors = [msg for msg in console_messages if msg["type"] == "error"]
    assert len(errors) == 0, f"Found console errors: {errors}"
    
    # Verify API calls were made
    api_calls = [req for req in network_requests if "/api/v1/" in req["url"]]
    print(f"API calls made: {len(api_calls)}")


@pytest.mark.e2e
@pytest.mark.playwright
def test_screenshot_example(app_page: Page, base_url: str, helpers):
    """
    Example showing how to take screenshots during tests
    """
    app_page.goto(base_url)
    app_page.wait_for_load_state("networkidle")
    
    # Take a debug screenshot
    helpers["take_debug_screenshot"](app_page, "dashboard_loaded")
    
    # Screenshots are saved to test-reports/playwright/screenshots/


@pytest.mark.e2e
@pytest.mark.playwright
@pytest.mark.parametrize("viewport", [
    {"width": 1920, "height": 1080},  # Desktop
    {"width": 768, "height": 1024},   # Tablet
    {"width": 375, "height": 667},    # Mobile
])
def test_responsive_example(app_page: Page, base_url: str, viewport: dict):
    """
    Example showing parametrized tests for different screen sizes
    """
    app_page.set_viewport_size(viewport)
    app_page.goto(base_url)
    app_page.wait_for_load_state("networkidle")
    
    # Test that page loads at this resolution
    expect(app_page.locator("body")).to_be_visible()
    
    print(f"\nTested viewport: {viewport['width']}x{viewport['height']}")


@pytest.mark.e2e
@pytest.mark.playwright
def test_keyboard_interaction_example(app_page: Page, base_url: str):
    """
    Example showing keyboard interactions
    """
    app_page.goto(base_url)
    
    # Test keyboard shortcuts (if implemented)
    app_page.keyboard.press("?")  # Often opens help
    app_page.wait_for_timeout(500)
    
    # Test Escape key
    app_page.keyboard.press("Escape")
    app_page.wait_for_timeout(500)
    
    # Test Tab navigation
    app_page.keyboard.press("Tab")
    
    # Test search with keyboard
    search_input = app_page.locator("input[type='search'], input[placeholder*='search' i]")
    if search_input.count() > 0:
        search_input.first.focus()
        search_input.first.type("test query")
        app_page.keyboard.press("Enter")


@pytest.mark.e2e
@pytest.mark.playwright
@pytest.mark.skipif(
    condition=True,  # Change to False to run this test
    reason="Example test - requires specific test data"
)
def test_conditional_skip_example(app_page: Page, base_url: str):
    """
    Example showing how to conditionally skip tests
    """
    # This test will be skipped
    assert True
