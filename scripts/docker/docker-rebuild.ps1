# Printernizer Docker Rebuild Script (PowerShell)
# Stops the existing container, removes it, and builds a fresh new one

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Printernizer Docker Rebuild Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$DockerDir = Join-Path $ProjectRoot "docker"

# Check if docker-compose.yml exists
$ComposeFile = Join-Path $DockerDir "docker-compose.yml"
if (-not (Test-Path $ComposeFile)) {
    Write-Host "Error: docker-compose.yml not found in $DockerDir" -ForegroundColor Red
    exit 1
}

# Change to docker directory
Set-Location $DockerDir

# Step 1: Stop and remove existing containers
Write-Host "Step 1: Stopping and removing existing containers..." -ForegroundColor Yellow
docker-compose down 2>$null
Write-Host "[OK] Containers stopped" -ForegroundColor Green
Write-Host ""

# Step 2: Remove old images and clean up dangling images
Write-Host "Step 2: Removing old Docker images and cleaning up..." -ForegroundColor Yellow
docker rmi printernizer:latest 2>$null
$danglingImages = docker images -f "dangling=true" -q
if ($danglingImages) {
    Write-Host "Removing dangling images..." -ForegroundColor Cyan
    docker rmi $danglingImages 2>$null
}
Write-Host "[OK] Images cleaned up" -ForegroundColor Green
Write-Host ""

# Step 3: Build fresh image (no cache)
Write-Host "Step 3: Building fresh Docker image (no cache)..." -ForegroundColor Yellow
Write-Host "This may take several minutes..." -ForegroundColor Cyan
docker-compose build --no-cache
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Fresh image built successfully" -ForegroundColor Green
Write-Host ""

# Step 4: Start the new container
Write-Host "Step 4: Starting new container..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to start container!" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Container started" -ForegroundColor Green
Write-Host ""

# Step 5: Wait for health check
Write-Host "Step 5: Waiting for application to be healthy..." -ForegroundColor Yellow
Write-Host "This may take up to 40 seconds..." -ForegroundColor Cyan
Write-Host ""

$maxWait = 60
$waited = 0
$healthy = $false

while ($waited -lt $maxWait) {
    $status = docker inspect --format='{{.State.Health.Status}}' printernizer 2>$null
    if ($status -eq "healthy") {
        Write-Host "[OK] Application is healthy and ready!" -ForegroundColor Green
        $healthy = $true
        break
    }

    Start-Sleep -Seconds 5
    $waited += 5
    $message = "Waiting... " + $waited + " seconds"
    Write-Host $message -ForegroundColor Cyan
}

if (-not $healthy) {
    Write-Host "[WARN] Health check timeout" -ForegroundColor Yellow
    Write-Host "Check container logs with: docker-compose logs -f" -ForegroundColor Cyan
}
Write-Host ""

# Display container status
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Container Status:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
docker-compose ps
Write-Host ""

# Display useful information
Write-Host "========================================" -ForegroundColor Green
Write-Host "Container is running!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Application URL:  http://localhost:8000"
Write-Host "Health Check:     http://localhost:8000/api/v1/health"
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  View logs:         docker-compose logs -f"
Write-Host "  Stop container:    docker-compose stop"
Write-Host "  Restart:           docker-compose restart"
Write-Host "  Remove all:        docker-compose down"
Write-Host "  Remove with data:  docker-compose down -v"
Write-Host ""
