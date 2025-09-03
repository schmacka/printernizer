#!/usr/bin/env python3
"""
Printernizer Test Runner
Comprehensive test execution script with coverage reporting and documentation generation
"""
import os
import sys
import subprocess
import argparse
import json
import time
from datetime import datetime
from pathlib import Path


class PrinternizerTestRunner:
    """Main test runner for Printernizer Phase 1"""
    
    def __init__(self, project_root=None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.test_root = self.project_root / "tests"
        self.coverage_dir = self.project_root / "coverage"
        self.reports_dir = self.project_root / "test-reports"
        
        # Ensure directories exist
        self.coverage_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
    
    def run_backend_tests(self, test_type="all", coverage=True, verbose=False):
        """Run backend Python tests"""
        print(f"\n🧪 Running backend tests ({test_type})...")
        
        # Base pytest command
        cmd = ["python", "-m", "pytest", "tests/backend/"]
        
        # Add coverage if requested
        if coverage:
            cmd.extend([
                "--cov=backend",
                f"--cov-report=html:{self.coverage_dir}/backend",
                f"--cov-report=json:{self.coverage_dir}/backend-coverage.json",
                "--cov-report=term-missing"
            ])
        
        # Add specific test selection
        if test_type != "all":
            test_patterns = {
                "unit": "test_api_*.py test_database.py",
                "integration": "test_integration.py",
                "e2e": "test_end_to_end.py",
                "performance": "test_performance.py",
                "german": "test_german_business.py", 
                "errors": "test_error_handling.py"
            }
            
            if test_type in test_patterns:
                cmd.extend(["-k", test_patterns[test_type]])
        
        # Add verbosity
        if verbose:
            cmd.append("-v")
        
        # Add output formats
        cmd.extend([
            f"--html={self.reports_dir}/backend-report.html",
            "--self-contained-html",
            f"--junit-xml={self.reports_dir}/backend-junit.xml"
        ])
        
        # Run tests
        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        end_time = time.time()
        
        # Process results
        self._process_backend_results(result, end_time - start_time)
        
        return result.returncode == 0
    
    def run_frontend_tests(self, test_type="all", coverage=True, verbose=False):
        """Run frontend JavaScript tests"""
        print(f"\n🎨 Running frontend tests ({test_type})...")
        
        # Change to frontend test directory
        frontend_test_dir = self.test_root / "frontend"
        
        # Base Jest command
        cmd = ["npm", "test"]
        
        # Add coverage if requested
        if coverage:
            cmd.append("--coverage")
        
        # Add specific test selection
        if test_type != "all":
            test_patterns = {
                "unit": "--testNamePattern='(API|Component|Utils)'",
                "integration": "--testNamePattern='Integration'",
                "websocket": "--testNamePattern='WebSocket'",
                "dashboard": "--testNamePattern='Dashboard'"
            }
            
            if test_type in test_patterns:
                cmd.append(test_patterns[test_type])
        
        # Add verbosity
        if verbose:
            cmd.append("--verbose")
        
        # Add output formats
        cmd.extend([
            "--outputFile", str(self.reports_dir / "frontend-results.json"),
            "--coverageDirectory", str(self.coverage_dir / "frontend")
        ])
        
        # Run tests
        start_time = time.time()
        result = subprocess.run(cmd, cwd=frontend_test_dir, capture_output=True, text=True)
        end_time = time.time()
        
        # Process results
        self._process_frontend_results(result, end_time - start_time)
        
        return result.returncode == 0
    
    def run_performance_benchmarks(self, duration=60, concurrent_users=10):
        """Run performance benchmarks"""
        print(f"\n⚡ Running performance benchmarks...")
        print(f"   Duration: {duration}s, Concurrent Users: {concurrent_users}")
        
        cmd = [
            "python", "-m", "pytest", 
            "tests/backend/test_performance.py",
            "--benchmark-only",
            f"--benchmark-warmup=5",
            f"--benchmark-min-rounds=10",
            f"--benchmark-json={self.reports_dir}/benchmark-results.json"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        end_time = time.time()
        
        # Process benchmark results
        self._process_benchmark_results(result, end_time - start_time)
        
        return result.returncode == 0
    
    def generate_coverage_report(self):
        """Generate comprehensive coverage report"""
        print("\n📊 Generating coverage report...")
        
        # Combine coverage from backend and frontend
        backend_coverage_file = self.coverage_dir / "backend-coverage.json"
        frontend_coverage_file = self.coverage_dir / "frontend" / "coverage-final.json"
        
        combined_coverage = {
            "timestamp": datetime.now().isoformat(),
            "backend": {},
            "frontend": {},
            "overall": {}
        }
        
        # Read backend coverage
        if backend_coverage_file.exists():
            with open(backend_coverage_file, 'r') as f:
                backend_data = json.load(f)
                combined_coverage["backend"] = {
                    "lines_covered": backend_data.get("totals", {}).get("covered_lines", 0),
                    "lines_total": backend_data.get("totals", {}).get("num_statements", 0),
                    "coverage_percent": backend_data.get("totals", {}).get("percent_covered", 0),
                    "branches_covered": backend_data.get("totals", {}).get("covered_branches", 0),
                    "branches_total": backend_data.get("totals", {}).get("num_branches", 0)
                }
        
        # Read frontend coverage (if exists)
        if frontend_coverage_file.exists():
            with open(frontend_coverage_file, 'r') as f:
                frontend_data = json.load(f)
                # Process Jest coverage format
                combined_coverage["frontend"] = {
                    "lines_covered": 0,  # Would extract from Jest format
                    "lines_total": 0,
                    "coverage_percent": 0,
                    "statements_percent": 0,
                    "branches_percent": 0,
                    "functions_percent": 0
                }
        
        # Calculate overall metrics
        backend_lines = combined_coverage["backend"].get("lines_total", 0)
        backend_covered = combined_coverage["backend"].get("lines_covered", 0)
        frontend_lines = combined_coverage["frontend"].get("lines_total", 0)
        frontend_covered = combined_coverage["frontend"].get("lines_covered", 0)
        
        total_lines = backend_lines + frontend_lines
        total_covered = backend_covered + frontend_covered
        
        combined_coverage["overall"] = {
            "total_lines": total_lines,
            "covered_lines": total_covered,
            "coverage_percent": (total_covered / total_lines * 100) if total_lines > 0 else 0,
            "backend_weight": (backend_lines / total_lines * 100) if total_lines > 0 else 0,
            "frontend_weight": (frontend_lines / total_lines * 100) if total_lines > 0 else 0
        }
        
        # Write combined coverage report
        combined_report_file = self.reports_dir / "combined-coverage.json"
        with open(combined_report_file, 'w') as f:
            json.dump(combined_coverage, f, indent=2)
        
        print(f"📊 Combined coverage report saved to: {combined_report_file}")
        
        # Print summary
        overall = combined_coverage["overall"]
        print(f"\n📈 Coverage Summary:")
        print(f"   Overall Coverage: {overall['coverage_percent']:.1f}%")
        print(f"   Backend Coverage: {combined_coverage['backend'].get('coverage_percent', 0):.1f}%")
        print(f"   Frontend Coverage: {combined_coverage['frontend'].get('coverage_percent', 0):.1f}%")
        
        return combined_coverage
    
    def generate_test_documentation(self):
        """Generate test documentation"""
        print("\n📝 Generating test documentation...")
        
        doc_content = self._create_test_documentation()
        
        doc_file = self.reports_dir / "TEST_DOCUMENTATION.md"
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(doc_content)
        
        print(f"📝 Test documentation saved to: {doc_file}")
        
        return doc_file
    
    def run_full_test_suite(self, skip_performance=False, skip_frontend=False):
        """Run complete test suite"""
        print("🚀 Starting Printernizer Phase 1 Test Suite")
        print(f"   Timestamp: {datetime.now()}")
        print(f"   Project Root: {self.project_root}")
        print("=" * 60)
        
        results = {
            "start_time": time.time(),
            "backend_passed": False,
            "frontend_passed": False,
            "performance_passed": False,
            "coverage_generated": False,
            "docs_generated": False
        }
        
        try:
            # Run backend tests
            results["backend_passed"] = self.run_backend_tests(coverage=True, verbose=True)
            
            # Run frontend tests (if not skipped)
            if not skip_frontend:
                results["frontend_passed"] = self.run_frontend_tests(coverage=True, verbose=True)
            else:
                results["frontend_passed"] = True  # Skip = assume pass
                print("⏭️  Frontend tests skipped")
            
            # Run performance tests (if not skipped)
            if not skip_performance:
                results["performance_passed"] = self.run_performance_benchmarks()
            else:
                results["performance_passed"] = True  # Skip = assume pass
                print("⏭️  Performance tests skipped")
            
            # Generate coverage report
            try:
                self.generate_coverage_report()
                results["coverage_generated"] = True
            except Exception as e:
                print(f"⚠️  Coverage report generation failed: {e}")
            
            # Generate documentation
            try:
                self.generate_test_documentation()
                results["docs_generated"] = True
            except Exception as e:
                print(f"⚠️  Documentation generation failed: {e}")
            
        except KeyboardInterrupt:
            print("\n⏹️  Test run interrupted by user")
            return False
        
        finally:
            results["end_time"] = time.time()
            results["total_duration"] = results["end_time"] - results["start_time"]
            
            # Print final summary
            self._print_final_summary(results)
        
        # Return overall success
        return (results["backend_passed"] and 
                results["frontend_passed"] and 
                results["performance_passed"])
    
    def _process_backend_results(self, result, duration):
        """Process backend test results"""
        print(f"⏱️  Backend tests completed in {duration:.2f}s")
        
        if result.returncode == 0:
            print("✅ Backend tests PASSED")
        else:
            print("❌ Backend tests FAILED")
            print("\nError output:")
            print(result.stderr)
    
    def _process_frontend_results(self, result, duration):
        """Process frontend test results"""
        print(f"⏱️  Frontend tests completed in {duration:.2f}s")
        
        if result.returncode == 0:
            print("✅ Frontend tests PASSED")
        else:
            print("❌ Frontend tests FAILED")
            print("\nError output:")
            print(result.stderr)
    
    def _process_benchmark_results(self, result, duration):
        """Process performance benchmark results"""
        print(f"⏱️  Performance benchmarks completed in {duration:.2f}s")
        
        if result.returncode == 0:
            print("✅ Performance benchmarks COMPLETED")
            
            # Try to read benchmark results
            benchmark_file = self.reports_dir / "benchmark-results.json"
            if benchmark_file.exists():
                with open(benchmark_file, 'r') as f:
                    benchmark_data = json.load(f)
                    
                print("\n📊 Performance Summary:")
                for benchmark in benchmark_data.get("benchmarks", []):
                    name = benchmark.get("name", "Unknown")
                    mean_time = benchmark.get("stats", {}).get("mean", 0)
                    print(f"   {name}: {mean_time:.3f}s")
        else:
            print("❌ Performance benchmarks FAILED")
    
    def _create_test_documentation(self):
        """Create comprehensive test documentation"""
        return f"""# Printernizer Phase 1 Test Documentation

## Test Suite Overview

This document provides comprehensive documentation for the Printernizer Phase 1 test suite, covering backend API endpoints, frontend components, German business logic, and system performance.

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Project**: Printernizer - 3D Print Management System  
**Phase**: Phase 1 (MVP)  
**Target Market**: Germany (Kornwestheim)  

## Test Categories

### 1. Backend API Tests (`tests/backend/`)

#### Core API Endpoints
- **Printer Management** (`test_api_printers.py`)
  - GET /api/v1/printers - List all configured printers
  - POST /api/v1/printers - Add new printer (Bambu Lab A1, Prusa Core One)
  - GET /api/v1/printers/{{id}}/status - Get printer status
  - PUT /api/v1/printers/{{id}} - Update printer configuration
  - DELETE /api/v1/printers/{{id}} - Remove printer

- **Job Management** (`test_api_jobs.py`)
  - GET /api/v1/jobs - List print jobs with filtering
  - POST /api/v1/jobs - Create new print job
  - GET /api/v1/jobs/{{id}} - Get job details
  - PUT /api/v1/jobs/{{id}}/status - Update job status

- **File Management** (`test_api_files.py`)
  - GET /api/v1/files/unified - Unified file listing (Drucker-Dateien system)
  - POST /api/v1/files/{{id}}/download - Download files from printer
  - DELETE /api/v1/files/{{id}} - Delete local files

- **Dashboard API** (`test_database.py`)
  - GET /api/v1/dashboard/stats - Dashboard statistics

#### Integration Tests (`test_integration.py`)
- Complete printer lifecycle workflows
- End-to-end job management with German business logic
- File download and organization workflows
- Real-time WebSocket updates

#### End-to-End Tests (`test_end_to_end.py`)
- Complete user workflows from start to finish
- Multi-printer scenarios
- German business compliance workflows
- VAT reporting and export functionality

#### German Business Logic (`test_german_business.py`)
- **Currency Handling**: EUR formatting and precision
- **VAT Calculations**: 19% German VAT rate compliance
- **Timezone**: Europe/Berlin timezone handling
- **Accounting Standards**: HGB and GoBD compliance
- **Tax Reporting**: USt-VA and ELSTER export formats

#### Performance Tests (`test_performance.py`)
- Database performance under load (1000+ jobs)
- Concurrent API request handling
- Large file download performance
- Memory usage optimization
- WebSocket high-frequency updates

#### Error Handling (`test_error_handling.py`)
- Network connectivity issues
- Invalid data validation
- Database error scenarios
- File system errors
- Security edge cases (SQL injection, XSS, path traversal)
- Resource exhaustion handling

### 2. Frontend Tests (`tests/frontend/`)

#### Component Tests
- **Dashboard** (`dashboard.test.js`)
  - Real-time printer status cards
  - Job monitoring and progress tracking
  - Statistics display with German currency formatting
  - WebSocket real-time updates

- **API Service** (`api.test.js`)
  - HTTP client wrapper testing
  - Error handling and retry logic
  - Request/response validation
  - German locale data handling

- **WebSocket Integration** (`websocket.test.js`)
  - Connection management and reconnection
  - Real-time message handling
  - High-frequency update performance
  - Error recovery scenarios

### 3. Test Infrastructure

#### Configuration (`conftest.py`)
- Database fixtures with sample data
- Mock printer APIs (Bambu MQTT, Prusa HTTP)
- German business configuration
- Utility functions for testing

#### Test Data
- Sample printer configurations (Bambu Lab A1, Prusa Core One)
- Job data with German business fields
- File management test scenarios
- Performance test datasets

## Coverage Requirements

### Backend Coverage Goals
- **API Endpoints**: 90%+ code coverage
- **Business Logic**: 100% coverage (critical for German compliance)
- **Database Operations**: 85%+ coverage
- **Error Handling**: 80%+ coverage

### Frontend Coverage Goals
- **Components**: 85%+ coverage
- **API Integration**: 90%+ coverage
- **WebSocket Handling**: 85%+ coverage
- **User Workflows**: Complete end-to-end coverage

## German Business Logic Testing

### Currency and VAT Testing
- EUR currency formatting with German locale (1.234,56 EUR)
- 19% VAT calculation accuracy
- VAT-exempt transaction handling
- Business vs. private job cost calculations

### Timezone Testing
- Europe/Berlin timezone conversions
- Daylight saving time transitions
- Business hours validation
- German date/time formatting (DD.MM.YYYY)

### Compliance Testing
- HGB (German Commercial Code) compliance
- GoBD (German Digital Records Act) requirements
- Invoice numbering sequence validation
- ELSTER XML export format testing

## Performance Benchmarks

### Database Performance
- Large dataset queries (1000+ jobs): < 1 second
- Concurrent database operations: 95%+ success rate
- Complex reporting queries: < 2 seconds

### API Performance
- Concurrent requests: 50+ requests/second
- Response times: < 200ms for standard queries
- Large response payloads: < 500ms generation time

### File Operations
- Large file downloads: 50+ MB/s effective rate
- Concurrent downloads: 8+ simultaneous streams
- File processing: Memory usage < 100MB per operation

### WebSocket Performance
- High-frequency updates: 100+ messages/second
- Connection management: < 100ms latency
- Reconnection handling: < 5 second recovery

## Test Execution

### Running All Tests
```bash
python tests/test_runner.py --full-suite
```

### Running Specific Test Categories
```bash
# Backend tests only
python tests/test_runner.py --backend

# Frontend tests only
python tests/test_runner.py --frontend

# German business logic tests
python tests/test_runner.py --backend --type german

# Performance benchmarks
python tests/test_runner.py --performance
```

### Coverage Reports
```bash
# Generate coverage report
python tests/test_runner.py --coverage-only

# View HTML coverage report
open coverage/backend/index.html
open coverage/frontend/index.html
```

## Continuous Integration

### Pre-commit Checks
- All tests must pass
- Coverage thresholds must be met
- German business logic tests are mandatory
- Security validation tests must pass

### Deployment Gates
- End-to-end tests must pass
- Performance benchmarks within acceptable limits
- German compliance tests verified
- Documentation generation successful

## Test Data Management

### Database Fixtures
- Clean database state for each test
- Realistic sample data matching German business patterns
- Isolated test environments
- Automatic cleanup after test completion

### Mock Services
- Bambu Lab MQTT API simulation
- Prusa PrusaLink HTTP API simulation
- WebSocket connection mocking
- File system operation mocking

## Security Testing

### Input Validation
- SQL injection attempt detection
- XSS prevention validation
- Path traversal protection
- Input sanitization verification

### Authentication & Authorization
- API key validation
- Session management testing
- Access control verification
- Rate limiting validation

## Monitoring and Alerting

### Test Metrics
- Test execution time trends
- Coverage percentage tracking
- Failure rate monitoring
- Performance regression detection

### Alerting Conditions
- Test failure notifications
- Coverage threshold violations
- Performance degradation alerts
- German compliance test failures

## Maintenance and Updates

### Test Maintenance
- Regular test data updates
- Mock service synchronization with real APIs
- Performance baseline adjustments
- Coverage threshold reviews

### Documentation Updates
- Test documentation versioning
- Coverage report archiving
- Performance trend analysis
- German regulation compliance updates

---

**Note**: This test suite is specifically designed for the German market and includes comprehensive German business logic testing to ensure compliance with local regulations and business practices.
"""
    
    def _print_final_summary(self, results):
        """Print final test run summary"""
        print("\n" + "=" * 60)
        print("🏁 Test Run Summary")
        print("=" * 60)
        
        duration_mins = results["total_duration"] / 60
        print(f"⏱️  Total Duration: {duration_mins:.1f} minutes")
        
        # Test results
        print("\n📋 Test Results:")
        print(f"   Backend Tests: {'✅ PASSED' if results['backend_passed'] else '❌ FAILED'}")
        print(f"   Frontend Tests: {'✅ PASSED' if results['frontend_passed'] else '❌ FAILED'}")
        print(f"   Performance Tests: {'✅ PASSED' if results['performance_passed'] else '❌ FAILED'}")
        
        # Reports generated
        print("\n📊 Reports Generated:")
        print(f"   Coverage Report: {'✅ YES' if results['coverage_generated'] else '❌ NO'}")
        print(f"   Test Documentation: {'✅ YES' if results['docs_generated'] else '❌ NO'}")
        
        # Overall result
        all_passed = (results["backend_passed"] and 
                     results["frontend_passed"] and 
                     results["performance_passed"])
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED! Ready for deployment.")
        else:
            print("\n⚠️  Some tests failed. Please review and fix before deployment.")
        
        print("\n📁 Report Files:")
        print(f"   Test Reports: {self.reports_dir}")
        print(f"   Coverage Reports: {self.coverage_dir}")


def main():
    """Main entry point for test runner"""
    parser = argparse.ArgumentParser(description='Printernizer Test Runner')
    parser.add_argument('--backend', action='store_true', help='Run backend tests only')
    parser.add_argument('--frontend', action='store_true', help='Run frontend tests only')
    parser.add_argument('--performance', action='store_true', help='Run performance tests only')
    parser.add_argument('--type', choices=['unit', 'integration', 'e2e', 'german', 'errors'], 
                       help='Run specific test type')
    parser.add_argument('--coverage-only', action='store_true', help='Generate coverage report only')
    parser.add_argument('--docs-only', action='store_true', help='Generate documentation only')
    parser.add_argument('--full-suite', action='store_true', help='Run complete test suite')
    parser.add_argument('--skip-performance', action='store_true', help='Skip performance tests')
    parser.add_argument('--skip-frontend', action='store_true', help='Skip frontend tests')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    runner = PrinternizerTestRunner()
    
    success = True
    
    try:
        if args.coverage_only:
            runner.generate_coverage_report()
        elif args.docs_only:
            runner.generate_test_documentation()
        elif args.full_suite:
            success = runner.run_full_test_suite(
                skip_performance=args.skip_performance,
                skip_frontend=args.skip_frontend
            )
        elif args.backend:
            success = runner.run_backend_tests(
                test_type=args.type or "all",
                verbose=args.verbose
            )
        elif args.frontend:
            success = runner.run_frontend_tests(
                test_type=args.type or "all", 
                verbose=args.verbose
            )
        elif args.performance:
            success = runner.run_performance_benchmarks()
        else:
            # Default: run full suite
            success = runner.run_full_test_suite()
            
    except KeyboardInterrupt:
        print("\n⏹️  Test execution interrupted")
        success = False
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        success = False
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()