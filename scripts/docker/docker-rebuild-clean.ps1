# Printernizer Docker Clean Rebuild Script (PowerShell)
# Stops the existing container, removes it, WIPES DATA, and builds a fresh new one
# WARNING: This deletes your database, downloaded files, and resets printer config!

Write-Host "========================================" -ForegroundColor Red
Write-Host "Printernizer Docker CLEAN Rebuild Script" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""
Write-Host "WARNING: This will DELETE all local data:" -ForegroundColor Yellow
Write-Host "  - Database (job history, materials, etc.)" -ForegroundColor Yellow
Write-Host "  - Downloaded files and thumbnails" -ForegroundColor Yellow
Write-Host "  - Printer configurations" -ForegroundColor Yellow
Write-Host "  - Application logs" -ForegroundColor Yellow
Write-Host ""
Write-Host "A backup will be created before deletion." -ForegroundColor Cyan
Write-Host ""

$confirmation = Read-Host "Are you sure you want to proceed? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host "Operation cancelled." -ForegroundColor Green
    exit 0
}

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScriptsDir = Split-Path -Parent $ScriptDir
$ProjectRoot = Split-Path -Parent $ScriptsDir
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

# Step 2: Backup existing data
Write-Host "Step 2: Creating backup of existing data..." -ForegroundColor Yellow
$BackupDir = Join-Path $ProjectRoot "backups"
$BackupTimestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$BackupPath = Join-Path $BackupDir "backup_$BackupTimestamp"

if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
}

$dataPath = Join-Path $DockerDir "data"
$configPath = Join-Path $DockerDir "config"

$backedUp = $false

if (Test-Path $dataPath) {
    Write-Host "Backing up data directory..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Force -Path $BackupPath | Out-Null
    Copy-Item -Path $dataPath -Destination (Join-Path $BackupPath "data") -Recurse
    $backedUp = $true
}

if (Test-Path $configPath) {
    Write-Host "Backing up config directory..." -ForegroundColor Cyan
    if (-not $backedUp) {
        New-Item -ItemType Directory -Force -Path $BackupPath | Out-Null
    }
    Copy-Item -Path $configPath -Destination (Join-Path $BackupPath "config") -Recurse
    $backedUp = $true
}

if ($backedUp) {
    Write-Host "[OK] Backup created at: $BackupPath" -ForegroundColor Green
} else {
    Write-Host "[SKIP] No existing data to backup" -ForegroundColor Cyan
}
Write-Host ""

# Step 3: Clean local data directories
Write-Host "Step 3: Wiping local data directories..." -ForegroundColor Yellow

if (Test-Path $dataPath) {
    Write-Host "Removing data directory..." -ForegroundColor Cyan
    Remove-Item -Path $dataPath -Recurse -Force
}

$printersConfig = Join-Path $configPath "printers.json"
if (Test-Path $printersConfig) {
    Write-Host "Removing printers.json..." -ForegroundColor Cyan
    Remove-Item -Path $printersConfig -Force
}

Write-Host "[OK] Local data wiped (backup preserved)" -ForegroundColor Green
Write-Host ""

# Step 4: Remove old images and clean up dangling images
Write-Host "Step 4: Removing old Docker images and cleaning up..." -ForegroundColor Yellow
docker rmi printernizer:latest 2>$null
$danglingImages = docker images -f "dangling=true" -q
if ($danglingImages) {
    Write-Host "Removing dangling images..." -ForegroundColor Cyan
    docker rmi $danglingImages 2>$null
}
Write-Host "[OK] Images cleaned up" -ForegroundColor Green
Write-Host ""

# Step 5: Build fresh image (no cache)
Write-Host "Step 5: Building fresh Docker image (no cache)..." -ForegroundColor Yellow
Write-Host "This may take several minutes..." -ForegroundColor Cyan
docker-compose build --no-cache
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Fresh image built successfully" -ForegroundColor Green
Write-Host ""

# Step 6: Start the new container
Write-Host "Step 6: Starting new container with fresh data..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to start container!" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Container started" -ForegroundColor Green
Write-Host ""

# Step 7: Wait for health check
Write-Host "Step 7: Waiting for application to be healthy..." -ForegroundColor Yellow
Write-Host "This may take up to 60 seconds..." -ForegroundColor Cyan
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
Write-Host "Clean rebuild complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Application URL:  http://localhost:8000"
Write-Host "Health Check:     http://localhost:8000/api/v1/health"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Configure your printers at: http://localhost:8000/settings.html"
Write-Host "  2. View backup at: $BackupPath"
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  View logs:         docker-compose logs -f"
Write-Host "  Stop container:    docker-compose stop"
Write-Host "  Restart:           docker-compose restart"
Write-Host "  Remove all:        docker-compose down"
Write-Host ""
