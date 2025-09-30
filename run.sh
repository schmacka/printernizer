#!/bin/bash
# Printernizer Startup Script
# Ensures proper Python path and working directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
export PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/src"
cd src
python main.py