"""
Page Object Model for Printernizer Printers page
"""
from playwright.sync_api import Page, expect
from typing import Optional


class PrintersPage:
    """Page object for the printers management page"""
    
    def __init__(self, page: Page):
        self.page = page
        
        # Selectors
        self.printers_list_selector = ".printers-list, #printersList"
        self.printer_row_selector = ".printer-row, tr.printer"
        self.add_printer_modal_selector = "#addPrinterModal, .add-printer-modal"
        self.printer_form_selector = "#printerForm, .printer-form"
        self.printer_name_input_selector = "input[name='name'], #printerName"
        self.printer_ip_input_selector = "input[name='ip'], #printerIp"
        self.printer_type_select_selector = "select[name='type'], #printerType"
        self.save_printer_button_selector = "button[type='submit'], .save-printer-btn"
        self.delete_printer_button_selector = ".delete-printer-btn, button[data-action='delete']"
        
    def navigate(self, base_url: str):
        """Navigate to printers page"""
        self.page.goto(f"{base_url}/printers.html")
        self.page.wait_for_load_state("networkidle")
        
    def open_add_printer_modal(self):
        """Open the add printer modal"""
        self.page.click("button:has-text('Add Printer')")
        self.page.wait_for_selector(self.add_printer_modal_selector, state="visible")
        
    def fill_printer_form(self, name: str, ip: str, printer_type: str = "bambu"):
        """Fill out the printer form"""
        self.page.fill(self.printer_name_input_selector, name)
        self.page.fill(self.printer_ip_input_selector, ip)
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
        self.page.wait_for_selector(self.add_printer_modal_selector, state="hidden", timeout=5000)
        
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
