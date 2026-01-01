# Version Management & Releases

## Version Extraction

Version is extracted from **git tags** via the `get_version()` utility.

```python
# src/main.py
APP_VERSION = get_version(fallback="2.9.1")
```

If no git tag is available, the fallback version is used.

## Version Files

**Primary version source**: Git tags (format: `vX.Y.Z`)

**Fallback locations** (update when releasing):
1. `src/main.py` line ~94 - `get_version(fallback="X.Y.Z")`
2. `CHANGELOG.md` - Version history with release notes

**Note**: The HA add-on version in `printernizer-ha/config.yaml` is updated automatically by GitHub Actions.

## Release Workflow

1. **Update CHANGELOG.md** with release notes
2. **Update fallback version** in `src/main.py`
3. **Commit**: `git commit -m "chore: Bump version to X.Y.Z"`
4. **Tag**: `git tag -a vX.Y.Z -m "Release vX.Y.Z - Brief description"`
5. **Push**: `git push origin master && git push --tags`

## What Happens Automatically

GitHub Actions will:
- Create GitHub release from tag
- Extract release notes from CHANGELOG.md
- Sync code to printernizer-ha repository
- Create matching tag in printernizer-ha
- Bump version in HA add-on config

## Version Format

- **Stable releases**: `X.Y.Z` (e.g., `2.9.1`)
- **Development**: `X.Y.Z-dev` (e.g., `2.10.0-dev`)
- **Git tags**: `vX.Y.Z` (e.g., `v2.9.1`)

## References

- Release process: `RELEASE.md`
- Version utility: `src/utils/version.py`
- CI/CD workflow: `.github/workflows/ci-cd.yml`
