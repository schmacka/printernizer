# Release Process

This document describes the release process for Printernizer, including versioning standards, branching strategy, tagging, and automated GitHub releases.

## Branching Strategy

Printernizer uses a **two-branch model** for development and releases:

### Branches

- **`development`** - Testing and integration branch
  - All feature branches merge here first
  - Used for Docker testing deployments
  - Pre-release versions (e.g., `2.7.0-dev`, `2.7.0-beta.1`)
  - Automated CI/CD builds Docker images tagged `development`
  - No production deployments

- **`master`** - Production-ready code
  - Only tested, stable code merges here
  - Used for Home Assistant add-on production releases
  - Release versions only (e.g., `2.7.0`)
  - Tagged commits trigger production releases
  - Automated HA add-on version bumping

### Workflow

```
Feature branch → development (test with Docker) → master (tag for release)
     ↓                ↓                              ↓
   PR + Review    Docker Testing              Production Release
```

### Version Conventions

- **Development branch**: Pre-release versions
  - Format: `X.Y.Z-dev` or `X.Y.Z-beta.N`
  - Example: `2.7.0-dev`, `2.7.0-beta.1`
  - Indicates work-in-progress

- **Master branch**: Release versions
  - Format: `X.Y.Z`
  - Example: `2.7.0`
  - Only applied when ready for production

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
3. **printernizer/config.yaml** - Home Assistant add-on `version: "X.Y.Z"`

## Release Workflow

### Prerequisites

Before creating a release, ensure:
- All features are merged to `development` branch
- Docker deployment testing completed on `development`
- All tests passing on `development`
- Ready to merge `development` → `master`

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
- [printernizer/config.yaml:2](printernizer/config.yaml#L2) - `version: "X.Y.Z"`

### 3. Merge development → master

Create a pull request from `development` to `master`:

```bash
# Switch to master and merge development
git checkout master
git pull origin master
git merge development --no-ff
```

Or create a PR on GitHub for review.

### 4. Commit Version Bump

```bash
git add CHANGELOG.md src/main.py printernizer/config.yaml
git commit -m "chore: Bump version to X.Y.Z"
```

The pre-commit hook will automatically sync files to the `printernizer/` directory.

### 5. Create Git Tag

**IMPORTANT**: Only tag commits on `master` branch.

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z - Brief description"
```

Example:
```bash
git tag -a v2.5.0 -m "Release v2.5.0 - Enhanced Library and Docker Support"
```

### 6. Push to GitHub

```bash
git push origin master
git push --tags
```

### 7. GitHub Release (Automated)

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
- [ ] Version updated in `printernizer/config.yaml`
- [ ] Version files committed
- [ ] Git tag created with descriptive message
- [ ] Tag pushed to GitHub
- [ ] GitHub release created (automatic or manual)
- [ ] Release notes reviewed for accuracy
- [ ] Home Assistant add-on tested with new version
- [ ] Docker build tested with new version

## Troubleshooting

### Version Mismatch

If versions are out of sync:

1. Check all three files: CHANGELOG.md, src/main.py, printernizer/config.yaml
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
# 1. Ensure all features tested on development branch
git checkout development
git pull origin development
# ... test with Docker ...

# 2. Merge development to master
git checkout master
git pull origin master
git merge development --no-ff

# 3. Update CHANGELOG.md
vim CHANGELOG.md

# 4. Update version files
vim src/main.py          # Change fallback="2.6.0"
vim printernizer/config.yaml  # Change version: "2.6.0"

# 5. Commit
git add CHANGELOG.md src/main.py printernizer/config.yaml
git commit -m "chore: Bump version to 2.6.0"

# 6. Tag
git tag -a v2.6.0 -m "Release v2.6.0 - New feature description"

# 7. Push
git push origin master && git push --tags

# 8. Sync master changes back to development
git checkout development
git merge master
git push origin development
```

### Example: Patch/Bugfix Release (2.5.0 → 2.5.1)

```bash
# For urgent hotfixes, you may work directly on master
# Otherwise, follow the same development → master flow

# 1. Merge development to master (or apply hotfix directly)
git checkout master
git merge development --no-ff  # Or skip if hotfix

# 2. Update version files
vim CHANGELOG.md
vim src/main.py
vim printernizer/config.yaml

# 3. Commit and tag
git add CHANGELOG.md src/main.py printernizer/config.yaml
git commit -m "chore: Bump version to 2.5.1"
git tag -a v2.5.1 -m "Release v2.5.1 - Critical bug fixes"

# 4. Push
git push origin master && git push --tags

# 5. Sync back to development
git checkout development
git merge master
git push origin development
```

## Best Practices

1. **Always test on development first** - Merge features to `development`, test with Docker, then merge to `master`
2. **Sync development ↔ master** - Keep branches in sync by merging master back to development after releases
3. **Only tag on master** - Production releases are only tagged on the `master` branch
4. **Tag immediately after version bump commit** - Don't let commits accumulate after updating version
5. **Use descriptive tag messages** - Include brief summary of main changes
6. **Keep CHANGELOG.md up to date** - Update it with each significant change
7. **Test before releasing** - Run tests and verify functionality
8. **Follow semantic versioning** - Be consistent with version number meanings
9. **Document breaking changes** - Clearly mark any breaking changes in CHANGELOG

## Related Documentation

- [CHANGELOG.md](CHANGELOG.md) - Complete version history
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [Development Workflow](.claude/skills/printernizer-development-workflow.md) - Code sync and version management

---

**Last Updated**: 2025-11-11
**Current Version**: 2.5.0
