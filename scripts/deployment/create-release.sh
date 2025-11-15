#!/bin/bash
# Printernizer Release Automation Script
# Creates git tags and GitHub Releases from CHANGELOG entries

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if we're in the right directory
if [ ! -f "CHANGELOG.md" ] || [ ! -f "VERSIONING.md" ]; then
    log_error "This script must be run from the printernizer root directory"
    exit 1
fi

# Check if we have git
if ! command -v git &> /dev/null; then
    log_error "git is not installed"
    exit 1
fi

# Parse command line arguments
VERSION=""
COMMIT=""
DRY_RUN=false
CREATE_GITHUB_RELEASE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -c|--commit)
            COMMIT="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --github)
            CREATE_GITHUB_RELEASE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 -v VERSION -c COMMIT [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --version VERSION    Version to release (e.g., 2.3.0)"
            echo "  -c, --commit COMMIT      Commit hash to tag"
            echo "  --dry-run                Show what would be done without doing it"
            echo "  --github                 Create GitHub Release (requires gh CLI)"
            echo "  -h, --help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 -v 2.3.0 -c 34734e1"
            echo "  $0 -v 2.4.0 -c HEAD --github"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$VERSION" ]; then
    log_error "Version is required. Use -v or --version"
    exit 1
fi

if [ -z "$COMMIT" ]; then
    log_error "Commit is required. Use -c or --commit"
    exit 1
fi

# Ensure version starts with 'v' for tag name
TAG_NAME="v${VERSION#v}"

# Verify commit exists
if ! git rev-parse --verify "$COMMIT" >/dev/null 2>&1; then
    log_error "Commit '$COMMIT' does not exist"
    exit 1
fi

COMMIT_HASH=$(git rev-parse "$COMMIT")
COMMIT_SHORT=$(git rev-parse --short "$COMMIT")

log_info "Creating release for version $TAG_NAME"
log_info "Commit: $COMMIT_SHORT ($COMMIT_HASH)"

# Extract release notes from CHANGELOG.md
log_info "Extracting release notes from CHANGELOG.md..."

# Try to find the version section in CHANGELOG
RELEASE_NOTES=$(awk "/^## \[$VERSION\]/,/^## \[/" CHANGELOG.md | sed '1d;$d' | sed '/^$/d')

if [ -z "$RELEASE_NOTES" ]; then
    log_warn "Could not find release notes for version $VERSION in CHANGELOG.md"
    RELEASE_NOTES="Release $TAG_NAME

See CHANGELOG.md for details."
fi

# Show what we're going to do
echo ""
log_info "=== Release Summary ==="
echo "Tag: $TAG_NAME"
echo "Commit: $COMMIT_SHORT"
echo "Release Notes:"
echo "---"
echo "$RELEASE_NOTES"
echo "---"
echo ""

if [ "$DRY_RUN" = true ]; then
    log_warn "DRY RUN - No changes will be made"
    echo ""
    echo "Would execute:"
    echo "  git tag -a $TAG_NAME $COMMIT_SHORT -m \"Release $TAG_NAME\""
    echo "  git push origin $TAG_NAME"
    if [ "$CREATE_GITHUB_RELEASE" = true ]; then
        echo "  gh release create $TAG_NAME --title \"Release $TAG_NAME\" --notes \"...\""
    fi
    exit 0
fi

# Confirm with user
read -p "Create this release? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warn "Release cancelled"
    exit 0
fi

# Create annotated git tag
log_info "Creating git tag $TAG_NAME..."
if git tag -a "$TAG_NAME" "$COMMIT_SHORT" -m "Release $TAG_NAME

$RELEASE_NOTES"; then
    log_info "✓ Tag created successfully"
else
    log_error "Failed to create tag (it may already exist)"
    exit 1
fi

# Push tag to remote
log_info "Pushing tag to origin..."
if git push origin "$TAG_NAME"; then
    log_info "✓ Tag pushed successfully"
else
    log_error "Failed to push tag to origin"
    log_warn "You may need to delete the local tag: git tag -d $TAG_NAME"
    exit 1
fi

# Create GitHub Release if requested
if [ "$CREATE_GITHUB_RELEASE" = true ]; then
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is not installed"
        log_info "Install it from: https://cli.github.com/"
        log_info "Or create the release manually at: https://github.com/schmacka/printernizer/releases/new?tag=$TAG_NAME"
        exit 1
    fi

    log_info "Creating GitHub Release..."
    if gh release create "$TAG_NAME" \
        --title "Release $TAG_NAME" \
        --notes "$RELEASE_NOTES"; then
        log_info "✓ GitHub Release created successfully"
        log_info "View at: https://github.com/schmacka/printernizer/releases/tag/$TAG_NAME"
    else
        log_error "Failed to create GitHub Release"
        log_info "You can create it manually at: https://github.com/schmacka/printernizer/releases/new?tag=$TAG_NAME"
        exit 1
    fi
fi

echo ""
log_info "=== Release Complete ==="
log_info "Tag: $TAG_NAME"
log_info "Pushed to: origin"
if [ "$CREATE_GITHUB_RELEASE" = false ]; then
    log_info "Next steps:"
    echo "  1. Create GitHub Release at: https://github.com/schmacka/printernizer/releases/new?tag=$TAG_NAME"
    echo "  2. Or run this script with --github flag to automate"
fi
echo ""
