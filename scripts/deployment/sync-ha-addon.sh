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

# Sync source code using cp (more reliable on Windows than rsync)
echo -e "${YELLOW}Syncing src/ → printernizer/src/${NC}"

# Remove old destination (to mimic rsync --delete behavior)
rm -rf "$PROJECT_ROOT/printernizer/src"
mkdir -p "$PROJECT_ROOT/printernizer/src"

# Copy files excluding unwanted patterns
find "$PROJECT_ROOT/src" -type f \
    ! -path "*/__pycache__/*" \
    ! -name "*.pyc" \
    ! -name "*.pyo" \
    ! -path "*/.pytest_cache/*" \
    ! -path "*.egg-info/*" \
    -exec bash -c 'dest="$1"; src="$2"; rel="${src#$3/src/}"; mkdir -p "$(dirname "$dest/printernizer/src/$rel")"; cp "$src" "$dest/printernizer/src/$rel"' _ "$PROJECT_ROOT" {} "$PROJECT_ROOT" \;

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Source code synced successfully${NC}"
else
    echo -e "${RED}✗ Source code sync failed${NC}"
    exit 1
fi

echo ""

# Sync frontend
echo -e "${YELLOW}Syncing frontend/ → printernizer/frontend/${NC}"

# Remove old destination
rm -rf "$PROJECT_ROOT/printernizer/frontend"
mkdir -p "$PROJECT_ROOT/printernizer/frontend"

# Copy files excluding unwanted patterns
find "$PROJECT_ROOT/frontend" -type f \
    ! -path "*/node_modules/*" \
    ! -path "*/.vite/*" \
    ! -path "*/dist/*" \
    -exec bash -c 'dest="$1"; src="$2"; rel="${src#$3/frontend/}"; mkdir -p "$(dirname "$dest/printernizer/frontend/$rel")"; cp "$src" "$dest/printernizer/frontend/$rel"' _ "$PROJECT_ROOT" {} "$PROJECT_ROOT" \;

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
