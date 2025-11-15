#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Capture screenshots of Printernizer web application for README documentation
"""
from playwright.sync_api import sync_playwright
import time
import os
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Create screenshots directory if it doesn't exist
screenshots_dir = os.path.join("docs", "screenshots")
os.makedirs(screenshots_dir, exist_ok=True)

print("Starting screenshot capture...")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()

    # Set longer timeout for page navigation
    page.set_default_navigation_timeout(60000)
    page.set_default_timeout(30000)

    try:
        # Wait for backend to fully initialize (60+ seconds for printer connections, data loading, etc.)
        print("Waiting 60 seconds for backend to fully initialize (printer connections, data loading)...")
        for i in range(12):
            print(f"  {(i+1)*5} seconds elapsed...")
            time.sleep(5)
        print("Backend initialization complete!")

        # Navigate to the application (frontend HTTP server on port 3000)
        print("Navigating to http://localhost:3000...")
        page.goto('http://localhost:3000', wait_until='domcontentloaded')
        page.wait_for_load_state('networkidle', timeout=60000)
        print("Page loaded successfully!")

        # Wait for frontend to fully render and populate with data
        print("Waiting for frontend to fully render...")
        time.sleep(5)

        # Capture 1: Main Dashboard
        print("Capturing dashboard view...")
        page.screenshot(path=os.path.join(screenshots_dir, '01-dashboard.png'), full_page=True)
        print("✓ Dashboard screenshot saved")

        # Capture 2: Try to navigate to Files page if available
        print("Looking for file management page...")
        files_link = page.locator('a:has-text("Drucker-Dateien"), a:has-text("Files"), a:has-text("Dateien")').first
        if files_link.is_visible(timeout=5000):
            files_link.click()
            page.wait_for_load_state('networkidle', timeout=60000)
            print("Waiting for file data to load...")
            time.sleep(5)
            page.screenshot(path=os.path.join(screenshots_dir, '02-file-management.png'), full_page=True)
            print("✓ File management screenshot saved")
        else:
            print("ℹ File management page not found")

        # Capture 3: Try to navigate to Jobs/Printers page
        print("Looking for jobs/printers page...")
        # Go back to home first
        page.goto('http://localhost:3000')
        page.wait_for_load_state('networkidle', timeout=60000)
        time.sleep(3)

        jobs_link = page.locator('a:has-text("Aufträge"), a:has-text("Jobs"), a:has-text("Printers"), a:has-text("Drucker")').first
        if jobs_link.is_visible(timeout=5000):
            jobs_link.click()
            page.wait_for_load_state('networkidle', timeout=60000)
            print("Waiting for job data to load...")
            time.sleep(5)
            page.screenshot(path=os.path.join(screenshots_dir, '03-jobs-printers.png'), full_page=True)
            print("✓ Jobs/Printers screenshot saved")
        else:
            print("ℹ Jobs/Printers page not found")

        # Capture 4: Printer status cards (if on dashboard)
        print("Capturing printer status detail...")
        page.goto('http://localhost:3000')
        page.wait_for_load_state('networkidle', timeout=60000)
        time.sleep(5)

        # Try to find printer status cards
        printer_cards = page.locator('.printer-card, .status-card, [class*="printer"]').first
        if printer_cards.is_visible(timeout=5000):
            printer_cards.screenshot(path=os.path.join(screenshots_dir, '04-printer-status-card.png'))
            print("✓ Printer status card screenshot saved")
        else:
            print("ℹ Printer status card not found, using full page")
            page.screenshot(path=os.path.join(screenshots_dir, '04-printer-status-card.png'))

        # Capture 5: Mobile view
        print("Capturing mobile view...")
        context2 = browser.new_context(viewport={"width": 375, "height": 667})
        mobile_page = context2.new_page()
        mobile_page.set_default_navigation_timeout(60000)
        mobile_page.set_default_timeout(30000)
        mobile_page.goto('http://localhost:3000', wait_until='domcontentloaded')
        mobile_page.wait_for_load_state('networkidle', timeout=60000)
        print("Waiting for mobile view to render...")
        time.sleep(5)
        mobile_page.screenshot(path=os.path.join(screenshots_dir, '05-mobile-view.png'), full_page=True)
        print("✓ Mobile view screenshot saved")
        mobile_page.close()
        context2.close()

        print("\n✓ All screenshots captured successfully!")
        print(f"Screenshots saved to: {os.path.abspath(screenshots_dir)}")

    except Exception as e:
        print(f"✗ Error capturing screenshots: {e}")
        # Take an error screenshot
        try:
            page.screenshot(path=os.path.join(screenshots_dir, 'error.png'), full_page=True)
            print("Error screenshot saved")
        except:
            pass
    finally:
        browser.close()
