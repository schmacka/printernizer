# Branching Strategy

## Two-Branch Model

Printernizer uses a **two-branch workflow** to separate integration/testing from production releases.

### `development` Branch
- **Purpose**: Integration and testing
- **Version format**: Pre-release versions (e.g., `2.9.0-dev`)
- **Docker images**: Tagged as `development`
- **HA sync**: Runs but NO version bump
- **Use for**: Feature development, testing, bug fixes

### `master` Branch
- **Purpose**: Production-ready code
- **Version format**: Stable release versions (e.g., `2.9.0`)
- **Docker images**: Tagged with version numbers
- **HA sync**: Auto version bump on tagged commits
- **Use for**: Stable releases only

## Development Workflow

```
Feature branch → development (PR) → Docker test → master (PR) → Tag for release
```

## Creating Feature Branches

**Always create feature branches from `development`, NEVER from `master`.**

```bash
# Correct
git checkout development
git pull origin development
git checkout -b feature/my-new-feature

# Incorrect - Do not branch from master
git checkout master
git checkout -b feature/my-new-feature
```

## Merging Strategy

1. **Feature → Development**: Create PR from feature branch to `development`
2. **Test on Development**: Verify Docker deployments using `development` tag
3. **Development → Master**: Create PR from `development` to `master` (stable code only)
4. **Tag Release**: After merging to `master`, create a version tag

## References

- Release process: `RELEASE.md`
- Contributing guide: `CONTRIBUTING.md`
