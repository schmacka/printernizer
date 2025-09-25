@echo off
REM Simple test runner batch script for Windows
REM Usage: test.bat [coverage]

echo Running Printernizer Tests...
echo.

if "%1"=="coverage" (
    echo Running with coverage...
    python run_working_tests.py --coverage
) else (
    echo Running working test suite...
    python run_working_tests.py
)

echo.
echo Test run complete. Check output above for results.
pause