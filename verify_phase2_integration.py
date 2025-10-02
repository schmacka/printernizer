#!/usr/bin/env python3
"""
Enhanced Metadata Phase 2 - Integration Verification Script
Validates that all components are properly integrated and accessible.
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists and report."""
    if filepath.exists():
        size = filepath.stat().st_size
        print(f"✅ {description}: {filepath} ({size:,} bytes)")
        return True
    else:
        print(f"❌ {description}: {filepath} NOT FOUND")
        return False

def check_file_contains(filepath, search_string, description):
    """Check if a file contains a specific string."""
    try:
        content = filepath.read_text()
        if search_string in content:
            print(f"✅ {description}")
            return True
        else:
            print(f"❌ {description} - NOT FOUND")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    """Run integration verification checks."""
    print("=" * 70)
    print("Enhanced Metadata Phase 2 - Integration Verification")
    print("=" * 70)
    print()
    
    project_root = Path(__file__).parent
    all_checks_passed = True
    
    # Check created files
    print("📁 Checking Created Files:")
    print("-" * 70)
    
    checks = [
        (project_root / "frontend/css/enhanced-metadata.css", "Enhanced Metadata CSS"),
        (project_root / "frontend/js/enhanced-metadata.js", "Enhanced Metadata JS"),
        (project_root / "docs/features/ENHANCED_METADATA_PHASE2_IMPLEMENTATION.md", "Phase 2 Documentation"),
    ]
    
    for filepath, description in checks:
        if not check_file_exists(filepath, description):
            all_checks_passed = False
    
    print()
    
    # Check HTML integration
    print("🔗 Checking HTML Integration:")
    print("-" * 70)
    
    index_html = project_root / "frontend/index.html"
    html_checks = [
        ("enhanced-metadata.css", "CSS stylesheet link"),
        ("enhanced-metadata.js", "JavaScript include"),
    ]
    
    for search_string, description in html_checks:
        if not check_file_contains(index_html, search_string, description):
            all_checks_passed = False
    
    print()
    
    # Check files.js integration
    print("🔌 Checking files.js Integration:")
    print("-" * 70)
    
    files_js = project_root / "frontend/js/files.js"
    files_checks = [
        ("loadAndRenderEnhancedMetadata", "Enhanced metadata loading function"),
        ("EnhancedFileMetadata", "EnhancedFileMetadata class usage"),
        ("enhanced-metadata-", "Metadata container ID"),
    ]
    
    for search_string, description in files_checks:
        if not check_file_contains(files_js, search_string, description):
            all_checks_passed = False
    
    print()
    
    # Check component styles
    print("🎨 Checking Component Styles:")
    print("-" * 70)
    
    components_css = project_root / "frontend/css/components.css"
    if check_file_contains(components_css, "enhanced-metadata-container", "Container styles"):
        pass
    else:
        all_checks_passed = False
    
    print()
    
    # Check version update
    print("📌 Checking Version Update:")
    print("-" * 70)
    
    health_py = project_root / "src/api/routers/health.py"
    if check_file_contains(health_py, '1.2.0', "Version 1.2.0"):
        pass
    else:
        all_checks_passed = False
    
    print()
    
    # Check JavaScript syntax
    print("✔️  Checking JavaScript Syntax:")
    print("-" * 70)
    
    try:
        import subprocess
        result = subprocess.run(
            ["node", "--check", str(project_root / "frontend/js/enhanced-metadata.js")],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ enhanced-metadata.js syntax is valid")
        else:
            print(f"❌ enhanced-metadata.js syntax error: {result.stderr}")
            all_checks_passed = False
    except Exception as e:
        print(f"⚠️  Could not verify JavaScript syntax: {e}")
    
    print()
    
    # Summary
    print("=" * 70)
    if all_checks_passed:
        print("✅ ALL CHECKS PASSED - Integration Complete!")
        print()
        print("Next Steps:")
        print("1. Start the application: ./run.sh")
        print("2. Open browser to http://localhost:8000")
        print("3. Navigate to Files page")
        print("4. Click on a 3D file (3MF, STL, G-code)")
        print("5. Verify enhanced metadata displays in preview modal")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Please review errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
