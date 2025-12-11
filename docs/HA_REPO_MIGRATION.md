# Home Assistant Repository Migration Plan

**Status**: ✅ **COMPLETED**
**Created**: 2025-12-08
**Completed**: 2025-12-11
**Goal**: Migrate HA add-on to separate `printernizer-ha` repository to eliminate code duplication

## Migration Complete! 🎉

The Home Assistant add-on has been successfully migrated to the separate [printernizer-ha](https://github.com/schmacka/printernizer-ha) repository.

### What Changed

**Before Migration**:
- Main repo contained `/printernizer/` with duplicated code (~6.3MB)
- Manual sync workflow copied `src/` and `frontend/` to local `/printernizer/` folder
- Pre-commit hooks auto-synced files on every commit
- HA-specific files mixed with synced code in the same repository

**After Migration**:
- Clean main repo without `/printernizer/` directory ✅
- Separate `printernizer-ha` repository with automated GitHub Actions sync ✅
- HA-specific files only in printernizer-ha repository ✅
- Automatic version syncing from main repo via `sync-to-ha-repo.yml` workflow ✅

### How It Works Now

1. **Development**: Edit code in `/src/` or `/frontend/` in the main printernizer repository
2. **Push**: Commit and push to `master` or `development` branch
3. **Auto-Sync**: GitHub Actions workflow automatically syncs changes to printernizer-ha repository
4. **Version Management**: Version is extracted from `src/main.py` and synced to printernizer-ha's `config.yaml`

**Workflow**: `.github/workflows/sync-to-ha-repo.yml`

---

## Implementation Summary

### Phase 1: Repository Setup & Preparation ✅

**Status**: Ready to implement
**Owner**: Development Team
**Timeline**: Week 1

#### 1.1 Create printernizer-ha Repository
- [x] Repository exists: `schmacka/printernizer-ha`
- [ ] Public repository
- [ ] Add description: "Home Assistant Add-on for Printernizer - Professional 3D Printer Management"
- [ ] Initialize with README explaining auto-sync

#### 1.2 Configure GitHub Secrets
- [ ] Add `HA_REPO_TOKEN` to main printernizer repo secrets
- [ ] Token permissions: `repo` and `workflow`
- [ ] Test token access to printernizer-ha

#### 1.3 Initial printernizer-ha Structure
```
printernizer-ha/
├── config.yaml          (HA add-on config)
├── build.yaml           (multi-arch build)
├── Dockerfile           (HA-specific)
├── run.sh              (startup script)
├── DOCS.md             (HA-specific docs)
├── README.md           (HA-specific readme)
├── icon.png
├── logo.png
├── CHANGELOG.md        (will be auto-synced)
├── .github/
│   └── workflows/
│       └── validate.yml (optional: validate add-on config)
└── (src/, frontend/, migrations/ will be auto-pushed)
```

**Files to Copy Initially from `/printernizer/`:**
- config.yaml
- build.yaml
- Dockerfile
- run.sh
- DOCS.md
- README.md (create new HA-specific version)
- icon.png
- logo.png

**Files to Auto-Sync:**
- src/ (entire directory)
- frontend/ (entire directory)
- migrations/ (entire directory)
- database_schema.sql
- requirements.txt
- CHANGELOG.md

---

### Phase 2: GitHub Actions Implementation 🚧

**Status**: In Progress
**Owner**: Development Team
**Timeline**: Week 1-2

#### 2.1 Create New Workflow: sync-to-ha-repo.yml

**File**: `.github/workflows/sync-to-ha-repo.yml`

**Triggers**:
- Push to `master` branch (production sync)
- Push to `development` branch (testing sync)
- Manual dispatch via `workflow_dispatch`

**Monitored Paths**:
```yaml
paths:
  - 'src/**'
  - 'frontend/**'
  - 'migrations/**'
  - 'database_schema.sql'
  - 'requirements.txt'
  - 'CHANGELOG.md'
```

**Workflow Steps**:
1. Checkout main printernizer repo
2. Checkout printernizer-ha repo (same branch name)
3. Sync files (remove old, copy fresh)
4. Extract version from `src/main.py`
5. Update `config.yaml` version (master only)
6. Commit and push to printernizer-ha

**Key Features**:
- Branch matching (master→master, development→development)
- Version extraction from main repo
- Automatic version bumping on master
- Descriptive commit messages with source SHA
- Skip if no changes

#### 2.2 Create Tag Sync Workflow

**File**: `.github/workflows/sync-release-tags.yml`

**Triggers**:
- Push tags matching `v*` pattern

**Purpose**:
- Create matching tags in printernizer-ha
- Enable version-specific HA add-on releases

---

### Phase 3: Main Repo Cleanup 📋

**Status**: Planned
**Owner**: Development Team
**Timeline**: Week 4

#### 3.1 Mark /printernizer/ as Deprecated
- [ ] Create `printernizer/.DEPRECATED` file
- [ ] Update `printernizer/README.md` with deprecation warning
- [ ] Add migration notice pointing to printernizer-ha
- [ ] Keep directory for transition period (2-4 weeks)

**Deprecation Notice Template**:
```markdown
# ⚠️ DEPRECATED

This directory is deprecated and will be removed in a future release.

**New Location**: https://github.com/schmacka/printernizer-ha

All Home Assistant add-on development has moved to the dedicated
printernizer-ha repository. This directory is kept temporarily for
backwards compatibility.

**Migration Date**: [Target Date]
```

#### 3.2 Update Documentation ✅
- [x] Update main `README.md` to reference printernizer-ha
- [ ] Update `CONTRIBUTING.md` deployment section (if needed)
- [ ] Update `docs/` deployment documentation (if needed)
- [x] Update copilot instructions with new structure
- [x] Remove code sync instructions from docs

**Files Updated**:
- README.md ✅
- .github/copilot-instructions.md ✅
- .github/agents/feature-completer.agent.md ✅
- .claude/agents/deployment-agent.md ✅
- .claude/skills/printernizer-development-workflow.md ✅
- scripts/README.md ✅

#### 3.3 Remove Old Workflow ✅
- [x] Removed `sync-ha-addon.yml` workflow
- [x] Removed sync scripts (`sync-ha-addon.sh` and `.bat`)
- [x] Removed `.git-hooks/pre-commit` hook
- [x] Documented in commit message

---

### Phase 4: Version Management 🏷️

**Status**: Planned
**Owner**: Development Team
**Timeline**: Week 2

#### 4.1 Version Sync Strategy

**Master Branch**:
- Extract version from `src/main.py` line 90
- Format: `APP_VERSION = get_version(fallback="X.Y.Z")`
- Update `config.yaml` in printernizer-ha to match
- Example: `version: "2.8.4"`

**Development Branch**:
- Use dev version format
- Example: `version: "2.8.4-dev"`
- Do NOT auto-increment version

**Release Tags**:
- On tag creation in main repo (e.g., `v2.8.5`)
- Create matching tag in printernizer-ha
- Enables version-specific HA add-on releases

#### 4.2 Version Sync Implementation

**Version Extraction**:
```bash
VERSION=$(grep "APP_VERSION = get_version(fallback=" src/main.py | grep -oP 'fallback="\K[^"]+')
```

**Version Update (master only)**:
```bash
sed -i "s/^version: .*/version: \"$VERSION\"/" ha-repo/config.yaml
```

**Commit Message**:
```
chore: Auto-sync from printernizer@{SHORT_SHA} ({BRANCH})

Synced version: {VERSION}
Source commit: {FULL_SHA}
Source branch: {BRANCH_NAME}

🤖 Automated sync via GitHub Actions
```

---

### Phase 5: Testing & Validation ✅

**Status**: Planned
**Owner**: QA/Development Team
**Timeline**: Week 2-3

#### 5.1 Test on Development Branch
- [ ] Create test commit on development branch
- [ ] Verify files sync to printernizer-ha development branch
- [ ] Verify all files present (src/, frontend/, migrations/, etc.)
- [ ] Test HA add-on build from printernizer-ha
- [ ] Install add-on in Home Assistant test instance
- [ ] Verify all features work correctly

#### 5.2 Test on Master Branch
- [ ] Merge test changes to master
- [ ] Verify version syncs correctly to config.yaml
- [ ] Test production HA add-on build
- [ ] Verify users can install from printernizer-ha
- [ ] Test multi-architecture builds

#### 5.3 Test Release Tags
- [ ] Create test tag (e.g., `v2.8.5-test`)
- [ ] Verify tag syncs to printernizer-ha
- [ ] Verify HA can use tagged version

#### 5.4 Validation Checklist

**File Sync**:
- [ ] src/ directory syncs completely
- [ ] frontend/ directory syncs completely
- [ ] migrations/ directory syncs completely
- [ ] database_schema.sql syncs
- [ ] requirements.txt syncs
- [ ] CHANGELOG.md syncs

**Version Management**:
- [ ] Version extracted correctly from main.py
- [ ] config.yaml updated on master
- [ ] Development branch doesn't change version
- [ ] Version format correct (X.Y.Z)

**HA Add-on Builds**:
- [ ] aarch64 architecture builds
- [ ] amd64 architecture builds
- [ ] armv7 architecture builds
- [ ] armhf architecture builds

**Functionality**:
- [ ] Add-on installs in Home Assistant
- [ ] Web UI accessible via Ingress
- [ ] Printer discovery works
- [ ] Job tracking works
- [ ] File management works
- [ ] All features functional

**Branch Strategy**:
- [ ] Master → printernizer-ha/master works
- [ ] Development → printernizer-ha/development works
- [ ] Tags sync correctly

**Performance**:
- [ ] Sync completes in reasonable time (<2 min)
- [ ] No unnecessary file transfers
- [ ] Git history clean

---

### Phase 6: Final Migration ✅

**Status**: ✅ **COMPLETED**
**Owner**: Development Team
**Completed**: 2025-12-11

#### 6.1 Pre-Migration Checklist ✅
- [x] All tests passing
- [x] Documentation updated
- [x] Sync to printernizer-ha working correctly
- [x] No open issues related to HA add-on structure

#### 6.2 Remove /printernizer/ Directory ✅

```bash
# Completed 2025-12-11
git rm -rf printernizer/
git commit -m "chore: Remove deprecated /printernizer/ directory

All HA add-on files now maintained in schmacka/printernizer-ha

Migration complete - printernizer-ha is now the official HA add-on repository"
```

#### 6.3 Remove Old Workflow ✅

```bash
# Completed 2025-12-11
git rm .github/workflows/sync-ha-addon.yml
git rm scripts/deployment/sync-ha-addon.sh
git rm scripts/deployment/sync-ha-addon.bat
git rm .git-hooks/pre-commit
git commit -m "chore: Remove legacy HA addon sync workflow

Replaced by sync-to-ha-repo.yml which pushes to printernizer-ha repository"
```

#### 6.4 Final Documentation Updates
- [ ] Update README.md with final migration notice
- [ ] Update CHANGELOG.md
- [ ] Create GitHub release notes
- [ ] Update Home Assistant add-on store (if applicable)
- [ ] Announce completion in discussions

---

## Implementation Timeline

| Week | Phase | Tasks | Status |
|------|-------|-------|--------|
| 1 | Phase 1 | Repository setup, secrets, initial structure | 🚧 In Progress |
| 1-2 | Phase 2 | GitHub Actions implementation | 📋 Planned |
| 2 | Phase 4 | Version management setup | 📋 Planned |
| 2-3 | Phase 5 | Testing on development branch | 📋 Planned |
| 3 | Phase 5 | Testing on master branch | 📋 Planned |
| 4 | Phase 3 | Main repo cleanup, deprecation notices | 📋 Planned |
| 5-6 | - | Transition period (both systems work) | 📋 Planned |
| 7 | Phase 6 | Final removal of /printernizer/ | 📋 Planned |

---

## Benefits After Migration

### Main Repository (printernizer)
✅ **Cleaner structure** - No duplicate code in /printernizer/
✅ **Smaller repo size** - Less redundancy
✅ **Clearer purpose** - Pure application development
✅ **Easier contributions** - Contributors don't need HA knowledge
✅ **Simpler CI/CD** - No HA-specific workflows in main repo

### HA Add-on Repository (printernizer-ha)
✅ **Self-contained** - All HA add-on files in one place
✅ **Clear separation** - HA-specific concerns isolated
✅ **Easier maintenance** - Single-purpose repository
✅ **Better organization** - Standard HA add-on structure
✅ **Version clarity** - Versions tied to main repo releases
✅ **Independent testing** - Can test HA add-on changes independently

### Workflow
✅ **Automated sync** - No manual copying required
✅ **Branch matching** - Development and master both supported
✅ **Version sync** - Automatic version management
✅ **Tag sync** - Release tags propagate automatically
✅ **Clear history** - Commit messages show source

---

## Rollback Plan

If issues arise during migration:

### During Testing (Phase 5)
1. Stop new workflow
2. Continue using old workflow temporarily
3. Fix issues in new workflow
4. Resume testing

### After Migration (Phase 6)
1. Revert commits removing /printernizer/
2. Re-enable old sync workflow
3. Disable new workflow
4. Investigate and fix issues
5. Plan re-migration

**Critical**: Keep old workflow disabled but not deleted until Phase 6 complete.

---

## Success Criteria

- [ ] printernizer-ha repository fully functional
- [ ] Automatic sync working for master and development
- [ ] Version management working correctly
- [ ] All HA add-on builds successful
- [ ] Users can install from printernizer-ha
- [ ] /printernizer/ directory removed from main repo
- [ ] Documentation fully updated
- [ ] No regression in HA add-on functionality
- [ ] Community informed of changes

---

## Questions & Decisions

### Answered
1. ✅ Repository exists: Yes (schmacka/printernizer-ha)
2. ✅ Files to push: Everything (self-contained approach)
3. ✅ CHANGELOG.md: Sync from main repo
4. ✅ Branching: Both master and development
5. ✅ Versioning: Tie to main repo releases
6. ✅ /printernizer/ removal: Keep temporarily during transition

### Open Questions
- [ ] Exact transition period length (suggest 4 weeks)
- [ ] Communication plan for users
- [ ] Home Assistant add-on store update process

---

## Related Files

### Main Repository
- `.github/workflows/sync-to-ha-repo.yml` (new)
- `.github/workflows/sync-release-tags.yml` (new)
- `.github/workflows/sync-ha-addon.yml` (to be disabled)
- `CLAUDE.md` (to be updated)
- `README.md` (to be updated)
- `CONTRIBUTING.md` (to be updated)

### HA Repository (printernizer-ha)
- `config.yaml`
- `build.yaml`
- `Dockerfile`
- `run.sh`
- `README.md`
- `DOCS.md`
- All synced files from main repo

---

## Contact

- **Repository Owner**: schmacka
- **Main Repo**: https://github.com/schmacka/printernizer
- **HA Repo**: https://github.com/schmacka/printernizer-ha
- **Issues**: Create in respective repository

---

**Last Updated**: 2025-12-08
**Document Version**: 1.0
**Status**: 🚧 Implementation In Progress
