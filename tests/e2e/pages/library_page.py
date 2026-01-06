"""
Page Object Model for Printernizer Library Page
"""
from playwright.sync_api import Page, expect
from typing import Optional, List
from .base_page import BasePage


class LibraryPage(BasePage):
    """Page object for the library page"""

    def __init__(self, page: Page):
        super().__init__(page)
        self.page_hash = "library"
        self.page_selector = "#library.page.active"

        # Header selectors
        self.title_selector = "h1:has-text('Bibliothek')"
        self.subtitle_selector = ".header-subtitle"

        # Search selectors
        self.search_input_selector = "#librarySearchInput"
        self.search_clear_button_selector = "#librarySearchClear"

        # Action buttons
        self.settings_button_selector = "#library button:has-text('Einstellungen')"
        self.upload_button_selector = "button:has-text('Hochladen')"
        self.refresh_button_selector = "#library .page-header button:has-text('Aktualisieren')"
        self.file_input_selector = "#libraryFileInput"

        # Statistics selectors
        self.stats_container_selector = "#libraryStats, .library-stats-container"
        self.stat_total_files_selector = "#statTotalFiles"
        self.stat_total_size_selector = "#statTotalSize"
        self.stat_with_thumbnails_selector = "#statWithThumbnails"
        self.stat_analyzed_selector = "#statAnalyzed"

        # Filter selectors - scope to library page
        self.filter_bar_selector = "#library.page.active .filter-bar"
        self.filter_source_type_selector = "#filterSourceType"
        self.filter_file_type_selector = "#filterFileType"
        self.filter_status_selector = "#filterStatus"
        self.filter_metadata_selector = "#filterMetadata"
        self.filter_tag_selector = "#filterTag"
        self.sort_by_selector = "#sortBy"

        # Library grid selectors
        self.library_container_selector = ".library-container"
        self.library_files_grid_selector = "#libraryFilesGrid"
        self.library_file_card_selector = ".library-file-card"

        # Pagination selectors
        self.pagination_container_selector = ".pagination-container"
        self.page_size_select_selector = "#pageSizeSelect"
        self.pagination_info_selector = "#paginationInfo"
        self.prev_page_button_selector = "#prevPageBtn"
        self.next_page_button_selector = "#nextPageBtn"
        self.current_page_info_selector = "#currentPageInfo"

        # File detail modal selectors
        self.file_detail_modal_selector = "#fileDetailModal"
        self.file_detail_content_selector = "#fileDetailContent"
        self.close_file_detail_button_selector = "#closeFileDetailModal"
        self.reprocess_file_button_selector = "#reprocessFileBtn, button:has-text('Neu analysieren')"
        self.download_file_button_selector = "button:has-text('Download')"
        self.delete_file_button_selector = "button:has-text('Löschen')"

        # Empty state
        self.empty_state_selector = ".empty-state, .no-files"

    def search(self, query: str):
        """Search in library"""
        self.fill_input(self.search_input_selector, query)
        self.page.wait_for_timeout(500)

    def clear_search(self):
        """Clear the search input"""
        clear_btn = self.page.locator(self.search_clear_button_selector)
        if clear_btn.is_visible():
            clear_btn.click()
            self.page.wait_for_timeout(300)

    def filter_by_source_type(self, source: str):
        """Filter by source type"""
        self.select_option(self.filter_source_type_selector, source)
        self.page.wait_for_timeout(500)

    def filter_by_file_type(self, file_type: str):
        """Filter by file type"""
        self.select_option(self.filter_file_type_selector, file_type)
        self.page.wait_for_timeout(500)

    def filter_by_status(self, status: str):
        """Filter by status"""
        self.select_option(self.filter_status_selector, status)
        self.page.wait_for_timeout(500)

    def filter_by_metadata(self, metadata: str):
        """Filter by metadata"""
        self.select_option(self.filter_metadata_selector, metadata)
        self.page.wait_for_timeout(500)

    def filter_by_tag(self, tag: str):
        """Filter by tag"""
        self.select_option(self.filter_tag_selector, tag)
        self.page.wait_for_timeout(500)

    def sort_by(self, sort_option: str):
        """Change sort order"""
        self.select_option(self.sort_by_selector, sort_option)
        self.page.wait_for_timeout(500)

    def click_upload(self):
        """Click upload button"""
        self.page.click(self.upload_button_selector)
        self.page.wait_for_timeout(300)

    def get_file_count(self) -> int:
        """Get the number of files displayed"""
        return self.page.locator(self.library_file_card_selector).count()

    def click_file_card(self, index: int = 0):
        """Click on a file card to open details"""
        cards = self.page.locator(self.library_file_card_selector).all()
        if len(cards) > index:
            cards[index].click()
            self.page.wait_for_selector(self.file_detail_modal_selector, state="visible", timeout=5000)

    def close_file_detail_modal(self):
        """Close the file detail modal"""
        self.page.click(self.close_file_detail_button_selector)
        self.page.wait_for_selector(self.file_detail_modal_selector, state="hidden", timeout=5000)

    def is_file_detail_modal_open(self) -> bool:
        """Check if file detail modal is open"""
        return self.page.locator(self.file_detail_modal_selector).is_visible()

    def click_reprocess(self):
        """Click reprocess button in modal"""
        self.page.click(self.reprocess_file_button_selector)
        self.page.wait_for_timeout(500)

    def click_download(self):
        """Click download button in modal"""
        self.page.click(self.download_file_button_selector)

    def click_delete(self, confirm: bool = True):
        """Click delete button in modal"""
        if confirm:
            self.page.on("dialog", lambda dialog: dialog.accept())
        else:
            self.page.on("dialog", lambda dialog: dialog.dismiss())
        self.page.click(self.delete_file_button_selector)
        self.page.wait_for_timeout(500)

    def go_to_prev_page(self):
        """Go to previous page"""
        btn = self.page.locator(self.prev_page_button_selector)
        if btn.is_enabled():
            btn.click()
            self.page.wait_for_timeout(500)

    def go_to_next_page(self):
        """Go to next page"""
        btn = self.page.locator(self.next_page_button_selector)
        if btn.is_enabled():
            btn.click()
            self.page.wait_for_timeout(500)

    def set_page_size(self, size: str):
        """Set page size"""
        self.select_option(self.page_size_select_selector, size)
        self.page.wait_for_timeout(500)

    def is_prev_page_enabled(self) -> bool:
        """Check if previous page button is enabled"""
        return self.page.locator(self.prev_page_button_selector).is_enabled()

    def is_next_page_enabled(self) -> bool:
        """Check if next page button is enabled"""
        return self.page.locator(self.next_page_button_selector).is_enabled()

    def get_pagination_info(self) -> str:
        """Get pagination info text"""
        return self.page.locator(self.pagination_info_selector).inner_text()

    def get_current_page_info(self) -> str:
        """Get current page info text"""
        return self.page.locator(self.current_page_info_selector).inner_text()

    def get_stats(self) -> dict:
        """Get all library stats"""
        return {
            "total_files": self.get_element_text(self.stat_total_files_selector),
            "total_size": self.get_element_text(self.stat_total_size_selector),
            "with_thumbnails": self.get_element_text(self.stat_with_thumbnails_selector),
            "analyzed": self.get_element_text(self.stat_analyzed_selector),
        }

    def expect_stats_visible(self):
        """Assert that stats are visible"""
        expect(self.page.locator(self.stats_container_selector)).to_be_visible()

    def expect_filters_visible(self):
        """Assert that filter bar is visible"""
        expect(self.page.locator(self.filter_bar_selector)).to_be_visible()

    def expect_pagination_visible(self):
        """Assert that pagination is visible"""
        expect(self.page.locator(self.pagination_container_selector)).to_be_visible()

    def expect_file_count(self, count: int):
        """Assert the number of files displayed"""
        expect(self.page.locator(self.library_file_card_selector)).to_have_count(count)

    def expect_file_detail_modal_open(self):
        """Assert that file detail modal is open"""
        expect(self.page.locator(self.file_detail_modal_selector)).to_be_visible()

    def expect_file_detail_modal_closed(self):
        """Assert that file detail modal is closed"""
        expect(self.page.locator(self.file_detail_modal_selector)).to_be_hidden()
