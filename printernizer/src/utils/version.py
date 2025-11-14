"""
Version management utilities.
Extracts version information from git tags and provides fallback.
"""

import subprocess
from pathlib import Path


def get_version(fallback: str = "2.6.9") -> str:
    """
    Get application version from git tags.

    Tries to extract version from git describe, falls back to hardcoded version.

    Args:
        fallback: Version string to use if git is unavailable

    Returns:
        Version string (e.g., "2.3.0" or "2.3.0-3-g1234567")
    """
    try:
        # Try to get version from git describe
        # This will return something like "v1.4.2" or "v1.4.2-3-g1234567"
        result = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
            cwd=Path(__file__).parent.parent.parent
        )

        if result.returncode == 0 and result.stdout:
            version = result.stdout.strip()
            # Remove leading 'v' if present
            if version.startswith('v'):
                version = version[1:]
            return version

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        # Git not available or command failed
        pass

    # Fallback to hardcoded version
    return fallback


def get_short_version(fallback: str = "2.6.9") -> str:
    """
    Get short version (major.minor.patch only).

    Args:
        fallback: Version string to use if git is unavailable

    Returns:
        Short version string (e.g., "2.3.0")
    """
    full_version = get_version(fallback)

    # Extract major.minor.patch from versions like "1.4.2-3-g1234567"
    parts = full_version.split('-')
    if parts:
        return parts[0]

    return fallback


if __name__ == "__main__":
    # For testing
    print(f"Full version: {get_version()}")
    print(f"Short version: {get_short_version()}")
