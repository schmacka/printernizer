# Branch Protection Setup

This document provides GitHub branch protection rules for the Printernizer repository.

## Why Branch Protection?

Branch protection rules ensure:
- Code quality through required reviews
- Automated testing before merge
- Prevention of accidental force pushes
- Stable production releases

## Branch Protection Rules

### `master` Branch (Production)

**Purpose**: Production-ready code for Home Assistant add-on releases

**Protection Rules**:
- ✅ **Require pull request before merging**
  - Required approvals: **1**
  - Dismiss stale reviews when new commits are pushed
  - Require review from code owners (if CODEOWNERS file exists)

- ✅ **Require status checks to pass**
  - Required checks:
    - `Backend Tests`
    - `Frontend Tests`
    - `E2E Tests (Playwright)`
    - `Security Scan`
  - Require branches to be up to date before merging

- ✅ **Require conversation resolution before merging**

- ✅ **Do not allow bypassing the above settings**

- ❌ **Do NOT require signed commits** (optional - enable if you use GPG signing)

- ✅ **Include administrators** (enforce rules for admins too)

- ❌ **Allow force pushes**: Disabled

- ❌ **Allow deletions**: Disabled

### `development` Branch (Testing/Integration)

**Purpose**: Integration branch for feature testing before production

**Protection Rules**:
- ✅ **Require pull request before merging**
  - Required approvals: **0** (optional - can be 1 for stricter workflow)
  - Dismiss stale reviews when new commits are pushed

- ✅ **Require status checks to pass**
  - Required checks:
    - `Backend Tests`
    - `Frontend Tests`
  - Require branches to be up to date before merging

- ✅ **Require conversation resolution before merging**

- ❌ **Do NOT require bypassing settings to be disabled** (allow maintainers to bypass for hotfixes)

- ❌ **Allow force pushes**: Disabled (but can be enabled for maintainers)

- ❌ **Allow deletions**: Disabled

## How to Configure on GitHub

### Step 1: Access Branch Protection Settings

1. Go to your repository on GitHub
2. Click **Settings** tab
3. Click **Branches** in the left sidebar
4. Click **Add branch protection rule**

### Step 2: Configure `master` Branch

1. **Branch name pattern**: `master`
2. Enable settings as listed above
3. Click **Create** or **Save changes**

### Step 3: Configure `development` Branch

1. Click **Add branch protection rule** again
2. **Branch name pattern**: `development`
3. Enable settings as listed above
4. Click **Create** or **Save changes**

## Testing Your Configuration

After setting up branch protection:

1. **Test PR requirement**:
   ```bash
   git checkout -b test-protection
   git commit --allow-empty -m "test: branch protection"
   git push origin test-protection
   ```
   Try to push directly to master - should fail ✓

2. **Test status checks**:
   - Create a PR to `development`
   - Verify CI/CD runs automatically
   - Verify merge is blocked until checks pass

3. **Test review requirement**:
   - Create a PR to `master`
   - Verify merge is blocked until approved

## Exceptions and Overrides

### When to Bypass Protection

Branch protection can be bypassed by administrators in these cases:
- **Critical hotfix** to production (master)
- **CI/CD failure** due to external service outage
- **Emergency rollback** of breaking changes

**Process**:
1. Document reason in PR or commit message
2. Notify team in Discussions or Issues
3. Follow up with retrospective

### Feature Branch Protection

Feature branches (`feature/*`, `fix/*`) do NOT need protection rules as they:
- Are short-lived
- Merge into `development` (which has protection)
- Are deleted after merge

## Troubleshooting

### "Required status check is not passing"

**Cause**: CI/CD tests failed or not running

**Solution**:
1. Check GitHub Actions tab for workflow status
2. Review test failures in workflow logs
3. Fix issues and push new commit
4. Re-run failed jobs if needed

### "This branch is out of date"

**Cause**: Target branch has new commits since PR was created

**Solution**:
```bash
git checkout your-feature-branch
git fetch origin
git merge origin/development  # or origin/master
git push
```

### "Approval required before merging"

**Cause**: No reviewers have approved the PR

**Solution**:
1. Request review from a team member
2. Address review comments
3. Wait for approval

## Best Practices

1. **Never force push** to protected branches
2. **Always create PRs** even for small changes
3. **Wait for CI/CD** to complete before merging
4. **Review your own PR** before requesting review
5. **Keep PRs small** (< 500 lines when possible)
6. **Write descriptive PR descriptions** with testing notes
7. **Link related issues** in PR description

## Related Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution workflow
- [RELEASE.md](RELEASE.md) - Release process
- [Development Workflow](.claude/skills/printernizer-development-workflow.md) - Branching strategy

---

**Last Updated**: 2025-11-13
**Branch Model**: Two-branch (development + master)
