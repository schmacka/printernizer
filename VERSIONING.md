# Printernizer Versioning System

## Overview

Printernizer uses **unified versioning** starting from version 2.0.0. All components (application, API, frontend, and Home Assistant add-on) share the same version number.

### Version Format

All versions follow **Semantic Versioning** (SemVer) in the `2.x.x` range:
- **2.x.x**: Unified version across all components
- Based on git tags (e.g., `v2.3.0`)
- Same version in `printernizer/config.yaml` (HA add-on)

## How It Works

1. **Git Tags as Source of Truth**: Version numbers are defined by git tags (e.g., `v2.3.0`)
2. **Automatic Extraction**: The `src/utils/version.py` utility extracts the version using `git describe --tags`
3. **Frontend Display**: The version is served via the `/health` API endpoint and displayed in the footer
4. **Consistent Everywhere**: Same version shown in app, API, and Home Assistant add-on

### Historical Note

Prior to v2.0.0, the project used dual versioning with separate 1.x.x (application) and 2.x.x (add-on) versions. This was consolidated to a single 2.x.x version scheme for clarity.

## Versioning Scheme

We follow **Semantic Versioning** (SemVer): `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes or major feature releases
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes and small improvements

### Examples
- `2.0.0` - Initial unified release
- `2.1.0` - Added new feature (Timelapse Management)
- `2.1.6` - Bug fix (Timelapse page refresh)
- `2.3.0` - Major improvements (Technical debt reduction)

## Creating a New Release

### Quick Reference: Where to Update Versions

**For Any Release (Unified Version - Everything Must Match):**

1. **Update CHANGELOG.md** with the new version `[2.X.X]` and changes

2. **Update all version references to match:**
   - `printernizer/config.yaml`: `version: "2.X.X"`
   - `src/utils/version.py`:
     - `get_version(fallback="2.X.X")`
     - `get_short_version(fallback="2.X.X")`

3. **Commit the version bump:**
   ```bash
   git add CHANGELOG.md printernizer/config.yaml src/utils/version.py
   git commit -m "chore: Version bump to 2.X.X"
   ```

4. **Create git tag:**
   ```bash
   git tag v2.X.X
   ```

5. **Push everything:**
   ```bash
   git push origin main  # or master
   git push origin v2.X.X
   ```

6. **Create GitHub Release** (see below)

**⚠️ Important:** All version numbers must match across config.yaml, version.py fallback, git tags, and CHANGELOG.md. This ensures consistency across all deployment methods.

### Creating GitHub Releases

GitHub Releases provide a user-friendly way to publish releases with release notes and allow the update-check endpoint to notify users of new versions.

**Option 1: Automated Script (Recommended)**
```bash
# Create a single release
./scripts/create-release.sh -v 2.4.0 -c HEAD --github

# Create releases for all missing tags
./scripts/create-missing-releases.sh
```

**Option 2: Using GitHub CLI**
```bash
# After creating and pushing a tag
gh release create v2.4.0 \
  --title "Release v2.4.0 - Feature Name" \
  --notes "Description from CHANGELOG.md"
```

**Option 3: Manual via GitHub UI**
1. Go to https://github.com/schmacka/printernizer/releases
2. Click "Draft a new release"
3. Select the tag from dropdown
4. Add title and description from CHANGELOG.md
5. Click "Publish release"

**Benefits of GitHub Releases:**
- Users can see release notes and download links
- The `/api/v1/update-check` endpoint works properly
- Notifications for watchers of the repository
- Professional appearance for the project

### Step 1: Make Your Changes
```bash
# Make code changes
git add .
git commit -m "fix: Your bug fix description"
```

### Step 2: Update Versions

**Creating Git Tags:**
```bash
# For a patch release (bug fixes)
git tag -a v2.3.1 -m "Release v2.3.1 - Bug fixes

- Fixed issue A
- Fixed issue B"

# For a minor release (new features)
git tag -a v2.4.0 -m "Release v2.4.0 - New features

- Added feature X
- Added feature Y"

# For a major release (breaking changes in the future)
git tag -a v3.0.0 -m "Release v3.0.0 - Major update

- Breaking: Changed API structure
- New: Complete UI overhaul"
```

### Step 3: That's It!
The version automatically updates. No code changes needed.

## Verification

### Check Current Version
```bash
# Via git
git describe --tags --always

# Via Python
python -c "from src.utils.version import get_version; print(get_version())"

# In the app
# The version appears in:
# - Frontend footer (visible to users)
# - /health API endpoint
# - Application logs
```

## Version Display Formats

### Clean Version (on tag)
```
git describe: v1.4.2
Displayed as: 1.4.2
```

### Development Version (commits after tag)
```
git describe: v1.4.2-3-g1234567
Displayed as: 1.4.2-3-g1234567
Meaning: 3 commits after v1.4.2 tag, commit hash g1234567
```

### Uncommitted Changes
```
git describe: v1.4.2-dirty
Displayed as: 1.4.2-dirty
Meaning: Working directory has uncommitted changes
```

## Fallback Behavior

If git is unavailable (e.g., deployed without .git directory), the system falls back to the hardcoded version in `src/utils/version.py`:

```python
APP_VERSION = get_version(fallback="1.4.2")
```

## Migration from Manual Versioning

### Old Way ❌
```python
# src/main.py
APP_VERSION = "1.4.2"  # Had to manually update this
```

Problems:
- Easy to forget updating
- Version in code != version in git
- Multiple places to update

### New Way ✅
```python
# src/main.py
from src.utils.version import get_version
APP_VERSION = get_version(fallback="1.4.2")
```

Benefits:
- Single source of truth (git tags)
- Automatic synchronization
- No manual updates needed

## Best Practices

### 1. Tag After Release Commits
```bash
# Make your changes
git commit -m "feat: Add new feature"

# Immediately tag
git tag -a v1.5.0 -m "Release v1.5.0"
```

### 2. Descriptive Tag Messages
```bash
# Good ✅
git tag -a v1.4.3 -m "Release v1.4.3 - Watch folder fixes

- Fixed modal not closing
- Fixed duplicate toasts
- Improved error handling"

# Bad ❌
git tag -a v1.4.3 -m "Version bump"
```

### 3. Push Tags to Remote
```bash
# Push specific tag
git push origin v1.4.3

# Push all tags
git push --tags
```

### 4. List All Tags
```bash
# List all tags
git tag -l

# List tags matching pattern
git tag -l "v1.4*"

# Show tag details
git show v1.4.2
```

## Troubleshooting

### Version Shows "error" in Footer
- Backend server couldn't reach `/health` endpoint
- Check if backend is running
- Check browser console for errors

### Version Shows Old Number
- Tag not created or pointing to wrong commit
- Check: `git describe --tags --always`
- Restart backend server to reload version

### Version Shows "dirty"
- Uncommitted changes in working directory
- Commit or stash changes
- Re-check: `git describe --tags --always`

## Implementation Details

### Source Files
- `src/utils/version.py` - Version extraction utility
- `src/main.py` - Imports and uses version
- `src/api/routers/health.py` - Serves version via API
- `frontend/js/utils.js` - Fetches and displays version

### How Frontend Gets Version
1. `loadAppVersion()` in `utils.js` runs on page load
2. Fetches `GET /api/v1/health`
3. Extracts `version` field from response
4. Updates `<span id="appVersion">` in footer

## Update Check Endpoint

The `/api/v1/update-check` endpoint checks for new releases on GitHub and notifies users when updates are available.

### How It Works

1. Fetches the latest release from GitHub API: `https://api.github.com/repos/schmacka/printernizer/releases/latest`
2. Compares the tag_name with the current application version
3. Returns update availability status

### Response Format

```json
{
  "current_version": "2.3.0",
  "latest_version": "2.4.0",
  "update_available": true,
  "release_url": "https://github.com/schmacka/printernizer/releases/tag/v2.4.0",
  "check_failed": false,
  "error_message": null
}
```

### Error Handling

- **404 (No Releases)**: Returns `check_failed: false` with message "No releases available yet"
- **Network Timeout**: Returns `check_failed: true` with timeout error
- **Other Errors**: Returns `check_failed: true` with error details

### Requirements

- GitHub Releases must be published (not just git tags)
- Releases should follow semantic versioning (v2.3.0 format)
- Release tag_name should match version format

### Testing

```bash
# Check current update status
curl http://localhost:8000/api/v1/update-check

# Or use frontend - version indicator shows update status
```

## Future Enhancements

Potential improvements:
- [ ] Pre-commit hook to remind about version tags
- [ ] Automated changelog generation from git tags
- [ ] CI/CD integration for automatic tagging and release creation
- [ ] Automated GitHub Release creation in CI/CD pipeline
