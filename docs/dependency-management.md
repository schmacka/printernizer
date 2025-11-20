# Dependency Management Guide

This guide explains how automated dependency management works in the Printernizer project and how to handle dependency updates responsibly.

## Overview

Printernizer uses **GitHub Dependabot** and **automated security scanning** to keep dependencies up-to-date and secure.

### What's Automated

1. **Dependabot** - Creates PRs for dependency updates
   - Python packages ([requirements.txt](../requirements.txt))
   - Docker base images
   - GitHub Actions
   - Frontend npm packages

2. **Security Scanning** - Detects vulnerabilities
   - `pip-audit` for Python packages (weekly)
   - Trivy for container vulnerabilities (on every build)
   - Bandit for Python code security (on every build)

3. **Outdated Package Checks** - Reports available updates (weekly)

## How It Works

### Dependabot Configuration

Configured in [`.github/dependabot.yml`](../.github/dependabot.yml):

- **Schedule**: Weekly on Mondays at 9:00 AM Berlin time
- **Grouping**: Minor and patch updates are grouped together to reduce PR noise
- **Auto-labeling**: PRs are tagged with `dependencies` and ecosystem labels
- **Reviewers**: Automatically assigns maintainers

### Security Scanning

Configured in [`.github/workflows/dependency-security-scan.yml`](../.github/workflows/dependency-security-scan.yml):

- **Schedule**: Weekly on Mondays at 7:00 AM UTC
- **Triggers**: Also runs on PRs that change `requirements.txt`
- **Actions**: Creates GitHub issues for vulnerabilities
- **Reports**: Uploads detailed scan results as artifacts

## Handling Dependency Updates

### 1. Review Dependabot PRs

When Dependabot creates a PR:

```bash
# Checkout the PR branch
gh pr checkout <PR_NUMBER>

# Or manually:
git fetch origin
git checkout dependabot/<branch-name>
```

### 2. Check CI/CD Results

All Dependabot PRs automatically trigger:
- Backend tests (pytest)
- Frontend tests (Jest)
- Security scans (Trivy, Bandit)
- E2E tests (Playwright)

✅ **Green CI**: Safe to merge
⚠️ **Failed CI**: Review failures, may need code changes

### 3. Test Locally (for Major Updates)

For major version updates, test locally:

```bash
# Install updated dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run the application
python src/main.py
```

### 4. Merge the PR

```bash
# Merge via GitHub CLI
gh pr merge <PR_NUMBER> --squash --delete-branch

# Or use the GitHub web interface
```

## Dependency Version Strategies

### Pinned Versions (`==`)

Used for critical dependencies where stability is paramount:

```python
fastapi==0.104.1
uvicorn[standard]==0.24.0
```

**Pros:**
- Reproducible builds
- No surprise breakages

**Cons:**
- Manual updates required
- May miss security patches

**When to use:**
- Core framework dependencies
- Production-critical packages
- Known-stable versions

### Range Versions (`>=`, `~=`)

Used for less critical dependencies:

```python
pydantic>=2.9.0  # Any version >= 2.9.0
aiohttp>=3.10.0  # Latest compatible version
```

**Pros:**
- Automatic patch/minor updates
- Security fixes applied faster

**Cons:**
- Potential breaking changes
- Less predictable

**When to use:**
- Utility libraries
- Development dependencies
- Libraries with good semver practices

### Recommended Approach

For Printernizer, we use:

1. **Pinned versions** for core dependencies (FastAPI, Uvicorn, etc.)
2. **Range versions** for:
   - Libraries with stable APIs (Pydantic, aiohttp)
   - Development tools (pytest, mkdocs)
   - Support libraries (trimesh, Pillow)

## Security Vulnerability Handling

### Automated Alerts

When vulnerabilities are found:

1. **GitHub Security Advisory** - Appears in Security tab
2. **Dependabot Alert** - Creates security update PR automatically
3. **Weekly Scan Issue** - Created by `dependency-security-scan.yml`

### Priority Response

**Critical/High Severity:**
- Review Dependabot PR immediately
- Merge within 24-48 hours if CI passes
- Create hotfix if production is affected

**Medium/Low Severity:**
- Review within 1 week
- Bundle with other updates if possible
- Update during normal development cycle

### Manual Security Check

Run security scan manually:

```bash
# Install pip-audit
pip install pip-audit

# Scan dependencies
pip-audit --requirement requirements.txt --desc on

# Fix vulnerabilities automatically (review changes!)
pip-audit --requirement requirements.txt --fix
```

## Updating Dependencies Manually

### Update a Single Package

```bash
# Check current version
pip show fastapi

# Update to specific version
pip install fastapi==0.109.0

# Update requirements.txt
# Edit requirements.txt manually or use pip-compile (if using pip-tools)

# Test
pytest tests/ -v

# Commit
git add requirements.txt
git commit -m "chore(deps): Update fastapi to 0.109.0"
```

### Update All Packages

```bash
# Check outdated packages
pip list --outdated

# Update all (DANGEROUS - not recommended)
pip install --upgrade -r requirements.txt

# Better: Use pip-compile with pip-tools
pip install pip-tools
pip-compile --upgrade requirements.in -o requirements.txt
```

## Best Practices

### 1. Never Merge Without CI

Always wait for CI to pass:
- ✅ Backend tests passing
- ✅ Frontend tests passing
- ✅ Security scans clear
- ✅ E2E tests passing

### 2. Review Changelogs

For major updates, review:
- Package changelog/release notes
- Breaking changes
- Migration guides

### 3. Update Development Branch First

For risky updates:

```bash
# Merge to development first
git checkout development
gh pr merge <PR_NUMBER> --auto

# Test in Docker
docker-compose up -d

# Monitor for issues
docker-compose logs -f

# Merge to master after validation
```

### 4. Keep Dependencies Minimal

Before adding new dependencies:
- Is it really needed?
- Is it actively maintained?
- Does it have security issues?
- Is there a better alternative?

### 5. Regular Maintenance

**Weekly:**
- Review Dependabot PRs
- Check security scan results

**Monthly:**
- Review all outdated packages
- Plan major updates

**Quarterly:**
- Audit unused dependencies
- Review version pinning strategy

## Troubleshooting

### Dependabot PRs Not Appearing

Check:
1. [`.github/dependabot.yml`](../.github/dependabot.yml) is valid
2. Dependabot is enabled in repository settings
3. No open PRs with same update (Dependabot limits PRs)

### Security Scan Failing

```bash
# Run locally to debug
pip install pip-audit
pip-audit --requirement requirements.txt --desc on

# Check for false positives
pip-audit --requirement requirements.txt --ignore-vuln VULN-ID
```

### Conflicting Dependency Versions

```bash
# Check dependency tree
pip install pipdeptree
pipdeptree

# Find conflicts
pipdeptree --warn conflict
```

### Version Compatibility Issues

```bash
# Test in isolated environment
python -m venv test_env
source test_env/bin/activate  # or test_env\Scripts\activate on Windows

pip install -r requirements.txt
pytest tests/ -v
```

## Advanced: Using pip-tools

For more control over dependency management:

```bash
# Install pip-tools
pip install pip-tools

# Create requirements.in (high-level dependencies)
cat > requirements.in <<EOF
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.9.0
EOF

# Compile to requirements.txt (with all sub-dependencies pinned)
pip-compile requirements.in

# Upgrade all dependencies
pip-compile --upgrade requirements.in

# Upgrade specific package
pip-compile --upgrade-package fastapi requirements.in
```

## CI/CD Integration

### Dependency Update Workflow

```
┌─────────────────┐
│  Dependabot     │
│  creates PR     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   CI/CD runs    │
│   - Tests       │
│   - Security    │
│   - Build       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌─────────────────┐
│  Development    │─────▶│     Master      │
│  (testing)      │      │  (production)   │
└─────────────────┘      └─────────────────┘
```

### Version Synchronization

**Critical**: When updating dependencies that affect version compatibility:

1. Update `requirements.txt`
2. Update `docker/requirements.txt` (if different)
3. Update `printernizer/requirements.txt` (HA add-on)
4. Test all deployment methods

## Resources

- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [pip-audit Documentation](https://pypi.org/project/pip-audit/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Semantic Versioning](https://semver.org/)

## Questions?

- Check [CONTRIBUTING.md](../CONTRIBUTING.md) for development workflow
- Open an issue for dependency-related problems
- Review past Dependabot PRs for examples
