"""
E2E tests for Printernizer Settings Page
Tests settings accessibility and tab switching functionality
"""
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.pages import SettingsPage


@pytest.mark.e2e
@pytest.mark.playwright
def test_settings_page_loads(app_page: Page, base_url: str):
    """Test that the settings page loads successfully"""
    settings = SettingsPage(app_page)
    settings.navigate(base_url)

    assert settings.is_loaded(), "Settings page should load successfully"


@pytest.mark.e2e
@pytest.mark.playwright
def test_all_settings_tabs_are_visible(app_page: Page, base_url: str):
    """Test that all settings tabs are visible"""
    settings = SettingsPage(app_page)
    settings.navigate(base_url)

    # Get all tabs
    tabs = settings.get_all_tabs()

    # Verify all expected tabs are present
    expected_tabs = ['general', 'jobs', 'library', 'files', 'timelapse', 'watch', 'system']
    for tab in expected_tabs:
        assert tab in tabs, f"Tab '{tab}' should be present in settings"
        assert settings.is_tab_visible(tab), f"Tab '{tab}' should be visible"


@pytest.mark.e2e
@pytest.mark.playwright
def test_settings_tab_switching_general_to_jobs(app_page: Page, base_url: str):
    """Test switching from general tab to jobs tab"""
    settings = SettingsPage(app_page)
    settings.navigate(base_url)

    # Verify general tab is active by default
    assert settings.is_tab_active('general'), "General tab should be active by default"
    assert settings.is_tab_pane_visible('general'), "General pane should be visible by default"

    # Click on jobs tab
    settings.click_tab('jobs')

    # Verify jobs tab is now active
    assert settings.is_tab_active('jobs'), "Jobs tab should be active after clicking"
    assert settings.is_tab_pane_visible('jobs'), "Jobs pane should be visible after clicking"

    # Verify general tab is no longer active
    assert not settings.is_tab_active('general'), "General tab should not be active after switching"


@pytest.mark.e2e
@pytest.mark.playwright
def test_settings_tab_switching_all_tabs(app_page: Page, base_url: str):
    """Test switching between all settings tabs"""
    settings = SettingsPage(app_page)
    settings.navigate(base_url)

    tabs_to_test = ['general', 'jobs', 'library', 'files', 'timelapse', 'watch', 'system']

    for tab in tabs_to_test:
        # Click on tab
        settings.click_tab(tab)

        # Verify tab is active
        assert settings.is_tab_active(tab), f"Tab '{tab}' should be active after clicking"

        # Verify tab pane is visible
        assert settings.is_tab_pane_visible(tab), f"Tab pane '{tab}' should be visible after clicking"

        # Verify only one tab is active at a time
        active_tabs = app_page.locator(".settings-tab.active").count()
        assert active_tabs == 1, f"Only one tab should be active at a time, found {active_tabs}"

        # Verify only one tab pane is visible at a time
        active_panes = app_page.locator(".tab-pane.active").count()
        assert active_panes == 1, f"Only one tab pane should be visible at a time, found {active_panes}"


@pytest.mark.e2e
@pytest.mark.playwright
def test_general_settings_fields_are_accessible(app_page: Page, base_url: str):
    """Test that all general settings fields are accessible"""
    settings = SettingsPage(app_page)
    settings.navigate(base_url)

    # Click on general tab
    settings.click_tab('general')

    # Verify general settings fields are visible
    general_fields = [
        settings.log_level_selector,
        settings.monitoring_interval_selector,
        settings.connection_timeout_selector,
        settings.vat_rate_selector,
    ]

    for field in general_fields:
        assert settings.is_setting_field_visible(field), f"Field {field} should be visible in general tab"


@pytest.mark.e2e
@pytest.mark.playwright
def test_jobs_settings_fields_are_accessible(app_page: Page, base_url: str):
    """Test that all jobs & g-code settings fields are accessible"""
    settings = SettingsPage(app_page)
    settings.navigate(base_url)

    # Click on jobs tab
    settings.click_tab('jobs')

    # Verify jobs settings fields are visible
    jobs_fields = [
        settings.job_auto_create_selector,
        settings.gcode_optimize_selector,
        settings.gcode_max_lines_selector,
        settings.gcode_render_max_lines_selector,
    ]

    for field in jobs_fields:
        assert settings.is_setting_field_visible(field), f"Field {field} should be visible in jobs tab"


@pytest.mark.e2e
@pytest.mark.playwright
def test_library_settings_fields_are_accessible(app_page: Page, base_url: str):
    """Test that all library settings fields are accessible"""
    settings = SettingsPage(app_page)
    settings.navigate(base_url)

    # Click on library tab
    settings.click_tab('library')

    # Verify library settings fields are visible
    library_fields = [
        settings.library_enabled_selector,
        settings.library_path_selector,
        settings.library_auto_organize_selector,
        settings.library_auto_extract_metadata_selector,
        settings.library_auto_deduplicate_selector,
        settings.library_preserve_originals_selector,
        settings.library_checksum_algorithm_selector,
        settings.library_processing_workers_selector,
        settings.library_search_enabled_selector,
        settings.library_search_min_length_selector,
    ]

    for field in library_fields:
        assert settings.is_setting_field_visible(field), f"Field {field} should be visible in library tab"


@pytest.mark.e2e
@pytest.mark.playwright
def test_files_settings_fields_are_accessible(app_page: Page, base_url: str):
    """Test that all file settings fields are accessible"""
    settings = SettingsPage(app_page)
    settings.navigate(base_url)

    # Click on files tab
    settings.click_tab('files')

    # Verify file settings fields are visible
    files_fields = [
        settings.downloads_path_selector,
        settings.max_file_size_selector,
        settings.enable_upload_selector,
        settings.max_upload_size_selector,
        settings.allowed_upload_extensions_selector,
    ]

    for field in files_fields:
        assert settings.is_setting_field_visible(field), f"Field {field} should be visible in files tab"


@pytest.mark.e2e
@pytest.mark.playwright
def test_timelapse_settings_fields_are_accessible(app_page: Page, base_url: str):
    """Test that all timelapse settings fields are accessible"""
    settings = SettingsPage(app_page)
    settings.navigate(base_url)

    # Click on timelapse tab
    settings.click_tab('timelapse')

    # Verify timelapse settings fields are visible
    timelapse_fields = [
        settings.timelapse_enabled_selector,
        settings.timelapse_source_folder_selector,
        settings.timelapse_output_folder_selector,
        settings.timelapse_output_strategy_selector,
        settings.timelapse_auto_process_timeout_selector,
        settings.timelapse_cleanup_age_days_selector,
    ]

    for field in timelapse_fields:
        assert settings.is_setting_field_visible(field), f"Field {field} should be visible in timelapse tab"


@pytest.mark.e2e
@pytest.mark.playwright
def test_settings_form_exists(app_page: Page, base_url: str):
    """Test that the settings form exists"""
    settings = SettingsPage(app_page)
    settings.navigate(base_url)

    # Verify form exists
    form = app_page.locator(settings.settings_form_selector)
    expect(form).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
def test_settings_save_button_exists(app_page: Page, base_url: str):
    """Test that the save button exists"""
    settings = SettingsPage(app_page)
    settings.navigate(base_url)

    # Verify save button exists
    save_button = app_page.locator(settings.save_button_selector)
    expect(save_button).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
def test_tab_switching_preserves_active_state(app_page: Page, base_url: str):
    """Test that switching tabs properly updates active states"""
    settings = SettingsPage(app_page)
    settings.navigate(base_url)

    # Start at general tab
    settings.click_tab('general')
    app_page.wait_for_timeout(500)

    # Switch to library tab
    settings.click_tab('library')
    app_page.wait_for_timeout(500)

    # Verify library tab is active and general is not
    settings.expect_tab_is_active('library')
    settings.expect_tab_pane_is_visible('library')

    # General tab should not be active
    assert not settings.is_tab_active('general'), "General tab should not be active"
    assert not settings.is_tab_pane_visible('general'), "General pane should not be visible"


@pytest.mark.e2e
@pytest.mark.playwright
def test_rapid_tab_switching(app_page: Page, base_url: str):
    """Test rapid tab switching to ensure no race conditions"""
    settings = SettingsPage(app_page)
    settings.navigate(base_url)

    # Rapidly switch between tabs
    tabs = ['general', 'jobs', 'library', 'files', 'timelapse']

    for i in range(3):  # Do 3 rounds of rapid switching
        for tab in tabs:
            settings.click_tab(tab)
            app_page.wait_for_timeout(100)  # Minimal wait

    # After rapid switching, verify last tab is active
    final_tab = tabs[-1]
    app_page.wait_for_timeout(500)  # Wait for any animations to complete

    assert settings.is_tab_active(final_tab), f"Final tab '{final_tab}' should be active after rapid switching"
    assert settings.is_tab_pane_visible(final_tab), f"Final pane '{final_tab}' should be visible after rapid switching"

    # Verify only one tab is active
    active_tabs = app_page.locator(".settings-tab.active").count()
    assert active_tabs == 1, f"Only one tab should be active after rapid switching, found {active_tabs}"
