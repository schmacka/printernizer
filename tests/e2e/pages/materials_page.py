"""
Page Object Model for Printernizer Materials page
"""
from playwright.sync_api import Page, expect
from typing import Optional


class MaterialsPage:
    """Page object for the materials/inventory page"""
    
    def __init__(self, page: Page):
        self.page = page
        
        # Selectors - matching actual HTML with German text
        # Note: Table view is hidden by default, cards view is shown
        self.materials_table_selector = "#materialsTable, .materials-table-wrapper"
        self.material_row_selector = "#materialsTableBody tr, .material-row"
        self.add_material_button_selector = "#addMaterialBtn, button:has-text('Filament hinzufügen')"
        self.material_modal_selector = "#materialModal, .material-modal"
        self.material_brand_input_selector = "#materialBrand, input[name='brand']"
        self.material_type_select_selector = "#materialType, select[name='material_type']"
        self.color_input_selector = "#materialColor, input[name='color']"
        self.weight_input_selector = "#materialSpoolWeight, input[name='spool_weight_g']"
        self.cost_input_selector = "#materialPricePerKg, input[name='price_per_kg']"
        self.submit_material_button_selector = "button[type='submit'], .submit-material-btn"
        
    def navigate(self, base_url: str):
        """Navigate to materials page"""
        self.page.goto(f"{base_url}/#materials", wait_until="domcontentloaded")
        self.page.wait_for_load_state("networkidle")
        # Wait for app initialization (main.js to execute)
        self.page.wait_for_function("() => window.app && window.app.currentPage")
        # Wait for the materials page section to be visible
        self.page.wait_for_selector("#page-materials.active", state="visible", timeout=5000)
        
    def open_add_material_modal(self):
        """Open the add material modal"""
        self.page.click(self.add_material_button_selector)
        self.page.wait_for_selector(self.material_modal_selector, state="visible")
        
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
        self.page.wait_for_selector(self.material_modal_selector, state="hidden", timeout=5000)
        
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
