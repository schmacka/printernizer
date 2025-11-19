#!/usr/bin/env python3
"""
DEPRECATED: This module has been moved to src.utils.bambu_utils

This file remains for backward compatibility with existing scripts.
Please update imports to use: from src.utils.bambu_utils import get_bambu_credentials
"""

import warnings

# Import from new location
from src.utils.bambu_utils import (
    BambuCredentials,
    get_bambu_credentials,
    print_credential_setup_help as setup_example_env
)

# Deprecated warning
warnings.warn(
    "scripts.bambu_credentials is deprecated. "
    "Use 'from src.utils.bambu_utils import get_bambu_credentials' instead.",
    DeprecationWarning,
    stacklevel=2
)

# For backward compatibility
_credentials = BambuCredentials()


if __name__ == "__main__":
    setup_example_env()
