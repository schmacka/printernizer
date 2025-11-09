"""
Capture screenshots of the Printernizer application for README documentation
"""
from playwright.sync_api import sync_playwright
import time
import os
import sys

# Ensure UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Create screenshots directory
screenshots_dir = "screenshots"
os.makedirs(screenshots_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})

    try:
        # Navigate to the application with longer timeout
        print("Navigating to http://localhost:8000...")
        page.goto('http://localhost:8000', timeout=60000)
        page.wait_for_load_state('networkidle', timeout=60000)

        # Wait for initial content to load
        print("Waiting for page to load...")
        time.sleep(3)

        # 1. Dashboard screenshot
        print("Capturing dashboard...")
        page.screenshot(path=f'{screenshots_dir}/01-dashboard.png', full_page=True)

        # 2. Navigate to File Management (Drucker-Dateien)
        print("Navigating to file management...")
        try:
            # Try to find and click the file management link
            file_link = page.locator('a:has-text("Drucker-Dateien"), a:has-text("Files"), a:has-text("Dateien")')
            if file_link.count() > 0:
                file_link.first.click()
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                print("Capturing file management view...")
                page.screenshot(path=f'{screenshots_dir}/02-file-management.png', full_page=True)
            else:
                print("File management link not found, trying URL navigation...")
                page.goto('http://localhost:8000/files.html')
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                page.screenshot(path=f'{screenshots_dir}/02-file-management.png', full_page=True)
        except Exception as e:
            print(f"Could not navigate to file management: {e}")

        # 3. Navigate to Job Management (Aufträge)
        print("Navigating to job management...")
        try:
            page.goto('http://localhost:8000')
            page.wait_for_load_state('networkidle')
            time.sleep(1)

            job_link = page.locator('a:has-text("Aufträge"), a:has-text("Jobs"), a:has-text("Job")')
            if job_link.count() > 0:
                job_link.first.click()
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                print("Capturing job management view...")
                page.screenshot(path=f'{screenshots_dir}/03-job-management.png', full_page=True)
            else:
                print("Job management link not found, trying URL navigation...")
                page.goto('http://localhost:8000/jobs.html')
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                page.screenshot(path=f'{screenshots_dir}/03-job-management.png', full_page=True)
        except Exception as e:
            print(f"Could not navigate to job management: {e}")

        # 4. Navigate to Printer Configuration (Drucker)
        print("Navigating to printer configuration...")
        try:
            page.goto('http://localhost:8000')
            page.wait_for_load_state('networkidle')
            time.sleep(1)

            printer_link = page.locator('a:has-text("Drucker"), a:has-text("Printers"), a:has-text("Configuration")')
            if printer_link.count() > 0:
                printer_link.first.click()
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                print("Capturing printer configuration view...")
                page.screenshot(path=f'{screenshots_dir}/04-printer-config.png', full_page=True)
            else:
                print("Printer configuration link not found, trying URL navigation...")
                page.goto('http://localhost:8000/printers.html')
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                page.screenshot(path=f'{screenshots_dir}/04-printer-config.png', full_page=True)
        except Exception as e:
            print(f"Could not navigate to printer configuration: {e}")

        # 5. Go back to dashboard for a final shot
        print("Returning to dashboard for final screenshot...")
        page.goto('http://localhost:8000')
        page.wait_for_load_state('networkidle')
        time.sleep(2)

        # Try to capture a printer status card if visible
        printer_cards = page.locator('.printer-card, [class*="printer"]').count()
        if printer_cards > 0:
            print("Capturing printer status cards...")
            page.screenshot(path=f'{screenshots_dir}/05-printer-status.png')

        print("\n✅ Screenshots captured successfully!")
        print(f"Screenshots saved in: {screenshots_dir}/")
        print("\nGenerated files:")
        for file in os.listdir(screenshots_dir):
            if file.endswith('.png'):
                print(f"  - {file}")

    except Exception as e:
        print(f"❌ Error during screenshot capture: {e}")
        # Take an error screenshot
        page.screenshot(path=f'{screenshots_dir}/error.png', full_page=True)
        print(f"Error screenshot saved to {screenshots_dir}/error.png")

    finally:
        browser.close()
