#!/usr/bin/env python3
"""
Simple test runner for working Printernizer tests
================================================

This script runs only the tests that are known to work,
providing a baseline for development and CI/CD.
"""
import os
import sys
import subprocess
from datetime import datetime


def run_working_tests():
    """Run the working test suite."""
    print("Running Printernizer Working Test Suite")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # List of test files that are known to work
    working_tests = [
        "tests/test_essential_config.py",
        "tests/test_essential_models.py",
        "tests/test_working_core.py",
        "tests/test_essential_printer_api.py"
    ]

    # Test command with basic options
    cmd = [
        "python", "-m", "pytest",
        *working_tests,
        "-v",
        "--tb=short",
        "--durations=10"
    ]

    print(f"Running command: {' '.join(cmd)}")
    print("-" * 60)

    try:
        # Run tests
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("Errors/Warnings:")
            print(result.stderr)

        # Print summary
        print("\n" + "=" * 60)
        if result.returncode == 0:
            print("ALL WORKING TESTS PASSED!")
            print("   The core functionality is working correctly.")
            print("   Ready for development and testing.")
        else:
            print("Some tests failed.")
            print("   Check the output above for details.")

        return result.returncode == 0

    except Exception as e:
        print(f"Error running tests: {e}")
        return False


def run_with_coverage():
    """Run working tests with coverage report."""
    print("Running tests with coverage...")

    cmd = [
        "python", "-m", "pytest",
        "tests/test_essential_config.py",
        "tests/test_essential_models.py",
        "tests/test_working_core.py",
        "tests/test_essential_printer_api.py",
        "-v",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html:coverage/working-tests"
    ]

    result = subprocess.run(cmd)
    return result.returncode == 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run working Printernizer tests")
    parser.add_argument("--coverage", action="store_true",
                       help="Run with coverage reporting")

    args = parser.parse_args()

    if args.coverage:
        success = run_with_coverage()
    else:
        success = run_working_tests()

    sys.exit(0 if success else 1)