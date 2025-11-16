@echo off
REM Printernizer Docker Rebuild Script (Windows)
REM Stops the existing container, removes it, and builds a fresh new one

setlocal enabledelayedexpansion

echo ========================================
echo Printernizer Docker Rebuild Script
echo ========================================
echo.

REM Get script directory and project root
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."
set "DOCKER_DIR=%PROJECT_ROOT%\docker"

REM Check if docker-compose.yml exists
if not exist "%DOCKER_DIR%\docker-compose.yml" (
    echo [ERROR] docker-compose.yml not found in %DOCKER_DIR%
    exit /b 1
)

REM Change to docker directory
cd /d "%DOCKER_DIR%"

REM Step 1: Stop and remove existing containers
echo [Step 1] Stopping and removing existing containers...
docker-compose ps -q printernizer >nul 2>&1
if %errorlevel% equ 0 (
    docker-compose down
    echo [OK] Container stopped and removed
) else (
    echo [INFO] No running containers found
)
echo.

REM Step 2: Remove old image (optional - for truly fresh build)
echo [Step 2] Removing old Docker image...
docker images printernizer:latest -q >nul 2>&1
if %errorlevel% equ 0 (
    docker rmi printernizer:latest 2>nul || echo [WARN] Could not remove image (may be in use)
    echo [OK] Old image removed
) else (
    echo [INFO] No existing image found
)
echo.

REM Step 3: Build fresh image (no cache)
echo [Step 3] Building fresh Docker image (no cache)...
echo This may take several minutes...
docker-compose build --no-cache
if %errorlevel% neq 0 (
    echo [ERROR] Build failed!
    exit /b 1
)
echo [OK] Fresh image built successfully
echo.

REM Step 4: Start the new container
echo [Step 4] Starting new container...
docker-compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start container!
    exit /b 1
)
echo [OK] Container started
echo.

REM Step 5: Wait for health check
echo [Step 5] Waiting for application to be healthy...
echo This may take up to 40 seconds...
echo.

set /a timeout=60
set /a elapsed=0

:healthcheck_loop
if %elapsed% geq %timeout% (
    echo [WARN] Health check timeout
    echo Check container logs with: docker-compose logs -f
    goto :done
)

REM Check if container is healthy
docker inspect --format="{{.State.Health.Status}}" printernizer 2>nul | findstr /C:"healthy" >nul
if %errorlevel% equ 0 (
    echo [OK] Application is healthy and ready!
    goto :done
)

timeout /t 5 /nobreak >nul
set /a elapsed+=5
echo Waiting... (%elapsed% seconds)
goto :healthcheck_loop

:done
echo.

REM Display container status
echo ========================================
echo Container Status:
echo ========================================
docker-compose ps
echo.

REM Display useful commands
echo ========================================
echo Container is running!
echo ========================================
echo Application URL:  http://localhost:8000
echo Health Check:     http://localhost:8000/api/v1/health
echo.
echo Useful commands:
echo   View logs:         docker-compose logs -f
echo   Stop container:    docker-compose stop
echo   Restart:           docker-compose restart
echo   Remove all:        docker-compose down
echo   Remove with data:  docker-compose down -v
echo.

endlocal
