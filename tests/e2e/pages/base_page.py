"""
Base Page Object Model class for common functionality
"""
from playwright.sync_api import Page, expect
from typing import Optional


class BasePage:
    """Base class for all page objects with common functionality"""

    def __init__(self, page: Page):
        self.page = page
        self.page_hash = ""
        self.page_selector = ""

    def navigate(self, base_url: str):
        """Navigate to the page using hash routing"""
        if self.page_hash:
            self.page.goto(f"{base_url}/#{self.page_hash}", wait_until="domcontentloaded")
        else:
            self.page.goto(base_url, wait_until="domcontentloaded")
        self.page.wait_for_load_state("networkidle")
        self.wait_for_app_ready()
        if self.page_selector:
            self.page.wait_for_selector(self.page_selector, state="visible", timeout=10000)

    def wait_for_app_ready(self):
        """Wait for the SPA app to be initialized"""
        self.page.wait_for_function("() => window.app && window.app.currentPage", timeout=10000)

    def is_loaded(self) -> bool:
        """Check if the page is loaded"""
        try:
            if self.page_selector:
                self.page.wait_for_selector(self.page_selector, timeout=5000)
            return True
        except:
            return False

    def wait_for_loading_complete(self, timeout: int = 5000):
        """Wait for loading placeholders to disappear"""
        try:
            self.page.wait_for_selector(".loading-placeholder", state="hidden", timeout=timeout)
        except:
            pass  # Loading placeholder may not exist

    def click_button(self, selector: str, wait_after: int = 300):
        """Click a button and optionally wait"""
        self.page.click(selector)
        if wait_after > 0:
            self.page.wait_for_timeout(wait_after)

    def fill_input(self, selector: str, value: str):
        """Fill an input field"""
        self.page.fill(selector, value)

    def select_option(self, selector: str, value: str):
        """Select a dropdown option by value"""
        self.page.select_option(selector, value)

    def get_input_value(self, selector: str) -> str:
        """Get the current value of an input field"""
        return self.page.locator(selector).input_value()

    def is_element_visible(self, selector: str) -> bool:
        """Check if an element is visible"""
        return self.page.locator(selector).is_visible()

    def get_element_count(self, selector: str) -> int:
        """Get the count of elements matching a selector"""
        return self.page.locator(selector).count()

    def get_element_text(self, selector: str) -> str:
        """Get the text content of an element"""
        return self.page.locator(selector).inner_text()

    def wait_for_element(self, selector: str, timeout: int = 5000, state: str = "visible"):
        """Wait for an element to reach a specific state"""
        self.page.wait_for_selector(selector, state=state, timeout=timeout)

    def expect_visible(self, selector: str):
        """Assert that an element is visible"""
        expect(self.page.locator(selector)).to_be_visible()

    def expect_hidden(self, selector: str):
        """Assert that an element is hidden"""
        expect(self.page.locator(selector)).to_be_hidden()

    def expect_text_contains(self, selector: str, text: str):
        """Assert that an element contains specific text"""
        expect(self.page.locator(selector)).to_contain_text(text)

    def expect_count(self, selector: str, count: int):
        """Assert the number of elements matching a selector"""
        expect(self.page.locator(selector)).to_have_count(count)

    def click_refresh_button(self):
        """Click the page refresh button (common across many pages)"""
        refresh_btn = self.page.locator("button:has-text('Aktualisieren')").first
        if refresh_btn.is_visible():
            refresh_btn.click()
            self.page.wait_for_timeout(500)

    def click_settings_button(self):
        """Click the page settings button (common across many pages)"""
        settings_btn = self.page.locator("button:has-text('Einstellungen')").first
        if settings_btn.is_visible():
            settings_btn.click()
            self.page.wait_for_timeout(300)

    def open_modal(self, modal_selector: str, trigger_selector: str):
        """Open a modal by clicking a trigger button"""
        self.page.click(trigger_selector)
        self.page.wait_for_selector(modal_selector, state="visible", timeout=5000)

    def close_modal(self, modal_selector: str, close_btn_selector: Optional[str] = None):
        """Close a modal using its close button or clicking outside"""
        if close_btn_selector:
            self.page.click(close_btn_selector)
        else:
            # Try common close button selectors
            close_btn = self.page.locator(f"{modal_selector} .modal-close, {modal_selector} button:has-text('Schließen')").first
            if close_btn.is_visible():
                close_btn.click()
        self.page.wait_for_selector(modal_selector, state="hidden", timeout=5000)

    def is_modal_open(self, modal_selector: str) -> bool:
        """Check if a modal is currently open"""
        return self.page.locator(modal_selector).is_visible()
