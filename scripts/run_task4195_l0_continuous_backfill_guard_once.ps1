param(
    [string]$ProjectRoot = "",
    [string]$LogPath = "logs/task_4195_l0_continuous_backfill_guard_scheduler.log"
)

$ErrorActionPreference = "Stop"
if (-not $ProjectRoot) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
Set-Location -LiteralPath $ProjectRoot

$env:L0_BACKFILL_GUARD_TASK_ID = "TASK-4195"
$env:L0_BACKFILL_GUARD_SLUG = "task_4195_l0_continuous_backfill_runtime_governance"

$logFullPath = Join-Path $ProjectRoot $LogPath
$logDir = Split-Path -Parent $logFullPath
if (-not (Test-Path -LiteralPath $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-TaskLog {
    param([string]$Message)
    $stamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    Add-Content -Path $logFullPath -Value "[$stamp] $Message" -Encoding UTF8
}

Write-TaskLog "TASK-4195 continuous L0 backfill guard one-shot start"
python scripts/run_task4193_l0_overnight_backfill_supervisor.py 2>&1 | Tee-Object -FilePath $logFullPath -Append
$runExit = $LASTEXITCODE
Write-TaskLog "TASK-4195 continuous L0 backfill guard one-shot end run_exit=$runExit"
exit $runExit
