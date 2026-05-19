# Spark Careers — weekly autonomous build wrapper
# Invoked by Windows Task Scheduler every Friday at 08:30 America/Edmonton.
#
# Locks Python + the repo path, executes run_weekly.py, and writes a transcript
# to runs/wrapper-<timestamp>.log so any Task Scheduler failure can be triaged.

$ErrorActionPreference = "Stop"

$RepoRoot   = "C:\Users\HP\Desktop\Personal Docs\Post Shell Projects\IdleSpark\Marketing\social-assets"
$Script     = Join-Path $RepoRoot "tools\generate\run_weekly.py"
$RunsDir    = Join-Path $RepoRoot "runs"
$Timestamp  = Get-Date -Format "yyyyMMdd-HHmmss"
$Logfile    = Join-Path $RunsDir "wrapper-$Timestamp.log"

# Find python: prefer the version on PATH; fall back to a known install.
$PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {
    $PythonExe = "C:\Users\HP\AppData\Local\Programs\Python\Python313\python.exe"
}

if (-not (Test-Path $RunsDir)) { New-Item -ItemType Directory -Path $RunsDir | Out-Null }

# Ensure CLAUDECODE is not set in this scope (it would block nested claude --print invocations).
Remove-Item Env:CLAUDECODE -ErrorAction SilentlyContinue

# Make sure git can find the user's identity; Task Scheduler runs in a stripped env.
$env:HOME      = $HOME
$env:USERPROFILE = $env:USERPROFILE

"=== Spark Careers wrapper started $(Get-Date -Format 'u') ===" | Out-File -FilePath $Logfile -Encoding utf8
"Python:    $PythonExe"        | Out-File -FilePath $Logfile -Encoding utf8 -Append
"Script:    $Script"           | Out-File -FilePath $Logfile -Encoding utf8 -Append
"Repo root: $RepoRoot"         | Out-File -FilePath $Logfile -Encoding utf8 -Append
""                              | Out-File -FilePath $Logfile -Encoding utf8 -Append

try {
    Set-Location $RepoRoot
    & $PythonExe $Script 2>&1 | Tee-Object -FilePath $Logfile -Append
    $exit = $LASTEXITCODE
    "" | Out-File -FilePath $Logfile -Encoding utf8 -Append
    "=== Wrapper finished $(Get-Date -Format 'u') exit=$exit ===" | Out-File -FilePath $Logfile -Encoding utf8 -Append
    exit $exit
}
catch {
    $err = $_.Exception.Message
    "ERROR: $err" | Out-File -FilePath $Logfile -Encoding utf8 -Append
    exit 1
}
