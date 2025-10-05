#!/usr/bin/env python3
"""
Bambu Lab printer utilities and credential management.

This module provides shared utilities for working with Bambu Lab printers,
including secure credential loading and common helper functions.
"""

import os
import sys
import getpass
from typing import Optional, Dict
from pathlib import Path


class BambuCredentials:
    """Secure credential management for Bambu Lab printers."""

    def __init__(self):
        self._credentials_cache: Dict[str, str] = {}

    def get_printer_credentials(self, host: str) -> tuple[str, str]:
        """
        Get printer credentials securely.

        Args:
            host: Printer IP address or hostname

        Returns:
            Tuple of (username, access_code)

        Raises:
            ValueError: If credentials cannot be obtained
        """
        # Try environment variables first
        username = os.getenv('BAMBU_USERNAME', 'bblp')
        access_code = os.getenv('BAMBU_ACCESS_CODE')

        if access_code:
            if self._validate_access_code(access_code):
                return username, access_code
            else:
                raise ValueError("Invalid access code from environment variable")

        # Try cache
        cache_key = f"{host}:{username}"
        if cache_key in self._credentials_cache:
            return username, self._credentials_cache[cache_key]

        # Interactive input as last resort (only in development)
        if self._is_development_environment():
            print(f"Credentials needed for Bambu Lab printer at {host}")
            print("Please set BAMBU_ACCESS_CODE environment variable for production use.")

            access_code = getpass.getpass("Enter 8-digit access code: ")
            if self._validate_access_code(access_code):
                self._credentials_cache[cache_key] = access_code
                return username, access_code
            else:
                raise ValueError("Invalid access code entered")

        raise ValueError(
            "No valid credentials found. Set BAMBU_ACCESS_CODE environment variable "
            "or run in development mode for interactive input."
        )

    def _validate_access_code(self, access_code: str) -> bool:
        """Validate access code format."""
        return (
            isinstance(access_code, str) and
            access_code.isdigit() and
            len(access_code) == 8
        )

    def _is_development_environment(self) -> bool:
        """Check if running in development environment."""
        return (
            os.getenv('ENVIRONMENT', '').lower() in ('development', 'dev', 'test') or
            os.getenv('DEBUG', '').lower() in ('true', '1', 'yes') or
            sys.stdin.isatty()  # Interactive terminal
        )


# Global instance for convenience
_credentials = BambuCredentials()


def get_bambu_credentials(host: str) -> tuple[str, str]:
    """
    Get Bambu Lab printer credentials securely.

    Args:
        host: Printer IP address or hostname

    Returns:
        Tuple of (username, access_code)

    Example:
        >>> from src.utils.bambu_utils import get_bambu_credentials
        >>> username, access_code = get_bambu_credentials("192.168.1.100")
    """
    return _credentials.get_printer_credentials(host)


def print_credential_setup_help():
    """Print example environment setup instructions."""
    print("Bambu Lab Printer Credential Setup")
    print("=" * 40)
    print()
    print("For security, credentials should be provided via environment variables:")
    print()
    print("Windows (PowerShell):")
    print("  $env:BAMBU_USERNAME='bblp'")
    print("  $env:BAMBU_ACCESS_CODE='12345678'  # Replace with actual code")
    print()
    print("Windows (Command Prompt):")
    print("  set BAMBU_USERNAME=bblp")
    print("  set BAMBU_ACCESS_CODE=12345678  # Replace with actual code")
    print()
    print("Linux/Mac:")
    print("  export BAMBU_USERNAME=bblp")
    print("  export BAMBU_ACCESS_CODE=12345678  # Replace with actual code")
    print()
    print("Or create a .env file in the project root:")
    print("  BAMBU_USERNAME=bblp")
    print("  BAMBU_ACCESS_CODE=12345678  # Replace with actual code")
    print()
