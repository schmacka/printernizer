# Changelog

All notable changes to Printernizer are documented in this file.

For the complete, detailed changelog, see the [CHANGELOG.md](https://github.com/schmacka/printernizer/blob/master/CHANGELOG.md) file in the repository.

## Latest Releases

### Recent Updates

Check the [GitHub Releases](https://github.com/schmacka/printernizer/releases) page for the latest releases with:
- Release notes
- Download links
- Installation instructions
- Breaking changes

### Version Check

You can check your current version and available updates:

```bash
# Check current version
curl http://localhost:8000/api/v1/health | grep version

# Check for updates
curl http://localhost:8000/api/v1/update-check
```

## Versioning

Printernizer follows [Semantic Versioning](https://semver.org/):

- **Major version** (X.0.0) - Breaking changes
- **Minor version** (0.X.0) - New features, backwards compatible
- **Patch version** (0.0.X) - Bug fixes, backwards compatible

## Release Channels

### Stable (master branch)

- Production-ready releases
- Fully tested
- Recommended for all users
- Used for Home Assistant add-on

**Docker tag:** `latest`

### Development (development branch)

- Latest features
- Pre-release testing
- May have bugs
- For testing and early adopters

**Docker tag:** `development`

## Complete Changelog

For the full changelog with all versions and detailed changes, see:

**[CHANGELOG.md on GitHub →](https://github.com/schmacka/printernizer/blob/master/CHANGELOG.md)**

## Release Notes

### How to Read Release Notes

Each release includes:

- **Added** - New features
- **Changed** - Changes to existing functionality
- **Deprecated** - Features to be removed in future
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Security improvements

### Migration Guides

When upgrading between major versions, check the changelog for:
- Breaking changes
- Migration steps
- Configuration updates
- Database migrations

## Staying Updated

### Notification Methods

1. **Watch GitHub releases:**
   - Visit [Releases page](https://github.com/schmacka/printernizer/releases)
   - Click "Watch" → "Custom" → "Releases"

2. **Check in-app:**
   - Visit Settings → About
   - Check "Update Available" notification

3. **API endpoint:**
   ```bash
   curl http://localhost:8000/api/v1/update-check
   ```

### Update Frequency

- **Security fixes:** Released immediately
- **Bug fixes:** Released as needed (patch versions)
- **New features:** Released monthly (minor versions)
- **Major changes:** Released when ready (major versions)

## Upgrading

See the [Installation Guide](getting-started/installation.md#upgrading) for upgrade instructions for your deployment method.

## Contributing to Changelog

When contributing to Printernizer:

1. Add changes to `CHANGELOG.md` in your PR
2. Follow the existing format
3. Place changes in the "Unreleased" section
4. Categorize properly (Added, Changed, Fixed, etc.)

See [Contributing Guide](development/contributing.md) for details.

## Archive

Older versions and their changes can be found in the complete [CHANGELOG.md](https://github.com/schmacka/printernizer/blob/master/CHANGELOG.md).
