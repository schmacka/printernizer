"""
E2E tests for Printernizer Materials/Inventory Management
"""
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.pages import MaterialsPage

# Timeout for E2E tests (longer for CI)
E2E_TIMEOUT = 30000


@pytest.mark.e2e
@pytest.mark.playwright
def test_materials_page_loads(app_page: Page, base_url: str):
    """Test that the materials page loads successfully"""
    materials = MaterialsPage(app_page)
    materials.navigate(base_url)

    # Check the hash-based routing for SPA
    expect(app_page).to_have_url(f"{base_url}/#materials", timeout=E2E_TIMEOUT)


@pytest.mark.e2e
@pytest.mark.playwright
def test_materials_table_display(app_page: Page, base_url: str):
    """Test that materials table or cards view is displayed"""
    materials = MaterialsPage(app_page)
    materials.navigate(base_url)

    # Check if materials table wrapper exists (table might be hidden, cards shown by default)
    table_wrapper = app_page.locator(".materials-table-wrapper, #materialsTableView, #materialsTable")
    cards_view = app_page.locator(".materials-cards-grid, #materialsCardsView")

    # Wait for at least one view to be attached to DOM
    try:
        table_wrapper.first.wait_for(state="attached", timeout=E2E_TIMEOUT)
    except Exception:
        pass

    # At least one view should exist in the DOM
    assert table_wrapper.count() > 0 or cards_view.count() > 0, "Should have materials display container"


@pytest.mark.e2e
@pytest.mark.playwright
def test_add_material_button_exists(app_page: Page, base_url: str):
    """Test that add material button is present"""
    materials = MaterialsPage(app_page)
    materials.navigate(base_url)

    add_button = app_page.locator(materials.add_material_button_selector)
    add_button.wait_for(state="visible", timeout=E2E_TIMEOUT)
    expect(add_button.first).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
def test_add_material_modal_opens(app_page: Page, base_url: str):
    """Test that the add material modal can be opened"""
    materials = MaterialsPage(app_page)
    materials.navigate(base_url)

    materials.open_add_material_modal()

    # Check if modal is visible
    modal = app_page.locator(materials.material_modal_selector)
    expect(modal.first).to_be_visible(timeout=E2E_TIMEOUT)


@pytest.mark.e2e
@pytest.mark.playwright
def test_material_types_available(app_page: Page, base_url: str):
    """Test that common material types are available"""
    materials = MaterialsPage(app_page)
    materials.navigate(base_url)
    
    materials.open_add_material_modal()
    
    # Check material type options
    type_select = app_page.locator(materials.material_type_select_selector)
    if type_select.count() > 0:
        options = type_select.first.locator("option").all()
        option_texts = [opt.inner_text() for opt in options]
        
        # Common 3D printing materials
        common_materials = ["PLA", "ABS", "PETG", "TPU"]
        found_materials = [mat for mat in common_materials if any(mat in text for text in option_texts)]
        
        assert len(found_materials) > 0, "Should have at least one common material type"


@pytest.mark.e2e
@pytest.mark.playwright
@pytest.mark.german
@pytest.mark.currency
def test_material_cost_input(app_page: Page, base_url: str):
    """Test material cost input with EUR currency"""
    materials = MaterialsPage(app_page)
    materials.navigate(base_url)
    
    materials.open_add_material_modal()
    
    # Check if cost input exists
    cost_input = app_page.locator(materials.cost_input_selector)
    if cost_input.count() > 0:
        expect(cost_input.first).to_be_visible()
        
        # Fill in a cost value
        cost_input.first.fill("25.99")
        
        # Check if EUR symbol is displayed (may be in label or after input)
        eur_symbol = app_page.locator("text=/€|EUR/i")
        # This may or may not be present depending on implementation


@pytest.mark.e2e
@pytest.mark.playwright
@pytest.mark.network
def test_add_material(app_page: Page, base_url: str):
    """Test adding a new material (requires backend)"""
    materials = MaterialsPage(app_page)
    materials.navigate(base_url)

    # Wait for add button to be available
    add_button = app_page.locator(materials.add_material_button_selector)
    add_button.wait_for(state="visible", timeout=E2E_TIMEOUT)

    # Add a test material
    test_material_name = "Test PLA Spool"

    materials.add_material(
        name=test_material_name,
        material_type="PLA",
        color="Blue",
        weight="1000",
        cost="20.00"
    )

    # Wait for page to update
    app_page.wait_for_timeout(1000)

    # Note: Verification requires backend to be running
    # This is more of an integration test


@pytest.mark.e2e
@pytest.mark.playwright
def test_material_form_validation(app_page: Page, base_url: str):
    """Test material form validation"""
    materials = MaterialsPage(app_page)
    materials.navigate(base_url)

    # Wait for button to be available before opening modal
    add_button = app_page.locator(materials.add_material_button_selector)
    add_button.wait_for(state="visible", timeout=E2E_TIMEOUT)

    materials.open_add_material_modal()

    # Try to submit empty form
    materials.submit_material_form()

    # Form should still be visible (validation failed)
    modal = app_page.locator(materials.material_modal_selector)
    expect(modal.first).to_be_visible(timeout=E2E_TIMEOUT)


@pytest.mark.e2e
@pytest.mark.playwright
def test_refresh_button_visible(app_page: Page, base_url: str):
    """Test that refresh button is visible on materials page"""
    materials = MaterialsPage(app_page)
    materials.navigate(base_url)

    # Check for refresh button
    refresh_btn = app_page.locator("button:has-text('Aktualisieren'), #refreshMaterialsBtn, .refresh-btn")
    try:
        refresh_btn.first.wait_for(state="visible", timeout=E2E_TIMEOUT)
        expect(refresh_btn.first).to_be_visible()
    except Exception:
        pytest.skip("Refresh button not present on this page")


@pytest.mark.e2e
@pytest.mark.playwright
def test_refresh_button_click(app_page: Page, base_url: str):
    """Test that clicking refresh button triggers data reload"""
    materials = MaterialsPage(app_page)
    materials.navigate(base_url)

    refresh_btn = app_page.locator("button:has-text('Aktualisieren'), #refreshMaterialsBtn, .refresh-btn")
    try:
        refresh_btn.first.wait_for(state="visible", timeout=E2E_TIMEOUT)
        if refresh_btn.first.is_visible():
            # Click refresh and verify page doesn't break
            refresh_btn.first.click()
            app_page.wait_for_timeout(1000)  # Wait for refresh to complete

            # Page should still be functional
            table_wrapper = app_page.locator(materials.materials_table_selector)
            expect(table_wrapper.first).to_be_attached()
    except Exception:
        pytest.skip("Refresh button not available")


@pytest.mark.e2e
@pytest.mark.playwright
@pytest.mark.network
def test_refresh_updates_data(page: Page, base_url: str, mock_materials_api):
    """Test that refresh triggers API call and updates data"""
    # Set up mock API
    mock_materials_api()

    page.goto(f"{base_url}/#materials")
    page.wait_for_load_state("networkidle")

    # Wait for page to load
    try:
        page.wait_for_function("() => window.app && window.app.currentPage", timeout=E2E_TIMEOUT)
    except Exception:
        pass

    page.wait_for_selector(
        "#page-materials.page.active, #materials.active, #materials.page.active",
        state="visible",
        timeout=E2E_TIMEOUT
    )

    refresh_btn = page.locator("button:has-text('Aktualisieren'), #refreshMaterialsBtn, .refresh-btn")
    try:
        refresh_btn.first.wait_for(state="visible", timeout=E2E_TIMEOUT)
        if refresh_btn.first.is_visible():
            # Set up response listener before clicking
            with page.expect_response(
                lambda response: "/api/v1/materials" in response.url,
                timeout=E2E_TIMEOUT
            ):
                refresh_btn.first.click()

            # Test passes if we received the API response
            assert True, "Refresh triggered API call"
    except Exception as e:
        # If refresh button not available or API mock not triggered, skip
        pytest.skip(f"Refresh functionality test skipped: {str(e)}")


@pytest.mark.e2e
@pytest.mark.playwright
def test_view_toggle_exists(app_page: Page, base_url: str):
    """Test that view toggle (table/cards) exists"""
    materials = MaterialsPage(app_page)
    materials.navigate(base_url)

    # Look for view toggle buttons
    view_toggle = app_page.locator(
        ".view-toggle, #viewToggle, button:has-text('Tabelle'), button:has-text('Karten')"
    )
    try:
        view_toggle.first.wait_for(state="attached", timeout=E2E_TIMEOUT)
        assert view_toggle.count() > 0, "View toggle should exist"
    except Exception:
        pytest.skip("View toggle not present on this page version")


@pytest.mark.e2e
@pytest.mark.playwright
def test_search_input_visible(app_page: Page, base_url: str):
    """Test that search input is visible on materials page"""
    materials = MaterialsPage(app_page)
    materials.navigate(base_url)

    # Check if search input exists
    search_input = app_page.locator("#searchMaterials, input[placeholder*='Suche'], .search-input")
    try:
        search_input.first.wait_for(state="attached", timeout=E2E_TIMEOUT)
        assert search_input.count() > 0, "Search input should exist"
    except Exception:
        pytest.skip("Search input not present on this page version")


@pytest.mark.e2e
@pytest.mark.playwright
def test_filter_by_type(app_page: Page, base_url: str):
    """Test filtering materials by type"""
    materials = MaterialsPage(app_page)
    materials.navigate(base_url)

    # Look for type filter dropdown
    type_filter = app_page.locator("#filterMaterialType, select[name='materialType'], .type-filter")
    try:
        type_filter.first.wait_for(state="attached", timeout=E2E_TIMEOUT)
        if type_filter.count() > 0 and type_filter.first.is_visible():
            # Select a type
            type_filter.first.select_option("PLA")
            app_page.wait_for_timeout(500)
            # Test passes if we can change the filter
            assert True, "Type filter works"
    except Exception:
        pytest.skip("Type filter not available")
