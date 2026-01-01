---
name: Release Checklist
about: Checklist for creating a new release
title: 'Release vX.Y.Z'
labels: release
assignees: ''

---

## Release Information

**Version**: vX.Y.Z
**Release Type**: [ ] Major [ ] Minor [ ] Patch
**Target Date**: YYYY-MM-DD

## Pre-Release Checklist

### Documentation
- [ ] Update `CHANGELOG.md` with version section and release notes
- [ ] Document all significant changes since last release
- [ ] Review and update README.md if needed
- [ ] Update any affected documentation in `docs/`

### Version Synchronization
- [ ] Update `src/main.py` - `APP_VERSION = get_version(fallback="X.Y.Z")`
- [ ] Verify CHANGELOG.md has entry for this version
- [ ] Version will automatically sync to printernizer-ha repository via GitHub Actions

### Testing
- [ ] Run test suite: `pytest`
- [ ] Test in standalone mode
- [ ] Test in Docker mode (if Docker changes)
- [ ] Test Home Assistant add-on (if HA changes)
- [ ] Verify all new features work as expected
- [ ] Check for any breaking changes

### Code Quality
- [ ] All tests passing
- [ ] No linting errors
- [ ] Code review completed (if applicable)
- [ ] Pre-commit hooks passing

## Release Process

### Create Release
```bash
# 1. Commit version bump
git add CHANGELOG.md src/main.py
git commit -m "chore: Bump version to X.Y.Z"

# 2. Create git tag
git tag -a vX.Y.Z -m "Release vX.Y.Z - Brief description"

# 3. Push to GitHub (this triggers sync to printernizer-ha)
git push origin master
git push --tags
```

### Post-Release Checklist
- [ ] Verify tag pushed to GitHub
- [ ] Verify GitHub Actions workflow completed successfully
- [ ] Verify GitHub release created automatically
- [ ] Verify release marked as "latest" (use `gh release edit vX.Y.Z --latest`)
- [ ] Verify release notes look correct
- [ ] Test `/api/v1/update-check` endpoint returns correct version
- [ ] Announce release (if applicable)

## Post-Release Tasks

### Documentation
- [ ] Update any external documentation
- [ ] Update README badges if needed
- [ ] Close related issues/PRs

### Communication
- [ ] Post release announcement (if applicable)
- [ ] Update project status
- [ ] Notify stakeholders (if applicable)

## Notes

<!-- Add any additional notes or context about this release -->

## Rollback Plan

If issues are discovered:
1. Document the issue
2. Create hotfix branch if needed
3. Release patch version
4. Update this issue with resolution

---

**See [RELEASE.md](../RELEASE.md) for detailed release procedures.**
