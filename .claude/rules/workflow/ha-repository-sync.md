# Home Assistant Repository Sync

## Architecture Overview

The Home Assistant add-on is maintained in a **separate repository**: [printernizer-ha](https://github.com/schmacka/printernizer-ha)

Code is automatically synced from this main repository via GitHub Actions.

## How It Works

### Automatic Sync (sync-to-ha-repo.yml)

On push to `master` or `development`:
1. Workflow copies `src/`, `frontend/`, `migrations/` to printernizer-ha
2. **Development branch**: Syncs without version bump
3. **Master branch**: Syncs with automatic version bump

### Tag Sync (sync-release-tags.yml)

On version tags (`v*`):
1. Creates matching tags in printernizer-ha repository
2. Triggers HA add-on release workflow

## What This Means for Development

- **Edit files in this repository** (`/src/`, `/frontend/`, `/migrations/`)
- **Do NOT edit printernizer-ha directly** (changes will be overwritten)
- **Deployments happen automatically** via GitHub Actions

## Local vs Production

| Environment | Source |
|------------|--------|
| Local development | This repository |
| Docker testing | This repository (development tag) |
| Home Assistant | printernizer-ha repository |

## Triggering a Sync Manually

Syncs happen automatically on push. If needed, you can manually trigger via GitHub Actions workflow dispatch.

## References

- Sync workflow: `.github/workflows/sync-to-ha-repo.yml`
- Tag sync: `.github/workflows/sync-release-tags.yml`
- HA repo: https://github.com/schmacka/printernizer-ha
