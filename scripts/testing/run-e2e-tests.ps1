# Playwright E2E Test Setup and Execution Script for Printernizer
# Run this script to set up and execute E2E tests

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Printernizer Playwright E2E Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Check if pip is available
try {
    $pipVersion = pip --version
    Write-Host "✓ pip found" -ForegroundColor Green
} catch {
    Write-Host "✗ pip not found. Please install pip" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 1: Installing test dependencies..." -ForegroundColor Yellow
pip install -r requirements-test.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Dependencies installed" -ForegroundColor Green

Write-Host ""
Write-Host "Step 2: Installing Playwright browsers..." -ForegroundColor Yellow
playwright install

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to install Playwright browsers" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Playwright browsers installed" -ForegroundColor Green

Write-Host ""
Write-Host "Step 3: Checking if Printernizer server is running..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Server is running at http://localhost:8000" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Server is not running at http://localhost:8000" -ForegroundColor Red
    Write-Host "  Please start the server with: .\run.bat" -ForegroundColor Yellow
    
    $startServer = Read-Host "Would you like to start the server now? (y/n)"
    if ($startServer -eq "y" -or $startServer -eq "Y") {
        Write-Host "Starting server..." -ForegroundColor Yellow
        Start-Process -FilePath ".\run.bat" -WindowStyle Normal
        Write-Host "Waiting for server to start..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        
        # Check again
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -TimeoutSec 2
            Write-Host "✓ Server started successfully" -ForegroundColor Green
        } catch {
            Write-Host "✗ Server failed to start. Please start manually with .\run.bat" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Please start the server manually before running tests" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "Step 4: Running E2E tests..." -ForegroundColor Yellow
Write-Host ""

# Ask user for test options
$testMode = Read-Host "Select test mode:`n  1. Run all tests (headless)`n  2. Run all tests (headed - see browser)`n  3. Run specific test file`n  4. Run with custom options`nEnter choice (1-4)"

switch ($testMode) {
    "1" {
        Write-Host "Running all E2E tests in headless mode..." -ForegroundColor Cyan
        pytest tests/e2e/ -v
    }
    "2" {
        Write-Host "Running all E2E tests in headed mode..." -ForegroundColor Cyan
        $env:PLAYWRIGHT_HEADLESS = "false"
        pytest tests/e2e/ -v
    }
    "3" {
        Write-Host "Available test files:" -ForegroundColor Cyan
        Write-Host "  1. test_dashboard.py"
        Write-Host "  2. test_printers.py"
        Write-Host "  3. test_jobs.py"
        Write-Host "  4. test_materials.py"
        Write-Host "  5. test_integration.py"
        $fileChoice = Read-Host "Select file (1-5)"
        
        $testFiles = @{
            "1" = "test_dashboard.py"
            "2" = "test_printers.py"
            "3" = "test_jobs.py"
            "4" = "test_materials.py"
            "5" = "test_integration.py"
        }
        
        if ($testFiles.ContainsKey($fileChoice)) {
            $testFile = $testFiles[$fileChoice]
            Write-Host "Running $testFile..." -ForegroundColor Cyan
            pytest "tests/e2e/$testFile" -v
        } else {
            Write-Host "Invalid choice" -ForegroundColor Red
            exit 1
        }
    }
    "4" {
        Write-Host "Enter pytest options (e.g., -v -k test_name --browser chromium):" -ForegroundColor Cyan
        $customOptions = Read-Host
        pytest tests/e2e/ $customOptions
    }
    default {
        Write-Host "Invalid choice, running all tests in headless mode..." -ForegroundColor Yellow
        pytest tests/e2e/ -v
    }
}

Write-Host ""
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "✗ Some tests failed. Check the output above." -ForegroundColor Red
    Write-Host "  Test artifacts saved to: test-reports/playwright/" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Test execution complete." -ForegroundColor Cyan
Write-Host ""
