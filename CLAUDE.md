# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference

For detailed information on specific topics, see the Claude Code Skills in `.claude/skills/`:

- **[Architecture & Context](.claude/skills/printernizer-architecture.md)** - Project overview, technology stack, API specifications
- **[Development Workflow](.claude/skills/printernizer-development-workflow.md)** - Code sync, version management, development guidelines
- **[Core Features](.claude/skills/printernizer-features.md)** - Job monitoring, file management, business features, metadata
- **[Deployment](.claude/skills/printernizer-deployment.md)** - Deployment methods, architecture, data persistence

## Project Overview

**Printernizer** is a professional 3D print management system designed for managing Bambu Lab A1 and Prusa Core One printers. It provides automated job tracking, file downloads, and business reporting capabilities for 3D printing operations.

**Primary Use Case**: Enterprise-grade 3D printer fleet management with automated job monitoring, file organization, and business analytics while maintaining simplicity for individual users.

**Language**: English (for logging, GUI, and reports)
**Timezone**: Configurable (defaults to system timezone)
**Business Focus**: Distinguish between business orders and private models

## Critical Development Rules

### ⚠️ Code Synchronization - READ THIS FIRST

**NEVER EDIT FILES IN `/printernizer/src/` OR `/printernizer/frontend/` DIRECTLY**

- **Single Source of Truth**: `/src/` and `/frontend/`
- **Auto-synced copy**: `/printernizer/src/` and `/printernizer/frontend/`
- Pre-commit hook automatically syncs changes
- See [Development Workflow](.claude/skills/printernizer-development-workflow.md) for details

### Version Management

**Version Files** (keep synchronized):
- `src/main.py` - `APP_VERSION = get_version(fallback="X.Y.Z")` (line 90)
- `printernizer/config.yaml` - `version: "X.Y.Z"` (line 2)
- `CHANGELOG.md` - Version history with release notes

**CRITICAL**: Always keep these three files synchronized!

See [Development Workflow](.claude/skills/printernizer-development-workflow.md) for versioning standards.

### Creating Releases

**When ready to release a new version:**

1. **Update CHANGELOG.md** - Add version section with release notes
2. **Update version files** - Sync `src/main.py` and `printernizer/config.yaml`
3. **Commit**: `git commit -m "chore: Bump version to X.Y.Z"`
4. **Tag**: `git tag -a vX.Y.Z -m "Release vX.Y.Z - Brief description"`
5. **Push**: `git push origin master && git push --tags`

**GitHub Actions will automatically:**
- Create GitHub release from tag
- Extract release notes from CHANGELOG.md
- Mark appropriate version as "latest"

See [RELEASE.md](RELEASE.md) for complete release workflow and troubleshooting.

## Quick Start

1. **Review Skills**: Read the skill files in `.claude/skills/` for detailed context
2. **Check Sync Status**: Ensure code sync is working before making changes
3. **Follow Patterns**: Use existing code patterns as templates
4. **Test Thoroughly**: Test changes in all deployment modes if applicable

## Key Documentation

- [`README.md`](README.md) - User-facing documentation
- [`CONTRIBUTING.md`](CONTRIBUTING.md) - Contribution guidelines
- [`docs/`](docs/) - Technical documentation
- [`CHANGELOG.md`](CHANGELOG.md) - Version history

## Architecture Quick Reference

**Core Services**:
- [`PrinterService`](src/services/printer_service.py) - Printer management
- [`JobService`](src/services/job_service.py) - Job tracking
- [`FileService`](src/services/file_service.py) - File management
- [`AnalyticsService`](src/services/analytics_service.py) - Business analytics

**Printer Integrations**:
- [`BambuLabPrinter`](src/printers/bambu_lab.py) - Bambu Lab MQTT
- [`PrusaPrinter`](src/printers/prusa.py) - Prusa HTTP API

**API Routers** (FastAPI):
- [`/api/v1/printers`](src/api/routers/printers.py)
- [`/api/v1/jobs`](src/api/routers/jobs.py)
- [`/api/v1/files`](src/api/routers/files.py)
- [`/api/v1/analytics`](src/api/routers/analytics.py)

## Common Tasks

### Adding a New Feature

1. Review relevant skill file for context
2. Identify affected services/routers
3. Update database schema if needed (with migration)
4. Implement backend logic
5. Add API endpoints
6. Update frontend
7. Add tests
8. Update documentation

### Fixing a Bug

1. Identify affected component(s)
2. Review related code in context
3. Write/update tests to reproduce bug
4. Fix issue
5. Verify tests pass
6. Update changelog if significant

### Adding Printer Support

1. Review [`BasePrinter`](src/printers/base.py) interface
2. Study existing implementations
3. Create new printer class
4. Implement required methods
5. Add configuration schema
6. Update documentation
7. Add integration tests

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_models.py

# Run with coverage
pytest --cov=src tests/
```

## API Routing Standards - CRITICAL

**Trailing Slash Policy**

This application has `redirect_slashes=False` configured in FastAPI to prevent conflicts with StaticFiles mounted at the root path.

**Mandatory Routing Pattern:**
- **NEVER use `"/"` as the endpoint path** in router decorators
- **ALWAYS use `""` (empty string)** for root resource endpoints
- This ensures API routes work WITHOUT trailing slashes (standard REST behavior)

**Correct Patterns:**

```python
# ✅ CORRECT
@router.get("")          # GET /api/v1/printers (no trailing slash)
@router.post("")         # POST /api/v1/printers (no trailing slash)
@router.get("/{id}")     # GET /api/v1/printers/abc123

# ❌ INCORRECT - Will cause 405 errors
@router.get("/")         # Creates route /api/v1/printers/ (WITH slash)
```

**Git History**: commits ddf53ea, 34680e6, branch fix/disable-redirect-slashes

## Need Help?

- **Documentation**: Start with skill files in `.claude/skills/`
- **Code Examples**: Review existing implementations
- **Issues**: Check GitHub issues for known problems
- **Discussions**: GitHub Discussions for questions

---

**Remember**: Always edit in `/src/` and `/frontend/`, never in `/printernizer/src/` or `/printernizer/frontend/`!