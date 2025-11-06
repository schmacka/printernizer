#!/bin/bash
#
# cleanup-ha-changelog.sh
# Cleans up generic auto-sync entries from HA add-on CHANGELOG.md
#
# This script:
# 1. Removes all generic "Auto-sync: Source code synchronized" entries
# 2. Consolidates them into a single note
# 3. Preserves all meaningful changelog entries
#

set -e

CHANGELOG_FILE="printernizer/CHANGELOG.md"

if [ ! -f "$CHANGELOG_FILE" ]; then
  echo "Error: $CHANGELOG_FILE not found"
  exit 1
fi

echo "Cleaning up HA add-on changelog..."

# Create a temporary file
TEMP_FILE=$(mktemp)

# Read the changelog and filter out generic auto-sync entries
# Keep only versions with meaningful content (more than just auto-sync message)
awk '
BEGIN {
  in_version = 0
  version_content = ""
  version_header = ""
  skip_version = 0
}

# Detect version header
/^## \[/ {
  # Process previous version if it had meaningful content
  if (in_version && !skip_version) {
    print version_header
    print version_content
  }

  # Start new version
  in_version = 1
  version_header = $0
  version_content = ""
  skip_version = 0
  next
}

# Check if this version only has generic auto-sync content
in_version {
  # Skip empty lines right after version header
  if ($0 == "" && version_content == "") {
    next
  }

  # Check if line is generic auto-sync
  if ($0 ~ /^- Auto-sync: Source code synchronized from main repository$/) {
    skip_version = 1
    next
  }

  # If we have other content, keep this version
  if ($0 != "") {
    skip_version = 0
  }

  version_content = version_content $0 "\n"
}

# Lines outside version blocks (header text)
!in_version {
  print
}

END {
  # Process last version
  if (in_version && !skip_version) {
    print version_header
    print version_content
  }
}
' "$CHANGELOG_FILE" > "$TEMP_FILE"

# Insert a consolidation note after the header
sed -i '1,/^# Changelog/ {
  /^# Changelog/a\
\
**Note**: Generic auto-sync entries have been consolidated. See git history for detailed changes between versions.
}' "$TEMP_FILE"

# Replace original file
mv "$TEMP_FILE" "$CHANGELOG_FILE"

echo "✓ Cleanup complete!"
echo ""
echo "Summary:"
echo "- Removed generic auto-sync entries"
echo "- Preserved all meaningful changelog entries"
echo "- Added consolidation note"
echo ""
echo "Please review the changes in: $CHANGELOG_FILE"
