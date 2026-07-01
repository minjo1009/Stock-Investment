param(
    [string[]]$Lanes = @("daily", "5m"),
    [string]$StartDate = "2016-01-01",
    [string]$EndDate = "",
    [int]$FiveMinChunkDays = 120,
    [int]$RequestsPerMinute = 120,
    [int]$RetryLimit = 3,
    [int]$MaxRequests = 0,
    [int]$MaxRuntimeMinutes = 0,
    [int]$UniverseOffset = 0,
    [int]$UniverseStride = 1,
    [string]$UniversePath = "data/raw/alpaca_active_us_equity_universe.csv",
    [string]$DailyRawDir = "data/raw/us_daily_alpaca_full_universe",
    [string]$DbPath = "trading.db",
    [string]$StatePath = "data/artifacts/l0_bar_full_backfill/collector_state.json",
    [string]$EventPath = "data/artifacts/l0_bar_full_backfill/collector_events.jsonl",
    [string]$ProgressPath = "data/artifacts/l0_bar_full_backfill/collector_progress.json",
    [string]$StopPath = "data/artifacts/l0_bar_full_backfill/STOP",
    [string]$PlanPath = "data/artifacts/l0_bar_full_backfill/full_backfill_plan.json",
    [string]$ContractPath = "data/artifacts/l0_bar_full_backfill/l1_l2_bar_contract.json",
    [string]$LogPath = "logs/l0_bar_full_backfill_collector.log",
    [string]$StatusPath = "data/artifacts/l0_bar_full_backfill/background_process.json"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (Test-Path -LiteralPath $StopPath) {
    Remove-Item -LiteralPath $StopPath -Force
}

$arguments = @(
    "scripts/run_l0_bar_full_backfill.py",
    "--mode", "historical_backfill",
    "--lanes"
) + $Lanes + @(
    "--start-date", $StartDate,
    "--five-min-chunk-days", [string]$FiveMinChunkDays,
    "--requests-per-minute", [string]$RequestsPerMinute,
    "--retry-limit", [string]$RetryLimit,
    "--max-requests", [string]$MaxRequests,
    "--max-runtime-minutes", [string]$MaxRuntimeMinutes,
    "--universe-offset", [string]$UniverseOffset,
    "--universe-stride", [string]$UniverseStride,
    "--universe-path", $UniversePath,
    "--daily-raw-dir", $DailyRawDir,
    "--db-path", $DbPath,
    "--state-path", $StatePath,
    "--event-path", $EventPath,
    "--progress-path", $ProgressPath,
    "--stop-path", $StopPath,
    "--plan-path", $PlanPath,
    "--contract-path", $ContractPath,
    "--log-path", $LogPath
)

if ($EndDate -ne "") {
    $arguments += @("--end-date", $EndDate)
}

$process = Start-Process -FilePath "python" -ArgumentList $arguments -WorkingDirectory $Root -WindowStyle Hidden -PassThru
$status = @{
    started_at = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    pid = $process.Id
    lanes = $Lanes
    start_date = $StartDate
    end_date = $EndDate
    five_min_chunk_days = $FiveMinChunkDays
    requests_per_minute = $RequestsPerMinute
    request_pacing_mode = "request_start_interval_cap"
    retry_limit = $RetryLimit
    max_requests = $MaxRequests
    max_runtime_minutes = $MaxRuntimeMinutes
    universe_offset = $UniverseOffset
    universe_stride = $UniverseStride
    universe_path = $UniversePath
    daily_raw_dir = $DailyRawDir
    db_path = $DbPath
    state_path = $StatePath
    event_path = $EventPath
    progress_path = $ProgressPath
    plan_path = $PlanPath
    contract_path = $ContractPath
    stop_path = $StopPath
    log_path = $LogPath
    diagnostic_only_flag = 1
    trade_authority_flag = 0
    broker_mutation_permitted_flag = 0
    real_capital_permitted_flag = 0
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $StatusPath) | Out-Null
$status | ConvertTo-Json -Depth 5 | Set-Content -Path $StatusPath -Encoding UTF8
Write-Output ("[L0_BAR_FULL_BACKFILL_STARTED] pid={0} status_path={1} progress_path={2}" -f $process.Id, $StatusPath, $ProgressPath)
