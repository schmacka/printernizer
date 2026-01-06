"""
E2E tests for Printernizer Debug Page
"""
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.pages.debug_page import DebugPage


@pytest.mark.e2e
@pytest.mark.playwright
class TestDebugPage:
    """Test suite for the Debug page"""

    def test_debug_page_loads(self, app_page: Page, base_url: str):
        """Test that the debug page loads successfully"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)

        assert debug.is_loaded(), "Debug page should load successfully"
        expect(app_page.locator("#debug.page.active h1")).to_contain_text("Debug")

    def test_refresh_button_visible(self, app_page: Page, base_url: str):
        """Test that refresh button is visible"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)

        expect(app_page.locator(debug.refresh_button_selector)).to_be_visible()

    def test_clear_logs_button_visible(self, app_page: Page, base_url: str):
        """Test that clear logs button is visible"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)

        expect(app_page.locator(debug.clear_logs_button_selector)).to_be_visible()

    def test_download_logs_button_visible(self, app_page: Page, base_url: str):
        """Test that download logs button is visible"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)

        expect(app_page.locator(debug.download_logs_button_selector)).to_be_visible()

    def test_refresh_button_click(self, app_page: Page, base_url: str):
        """Test that clicking refresh works"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)
        debug.wait_for_loading_complete()

        debug.click_refresh_button()
        app_page.wait_for_timeout(1000)

        assert debug.is_loaded()

    def test_debug_container_visible(self, app_page: Page, base_url: str):
        """Test that debug container is visible"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)

        expect(app_page.locator(debug.debug_container_selector)).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
class TestDebugHealthSection:
    """Test suite for Debug Health section"""

    def test_health_section_visible(self, app_page: Page, base_url: str):
        """Test that health section is visible"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)

        debug.expect_health_section_visible()

    def test_health_info_visible(self, app_page: Page, base_url: str):
        """Test that health info container is visible"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)
        debug.wait_for_loading_complete()

        expect(app_page.locator(debug.health_info_selector)).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
class TestDebugLogsSection:
    """Test suite for Debug Logs section"""

    def test_logs_section_visible(self, app_page: Page, base_url: str):
        """Test that logs section is visible"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)

        debug.expect_logs_section_visible()

    def test_log_viewer_visible(self, app_page: Page, base_url: str):
        """Test that log viewer is visible"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)
        debug.wait_for_loading_complete()

        expect(app_page.locator(debug.log_viewer_selector)).to_be_visible()

    def test_log_level_filter_visible(self, app_page: Page, base_url: str):
        """Test that log level filter is visible"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)

        expect(app_page.locator(debug.log_level_filter_selector)).to_be_visible()

    def test_log_level_filter_options(self, app_page: Page, base_url: str):
        """Test that log level filter has expected options"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)

        options = debug.get_log_level_filter_options()
        assert "" in options  # All option
        assert "ERROR" in options
        assert "WARNING" in options
        assert "INFO" in options
        assert "DEBUG" in options

    def test_log_level_filter_change(self, app_page: Page, base_url: str):
        """Test that log level filter can be changed"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)
        debug.wait_for_loading_complete()

        debug.filter_log_level("ERROR")
        assert app_page.locator(debug.log_level_filter_selector).input_value() == "ERROR"

    def test_auto_refresh_checkbox_visible(self, app_page: Page, base_url: str):
        """Test that auto-refresh checkbox is visible"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)

        expect(app_page.locator(debug.auto_refresh_checkbox_selector)).to_be_visible()

    def test_auto_refresh_toggle(self, app_page: Page, base_url: str):
        """Test that auto-refresh can be toggled"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)

        initial_state = debug.is_auto_refresh_checked()
        debug.toggle_auto_refresh()
        new_state = debug.is_auto_refresh_checked()

        assert initial_state != new_state, "Auto-refresh should toggle"


@pytest.mark.e2e
@pytest.mark.playwright
class TestDebugPerformanceSection:
    """Test suite for Debug Performance section"""

    def test_performance_section_visible(self, app_page: Page, base_url: str):
        """Test that performance section is visible"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)

        debug.expect_performance_section_visible()

    def test_performance_metrics_visible(self, app_page: Page, base_url: str):
        """Test that performance metrics container is visible"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)
        debug.wait_for_loading_complete()

        expect(app_page.locator(debug.performance_metrics_selector)).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
class TestDebugThumbnailSection:
    """Test suite for Debug Thumbnail Processing section"""

    def test_thumbnail_section_visible(self, app_page: Page, base_url: str):
        """Test that thumbnail section is visible"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)

        debug.expect_thumbnail_section_visible()

    def test_thumbnail_log_visible(self, app_page: Page, base_url: str):
        """Test that thumbnail log container is visible"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)
        debug.wait_for_loading_complete()

        expect(app_page.locator(debug.thumbnail_log_selector)).to_be_visible()

    def test_thumbnail_log_limit_visible(self, app_page: Page, base_url: str):
        """Test that thumbnail log limit selector is visible"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)

        expect(app_page.locator(debug.thumbnail_log_limit_selector)).to_be_visible()

    def test_thumbnail_log_limit_options(self, app_page: Page, base_url: str):
        """Test that thumbnail log limit has expected options"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)

        options = debug.get_thumbnail_limit_options()
        assert "10" in options
        assert "20" in options
        assert "50" in options

    def test_thumbnail_log_limit_change(self, app_page: Page, base_url: str):
        """Test that thumbnail log limit can be changed"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)
        debug.wait_for_loading_complete()

        debug.set_thumbnail_log_limit("50")
        assert app_page.locator(debug.thumbnail_log_limit_selector).input_value() == "50"


@pytest.mark.e2e
@pytest.mark.playwright
class TestDebugAllSections:
    """Test suite for all Debug sections together"""

    def test_all_sections_visible(self, app_page: Page, base_url: str):
        """Test that all debug sections are visible"""
        debug = DebugPage(app_page)
        debug.navigate(base_url)
        debug.wait_for_loading_complete()

        debug.expect_all_sections_visible()
