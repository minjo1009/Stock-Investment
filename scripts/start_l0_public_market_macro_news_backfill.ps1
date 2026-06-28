param(
    [string[]]$Sources = @(
        "guardian_open_platform",
        "ap_news_monthly_sitemap",
        "cnbc_public_rss",
        "wikimedia_current_events",
        "common_crawl_market_news_archive",
        "thehill_public_wp",
        "techcrunch_public_wp",
        "electrek_public_wp",
        "teslarati_public_wp",
        "semiengineering_public_wp",
        "bitcoinmagazine_public_wp",
        "nine_to_five_mac_public_wp",
        "nine_to_five_google_public_wp",
        "pv_magazine_usa_public_wp",
        "investors_public_wp",
        "investorplace_public_wp",
        "etftrends_public_wp",
        "housingwire_public_wp",
        "spacenews_public_wp",
        "carbonbrief_public_wp",
        "robotreport_public_wp"
    ),
    [int]$MaxItemsPerSource = 500,
    [int]$MaxFetchesPerSource = 24,
    [int]$CycleSleepSeconds = 300,
    [double]$RequestSleepSeconds = 1.0,
    [string]$BackfillStartDate = "2016-01-01",
    [string]$BackfillEndDate = "",
    [int]$GuardianPageSize = 50,
    [int]$MaxBytes = 25000000,
    [string]$RawDir = "data/raw/l0_public_market_macro_news_backfill",
    [string]$StatePath = "data/artifacts/l0_public_market_macro_news_backfill/collector_state.json",
    [string]$EventPath = "data/artifacts/l0_public_market_macro_news_backfill/collector_events.jsonl",
    [string]$ProgressPath = "data/artifacts/l0_public_market_macro_news_backfill/collector_progress.json",
    [string]$PlanPath = "data/artifacts/l0_public_market_macro_news_backfill/collection_plan.json",
    [string]$StopPath = "data/artifacts/l0_public_market_macro_news_backfill/STOP",
    [string]$LogPath = "logs/l0_public_market_macro_news_backfill.log",
    [string]$StatusPath = "data/artifacts/l0_public_market_macro_news_backfill/background_process.json"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (Test-Path -LiteralPath $StopPath) {
    Remove-Item -LiteralPath $StopPath -Force
}

$arguments = @(
    "scripts/run_l0_public_market_macro_news_collector.py",
    "--mode", "backfill",
    "--sources"
) + $Sources + @(
    "--max-items-per-source", [string]$MaxItemsPerSource,
    "--max-fetches-per-source", [string]$MaxFetchesPerSource,
    "--cycle-sleep-seconds", [string]$CycleSleepSeconds,
    "--request-sleep-seconds", [string]$RequestSleepSeconds,
    "--max-bytes", [string]$MaxBytes,
    "--backfill-start-date", $BackfillStartDate,
    "--guardian-page-size", [string]$GuardianPageSize,
    "--raw-dir", $RawDir,
    "--state-path", $StatePath,
    "--event-path", $EventPath,
    "--progress-path", $ProgressPath,
    "--plan-path", $PlanPath,
    "--stop-path", $StopPath,
    "--log-path", $LogPath
)

if ($BackfillEndDate -ne "") {
    $arguments += @("--backfill-end-date", $BackfillEndDate)
}

$process = Start-Process -FilePath "python" -ArgumentList $arguments -WorkingDirectory $Root -WindowStyle Hidden -PassThru
$status = @{
    started_at = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    pid = $process.Id
    sources = $Sources
    provider = "public_market_macro_news_feeds"
    mode = "historical_backfill"
    max_items_per_source = $MaxItemsPerSource
    max_fetches_per_source = $MaxFetchesPerSource
    cycle_sleep_seconds = $CycleSleepSeconds
    request_sleep_seconds = $RequestSleepSeconds
    max_bytes = $MaxBytes
    backfill_start_date = $BackfillStartDate
    backfill_end_date = $BackfillEndDate
    guardian_page_size = $GuardianPageSize
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
Write-Output ("[L0_PUBLIC_MARKET_MACRO_NEWS_BACKFILL_STARTED] pid={0} status_path={1} progress_path={2}" -f $process.Id, $StatusPath, $ProgressPath)
