# Spark Careers — remove the Windows scheduled task.
$ErrorActionPreference = "Stop"

$TaskName = "WeeklyContentBuild"
$TaskPath = "\SparkCareers\"
$FullName = "$TaskPath$TaskName"

$existing = Get-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -ErrorAction SilentlyContinue
if (-not $existing) {
    Write-Host "Task '$FullName' is not registered. Nothing to do." -ForegroundColor Yellow
    exit 0
}

Write-Host "Removing task '$FullName'..." -ForegroundColor Cyan
Unregister-ScheduledTask -TaskName $TaskName -TaskPath $TaskPath -Confirm:$false
Write-Host "Task removed." -ForegroundColor Green
