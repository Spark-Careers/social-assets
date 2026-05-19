# Spark Careers — install the Windows scheduled task.
# Run this ONCE from PowerShell to register the weekly Friday 08:30 build.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File install-task.ps1
#
# To uninstall later: run uninstall-task.ps1

$ErrorActionPreference = "Stop"

$TaskName = "WeeklyContentBuild"
$TaskPath = "\SparkCareers\"
$FullName = "$TaskPath$TaskName"
$XmlPath  = Join-Path $PSScriptRoot "SparkWeeklyContent.xml"

if (-not (Test-Path $XmlPath)) {
    Write-Error "Task XML not found at $XmlPath"
    exit 1
}

# Idempotent: remove existing task with the same name (if any)
$existing = Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Existing task found at $FullName, removing first..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -Confirm:$false
}

# Register from the XML
Write-Host "Registering task '$FullName' from $XmlPath..." -ForegroundColor Cyan
$xmlContent = Get-Content -Path $XmlPath -Raw

try {
    Register-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -Xml $xmlContent -Force | Out-Null
}
catch {
    Write-Error "Register-ScheduledTask failed: $($_.Exception.Message)"
    exit 1
}

# Verify
$verify = Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -ErrorAction SilentlyContinue
if (-not $verify) {
    Write-Error "Task registration appeared to succeed but the task is not visible. Open Task Scheduler GUI to investigate."
    exit 1
}

Write-Host ""
Write-Host "Task registered." -ForegroundColor Green
Write-Host "  Name:     $FullName"
Write-Host "  Trigger:  Every Friday at 08:30 (America/Edmonton)"
Write-Host "  Action:   run_weekly.ps1 -> run_weekly.py"
Write-Host "  Logs:     <repo>\runs\wrapper-<timestamp>.log"
Write-Host ""
Write-Host "Next: trigger a test run on demand with:"
Write-Host "  Start-ScheduledTask -TaskName '$TaskName' -TaskPath '$TaskPath'" -ForegroundColor Cyan
Write-Host ""
Write-Host "To uninstall later:"
Write-Host "  powershell -ExecutionPolicy Bypass -File uninstall-task.ps1" -ForegroundColor Cyan
