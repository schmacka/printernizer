"""
Page Object Model for Printernizer Printers page
"""
from playwright.sync_api import Page, expect
from typing import Optional


class PrintersPage:
    """Page object for the printers management page"""

    # Default timeout for CI environments (longer than local)
    DEFAULT_TIMEOUT = 30000

    def __init__(self, page: Page):
        self.page = page

        # Selectors - use multiple fallbacks for robustness
        self.printers_list_selector = "#printersList, .printers-list"
        self.printer_row_selector = ".printer-card, .printer-row, [data-printer-id]"
        self.add_printer_modal_selector = "#addPrinterModal"
        self.printer_form_selector = "#addPrinterForm, #printerForm"
        self.printer_name_input_selector = "#printerName, input[name='name']"
        self.printer_ip_input_selector = "#printerIp, input[name='ip']"
        self.printer_type_select_selector = "#printerType, select[name='type']"
        self.save_printer_button_selector = "#addPrinterForm button[type='submit'], .save-printer-btn"
        self.delete_printer_button_selector = ".delete-printer-btn, button[data-action='delete']"
        self.add_printer_button_selector = "#addPrinterBtn"

    def navigate(self, base_url: str):
        """Navigate to printers page with robust waiting"""
        # First go to base URL to ensure app is loaded
        self.page.goto(base_url, wait_until="domcontentloaded")
        self.page.wait_for_load_state("networkidle")

        # Wait for app initialization
        try:
            self.page.wait_for_function(
                "() => window.app && typeof window.app.showPage === 'function'",
                timeout=self.DEFAULT_TIMEOUT
            )
        except Exception:
            pass

        # Navigate to printers page via hash
        self.page.goto(f"{base_url}/#printers", wait_until="domcontentloaded")

        # Wait for navigation to complete - check that currentPage is 'printers'
        try:
            self.page.wait_for_function(
                "() => window.app && window.app.currentPage === 'printers'",
                timeout=self.DEFAULT_TIMEOUT
            )
        except Exception:
            # Fallback: wait a bit for navigation to settle
            self.page.wait_for_timeout(500)

        # Wait for the printers page section to be visible
        # Use longer timeout and ensure page is actually visible (not just attached)
        self.page.wait_for_selector(
            "#printers.page.active, #printers.active",
            state="visible",
            timeout=self.DEFAULT_TIMEOUT
        )
        
    def open_add_printer_modal(self):
        """Open the add printer modal"""
        self.page.click(self.add_printer_button_selector)
        self.page.wait_for_selector(self.add_printer_modal_selector, state="visible", timeout=self.DEFAULT_TIMEOUT)

    def fill_printer_form(self, name: str, ip: str, printer_type: str = "bambu"):
        """Fill out the printer form"""
        self.page.fill(self.printer_name_input_selector, name)
        self.page.fill(self.printer_ip_input_selector, ip)
        type_select = self.page.locator(self.printer_type_select_selector)
        if type_select.is_visible():
            self.page.select_option(self.printer_type_select_selector, printer_type)

    def submit_printer_form(self):
        """Submit the printer form"""
        self.page.click(self.save_printer_button_selector)

    def add_printer(self, name: str, ip: str, printer_type: str = "bambu"):
        """Complete flow to add a new printer"""
        self.open_add_printer_modal()
        self.fill_printer_form(name, ip, printer_type)
        self.submit_printer_form()
        # Wait for modal to close
        self.page.wait_for_selector(self.add_printer_modal_selector, state="hidden", timeout=self.DEFAULT_TIMEOUT)
        
    def get_printer_list(self) -> list[str]:
        """Get list of all printer names"""
        names = []
        rows = self.page.locator(self.printer_row_selector).all()
        for row in rows:
            name_element = row.locator(".printer-name, td:first-child")
            if name_element.count() > 0:
                names.append(name_element.inner_text())
        return names
        
    def delete_printer(self, printer_name: str):
        """Delete a printer by name"""
        printer_row = self.page.locator(f"{self.printer_row_selector}:has-text('{printer_name}')")
        printer_row.locator(self.delete_printer_button_selector).click()
        
        # Handle confirmation dialog if present
        self.page.on("dialog", lambda dialog: dialog.accept())
        
    def expect_printer_in_list(self, printer_name: str):
        """Assert that a printer appears in the list"""
        expect(self.page.locator(f"{self.printer_row_selector}:has-text('{printer_name}')")).to_be_visible()
