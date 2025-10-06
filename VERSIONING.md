# Printernizer Versioning System

## Overview

Printernizer uses **automatic versioning** based on git tags. The version is dynamically extracted from git tags at application startup, eliminating the need for manual version updates in code.

## How It Works

1. **Git Tags as Source of Truth**: Version numbers are defined by git tags (e.g., `v1.4.2`)
2. **Automatic Extraction**: The `src/utils/version.py` utility extracts the version using `git describe --tags`
3. **Frontend Display**: The version is served via the `/health` API endpoint and displayed in the footer

## Versioning Scheme

We follow **Semantic Versioning** (SemVer): `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes or major feature releases
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes and small improvements

### Examples
- `1.0.0` - Initial release
- `1.1.0` - Added new feature
- `1.1.1` - Bug fix
- `2.0.0` - Major refactoring with breaking changes

## Creating a New Release

### Step 1: Make Your Changes
```bash
# Make code changes
git add .
git commit -m "fix: Your bug fix description"
```

### Step 2: Create a Git Tag
```bash
# For a patch release (bug fixes)
git tag -a v1.4.3 -m "Release v1.4.3 - Bug fixes

- Fixed issue A
- Fixed issue B"

# For a minor release (new features)
git tag -a v1.5.0 -m "Release v1.5.0 - New features

- Added feature X
- Added feature Y"

# For a major release (breaking changes)
git tag -a v2.0.0 -m "Release v2.0.0 - Major update

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

## Future Enhancements

Potential improvements:
- [ ] Pre-commit hook to remind about version tags
- [ ] Automated changelog generation from git tags
- [ ] Version comparison in frontend (notify about updates)
- [ ] CI/CD integration for automatic tagging
