"""
Page Object Model for Printernizer Timelapses Page
"""
from playwright.sync_api import Page, expect
from typing import Optional, List
from .base_page import BasePage


class TimelapsesPage(BasePage):
    """Page object for the timelapses/videos page"""

    def __init__(self, page: Page):
        super().__init__(page)
        self.page_hash = "timelapses"
        self.page_selector = "#timelapses.page.active"

        # Header selectors
        self.title_selector = "#timelapses.page.active h1:has-text('Zeitraffer')"
        self.status_filter_selector = "#timelapseStatusFilter"
        self.linked_only_checkbox_selector = "#timelapseLinkedOnly"
        self.settings_button_selector = "#timelapses.page.active button[onclick*='timelapse']"
        self.refresh_button_selector = "#timelapses.page.active button:has-text('Aktualisieren')"

        # Stats bar selectors
        self.stats_bar_selector = "#timelapseStats"
        self.stat_total_videos_selector = "#statTotalVideos"
        self.stat_processing_selector = "#statProcessing"
        self.stat_completed_selector = "#statCompleted"
        self.stat_storage_size_selector = "#statStorageSize"
        self.stat_cleanup_candidates_selector = "#statCleanupCandidates"

        # Processing queue selectors
        self.processing_queue_selector = "#processingQueue"
        self.queue_item_selector = "#queueItem"

        # Timelapses grid selectors
        self.timelapses_container_selector = ".timelapses-container"
        self.timelapses_grid_selector = "#timelapsesList"
        self.timelapse_card_selector = ".timelapse-card"

        # Card action selectors
        self.play_button_selector = ".timelapse-card button:has-text('Abspielen')"
        self.process_button_selector = ".timelapse-card button:has-text('Verarbeiten')"
        self.pin_button_selector = ".timelapse-card button:has-text('Anpinnen'), .timelapse-card button:has-text('Lösen')"
        self.delete_button_selector = ".timelapse-card button:has-text('Löschen')"
        self.download_button_selector = ".timelapse-card button:has-text('Download')"

        # Video player modal selectors
        self.video_modal_selector = "#videoPlayerModal"
        self.video_player_selector = "#videoPlayer"
        self.download_video_button_selector = "#downloadVideoBtn"
        self.close_video_modal_button_selector = "#videoPlayerModal .modal-close"

        # Empty state selector
        self.empty_state_selector = ".empty-state, .no-timelapses"

    def filter_by_status(self, status: str):
        """Filter timelapses by status"""
        self.select_option(self.status_filter_selector, status)
        self.page.wait_for_timeout(500)

    def toggle_linked_only(self):
        """Toggle the 'linked only' checkbox"""
        self.page.click(self.linked_only_checkbox_selector)
        self.page.wait_for_timeout(300)

    def is_linked_only_checked(self) -> bool:
        """Check if 'linked only' checkbox is checked"""
        return self.page.locator(self.linked_only_checkbox_selector).is_checked()

    def get_timelapse_count(self) -> int:
        """Get the number of timelapse cards displayed"""
        return self.page.locator(self.timelapse_card_selector).count()

    def get_stats(self) -> dict:
        """Get all stats from the stats bar"""
        return {
            "total": self.get_element_text(self.stat_total_videos_selector),
            "processing": self.get_element_text(self.stat_processing_selector),
            "completed": self.get_element_text(self.stat_completed_selector),
            "storage": self.get_element_text(self.stat_storage_size_selector),
            "cleanup": self.get_element_text(self.stat_cleanup_candidates_selector),
        }

    def click_timelapse_card(self, index: int = 0):
        """Click on a timelapse card by index"""
        cards = self.page.locator(self.timelapse_card_selector).all()
        if len(cards) > index:
            cards[index].click()

    def play_timelapse(self, index: int = 0):
        """Click play button on a timelapse card"""
        play_buttons = self.page.locator(self.play_button_selector).all()
        if len(play_buttons) > index:
            play_buttons[index].click()
            self.page.wait_for_selector(self.video_modal_selector, state="visible", timeout=5000)

    def process_timelapse(self, index: int = 0):
        """Click process button on a timelapse card"""
        process_buttons = self.page.locator(self.process_button_selector).all()
        if len(process_buttons) > index:
            process_buttons[index].click()
            self.page.wait_for_timeout(500)

    def toggle_pin_timelapse(self, index: int = 0):
        """Toggle pin status on a timelapse card"""
        pin_buttons = self.page.locator(self.pin_button_selector).all()
        if len(pin_buttons) > index:
            pin_buttons[index].click()
            self.page.wait_for_timeout(500)

    def delete_timelapse(self, index: int = 0, confirm: bool = True):
        """Delete a timelapse card"""
        delete_buttons = self.page.locator(self.delete_button_selector).all()
        if len(delete_buttons) > index:
            # Handle confirmation dialog
            if confirm:
                self.page.on("dialog", lambda dialog: dialog.accept())
            else:
                self.page.on("dialog", lambda dialog: dialog.dismiss())
            delete_buttons[index].click()
            self.page.wait_for_timeout(500)

    def download_timelapse(self, index: int = 0):
        """Download a timelapse"""
        download_buttons = self.page.locator(self.download_button_selector).all()
        if len(download_buttons) > index:
            download_buttons[index].click()

    def is_video_modal_open(self) -> bool:
        """Check if video player modal is open"""
        return self.page.locator(self.video_modal_selector).is_visible()

    def close_video_modal(self):
        """Close the video player modal"""
        self.page.click(self.close_video_modal_button_selector)
        self.page.wait_for_selector(self.video_modal_selector, state="hidden", timeout=5000)

    def download_from_modal(self):
        """Click download button in video modal"""
        self.page.click(self.download_video_button_selector)

    def is_processing_queue_visible(self) -> bool:
        """Check if processing queue is visible"""
        return self.page.locator(self.processing_queue_selector).is_visible()

    def is_empty_state_visible(self) -> bool:
        """Check if empty state is visible"""
        return self.page.locator(self.empty_state_selector).is_visible()

    def expect_stats_bar_visible(self):
        """Assert that stats bar is visible"""
        expect(self.page.locator(self.stats_bar_selector)).to_be_visible()

    def expect_timelapse_count(self, count: int):
        """Assert the number of timelapse cards"""
        expect(self.page.locator(self.timelapse_card_selector)).to_have_count(count)

    def expect_video_modal_open(self):
        """Assert that video modal is open"""
        expect(self.page.locator(self.video_modal_selector)).to_be_visible()

    def expect_video_modal_closed(self):
        """Assert that video modal is closed"""
        expect(self.page.locator(self.video_modal_selector)).to_be_hidden()
