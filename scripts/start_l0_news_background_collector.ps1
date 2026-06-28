param(
    [switch]$UseFullUniverse,
    [int]$GdeltCooldownMinutes = 15,
    [int]$MarketauxBatchSize = 5,
    [int]$MaxRequestsPerCycle = 4,
    [int]$CycleSleepSeconds = 60,
    [int]$MaxRuntimeMinutes = 0,
    [string]$UniversePath = "data/raw/alpaca_active_us_equity_universe.csv",
    [string]$RawDir = "data/raw/l0_news",
    [string]$StatePath = "data/artifacts/l0_news_background_queue/collector_state.json",
    [string]$EventPath = "data/artifacts/l0_news_background_queue/collector_events.jsonl",
    [string]$ProgressPath = "data/artifacts/l0_news_background_queue/collector_progress.json",
    [string]$StopPath = "data/artifacts/l0_news_background_queue/STOP",
    [string]$LogPath = "logs/l0_news_background_collector.log"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (Test-Path -LiteralPath $StopPath) {
    Remove-Item -LiteralPath $StopPath -Force
}

$arguments = @(
    "scripts/run_l0_news_background_collector.py",
    "--gdelt-cooldown-minutes", [string]$GdeltCooldownMinutes,
    "--marketaux-batch-size", [string]$MarketauxBatchSize,
    "--max-requests-per-cycle", [string]$MaxRequestsPerCycle,
    "--cycle-sleep-seconds", [string]$CycleSleepSeconds,
    "--max-runtime-minutes", [string]$MaxRuntimeMinutes,
    "--universe-path", $UniversePath,
    "--raw-dir", $RawDir,
    "--state-path", $StatePath,
    "--event-path", $EventPath,
    "--progress-path", $ProgressPath,
    "--stop-path", $StopPath,
    "--log-path", $LogPath
)

if ($UseFullUniverse) {
    $arguments += "--use-full-universe"
}

$process = Start-Process -FilePath "python" -ArgumentList $arguments -WorkingDirectory $Root -WindowStyle Hidden -PassThru
$status = @{
    started_at = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    pid = $process.Id
    use_full_universe = [bool]$UseFullUniverse
    gdelt_cooldown_minutes = $GdeltCooldownMinutes
    marketaux_batch_size = $MarketauxBatchSize
    max_requests_per_cycle = $MaxRequestsPerCycle
    cycle_sleep_seconds = $CycleSleepSeconds
    max_runtime_minutes = $MaxRuntimeMinutes
    state_path = $StatePath
    event_path = $EventPath
    progress_path = $ProgressPath
    log_path = $LogPath
    stop_path = $StopPath
    diagnostic_only_flag = 1
    trade_authority_flag = 0
    broker_mutation_permitted_flag = 0
    real_capital_permitted_flag = 0
}

$statusPath = "data/artifacts/l0_news_background_queue/background_process.json"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $statusPath) | Out-Null
$status | ConvertTo-Json -Depth 4 | Set-Content -Path $statusPath -Encoding UTF8
Write-Output ("[L0_NEWS_BACKGROUND_STARTED] pid={0} status_path={1} progress_path={2}" -f $process.Id, $statusPath, $ProgressPath)
