<#
.SYNOPSIS
    Automated deployment script for Printernizer to Raspberry Pi with rollback capability.

.DESCRIPTION
    Deploys Printernizer Docker container to Raspberry Pi 4 with:
    - Pre-deployment validation
    - Automatic backup before deployment
    - Health checks after deployment
    - Automatic rollback on failure
    - Deployment history tracking

.PARAMETER PiHost
    IP address or hostname of the Raspberry Pi

.PARAMETER PiUser
    SSH username (default: pi)

.PARAMETER RemotePath
    Installation path on Pi (default: /home/pi/printernizer)

.PARAMETER SkipBackup
    Skip pre-deployment backup (not recommended)

.PARAMETER Force
    Force deployment even if health checks fail

.EXAMPLE
    .\scripts\pi-deployment\deploy-to-pi.ps1 -PiHost 192.168.1.100
    .\scripts\pi-deployment\deploy-to-pi.ps1 -PiHost 192.168.1.100 -Force
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$PiHost,
    
    [string]$PiUser = "pi",
    [string]$RemotePath = "/home/pi/printernizer",
    [switch]$SkipBackup,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$DeploymentId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptRoot = Split-Path -Parent $PSCommandPath
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptRoot)
$LocalBackupPath = Join-Path $ProjectRoot "deployments\backup_$DeploymentId"

# Color output functions
function Write-Step { param($Message) Write-Host "`n▶ $Message" -ForegroundColor Cyan }
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }

# Deployment state tracking
$DeploymentState = @{
    PreDeploymentBackupCreated = $false
    FilesUploaded = $false
    ContainerStopped = $false
    ContainerStarted = $false
    HealthCheckPassed = $false
    RollbackNeeded = $false
}

function Test-SSHConnection {
    Write-Step "Testing SSH connection to $PiUser@$PiHost..."
    
    try {
        $result = ssh -o ConnectTimeout=5 -o BatchMode=yes "$PiUser@$PiHost" "echo 'Connection successful'" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "SSH connection established"
            return $true
        }
    }
    catch {
        Write-Error "SSH connection failed: $_"
        Write-Warning "Ensure SSH is enabled and you have key-based authentication configured"
        Write-Warning "Run: ssh-copy-id $PiUser@$PiHost"
        return $false
    }
    
    Write-Error "SSH connection failed. Exit code: $LASTEXITCODE"
    return $false
}

function Test-Prerequisites {
    Write-Step "Validating deployment prerequisites..."
    
    # Check local files exist
    $requiredFiles = @(
        "docker-compose.yml",
        "Dockerfile",
        "requirements.txt",
        "src/main.py",
        "frontend/index.html",
        "database_schema.sql"
    )
    
    foreach ($file in $requiredFiles) {
        $fullPath = Join-Path $ProjectRoot $file
        if (-not (Test-Path $fullPath)) {
            Write-Error "Required file missing: $file"
            return $false
        }
    }
    
    # Check remote Docker installation
    Write-Host "  Checking Docker on Pi..."
    $dockerCheck = ssh "$PiUser@$PiHost" "command -v docker && command -v docker-compose" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker or docker-compose not found on Pi"
        Write-Warning "Install Docker with: curl -fsSL https://get.docker.com | sh"
        return $false
    }
    
    # Check remote disk space (need at least 2GB free)
    Write-Host "  Checking disk space..."
    $diskSpace = ssh "$PiUser@$PiHost" "df -BG $RemotePath 2>/dev/null | tail -1 | awk '{print `$4}' | sed 's/G//' || echo 100" 2>&1
    if ([int]$diskSpace -lt 2) {
        Write-Warning "Low disk space on Pi: ${diskSpace}GB free"
        if (-not $Force) {
            Write-Error "Deployment cancelled. Use -Force to override."
            return $false
        }
    }
    
    Write-Success "Prerequisites validated"
    return $true
}

function Backup-RemoteDeployment {
    if ($SkipBackup) {
        Write-Warning "Skipping pre-deployment backup (not recommended)"
        return $true
    }
    
    Write-Step "Creating pre-deployment backup on Pi..."
    
    $backupScript = @"
#!/bin/bash
set -e

BACKUP_DIR="/home/pi/printernizer_backups"
BACKUP_FILE="backup_$DeploymentId.tar.gz"

mkdir -p "`$BACKUP_DIR"

# Check if deployment exists
if [ ! -d "$RemotePath" ]; then
    echo "No existing deployment to backup"
    exit 0
fi

cd "$RemotePath"

# Stop container gracefully
if docker-compose ps 2>/dev/null | grep -q "Up"; then
    echo "Stopping container..."
    docker-compose stop
    sleep 2
fi

# Create backup
echo "Creating backup..."
tar -czf "`$BACKUP_DIR/`$BACKUP_FILE" \
    --exclude='*.log' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    data/ config/ docker-compose.yml .env 2>/dev/null || true

# Restart container if it was running
if docker-compose ps -a 2>/dev/null | grep -q "printernizer"; then
    echo "Restarting container..."
    docker-compose start
fi

echo "Backup created: `$BACKUP_DIR/`$BACKUP_FILE"

# Keep only last 10 backups
ls -t "`$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm

echo "BACKUP_SUCCESS"
"@
    
    try {
        $result = $backupScript | ssh "$PiUser@$PiHost" "bash -s" 2>&1
        if ($result -match "BACKUP_SUCCESS") {
            Write-Success "Backup created: backup_$DeploymentId.tar.gz"
            $DeploymentState.PreDeploymentBackupCreated = $true
            
            # Download backup locally for extra safety
            New-Item -ItemType Directory -Force -Path $LocalBackupPath | Out-Null
            scp "$PiUser@$($PiHost):/home/pi/printernizer_backups/backup_$DeploymentId.tar.gz" "$LocalBackupPath/" 2>&1 | Out-Null
            Write-Success "Local backup copy saved to: $LocalBackupPath"
            
            return $true
        }
    }
    catch {
        Write-Error "Backup failed: $_"
        if (-not $Force) {
            Write-Error "Deployment cancelled. Use -Force to skip backup."
            return $false
        }
        Write-Warning "Continuing without backup due to -Force flag"
    }
    
    return $Force
}

function Deploy-Files {
    Write-Step "Deploying files to Pi..."
    
    # Create temporary deployment package
    $tempDir = Join-Path $ProjectRoot "deployments\deploy_$DeploymentId"
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
    
    try {
        # Copy files to temp directory
        Write-Host "  Preparing deployment package..."
        
        # Core files
        Copy-Item (Join-Path $ProjectRoot "docker-compose.yml") "$tempDir/" -Force
        Copy-Item (Join-Path $ProjectRoot "Dockerfile") "$tempDir/" -Force
        Copy-Item (Join-Path $ProjectRoot "requirements.txt") "$tempDir/" -Force
        Copy-Item (Join-Path $ProjectRoot "database_schema.sql") "$tempDir/" -Force
        
        # Source code
        Copy-Item (Join-Path $ProjectRoot "src") "$tempDir/" -Recurse -Force
        Copy-Item (Join-Path $ProjectRoot "frontend") "$tempDir/" -Recurse -Force
        
        # Config (if exists)
        $configPath = Join-Path $ProjectRoot "config"
        if (Test-Path $configPath) {
            Copy-Item $configPath "$tempDir/" -Recurse -Force
        }
        
        # Migrations
        $migrationsPath = Join-Path $ProjectRoot "migrations"
        if (Test-Path $migrationsPath) {
            Copy-Item $migrationsPath "$tempDir/" -Recurse -Force
        }
        
        # Environment file template
        $envExample = Join-Path $ProjectRoot ".env.example"
        if (Test-Path $envExample) {
            Copy-Item $envExample "$tempDir/.env" -Force
        }
        
        # Create deployment metadata
        @{
            deployment_id = $DeploymentId
            deployed_at = (Get-Date).ToString("o")
            deployed_by = $env:USERNAME
            git_commit = (git -C $ProjectRoot rev-parse HEAD 2>$null)
            git_branch = (git -C $ProjectRoot rev-parse --abbrev-ref HEAD 2>$null)
        } | ConvertTo-Json | Out-File "$tempDir/deployment.json"
        
        # Create remote directory structure
        Write-Host "  Creating remote directories..."
        ssh "$PiUser@$PiHost" "mkdir -p $RemotePath/{data/{database,thumbnails,files},logs,config}" 2>&1 | Out-Null
        
        # Upload files
        Write-Host "  Uploading files (this may take a moment)..."
        scp -r -C -q "$tempDir/*" "$PiUser@$($PiHost):$RemotePath/" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Files deployed successfully"
            $DeploymentState.FilesUploaded = $true
            return $true
        }
        else {
            Write-Error "File upload failed with exit code: $LASTEXITCODE"
            return $false
        }
    }
    catch {
        Write-Error "Deployment failed: $_"
        return $false
    }
    finally {
        # Cleanup temp directory
        Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Start-RemoteContainer {
    Write-Step "Starting Docker container on Pi..."
    
    $startScript = @"
#!/bin/bash
set -e

cd "$RemotePath"

# Pull latest base images
echo "Pulling Docker images..."
docker-compose pull

# Stop existing container
if docker-compose ps 2>/dev/null | grep -q "Up"; then
    echo "Stopping existing container..."
    docker-compose down
    sleep 2
fi

# Build and start new container
echo "Building and starting container..."
docker-compose up -d --build

# Wait for container to be running
echo "Waiting for container to start..."
for i in {1..30}; do
    if docker-compose ps 2>/dev/null | grep -q "Up"; then
        echo "Container is running"
        exit 0
    fi
    sleep 1
done

echo "ERROR: Container failed to start"
docker-compose logs --tail=50
exit 1
"@
    
    try {
        $result = $startScript | ssh "$PiUser@$PiHost" "bash -s" 2>&1
        Write-Host $result
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Container started successfully"
            $DeploymentState.ContainerStarted = $true
            return $true
        }
        else {
            Write-Error "Container start failed"
            return $false
        }
    }
    catch {
        Write-Error "Failed to start container: $_"
        return $false
    }
}

function Test-Deployment {
    Write-Step "Running health checks..."
    
    # Wait for application to be ready
    Write-Host "  Waiting for application startup (30s timeout)..."
    Start-Sleep -Seconds 5
    
    for ($i = 1; $i -le 25; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://$PiHost`:8000/api/v1/health" -TimeoutSec 2 -UseBasicParsing
            $health = $response.Content | ConvertFrom-Json
            
            if ($health.status -eq "healthy") {
                Write-Success "Health check passed"
                Write-Host "  Version: $($health.version)"
                Write-Host "  Environment: $($health.environment)"
                Write-Host "  Uptime: $($health.uptime_seconds)s"
                $DeploymentState.HealthCheckPassed = $true
                return $true
            }
        }
        catch {
            # Still waiting...
        }
        
        Start-Sleep -Seconds 1
        Write-Host "." -NoNewline
    }
    
    Write-Host ""
    Write-Error "Health check failed - application not responding"
    
    # Get container logs for debugging
    Write-Warning "Fetching container logs..."
    $logs = ssh "$PiUser@$PiHost" "cd $RemotePath && docker-compose logs --tail=50" 2>&1
    Write-Host $logs
    
    return $false
}

function Invoke-Rollback {
    Write-Step "Rolling back to previous version..."
    
    if (-not $DeploymentState.PreDeploymentBackupCreated) {
        Write-Error "No backup available for rollback"
        return $false
    }
    
    $rollbackScript = @"
#!/bin/bash
set -e

BACKUP_FILE="/home/pi/printernizer_backups/backup_$DeploymentId.tar.gz"

if [ ! -f "`$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: `$BACKUP_FILE"
    exit 1
fi

cd "$RemotePath"

# Stop current container
echo "Stopping current container..."
docker-compose down

# Restore backup
echo "Restoring backup..."
tar -xzf "`$BACKUP_FILE" -C "$RemotePath"

# Start restored container
echo "Starting restored container..."
docker-compose up -d

echo "ROLLBACK_SUCCESS"
"@
    
    try {
        $result = $rollbackScript | ssh "$PiUser@$PiHost" "bash -s" 2>&1
        if ($result -match "ROLLBACK_SUCCESS") {
            Write-Success "Rollback completed successfully"
            
            # Verify rolled back version
            Start-Sleep -Seconds 5
            try {
                $response = Invoke-WebRequest -Uri "http://$PiHost`:8000/api/v1/health" -TimeoutSec 5 -UseBasicParsing
                $health = $response.Content | ConvertFrom-Json
                Write-Success "Rolled back to version: $($health.version)"
            }
            catch {
                Write-Warning "Rolled back but health check not responding yet"
            }
            
            return $true
        }
    }
    catch {
        Write-Error "Rollback failed: $_"
        Write-Error "Manual intervention required!"
        Write-Warning "To manually restore, SSH to Pi and run:"
        Write-Warning "  cd /home/pi/printernizer_backups"
        Write-Warning "  tar -xzf backup_$DeploymentId.tar.gz -C $RemotePath"
        Write-Warning "  cd $RemotePath && docker-compose up -d"
        return $false
    }
    
    return $false
}

function Save-DeploymentHistory {
    param($Success, $Duration)
    
    $historyFile = Join-Path $ProjectRoot "deployments\history.json"
    $history = @()
    
    if (Test-Path $historyFile) {
        $history = Get-Content $historyFile | ConvertFrom-Json
    }
    
    $history += @{
        deployment_id = $DeploymentId
        timestamp = (Get-Date).ToString("o")
        target = "$PiUser@$PiHost"
        success = $Success
        duration_seconds = $Duration
        rolled_back = $DeploymentState.RollbackNeeded
        git_commit = (git -C $ProjectRoot rev-parse HEAD 2>$null)
        deployed_by = $env:USERNAME
    }
    
    # Keep last 50 deployments
    if ($history.Count -gt 50) {
        $history = $history[-50..-1]
    }
    
    New-Item -ItemType Directory -Force -Path (Join-Path $ProjectRoot "deployments") | Out-Null
    $history | ConvertTo-Json -Depth 5 | Out-File $historyFile
}

# ============================================================================
# MAIN DEPLOYMENT WORKFLOW
# ============================================================================

Write-Host @"

╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║       PRINTERNIZER RASPBERRY PI DEPLOYMENT v1.0          ║
║                                                           ║
║  Target: $PiUser@$PiHost                                 ║
║  Deployment ID: $DeploymentId                            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

$startTime = Get-Date

try {
    # Phase 1: Pre-deployment validation
    if (-not (Test-SSHConnection)) { exit 1 }
    if (-not (Test-Prerequisites)) { exit 1 }
    
    # Phase 2: Backup current deployment
    if (-not (Backup-RemoteDeployment)) { exit 1 }
    
    # Phase 3: Deploy new version
    if (-not (Deploy-Files)) {
        $DeploymentState.RollbackNeeded = $true
        throw "File deployment failed"
    }
    
    # Phase 4: Start container
    if (-not (Start-RemoteContainer)) {
        $DeploymentState.RollbackNeeded = $true
        throw "Container start failed"
    }
    
    # Phase 5: Health checks
    if (-not (Test-Deployment)) {
        if (-not $Force) {
            $DeploymentState.RollbackNeeded = $true
            throw "Health check failed"
        }
        Write-Warning "Health check failed but continuing due to -Force flag"
    }
    
    # Success!
    $duration = ((Get-Date) - $startTime).TotalSeconds
    
    Write-Host @"

╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║               ✅ DEPLOYMENT SUCCESSFUL!                   ║
║                                                           ║
║  Printernizer is now running on your Raspberry Pi        ║
║                                                           ║
║  🌐 Web Interface: http://$PiHost`:8000                  ║
║  📊 API Health: http://$PiHost`:8000/api/v1/health      ║
║  📝 View Logs: ssh $PiUser@$PiHost                       ║
║                'cd $RemotePath && docker-compose logs'    ║
║                                                           ║
║  Duration: $([math]::Round($duration, 1))s               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green
    
    Save-DeploymentHistory -Success $true -Duration $duration
    
    # Display next steps
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Open http://$PiHost`:8000 in your browser"
    Write-Host "  2. Add your printers in the settings"
    Write-Host "  3. Monitor logs: ssh $PiUser@$PiHost 'cd $RemotePath && docker-compose logs -f'"
    Write-Host ""
    Write-Host "Backup location: /home/pi/printernizer_backups/backup_$DeploymentId.tar.gz" -ForegroundColor Cyan
    
    exit 0
}
catch {
    $duration = ((Get-Date) - $startTime).TotalSeconds
    
    Write-Host @"

╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║               ❌ DEPLOYMENT FAILED                        ║
║                                                           ║
║  Error: $($_.Exception.Message)
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Red
    
    Save-DeploymentHistory -Success $false -Duration $duration
    
    # Automatic rollback if backup exists
    if ($DeploymentState.RollbackNeeded -and $DeploymentState.PreDeploymentBackupCreated) {
        Write-Warning "Attempting automatic rollback..."
        if (Invoke-Rollback) {
            Write-Success "Successfully rolled back to previous version"
            exit 2
        }
        else {
            Write-Error "Rollback failed - manual intervention required"
            exit 3
        }
    }
    
    exit 1
}
