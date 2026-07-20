#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Capture screenshots of the Printernizer web application for README documentation.

Usage:
    # 1. Start Printernizer (serves the frontend at http://localhost:8000)
    python src/main.py

    # 2. In a second shell:
    python scripts/testing/capture_screenshots.py [--url URL] [--out DIR]

Screenshots are written to `screenshots/` (the directory referenced by README.md).
The UI locale is forced to English so the captures match the documentation language.
"""
import argparse
import os
import sys

from playwright.sync_api import sync_playwright

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Pages to capture: (filename, nav hash, description)
PAGES = [
    ('01-dashboard.png', 'dashboard', 'Dashboard overview'),
    ('02-library.png', 'library', 'Library'),
    ('03-printers.png', 'printers', 'Printers'),
    ('04-jobs.png', 'jobs', 'Jobs'),
    ('05-files.png', 'files', 'File management'),
    ('06-materials.png', 'materials', 'Material inventory'),
    ('07-generator.png', 'generator', 'Model generator'),
]


# Transient overlays that would otherwise cover the UI in a capture:
# toast notifications ("System Ready", ...) and the auto-discovery banner.
DISMISS_OVERLAYS = (
    "document.querySelectorAll("
    "'.toast, .toast-container, #toast-container, .discovered-printers-banner'"
    ").forEach(el => el.remove())"
)


def prepare(page, url):
    """Force English locale and dismiss transient overlays before capturing."""
    page.goto(url, wait_until='domcontentloaded')
    page.evaluate("localStorage.setItem('printernizer_locale', 'en')")
    page.reload(wait_until='networkidle')
    page.wait_for_timeout(3000)
    page.evaluate(DISMISS_OVERLAYS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://localhost:8000',
                        help='Base URL of a running Printernizer instance')
    parser.add_argument('--out', default='screenshots',
                        help='Output directory (default: screenshots/)')
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    print(f"Capturing screenshots from {args.url} into {args.out}/")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1600, 'height': 1000})
        page = context.new_page()
        page.set_default_navigation_timeout(60000)
        page.set_default_timeout(30000)

        try:
            prepare(page, args.url)

            for filename, nav, description in PAGES:
                print(f"Capturing {description}...")
                page.goto(f"{args.url}/#{nav}", wait_until='networkidle')
                page.wait_for_timeout(2500)
                page.evaluate(DISMISS_OVERLAYS)
                page.screenshot(path=os.path.join(args.out, filename), full_page=True)
                print(f"  -> {filename}")

            # Mobile view
            print("Capturing mobile view...")
            mobile_context = browser.new_context(
                viewport={'width': 390, 'height': 844},
                device_scale_factor=2,
                is_mobile=True,
                has_touch=True,
            )
            mobile_page = mobile_context.new_page()
            mobile_page.set_default_navigation_timeout(60000)
            prepare(mobile_page, args.url)
            # Viewport-only: a full-page mobile capture is several thousand
            # pixels tall and unusable in the README.
            mobile_page.screenshot(
                path=os.path.join(args.out, '08-mobile-view.png')
            )
            print("  -> 08-mobile-view.png")
            mobile_context.close()

            print(f"\nAll screenshots captured to {os.path.abspath(args.out)}")
            return 0

        except Exception as exc:
            print(f"Error capturing screenshots: {exc}")
            try:
                page.screenshot(path=os.path.join(args.out, 'error.png'), full_page=True)
                print("Error screenshot saved as error.png")
            except Exception:
                pass
            return 1
        finally:
            browser.close()


if __name__ == '__main__':
    sys.exit(main())
