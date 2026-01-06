"""
E2E tests for Printernizer Navigation
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
@pytest.mark.playwright
class TestSidebarNavigation:
    """Test suite for sidebar navigation"""

    def test_navigate_to_dashboard(self, app_page: Page, base_url: str, click_nav_link):
        """Test navigating to Dashboard via sidebar"""
        app_page.goto(base_url)
        app_page.wait_for_load_state("networkidle")

        click_nav_link("dashboard")
        expect(app_page).to_have_url(f"{base_url}/#dashboard")
        expect(app_page.locator("#dashboard.page.active")).to_be_visible()

    def test_navigate_to_printers(self, app_page: Page, base_url: str, click_nav_link):
        """Test navigating to Printers via sidebar"""
        app_page.goto(base_url)
        app_page.wait_for_load_state("networkidle")

        click_nav_link("printers")
        expect(app_page).to_have_url(f"{base_url}/#printers")
        expect(app_page.locator("#printers.page.active")).to_be_visible()

    def test_navigate_to_jobs(self, app_page: Page, base_url: str, click_nav_link):
        """Test navigating to Jobs via sidebar"""
        app_page.goto(base_url)
        app_page.wait_for_load_state("networkidle")

        click_nav_link("jobs")
        expect(app_page).to_have_url(f"{base_url}/#jobs")
        expect(app_page.locator("#page-jobs.page.active")).to_be_visible()

    def test_navigate_to_timelapses(self, app_page: Page, base_url: str, click_nav_link):
        """Test navigating to Timelapses via sidebar"""
        app_page.goto(base_url)
        app_page.wait_for_load_state("networkidle")

        click_nav_link("timelapses")
        expect(app_page).to_have_url(f"{base_url}/#timelapses")
        expect(app_page.locator("#timelapses.page.active")).to_be_visible()

    def test_navigate_to_files(self, app_page: Page, base_url: str, click_nav_link):
        """Test navigating to Files via sidebar"""
        app_page.goto(base_url)
        app_page.wait_for_load_state("networkidle")

        click_nav_link("files")
        expect(app_page).to_have_url(f"{base_url}/#files")
        expect(app_page.locator("#files.page.active")).to_be_visible()

    def test_navigate_to_library(self, app_page: Page, base_url: str, click_nav_link):
        """Test navigating to Library via sidebar"""
        app_page.goto(base_url)
        app_page.wait_for_load_state("networkidle")

        click_nav_link("library")
        expect(app_page).to_have_url(f"{base_url}/#library")
        expect(app_page.locator("#library.page.active")).to_be_visible()

    def test_navigate_to_materials(self, app_page: Page, base_url: str, click_nav_link):
        """Test navigating to Materials via sidebar"""
        app_page.goto(base_url)
        app_page.wait_for_load_state("networkidle")

        click_nav_link("materials")
        expect(app_page).to_have_url(f"{base_url}/#materials")
        expect(app_page.locator("#page-materials.page.active")).to_be_visible()

    def test_navigate_to_ideas(self, app_page: Page, base_url: str, click_nav_link):
        """Test navigating to Ideas via sidebar"""
        app_page.goto(base_url)
        app_page.wait_for_load_state("networkidle")

        click_nav_link("ideas")
        expect(app_page).to_have_url(f"{base_url}/#ideas")
        expect(app_page.locator("#ideas.page.active")).to_be_visible()

    def test_navigate_to_settings(self, app_page: Page, base_url: str, click_nav_link):
        """Test navigating to Settings via sidebar"""
        app_page.goto(base_url)
        app_page.wait_for_load_state("networkidle")

        click_nav_link("settings")
        expect(app_page).to_have_url(f"{base_url}/#settings")
        expect(app_page.locator("#settings.page.active")).to_be_visible()

    def test_navigate_to_debug(self, app_page: Page, base_url: str, click_nav_link):
        """Test navigating to Debug via sidebar"""
        app_page.goto(base_url)
        app_page.wait_for_load_state("networkidle")

        click_nav_link("debug")
        expect(app_page).to_have_url(f"{base_url}/#debug")
        expect(app_page.locator("#debug.page.active")).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
class TestHashRouting:
    """Test suite for hash-based routing"""

    def test_direct_url_dashboard(self, app_page: Page, base_url: str):
        """Test direct URL navigation to Dashboard"""
        app_page.goto(f"{base_url}/#dashboard")
        app_page.wait_for_load_state("networkidle")

        expect(app_page.locator("#dashboard.page.active")).to_be_visible()

    def test_direct_url_printers(self, app_page: Page, base_url: str):
        """Test direct URL navigation to Printers"""
        app_page.goto(f"{base_url}/#printers")
        app_page.wait_for_load_state("networkidle")

        expect(app_page.locator("#printers.page.active")).to_be_visible()

    def test_direct_url_jobs(self, app_page: Page, base_url: str):
        """Test direct URL navigation to Jobs"""
        app_page.goto(f"{base_url}/#jobs")
        app_page.wait_for_load_state("networkidle")

        expect(app_page.locator("#page-jobs.page.active")).to_be_visible()

    def test_direct_url_timelapses(self, app_page: Page, base_url: str):
        """Test direct URL navigation to Timelapses"""
        app_page.goto(f"{base_url}/#timelapses")
        app_page.wait_for_load_state("networkidle")

        expect(app_page.locator("#timelapses.page.active")).to_be_visible()

    def test_direct_url_files(self, app_page: Page, base_url: str):
        """Test direct URL navigation to Files"""
        app_page.goto(f"{base_url}/#files")
        app_page.wait_for_load_state("networkidle")

        expect(app_page.locator("#files.page.active")).to_be_visible()

    def test_direct_url_library(self, app_page: Page, base_url: str):
        """Test direct URL navigation to Library"""
        app_page.goto(f"{base_url}/#library")
        app_page.wait_for_load_state("networkidle")

        expect(app_page.locator("#library.page.active")).to_be_visible()

    def test_direct_url_materials(self, app_page: Page, base_url: str):
        """Test direct URL navigation to Materials"""
        app_page.goto(f"{base_url}/#materials")
        app_page.wait_for_load_state("networkidle")

        expect(app_page.locator("#page-materials.page.active")).to_be_visible()

    def test_direct_url_ideas(self, app_page: Page, base_url: str):
        """Test direct URL navigation to Ideas"""
        app_page.goto(f"{base_url}/#ideas")
        app_page.wait_for_load_state("networkidle")

        expect(app_page.locator("#ideas.page.active")).to_be_visible()

    def test_direct_url_settings(self, app_page: Page, base_url: str):
        """Test direct URL navigation to Settings"""
        app_page.goto(f"{base_url}/#settings")
        app_page.wait_for_load_state("networkidle")

        expect(app_page.locator("#settings.page.active")).to_be_visible()

    def test_direct_url_debug(self, app_page: Page, base_url: str):
        """Test direct URL navigation to Debug"""
        app_page.goto(f"{base_url}/#debug")
        app_page.wait_for_load_state("networkidle")

        expect(app_page.locator("#debug.page.active")).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
class TestNavbarElements:
    """Test suite for navbar elements"""

    def test_navbar_visible(self, app_page: Page, base_url: str):
        """Test that navbar is visible"""
        app_page.goto(base_url)
        app_page.wait_for_load_state("networkidle")

        expect(app_page.locator(".navbar")).to_be_visible()

    def test_navbar_brand_visible(self, app_page: Page, base_url: str):
        """Test that navbar brand is visible"""
        app_page.goto(base_url)
        app_page.wait_for_load_state("networkidle")

        expect(app_page.locator(".nav-brand")).to_be_visible()

    def test_navbar_logo_visible(self, app_page: Page, base_url: str):
        """Test that navbar logo is visible"""
        app_page.goto(base_url)
        app_page.wait_for_load_state("networkidle")

        expect(app_page.locator(".logo")).to_be_visible()

    def test_connection_status_visible(self, app_page: Page, base_url: str):
        """Test that connection status indicator is visible"""
        app_page.goto(base_url)
        app_page.wait_for_load_state("networkidle")

        expect(app_page.locator("#connectionStatus")).to_be_visible()

    def test_theme_toggle_visible(self, app_page: Page, base_url: str):
        """Test that theme toggle is visible"""
        app_page.goto(base_url)
        app_page.wait_for_load_state("networkidle")

        expect(app_page.locator("#themeToggle")).to_be_visible()

    def test_theme_toggle_click(self, app_page: Page, base_url: str):
        """Test that theme toggle can be clicked"""
        app_page.goto(base_url)
        app_page.wait_for_load_state("networkidle")

        app_page.click("#themeToggle")
        app_page.wait_for_timeout(500)

        # Should not cause any errors
        expect(app_page.locator(".navbar")).to_be_visible()

    def test_system_time_visible(self, app_page: Page, base_url: str):
        """Test that system time is visible"""
        app_page.goto(base_url)
        app_page.wait_for_load_state("networkidle")

        expect(app_page.locator("#systemTime")).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
class TestNavLinkHighlighting:
    """Test suite for nav link highlighting"""

    def test_dashboard_link_active_on_dashboard(self, app_page: Page, base_url: str):
        """Test that dashboard link is active when on dashboard"""
        app_page.goto(f"{base_url}/#dashboard")
        app_page.wait_for_load_state("networkidle")

        expect(app_page.locator("a[data-page='dashboard'].active")).to_be_visible()

    def test_printers_link_active_on_printers(self, app_page: Page, base_url: str):
        """Test that printers link is active when on printers"""
        app_page.goto(f"{base_url}/#printers")
        app_page.wait_for_load_state("networkidle")

        expect(app_page.locator("a[data-page='printers'].active")).to_be_visible()

    def test_settings_link_active_on_settings(self, app_page: Page, base_url: str):
        """Test that settings link is active when on settings"""
        app_page.goto(f"{base_url}/#settings")
        app_page.wait_for_load_state("networkidle")

        expect(app_page.locator("a[data-page='settings'].active")).to_be_visible()
