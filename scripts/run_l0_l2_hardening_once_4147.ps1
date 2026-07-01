param(
    [string]$ProjectRoot = "",
    [string]$LogPath = "logs/task_4147_l0_l2_hardening_scheduler.log"
)

$ErrorActionPreference = "Stop"
if (-not $ProjectRoot) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
Set-Location $ProjectRoot

$logFullPath = Join-Path $ProjectRoot $LogPath
$logDir = Split-Path -Parent $logFullPath
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-TaskLog {
    param([string]$Message)
    $stamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    Add-Content -Path $logFullPath -Value "[$stamp] $Message" -Encoding UTF8
}

Write-TaskLog "TASK-4147 one-shot start"
python scripts/run_l0_l2_hardening_4147.py 2>&1 | Tee-Object -FilePath $logFullPath -Append
$runExit = $LASTEXITCODE
python scripts/validate_l0_l2_hardening_4147.py 2>&1 | Tee-Object -FilePath $logFullPath -Append
$validateExit = $LASTEXITCODE
if ($runExit -eq 0 -and $validateExit -eq 0) {
    python scripts/run_task4199_l3_l4_refresh_after_l0_l2.py 2>&1 | Tee-Object -FilePath $logFullPath -Append
    $refreshExit = $LASTEXITCODE
} else {
    $refreshExit = 0
}
Write-TaskLog "TASK-4147 one-shot end run_exit=$runExit validate_exit=$validateExit refresh_exit=$refreshExit"

if ($runExit -ne 0) {
    exit $runExit
}
if ($validateExit -ne 0) {
    exit $validateExit
}
exit $refreshExit
