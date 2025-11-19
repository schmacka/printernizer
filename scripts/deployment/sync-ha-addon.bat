@echo off
REM sync-ha-addon.bat
REM Syncs source code from /src to /printernizer/src for Home Assistant add-on
REM
REM This script maintains a single source of truth in /src/ while ensuring
REM the Home Assistant add-on has the files it needs in its build context.
REM

setlocal enabledelayedexpansion

echo === Printernizer HA Add-on Sync ===
echo.

REM Get script directory and project root
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."

echo Project root: %PROJECT_ROOT%
echo.

REM Sync source code
echo Syncing src/ --^> printernizer/src/
robocopy "%PROJECT_ROOT%\src" "%PROJECT_ROOT%\printernizer\src" /MIR /NFL /NDL /NJH /NJS /NC /NS /NP ^
    /XD __pycache__ .pytest_cache *.egg-info ^
    /XF *.pyc *.pyo

if !ERRORLEVEL! LEQ 1 (
    echo [OK] Source code synced successfully
) else (
    echo [ERROR] Source code sync failed
    exit /b 1
)

echo.

REM Sync frontend
echo Syncing frontend/ --^> printernizer/frontend/
robocopy "%PROJECT_ROOT%\frontend" "%PROJECT_ROOT%\printernizer\frontend" /MIR /NFL /NDL /NJH /NJS /NC /NS /NP ^
    /XD node_modules .vite dist

if !ERRORLEVEL! LEQ 1 (
    echo [OK] Frontend synced successfully
) else (
    echo [ERROR] Frontend sync failed
    exit /b 1
)

echo.
echo === Sync completed successfully ===
echo.
echo Files in /src/ and /frontend/ have been synchronized to:
echo   - printernizer/src/
echo   - printernizer/frontend/
echo.
echo The Home Assistant add-on build will now use the latest code.
echo.

endlocal
exit /b 0
