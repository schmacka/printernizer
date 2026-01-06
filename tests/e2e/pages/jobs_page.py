"""
Page Object Model for Printernizer Jobs page
"""
from playwright.sync_api import Page, expect
from typing import Optional


class JobsPage:
    """Page object for the jobs page"""

    # Default timeout for CI environments
    DEFAULT_TIMEOUT = 30000

    def __init__(self, page: Page):
        self.page = page

        # Selectors - matching actual HTML structure from index.html
        self.jobs_table_selector = "#jobsTable, .jobs-table"
        self.job_row_selector = "#jobsTableBody tr, .job-row"
        self.create_job_button_selector = "#createJobBtn"
        self.job_modal_selector = "#createJobModal, #jobModal, .job-modal, .modal:has(#createJobForm)"
        self.job_name_input_selector = "#jobName, input[name='job_name']"
        self.file_select_selector = "#fileSelect, select[name='file']"
        self.printer_select_selector = "#printerSelect, select[name='printer']"
        self.business_checkbox_selector = "#isBusiness, input[name='is_business'], input[type='checkbox'][id*='business']"
        self.customer_name_input_selector = "#customerName, input[name='customer_name']"
        self.submit_job_button_selector = ".submit-job-btn, button[type='submit'][form='createJobForm']"
        self.job_status_selector = ".job-status"

    def navigate(self, base_url: str):
        """Navigate to jobs page with robust waiting"""
        self.page.goto(f"{base_url}/#jobs", wait_until="domcontentloaded")
        self.page.wait_for_load_state("networkidle")

        # Wait for app initialization with longer timeout for CI
        try:
            self.page.wait_for_function(
                "() => window.app && window.app.currentPage !== undefined",
                timeout=self.DEFAULT_TIMEOUT
            )
        except Exception:
            # Fallback: just wait for the page element to exist
            pass

        # Wait for the jobs page section to be visible (try both ID formats)
        self.page.wait_for_selector(
            "#page-jobs.active, #jobs.active, #page-jobs.page.active",
            state="visible",
            timeout=self.DEFAULT_TIMEOUT
        )

    def open_create_job_modal(self):
        """Open the create job modal"""
        # Wait for button to be clickable
        self.page.wait_for_selector(self.create_job_button_selector, state="visible", timeout=self.DEFAULT_TIMEOUT)
        self.page.click(self.create_job_button_selector)
        self.page.wait_for_selector(self.job_modal_selector, state="visible", timeout=self.DEFAULT_TIMEOUT)
        
    def fill_job_form(
        self, 
        job_name: str, 
        file_name: Optional[str] = None,
        printer_name: Optional[str] = None,
        is_business: bool = False,
        customer_name: Optional[str] = None
    ):
        """Fill out the job creation form"""
        self.page.fill(self.job_name_input_selector, job_name)
        
        if file_name:
            self.page.select_option(self.file_select_selector, label=file_name)
            
        if printer_name:
            self.page.select_option(self.printer_select_selector, label=printer_name)
            
        if is_business:
            self.page.check(self.business_checkbox_selector)
            if customer_name:
                self.page.fill(self.customer_name_input_selector, customer_name)
                
    def submit_job_form(self):
        """Submit the job creation form"""
        self.page.click(self.submit_job_button_selector)
        
    def create_job(
        self,
        job_name: str,
        file_name: Optional[str] = None,
        printer_name: Optional[str] = None,
        is_business: bool = False,
        customer_name: Optional[str] = None
    ):
        """Complete flow to create a new job"""
        self.open_create_job_modal()
        self.fill_job_form(job_name, file_name, printer_name, is_business, customer_name)
        self.submit_job_form()
        # Wait for modal to close
        self.page.wait_for_selector(self.job_modal_selector, state="hidden", timeout=self.DEFAULT_TIMEOUT)
        
    def get_job_list(self) -> list[str]:
        """Get list of all job names"""
        names = []
        rows = self.page.locator(self.job_row_selector).all()
        for row in rows:
            name_element = row.locator(".job-name, td:nth-child(2)")
            if name_element.count() > 0:
                names.append(name_element.inner_text())
        return names
        
    def get_job_status(self, job_name: str) -> Optional[str]:
        """Get status of a specific job"""
        job_row = self.page.locator(f"{self.job_row_selector}:has-text('{job_name}')")
        if job_row.count() > 0:
            status = job_row.locator(self.job_status_selector).first
            return status.inner_text()
        return None
        
    def expect_job_in_list(self, job_name: str):
        """Assert that a job appears in the list"""
        expect(self.page.locator(f"{self.job_row_selector}:has-text('{job_name}')")).to_be_visible()
        
    def expect_job_status(self, job_name: str, expected_status: str):
        """Assert that a job has a specific status"""
        job_row = self.page.locator(f"{self.job_row_selector}:has-text('{job_name}')")
        expect(job_row.locator(self.job_status_selector)).to_have_text(expected_status)
