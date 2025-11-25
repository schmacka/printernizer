#!/usr/bin/env python3
"""
Capture fresh screenshots of Printernizer application for README.md
"""
from playwright.sync_api import sync_playwright
import time
from pathlib import Path

# Create screenshots directory if it doesn't exist
screenshots_dir = Path("screenshots")
screenshots_dir.mkdir(exist_ok=True)

def capture_screenshots():
    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)

        # Create context with larger viewport for desktop screenshots
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        print("Starting screenshot capture...")

        # 1. Dashboard Overview
        print("[1/5] Capturing Dashboard Overview...")
        page.goto('http://localhost:8000/')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)  # Extra wait for any animations
        page.screenshot(path='screenshots/01-dashboard.png', full_page=True)
        print("  -> Saved: 01-dashboard.png")

        # 2. File Management
        print("[2/5] Capturing File Management...")
        # Try to navigate to files section if it exists
        # Check if there's a navigation link or button for files
        try:
            # Look for files navigation
            files_nav = page.locator('text=/files/i').first
            if files_nav.is_visible(timeout=2000):
                files_nav.click()
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(2000)
        except:
            # If no navigation, files might be on the main page or a specific route
            try:
                page.goto('http://localhost:8000/#files')
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(2000)
            except:
                pass

        page.screenshot(path='screenshots/02-file-management.png', full_page=True)
        print("  -> Saved: 02-file-management.png")

        # 3. Jobs & Printer Management
        print("[3/5] Capturing Jobs & Printers...")
        try:
            # Try to navigate to jobs section
            jobs_nav = page.locator('text=/jobs/i').first
            if jobs_nav.is_visible(timeout=2000):
                jobs_nav.click()
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(2000)
        except:
            # Try direct navigation
            try:
                page.goto('http://localhost:8000/#jobs')
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(2000)
            except:
                pass

        page.screenshot(path='screenshots/03-jobs-printers.png', full_page=True)
        print("  -> Saved: 03-jobs-printers.png")

        # 4. Printer Status Card (focus on a specific card if available)
        print("[4/5] Capturing Printer Status Card...")
        # Go back to dashboard where printer cards are
        page.goto('http://localhost:8000/')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(2000)

        # Try to find a printer card and capture it
        try:
            # Look for printer card elements by class
            printer_cards = page.locator('.printer-card').all()
            if len(printer_cards) > 0:
                # Capture the first printer card
                printer_cards[0].screenshot(path='screenshots/04-printer-status-card.png')
                print("  -> Saved: 04-printer-status-card.png (focused card)")
            else:
                # No printer cards found, capture the printer grid area or full dashboard
                print("  -> No printer cards found, capturing dashboard view")
                page.screenshot(path='screenshots/04-printer-status-card.png', full_page=False)
                print("  -> Saved: 04-printer-status-card.png (dashboard view)")
        except Exception as e:
            # Fallback: capture full page
            print(f"  -> Error capturing printer card: {e}")
            page.screenshot(path='screenshots/04-printer-status-card.png', full_page=False)
            print("  -> Saved: 04-printer-status-card.png (fallback viewport)")

        # 5. Mobile Responsive Design
        print("[5/5] Capturing Mobile View...")
        # Create new context with mobile viewport
        mobile_context = browser.new_context(
            viewport={'width': 375, 'height': 812},
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
        )
        mobile_page = mobile_context.new_page()
        mobile_page.goto('http://localhost:8000/')
        mobile_page.wait_for_load_state('networkidle')
        mobile_page.wait_for_timeout(2000)
        mobile_page.screenshot(path='screenshots/05-mobile-view.png', full_page=True)
        print("  -> Saved: 05-mobile-view.png")

        # Close contexts and browser
        mobile_context.close()
        context.close()
        browser.close()

        print("\nScreenshot capture complete!")
        print(f"Screenshots saved to: {screenshots_dir.absolute()}")

if __name__ == "__main__":
    try:
        capture_screenshots()
    except Exception as e:
        print(f"ERROR: {e}")
        raise
