param(
    [int]$IntervalSeconds = 900,
    [string]$StatusPath = "data/artifacts/task_4146_l0_l2_wide_packetization_handoff/continuous_handoff_loop_status.json",
    [string]$LogPath = "logs/task_4146_l0_l2_wide_handoff_loop.log",
    [string]$StopPath = "data/artifacts/task_4146_l0_l2_wide_packetization_handoff/STOP"
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $StatusPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $LogPath) | Out-Null

function Write-LoopStatus {
    param([hashtable]$Payload)
    $Payload.task_id = "TASK-4146"
    $Payload.pid = $PID
    $Payload.interval_seconds = $IntervalSeconds
    $Payload.diagnostic_only_flag = 1
    $Payload.trade_authority_flag = 0
    $Payload.broker_mutation_permitted_flag = 0
    $Payload.real_capital_permitted_flag = 0
    $Payload.updated_at = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    $Payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $StatusPath -Encoding UTF8
}

Write-LoopStatus @{
    status = "STARTED"
    started_at = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    last_run_result = ""
    last_validation_result = ""
}

while ($true) {
    if (Test-Path -LiteralPath $StopPath) {
        Write-LoopStatus @{
            status = "STOPPED_BY_STOP_FILE"
            stop_path = $StopPath
            last_run_result = ""
            last_validation_result = ""
        }
        break
    }
    $runOutput = & python scripts/run_l0_l2_wide_handoff_4146.py 2>&1
    $runExit = $LASTEXITCODE
    Add-Content -LiteralPath $LogPath -Value ("[{0}] RUN_EXIT={1}`n{2}" -f [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"), $runExit, ($runOutput -join "`n"))
    $validationOutput = & python scripts/validate_l0_l2_wide_handoff_4146.py 2>&1
    $validationExit = $LASTEXITCODE
    Add-Content -LiteralPath $LogPath -Value ("[{0}] VALIDATION_EXIT={1}`n{2}" -f [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"), $validationExit, ($validationOutput -join "`n"))
    Write-LoopStatus @{
        status = if ($runExit -eq 0 -and $validationExit -eq 0) { "RUNNING_PASS" } else { "RUNNING_WITH_FAILURE" }
        last_run_exit = $runExit
        last_validation_exit = $validationExit
        last_run_result = ($runOutput -join "`n")
        last_validation_result = ($validationOutput -join "`n")
    }
    Start-Sleep -Seconds ([Math]::Max($IntervalSeconds, 60))
}
