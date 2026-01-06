"""
E2E tests for Printernizer Timelapses Page
"""
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.pages.timelapses_page import TimelapsesPage


@pytest.mark.e2e
@pytest.mark.playwright
class TestTimelapsesPage:
    """Test suite for the Timelapses page"""

    def test_timelapses_page_loads(self, app_page: Page, base_url: str):
        """Test that the timelapses page loads successfully"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)

        assert timelapses.is_loaded(), "Timelapses page should load successfully"
        expect(app_page.locator("#timelapses.page.active h1")).to_contain_text("Zeitraffer")

    def test_status_filter_dropdown_visible(self, app_page: Page, base_url: str):
        """Test that status filter dropdown is visible"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)

        expect(app_page.locator(timelapses.status_filter_selector)).to_be_visible()

    def test_status_filter_options(self, app_page: Page, base_url: str):
        """Test that status filter has all expected options"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)

        # Click to open dropdown and check options
        filter_element = app_page.locator(timelapses.status_filter_selector)
        options = filter_element.locator("option").all()

        option_values = [opt.get_attribute("value") for opt in options]
        expected_values = ["", "discovered", "pending", "processing", "completed", "failed"]
        for val in expected_values:
            assert val in option_values, f"Status filter should have '{val}' option"

    def test_status_filter_changes_display(self, app_page: Page, base_url: str):
        """Test that changing status filter updates the display"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)
        timelapses.wait_for_loading_complete()

        # Select 'completed' status
        timelapses.filter_by_status("completed")

        # Verify filter was applied (value changed)
        filter_value = app_page.locator(timelapses.status_filter_selector).input_value()
        assert filter_value == "completed"

    def test_linked_only_checkbox_visible(self, app_page: Page, base_url: str):
        """Test that linked-only checkbox is visible"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)

        expect(app_page.locator(timelapses.linked_only_checkbox_selector)).to_be_visible()

    def test_linked_only_checkbox_toggle(self, app_page: Page, base_url: str):
        """Test that linked-only checkbox can be toggled"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)

        initial_state = timelapses.is_linked_only_checked()
        timelapses.toggle_linked_only()
        new_state = timelapses.is_linked_only_checked()

        assert initial_state != new_state, "Checkbox should toggle"

    def test_settings_button_visible(self, app_page: Page, base_url: str):
        """Test that settings button is visible"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)

        expect(app_page.locator(timelapses.settings_button_selector)).to_be_visible()

    def test_refresh_button_visible(self, app_page: Page, base_url: str):
        """Test that refresh button is visible"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)

        expect(app_page.locator(timelapses.refresh_button_selector)).to_be_visible()

    def test_refresh_button_click(self, app_page: Page, base_url: str):
        """Test that clicking refresh button reloads data"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)
        timelapses.wait_for_loading_complete()

        # Click refresh and verify no errors
        timelapses.click_refresh_button()
        app_page.wait_for_timeout(1000)

        # Page should still be loaded
        assert timelapses.is_loaded()

    def test_stats_bar_visible(self, app_page: Page, base_url: str):
        """Test that stats bar is visible"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)

        timelapses.expect_stats_bar_visible()

    def test_stats_bar_elements(self, app_page: Page, base_url: str):
        """Test that all stats bar elements are present"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)
        timelapses.wait_for_loading_complete()

        # Check each stat element
        expect(app_page.locator(timelapses.stat_total_videos_selector)).to_be_visible()
        expect(app_page.locator(timelapses.stat_processing_selector)).to_be_visible()
        expect(app_page.locator(timelapses.stat_completed_selector)).to_be_visible()
        expect(app_page.locator(timelapses.stat_storage_size_selector)).to_be_visible()
        expect(app_page.locator(timelapses.stat_cleanup_candidates_selector)).to_be_visible()

    def test_timelapses_grid_visible(self, app_page: Page, base_url: str):
        """Test that timelapses grid container is visible"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)

        expect(app_page.locator(timelapses.timelapses_grid_selector)).to_be_visible()

    @pytest.mark.slow
    def test_timelapse_card_play_button(self, app_page: Page, base_url: str):
        """Test that play button opens video modal (if timelapses exist)"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)
        timelapses.wait_for_loading_complete()

        card_count = timelapses.get_timelapse_count()
        if card_count > 0:
            timelapses.play_timelapse(0)
            assert timelapses.is_video_modal_open(), "Video modal should open"
            timelapses.close_video_modal()
            assert not timelapses.is_video_modal_open(), "Video modal should close"

    @pytest.mark.slow
    def test_video_modal_controls(self, app_page: Page, base_url: str):
        """Test video modal has expected controls (if timelapses exist)"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)
        timelapses.wait_for_loading_complete()

        card_count = timelapses.get_timelapse_count()
        if card_count > 0:
            # Find a completed timelapse to play
            timelapses.filter_by_status("completed")
            app_page.wait_for_timeout(500)

            if timelapses.get_timelapse_count() > 0:
                timelapses.play_timelapse(0)
                timelapses.expect_video_modal_open()

                # Check for download button
                expect(app_page.locator(timelapses.download_video_button_selector)).to_be_visible()

                timelapses.close_video_modal()


@pytest.mark.e2e
@pytest.mark.playwright
class TestTimelapsesFilters:
    """Test suite for Timelapses filtering functionality"""

    def test_filter_discovered(self, app_page: Page, base_url: str):
        """Test filtering by discovered status"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)
        timelapses.wait_for_loading_complete()

        timelapses.filter_by_status("discovered")
        assert app_page.locator(timelapses.status_filter_selector).input_value() == "discovered"

    def test_filter_pending(self, app_page: Page, base_url: str):
        """Test filtering by pending status"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)
        timelapses.wait_for_loading_complete()

        timelapses.filter_by_status("pending")
        assert app_page.locator(timelapses.status_filter_selector).input_value() == "pending"

    def test_filter_processing(self, app_page: Page, base_url: str):
        """Test filtering by processing status"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)
        timelapses.wait_for_loading_complete()

        timelapses.filter_by_status("processing")
        assert app_page.locator(timelapses.status_filter_selector).input_value() == "processing"

    def test_filter_completed(self, app_page: Page, base_url: str):
        """Test filtering by completed status"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)
        timelapses.wait_for_loading_complete()

        timelapses.filter_by_status("completed")
        assert app_page.locator(timelapses.status_filter_selector).input_value() == "completed"

    def test_filter_failed(self, app_page: Page, base_url: str):
        """Test filtering by failed status"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)
        timelapses.wait_for_loading_complete()

        timelapses.filter_by_status("failed")
        assert app_page.locator(timelapses.status_filter_selector).input_value() == "failed"

    def test_filter_all(self, app_page: Page, base_url: str):
        """Test clearing filter to show all"""
        timelapses = TimelapsesPage(app_page)
        timelapses.navigate(base_url)
        timelapses.wait_for_loading_complete()

        # First filter, then clear
        timelapses.filter_by_status("completed")
        timelapses.filter_by_status("")

        assert app_page.locator(timelapses.status_filter_selector).input_value() == ""
