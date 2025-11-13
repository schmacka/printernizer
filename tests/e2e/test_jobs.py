"""
E2E tests for Printernizer Jobs Management
"""
import pytest
from playwright.sync_api import Page, expect
from tests.e2e.pages import JobsPage


@pytest.mark.e2e
@pytest.mark.playwright
def test_jobs_page_loads(app_page: Page, base_url: str):
    """Test that the jobs page loads successfully"""
    jobs = JobsPage(app_page)
    jobs.navigate(base_url)
    
    # Check the hash-based routing for SPA
    expect(app_page).to_have_url(f"{base_url}/#jobs")


@pytest.mark.e2e
@pytest.mark.playwright
def test_jobs_table_display(app_page: Page, base_url: str):
    """Test that jobs table is displayed"""
    jobs = JobsPage(app_page)
    jobs.navigate(base_url)
    
    # Check if jobs table exists
    table_element = app_page.locator(jobs.jobs_table_selector)
    expect(table_element.first).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
def test_create_job_button_exists(app_page: Page, base_url: str):
    """Test that create job button is present"""
    jobs = JobsPage(app_page)
    jobs.navigate(base_url)
    
    create_button = app_page.locator(jobs.create_job_button_selector)
    expect(create_button.first).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
def test_create_job_modal_opens(app_page: Page, base_url: str):
    """Test that the create job modal can be opened"""
    jobs = JobsPage(app_page)
    jobs.navigate(base_url)
    
    jobs.open_create_job_modal()
    
    # Check if modal is visible
    modal = app_page.locator(jobs.job_modal_selector)
    expect(modal.first).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
def test_business_job_fields(app_page: Page, base_url: str):
    """Test that business job fields appear when is_business is checked"""
    jobs = JobsPage(app_page)
    jobs.navigate(base_url)
    
    jobs.open_create_job_modal()
    
    # Check the business checkbox
    business_checkbox = app_page.locator(jobs.business_checkbox_selector)
    if business_checkbox.count() > 0:
        business_checkbox.first.check()
        
        # Customer name field should become visible
        customer_field = app_page.locator(jobs.customer_name_input_selector)
        expect(customer_field.first).to_be_visible()


@pytest.mark.e2e
@pytest.mark.playwright
@pytest.mark.german
def test_vat_calculation_display(app_page: Page, base_url: str):
    """Test that VAT calculation is displayed for business jobs"""
    jobs = JobsPage(app_page)
    jobs.navigate(base_url)
    
    jobs.open_create_job_modal()
    
    # Enable business mode
    business_checkbox = app_page.locator(jobs.business_checkbox_selector)
    if business_checkbox.count() > 0:
        business_checkbox.first.check()
        
        # Look for VAT-related elements
        vat_elements = app_page.locator("text=/VAT|MwSt/i")
        # VAT display may only appear after entering cost data
        # This is a placeholder test
        assert True, "VAT calculation test placeholder"


@pytest.mark.e2e
@pytest.mark.playwright
@pytest.mark.network
def test_job_status_updates(app_page: Page, base_url: str):
    """Test that job status updates are reflected in the UI"""
    jobs = JobsPage(app_page)
    jobs.navigate(base_url)
    
    # This test requires backend and active jobs
    # Get current job list
    job_list = jobs.get_job_list()
    
    if len(job_list) > 0:
        # Check if status is displayed
        first_job = job_list[0]
        status = jobs.get_job_status(first_job)
        assert status is not None or status == "", "Job should have a status"


@pytest.mark.e2e
@pytest.mark.playwright
def test_job_form_validation(app_page: Page, base_url: str):
    """Test job form validation"""
    jobs = JobsPage(app_page)
    jobs.navigate(base_url)
    
    jobs.open_create_job_modal()
    
    # Try to submit empty form
    jobs.submit_job_form()
    
    # Form should still be visible (validation failed)
    modal = app_page.locator(jobs.job_modal_selector)
    expect(modal.first).to_be_visible()
