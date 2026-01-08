# Branching Strategy

## Feature Branch Model

Printernizer uses a **simple feature branch workflow** where all changes merge directly into `master`.

### `master` Branch
- **Purpose**: Production-ready code and all development
- **Version format**: Release versions (e.g., `2.9.0`)
- **Docker images**: Tagged with version numbers and `latest`
- **HA sync**: Auto version bump on tagged commits
- **Use for**: All releases and as base for feature branches

## Development Workflow

```
Feature branch → master (PR) → Tag for release
     ↓              ↓              ↓
  PR + Review    Merge + Test   Production Release
```

## Creating Feature Branches

**Always create feature branches from `master`.**

```bash
# Correct workflow
git checkout master
git pull origin master
git checkout -b feature/my-new-feature

# Work on your feature...
git add .
git commit -m "feat: Add new feature"

# Push and create PR to master
git push origin feature/my-new-feature
```

## Branch Naming Conventions

Use descriptive prefixes:
- `feature/` - New features (e.g., `feature/timelapse-support`)
- `fix/` - Bug fixes (e.g., `fix/mqtt-reconnection`)
- `refactor/` - Code refactoring (e.g., `refactor/printer-service`)
- `docs/` - Documentation changes (e.g., `docs/api-endpoints`)
- `test/` - Test additions/fixes (e.g., `test/e2e-coverage`)

## Merging Strategy

1. **Create feature branch** from `master`
2. **Make changes** and commit with conventional commit messages
3. **Push branch** and create PR targeting `master`
4. **Review and merge** PR into `master`
5. **Tag release** when ready for production deployment

## Releasing

After merging to master, create a version tag:

```bash
git checkout master
git pull origin master
git tag -a vX.Y.Z -m "Release vX.Y.Z - Brief description"
git push origin master --tags
```

## References

- Release process: `RELEASE.md`
- Contributing guide: `CONTRIBUTING.md`
