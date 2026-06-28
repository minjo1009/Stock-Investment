param(
    [string[]]$Sources = @("prnewswire", "globenewswire", "businesswire"),
    [int]$MaxItemsPerSource = 50,
    [int]$MaxFetchesPerSource = 12,
    [int]$CycleSleepSeconds = 1800,
    [double]$RequestSleepSeconds = 1.0,
    [string]$UniversePath = "data/raw/alpaca_active_us_equity_universe.csv",
    [string]$RawDir = "data/raw/l0_public_newswire",
    [string]$StatePath = "data/artifacts/l0_public_newswire/collector_state.json",
    [string]$EventPath = "data/artifacts/l0_public_newswire/collector_events.jsonl",
    [string]$ProgressPath = "data/artifacts/l0_public_newswire/collector_progress.json",
    [string]$PlanPath = "data/artifacts/l0_public_newswire/collection_plan.json",
    [string]$StopPath = "data/artifacts/l0_public_newswire/STOP",
    [string]$LogPath = "logs/l0_public_newswire_collector.log",
    [string]$StatusPath = "data/artifacts/l0_public_newswire/background_process.json"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (Test-Path -LiteralPath $StopPath) {
    Remove-Item -LiteralPath $StopPath -Force
}

$arguments = @(
    "scripts/run_l0_public_newswire_collector.py",
    "--mode", "background",
    "--sources"
) + $Sources + @(
    "--universe-path", $UniversePath,
    "--max-items-per-source", [string]$MaxItemsPerSource,
    "--max-fetches-per-source", [string]$MaxFetchesPerSource,
    "--cycle-sleep-seconds", [string]$CycleSleepSeconds,
    "--request-sleep-seconds", [string]$RequestSleepSeconds,
    "--raw-dir", $RawDir,
    "--state-path", $StatePath,
    "--event-path", $EventPath,
    "--progress-path", $ProgressPath,
    "--plan-path", $PlanPath,
    "--stop-path", $StopPath,
    "--log-path", $LogPath
)

$process = Start-Process -FilePath "python" -ArgumentList $arguments -WorkingDirectory $Root -WindowStyle Hidden -PassThru
$status = @{
    started_at = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    pid = $process.Id
    sources = $Sources
    provider = "public_newswire_feeds"
    max_items_per_source = $MaxItemsPerSource
    max_fetches_per_source = $MaxFetchesPerSource
    cycle_sleep_seconds = $CycleSleepSeconds
    request_sleep_seconds = $RequestSleepSeconds
    universe_path = $UniversePath
    state_path = $StatePath
    event_path = $EventPath
    progress_path = $ProgressPath
    plan_path = $PlanPath
    stop_path = $StopPath
    log_path = $LogPath
    diagnostic_only_flag = 1
    trade_authority_flag = 0
    broker_mutation_permitted_flag = 0
    real_capital_permitted_flag = 0
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $StatusPath) | Out-Null
$status | ConvertTo-Json -Depth 5 | Set-Content -Path $StatusPath -Encoding UTF8
Write-Output ("[L0_PUBLIC_NEWSWIRE_STARTED] pid={0} status_path={1} progress_path={2}" -f $process.Id, $StatusPath, $ProgressPath)
