"""
Page Object Model for Printernizer Materials page
"""
from playwright.sync_api import Page, expect
from typing import Optional


class MaterialsPage:
    """Page object for the materials/inventory page"""

    # Default timeout for CI environments
    DEFAULT_TIMEOUT = 30000

    def __init__(self, page: Page):
        self.page = page

        # Selectors - matching actual HTML structure from index.html
        self.materials_table_selector = "#materialsTable, .materials-table-wrapper, #materialsTableView"
        self.material_row_selector = "#materialsTableBody tr, .material-row, .material-card"
        self.add_material_button_selector = "#addMaterialBtn"
        self.material_modal_selector = "#materialModal"
        self.material_brand_input_selector = "#materialBrand, input[name='brand']"
        self.material_type_select_selector = "#materialType, select[name='material_type']"
        self.color_input_selector = "#materialColor, input[name='color']"
        self.weight_input_selector = "#materialSpoolWeight, input[name='spool_weight_g']"
        self.cost_input_selector = "#materialPricePerKg, input[name='price_per_kg']"
        self.submit_material_button_selector = "#materialModal button[type='submit'], .submit-material-btn"

    def navigate(self, base_url: str):
        """Navigate to materials page with robust waiting"""
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

        # Navigate to materials page via hash
        self.page.goto(f"{base_url}/#materials", wait_until="domcontentloaded")

        # Wait for navigation to complete - check that currentPage is 'materials'
        try:
            self.page.wait_for_function(
                "() => window.app && window.app.currentPage === 'materials'",
                timeout=self.DEFAULT_TIMEOUT
            )
        except Exception:
            self.page.wait_for_timeout(500)

        # Wait for the materials page section to be visible
        # Note: Materials page uses #page-materials ID in the HTML
        # Use longer timeout and ensure page is actually visible (not just attached)
        self.page.wait_for_selector(
            "#page-materials.page.active, #page-materials.active",
            state="visible",
            timeout=self.DEFAULT_TIMEOUT
        )

    def open_add_material_modal(self):
        """Open the add material modal"""
        # Wait for button to be clickable
        self.page.wait_for_selector(self.add_material_button_selector, state="visible", timeout=self.DEFAULT_TIMEOUT)
        self.page.click(self.add_material_button_selector)
        self.page.wait_for_selector(self.material_modal_selector, state="visible", timeout=self.DEFAULT_TIMEOUT)
        
    def fill_material_form(
        self,
        name: str,
        material_type: str = "PLA",
        color: Optional[str] = None,
        weight: Optional[str] = None,
        cost: Optional[str] = None
    ):
        """Fill out the material form"""
        self.page.fill(self.material_brand_input_selector, name)
        self.page.select_option(self.material_type_select_selector, material_type)
        
        if color:
            self.page.fill(self.color_input_selector, color)
        if weight:
            self.page.fill(self.weight_input_selector, weight)
        if cost:
            self.page.fill(self.cost_input_selector, cost)
            
    def submit_material_form(self):
        """Submit the material form"""
        self.page.click(self.submit_material_button_selector)
        
    def add_material(
        self,
        name: str,
        material_type: str = "PLA",
        color: Optional[str] = None,
        weight: Optional[str] = None,
        cost: Optional[str] = None
    ):
        """Complete flow to add a new material"""
        self.open_add_material_modal()
        self.fill_material_form(name, material_type, color, weight, cost)
        self.submit_material_form()
        # Wait for modal to close
        self.page.wait_for_selector(self.material_modal_selector, state="hidden", timeout=self.DEFAULT_TIMEOUT)
        
    def get_material_list(self) -> list[str]:
        """Get list of all material names"""
        names = []
        rows = self.page.locator(self.material_row_selector).all()
        for row in rows:
            name_element = row.locator(".material-name, td:first-child")
            if name_element.count() > 0:
                names.append(name_element.inner_text())
        return names
        
    def expect_material_in_list(self, material_name: str):
        """Assert that a material appears in the list"""
        expect(self.page.locator(f"{self.material_row_selector}:has-text('{material_name}')")).to_be_visible()
