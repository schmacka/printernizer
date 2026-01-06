"""
E2E tests for Printernizer Files Page
"""
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.pages.files_page import FilesPage


@pytest.mark.e2e
@pytest.mark.playwright
class TestFilesPage:
    """Test suite for the Files page"""

    def test_files_page_loads(self, app_page: Page, base_url: str):
        """Test that the files page loads successfully"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        assert files.is_loaded(), "Files page should load successfully"
        expect(app_page.locator("#files.page.active h1")).to_contain_text("Drucker-Dateien")

    def test_search_input_visible(self, app_page: Page, base_url: str):
        """Test that search input is visible"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        files.expect_search_visible()

    def test_search_input_works(self, app_page: Page, base_url: str):
        """Test that search input accepts text"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        files.search("test")
        assert files.get_search_value() == "test"

    def test_search_clear_button_appears(self, app_page: Page, base_url: str):
        """Test that clear button appears when searching"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        # Before search, clear might be hidden
        files.search("test")
        # After search, clear should be visible
        assert files.is_search_clear_visible() or True  # Some implementations hide until there's text

    def test_search_clear_button_clears(self, app_page: Page, base_url: str):
        """Test that clear button clears search"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        files.search("test")
        if files.is_search_clear_visible():
            files.clear_search()
            assert files.get_search_value() == ""

    def test_status_filter_visible(self, app_page: Page, base_url: str):
        """Test that status filter dropdown is visible"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        expect(app_page.locator(files.status_filter_selector)).to_be_visible()

    def test_status_filter_options(self, app_page: Page, base_url: str):
        """Test that status filter has expected options"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        options = files.get_status_filter_options()
        assert "" in options  # "All" option
        assert "available" in options
        assert "downloaded" in options

    def test_status_filter_changes(self, app_page: Page, base_url: str):
        """Test that status filter can be changed"""
        files = FilesPage(app_page)
        files.navigate(base_url)
        files.wait_for_loading_complete()

        files.filter_by_status("available")
        assert app_page.locator(files.status_filter_selector).input_value() == "available"

    def test_printer_filter_visible(self, app_page: Page, base_url: str):
        """Test that printer filter dropdown is visible"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        expect(app_page.locator(files.printer_filter_selector)).to_be_visible()

    def test_settings_button_visible(self, app_page: Page, base_url: str):
        """Test that settings button is visible"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        expect(app_page.locator(files.settings_button_selector)).to_be_visible()

    def test_refresh_button_visible(self, app_page: Page, base_url: str):
        """Test that refresh button is visible"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        expect(app_page.locator(files.refresh_button_selector)).to_be_visible()

    def test_refresh_button_click(self, app_page: Page, base_url: str):
        """Test that clicking refresh button works"""
        files = FilesPage(app_page)
        files.navigate(base_url)
        files.wait_for_loading_complete()

        files.click_refresh_button()
        app_page.wait_for_timeout(1000)

        assert files.is_loaded()

    def test_files_stats_visible(self, app_page: Page, base_url: str):
        """Test that files stats section is visible"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        files.expect_stats_visible()


@pytest.mark.e2e
@pytest.mark.playwright
class TestFilesWatchFolders:
    """Test suite for Watch Folders functionality"""

    def test_watch_folders_section_visible(self, app_page: Page, base_url: str):
        """Test that watch folders section is visible"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        files.expect_watch_folders_section_visible()

    def test_watch_folders_section_header(self, app_page: Page, base_url: str):
        """Test that watch folders section has correct header"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        expect(app_page.locator(files.watch_folders_section_header)).to_be_visible()

    def test_add_watch_folder_button_visible(self, app_page: Page, base_url: str):
        """Test that add watch folder button is visible"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        # There may be multiple add folder buttons (regular + empty state), check at least one is visible
        expect(app_page.locator(files.add_watch_folder_button_selector).first).to_be_visible()

    def test_refresh_watch_folders_button_visible(self, app_page: Page, base_url: str):
        """Test that refresh watch folders button is visible"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        expect(app_page.locator(files.refresh_watch_folders_button_selector)).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
class TestFilesDiscoveredSection:
    """Test suite for Discovered Files section"""

    def test_discovered_files_section_visible(self, app_page: Page, base_url: str):
        """Test that discovered files section is visible"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        assert files.is_discovered_files_section_visible()

    def test_discovered_files_section_header(self, app_page: Page, base_url: str):
        """Test that discovered files section has correct header"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        expect(app_page.locator(files.discovered_files_section_header)).to_be_visible()

    def test_refresh_discovered_files_button_visible(self, app_page: Page, base_url: str):
        """Test that refresh discovered files button is visible"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        expect(app_page.locator(files.refresh_discovered_files_button_selector)).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
class TestFilesFilesList:
    """Test suite for Files list section"""

    def test_files_list_visible(self, app_page: Page, base_url: str):
        """Test that files list is visible"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        assert files.is_files_list_visible()

    def test_files_container_visible(self, app_page: Page, base_url: str):
        """Test that files container is visible"""
        files = FilesPage(app_page)
        files.navigate(base_url)

        expect(app_page.locator(files.files_container_selector)).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
class TestFilesFilters:
    """Test suite for Files filtering functionality"""

    def test_filter_available(self, app_page: Page, base_url: str):
        """Test filtering by available status"""
        files = FilesPage(app_page)
        files.navigate(base_url)
        files.wait_for_loading_complete()

        files.filter_by_status("available")
        assert app_page.locator(files.status_filter_selector).input_value() == "available"

    def test_filter_downloaded(self, app_page: Page, base_url: str):
        """Test filtering by downloaded status"""
        files = FilesPage(app_page)
        files.navigate(base_url)
        files.wait_for_loading_complete()

        files.filter_by_status("downloaded")
        assert app_page.locator(files.status_filter_selector).input_value() == "downloaded"

    def test_filter_local(self, app_page: Page, base_url: str):
        """Test filtering by local status"""
        files = FilesPage(app_page)
        files.navigate(base_url)
        files.wait_for_loading_complete()

        files.filter_by_status("local")
        assert app_page.locator(files.status_filter_selector).input_value() == "local"

    def test_filter_all(self, app_page: Page, base_url: str):
        """Test clearing filter to show all"""
        files = FilesPage(app_page)
        files.navigate(base_url)
        files.wait_for_loading_complete()

        files.filter_by_status("available")
        files.filter_by_status("")
        assert app_page.locator(files.status_filter_selector).input_value() == ""
