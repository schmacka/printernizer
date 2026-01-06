"""
E2E tests for Printernizer Ideas Page
"""
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.pages.ideas_page import IdeasPage


@pytest.mark.e2e
@pytest.mark.playwright
class TestIdeasPage:
    """Test suite for the Ideas page"""

    def test_ideas_page_loads(self, app_page: Page, base_url: str):
        """Test that the ideas page loads successfully"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        assert ideas.is_loaded(), "Ideas page should load successfully"
        expect(app_page.locator("#ideas.page.active h1")).to_contain_text("Ideen")

    def test_refresh_button_visible(self, app_page: Page, base_url: str):
        """Test that refresh button is visible"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        expect(app_page.locator(ideas.refresh_button_selector)).to_be_visible()

    def test_import_url_button_visible(self, app_page: Page, base_url: str):
        """Test that import URL button is visible"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        expect(app_page.locator(ideas.import_url_button_selector)).to_be_visible()

    def test_new_idea_button_visible(self, app_page: Page, base_url: str):
        """Test that new idea button is visible"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        expect(app_page.locator(ideas.new_idea_button_selector)).to_be_visible()

    def test_refresh_button_click(self, app_page: Page, base_url: str):
        """Test that clicking refresh works"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)
        ideas.wait_for_loading_complete()

        ideas.click_refresh_button()
        app_page.wait_for_timeout(1000)

        assert ideas.is_loaded()


@pytest.mark.e2e
@pytest.mark.playwright
class TestIdeasFilters:
    """Test suite for Ideas filtering functionality"""

    def test_filters_visible(self, app_page: Page, base_url: str):
        """Test that all filters are visible"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        ideas.expect_filters_visible()

    def test_status_filter_visible(self, app_page: Page, base_url: str):
        """Test that status filter is visible"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        expect(app_page.locator(ideas.status_filter_selector)).to_be_visible()

    def test_status_filter_works(self, app_page: Page, base_url: str):
        """Test that status filter can be changed"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)
        ideas.wait_for_loading_complete()

        ideas.filter_by_status("idea")
        assert app_page.locator(ideas.status_filter_selector).input_value() == "idea"

    def test_type_filter_visible(self, app_page: Page, base_url: str):
        """Test that type filter is visible"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        expect(app_page.locator(ideas.type_filter_selector)).to_be_visible()

    def test_type_filter_works(self, app_page: Page, base_url: str):
        """Test that type filter can be changed"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)
        ideas.wait_for_loading_complete()

        ideas.filter_by_type("business")
        assert app_page.locator(ideas.type_filter_selector).input_value() == "business"

    def test_source_filter_visible(self, app_page: Page, base_url: str):
        """Test that source filter is visible"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        expect(app_page.locator(ideas.source_filter_selector)).to_be_visible()

    def test_source_filter_works(self, app_page: Page, base_url: str):
        """Test that source filter can be changed"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)
        ideas.wait_for_loading_complete()

        ideas.filter_by_source("manual")
        assert app_page.locator(ideas.source_filter_selector).input_value() == "manual"


@pytest.mark.e2e
@pytest.mark.playwright
class TestIdeasTabs:
    """Test suite for Ideas tabs functionality"""

    def test_tabs_visible(self, app_page: Page, base_url: str):
        """Test that tabs container is visible"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        ideas.expect_tabs_visible()

    def test_my_ideas_tab_visible(self, app_page: Page, base_url: str):
        """Test that My Ideas tab is visible"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        expect(app_page.locator(ideas.my_ideas_tab_selector)).to_be_visible()

    def test_bookmarks_tab_visible(self, app_page: Page, base_url: str):
        """Test that Bookmarks tab is visible"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        expect(app_page.locator(ideas.bookmarks_tab_selector)).to_be_visible()

    def test_trending_tab_visible(self, app_page: Page, base_url: str):
        """Test that Trending tab is visible"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        expect(app_page.locator(ideas.trending_tab_selector)).to_be_visible()

    def test_my_ideas_tab_default_active(self, app_page: Page, base_url: str):
        """Test that My Ideas tab is active by default"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        assert ideas.get_active_tab() == "my-ideas"

    def test_switch_to_bookmarks_tab(self, app_page: Page, base_url: str):
        """Test switching to Bookmarks tab"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        ideas.switch_to_bookmarks_tab()
        assert ideas.get_active_tab() == "bookmarks"

    def test_switch_to_trending_tab(self, app_page: Page, base_url: str):
        """Test switching to Trending tab"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        ideas.switch_to_trending_tab()
        assert ideas.get_active_tab() == "trending"

    def test_switch_back_to_my_ideas(self, app_page: Page, base_url: str):
        """Test switching back to My Ideas tab"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        ideas.switch_to_bookmarks_tab()
        ideas.switch_to_my_ideas_tab()
        assert ideas.get_active_tab() == "my-ideas"


@pytest.mark.e2e
@pytest.mark.playwright
class TestIdeasMyIdeasSection:
    """Test suite for My Ideas section"""

    def test_my_ideas_container_visible(self, app_page: Page, base_url: str):
        """Test that My Ideas container is visible"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        expect(app_page.locator(ideas.my_ideas_container_selector)).to_be_visible()

    def test_view_toggle_buttons_visible(self, app_page: Page, base_url: str):
        """Test that view toggle buttons are visible"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        expect(app_page.locator(ideas.grid_view_button_selector)).to_be_visible()
        expect(app_page.locator(ideas.list_view_button_selector)).to_be_visible()

    def test_grid_view_click(self, app_page: Page, base_url: str):
        """Test clicking grid view button"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        ideas.click_grid_view()
        # Verify no errors occurred
        assert ideas.is_loaded()

    def test_list_view_click(self, app_page: Page, base_url: str):
        """Test clicking list view button"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        ideas.click_list_view()
        # Verify no errors occurred
        assert ideas.is_loaded()


@pytest.mark.e2e
@pytest.mark.playwright
class TestIdeasBookmarksSection:
    """Test suite for Bookmarks section"""

    def test_bookmarks_container_visible(self, app_page: Page, base_url: str):
        """Test that Bookmarks container is visible when tab is active"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)
        ideas.switch_to_bookmarks_tab()

        expect(app_page.locator(ideas.bookmarks_container_selector)).to_be_visible()

    def test_platform_filter_buttons_visible(self, app_page: Page, base_url: str):
        """Test that platform filter buttons are visible in Bookmarks"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)
        ideas.switch_to_bookmarks_tab()

        expect(app_page.locator(ideas.platform_filter_buttons_selector).first).to_be_visible()

    def test_platform_filter_all(self, app_page: Page, base_url: str):
        """Test clicking All platform filter"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)
        ideas.switch_to_bookmarks_tab()

        ideas.filter_platform("all")
        assert ideas.is_loaded()

    def test_platform_filter_makerworld(self, app_page: Page, base_url: str):
        """Test clicking Makerworld platform filter"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)
        ideas.switch_to_bookmarks_tab()

        ideas.filter_platform("makerworld")
        assert ideas.is_loaded()

    def test_platform_filter_printables(self, app_page: Page, base_url: str):
        """Test clicking Printables platform filter"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)
        ideas.switch_to_bookmarks_tab()

        ideas.filter_platform("printables")
        assert ideas.is_loaded()


@pytest.mark.e2e
@pytest.mark.playwright
class TestIdeasTrendingSection:
    """Test suite for Trending section"""

    def test_trending_container_visible(self, app_page: Page, base_url: str):
        """Test that Trending container is visible when tab is active"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)
        ideas.switch_to_trending_tab()

        expect(app_page.locator(ideas.trending_container_selector)).to_be_visible()

    def test_trending_platform_filter_visible(self, app_page: Page, base_url: str):
        """Test that platform filter is visible in Trending"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)
        ideas.switch_to_trending_tab()

        expect(app_page.locator(ideas.trending_platform_filter_selector).first).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
class TestIdeasModals:
    """Test suite for Ideas modals"""

    def test_new_idea_modal_opens(self, app_page: Page, base_url: str):
        """Test that new idea modal opens"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        ideas.click_new_idea()
        assert ideas.is_add_idea_modal_open()
        ideas.close_modal()

    def test_import_url_modal_opens(self, app_page: Page, base_url: str):
        """Test that import URL modal opens"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        ideas.click_import_url()
        assert ideas.is_import_modal_open()
        ideas.close_modal()

    def test_new_idea_modal_has_title_field(self, app_page: Page, base_url: str):
        """Test that new idea modal has title field"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        ideas.click_new_idea()
        expect(app_page.locator(ideas.idea_title_input_selector)).to_be_visible()
        ideas.close_modal()

    def test_new_idea_modal_business_checkbox(self, app_page: Page, base_url: str):
        """Test that new idea modal has business checkbox"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        ideas.click_new_idea()
        expect(app_page.locator(ideas.idea_is_business_checkbox_selector)).to_be_visible()
        ideas.close_modal()

    def test_import_modal_has_url_field(self, app_page: Page, base_url: str):
        """Test that import modal has URL field"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        ideas.click_import_url()
        expect(app_page.locator(ideas.import_url_input_selector)).to_be_visible()
        ideas.close_modal()


@pytest.mark.e2e
@pytest.mark.playwright
class TestIdeasStats:
    """Test suite for Ideas statistics"""

    def test_stats_section_visible(self, app_page: Page, base_url: str):
        """Test that stats section is visible"""
        ideas = IdeasPage(app_page)
        ideas.navigate(base_url)

        expect(app_page.locator(ideas.ideas_stats_selector)).to_be_visible()
