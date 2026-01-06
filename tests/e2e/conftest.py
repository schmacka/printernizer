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
