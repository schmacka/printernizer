"""
Playwright fixtures and configuration for E2E tests
"""
import pytest
from playwright.sync_api import Page, BrowserContext, expect
from typing import Generator
import os


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
