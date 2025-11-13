<#
.SYNOPSIS
    Monitoring and diagnostics script for Printernizer on Raspberry Pi.

.DESCRIPTION
    Provides real-time monitoring, logs, and system status.

.PARAMETER PiHost
    IP address or hostname of the Raspberry Pi

.PARAMETER PiUser
    SSH username (default: pi)

.PARAMETER Follow
    Follow logs in real-time

.PARAMETER SystemInfo
    Show system information

.EXAMPLE
    .\scripts\pi-deployment\monitor-pi.ps1 -PiHost 192.168.1.100
    .\scripts\pi-deployment\monitor-pi.ps1 -PiHost 192.168.1.100 -Follow
    .\scripts\pi-deployment\monitor-pi.ps1 -PiHost 192.168.1.100 -SystemInfo
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$PiHost,
    
    [string]$PiUser = "pi",
    [switch]$Follow,
    [switch]$SystemInfo
)

function Get-SystemStatus {
    $statusScript = @"
#!/bin/bash

echo "=== PRINTERNIZER STATUS ==="
cd /home/pi/printernizer
docker-compose ps

echo -e "\n=== CONTAINER STATS ==="
docker stats --no-stream printernizer 2>/dev/null || echo "Container not running"

echo -e "\n=== DISK USAGE ==="
df -h /home/pi/printernizer/data

echo -e "\n=== RASPBERRY PI STATUS ==="
echo "Temperature: `$(vcgencmd measure_temp | cut -d= -f2)"
echo "CPU: `$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - `$1"%"}')"
echo "Memory: `$(free -m | awk 'NR==2{printf "%.1f%%", `$3*100/`$2 }')"
echo "Uptime: `$(uptime -p)"

echo -e "\n=== RECENT LOGS (last 20 lines) ==="
cd /home/pi/printernizer
docker-compose logs --tail=20 2>/dev/null || echo "No logs available"
"@
    
    $statusScript | ssh "$PiUser@$PiHost" "bash -s"
}

function Show-SystemInfo {
    $infoScript = @"
#!/bin/bash

echo "=== SYSTEM INFORMATION ==="
echo "Hostname: `$(hostname)"
echo "OS: `$(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "Kernel: `$(uname -r)"
echo "Architecture: `$(uname -m)"

echo -e "\n=== HARDWARE ==="
echo "Model: `$(cat /proc/cpuinfo | grep 'Model' | cut -d: -f2 | xargs)"
echo "CPU: `$(nproc) cores"
echo "Memory: `$(free -h | awk '/^Mem:/ {print `$2}')"
echo "Temperature: `$(vcgencmd measure_temp | cut -d= -f2)"

echo -e "\n=== DOCKER VERSION ==="
docker --version
docker-compose --version

echo -e "\n=== PRINTERNIZER VERSION ==="
curl -s http://localhost:8000/api/v1/health 2>/dev/null | python3 -m json.tool || echo "Application not responding"

echo -e "\n=== NETWORK ==="
ip -4 addr show | grep inet | grep -v 127.0.0.1
"@
    
    $infoScript | ssh "$PiUser@$PiHost" "bash -s"
}

function Watch-Logs {
    Write-Host "Following Printernizer logs (Ctrl+C to stop)..." -ForegroundColor Cyan
    Write-Host ""
    ssh -t "$PiUser@$PiHost" "cd /home/pi/printernizer && docker-compose logs -f --tail=50"
}

# Main execution
Write-Host @"

╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         PRINTERNIZER MONITORING CONSOLE                  ║
║                                                           ║
║  Target: $PiUser@$PiHost                                 ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

if ($SystemInfo) {
    Show-SystemInfo
}
elseif ($Follow) {
    Watch-Logs
}
else {
    Get-SystemStatus
}
