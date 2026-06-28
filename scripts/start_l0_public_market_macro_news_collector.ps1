param(
    [string[]]$Sources = @(
        "cnbc_public_rss",
        "npr_public_radio_rss",
        "pbs_newshour_rss",
        "abc_news_public_rss",
        "cbs_news_public_rss",
        "census_public_rss",
        "yahoo_finance_public_rss",
        "nytimes_public_rss",
        "fox_business_public_rss",
        "investing_public_rss",
        "nasdaq_trader_notices",
        "bbc_public_rss",
        "ft_public_rss",
        "marketwatch_public_rss",
        "cointelegraph_public_rss",
        "decrypt_public_rss",
        "cryptoslate_public_rss",
        "oilprice_public_rss",
        "mining_copper_public_rss",
        "bleepingcomputer_public_rss",
        "krebsonsecurity_public_rss",
        "semiengineering_public_rss",
        "axios_public_rss",
        "the_verge_public_rss",
        "wired_business_public_rss",
        "siliconangle_public_rss",
        "securityweek_public_rss",
        "utilitydive_public_rss",
        "supplychaindive_public_rss",
        "biopharmadive_public_rss",
        "constructiondive_public_rss",
        "cfodive_public_rss",
        "restaurantdive_public_rss",
        "grocerydive_public_rss",
        "marketingdive_public_rss",
        "hrdive_public_rss",
        "medtechdive_public_rss",
        "highereddive_public_rss",
        "k12dive_public_rss",
        "smartcitiesdive_public_rss",
        "fiercebiotech_public_rss",
        "stat_public_rss",
        "breakingdefense_public_rss",
        "defensenews_global_public_rss",
        "spacenews_public_rss",
        "freightwaves_public_rss",
        "loadstar_public_rss",
        "seekingalpha_market_currents_rss",
        "stocktitan_public_rss",
        "finviz_public_news_html",
        "investors_public_rss",
        "investorplace_public_rss",
        "fxstreet_public_rss",
        "defenseone_public_rss",
        "nareit_public_rss",
        "etftrends_public_rss",
        "housingwire_public_rss",
        "americanbanker_public_rss",
        "techmeme_public_rss",
        "bankingdive_public_rss",
        "retaildive_public_rss",
        "ciodive_public_rss",
        "cybersecuritydive_public_rss",
        "paymentsdive_public_rss",
        "manufacturingdive_public_rss",
        "fooddive_public_rss",
        "healthcaredive_public_rss",
        "pharmavoice_public_rss"
    ),
    [int]$MaxItemsPerSource = 50,
    [int]$MaxFetchesPerSource = 6,
    [int]$CycleSleepSeconds = 1800,
    [double]$RequestSleepSeconds = 1.0,
    [string]$RawDir = "data/raw/l0_public_market_macro_news",
    [string]$StatePath = "data/artifacts/l0_public_market_macro_news/collector_state.json",
    [string]$EventPath = "data/artifacts/l0_public_market_macro_news/collector_events.jsonl",
    [string]$ProgressPath = "data/artifacts/l0_public_market_macro_news/collector_progress.json",
    [string]$PlanPath = "data/artifacts/l0_public_market_macro_news/collection_plan.json",
    [string]$StopPath = "data/artifacts/l0_public_market_macro_news/STOP",
    [string]$LogPath = "logs/l0_public_market_macro_news_collector.log",
    [string]$StatusPath = "data/artifacts/l0_public_market_macro_news/background_process.json"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (Test-Path -LiteralPath $StopPath) {
    Remove-Item -LiteralPath $StopPath -Force
}

$arguments = @(
    "scripts/run_l0_public_market_macro_news_collector.py",
    "--mode", "background",
    "--sources"
) + $Sources + @(
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
    provider = "public_market_macro_news_feeds"
    mode = "market_macro_watch"
    max_items_per_source = $MaxItemsPerSource
    max_fetches_per_source = $MaxFetchesPerSource
    cycle_sleep_seconds = $CycleSleepSeconds
    request_sleep_seconds = $RequestSleepSeconds
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
Write-Output ("[L0_PUBLIC_MARKET_MACRO_NEWS_STARTED] pid={0} status_path={1} progress_path={2}" -f $process.Id, $StatusPath, $ProgressPath)
