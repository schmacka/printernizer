#!/bin/bash
# ============================================================================
# Printernizer Startup Script (DEPRECATED FOR PRODUCTION USE)
# ============================================================================
#
# ⚠️  WARNING: This script is DEPRECATED for production deployments!
#
# For production use, please use one of these recommended methods:
#   1. Docker Standalone (RECOMMENDED): cd docker && docker-compose up -d
#   2. Home Assistant Add-on: Install via HA Add-on Store
#
# This script is maintained for:
#   - Local development and testing
#   - Contributing to the project
#   - Quick prototyping and debugging
#
# See README.md for complete deployment options and guides.
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
export PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/src"
cd src
python main.py