# Spark Careers — install the Windows scheduled task.
# Run this ONCE from PowerShell to register the weekly Friday 08:30 build.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File install-task.ps1
#
# To uninstall later: run uninstall-task.ps1

$ErrorActionPreference = "Stop"

$TaskName  = "SparkCareers\WeeklyContentBuild"
$XmlPath   = Join-Path $PSScriptRoot "SparkWeeklyContent.xml"

if (-not (Test-Path $XmlPath)) {
    Write-Error "Task XML not found at $XmlPath"
    exit 1
}

# Remove an existing task with the same name (idempotent re-install).
schtasks /Query /TN $TaskName 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Existing task found, removing first..." -ForegroundColor Yellow
    schtasks /Delete /TN $TaskName /F | Out-Null
}

# Register from the XML.
Write-Host "Registering task '$TaskName' from $XmlPath..." -ForegroundColor Cyan
schtasks /Create /TN $TaskName /XML "$XmlPath" /F

if ($LASTEXITCODE -ne 0) {
    Write-Error "schtasks /Create failed with exit code $LASTEXITCODE"
    exit 1
}

Write-Host ""
Write-Host "Task registered." -ForegroundColor Green
Write-Host "  Name:     $TaskName"
Write-Host "  Trigger:  Every Friday at 08:30 (America/Edmonton)"
Write-Host "  Action:   run_weekly.ps1 -> run_weekly.py"
Write-Host "  Logs:     <repo>/runs/wrapper-<timestamp>.log"
Write-Host ""
Write-Host "Next: trigger a test run on demand with --"
Write-Host "  schtasks /Run /TN '$TaskName'" -ForegroundColor Cyan
Write-Host ""
Write-Host "To uninstall later:"
Write-Host "  powershell -ExecutionPolicy Bypass -File uninstall-task.ps1" -ForegroundColor Cyan
