# GitHub Releases Setup Guide

## Overview

This guide explains the complete git tags + GitHub Releases implementation for Printernizer's version management and update notification system.

## What Was Implemented

### 1. Fixed Update-Check Endpoint

**File**: `src/api/routers/health.py`

The `/api/v1/update-check` endpoint now properly handles the case when no GitHub Releases exist:

**Before**:
```json
{
  "check_failed": true,
  "error_message": "GitHub API returned status 404"
}
```

**After**:
```json
{
  "check_failed": false,
  "error_message": "No releases available yet"
}
```

This treats "no releases yet" as a valid state rather than an error.

### 2. Release Automation Scripts

Two new scripts in `scripts/` directory:

#### `create-release.sh` - Create Individual Releases

Interactive script for creating new releases:

```bash
# Create a single release
./scripts/create-release.sh -v 2.4.0 -c HEAD --github

# Dry run to see what would happen
./scripts/create-release.sh -v 2.4.0 -c HEAD --dry-run

# Get help
./scripts/create-release.sh --help
```

Features:
- Extracts release notes from CHANGELOG.md automatically
- Creates annotated git tags
- Pushes tags to GitHub
- Creates GitHub Release via gh CLI
- Dry-run mode for testing
- Interactive confirmation

#### `create-missing-releases.sh` - Batch Create Releases

Creates GitHub Releases for all existing tags that don't have releases:

```bash
./scripts/create-missing-releases.sh
```

Features:
- Checks for existing releases to avoid duplicates
- Processes multiple tags in one run
- Rate-limiting friendly
- Summary report

### 3. Enhanced Documentation

**File**: `VERSIONING.md`

Added comprehensive sections:
- "Creating GitHub Releases" with 3 options (script, gh CLI, manual)
- "Update Check Endpoint" explaining how it works
- Error handling documentation
- Testing instructions

## Current State

### Version Consolidation

As of November 2025, Printernizer uses **unified 2.x.x versioning** across all components:
- Application, API, Frontend: Same version from git tags
- Home Assistant Add-on: Same version in `printernizer/config.yaml`
- All use the same version number (e.g., v2.3.0)

### Existing Git Tags

The repository has the following tags:
- `v1.0.0` through `v1.5.9` (legacy 1.x.x versions - pre-consolidation)
- `v2.1.0`, `v2.1.6`, `v2.2.0`, `v2.3.0` (unified 2.x.x versions)

**Note**: Historical 1.x.x tags remain for backwards compatibility but new releases use only 2.x.x versions.

### GitHub Releases

**Currently**: No GitHub Releases exist (all return 404)

**After running scripts**: All tags will have corresponding releases with proper release notes

The update-check endpoint will then work properly to notify users of new versions.

## How to Enable the Update-Check Feature

### Prerequisites

1. **Install GitHub CLI** (if not already installed):
   ```bash
   # macOS
   brew install gh

   # Linux
   sudo apt install gh

   # Windows
   winget install --id GitHub.cli
   ```

2. **Authenticate GitHub CLI**:
   ```bash
   gh auth login
   ```

### Steps to Create Releases

#### Option 1: Automated (Recommended)

From the `main` or `master` branch:

```bash
# 1. Ensure you're on main branch
git checkout main
git pull origin main

# 2. Fetch all tags
git fetch --tags

# 3. Create all missing releases
./scripts/create-missing-releases.sh
```

This will create GitHub Releases for:
- v1.5.9 - Printer Autodiscovery Fixes
- v2.1.0 - Timelapse Management System
- v2.1.6 - Timelapse Page Refresh Fix
- v2.2.0 - Timelapse Configuration UI
- v2.3.0 - Technical Debt Reduction

#### Option 2: Manual via GitHub UI

1. Go to https://github.com/schmacka/printernizer/releases
2. Click "Draft a new release"
3. In "Choose a tag" dropdown, select one of the existing tags (e.g., `v2.3.0`)
4. Add title: "Release v2.3.0 - Technical Debt Reduction"
5. Copy release notes from `CHANGELOG.md`
6. Click "Publish release"
7. Repeat for other tags

#### Option 3: Using gh CLI Directly

```bash
gh release create v2.3.0 \
  --title "Release v2.3.0 - Technical Debt Reduction" \
  --notes "Major code quality improvements including comprehensive documentation, standardized error handling, and settings validation."
```

## Verification

After creating releases, verify the update-check endpoint works:

```bash
# Test the endpoint
curl http://localhost:8000/api/v1/update-check

# Expected response (when on older version):
{
  "current_version": "2.2.0",
  "latest_version": "2.3.0",
  "update_available": true,
  "release_url": "https://github.com/schmacka/printernizer/releases/tag/v2.3.0",
  "check_failed": false
}
```

## Future Release Workflow

For future releases:

1. **Make your changes** and commit them
2. **Update CHANGELOG.md** with the new version
3. **Create and push release** using the script:
   ```bash
   ./scripts/create-release.sh -v 2.4.0 -c HEAD --github
   ```

That's it! The script handles:
- Extracting release notes from CHANGELOG.md
- Creating annotated git tag
- Pushing tag to GitHub
- Creating GitHub Release

## Troubleshooting

### "403 Error" when pushing tags

You might be on a feature branch with restrictions. Switch to `main`:
```bash
git checkout main
git pull origin main
```

### "gh: command not found"

Install GitHub CLI:
- macOS: `brew install gh`
- Linux: `sudo apt install gh`
- Windows: `winget install --id GitHub.cli`

### "Tag already exists"

If a tag already exists remotely:
```bash
# Delete local tag
git tag -d v2.3.0

# Fetch from remote
git fetch --tags

# Use the remote version
```

### GitHub Release fails to create

Check authentication:
```bash
gh auth status
gh auth login  # if not authenticated
```

## Benefits of This Setup

1. **Update Notifications**: Users see when new versions are available
2. **Professional Releases**: Proper release notes and download pages
3. **Automated Workflow**: Scripts reduce manual effort
4. **Consistent Versioning**: Integrates with existing tag-based system
5. **User-Friendly**: Release notes from CHANGELOG.md automatically included

## Related Documentation

- `VERSIONING.md` - Complete versioning system documentation
- `CHANGELOG.md` - Version history and release notes
- `scripts/create-release.sh` - Release automation script
- `scripts/create-missing-releases.sh` - Batch release creation

## Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Review logs from the scripts
3. Verify GitHub CLI authentication: `gh auth status`
4. Check GitHub repository permissions

---

**Created**: 2025-11-08
**Last Updated**: 2025-11-08
**Status**: Ready to use - waiting for releases to be created
