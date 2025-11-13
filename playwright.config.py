"""
Playwright Configuration for Printernizer E2E Tests
"""
import os
from typing import Dict

# Base URL for testing (can be overridden with --base-url)
BASE_URL = os.getenv("PLAYWRIGHT_BASE_URL", "http://localhost:8000")

# Browser configuration
BROWSERS = ["chromium", "firefox", "webkit"]
HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"

# Timeouts (in milliseconds)
TIMEOUT = 30000  # 30 seconds
NAVIGATION_TIMEOUT = 30000
ACTION_TIMEOUT = 10000

# Screenshot and video settings
SCREENSHOT_ON_FAILURE = True
VIDEO_ON_FAILURE = True

# Viewport size
VIEWPORT = {"width": 1280, "height": 720}

# Slow motion (for debugging, in milliseconds)
SLOW_MO = int(os.getenv("PLAYWRIGHT_SLOW_MO", "0"))

# Test artifacts directory
ARTIFACTS_DIR = "test-reports/playwright"

# Playwright configuration dictionary
PLAYWRIGHT_CONFIG: Dict = {
    "base_url": BASE_URL,
    "timeout": TIMEOUT,
    "headless": HEADLESS,
    "viewport": VIEWPORT,
    "screenshot": "only-on-failure" if SCREENSHOT_ON_FAILURE else "off",
    "video": "retain-on-failure" if VIDEO_ON_FAILURE else "off",
    "trace": "retain-on-failure",
    "slow_mo": SLOW_MO,
}

# pytest-playwright configuration
def pytest_configure(config):
    """Configure pytest with Playwright settings"""
    config.addinivalue_line(
        "markers", "playwright: mark test as a Playwright E2E test"
    )
    config.addinivalue_line(
        "markers", "browser: specify browser(s) to run test on"
    )
