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

# Resolve the Claude OAuth token for headless `claude --print` invocations.
# Task Scheduler often strips user-scope env vars even with InteractiveToken,
# so we re-read it from the user registry hive directly.
$OauthToken = [System.Environment]::GetEnvironmentVariable("CLAUDE_CODE_OAUTH_TOKEN", "User")
if (-not $OauthToken) {
    $OauthToken = $env:CLAUDE_CODE_OAUTH_TOKEN
}
if (-not $OauthToken) {
    "ERROR: CLAUDE_CODE_OAUTH_TOKEN is not set." | Out-File -FilePath $Logfile -Encoding utf8 -Append
    "Run 'claude setup-token' once interactively, then set the result as a User env var:" | Out-File -FilePath $Logfile -Encoding utf8 -Append
    "  [System.Environment]::SetEnvironmentVariable('CLAUDE_CODE_OAUTH_TOKEN', '<token>', 'User')" | Out-File -FilePath $Logfile -Encoding utf8 -Append
    exit 2
}
$env:CLAUDE_CODE_OAUTH_TOKEN = $OauthToken
"OAuth:     CLAUDE_CODE_OAUTH_TOKEN is set (length $($OauthToken.Length))" | Out-File -FilePath $Logfile -Encoding utf8 -Append
""                              | Out-File -FilePath $Logfile -Encoding utf8 -Append

try {
    Set-Location $RepoRoot
    # Force Python to emit UTF-8 so the log file is readable
    $env:PYTHONIOENCODING = "utf-8"
    $env:PYTHONUTF8 = "1"
    & $PythonExe $Script 2>&1 | ForEach-Object { $_.ToString() } | Tee-Object -FilePath $Logfile -Append -Encoding utf8
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
