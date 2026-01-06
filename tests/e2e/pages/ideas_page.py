"""
Page Object Model for Printernizer Ideas Page
"""
from playwright.sync_api import Page, expect
from typing import Optional, List
from .base_page import BasePage


class IdeasPage(BasePage):
    """Page object for the ideas page"""

    def __init__(self, page: Page):
        super().__init__(page)
        self.page_hash = "ideas"
        self.page_selector = "#ideas.page.active"

        # Header selectors
        self.title_selector = "h1:has-text('Ideen')"

        # Filter selectors
        self.status_filter_selector = "#ideaStatusFilter"
        self.type_filter_selector = "#ideaTypeFilter"
        self.source_filter_selector = "#ideaSourceFilter"

        # Action buttons - use onclick for specificity where needed
        self.refresh_button_selector = "#ideas.page.active button[onclick='refreshIdeas()']"
        self.import_url_button_selector = "#ideas.page.active .page-header button:has-text('Aus URL importieren')"
        self.new_idea_button_selector = "#ideas.page.active button:has-text('Neue Idee')"

        # Tab selectors
        self.tab_container_selector = ".ideas-nav-tabs"
        self.my_ideas_tab_selector = "button[data-tab='my-ideas'], .tab-button[data-tab='my-ideas']"
        self.bookmarks_tab_selector = "button[data-tab='bookmarks'], .tab-button[data-tab='bookmarks']"
        self.trending_tab_selector = "button[data-tab='trending'], .tab-button[data-tab='trending']"
        self.active_tab_selector = ".tab-button.active"

        # Tab content selectors
        self.my_ideas_tab_content_selector = "#my-ideas-tab"
        self.bookmarks_tab_content_selector = "#bookmarks-tab"
        self.trending_tab_content_selector = "#trending-tab"
        self.active_tab_content_selector = ".ideas-tab-content.active"

        # Statistics selectors
        self.ideas_stats_selector = "#ideasStats"

        # My Ideas section
        self.my_ideas_container_selector = "#myIdeasContainer"
        self.grid_view_button_selector = "#gridViewBtn"
        self.list_view_button_selector = "#listViewBtn"
        self.idea_card_selector = ".idea-card"

        # Bookmarks section
        self.bookmarks_container_selector = "#bookmarksContainer"
        self.platform_filter_buttons_selector = ".platform-filter .platform-btn"
        self.bookmark_card_selector = ".bookmark-card"

        # Trending section
        self.trending_container_selector = "#trendingContainer"
        self.trending_platform_filter_selector = ".trending-platform-filter .platform-btn"
        self.trending_card_selector = ".trending-card"
        self.trending_refresh_button_selector = "#trending-tab button:has-text('Aktualisieren')"

        # Platform filter buttons
        self.platform_all_button_selector = ".platform-btn[data-platform='all']"
        self.platform_makerworld_button_selector = ".platform-btn[data-platform='makerworld']"
        self.platform_printables_button_selector = ".platform-btn[data-platform='printables']"

        # Add Idea Modal - use specific IDs to avoid conflicts with edit/import modals
        self.add_idea_modal_selector = "#addIdeaModal"
        self.idea_title_input_selector = "#ideaTitle"
        self.idea_description_input_selector = "#ideaDescription"
        self.idea_category_input_selector = "#ideaCategory"
        self.idea_priority_selector = "#ideaPriority"
        self.idea_is_business_checkbox_selector = "#ideaIsBusiness"
        self.idea_tags_input_selector = "#ideaTags"
        self.save_idea_button_selector = "#addIdeaModal button:has-text('Speichern')"

        # Edit Idea Modal
        self.edit_idea_modal_selector = "#editIdeaModal, .modal:has-text('Idee bearbeiten')"

        # Import Idea Modal
        self.import_idea_modal_selector = "#importIdeaModal, .modal:has-text('Import')"
        self.import_url_input_selector = "#importUrl, input[name='url']"
        self.import_submit_button_selector = "button:has-text('Importieren')"

        # Idea Details Modal
        self.idea_details_modal_selector = "#ideaDetailsModal, .modal.idea-details"
        self.idea_details_content_selector = "#ideaDetailsContent"

        # Card action buttons
        self.idea_details_button_selector = ".idea-card button:has-text('Details')"
        self.idea_edit_button_selector = ".idea-card button:has-text('Bearbeiten')"
        self.idea_plan_button_selector = ".idea-card button:has-text('Planen')"
        self.idea_print_button_selector = ".idea-card button:has-text('Drucken')"

        # Empty state
        self.empty_state_selector = ".empty-state, .no-ideas"

    def switch_to_my_ideas_tab(self):
        """Switch to My Ideas tab"""
        self.page.click(self.my_ideas_tab_selector)
        self.page.wait_for_selector(f"{self.my_ideas_tab_content_selector}.active", timeout=3000)

    def switch_to_bookmarks_tab(self):
        """Switch to Bookmarks tab"""
        self.page.click(self.bookmarks_tab_selector)
        self.page.wait_for_selector(f"{self.bookmarks_tab_content_selector}.active", timeout=3000)

    def switch_to_trending_tab(self):
        """Switch to Trending tab"""
        self.page.click(self.trending_tab_selector)
        self.page.wait_for_selector(f"{self.trending_tab_content_selector}.active", timeout=3000)

    def get_active_tab(self) -> str:
        """Get the currently active tab name"""
        active_tab = self.page.locator(self.active_tab_selector).first
        return active_tab.get_attribute("data-tab") or ""

    def filter_by_status(self, status: str):
        """Filter ideas by status"""
        self.select_option(self.status_filter_selector, status)
        self.page.wait_for_timeout(500)

    def filter_by_type(self, idea_type: str):
        """Filter ideas by type"""
        self.select_option(self.type_filter_selector, idea_type)
        self.page.wait_for_timeout(500)

    def filter_by_source(self, source: str):
        """Filter ideas by source"""
        self.select_option(self.source_filter_selector, source)
        self.page.wait_for_timeout(500)

    def click_grid_view(self):
        """Switch to grid view"""
        self.page.click(self.grid_view_button_selector)
        self.page.wait_for_timeout(300)

    def click_list_view(self):
        """Switch to list view"""
        self.page.click(self.list_view_button_selector)
        self.page.wait_for_timeout(300)

    def click_new_idea(self):
        """Click new idea button"""
        self.page.click(self.new_idea_button_selector)
        self.page.wait_for_selector(self.add_idea_modal_selector, state="visible", timeout=5000)

    def click_import_url(self):
        """Click import URL button"""
        self.page.click(self.import_url_button_selector)
        self.page.wait_for_selector(self.import_idea_modal_selector, state="visible", timeout=5000)

    def filter_platform(self, platform: str):
        """Filter by platform"""
        btn = self.page.locator(f".platform-btn[data-platform='{platform}']").first
        if btn.is_visible():
            btn.click()
            self.page.wait_for_timeout(500)

    def get_idea_count(self) -> int:
        """Get the number of idea cards in current tab"""
        return self.page.locator(self.idea_card_selector).count()

    def get_bookmark_count(self) -> int:
        """Get the number of bookmark cards"""
        return self.page.locator(self.bookmark_card_selector).count()

    def get_trending_count(self) -> int:
        """Get the number of trending cards"""
        return self.page.locator(self.trending_card_selector).count()

    def click_idea_details(self, index: int = 0):
        """Click details button on an idea card"""
        buttons = self.page.locator(self.idea_details_button_selector).all()
        if len(buttons) > index:
            buttons[index].click()
            self.page.wait_for_timeout(500)

    def click_idea_edit(self, index: int = 0):
        """Click edit button on an idea card"""
        buttons = self.page.locator(self.idea_edit_button_selector).all()
        if len(buttons) > index:
            buttons[index].click()
            self.page.wait_for_timeout(500)

    def is_add_idea_modal_open(self) -> bool:
        """Check if add idea modal is open"""
        return self.page.locator(self.add_idea_modal_selector).is_visible()

    def is_import_modal_open(self) -> bool:
        """Check if import modal is open"""
        return self.page.locator(self.import_idea_modal_selector).is_visible()

    def close_modal(self):
        """Close any open modal"""
        close_btn = self.page.locator(".modal.show .modal-close, .modal:visible .modal-close").first
        if close_btn.is_visible():
            close_btn.click()
            self.page.wait_for_timeout(300)

    def fill_idea_form(self, title: str, description: str = "", is_business: bool = False):
        """Fill the add idea form"""
        self.fill_input(self.idea_title_input_selector, title)
        if description:
            self.fill_input(self.idea_description_input_selector, description)
        if is_business:
            checkbox = self.page.locator(self.idea_is_business_checkbox_selector)
            if not checkbox.is_checked():
                checkbox.click()

    def submit_idea_form(self):
        """Submit the idea form"""
        self.page.click(self.save_idea_button_selector)
        self.page.wait_for_timeout(500)

    def fill_import_url(self, url: str):
        """Fill import URL field"""
        self.fill_input(self.import_url_input_selector, url)

    def submit_import(self):
        """Submit import form"""
        self.page.click(self.import_submit_button_selector)
        self.page.wait_for_timeout(500)

    def expect_tabs_visible(self):
        """Assert that tab container is visible"""
        expect(self.page.locator(self.tab_container_selector)).to_be_visible()

    def expect_my_ideas_tab_active(self):
        """Assert that My Ideas tab is active"""
        expect(self.page.locator(f"{self.my_ideas_tab_selector}.active")).to_be_visible()

    def expect_bookmarks_tab_active(self):
        """Assert that Bookmarks tab is active"""
        expect(self.page.locator(f"{self.bookmarks_tab_selector}.active")).to_be_visible()

    def expect_trending_tab_active(self):
        """Assert that Trending tab is active"""
        expect(self.page.locator(f"{self.trending_tab_selector}.active")).to_be_visible()

    def expect_filters_visible(self):
        """Assert that filters are visible"""
        expect(self.page.locator(self.status_filter_selector)).to_be_visible()
        expect(self.page.locator(self.type_filter_selector)).to_be_visible()
        expect(self.page.locator(self.source_filter_selector)).to_be_visible()
