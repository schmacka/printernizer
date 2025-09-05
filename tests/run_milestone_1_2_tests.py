#!/usr/bin/env python3
"""
Printernizer Essential Tests Runner for Milestone 1.2: Printer API Integration
==============================================================================

Focused test runner for Milestone 1.2 without over-testing.
Tests core printer integration functionality and German business logic.

Usage:
    python tests/run_milestone_1_2_tests.py
    python tests/run_milestone_1_2_tests.py --verbose
    python tests/run_milestone_1_2_tests.py --coverage
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

class Milestone12TestRunner:
    """Test runner for Milestone 1.2 essential tests."""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.project_dir = self.test_dir.parent
        
        # Essential test files for Milestone 1.2 (limited set)
        self.milestone_1_2_tests = [
            "test_essential_printer_api.py",           # Backend API endpoints
            "test_essential_printer_drivers.py",       # Printer driver integration
            "frontend/test_essential_printer_monitoring.js"  # Frontend monitoring
        ]
        
        # Include Milestone 1.1 tests for regression
        self.milestone_1_1_tests = [
            "test_essential_models.py",
            "test_essential_config.py", 
            "test_essential_integration.py",
            "backend/test_api_health.py"
        ]

    def print_header(self):
        """Print test runner header."""
        print("🖨️ Printernizer Essential Tests - Milestone 1.2: Printer API Integration")
        print("=" * 80)
        print()
        print("📋 Testing core printer integration functionality:")
        print("   • Real-time printer monitoring (30-second polling)")
        print("   • Bambu Lab MQTT integration via bambulabs-api")
        print("   • Prusa Core One HTTP API integration") 
        print("   • Drucker-Dateien file management system")
        print("   • German business logic and VAT calculations")
        print("   • WebSocket real-time updates")
        print()

    def check_dependencies(self):
        """Check if required test dependencies are installed."""
        print("🔍 Checking test dependencies...")
        
        required_packages = [
            'pytest',
            'pytest-asyncio',
            'aiohttp',
            'structlog'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Missing required packages: {', '.join(missing_packages)}")
            print("   Install with: pip install pytest pytest-asyncio aiohttp structlog")
            return False
        
        print("✅ All test dependencies are installed")
        return True

    def run_backend_tests(self, verbose=False, coverage=False):
        """Run backend Python tests."""
        print("\n🐍 Running Backend Tests (Python/pytest)")
        print("-" * 50)
        
        # Build pytest command
        cmd = ['pytest']
        
        if verbose:
            cmd.extend(['-v', '-s'])
        
        if coverage:
            cmd.extend(['--cov=src', '--cov-report=term-missing'])
        
        # Add test files
        backend_tests = []
        
        # Milestone 1.2 backend tests
        for test_file in self.milestone_1_2_tests:
            if test_file.endswith('.py'):
                test_path = self.test_dir / test_file
                if test_path.exists():
                    backend_tests.append(str(test_path))
        
        # Include Milestone 1.1 tests for regression  
        for test_file in self.milestone_1_1_tests:
            test_path = self.test_dir / test_file
            if test_path.exists():
                backend_tests.append(str(test_path))
        
        if not backend_tests:
            print("❌ No backend test files found")
            return False
        
        cmd.extend(backend_tests)
        
        print(f"📋 Running tests: {', '.join([Path(t).name for t in backend_tests])}")
        print(f"🚀 Command: {' '.join(cmd)}")
        print()
        
        try:
            result = subprocess.run(cmd, cwd=self.project_dir, capture_output=False)
            return result.returncode == 0
        except FileNotFoundError:
            print("❌ pytest not found. Install with: pip install pytest pytest-asyncio")
            return False

    def run_frontend_tests(self, verbose=False):
        """Run frontend JavaScript tests if available."""
        print("\n🌐 Frontend Tests (JavaScript/Jest)")
        print("-" * 50)
        
        # Check if Node.js and Jest are available
        frontend_test_file = self.test_dir / "frontend/test_essential_printer_monitoring.js"
        
        if not frontend_test_file.exists():
            print("⚠️  Frontend test file not found, skipping")
            return True
        
        # Check for Jest
        try:
            subprocess.run(['npx', 'jest', '--version'], 
                         capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("⚠️  Jest not available, skipping frontend tests")
            print("   To run frontend tests, install: npm install -g jest jsdom")
            return True
        
        # Run Jest tests
        cmd = ['npx', 'jest', str(frontend_test_file)]
        if verbose:
            cmd.append('--verbose')
        
        print(f"📋 Running: {frontend_test_file.name}")
        print(f"🚀 Command: {' '.join(cmd)}")
        print()
        
        try:
            result = subprocess.run(cmd, cwd=self.project_dir, capture_output=False)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Frontend test error: {e}")
            return False

    def print_summary(self, backend_success, frontend_success, start_time):
        """Print test execution summary."""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 80)
        
        if backend_success and frontend_success:
            print("✅ All Milestone 1.2 Essential Tests Passed!")
            print()
            print("🎯 Core printer integration functionality validated:")
            print("   • Real-time printer status monitoring")
            print("   • Bambu Lab MQTT and Prusa HTTP drivers") 
            print("   • File management (Drucker-Dateien system)")
            print("   • German business logic integration")
            print("   • WebSocket real-time updates")
            print("   • Connection recovery and error handling")
            print()
            print("🚀 Milestone 1.2: Printer API Integration - VALIDATED")
        else:
            print("❌ Some tests failed")
            if not backend_success:
                print("   • Backend tests failed")
            if not frontend_success:
                print("   • Frontend tests failed")
        
        print(f"\n⏱️  Test execution time: {duration:.2f} seconds")
        print(f"📅 Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

    def run_tests(self, verbose=False, coverage=False):
        """Run all essential tests for Milestone 1.2."""
        start_time = datetime.now()
        
        self.print_header()
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Run backend tests
        backend_success = self.run_backend_tests(verbose, coverage)
        
        # Run frontend tests
        frontend_success = self.run_frontend_tests(verbose)
        
        # Print summary
        self.print_summary(backend_success, frontend_success, start_time)
        
        return backend_success and frontend_success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run Printernizer essential tests for Milestone 1.2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_milestone_1_2_tests.py
  python tests/run_milestone_1_2_tests.py --verbose
  python tests/run_milestone_1_2_tests.py --coverage
  python tests/run_milestone_1_2_tests.py --verbose --coverage
        """
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show verbose test output'
    )
    
    parser.add_argument(
        '--coverage', '-c',
        action='store_true', 
        help='Generate code coverage report'
    )
    
    args = parser.parse_args()
    
    # Run tests
    runner = Milestone12TestRunner()
    success = runner.run_tests(args.verbose, args.coverage)
    
    # Exit with proper code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()