param(
    [string[]]$Sources = @("official", "gdelt", "marketaux"),
    [string]$StartDate = "2016-01-01",
    [string]$EndDate = "",
    [string]$GdeltStartTs = "20160101000000",
    [int]$GdeltRequestsPerMinute = 12,
    [int]$MarketauxDailyCap = 95,
    [int]$MarketauxBatchSize = 5,
    [int]$MarketauxWindowDays = 366,
    [int]$MarketauxLimit = 3,
    [int]$OfficialRefreshHours = 24,
    [int]$MaxRequests = 0,
    [int]$MaxRuntimeMinutes = 0,
    [string]$UniversePath = "data/raw/alpaca_active_us_equity_universe.csv",
    [string]$RawDir = "data/raw/l0_news_full_backfill",
    [string]$StatePath = "data/artifacts/l0_news_full_backfill/collector_state.json",
    [string]$EventPath = "data/artifacts/l0_news_full_backfill/collector_events.jsonl",
    [string]$ProgressPath = "data/artifacts/l0_news_full_backfill/collector_progress.json",
    [string]$StopPath = "data/artifacts/l0_news_full_backfill/STOP",
    [string]$PlanPath = "data/artifacts/l0_news_full_backfill/full_backfill_plan.json",
    [string]$OfficialBlockersPath = "data/artifacts/l0_news_full_backfill/official_endpoint_missing_universe.csv",
    [string]$LogPath = "logs/l0_news_full_backfill_collector.log"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (Test-Path -LiteralPath $StopPath) {
    Remove-Item -LiteralPath $StopPath -Force
}

$arguments = @(
    "scripts/run_l0_news_full_backfill.py",
    "--mode", "historical_backfill",
    "--sources"
) + $Sources + @(
    "--start-date", $StartDate,
    "--gdelt-start-ts", $GdeltStartTs,
    "--gdelt-requests-per-minute", [string]$GdeltRequestsPerMinute,
    "--marketaux-daily-cap", [string]$MarketauxDailyCap,
    "--marketaux-batch-size", [string]$MarketauxBatchSize,
    "--marketaux-window-days", [string]$MarketauxWindowDays,
    "--marketaux-limit", [string]$MarketauxLimit,
    "--official-refresh-hours", [string]$OfficialRefreshHours,
    "--max-requests", [string]$MaxRequests,
    "--max-runtime-minutes", [string]$MaxRuntimeMinutes,
    "--universe-path", $UniversePath,
    "--raw-dir", $RawDir,
    "--state-path", $StatePath,
    "--event-path", $EventPath,
    "--progress-path", $ProgressPath,
    "--stop-path", $StopPath,
    "--plan-path", $PlanPath,
    "--official-blockers-path", $OfficialBlockersPath,
    "--log-path", $LogPath
)

if ($EndDate -ne "") {
    $arguments += @("--end-date", $EndDate)
}

$process = Start-Process -FilePath "python" -ArgumentList $arguments -WorkingDirectory $Root -WindowStyle Hidden -PassThru
$status = @{
    started_at = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    pid = $process.Id
    sources = $Sources
    start_date = $StartDate
    end_date = $EndDate
    gdelt_start_ts = $GdeltStartTs
    gdelt_requests_per_minute = $GdeltRequestsPerMinute
    marketaux_daily_cap = $MarketauxDailyCap
    marketaux_batch_size = $MarketauxBatchSize
    marketaux_window_days = $MarketauxWindowDays
    marketaux_limit = $MarketauxLimit
    official_refresh_hours = $OfficialRefreshHours
    max_requests = $MaxRequests
    max_runtime_minutes = $MaxRuntimeMinutes
    state_path = $StatePath
    event_path = $EventPath
    progress_path = $ProgressPath
    plan_path = $PlanPath
    official_blockers_path = $OfficialBlockersPath
    stop_path = $StopPath
    log_path = $LogPath
    diagnostic_only_flag = 1
    trade_authority_flag = 0
    broker_mutation_permitted_flag = 0
    real_capital_permitted_flag = 0
}

$statusPath = "data/artifacts/l0_news_full_backfill/background_process.json"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $statusPath) | Out-Null
$status | ConvertTo-Json -Depth 5 | Set-Content -Path $statusPath -Encoding UTF8
Write-Output ("[L0_NEWS_FULL_BACKFILL_STARTED] pid={0} status_path={1} progress_path={2}" -f $process.Id, $statusPath, $ProgressPath)
