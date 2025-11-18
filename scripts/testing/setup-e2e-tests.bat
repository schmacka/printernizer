@echo off
REM Playwright E2E Test Setup and Execution Script for Printernizer

echo ========================================
echo   Printernizer Playwright E2E Tests
echo ========================================
echo.

REM Install dependencies
echo Installing test dependencies...
pip install -r requirements-test.txt
if errorlevel 1 goto error

echo.
echo Installing Playwright browsers...
playwright install
if errorlevel 1 goto error

echo.
echo Setup complete!
echo.
echo To run tests:
echo   pytest tests/e2e/
echo.
echo Or use the interactive PowerShell script:
echo   .\run-e2e-tests.ps1
echo.
goto end

:error
echo.
echo Setup failed. Please check the errors above.
pause
exit /b 1

:end
pause
