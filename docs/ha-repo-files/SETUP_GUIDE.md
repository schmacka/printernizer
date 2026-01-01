# printernizer-ha Repository Setup Guide

This guide walks through setting up the printernizer-ha repository for automatic syncing.

## Prerequisites

- GitHub account with permissions to create repositories
- Access to `schmacka` organization (or personal account)
- GitHub Personal Access Token with `repo` and `workflow` permissions

---

## Step 1: Create printernizer-ha Repository

1. Go to https://github.com/new (or your organization)
2. **Repository name**: `printernizer-ha`
3. **Description**: `Home Assistant Add-on for Printernizer - Professional 3D Printer Management`
4. **Visibility**: Public
5. **Initialize repository**:
   - ✅ Add a README file (we'll replace it)
   - ✅ Choose a license: MIT License
   - ❌ Don't add .gitignore (we'll create a custom one)
6. Click **Create repository**

---

## Step 2: Initialize Repository Structure

Clone the new repository and set up initial files:

```bash
# Clone the repository
git clone https://github.com/schmacka/printernizer-ha.git
cd printernizer-ha

# Copy HA-specific files from main printernizer repo
# (Assuming you have printernizer cloned in a sibling directory)
cp ../printernizer/printernizer/config.yaml .
cp ../printernizer/printernizer/build.yaml .
cp ../printernizer/printernizer/Dockerfile .
cp ../printernizer/printernizer/run.sh .
cp ../printernizer/printernizer/DOCS.md .
cp ../printernizer/printernizer/icon.png .
cp ../printernizer/printernizer/logo.png .

# Copy the new README from the docs folder
cp ../printernizer/docs/ha-repo-files/README.md .

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Virtual environments
venv/
env/
ENV/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Temporary files
*.tmp
temp/
EOF

# Create initial CHANGELOG.md
cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to the Printernizer Home Assistant Add-on will be documented in this file.

This file is automatically synchronized from the main [printernizer](https://github.com/schmacka/printernizer) repository.

## [Unreleased]

Initial setup of automated repository sync.

EOF

# Create branches
git checkout -b development

# Commit initial structure
git add .
git commit -m "chore: Initialize printernizer-ha repository

- Add HA-specific configuration files
- Set up repository structure
- Prepare for automated sync from main repo

This repository will be automatically synchronized from:
https://github.com/schmacka/printernizer"

# Push both branches
git push -u origin development
git checkout master
git push -u origin master
```

---

## Step 3: Configure GitHub Secrets

### 3.1 Create GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click **Generate new token** → **Generate new token (classic)**
3. **Note**: `printernizer-ha-sync`
4. **Expiration**: No expiration (or set appropriate date)
5. **Select scopes**:
   - ✅ `repo` (all repo permissions)
   - ✅ `workflow` (update workflows)
6. Click **Generate token**
7. **COPY THE TOKEN** (you won't see it again!)

### 3.2 Add Secret to Main Repository

1. Go to https://github.com/schmacka/printernizer
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. **Name**: `HA_REPO_TOKEN`
5. **Secret**: Paste the token you created
6. Click **Add secret**

---

## Step 4: Test Initial Sync

### 4.1 Enable Workflows in Main Repo

The workflows are already created in the main repository:
- `.github/workflows/sync-to-ha-repo.yml`
- `.github/workflows/sync-release-tags.yml`

### 4.2 Trigger Manual Sync (Optional)

To test the sync before making actual changes:

1. Go to https://github.com/schmacka/printernizer/actions
2. Click **Sync to HA Add-on Repository**
3. Click **Run workflow**
4. Select branch: `development`
5. Click **Run workflow**

Wait for the workflow to complete and check printernizer-ha for synced files.

### 4.3 Verify Sync Results

Check printernizer-ha repository for:
- ✅ `src/` directory (synced)
- ✅ `frontend/` directory (synced)
- ✅ `migrations/` directory (synced)
- ✅ `database_schema.sql` (synced)
- ✅ `requirements.txt` (synced)
- ✅ `CHANGELOG.md` (synced)
- ✅ `config.yaml` version updated (master only)

---

## Step 5: Update Main Repository Documentation

### 5.1 Add Deprecation Notice to /printernizer/

```bash
cd ../printernizer

# Create deprecation notice
cat > printernizer/.DEPRECATED << 'EOF'
⚠️ DEPRECATED ⚠️

This directory is deprecated and will be removed in a future release.

New Location: https://github.com/schmacka/printernizer-ha

All Home Assistant add-on development has moved to the dedicated
printernizer-ha repository.

Migration Timeline:
- 2025-12-08: Migration started, auto-sync enabled
- 2026-01-08: Planned removal date (4 weeks)

This directory is kept temporarily for backwards compatibility.
EOF

# Update printernizer/README.md
cat > printernizer/README.md << 'EOF'
# ⚠️ DEPRECATED

This directory has been replaced by a dedicated repository.

## New Location

**Home Assistant Add-on**: https://github.com/schmacka/printernizer-ha

## What Changed?

The Printernizer Home Assistant add-on now has its own repository for:
- Cleaner separation of concerns
- Easier maintenance
- Automatic version syncing
- No code duplication

## Migration

If you're developing the HA add-on:
1. Clone the new repository: `git clone https://github.com/schmacka/printernizer-ha.git`
2. Make HA-specific changes there
3. For source code changes, continue using the main printernizer repository

## Timeline

- **Started**: 2025-12-08
- **Removal**: Approximately 4 weeks (2026-01-08)

This directory will be completely removed after the transition period.

For questions, see the [migration documentation](../docs/HA_REPO_MIGRATION.md).
EOF

git add printernizer/.DEPRECATED printernizer/README.md
git commit -m "chore: Mark /printernizer/ as deprecated

The HA add-on has moved to https://github.com/schmacka/printernizer-ha

See docs/HA_REPO_MIGRATION.md for details."
```

---

## Step 6: Validate Setup

### Checklist

- [ ] printernizer-ha repository created
- [ ] Initial files committed (config.yaml, Dockerfile, etc.)
- [ ] Master and development branches created
- [ ] GitHub Personal Access Token created
- [ ] `HA_REPO_TOKEN` secret added to main repo
- [ ] Workflows exist in main repo:
  - [ ] sync-to-ha-repo.yml
  - [ ] sync-release-tags.yml
- [ ] Manual workflow test successful
- [ ] Files synced correctly to printernizer-ha
- [ ] Version updated in config.yaml (master branch)
- [ ] Deprecation notice added to main repo

---

## Step 7: First Real Test

Make a small change in the main repository to trigger automatic sync:

```bash
cd ../printernizer

# Make sure you're on development branch
git checkout development

# Make a small, safe change (e.g., add a comment)
echo "# Test sync comment" >> src/main.py

git add src/main.py
git commit -m "test: Trigger HA repo sync test"
git push origin development
```

Then verify:
1. GitHub Action runs in main repo
2. Changes appear in printernizer-ha development branch
3. Commit message references source commit

---

## Troubleshooting

### Workflow Fails with "Permission Denied"

**Problem**: `HA_REPO_TOKEN` doesn't have correct permissions

**Solution**:
1. Verify token has `repo` and `workflow` scopes
2. Regenerate token if needed
3. Update secret in main repo settings

### Branch Doesn't Exist in HA Repo

**Problem**: Workflow tries to sync to non-existent branch

**Solution**:
The workflow now automatically creates branches. If it fails:
1. Manually create the branch in printernizer-ha
2. Push at least one commit
3. Re-run the workflow

### Files Not Syncing

**Problem**: Changes don't appear in printernizer-ha

**Solution**:
1. Check the workflow run logs in GitHub Actions
2. Verify the `paths:` in workflow matches changed files
3. Check if commits were made to monitored directories

### Version Not Updating

**Problem**: `config.yaml` version stays old

**Solution**:
1. Version only updates on **master** branch
2. Check `src/main.py` line 90 has correct format
3. Verify regex in workflow: `grep "APP_VERSION = get_version(fallback="`

---

## Next Steps

After successful setup:

1. **Phase 3**: Monitor sync for 1-2 weeks
2. **Phase 4**: Test HA add-on builds from printernizer-ha
3. **Phase 5**: Announce migration to users
4. **Phase 6**: Remove `/printernizer/` directory after transition

See [HA_REPO_MIGRATION.md](../HA_REPO_MIGRATION.md) for complete migration plan.

---

## Support

- **Issues**: https://github.com/schmacka/printernizer/issues
- **Discussions**: https://github.com/schmacka/printernizer/discussions
- **Documentation**: ../HA_REPO_MIGRATION.md

---

**Setup Date**: 2025-12-08
**Document Version**: 1.0
