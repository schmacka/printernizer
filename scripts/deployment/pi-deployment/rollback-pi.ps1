<#
.SYNOPSIS
    Manual rollback script for Printernizer on Raspberry Pi.

.DESCRIPTION
    Allows manual rollback to any previous backup.

.PARAMETER PiHost
    IP address or hostname of the Raspberry Pi

.PARAMETER PiUser
    SSH username (default: pi)

.PARAMETER BackupId
    Backup ID to restore (YYYYMMDD_HHMMSS format). If not specified, shows list.

.EXAMPLE
    .\scripts\pi-deployment\rollback-pi.ps1 -PiHost 192.168.1.100
    .\scripts\pi-deployment\rollback-pi.ps1 -PiHost 192.168.1.100 -BackupId 20241113_143022
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$PiHost,
    
    [string]$PiUser = "pi",
    [string]$BackupId
)

function Write-ColorOutput {
    param($Message, $Color)
    Write-Host $Message -ForegroundColor $Color
}

function Get-AvailableBackups {
    Write-ColorOutput "Fetching available backups from Pi..." Cyan
    
    $listScript = @"
#!/bin/bash
cd /home/pi/printernizer_backups 2>/dev/null || exit 1
ls -t backup_*.tar.gz 2>/dev/null | while read file; do
    size=`$(du -h "`$file" | cut -f1)
    date=`$(stat -c %y "`$file" | cut -d' ' -f1,2 | cut -d'.' -f1)
    echo "`${file}|`${size}|`${date}"
done
"@
    
    $backups = $listScript | ssh "$PiUser@$PiHost" "bash -s" 2>&1
    
    if ($LASTEXITCODE -ne 0 -or -not $backups) {
        Write-ColorOutput "No backups found on Pi" Red
        return @()
    }
    
    $backupList = @()
    foreach ($line in $backups) {
        if ($line -match "backup_(\d{8}_\d{6})\.tar\.gz\|(.+)\|(.+)") {
            $backupList += @{
                Id = $matches[1]
                Size = $matches[2]
                Date = $matches[3]
                FileName = "backup_$($matches[1]).tar.gz"
            }
        }
    }
    
    return $backupList
}

function Show-BackupMenu {
    param($Backups)
    
    Write-Host "`nAvailable Backups:" -ForegroundColor Cyan
    Write-Host ("="*70)
    Write-Host ("{0,-3} {1,-20} {2,-10} {3,-25}" -f "#", "Backup ID", "Size", "Date")
    Write-Host ("="*70)
    
    for ($i = 0; $i -lt $Backups.Count; $i++) {
        $backup = $Backups[$i]
        Write-Host ("{0,-3} {1,-20} {2,-10} {3,-25}" -f ($i+1), $backup.Id, $backup.Size, $backup.Date)
    }
    
    Write-Host ("="*70)
    Write-Host ""
}

function Invoke-RestoreBackup {
    param($BackupFileName)
    
    Write-ColorOutput "Restoring backup: $BackupFileName" Yellow
    
    $restoreScript = @"
#!/bin/bash
set -e

BACKUP_FILE="/home/pi/printernizer_backups/$BackupFileName"
REMOTE_PATH="/home/pi/printernizer"

if [ ! -f "`$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found"
    exit 1
fi

cd "`$REMOTE_PATH"

# Stop container
echo "Stopping container..."
docker-compose down 2>/dev/null || true

# Create pre-rollback backup
echo "Creating pre-rollback backup..."
PRE_ROLLBACK="pre_rollback_`$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf "/home/pi/printernizer_backups/`$PRE_ROLLBACK" \
    --exclude='*.log' \
    data/ config/ docker-compose.yml .env 2>/dev/null || true

# Restore backup
echo "Restoring files..."
tar -xzf "`$BACKUP_FILE" -C "`$REMOTE_PATH"

# Start container
echo "Starting container..."
docker-compose up -d

# Wait and check health
sleep 5
if docker-compose ps | grep -q "Up"; then
    echo "RESTORE_SUCCESS"
    exit 0
else
    echo "ERROR: Container failed to start"
    docker-compose logs --tail=30
    exit 1
fi
"@
    
    $result = $restoreScript | ssh "$PiUser@$PiHost" "bash -s" 2>&1
    Write-Host $result
    
    if ($result -match "RESTORE_SUCCESS") {
        Write-ColorOutput "`n✅ Rollback completed successfully!" Green
        
        # Verify health
        Start-Sleep -Seconds 3
        try {
            $response = Invoke-WebRequest -Uri "http://$PiHost`:8000/api/v1/health" -TimeoutSec 5 -UseBasicParsing
            $health = $response.Content | ConvertFrom-Json
            Write-ColorOutput "Restored version: $($health.version)" Cyan
            Write-ColorOutput "Access at: http://$PiHost`:8000" Cyan
        }
        catch {
            Write-ColorOutput "Application starting, may take a moment to respond" Yellow
        }
        
        return $true
    }
    
    Write-ColorOutput "❌ Rollback failed" Red
    return $false
}

# Main execution
Write-Host @"

╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         PRINTERNIZER ROLLBACK UTILITY                    ║
║                                                           ║
║  Target: $PiUser@$PiHost                                 ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Yellow

$backups = Get-AvailableBackups

if ($backups.Count -eq 0) {
    Write-ColorOutput "No backups available for rollback" Red
    exit 1
}

if (-not $BackupId) {
    Show-BackupMenu -Backups $backups
    
    $selection = Read-Host "Select backup number to restore (or 'q' to quit)"
    
    if ($selection -eq 'q') {
        Write-ColorOutput "Rollback cancelled" Yellow
        exit 0
    }
    
    $index = [int]$selection - 1
    if ($index -lt 0 -or $index -ge $backups.Count) {
        Write-ColorOutput "Invalid selection" Red
        exit 1
    }
    
    $selectedBackup = $backups[$index]
}
else {
    $selectedBackup = $backups | Where-Object { $_.Id -eq $BackupId }
    if (-not $selectedBackup) {
        Write-ColorOutput "Backup not found: $BackupId" Red
        Show-BackupMenu -Backups $backups
        exit 1
    }
}

Write-Host "`nSelected backup:" -ForegroundColor Cyan
Write-Host "  ID: $($selectedBackup.Id)"
Write-Host "  Date: $($selectedBackup.Date)"
Write-Host "  Size: $($selectedBackup.Size)"

$confirm = Read-Host "`nProceed with rollback? This will stop the current deployment (y/N)"
if ($confirm -ne 'y') {
    Write-ColorOutput "Rollback cancelled" Yellow
    exit 0
}

if (Invoke-RestoreBackup -BackupFileName $selectedBackup.FileName) {
    exit 0
}
else {
    exit 1
}
