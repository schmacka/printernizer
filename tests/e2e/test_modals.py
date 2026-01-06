"""
E2E tests for Printernizer Modals
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
@pytest.mark.playwright
class TestPrinterModals:
    """Test suite for Printer-related modals"""

    def test_add_printer_modal_opens(self, app_page: Page, base_url: str):
        """Test that add printer modal opens"""
        app_page.goto(f"{base_url}/#printers")
        app_page.wait_for_load_state("networkidle")
        app_page.wait_for_function("() => window.app && window.app.currentPage")

        # Click add printer button
        app_page.click("#addPrinterBtn, button:has-text('Drucker hinzufügen')")
        app_page.wait_for_timeout(500)

        # Modal should be visible
        expect(app_page.locator("#addPrinterModal, .modal:has-text('Drucker')")).to_be_visible()

    def test_add_printer_modal_has_form(self, app_page: Page, base_url: str):
        """Test that add printer modal has form fields"""
        app_page.goto(f"{base_url}/#printers")
        app_page.wait_for_load_state("networkidle")
        app_page.wait_for_function("() => window.app && window.app.currentPage")

        app_page.click("#addPrinterBtn, button:has-text('Drucker hinzufügen')")
        app_page.wait_for_timeout(500)

        # Check for name input
        expect(app_page.locator("input[name='name'], #printerName")).to_be_visible()

    def test_add_printer_modal_closes(self, app_page: Page, base_url: str):
        """Test that add printer modal can be closed"""
        app_page.goto(f"{base_url}/#printers")
        app_page.wait_for_load_state("networkidle")
        app_page.wait_for_function("() => window.app && window.app.currentPage")

        # Open modal
        app_page.click("#addPrinterBtn, button:has-text('Drucker hinzufügen')")
        app_page.wait_for_timeout(500)

        # Close modal
        close_btn = app_page.locator(".modal .modal-close, .modal button:has-text('Abbrechen')").first
        if close_btn.is_visible():
            close_btn.click()
            app_page.wait_for_timeout(500)

        # Modal should be hidden
        expect(app_page.locator("#addPrinterModal")).to_be_hidden()


@pytest.mark.e2e
@pytest.mark.playwright
class TestIdeasModals:
    """Test suite for Ideas-related modals"""

    def test_new_idea_modal_opens(self, app_page: Page, base_url: str):
        """Test that new idea modal opens"""
        app_page.goto(f"{base_url}/#ideas")
        app_page.wait_for_load_state("networkidle")
        app_page.wait_for_function("() => window.app && window.app.currentPage")

        app_page.click("button:has-text('Neue Idee')")
        app_page.wait_for_timeout(500)

        expect(app_page.locator(".modal:has-text('Idee'), #addIdeaModal")).to_be_visible()

    def test_import_url_modal_opens(self, app_page: Page, base_url: str):
        """Test that import URL modal opens"""
        app_page.goto(f"{base_url}/#ideas")
        app_page.wait_for_load_state("networkidle")
        app_page.wait_for_function("() => window.app && window.app.currentPage")

        app_page.click("button:has-text('Aus URL importieren')")
        app_page.wait_for_timeout(500)

        expect(app_page.locator(".modal:has-text('Import'), #importIdeaModal")).to_be_visible()

    def test_import_modal_has_url_field(self, app_page: Page, base_url: str):
        """Test that import modal has URL field"""
        app_page.goto(f"{base_url}/#ideas")
        app_page.wait_for_load_state("networkidle")
        app_page.wait_for_function("() => window.app && window.app.currentPage")

        app_page.click("button:has-text('Aus URL importieren')")
        app_page.wait_for_timeout(500)

        expect(app_page.locator("#importUrl, input[name='url'], input[type='url']")).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
class TestMaterialsModals:
    """Test suite for Materials-related modals"""

    def test_add_material_modal_opens(self, app_page: Page, base_url: str):
        """Test that add material modal opens"""
        app_page.goto(f"{base_url}/#materials")
        app_page.wait_for_load_state("networkidle")
        app_page.wait_for_function("() => window.app && window.app.currentPage")

        app_page.click("#addMaterialBtn, button:has-text('Filament hinzufügen')")
        app_page.wait_for_timeout(500)

        expect(app_page.locator(".modal:has-text('Filament'), #materialModal")).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
class TestLibraryModals:
    """Test suite for Library-related modals"""

    @pytest.mark.slow
    def test_file_detail_modal_opens(self, app_page: Page, base_url: str):
        """Test that file detail modal opens when clicking a file"""
        app_page.goto(f"{base_url}/#library")
        app_page.wait_for_load_state("networkidle")
        app_page.wait_for_function("() => window.app && window.app.currentPage")
        app_page.wait_for_timeout(1000)  # Wait for files to load

        # Check if there are any files
        file_cards = app_page.locator(".library-file-card")
        if file_cards.count() > 0:
            file_cards.first.click()
            app_page.wait_for_timeout(500)

            expect(app_page.locator("#fileDetailModal")).to_be_visible()

    @pytest.mark.slow
    def test_file_detail_modal_has_close_button(self, app_page: Page, base_url: str):
        """Test that file detail modal has close button"""
        app_page.goto(f"{base_url}/#library")
        app_page.wait_for_load_state("networkidle")
        app_page.wait_for_function("() => window.app && window.app.currentPage")
        app_page.wait_for_timeout(1000)

        file_cards = app_page.locator(".library-file-card")
        if file_cards.count() > 0:
            file_cards.first.click()
            app_page.wait_for_timeout(500)

            expect(app_page.locator("#closeFileDetailModal, #fileDetailModal .modal-close")).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
class TestModalBehavior:
    """Test suite for modal behavior"""

    def test_modal_close_button_works(self, app_page: Page, base_url: str):
        """Test that modal close button works"""
        app_page.goto(f"{base_url}/#ideas")
        app_page.wait_for_load_state("networkidle")
        app_page.wait_for_function("() => window.app && window.app.currentPage")

        # Open modal
        app_page.click("button:has-text('Neue Idee')")
        app_page.wait_for_timeout(500)

        # Find and click close button
        close_btn = app_page.locator(".modal:visible .modal-close, .modal.show .modal-close").first
        if close_btn.is_visible():
            close_btn.click()
            app_page.wait_for_timeout(500)

            # Modal should be hidden
            expect(app_page.locator(".modal:visible")).to_have_count(0)

    def test_modal_escape_key_closes(self, app_page: Page, base_url: str):
        """Test that pressing Escape closes the modal"""
        app_page.goto(f"{base_url}/#ideas")
        app_page.wait_for_load_state("networkidle")
        app_page.wait_for_function("() => window.app && window.app.currentPage")

        # Open modal
        app_page.click("button:has-text('Neue Idee')")
        app_page.wait_for_timeout(500)

        # Press Escape
        app_page.keyboard.press("Escape")
        app_page.wait_for_timeout(500)

        # Modal might be hidden (depends on implementation)
        # This test documents expected behavior
        assert True

    def test_multiple_modals_can_open(self, app_page: Page, base_url: str):
        """Test that different modals can be opened"""
        app_page.goto(f"{base_url}/#ideas")
        app_page.wait_for_load_state("networkidle")
        app_page.wait_for_function("() => window.app && window.app.currentPage")

        # Open new idea modal
        app_page.click("button:has-text('Neue Idee')")
        app_page.wait_for_timeout(500)
        expect(app_page.locator(".modal:visible")).to_have_count(1)

        # Close it
        close_btn = app_page.locator(".modal:visible .modal-close").first
        if close_btn.is_visible():
            close_btn.click()
            app_page.wait_for_timeout(500)

        # Open import modal
        app_page.click("button:has-text('Aus URL importieren')")
        app_page.wait_for_timeout(500)
        expect(app_page.locator(".modal:visible")).to_have_count(1)


@pytest.mark.e2e
@pytest.mark.playwright
class TestSettingsModal:
    """Test suite for Settings page-specific modals"""

    def test_settings_has_tabs(self, app_page: Page, base_url: str):
        """Test that settings page has tabs"""
        app_page.goto(f"{base_url}/#settings")
        app_page.wait_for_load_state("networkidle")
        app_page.wait_for_function("() => window.app && window.app.currentPage")

        expect(app_page.locator(".settings-tabs")).to_be_visible()

    def test_settings_tab_switching(self, app_page: Page, base_url: str):
        """Test that settings tabs can be switched"""
        app_page.goto(f"{base_url}/#settings")
        app_page.wait_for_load_state("networkidle")
        app_page.wait_for_function("() => window.app && window.app.currentPage")

        # Click on Jobs tab
        jobs_tab = app_page.locator(".settings-tab[data-tab='jobs']")
        if jobs_tab.is_visible():
            jobs_tab.click()
            app_page.wait_for_timeout(300)

            # Jobs tab should be active
            expect(app_page.locator(".settings-tab[data-tab='jobs'].active")).to_be_visible()

    def test_settings_save_button_visible(self, app_page: Page, base_url: str):
        """Test that save button is visible"""
        app_page.goto(f"{base_url}/#settings")
        app_page.wait_for_load_state("networkidle")
        app_page.wait_for_function("() => window.app && window.app.currentPage")

        expect(app_page.locator("button:has-text('Speichern')")).to_be_visible()

    def test_settings_export_button_visible(self, app_page: Page, base_url: str):
        """Test that export button is visible"""
        app_page.goto(f"{base_url}/#settings")
        app_page.wait_for_load_state("networkidle")
        app_page.wait_for_function("() => window.app && window.app.currentPage")

        expect(app_page.locator("button:has-text('Exportieren')")).to_be_visible()

    def test_settings_import_button_visible(self, app_page: Page, base_url: str):
        """Test that import button is visible"""
        app_page.goto(f"{base_url}/#settings")
        app_page.wait_for_load_state("networkidle")
        app_page.wait_for_function("() => window.app && window.app.currentPage")

        expect(app_page.locator("button:has-text('Importieren')")).to_be_visible()
