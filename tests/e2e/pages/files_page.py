"""
Page Object Model for Printernizer Files Page
"""
from playwright.sync_api import Page, expect
from typing import Optional, List
from .base_page import BasePage


class FilesPage(BasePage):
    """Page object for the printer files page"""

    def __init__(self, page: Page):
        super().__init__(page)
        self.page_hash = "files"
        self.page_selector = "#files.page.active"

        # Header selectors
        self.title_selector = "h1:has-text('Drucker-Dateien')"

        # Search selectors
        self.search_input_selector = "#fileSearchInput"
        self.search_clear_button_selector = "#fileSearchClear"
        self.search_icon_selector = ".search-icon"

        # Filter selectors
        self.status_filter_selector = "#fileStatusFilter"
        self.printer_filter_selector = "#filePrinterFilter"

        # Action buttons
        self.settings_button_selector = "#files button:has-text('Einstellungen')"
        self.refresh_button_selector = "#files .page-header button:has-text('Aktualisieren')"

        # Files stats
        self.files_stats_selector = "#filesStats"

        # Watch folders section
        self.watch_folders_section_header = "#files.page.active h2:has-text('Überwachte Verzeichnisse')"
        self.watch_folders_container_selector = "#watchFoldersContainer"
        self.refresh_watch_folders_button_selector = "#files.page.active .section:has(h2:has-text('Überwachte Verzeichnisse')) button:has-text('Aktualisieren')"
        self.add_watch_folder_button_selector = "#files.page.active .section:has(h2:has-text('Überwachte Verzeichnisse')) button:has-text('Verzeichnis hinzufügen')"

        # Discovered files section
        self.discovered_files_section_header = "h2:has-text('Entdeckte Dateien')"
        self.discovered_files_container_selector = "#discoveredFilesContainer"
        self.refresh_discovered_files_button_selector = ".discovered-files-section button:has-text('Aktualisieren')"

        # Files list
        self.files_container_selector = ".files-container"
        self.files_list_selector = "#filesList"
        self.file_row_selector = ".file-row, .file-card"

        # Watch folder modal
        self.add_watch_folder_modal_selector = ".modal:has-text('Verzeichnis')"
        self.watch_folder_path_input_selector = "#watchFolderPath, input[name='path']"

        # File preview modal
        self.file_preview_modal_selector = ".modal.file-preview, #filePreviewModal"

        # Empty state
        self.empty_state_selector = ".empty-state, .no-files"

    def search(self, query: str):
        """Search for files"""
        self.fill_input(self.search_input_selector, query)
        self.page.wait_for_timeout(500)

    def clear_search(self):
        """Clear the search input"""
        clear_btn = self.page.locator(self.search_clear_button_selector)
        if clear_btn.is_visible():
            clear_btn.click()
            self.page.wait_for_timeout(300)

    def filter_by_status(self, status: str):
        """Filter files by status"""
        self.select_option(self.status_filter_selector, status)
        self.page.wait_for_timeout(500)

    def filter_by_printer(self, printer: str):
        """Filter files by printer"""
        self.select_option(self.printer_filter_selector, printer)
        self.page.wait_for_timeout(500)

    def get_file_count(self) -> int:
        """Get the number of files displayed"""
        return self.page.locator(self.file_row_selector).count()

    def get_search_value(self) -> str:
        """Get the current search input value"""
        return self.page.locator(self.search_input_selector).input_value()

    def is_search_clear_visible(self) -> bool:
        """Check if search clear button is visible"""
        return self.page.locator(self.search_clear_button_selector).is_visible()

    def click_add_watch_folder(self):
        """Click add watch folder button"""
        self.page.click(self.add_watch_folder_button_selector)
        self.page.wait_for_timeout(300)

    def refresh_watch_folders(self):
        """Click refresh watch folders button"""
        self.page.click(self.refresh_watch_folders_button_selector)
        self.page.wait_for_timeout(500)

    def refresh_discovered_files(self):
        """Click refresh discovered files button"""
        self.page.click(self.refresh_discovered_files_button_selector)
        self.page.wait_for_timeout(500)

    def click_file(self, index: int = 0):
        """Click on a file to open preview"""
        files = self.page.locator(self.file_row_selector).all()
        if len(files) > index:
            files[index].click()
            self.page.wait_for_timeout(300)

    def get_status_filter_options(self) -> List[str]:
        """Get all status filter options"""
        options = self.page.locator(f"{self.status_filter_selector} option").all()
        return [opt.get_attribute("value") for opt in options]

    def get_printer_filter_options(self) -> List[str]:
        """Get all printer filter options"""
        options = self.page.locator(f"{self.printer_filter_selector} option").all()
        return [opt.get_attribute("value") for opt in options]

    def is_watch_folders_section_visible(self) -> bool:
        """Check if watch folders section is visible"""
        return self.page.locator(self.watch_folders_container_selector).is_visible()

    def is_discovered_files_section_visible(self) -> bool:
        """Check if discovered files section is visible"""
        return self.page.locator(self.discovered_files_container_selector).is_visible()

    def is_files_list_visible(self) -> bool:
        """Check if files list is visible"""
        return self.page.locator(self.files_list_selector).is_visible()

    def expect_search_visible(self):
        """Assert that search input is visible"""
        expect(self.page.locator(self.search_input_selector)).to_be_visible()

    def expect_filters_visible(self):
        """Assert that filter dropdowns are visible"""
        expect(self.page.locator(self.status_filter_selector)).to_be_visible()
        expect(self.page.locator(self.printer_filter_selector)).to_be_visible()

    def expect_stats_visible(self):
        """Assert that files stats are visible"""
        expect(self.page.locator(self.files_stats_selector)).to_be_visible()

    def expect_watch_folders_section_visible(self):
        """Assert that watch folders section is visible"""
        expect(self.page.locator(self.watch_folders_container_selector)).to_be_visible()

    def expect_file_count(self, count: int):
        """Assert the number of files displayed"""
        expect(self.page.locator(self.file_row_selector)).to_have_count(count)
