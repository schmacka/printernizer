# Printernizer Development Workflow

## Branching Strategy

**Two-Branch Model**:

### Branches

- **`development`** - Integration and testing branch
  - All feature branches merge here first
  - Used for Docker testing deployments
  - Pre-release versions (e.g., `2.7.0-dev`, `2.7.0-beta.1`)
  - Automated CI/CD builds Docker images tagged `development`
  - HA add-on sync runs but NO version bump

- **`master`** - Production branch
  - Only stable, tested code
  - Used for Home Assistant add-on production releases
  - Release versions only (e.g., `2.7.0`)
  - Tagged commits trigger production releases
  - HA add-on auto version bump on sync

### Workflow

```
Feature branch → development (PR + review) → Docker testing → master (PR + review) → Tag for release
```

### Development Process

1. **Create feature branch from `development`**:
   ```bash
   git checkout development
   git pull origin development
   git checkout -b feature/your-feature
   ```

2. **Develop and test locally**

3. **Create PR to `development`** (not master!)

4. **After merge**: CI/CD builds Docker image tagged `development`

5. **Test with Docker deployment**

6. **When ready for release**: Create PR from `development` to `master`

7. **After merge to master**: Follow release process (see RELEASE.md)

## Code Synchronization - CRITICAL

**Single Source of Truth**: Edit code ONLY in `/src/` and `/frontend/` directories.

### Automated Sync to printernizer-ha Repository

**Home Assistant Add-on**: Code is automatically synced to the separate [printernizer-ha](https://github.com/schmacka/printernizer-ha) repository.

1. **On Push to master/development**:
   - Edit files in `/src/` or `/frontend/`
   - Push to `master` or `development` branch
   - GitHub Actions workflow `sync-to-ha-repo.yml` automatically syncs to printernizer-ha repository
   - Version is automatically extracted from `src/main.py` and updated in printernizer-ha

2. **Manual Trigger** (if needed):
   - Visit: https://github.com/schmacka/printernizer/actions/workflows/sync-to-ha-repo.yml
   - Click "Run workflow" button
   - Select branch (master or development)

3. **Verification**:
   - Check workflow runs: https://github.com/schmacka/printernizer/actions/workflows/sync-to-ha-repo.yml
   - Verify printernizer-ha repository: https://github.com/schmacka/printernizer-ha

### Why This Architecture

- Home Assistant add-on is maintained in separate printernizer-ha repository
- Single source prevents code divergence and version drift
- Automated sync ensures consistency
- Developers work in one place, automation handles distribution

## Version Management

**Version is extracted from git tags** via `get_version()` utility in `src/utils/version.py`.

**Files to update when releasing:**
- `src/main.py` - Update fallback version in `get_version(fallback="X.Y.Z")`
- `CHANGELOG.md` - Add version section with release notes

**Note**: The HA add-on files (in [printernizer-ha](https://github.com/schmacka/printernizer-ha) repository) are updated automatically by GitHub Actions.

**Versioning Standard**: Semantic Versioning (MAJOR.MINOR.PATCH)
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

**Version Update Checklist**:
1. Update CHANGELOG.md with release notes
2. Update fallback version in src/main.py
3. Add entry to CHANGELOG.md
4. Commit with message: "chore: bump version to X.Y.Z"

## Development Guidelines

### Business Logic Requirements

- **Business Integration**: Flexible workflow and reporting capabilities
- **Material Tracking**: Comprehensive material usage monitoring
- **Localization**: Configurable timezone and locale settings
- **Export Compatibility**: Excel/CSV formats for standard accounting software

### File Organization

- Downloads organized by printer and date
- Secure file naming conventions
- Local file management with status tracking
- Flexible file organization and management

### API Routing Standards

All API endpoints follow REST conventions:
- `/api/v1/printers` - Printer management
- `/api/v1/jobs` - Job monitoring
- `/api/v1/files` - File management
- `/api/v1/analytics` - Business analytics
- `/api/v1/health` - System health

### Code Style

- Python: Follow PEP 8
- JavaScript: Modern ES6+
- SQL: Lowercase with underscores
- Documentation: Clear docstrings for all public functions
