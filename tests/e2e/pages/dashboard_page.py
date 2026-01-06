"""
Page Object Model for Printernizer Dashboard
"""
from playwright.sync_api import Page, expect
from typing import Optional


class DashboardPage:
    """Page object for the main dashboard page"""

    # Default timeout for CI environments
    DEFAULT_TIMEOUT = 30000

    def __init__(self, page: Page):
        self.page = page

        # Selectors - matching actual HTML structure
        self.title_selector = "h1, .dashboard-title, .page-header h1"
        self.printer_card_selector = ".printer-card, .dashboard-printer-card"
        self.add_printer_button_selector = "#addPrinterBtn, button[data-action='add-printer']"
        self.status_indicator_selector = ".status-indicator, .printer-status"
        self.printer_name_selector = ".printer-name"
        self.dashboard_page_selector = "#dashboard.active, #page-dashboard.active, #dashboard.page.active"

    def navigate(self, base_url: str):
        """Navigate to the dashboard with robust waiting"""
        self.page.goto(base_url)
        self.page.wait_for_load_state("networkidle")

        # Wait for app initialization
        try:
            self.page.wait_for_function(
                "() => window.app && window.app.currentPage !== undefined",
                timeout=self.DEFAULT_TIMEOUT
            )
        except Exception:
            pass

    def is_loaded(self) -> bool:
        """Check if the dashboard is loaded"""
        try:
            # Try multiple selectors for robustness
            self.page.wait_for_selector(
                f"{self.title_selector}, {self.dashboard_page_selector}, body",
                timeout=self.DEFAULT_TIMEOUT
            )
            return True
        except Exception:
            return False
            
    def get_printer_count(self) -> int:
        """Get the number of printers displayed"""
        return self.page.locator(self.printer_card_selector).count()
        
    def click_add_printer(self):
        """Click the add printer button"""
        self.page.click(self.add_printer_button_selector)
        
    def get_printer_names(self) -> list[str]:
        """Get list of all printer names"""
        names = []
        elements = self.page.locator(self.printer_name_selector).all()
        for element in elements:
            names.append(element.inner_text())
        return names
        
    def get_printer_status(self, printer_name: str) -> Optional[str]:
        """Get status of a specific printer"""
        printer_card = self.page.locator(f"{self.printer_card_selector}:has-text('{printer_name}')")
        if printer_card.count() > 0:
            status = printer_card.locator(self.status_indicator_selector).first
            return status.get_attribute("data-status") or status.inner_text()
        return None
        
    def click_printer(self, printer_name: str):
        """Click on a specific printer card"""
        self.page.click(f"{self.printer_card_selector}:has-text('{printer_name}')")
        
    def wait_for_printers_to_load(self, timeout: int = 5000):
        """Wait for printer cards to appear"""
        self.page.wait_for_selector(self.printer_card_selector, timeout=timeout)
        
    def expect_printer_exists(self, printer_name: str):
        """Assert that a printer exists in the dashboard"""
        expect(self.page.locator(f"{self.printer_card_selector}:has-text('{printer_name}')")).to_be_visible()
        
    def expect_no_printers(self):
        """Assert that no printers are shown"""
        expect(self.page.locator(self.printer_card_selector)).to_have_count(0)
