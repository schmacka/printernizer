# Printernizer Development Workflow

## Code Synchronization - CRITICAL

**Single Source of Truth**: Edit code ONLY in `/src/` and `/frontend/` directories.

### Automated Sync Process

1. **During Development**:
   - Edit files in `/src/` or `/frontend/` 
   - NEVER touch `/printernizer/src/` or `/printernizer/frontend/`
   - Pre-commit hook auto-syncs on commit
   - Synced files automatically staged and included in commit

2. **Manual Sync** (if needed):
   ```bash
   # Linux/Mac
   ./scripts/sync-ha-addon.sh

   # Windows
   scripts\sync-ha-addon.bat
   ```

3. **CI/CD Validation**:
   - GitHub Actions runs sync on push to master
   - Auto-bumps HA add-on version
   - Commits and pushes changes if needed

### Why This Architecture

- Home Assistant build system requires files in `printernizer/` directory
- Single source prevents code divergence and version drift
- Triple safety net (hook + CI + manual) ensures consistency
- Developers work in one place, automation handles the rest

## Version Management

**Version Files** (keep synchronized):
- `src/api/routers/health.py` - API version
- `printernizer/config.yaml` - Home Assistant add-on version
- `printernizer/CHANGELOG.md` - Version history

**Versioning Standard**: Semantic Versioning (MAJOR.MINOR.PATCH)
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

**Version Update Checklist**:
1. Update version in health.py
2. Update version in config.yaml
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
