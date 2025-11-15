#!/bin/bash
# Create GitHub Releases for existing tags that don't have releases yet
# This script should be run from the main/master branch

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Check for gh CLI
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI (gh) is required but not installed."
    echo "Install it from: https://cli.github.com/"
    echo ""
    echo "Alternatively, create releases manually:"
    echo "1. Go to https://github.com/schmacka/printernizer/releases"
    echo "2. Click 'Draft a new release'"
    echo "3. Select the tag from the dropdown"
    echo "4. Add release notes from CHANGELOG.md"
    echo "5. Publish the release"
    exit 1
fi

# Releases to create (tag_name:title:description)
# These are based on CHANGELOG.md entries
declare -A RELEASES=(
    ["v1.5.9"]="Printer Autodiscovery Fixes|Fixed 503 error on printer discovery endpoint. Added netifaces-plus package and fixed ServiceListener import issues."
    ["v2.1.0"]="Timelapse Management System|Complete automated timelapse video creation and management with FlickerFree integration, gallery UI, and smart job linking."
    ["v2.1.6"]="Timelapse Page Refresh Fix|Fixed timelapse page refresh functionality by adding missing case in refreshCurrentPage() function."
    ["v2.2.0"]="Timelapse Configuration UI|Expose timelapse settings in Home Assistant addon configuration with automatic directory creation."
    ["v2.3.0"]="Technical Debt Reduction|Major code quality improvements including comprehensive documentation, standardized error handling, and settings validation."
)

log_info "Checking for existing releases..."
EXISTING_RELEASES=$(gh release list --limit 100 --json tagName --jq '.[].tagName')

log_info "Creating GitHub Releases for missing tags..."
echo ""

CREATED_COUNT=0
SKIPPED_COUNT=0

for TAG in "${!RELEASES[@]}"; do
    IFS='|' read -r TITLE DESCRIPTION <<< "${RELEASES[$TAG]}"

    # Check if release already exists
    if echo "$EXISTING_RELEASES" | grep -q "^$TAG$"; then
        log_warn "Release $TAG already exists, skipping"
        ((SKIPPED_COUNT++))
        continue
    fi

    # Check if tag exists
    if ! git rev-parse "$TAG" >/dev/null 2>&1; then
        log_warn "Tag $TAG does not exist locally, skipping"
        ((SKIPPED_COUNT++))
        continue
    fi

    log_info "Creating release for $TAG..."

    if gh release create "$TAG" \
        --title "$TITLE" \
        --notes "$DESCRIPTION" \
        --verify-tag 2>&1; then
        log_info "✓ Created release $TAG"
        ((CREATED_COUNT++))
    else
        log_warn "Failed to create release $TAG"
        ((SKIPPED_COUNT++))
    fi

    # Small delay to avoid rate limiting
    sleep 1
done

echo ""
log_info "=== Summary ==="
echo "Created: $CREATED_COUNT releases"
echo "Skipped: $SKIPPED_COUNT releases"
echo ""
log_info "View all releases at: https://github.com/schmacka/printernizer/releases"
