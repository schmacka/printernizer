# Release Process

This document describes the release process for Printernizer, including versioning standards, branching strategy, tagging, and automated GitHub releases.

## Branching Strategy

Printernizer uses a **feature branch model** where all changes merge directly into `master`.

### Branch

- **`master`** - Main branch for all development and releases
  - All feature branches merge here directly
  - Used for Home Assistant add-on releases
  - Release versions (e.g., `2.7.0`)
  - Tagged commits trigger production releases
  - Automated HA add-on version bumping

### Workflow

```
Feature branch → master (PR) → Tag for release
     ↓              ↓              ↓
  PR + Review    Merge + Test   Production Release
```

## Version Numbering

Printernizer follows [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., 2.5.0)
- **MAJOR**: Breaking changes or major feature overhauls
- **MINOR**: New features, backward-compatible
- **PATCH**: Bug fixes and minor improvements

## Version Synchronization

All version numbers must be synchronized across these files:

1. **CHANGELOG.md** - Release notes and version history
2. **src/main.py** - `APP_VERSION = get_version(fallback="X.Y.Z")`

## Release Workflow

### Prerequisites

Before creating a release, ensure:
- All features are merged to `master` branch
- All tests passing
- Changes documented in CHANGELOG.md

### 1. Update CHANGELOG.md

Add a new section under `## [Unreleased]`:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features...

### Changed
- Changes to existing functionality...

### Fixed
- Bug fixes...

### Removed
- Removed features...
```

### 2. Update Version Files

Update the version number in:

- [src/main.py:90](src/main.py#L90) - `APP_VERSION = get_version(fallback="X.Y.Z")`

### 3. Commit Version Bump

```bash
git add CHANGELOG.md src/main.py
git commit -m "chore: Bump version to X.Y.Z"
```

### 4. Create Git Tag

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z - Brief description"
```

Example:
```bash
git tag -a v2.5.0 -m "Release v2.5.0 - Enhanced Library and Docker Support"
```

### 5. Push to GitHub

```bash
git push origin master --tags
```

### 6. GitHub Release (Automated)

When you push a tag matching `v*.*.*`, the GitHub Actions workflow (`.github/workflows/release.yml`) automatically:

1. Extracts the version number from the tag
2. Extracts release notes from CHANGELOG.md
3. Creates a GitHub release with the notes
4. Marks it as the latest release

**Manual Alternative:**

If you prefer to create releases manually:

```bash
gh release create vX.Y.Z \
  --title "vX.Y.Z - Brief Title" \
  --notes-file release_notes.md
```

## Automated Releases

The project uses GitHub Actions to automate release creation:

- **Workflow File**: `.github/workflows/release.yml`
- **Trigger**: Push of tags matching `v*.*.*`
- **Actions**:
  - Checkout code
  - Extract version from tag
  - Extract release notes from CHANGELOG.md
  - Create GitHub release

## Version Detection

The application automatically detects its version using git tags:

1. **With git available**: Uses `git describe --tags --always --dirty`
   - Returns: `v2.5.0` (on tag) or `v2.5.0-3-g1234567` (commits after tag)
2. **Without git**: Falls back to hardcoded version in `src/main.py`

This is handled by [src/utils/version.py:10](src/utils/version.py#L10).

## Update Check Endpoint

The application includes an update check endpoint at `/api/v1/update-check`:

- Fetches latest GitHub release
- Compares with current version
- Returns update availability status

See [src/api/routers/health.py:224](src/api/routers/health.py#L224) for implementation.

## Release Checklist

Use this checklist when creating a release:

- [ ] All changes documented in CHANGELOG.md
- [ ] Version updated in `src/main.py`
- [ ] Version files committed
- [ ] Git tag created with descriptive message
- [ ] Tag pushed to GitHub
- [ ] GitHub release created (automatic or manual)
- [ ] Release notes reviewed for accuracy

## Troubleshooting

### Version Mismatch

If versions are out of sync:

1. Check both files: CHANGELOG.md, src/main.py
2. Update to match the latest version
3. Commit with message: `fix: Synchronize version numbers to X.Y.Z`

### Failed GitHub Release

If the GitHub Action fails:

1. Check workflow logs: https://github.com/schmacka/printernizer/actions
2. Verify CHANGELOG.md has an entry for the version
3. Ensure tag format is `v*.*.*` (with 'v' prefix)
4. Create release manually using `gh release create`

### Missing Tag

If you forgot to create a tag:

```bash
# Find the commit hash for the version bump
git log --oneline | head -20

# Create tag on that commit
git tag -a vX.Y.Z <commit-hash> -m "Release vX.Y.Z"

# Push the tag
git push --tags
```

## Examples

### Example: Minor Feature Release (2.5.0 → 2.6.0)

```bash
# 1. Ensure you're on master with latest changes
git checkout master
git pull origin master

# 2. Update CHANGELOG.md
vim CHANGELOG.md

# 3. Update version file
vim src/main.py          # Change fallback="2.6.0"

# 4. Commit
git add CHANGELOG.md src/main.py
git commit -m "chore: Bump version to 2.6.0"

# 5. Tag
git tag -a v2.6.0 -m "Release v2.6.0 - New feature description"

# 6. Push
git push origin master --tags
```

### Example: Patch/Bugfix Release (2.5.0 → 2.5.1)

```bash
# 1. Ensure you're on master
git checkout master
git pull origin master

# 2. Update version files
vim CHANGELOG.md
vim src/main.py

# 3. Commit and tag
git add CHANGELOG.md src/main.py
git commit -m "chore: Bump version to 2.5.1"
git tag -a v2.5.1 -m "Release v2.5.1 - Critical bug fixes"

# 4. Push
git push origin master --tags
```

## Best Practices

1. **Test before releasing** - Run tests and verify functionality before tagging
2. **Tag immediately after version bump commit** - Don't let commits accumulate after updating version
3. **Use descriptive tag messages** - Include brief summary of main changes
4. **Keep CHANGELOG.md up to date** - Update it with each significant change
5. **Follow semantic versioning** - Be consistent with version number meanings
6. **Document breaking changes** - Clearly mark any breaking changes in CHANGELOG

## Related Documentation

- [CHANGELOG.md](CHANGELOG.md) - Complete version history
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [Development Workflow](.claude/skills/printernizer-development-workflow.md) - Code sync and version management

---

**Last Updated**: 2026-01-08
**Current Version**: 2.24.3
