"""
Page Object Model for Printernizer Statistics page
"""
from playwright.sync_api import Page, expect
from typing import Optional


class StatisticsPage:
    """Page object for the statistics/dashboard page"""
    
    def __init__(self, page: Page):
        self.page = page
        
        # Selectors for dashboard statistics
        self.stats_container_selector = ".stats-container, .dashboard-stats"
        self.stat_card_selector = ".stat-card"
        self.stat_value_selector = ".stat-value"
        self.stat_label_selector = ".stat-label"
        
        # Chart selectors
        self.chart_container_selector = ".chart-container, #chartsContainer"
        self.chart_selector = "canvas, .chart"
        
        # Filter selectors
        self.time_filter_selector = "select.time-filter, #timeRangeFilter"
        self.printer_filter_selector = "select.printer-filter, #printerFilter"
        
        # Specific stat selectors
        self.total_jobs_selector = "#statTotalJobs, [data-stat='total-jobs']"
        self.total_print_time_selector = "#statTotalPrintTime, [data-stat='total-time']"
        self.total_filament_selector = "#statTotalFilament, [data-stat='total-filament']"
        self.success_rate_selector = "#statSuccessRate, [data-stat='success-rate']"
        
    def navigate(self, base_url: str):
        """Navigate to statistics/dashboard page"""
        self.page.goto(f"{base_url}/#dashboard", wait_until="domcontentloaded")
        self.page.wait_for_load_state("networkidle")
        # Wait for app initialization
        self.page.wait_for_function("() => window.app && window.app.currentPage")
        # Wait for the dashboard section to be visible
        self.page.wait_for_selector("#dashboard.active, [id='dashboard'].page.active", state="visible", timeout=5000)
        
    def is_loaded(self) -> bool:
        """Check if the statistics page is loaded"""
        try:
            self.page.wait_for_selector(self.stats_container_selector, timeout=5000)
            return True
        except:
            return False
            
    def get_stat_cards_count(self) -> int:
        """Get the number of stat cards displayed"""
        return self.page.locator(self.stat_card_selector).count()
        
    def get_stat_value(self, stat_label: str) -> Optional[str]:
        """Get the value of a specific statistic by its label"""
        stat_card = self.page.locator(f"{self.stat_card_selector}:has-text('{stat_label}')")
        if stat_card.count() > 0:
            value_element = stat_card.locator(self.stat_value_selector).first
            return value_element.inner_text()
        return None
        
    def get_all_stat_values(self) -> dict[str, str]:
        """Get all statistics as a dictionary of label: value"""
        stats = {}
        stat_cards = self.page.locator(self.stat_card_selector).all()
        for card in stat_cards:
            label_element = card.locator(self.stat_label_selector)
            value_element = card.locator(self.stat_value_selector)
            if label_element.count() > 0 and value_element.count() > 0:
                label = label_element.inner_text()
                value = value_element.inner_text()
                stats[label] = value
        return stats
        
    def wait_for_stats_to_load(self, timeout: int = 5000):
        """Wait for statistics to load (not showing loading placeholder)"""
        # Wait for at least one stat card with actual data
        self.page.wait_for_function(
            """() => {
                const statValues = document.querySelectorAll('.stat-value');
                return Array.from(statValues).some(el => 
                    el.textContent && 
                    el.textContent.trim() !== '' && 
                    el.textContent.trim() !== '--' &&
                    !el.textContent.includes('Lade')
                );
            }""",
            timeout=timeout
        )
        
    def expect_stat_exists(self, stat_label: str):
        """Assert that a specific statistic exists"""
        expect(self.page.locator(f"{self.stat_card_selector}:has-text('{stat_label}')")).to_be_visible()
        
    def has_charts(self) -> bool:
        """Check if charts are displayed"""
        return self.page.locator(self.chart_selector).count() > 0
        
    def get_charts_count(self) -> int:
        """Get the number of charts displayed"""
        return self.page.locator(self.chart_selector).count()
        
    def apply_time_filter(self, filter_value: str):
        """Apply a time range filter"""
        time_filter = self.page.locator(self.time_filter_selector)
        if time_filter.count() > 0:
            time_filter.first.select_option(filter_value)
            self.page.wait_for_timeout(500)  # Wait for filter to apply
            
    def apply_printer_filter(self, printer_name: str):
        """Apply a printer filter"""
        printer_filter = self.page.locator(self.printer_filter_selector)
        if printer_filter.count() > 0:
            printer_filter.first.select_option(label=printer_name)
            self.page.wait_for_timeout(500)  # Wait for filter to apply
            
    def expect_stats_not_empty(self):
        """Assert that statistics are not empty"""
        stats = self.get_all_stat_values()
        assert len(stats) > 0, "Should have at least one statistic"
        # Check that at least one stat has a real value (not loading state)
        has_real_value = any(
            value and value.strip() and value.strip() != '--' and 'Lade' not in value
            for value in stats.values()
        )
        assert has_real_value, "Should have at least one stat with real data"
