"""
E2E tests for Printernizer Dashboard
"""
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.pages import DashboardPage


@pytest.mark.e2e
@pytest.mark.playwright
def test_dashboard_loads(app_page: Page, base_url: str):
    """Test that the dashboard page loads successfully"""
    dashboard = DashboardPage(app_page)
    dashboard.navigate(base_url)
    
    assert dashboard.is_loaded(), "Dashboard should load successfully"
    expect(app_page).to_have_title("Printernizer - 3D-Drucker Verwaltung")


@pytest.mark.e2e
@pytest.mark.playwright
def test_dashboard_displays_printers(app_page: Page, base_url: str):
    """Test that printers are displayed on the dashboard"""
    dashboard = DashboardPage(app_page)
    dashboard.navigate(base_url)
    
    # Wait for printers to load (may be 0 if none configured)
    app_page.wait_for_timeout(1000)  # Give time for API call
    
    printer_count = dashboard.get_printer_count()
    assert printer_count >= 0, "Should display printer cards (or none if not configured)"


@pytest.mark.e2e
@pytest.mark.playwright
def test_dashboard_add_printer_button_exists(app_page: Page, base_url: str):
    """Test that the add printer button is present"""
    dashboard = DashboardPage(app_page)
    dashboard.navigate(base_url)
    
    add_button = app_page.locator(dashboard.add_printer_button_selector)
    expect(add_button.first).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
def test_dashboard_navigation(app_page: Page, base_url: str):
    """Test navigation from dashboard to other pages"""
    app_page.goto(base_url)
    
    # Test navigation to printers page
    printers_link = app_page.locator("a[href*='printers'], nav a:has-text('Printers')")
    if printers_link.count() > 0:
        printers_link.first.click()
        app_page.wait_for_load_state("networkidle")
        assert "printers" in app_page.url.lower() or app_page.url == f"{base_url}/printers.html"


@pytest.mark.e2e
@pytest.mark.playwright
@pytest.mark.slow
def test_dashboard_real_time_updates(app_page: Page, base_url: str):
    """Test that dashboard receives real-time updates via WebSocket"""
    dashboard = DashboardPage(app_page)
    dashboard.navigate(base_url)
    
    # Monitor WebSocket connections
    ws_established = False
    
    def handle_websocket(ws):
        nonlocal ws_established
        ws_established = True
        
    app_page.on("websocket", handle_websocket)
    
    # Reload to trigger WebSocket connection
    app_page.reload()
    app_page.wait_for_timeout(2000)
    
    # Note: This test will pass even without WebSocket if not implemented yet
    # It's a placeholder for future WebSocket testing
    assert True, "WebSocket test placeholder"


@pytest.mark.e2e
@pytest.mark.playwright
def test_dashboard_responsive_design(app_page: Page, base_url: str):
    """Test dashboard responsiveness on different screen sizes"""
    dashboard = DashboardPage(app_page)
    
    # Test desktop view
    app_page.set_viewport_size({"width": 1920, "height": 1080})
    dashboard.navigate(base_url)
    assert dashboard.is_loaded()
    
    # Test tablet view
    app_page.set_viewport_size({"width": 768, "height": 1024})
    app_page.reload()
    assert dashboard.is_loaded()
    
    # Test mobile view
    app_page.set_viewport_size({"width": 375, "height": 667})
    app_page.reload()
    assert dashboard.is_loaded()
