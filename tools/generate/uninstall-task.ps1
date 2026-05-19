# Spark Careers — remove the Windows scheduled task.
$ErrorActionPreference = "Stop"

$TaskName = "SparkCareers\WeeklyContentBuild"

schtasks /Query /TN $TaskName 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Task '$TaskName' is not registered. Nothing to do." -ForegroundColor Yellow
    exit 0
}

Write-Host "Removing task '$TaskName'..." -ForegroundColor Cyan
schtasks /Delete /TN $TaskName /F

if ($LASTEXITCODE -eq 0) {
    Write-Host "Task removed." -ForegroundColor Green
} else {
    Write-Error "schtasks /Delete failed with exit code $LASTEXITCODE"
    exit 1
}
