param(
    [int]$IntervalSeconds = 900,
    [string]$StatusPath = "data/artifacts/task_4146_l0_l2_wide_packetization_handoff/continuous_handoff_loop_status.json",
    [string]$LogPath = "logs/task_4146_l0_l2_wide_handoff_loop.log",
    [string]$StopPath = "data/artifacts/task_4146_l0_l2_wide_packetization_handoff/STOP"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (Test-Path -LiteralPath $StopPath) {
    Remove-Item -LiteralPath $StopPath -Force
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $StatusPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $LogPath) | Out-Null

$arguments = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "scripts/run_l0_l2_wide_handoff_loop_4146.ps1",
    "-IntervalSeconds", [string]$IntervalSeconds,
    "-StatusPath", $StatusPath,
    "-LogPath", $LogPath,
    "-StopPath", $StopPath
)

$process = Start-Process -FilePath "powershell" -ArgumentList $arguments -WorkingDirectory $Root -WindowStyle Hidden -PassThru
$status = @{
    task_id = "TASK-4146"
    status = "START_REQUESTED"
    pid = $process.Id
    interval_seconds = $IntervalSeconds
    status_path = $StatusPath
    log_path = $LogPath
    stop_path = $StopPath
    diagnostic_only_flag = 1
    trade_authority_flag = 0
    broker_mutation_permitted_flag = 0
    real_capital_permitted_flag = 0
    started_at = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
}
$status | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $StatusPath -Encoding UTF8
Write-Output ("[TASK_4146_WIDE_HANDOFF_LOOP_STARTED] pid={0} status_path={1}" -f $process.Id, $StatusPath)
