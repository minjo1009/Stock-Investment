param(
    [int]$IntervalSeconds = 3600,
    [switch]$Once,
    [string]$Root = "",
    [string]$ReportDir = "data/artifacts/l0_backfill_orchestration/hourly",
    [string]$StatusPath = "data/artifacts/l0_backfill_orchestration/hourly_reporter_process.json",
    [string]$AlertPath = "data/artifacts/l0_backfill_orchestration/hourly_alerts.jsonl",
    [string]$LogPath = "logs/l0_backfill_orchestration/hourly_reporter.log"
)

$ErrorActionPreference = "Stop"
if ($Root -eq "") {
    $Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}
Set-Location $Root

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $StatusPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $AlertPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $LogPath) | Out-Null

$status = @{
    started_at = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    pid = $PID
    interval_seconds = $IntervalSeconds
    report_dir = $ReportDir
    alert_path = $AlertPath
    diagnostic_only_flag = 1
    trade_authority_flag = 0
    broker_mutation_permitted_flag = 0
    real_capital_permitted_flag = 0
}
if ($Once) {
    $onceStatusPath = Join-Path (Split-Path -Parent $StatusPath) "hourly_once_last_process.json"
    $status | ConvertTo-Json -Depth 5 | Set-Content -Path $onceStatusPath -Encoding UTF8
} else {
    $status | ConvertTo-Json -Depth 5 | Set-Content -Path $StatusPath -Encoding UTF8
}

function Get-JsonFile {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }
    try {
        return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        return $null
    }
}

function Test-BackgroundRunning {
    param([object]$Node)
    if ($null -eq $Node) {
        return $false
    }
    $pidValue = [int]($Node.pid -as [int])
    if ($pidValue -le 0) {
        return $false
    }
    return $null -ne (Get-Process -Id $pidValue -ErrorAction SilentlyContinue)
}

function Write-HourlySnapshot {
    $stamp = [DateTimeOffset]::UtcNow.ToString("yyyyMMddTHHmmssZ")
    $null = python scripts/report_l0_collection_status.py 2>&1 | Tee-Object -FilePath $LogPath -Append
    $null = python scripts/run_l0_backfill_reliability_audit.py --write 2>&1 | Tee-Object -FilePath $LogPath -Append
    $statusJsonPath = "data/artifacts/l0_collection_status/current_status.json"
    $current = Get-JsonFile -Path $statusJsonPath
    if ($null -eq $current) {
        $alert = @{
            ts = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
            severity = "WARN"
            alert = "current_status_missing_or_unreadable"
            diagnostic_only_flag = 1
        }
        Add-Content -LiteralPath $AlertPath -Value ($alert | ConvertTo-Json -Compress -Depth 5)
        return
    }

    $snapshotPath = Join-Path $ReportDir ("status_{0}.json" -f $stamp)
    $current | ConvertTo-Json -Depth 20 | Set-Content -Path $snapshotPath -Encoding UTF8

    $bg = $current.background_processes
    $running = @{
        daily = Test-BackgroundRunning $bg.daily
        five_min = Test-BackgroundRunning $bg.five_min
        public_newswire_backfill = Test-BackgroundRunning $bg.public_newswire_backfill
        public_context_news_backfill = Test-BackgroundRunning $bg.public_context_news_backfill
        public_market_macro_news_backfill = Test-BackgroundRunning $bg.public_market_macro_news_backfill
    }
    $progress = @{
        daily_pct = $current.daily_bars.progress_pct
        five_min_pct = $current.five_min_bars.progress_pct
        public_newswire_backfill_pct = $current.public_newswire_backfill.progress_pct
        public_context_news_backfill_pct = $current.public_context_news_backfill.progress_pct
        public_market_macro_news_backfill_pct = $current.public_market_macro_news_backfill.progress_pct
    }
    $summary = @{
        task_id = "TASK-4131"
        ts = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
        snapshot_path = $snapshotPath
        running = $running
        progress = $progress
        strategy = "NOT_ACCEPTED"
        deployment = "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"
        real_capital = "FORBIDDEN"
        diagnostic_only_flag = 1
        trade_authority_flag = 0
        broker_mutation_permitted_flag = 0
        real_capital_permitted_flag = 0
    }
    $summaryPath = Join-Path $ReportDir "latest_summary.json"
    $enhancedPath = "data/artifacts/l0_backfill_orchestration/enhanced_latest_summary.json"
    $alertsPath = "data/artifacts/l0_backfill_orchestration/current_alerts.json"
    $enhanced = Get-JsonFile -Path $enhancedPath
    $alerts = Get-JsonFile -Path $alertsPath
    if ($null -ne $enhanced) {
        $summary.task_id = "TASK-4132"
        $summary.enhanced_summary_path = $enhancedPath
        $summary.current_alerts_path = $alertsPath
        $summary.reliability = @{
            stall_threshold_minutes = $enhanced.stall_threshold_minutes
            supervisor_recommendation_count = @($enhanced.supervisor_recommendations).Count
            alert_count = @($enhanced.alerts).Count
            lane_health = $enhanced.lanes
            five_min_checkpoint = $enhanced.five_min_checkpoint
            raw_audit = $enhanced.raw_audit
        }
    }
    if ($null -ne $alerts) {
        $summary.current_alerts = $alerts.alerts
    }
    $summary | ConvertTo-Json -Depth 10 | Set-Content -Path $summaryPath -Encoding UTF8

    foreach ($name in $running.Keys) {
        if (-not $running[$name]) {
            $alert = @{
                ts = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
                severity = "INFO"
                alert = "lane_not_running"
                lane = $name
                progress = $progress
                diagnostic_only_flag = 1
            }
            Add-Content -LiteralPath $AlertPath -Value ($alert | ConvertTo-Json -Compress -Depth 10)
        }
    }
}

do {
    try {
        Write-HourlySnapshot
    } catch {
        $alert = @{
            ts = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
            severity = "ERROR"
            alert = "hourly_reporter_exception"
            message = $_.Exception.Message
            diagnostic_only_flag = 1
        }
        Add-Content -LiteralPath $AlertPath -Value ($alert | ConvertTo-Json -Compress -Depth 5)
    }
    if ($Once) {
        break
    }
    Start-Sleep -Seconds ([Math]::Max($IntervalSeconds, 60))
} while ($true)
