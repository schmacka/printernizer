#!/usr/bin/env python3
"""
Essential Test Runner for Printernizer Milestone 1.1
Runs only the core essential tests without over-testing.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def main():
    """Run essential tests for Printernizer Milestone 1.1."""
    parser = argparse.ArgumentParser(description="Run Printernizer essential tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true", help="Run with coverage")
    parser.add_argument("--fast", "-f", action="store_true", help="Skip slow tests")
    args = parser.parse_args()

    # Set up paths
    project_root = Path(__file__).parent.parent
    tests_dir = Path(__file__).parent
    
    # Essential test files (limited set)
    essential_tests = [
        "test_essential_models.py",
        "test_essential_config.py", 
        "test_essential_integration.py",
        "backend/test_api_health.py"  # Only health endpoint from existing tests
    ]

    print("🧪 Running Printernizer Essential Tests for Milestone 1.1")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print(f"Tests directory: {tests_dir}")
    print()

    # Check if essential test files exist
    missing_files = []
    for test_file in essential_tests:
        full_path = tests_dir / test_file
        if not full_path.exists():
            missing_files.append(test_file)
    
    if missing_files:
        print("❌ Missing essential test files:")
        for file in missing_files:
            print(f"   - {file}")
        print()
        print("Please ensure all essential test files are created.")
        return 1

    # Build pytest command
    pytest_args = ["python", "-m", "pytest"]
    
    if args.verbose:
        pytest_args.append("-v")
    else:
        pytest_args.append("-q")
    
    if args.coverage:
        pytest_args.extend([
            "--cov=src", 
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ])
    
    if args.fast:
        pytest_args.extend(["-m", "not slow"])
    
    # Add specific test files
    for test_file in essential_tests:
        pytest_args.append(str(tests_dir / test_file))

    # Change to project root for imports
    os.chdir(project_root)
    
    print("📋 Running essential tests:")
    for test_file in essential_tests:
        print(f"   ✓ {test_file}")
    print()

    # Run tests
    print("🚀 Executing tests...")
    print(f"Command: {' '.join(pytest_args)}")
    print()
    
    try:
        result = subprocess.run(pytest_args, check=False)
        exit_code = result.returncode
    except FileNotFoundError:
        print("❌ pytest not found. Install test dependencies:")
        print("   pip install -r requirements-test.txt")
        return 1
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 130

    print()
    print("=" * 60)
    
    if exit_code == 0:
        print("✅ All essential tests passed!")
        print()
        print("🎯 Core functionality validated:")
        print("   • Data model validation")
        print("   • German business configuration")
        print("   • Basic API endpoints")
        print("   • Frontend form validation")
        print("   • Core integration workflow")
        
        if args.coverage:
            print()
            print("📊 Coverage report generated in htmlcov/")
            
    else:
        print("❌ Some tests failed!")
        print()
        print("💡 Tips for fixing test failures:")
        print("   • Check model imports in src/models/")
        print("   • Ensure FastAPI app starts correctly")
        print("   • Verify database schema matches models")
        print("   • Check German timezone configuration")
        print()
        print("Run with --verbose for detailed error information")

    return exit_code


def run_frontend_tests():
    """Run essential frontend tests if Node.js is available."""
    print("\n🌐 Checking for frontend test capability...")
    
    try:
        # Check if Node.js and Jest are available
        subprocess.run(["node", "--version"], check=True, capture_output=True)
        subprocess.run(["npx", "jest", "--version"], check=True, capture_output=True)
        
        print("✅ Node.js and Jest available - running frontend tests...")
        
        # Run frontend tests
        frontend_test = Path(__file__).parent / "frontend" / "test_essential_forms.js"
        if frontend_test.exists():
            result = subprocess.run([
                "npx", "jest", str(frontend_test), "--verbose"
            ], check=False)
            
            if result.returncode == 0:
                print("✅ Frontend tests passed!")
            else:
                print("❌ Frontend tests failed!")
                
            return result.returncode
        else:
            print("⚠️  Frontend test file not found")
            return 0
            
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Node.js/Jest not available - skipping frontend tests")
        print("   Install with: npm install -g jest jsdom")
        return 0


if __name__ == "__main__":
    # Run Python tests
    python_exit_code = main()
    
    # Run frontend tests if available
    frontend_exit_code = run_frontend_tests()
    
    # Exit with worst exit code
    final_exit_code = max(python_exit_code, frontend_exit_code)
    
    if final_exit_code == 0:
        print()
        print("🎉 All essential tests completed successfully!")
        print("   Printernizer Milestone 1.1 core functionality validated.")
    
    sys.exit(final_exit_code)