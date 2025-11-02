#!/bin/bash
#
# sync-ha-addon.sh
# Syncs source code from /src to /printernizer/src for Home Assistant add-on
#
# This script maintains a single source of truth in /src/ while ensuring
# the Home Assistant add-on has the files it needs in its build context.
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${YELLOW}=== Printernizer HA Add-on Sync ===${NC}"
echo "Project root: $PROJECT_ROOT"
echo ""

# Check if rsync is available
if ! command -v rsync &> /dev/null; then
    echo -e "${RED}Error: rsync is not installed${NC}"
    echo "Please install rsync to use this script"
    exit 1
fi

# Sync source code
echo -e "${YELLOW}Syncing src/ → printernizer/src/${NC}"
rsync -av --delete \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='.pytest_cache' \
    --exclude='*.egg-info' \
    "$PROJECT_ROOT/src/" \
    "$PROJECT_ROOT/printernizer/src/"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Source code synced successfully${NC}"
else
    echo -e "${RED}✗ Source code sync failed${NC}"
    exit 1
fi

echo ""

# Sync frontend
echo -e "${YELLOW}Syncing frontend/ → printernizer/frontend/${NC}"
rsync -av --delete \
    --exclude='node_modules' \
    --exclude='.vite' \
    --exclude='dist' \
    "$PROJECT_ROOT/frontend/" \
    "$PROJECT_ROOT/printernizer/frontend/"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Frontend synced successfully${NC}"
else
    echo -e "${RED}✗ Frontend sync failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=== Sync completed successfully ===${NC}"
echo ""
echo "Files in /src/ and /frontend/ have been synchronized to:"
echo "  - printernizer/src/"
echo "  - printernizer/frontend/"
echo ""
echo "The Home Assistant add-on build will now use the latest code."
