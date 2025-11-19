# Database Schema Fix Script
# Run this script to apply all missing tables and fixes to the database

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Printernizer Database Schema Fix" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if container is running
$containerRunning = docker ps --filter "name=printernizer" --format "{{.Names}}"
if (-not $containerRunning) {
    Write-Host "ERROR: printernizer container is not running!" -ForegroundColor Red
    Write-Host "Start the container first with: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Container is running" -ForegroundColor Green
Write-Host ""

# Phase 1: Critical Tables
Write-Host "Phase 1: Applying critical table migrations..." -ForegroundColor Yellow
Write-Host "  - configuration (system settings)" -ForegroundColor Gray
Write-Host "  - watch_folders (file monitoring)" -ForegroundColor Gray
Write-Host "  - download_history (download tracking)" -ForegroundColor Gray
Write-Host "  - printer_status_log (printer monitoring)" -ForegroundColor Gray
Write-Host "  - system_events (audit logging)" -ForegroundColor Gray

docker cp migrations/015_add_missing_core_tables.sql printernizer:/tmp/
docker exec printernizer sqlite3 //app//data//printernizer.db ".read /tmp/015_add_missing_core_tables.sql"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Phase 1 complete" -ForegroundColor Green
} else {
    Write-Host "✗ Phase 1 failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Phase 2: Optional Tables
Write-Host "Phase 2: Applying optional table migrations..." -ForegroundColor Yellow
Write-Host "  - collections (library organization)" -ForegroundColor Gray
Write-Host "  - collection_members (file grouping)" -ForegroundColor Gray
Write-Host "  - file_metadata (flexible metadata)" -ForegroundColor Gray

docker cp migrations/016_add_optional_tables.sql printernizer:/tmp/
docker exec printernizer sqlite3 //app//data//printernizer.db ".read /tmp/016_add_optional_tables.sql"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Phase 2 complete" -ForegroundColor Green
} else {
    Write-Host "✗ Phase 2 failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Phase 3: Performance Indexes
Write-Host "Phase 3: Adding performance indexes..." -ForegroundColor Yellow
Write-Host "  - library_files indexes" -ForegroundColor Gray

docker cp migrations/017_add_performance_indexes.sql printernizer:/tmp/
docker exec printernizer sqlite3 //app//data//printernizer.db ".read /tmp/017_add_performance_indexes.sql"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Phase 3 complete" -ForegroundColor Green
} else {
    Write-Host "✗ Phase 3 failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Phase 4: Triggers
Write-Host "Phase 4: Adding triggers..." -ForegroundColor Yellow
Write-Host "  - Automatic timestamp updates" -ForegroundColor Gray
Write-Host "  - Job status change logging" -ForegroundColor Gray

docker cp migrations/018_add_triggers.sql printernizer:/tmp/
docker exec printernizer sqlite3 //app//data//printernizer.db ".read /tmp/018_add_triggers.sql"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Phase 4 complete" -ForegroundColor Green
} else {
    Write-Host "✗ Phase 4 failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Verification
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Checking tables..." -ForegroundColor Yellow
$tables = docker exec printernizer sqlite3 //app//data//printernizer.db ".tables"
Write-Host $tables -ForegroundColor Gray
Write-Host ""

Write-Host "Checking configuration entries..." -ForegroundColor Yellow
$config = docker exec printernizer sqlite3 //app//data//printernizer.db "SELECT COUNT(*) FROM configuration;"
Write-Host "Configuration entries: $config" -ForegroundColor Gray
Write-Host ""

Write-Host "Running integrity check..." -ForegroundColor Yellow
$integrity = docker exec printernizer sqlite3 //app//data//printernizer.db "PRAGMA integrity_check;"
if ($integrity -eq "ok") {
    Write-Host "✓ Database integrity: OK" -ForegroundColor Green
} else {
    Write-Host "✗ Database integrity issues detected:" -ForegroundColor Red
    Write-Host $integrity -ForegroundColor Red
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Migration Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Restart the container: docker-compose restart printernizer" -ForegroundColor White
Write-Host "2. Check logs: docker logs -f printernizer" -ForegroundColor White
Write-Host "3. Review the validation report: DATABASE_SCHEMA_VALIDATION_REPORT.md" -ForegroundColor White
Write-Host ""
