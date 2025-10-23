#!/bin/bash
# Sync Home Assistant Add-on Files
# This script synchronizes the shared codebase to the Home Assistant add-on directory
# Run this script whenever you make changes to src/, frontend/, requirements.txt, or database_schema.sql

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Syncing Printernizer files to Home Assistant add-on directory...${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
ADDON_DIR="$ROOT_DIR/printernizer"

# Sync files
echo -e "${GREEN}Syncing requirements.txt...${NC}"
cp "$ROOT_DIR/requirements.txt" "$ADDON_DIR/"

echo -e "${GREEN}Syncing database_schema.sql...${NC}"
cp "$ROOT_DIR/database_schema.sql" "$ADDON_DIR/"

echo -e "${GREEN}Syncing src/ directory...${NC}"
rm -rf "$ADDON_DIR/src"
cp -r "$ROOT_DIR/src" "$ADDON_DIR/"

echo -e "${GREEN}Syncing frontend/ directory...${NC}"
rm -rf "$ADDON_DIR/frontend"
cp -r "$ROOT_DIR/frontend" "$ADDON_DIR/"

echo -e "${BLUE}✓ Sync complete!${NC}"
echo ""
echo "The following files have been synchronized:"
echo "  - requirements.txt"
echo "  - database_schema.sql"
echo "  - src/"
echo "  - frontend/"
echo ""
echo "Don't forget to commit these changes if you're updating the add-on!"
