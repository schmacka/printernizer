# Scripts Directory

Utility scripts for Printernizer development, testing, and operations.

## 📁 Directory Structure

Scripts are organized by category for easy navigation:

```
scripts/
├── docker/          # Docker build and deployment utilities
├── deployment/      # Release and deployment scripts
├── database/        # Database management utilities
├── bambu/           # Bambu Lab printer-specific tools
├── library/         # Library management scripts
├── analysis/        # Code analysis and profiling tools
├── testing/         # Test utilities and helpers
└── utilities/       # Miscellaneous helper scripts
```

## 🐳 Docker Scripts
**Location:** [`docker/`](docker/)

Build, rebuild, and manage Docker containers.

- **docker-rebuild.sh** - Rebuild Docker container (Linux/Mac)
- **docker-rebuild.bat** - Rebuild Docker container (Windows)
- **docker-rebuild.ps1** - Rebuild Docker container (PowerShell)
- **docker-rebuild-clean.ps1** - Clean rebuild (removes volumes)

**Usage:**
```bash
# Linux/Mac
./scripts/docker/docker-rebuild.sh

# Windows (PowerShell)
.\scripts\docker\docker-rebuild.ps1

# Clean rebuild
.\scripts\docker\docker-rebuild-clean.ps1
```

## 🚀 Deployment Scripts
**Location:** [`deployment/`](deployment/)

Release automation, version management, and deployment tools.

- **create-release.sh** - Create GitHub release from tag
- **create-missing-releases.sh** - Backfill missing releases
- **cleanup-ha-changelog.sh** - Clean Home Assistant changelog
- **sync-ha-addon.sh/.bat** - Sync to Home Assistant add-on repo
- **pi-deployment/** - Raspberry Pi deployment scripts
  - **pi-setup.sh** - Automated Pi setup script
  - **deploy-to-pi.ps1** - Deploy to Raspberry Pi
  - **monitor-pi.ps1** - Monitor Pi deployment
  - **rollback-pi.ps1** - Rollback Pi deployment

**Usage:**
```bash
# Create release
./scripts/deployment/create-release.sh v2.7.0

# Deploy to Raspberry Pi
curl -fsSL https://raw.githubusercontent.com/schmacka/printernizer/master/scripts/deployment/pi-deployment/pi-setup.sh | bash
```

## 🗄️ Database Scripts
**Location:** [`database/`](database/)

Database management and maintenance tools.

- **cleanup-db-only.py** - Clean database without affecting files
- **fix-database-schema.ps1** - Fix database schema issues

**Database Schema:** See [`assets/database/schema.sql`](../assets/database/schema.sql)

**Usage:**
```bash
python scripts/database/cleanup-db-only.py
```

## 🖨️ Bambu Lab Scripts
**Location:** [`bambu/`](bambu/)

Bambu Lab printer-specific utilities and diagnostic tools.

- **bambu-credentials.py** - Credential management (use `src.utils.bambu_utils` in production)
- **download-bambu-files.py** - Main file download tool
- **quick-bambu-check.py** - Quick printer status check
- **simple-bambu-test.py** - Simple connection test
- **verify-bambu-download.py** - Verify download functionality
- **working-bambu-ftp.py** - FTP connection utility

**Setup:**
```bash
export BAMBU_USERNAME=bblp
export BAMBU_ACCESS_CODE=12345678
export BAMBU_HOST=192.168.1.100
```

**Usage:**
```bash
# Quick status check
python scripts/bambu/quick-bambu-check.py

# Download files
python scripts/bambu/download-bambu-files.py

# Verify download
python scripts/bambu/verify-bambu-download.py
```

## 📚 Library Scripts
**Location:** [`library/`](library/)

File library management and maintenance tools.

- **cleanup-library.py** - Clean up library files
- **detect-duplicates.py** - Detect duplicate files (Phase 2 analysis)
- **verify-duplicate-fix.py** - Verify duplicate removal

**Usage:**
```bash
# Detect duplicates
python scripts/library/detect-duplicates.py

# Cleanup library
python scripts/library/cleanup-library.py

# Verify fix
python scripts/library/verify-duplicate-fix.py
```

## 🔍 Analysis Scripts
**Location:** [`analysis/`](analysis/)

Code analysis, profiling, and diagnostic tools.

- **analyze-codebase.py** - Phase 1: Function inventory and dependency mapping
- **analyze-usage.py** - Phase 3: Usage pattern and dead code analysis
- **error-analysis-agent.py** - Error pattern analysis tool

**Usage:**
```bash
# Codebase analysis
python scripts/analysis/analyze-codebase.py

# Usage analysis
python scripts/analysis/analyze-usage.py

# Error analysis
python scripts/analysis/error-analysis-agent.py
```

## 🧪 Testing Scripts
**Location:** [`testing/`](testing/)

Test utilities, helpers, and E2E test management.

- **capture-screenshots.py** - Capture UI screenshots
- **run-e2e-tests.ps1** - Run E2E tests (PowerShell)
- **setup-e2e-tests.bat** - Setup E2E test environment (Windows)

**Usage:**
```bash
# Run E2E tests
.\scripts\testing\run-e2e-tests.ps1

# Setup E2E environment
.\scripts\testing\setup-e2e-tests.bat

# Capture screenshots
python scripts/testing/capture-screenshots.py
```

**See also:** [Testing Documentation](../docs/testing/)

## 🛠️ Utilities
**Location:** [`utilities/`](utilities/)

Miscellaneous helper scripts and tools.

- **kill-port-8000.bat** - Kill process on port 8000 (Windows)
- **kill-port-8000.ps1** - Kill process on port 8000 (PowerShell)

**Usage:**
```bash
# Windows
.\scripts\utilities\kill-port-8000.bat

# PowerShell
.\scripts\utilities\kill-port-8000.ps1
```

## 📝 Best Practices

### Running Scripts

1. **Always run from project root:**
   ```bash
   python scripts/category/script-name.py
   ```

2. **Check script requirements:**
   - Some scripts require environment variables
   - Some require specific Python packages
   - Check script header comments for dependencies

3. **Use virtual environment:**
   ```bash
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

### Environment Variables

Common environment variables used by scripts:

```bash
# Bambu Lab
export BAMBU_USERNAME=bblp
export BAMBU_ACCESS_CODE=your_access_code
export BAMBU_HOST=printer_ip

# Database
export DATABASE_URL=sqlite:///data/printernizer.db

# Deployment
export GITHUB_TOKEN=your_github_token
```

## 🔗 Related Documentation

- [Build Scripts](../build/) - Build and production readiness scripts
- [Testing Documentation](../docs/testing/) - Testing guides and architecture
- [Deployment Documentation](../docs/deployment/) - Deployment guides
- [Development Guide](../docs/development/) - Development workflow

---

**Last Updated:** 2025-11-15
