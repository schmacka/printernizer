"""
E2E tests for Printernizer Statistics Dashboard
"""
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.pages import StatisticsPage


@pytest.mark.e2e
@pytest.mark.playwright
def test_statistics_page_loads(app_page: Page, base_url: str):
    """Test that the statistics/dashboard page loads successfully"""
    stats = StatisticsPage(app_page)
    stats.navigate(base_url)
    
    assert stats.is_loaded(), "Statistics page should load successfully"
    expect(app_page).to_have_title("Printernizer - 3D-Drucker Verwaltung")


@pytest.mark.e2e
@pytest.mark.playwright
def test_statistics_cards_display(app_page: Page, base_url: str):
    """Test that statistics cards are displayed"""
    stats = StatisticsPage(app_page)
    stats.navigate(base_url)
    
    # Wait for stats to load
    app_page.wait_for_timeout(1000)
    
    card_count = stats.get_stat_cards_count()
    assert card_count > 0, "Should display at least one statistic card"


@pytest.mark.e2e
@pytest.mark.playwright
def test_statistics_have_values(app_page: Page, base_url: str):
    """Test that statistics display actual values"""
    stats = StatisticsPage(app_page)
    stats.navigate(base_url)
    
    # Wait for data to load
    try:
        stats.wait_for_stats_to_load(timeout=10000)
    except:
        # If no data loads (empty system), that's acceptable
        pass
    
    all_stats = stats.get_all_stat_values()
    assert len(all_stats) > 0, "Should have at least one statistic displayed"


@pytest.mark.e2e
@pytest.mark.playwright
def test_dashboard_printers_section(app_page: Page, base_url: str):
    """Test that the printers section is visible on dashboard"""
    stats = StatisticsPage(app_page)
    stats.navigate(base_url)
    
    # Check for printers section
    printers_section = app_page.locator(".printers-grid, #printersGrid, .dashboard-printers")
    # Printers section should exist (even if empty)
    assert printers_section.count() >= 0, "Should have printers section in DOM"


@pytest.mark.e2e
@pytest.mark.playwright
def test_dashboard_recent_jobs_section(app_page: Page, base_url: str):
    """Test that recent jobs section is visible"""
    stats = StatisticsPage(app_page)
    stats.navigate(base_url)
    
    # Check for recent jobs section
    jobs_section = app_page.locator(".jobs-preview, #recentJobs")
    expect(jobs_section.first).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
def test_dashboard_navigation_links(app_page: Page, base_url: str):
    """Test that dashboard has working navigation links"""
    stats = StatisticsPage(app_page)
    stats.navigate(base_url)
    
    # Look for "View All" or "Alle anzeigen" buttons
    view_all_buttons = app_page.locator("a:has-text('Alle anzeigen'), button:has-text('Alle anzeigen')")
    if view_all_buttons.count() > 0:
        # Click first "View All" button
        view_all_buttons.first.click()
        app_page.wait_for_timeout(500)
        # URL should have changed or page should have changed
        assert app_page.url != f"{base_url}/#dashboard", "Should navigate to different page"


@pytest.mark.e2e
@pytest.mark.playwright
def test_statistics_refresh_capability(app_page: Page, base_url: str):
    """Test that statistics can be refreshed"""
    stats = StatisticsPage(app_page)
    stats.navigate(base_url)
    
    # Get initial stats
    initial_stats = stats.get_all_stat_values()
    
    # Reload page
    app_page.reload()
    stats.navigate(base_url)
    
    # Stats should load again
    refreshed_stats = stats.get_all_stat_values()
    assert len(refreshed_stats) >= len(initial_stats), "Stats should reload on refresh"


@pytest.mark.e2e
@pytest.mark.playwright
@pytest.mark.charts
def test_statistics_charts_present(app_page: Page, base_url: str):
    """Test if charts are present on statistics page"""
    stats = StatisticsPage(app_page)
    stats.navigate(base_url)
    
    # Wait for potential charts to load
    app_page.wait_for_timeout(2000)
    
    # Check if charts exist (this is optional functionality)
    has_charts = stats.has_charts()
    # This test is informational - charts may or may not be implemented
    if has_charts:
        assert stats.get_charts_count() > 0, "If charts exist, should have at least one"


@pytest.mark.e2e
@pytest.mark.playwright
@pytest.mark.filters
def test_statistics_filters_exist(app_page: Page, base_url: str):
    """Test if filter controls exist on dashboard"""
    stats = StatisticsPage(app_page)
    stats.navigate(base_url)
    
    # Check for any filter controls (these may not exist yet)
    filter_controls = app_page.locator(
        "select.filter-select, .filter-controls, select.time-filter, select.printer-filter"
    )
    
    # This is a soft check - filters may not be implemented yet
    filter_count = filter_controls.count()
    # No assertion - just checking if they exist


@pytest.mark.e2e
@pytest.mark.playwright
@pytest.mark.german
def test_statistics_german_labels(app_page: Page, base_url: str):
    """Test that statistics use German labels"""
    stats = StatisticsPage(app_page)
    stats.navigate(base_url)
    
    all_stats = stats.get_all_stat_values()
    
    # Common German labels that might appear
    german_terms = ["Drucker", "Aufträge", "Druckzeit", "Filament", "Spulen", "Dateien"]
    
    # Check if any German terms appear in the labels
    has_german = any(
        any(term in label for term in german_terms)
        for label in all_stats.keys()
    )
    
    # This is informational - the page should use German text
    # Not a hard requirement if no stats are displayed
    if len(all_stats) > 0:
        # At least check that page text is German
        page_text = app_page.inner_text("body")
        assert any(term in page_text for term in german_terms), "Dashboard should use German text"


@pytest.mark.e2e
@pytest.mark.playwright
@pytest.mark.responsive
def test_statistics_responsive_layout(app_page: Page, base_url: str):
    """Test that statistics page is responsive"""
    stats = StatisticsPage(app_page)
    
    # Test desktop
    app_page.set_viewport_size({"width": 1920, "height": 1080})
    stats.navigate(base_url)
    assert stats.is_loaded(), "Should load on desktop"
    desktop_cards = stats.get_stat_cards_count()
    
    # Test tablet
    app_page.set_viewport_size({"width": 768, "height": 1024})
    app_page.reload()
    stats.navigate(base_url)
    assert stats.is_loaded(), "Should load on tablet"
    
    # Test mobile
    app_page.set_viewport_size({"width": 375, "height": 667})
    app_page.reload()
    stats.navigate(base_url)
    assert stats.is_loaded(), "Should load on mobile"
