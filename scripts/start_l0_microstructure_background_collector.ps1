param(
    [string]$Feed = "iex",
    [string]$StartDate = "2016-01-01",
    [string]$EndDate = "",
    [int]$ChunkMinutes = 15,
    [int]$RequestsPerMinute = 60,
    [int]$MaxChunks = 0,
    [int]$MaxRuntimeMinutes = 0,
    [string]$UniversePath = "data/raw/alpaca_active_us_equity_universe.csv",
    [string]$RawDir = "data/raw/alpaca_historical_microstructure_backfill",
    [string]$StatePath = "data/artifacts/microstructure_backfill_queue_15m/collector_state.json",
    [string]$EventPath = "data/artifacts/microstructure_backfill_queue_15m/collector_events.jsonl",
    [string]$ProgressPath = "data/artifacts/microstructure_backfill_queue_15m/collector_progress.json",
    [string]$StopPath = "data/artifacts/microstructure_backfill_queue_15m/STOP",
    [string]$LogPath = "logs/l0_microstructure_background_collector_15m.log"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (Test-Path -LiteralPath $StopPath) {
    Remove-Item -LiteralPath $StopPath -Force
}

$arguments = @(
    "scripts/run_l0_microstructure_background_collector.py",
    "--feed", $Feed,
    "--start-date", $StartDate,
    "--chunk-minutes", [string]$ChunkMinutes,
    "--requests-per-minute", [string]$RequestsPerMinute,
    "--max-chunks", [string]$MaxChunks,
    "--max-runtime-minutes", [string]$MaxRuntimeMinutes,
    "--universe-path", $UniversePath,
    "--raw-dir", $RawDir,
    "--state-path", $StatePath,
    "--event-path", $EventPath,
    "--progress-path", $ProgressPath,
    "--stop-path", $StopPath,
    "--log-path", $LogPath
)

if ($EndDate -ne "") {
    $arguments += @("--end-date", $EndDate)
}

$process = Start-Process -FilePath "python" -ArgumentList $arguments -WorkingDirectory $Root -WindowStyle Hidden -PassThru
$status = @{
    started_at = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    pid = $process.Id
    feed = $Feed
    start_date = $StartDate
    end_date = $EndDate
    chunk_minutes = $ChunkMinutes
    requests_per_minute = $RequestsPerMinute
    max_chunks = $MaxChunks
    max_runtime_minutes = $MaxRuntimeMinutes
    state_path = $StatePath
    event_path = $EventPath
    progress_path = $ProgressPath
    log_path = $LogPath
    stop_path = $StopPath
    feature_builder_allowed_flag = 0
    broker_mutation_permitted_flag = 0
}

$statusPath = "data/artifacts/microstructure_backfill_queue_15m/background_process.json"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $statusPath) | Out-Null
$status | ConvertTo-Json -Depth 4 | Set-Content -Path $statusPath -Encoding UTF8
Write-Output ("[L0_MICROSTRUCTURE_BACKGROUND_STARTED] pid={0} status_path={1} progress_path={2}" -f $process.Id, $statusPath, $ProgressPath)
