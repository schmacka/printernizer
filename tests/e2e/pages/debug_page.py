"""
Page Object Model for Printernizer Debug Page
"""
from playwright.sync_api import Page, expect
from typing import Optional, List
from .base_page import BasePage


class DebugPage(BasePage):
    """Page object for the debug page"""

    def __init__(self, page: Page):
        super().__init__(page)
        self.page_hash = "debug"
        self.page_selector = "#debug.page.active"

        # Header selectors
        self.title_selector = "h1:has-text('Debug')"

        # Action buttons - use onclick attribute for specificity
        self.refresh_button_selector = "#debug.page.active button[onclick='refreshDebugInfo()']"
        self.clear_logs_button_selector = "#debug.page.active button:has-text('Logs löschen')"
        self.download_logs_button_selector = "#debug.page.active button:has-text('Logs herunterladen')"

        # System Health section
        self.health_section_selector = ".debug-section:has(h3:has-text('System-Status'))"
        self.health_info_selector = "#healthInfo"

        # Application Logs section
        self.logs_section_selector = ".debug-section:has(h3:has-text('Anwendungsprotokolle'))"
        self.log_viewer_selector = "#logViewer"
        self.log_level_filter_selector = "#logLevelFilter"
        self.auto_refresh_checkbox_selector = "#autoRefreshLogs"
        self.log_controls_selector = ".log-controls"

        # Performance Metrics section
        self.performance_section_selector = ".debug-section:has(h3:has-text('Performance-Metriken'))"
        self.performance_metrics_selector = "#performanceMetrics"

        # Thumbnail Processing Log section
        self.thumbnail_section_selector = ".debug-section:has(h3:has-text('Thumbnail Processing'))"
        self.thumbnail_log_selector = "#thumbnailProcessingLog"
        self.thumbnail_log_refresh_button_selector = ".debug-section:has(h3:has-text('Thumbnail')) button:has-text('Aktualisieren')"
        self.thumbnail_log_limit_selector = "#thumbnailLogLimit"

        # Debug container
        self.debug_container_selector = ".debug-container"

    def click_clear_logs(self, confirm: bool = True):
        """Click clear logs button"""
        if confirm:
            self.page.on("dialog", lambda dialog: dialog.accept())
        else:
            self.page.on("dialog", lambda dialog: dialog.dismiss())
        self.page.click(self.clear_logs_button_selector)
        self.page.wait_for_timeout(500)

    def click_download_logs(self):
        """Click download logs button"""
        self.page.click(self.download_logs_button_selector)

    def filter_log_level(self, level: str):
        """Filter logs by level"""
        self.select_option(self.log_level_filter_selector, level)
        self.page.wait_for_timeout(500)

    def toggle_auto_refresh(self):
        """Toggle auto-refresh checkbox"""
        self.page.click(self.auto_refresh_checkbox_selector)
        self.page.wait_for_timeout(300)

    def is_auto_refresh_checked(self) -> bool:
        """Check if auto-refresh is enabled"""
        return self.page.locator(self.auto_refresh_checkbox_selector).is_checked()

    def refresh_thumbnail_log(self):
        """Refresh thumbnail processing log"""
        btn = self.page.locator(self.thumbnail_log_refresh_button_selector)
        if btn.is_visible():
            btn.click()
            self.page.wait_for_timeout(500)

    def set_thumbnail_log_limit(self, limit: str):
        """Set thumbnail log entry limit"""
        self.select_option(self.thumbnail_log_limit_selector, limit)
        self.page.wait_for_timeout(500)

    def get_log_level_filter_options(self) -> List[str]:
        """Get all log level filter options"""
        options = self.page.locator(f"{self.log_level_filter_selector} option").all()
        return [opt.get_attribute("value") for opt in options]

    def get_thumbnail_limit_options(self) -> List[str]:
        """Get all thumbnail log limit options"""
        options = self.page.locator(f"{self.thumbnail_log_limit_selector} option").all()
        return [opt.get_attribute("value") for opt in options]

    def is_health_section_visible(self) -> bool:
        """Check if health section is visible"""
        return self.page.locator(self.health_info_selector).is_visible()

    def is_logs_section_visible(self) -> bool:
        """Check if logs section is visible"""
        return self.page.locator(self.log_viewer_selector).is_visible()

    def is_performance_section_visible(self) -> bool:
        """Check if performance section is visible"""
        return self.page.locator(self.performance_metrics_selector).is_visible()

    def is_thumbnail_section_visible(self) -> bool:
        """Check if thumbnail processing section is visible"""
        return self.page.locator(self.thumbnail_log_selector).is_visible()

    def expect_health_section_visible(self):
        """Assert that health section is visible"""
        expect(self.page.locator(self.health_info_selector)).to_be_visible()

    def expect_logs_section_visible(self):
        """Assert that logs section is visible"""
        expect(self.page.locator(self.log_viewer_selector)).to_be_visible()

    def expect_performance_section_visible(self):
        """Assert that performance section is visible"""
        expect(self.page.locator(self.performance_metrics_selector)).to_be_visible()

    def expect_thumbnail_section_visible(self):
        """Assert that thumbnail section is visible"""
        expect(self.page.locator(self.thumbnail_log_selector)).to_be_visible()

    def expect_all_sections_visible(self):
        """Assert that all debug sections are visible"""
        self.expect_health_section_visible()
        self.expect_logs_section_visible()
        self.expect_performance_section_visible()
        self.expect_thumbnail_section_visible()
