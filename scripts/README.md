# Scripts Directory

Utility scripts for Printernizer development, testing, and operations.

## Analysis & Cleanup Scripts

### Codebase Analysis
- **analyze_codebase.py** - Phase 1 analysis: Function inventory and dependency mapping
- **detect_duplicates.py** - Phase 2 analysis: Duplicate function detection
- **analyze_usage.py** - Phase 3 analysis: Usage pattern and dead code analysis

Usage:
```bash
python scripts/analyze_codebase.py
python scripts/detect_duplicates.py
python scripts/analyze_usage.py
```

## Bambu Lab Printer Scripts

### Active Scripts
- **bambu_credentials.py** - Credential management (use src.utils.bambu_utils instead)
- **download_bambu_files.py** - Main file download tool
- **quick_bambu_check.py** - Quick printer status check
- **test_ssl_connection.py** - Network diagnostic

### Deleted (Consolidated)
- debug_bambu_ftp.py - Redundant
- debug_bambu_ftp_v2.py - Redundant
- download_target_file.py - Use download_bambu_files.py
- test_bambu_ftp_direct.py - Covered by tests

## Usage

Set credentials:
```bash
export BAMBU_USERNAME=bblp
export BAMBU_ACCESS_CODE=12345678
```

Download files:
```bash
python scripts/download_bambu_files.py
```

Last updated: 2025-10-04 - Action 1.1 Complete
