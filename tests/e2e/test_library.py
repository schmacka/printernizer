"""
E2E tests for Printernizer Library Page
"""
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.pages.library_page import LibraryPage


@pytest.mark.e2e
@pytest.mark.playwright
class TestLibraryPage:
    """Test suite for the Library page"""

    def test_library_page_loads(self, app_page: Page, base_url: str):
        """Test that the library page loads successfully"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        assert library.is_loaded(), "Library page should load successfully"
        expect(app_page.locator("#library.page.active h1")).to_contain_text("Bibliothek")

    def test_search_input_visible(self, app_page: Page, base_url: str):
        """Test that search input is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        expect(app_page.locator(library.search_input_selector)).to_be_visible()

    def test_search_input_works(self, app_page: Page, base_url: str):
        """Test that search input accepts text"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        library.search("benchy")
        assert library.get_input_value(library.search_input_selector) == "benchy"

    def test_upload_button_visible(self, app_page: Page, base_url: str):
        """Test that upload button is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        expect(app_page.locator(library.upload_button_selector)).to_be_visible()

    def test_refresh_button_visible(self, app_page: Page, base_url: str):
        """Test that refresh button is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        expect(app_page.locator(library.refresh_button_selector)).to_be_visible()

    def test_settings_button_visible(self, app_page: Page, base_url: str):
        """Test that settings button is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        expect(app_page.locator(library.settings_button_selector)).to_be_visible()

    def test_refresh_button_click(self, app_page: Page, base_url: str):
        """Test that clicking refresh button works"""
        library = LibraryPage(app_page)
        library.navigate(base_url)
        library.wait_for_loading_complete()

        library.click_refresh_button()
        app_page.wait_for_timeout(1000)

        assert library.is_loaded()


@pytest.mark.e2e
@pytest.mark.playwright
class TestLibraryStats:
    """Test suite for Library statistics"""

    def test_stats_visible(self, app_page: Page, base_url: str):
        """Test that stats section is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        library.expect_stats_visible()

    def test_stat_total_files_visible(self, app_page: Page, base_url: str):
        """Test that total files stat is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)
        library.wait_for_loading_complete()

        expect(app_page.locator(library.stat_total_files_selector)).to_be_visible()

    def test_stat_total_size_visible(self, app_page: Page, base_url: str):
        """Test that total size stat is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)
        library.wait_for_loading_complete()

        expect(app_page.locator(library.stat_total_size_selector)).to_be_visible()

    def test_stat_with_thumbnails_visible(self, app_page: Page, base_url: str):
        """Test that thumbnails stat is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)
        library.wait_for_loading_complete()

        expect(app_page.locator(library.stat_with_thumbnails_selector)).to_be_visible()

    def test_stat_analyzed_visible(self, app_page: Page, base_url: str):
        """Test that analyzed stat is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)
        library.wait_for_loading_complete()

        expect(app_page.locator(library.stat_analyzed_selector)).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
class TestLibraryFilters:
    """Test suite for Library filtering functionality"""

    def test_filter_bar_visible(self, app_page: Page, base_url: str):
        """Test that filter bar is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        library.expect_filters_visible()

    def test_filter_source_type_visible(self, app_page: Page, base_url: str):
        """Test that source type filter is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        expect(app_page.locator(library.filter_source_type_selector)).to_be_visible()

    def test_filter_source_type_works(self, app_page: Page, base_url: str):
        """Test that source type filter can be changed"""
        library = LibraryPage(app_page)
        library.navigate(base_url)
        library.wait_for_loading_complete()

        library.filter_by_source_type("printer")
        assert app_page.locator(library.filter_source_type_selector).input_value() == "printer"

    def test_filter_file_type_visible(self, app_page: Page, base_url: str):
        """Test that file type filter is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        expect(app_page.locator(library.filter_file_type_selector)).to_be_visible()

    def test_filter_file_type_works(self, app_page: Page, base_url: str):
        """Test that file type filter can be changed"""
        library = LibraryPage(app_page)
        library.navigate(base_url)
        library.wait_for_loading_complete()

        library.filter_by_file_type(".3mf")
        assert app_page.locator(library.filter_file_type_selector).input_value() == ".3mf"

    def test_filter_status_visible(self, app_page: Page, base_url: str):
        """Test that status filter is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        expect(app_page.locator(library.filter_status_selector)).to_be_visible()

    def test_filter_status_works(self, app_page: Page, base_url: str):
        """Test that status filter can be changed"""
        library = LibraryPage(app_page)
        library.navigate(base_url)
        library.wait_for_loading_complete()

        library.filter_by_status("available")
        assert app_page.locator(library.filter_status_selector).input_value() == "available"

    def test_filter_metadata_visible(self, app_page: Page, base_url: str):
        """Test that metadata filter is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        expect(app_page.locator(library.filter_metadata_selector)).to_be_visible()

    def test_filter_metadata_works(self, app_page: Page, base_url: str):
        """Test that metadata filter can be changed"""
        library = LibraryPage(app_page)
        library.navigate(base_url)
        library.wait_for_loading_complete()

        library.filter_by_metadata("has_thumbnail")
        assert app_page.locator(library.filter_metadata_selector).input_value() == "has_thumbnail"

    def test_filter_tag_visible(self, app_page: Page, base_url: str):
        """Test that tag filter is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        expect(app_page.locator(library.filter_tag_selector)).to_be_visible()

    def test_sort_by_visible(self, app_page: Page, base_url: str):
        """Test that sort dropdown is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        expect(app_page.locator(library.sort_by_selector)).to_be_visible()

    def test_sort_by_works(self, app_page: Page, base_url: str):
        """Test that sort can be changed"""
        library = LibraryPage(app_page)
        library.navigate(base_url)
        library.wait_for_loading_complete()

        library.sort_by("filename:asc")
        assert app_page.locator(library.sort_by_selector).input_value() == "filename:asc"


@pytest.mark.e2e
@pytest.mark.playwright
class TestLibraryGrid:
    """Test suite for Library grid display"""

    def test_library_grid_visible(self, app_page: Page, base_url: str):
        """Test that library grid is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        expect(app_page.locator(library.library_files_grid_selector)).to_be_visible()

    def test_library_container_visible(self, app_page: Page, base_url: str):
        """Test that library container is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        expect(app_page.locator(library.library_container_selector)).to_be_visible()

    @pytest.mark.slow
    def test_file_card_click_opens_modal(self, app_page: Page, base_url: str):
        """Test that clicking a file card opens the detail modal"""
        library = LibraryPage(app_page)
        library.navigate(base_url)
        library.wait_for_loading_complete()

        file_count = library.get_file_count()
        if file_count > 0:
            library.click_file_card(0)
            library.expect_file_detail_modal_open()
            library.close_file_detail_modal()
            library.expect_file_detail_modal_closed()


@pytest.mark.e2e
@pytest.mark.playwright
class TestLibraryPagination:
    """Test suite for Library pagination"""

    def test_pagination_visible(self, app_page: Page, base_url: str):
        """Test that pagination is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        library.expect_pagination_visible()

    def test_page_size_selector_visible(self, app_page: Page, base_url: str):
        """Test that page size selector is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        expect(app_page.locator(library.page_size_select_selector)).to_be_visible()

    def test_page_size_change(self, app_page: Page, base_url: str):
        """Test that page size can be changed"""
        library = LibraryPage(app_page)
        library.navigate(base_url)
        library.wait_for_loading_complete()

        library.set_page_size("25")
        assert app_page.locator(library.page_size_select_selector).input_value() == "25"

    def test_pagination_info_visible(self, app_page: Page, base_url: str):
        """Test that pagination info is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        expect(app_page.locator(library.pagination_info_selector)).to_be_visible()

    def test_prev_page_button_visible(self, app_page: Page, base_url: str):
        """Test that prev page button is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        expect(app_page.locator(library.prev_page_button_selector)).to_be_visible()

    def test_next_page_button_visible(self, app_page: Page, base_url: str):
        """Test that next page button is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        expect(app_page.locator(library.next_page_button_selector)).to_be_visible()

    def test_current_page_info_visible(self, app_page: Page, base_url: str):
        """Test that current page info is visible"""
        library = LibraryPage(app_page)
        library.navigate(base_url)

        expect(app_page.locator(library.current_page_info_selector)).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
class TestLibraryFileDetailModal:
    """Test suite for Library file detail modal"""

    @pytest.mark.slow
    def test_file_detail_modal_opens(self, app_page: Page, base_url: str):
        """Test that file detail modal opens when clicking a card"""
        library = LibraryPage(app_page)
        library.navigate(base_url)
        library.wait_for_loading_complete()

        if library.get_file_count() > 0:
            library.click_file_card(0)
            assert library.is_file_detail_modal_open()
            library.close_file_detail_modal()

    @pytest.mark.slow
    def test_file_detail_modal_closes(self, app_page: Page, base_url: str):
        """Test that file detail modal closes properly"""
        library = LibraryPage(app_page)
        library.navigate(base_url)
        library.wait_for_loading_complete()

        if library.get_file_count() > 0:
            library.click_file_card(0)
            library.expect_file_detail_modal_open()
            library.close_file_detail_modal()
            library.expect_file_detail_modal_closed()

    @pytest.mark.slow
    def test_file_detail_modal_has_content(self, app_page: Page, base_url: str):
        """Test that file detail modal has content"""
        library = LibraryPage(app_page)
        library.navigate(base_url)
        library.wait_for_loading_complete()

        if library.get_file_count() > 0:
            library.click_file_card(0)
            expect(app_page.locator(library.file_detail_content_selector)).to_be_visible()
            library.close_file_detail_modal()
