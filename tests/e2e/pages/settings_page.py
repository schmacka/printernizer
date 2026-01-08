"""
Page Object Model for Printernizer Settings Page
"""
from playwright.sync_api import Page, expect
from typing import Optional, List


class SettingsPage:
    """Page object for the settings page"""

    # Default timeout for CI environments
    DEFAULT_TIMEOUT = 30000

    def __init__(self, page: Page):
        self.page = page

        # Tab selectors
        self.settings_tabs_selector = ".settings-tab"
        self.active_tab_selector = ".settings-tab.active"
        self.tab_content_selector = ".tab-pane"
        self.active_tab_content_selector = ".tab-pane.active"

        # Tab button selectors
        self.general_tab_selector = ".settings-tab[data-tab='general']"
        self.jobs_tab_selector = ".settings-tab[data-tab='jobs']"
        self.library_tab_selector = ".settings-tab[data-tab='library']"
        self.files_tab_selector = ".settings-tab[data-tab='files']"
        self.timelapse_tab_selector = ".settings-tab[data-tab='timelapse']"
        self.watch_tab_selector = ".settings-tab[data-tab='watch']"
        self.system_tab_selector = ".settings-tab[data-tab='system']"

        # Tab pane selectors
        self.general_pane_selector = "#general-tab"
        self.jobs_pane_selector = "#jobs-tab"
        self.library_pane_selector = "#library-tab"
        self.files_pane_selector = "#files-tab"
        self.timelapse_pane_selector = "#timelapse-tab"
        self.watch_pane_selector = "#watch-tab"
        self.system_pane_selector = "#system-tab"

        # Form selectors
        self.settings_form_selector = "#applicationSettingsForm"
        self.save_button_selector = "button[onclick='saveSettings()']"

        # Settings field selectors (General)
        self.log_level_selector = "#logLevel"
        self.monitoring_interval_selector = "#monitoringInterval"
        self.connection_timeout_selector = "#connectionTimeout"
        self.vat_rate_selector = "#vatRate"

        # Settings field selectors (Jobs & G-Code)
        self.job_auto_create_selector = "#jobCreationAutoCreate"
        self.gcode_optimize_selector = "#gcodeOptimizePrintOnly"
        self.gcode_max_lines_selector = "#gcodeOptimizationMaxLines"
        self.gcode_render_max_lines_selector = "#gcodeRenderMaxLines"

        # Settings field selectors (Library)
        self.library_enabled_selector = "#libraryEnabled"
        self.library_path_selector = "#libraryPath"
        self.library_auto_organize_selector = "#libraryAutoOrganize"
        self.library_auto_extract_metadata_selector = "#libraryAutoExtractMetadata"
        self.library_auto_deduplicate_selector = "#libraryAutoDeduplicate"
        self.library_preserve_originals_selector = "#libraryPreserveOriginals"
        self.library_checksum_algorithm_selector = "#libraryChecksumAlgorithm"
        self.library_processing_workers_selector = "#libraryProcessingWorkers"
        self.library_search_enabled_selector = "#librarySearchEnabled"
        self.library_search_min_length_selector = "#librarySearchMinLength"

        # Settings field selectors (Files)
        self.downloads_path_selector = "#downloadsPath"
        self.max_file_size_selector = "#maxFileSize"
        self.enable_upload_selector = "#enableUpload"
        self.max_upload_size_selector = "#maxUploadSizeMb"
        self.allowed_upload_extensions_selector = "#allowedUploadExtensions"

        # Settings field selectors (Timelapse)
        self.timelapse_enabled_selector = "#timelapseEnabled"
        self.timelapse_source_folder_selector = "#timelapseSourceFolder"
        self.timelapse_output_folder_selector = "#timelapseOutputFolder"
        self.timelapse_output_strategy_selector = "#timelapseOutputStrategy"
        self.timelapse_auto_process_timeout_selector = "#timelapseAutoProcessTimeout"
        self.timelapse_cleanup_age_days_selector = "#timelapseCleanupAgeDays"

    def navigate(self, base_url: str):
        """Navigate to settings page with robust waiting"""
        # First go to base URL to ensure app is loaded
        self.page.goto(base_url, wait_until="domcontentloaded")
        self.page.wait_for_load_state("networkidle")

        # Wait for app initialization
        try:
            self.page.wait_for_function(
                "() => window.app && typeof window.app.showPage === 'function'",
                timeout=self.DEFAULT_TIMEOUT
            )
        except Exception:
            pass

        # Navigate to specific page via hash
        self.page.goto(f"{base_url}/#settings", wait_until="domcontentloaded")

        # Wait for navigation to complete - check that currentPage is correct
        try:
            self.page.wait_for_function(
                "() => window.app && window.app.currentPage === 'settings'",
                timeout=self.DEFAULT_TIMEOUT
            )
        except Exception:
            self.page.wait_for_timeout(500)

        # Wait for the page section to be visible
        try:
            self.page.wait_for_selector(
                "#settings.active, #page-settings.active",
                state="visible",
                timeout=5000
            )
        except Exception:
            # If selector doesn't match, just verify element exists
            self.page.wait_for_selector("#settings", state="attached", timeout=5000)

    def is_loaded(self) -> bool:
        """Check if the settings page is loaded"""
        try:
            self.page.wait_for_selector(self.settings_tabs_selector, timeout=5000)
            return True
        except:
            return False

    def get_all_tabs(self) -> List[str]:
        """Get all available tab names"""
        tabs = []
        tab_elements = self.page.locator(self.settings_tabs_selector).all()
        for tab in tab_elements:
            tab_name = tab.get_attribute("data-tab")
            if tab_name:
                tabs.append(tab_name)
        return tabs

    def get_active_tab(self) -> Optional[str]:
        """Get the currently active tab name"""
        active_tab = self.page.locator(self.active_tab_selector).first
        if active_tab.count() > 0:
            return active_tab.get_attribute("data-tab")
        return None

    def click_tab(self, tab_name: str):
        """Click on a specific tab"""
        tab_selector = f".settings-tab[data-tab='{tab_name}']"
        self.page.click(tab_selector)
        self.page.wait_for_timeout(300)  # Wait for tab transition

    def is_tab_visible(self, tab_name: str) -> bool:
        """Check if a tab is visible"""
        tab_selector = f".settings-tab[data-tab='{tab_name}']"
        return self.page.locator(tab_selector).is_visible()

    def is_tab_active(self, tab_name: str) -> bool:
        """Check if a specific tab is active"""
        tab_selector = f".settings-tab[data-tab='{tab_name}'].active"
        return self.page.locator(tab_selector).count() > 0

    def is_tab_pane_visible(self, tab_name: str) -> bool:
        """Check if a tab pane is visible"""
        pane_selector = f"#{tab_name}-tab.active"
        return self.page.locator(pane_selector).is_visible()

    def wait_for_tab_to_load(self, tab_name: str, timeout: int = 5000):
        """Wait for a specific tab pane to be visible"""
        pane_selector = f"#{tab_name}-tab.active"
        self.page.wait_for_selector(pane_selector, timeout=timeout)

    def is_setting_field_visible(self, field_selector: str) -> bool:
        """Check if a specific setting field is visible"""
        return self.page.locator(field_selector).is_visible()

    def get_setting_value(self, field_selector: str) -> str:
        """Get the value of a setting field"""
        element = self.page.locator(field_selector).first
        input_type = element.get_attribute("type")

        if input_type == "checkbox":
            return str(element.is_checked())
        else:
            return element.input_value()

    def set_setting_value(self, field_selector: str, value):
        """Set the value of a setting field"""
        element = self.page.locator(field_selector).first
        input_type = element.get_attribute("type")

        if input_type == "checkbox":
            if value:
                element.check()
            else:
                element.uncheck()
        else:
            element.fill(str(value))

    def click_save_button(self):
        """Click the save settings button"""
        self.page.click(self.save_button_selector)
        self.page.wait_for_timeout(500)  # Wait for save operation

    def expect_tab_is_active(self, tab_name: str):
        """Assert that a tab is active"""
        tab_selector = f".settings-tab[data-tab='{tab_name}'].active"
        expect(self.page.locator(tab_selector)).to_be_visible()

    def expect_tab_pane_is_visible(self, tab_name: str):
        """Assert that a tab pane is visible"""
        pane_selector = f"#{tab_name}-tab.active"
        expect(self.page.locator(pane_selector)).to_be_visible()

    def expect_setting_field_is_visible(self, field_selector: str):
        """Assert that a setting field is visible"""
        expect(self.page.locator(field_selector)).to_be_visible()
