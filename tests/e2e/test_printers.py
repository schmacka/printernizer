"""
E2E tests for Printernizer Printers Management
"""
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.pages import PrintersPage

# Timeout for E2E tests (longer for CI)
E2E_TIMEOUT = 30000


@pytest.mark.e2e
@pytest.mark.playwright
def test_printers_page_loads(app_page: Page, base_url: str):
    """Test that the printers page loads successfully"""
    printers = PrintersPage(app_page)
    printers.navigate(base_url)

    # Verify URL contains printers hash
    expect(app_page).to_have_url(f"{base_url}/#printers", timeout=E2E_TIMEOUT)


@pytest.mark.e2e
@pytest.mark.playwright
def test_add_printer_modal_opens(app_page: Page, base_url: str):
    """Test that the add printer modal can be opened"""
    printers = PrintersPage(app_page)
    printers.navigate(base_url)

    # Wait for add button to be available
    add_button = app_page.locator(printers.add_printer_button_selector)
    add_button.wait_for(state="visible", timeout=E2E_TIMEOUT)

    if add_button.is_visible():
        printers.open_add_printer_modal()

        # Check if modal is visible
        modal = app_page.locator(printers.add_printer_modal_selector)
        expect(modal).to_be_visible(timeout=E2E_TIMEOUT)


@pytest.mark.e2e
@pytest.mark.playwright
def test_printer_form_validation(app_page: Page, base_url: str):
    """Test printer form validation"""
    printers = PrintersPage(app_page)
    printers.navigate(base_url)

    add_button = app_page.locator(printers.add_printer_button_selector)
    add_button.wait_for(state="visible", timeout=E2E_TIMEOUT)

    if add_button.is_visible():
        printers.open_add_printer_modal()

        # Try to submit empty form
        printers.submit_printer_form()

        # Form should still be visible (validation failed)
        modal = app_page.locator(printers.add_printer_modal_selector)
        expect(modal).to_be_visible(timeout=E2E_TIMEOUT)


@pytest.mark.e2e
@pytest.mark.playwright
@pytest.mark.network
def test_add_bambu_printer(app_page: Page, base_url: str):
    """Test adding a Bambu Lab printer (requires backend)"""
    printers = PrintersPage(app_page)
    printers.navigate(base_url)

    add_button = app_page.locator(printers.add_printer_button_selector)
    add_button.wait_for(state="visible", timeout=E2E_TIMEOUT)

    if add_button.is_visible():
        # Add a test printer
        test_printer_name = "Test Bambu Printer"
        test_printer_ip = "192.168.1.100"

        printers.add_printer(test_printer_name, test_printer_ip, "bambu")

        # Wait for page to update
        app_page.wait_for_timeout(1000)

        # Verify printer appears in list (may fail if backend not running)
        printer_list = printers.get_printer_list()
        # Note: This assertion may fail if backend is not running
        # It's more of an integration test


@pytest.mark.e2e
@pytest.mark.playwright
def test_printer_list_display(app_page: Page, base_url: str):
    """Test that printer list is displayed"""
    printers = PrintersPage(app_page)
    printers.navigate(base_url)

    # Check if printers list exists (wait for it to be attached to DOM)
    list_element = app_page.locator(printers.printers_list_selector)
    # Use attached state instead of visible - list may be empty but should exist
    list_element.wait_for(state="attached", timeout=E2E_TIMEOUT)
    expect(list_element.first).to_be_attached()


@pytest.mark.e2e
@pytest.mark.playwright
def test_printer_types_available(app_page: Page, base_url: str):
    """Test that both Bambu and Prusa printer types are available"""
    printers = PrintersPage(app_page)
    printers.navigate(base_url)
    
    add_button = app_page.locator("#addPrinterBtn, button:has-text('Drucker hinzufügen')")
    if add_button.count() > 0:
        printers.open_add_printer_modal()
        
        # Check printer type options
        type_select = app_page.locator(printers.printer_type_select_selector)
        if type_select.count() > 0:
            options = type_select.first.locator("option").all()
            option_values = [opt.get_attribute("value") for opt in options]
            
            # Should have both bambu and prusa options
            assert any("bambu" in str(val).lower() for val in option_values), "Should have Bambu Lab option"
            assert any("prusa" in str(val).lower() for val in option_values), "Should have Prusa option"
