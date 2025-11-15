# Kill process running on port 8000
# Usage: .\kill-port-8000.ps1

Write-Host "Finding process on port 8000..." -ForegroundColor Yellow

$connections = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue

if ($connections) {
    # Get unique PIDs to avoid killing the same process multiple times
    $uniquePids = $connections | Select-Object -ExpandProperty OwningProcess -Unique

    foreach ($processId in $uniquePids) {
        Write-Host "Found PID: $processId" -ForegroundColor Cyan

        try {
            Stop-Process -Id $processId -Force -ErrorAction Stop
            Write-Host "Process $processId killed successfully." -ForegroundColor Green
        } catch {
            Write-Host "Failed to kill process $processId. You may need administrator privileges." -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "No process found listening on port 8000." -ForegroundColor Green
}

exit 0
