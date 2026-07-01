param(
    [int]$IntervalMinutes = 5,
    [int]$OutsideMarketSleepMinutes = 5,
    [string]$DbPath = "trading.db",
    [string]$EnvFile = "config/kis_paper.env",
    [string]$Symbols = "",
    [int]$MaxRuns = 0,
    [int]$OpenHour = 9,
    [int]$OpenMinute = 35,
    [int]$CloseHour = 15,
    [int]$CloseMinute = 50,
    [string]$CalendarCsv = "config/nasdaq_market_calendar.csv",
    [int]$TradeStartOffsetMinutes = 5,
    [int]$TradeEndBufferMinutes = 10,
    [int]$EodDelayMinutes = 30,
    [ValidateSet("None", "Sleep", "Hibernate", "Shutdown")]
    [string]$PowerActionAfterEod = "Hibernate",
    [string]$LogDir = "logs"
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $projectRoot

if ($IntervalMinutes -lt 0) {
    Write-Warning "[PARAM INVALID] IntervalMinutes cannot be negative. Skipping execution."
    exit 0
}
if ($OutsideMarketSleepMinutes -lt 1) {
    Write-Warning "[PARAM GUARD] OutsideMarketSleepMinutes must be at least 1. Using 1."
    $OutsideMarketSleepMinutes = 1
}

function Get-NasdaqNowEastern {
    $tz = [System.TimeZoneInfo]::FindSystemTimeZoneById("Eastern Standard Time")
    return [System.TimeZoneInfo]::ConvertTimeFromUtc([DateTime]::UtcNow, $tz)
}

function Get-NasdaqCalendarStatus {
    $env:PYTHONPATH = "src" + [System.IO.Path]::PathSeparator + $env:PYTHONPATH
    $json = & python -m src.app.nasdaq_market_calendar `
        --calendar-csv $CalendarCsv `
        --trade-start-offset-minutes $TradeStartOffsetMinutes `
        --trade-end-buffer-minutes $TradeEndBufferMinutes `
        --eod-delay-minutes $EodDelayMinutes
    if ($LASTEXITCODE -ne 0) {
        throw "NASDAQ_CALENDAR_STATUS_FAILED"
    }
    return ($json | ConvertFrom-Json)
}

function Write-SupervisorStatus {
    param(
        [string]$Status,
        [string]$Reason,
        [int]$RunCount,
        [int]$ExitCode,
        [DateTime]$EasternNow
    )
    $reportDir = Join-Path $projectRoot "docs/reports/task_588_kis_paper_market_hours_runtime_loop"
    New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
    $path = Join-Path $reportDir "nasdaq_paper_supervisor_status.csv"
    $row = [pscustomobject]@{
        created_at_utc = [DateTime]::UtcNow.ToString("o")
        eastern_time = $EasternNow.ToString("yyyy-MM-dd HH:mm:ss")
        status = $Status
        reason = $Reason
        run_count = $RunCount
        exit_code = $ExitCode
        interval_minutes = $IntervalMinutes
        db_path = $DbPath
        env_file = $EnvFile
        symbols = $Symbols
        calendar_csv = $CalendarCsv
    }
    if (Test-Path $path) {
        $row | Export-Csv -Path $path -Append -NoTypeInformation -Encoding UTF8
    } else {
        $row | Export-Csv -Path $path -NoTypeInformation -Encoding UTF8
    }
}

function Invoke-Task588Once {
    $env:PYTHONPATH = "src" + [System.IO.Path]::PathSeparator + $env:PYTHONPATH
    if (-not $env:TRADING_MAX_OPEN_ORDERS) { $env:TRADING_MAX_OPEN_ORDERS = "1" }
    if (-not $env:TRADING_MAX_PAPER_ORDERS_PER_DAY) { $env:TRADING_MAX_PAPER_ORDERS_PER_DAY = "3" }

    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
    $stdout = Join-Path $LogDir "task588_nasdaq_paper_loop_stdout.log"
    $stderr = Join-Path $LogDir "task588_nasdaq_paper_loop_stderr.log"

    $args = @(
        "-m", "src.app.task_588_kis_paper_market_hours_runtime_loop",
        "--db-path", $DbPath,
        "--env-file", $EnvFile,
        "--iterations", "1",
        "--interval-seconds", "60"
    )
    if ($Symbols.Trim() -ne "") {
        $args += @("--symbols", $Symbols)
    }

    $stamp = [DateTime]::UtcNow.ToString("o")
    Add-Content -Path $stdout -Value "[$stamp] RUN Task588 once"
    & python @args 1>> $stdout 2>> $stderr
    return $LASTEXITCODE
}

function Invoke-EodReport {
    param([string]$SessionDate)
    $env:PYTHONPATH = "src" + [System.IO.Path]::PathSeparator + $env:PYTHONPATH
    $stdout = Join-Path $LogDir "task589_paper_eod_stdout.log"
    $stderr = Join-Path $LogDir "task589_paper_eod_stderr.log"
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
    & python -m src.app.task_589_paper_eod_slack_report --db-path $DbPath --env-file $EnvFile --session-date $SessionDate 1>> $stdout 2>> $stderr
    return $LASTEXITCODE
}

function Invoke-SupervisorFailureAlert {
    param(
        [string]$Component,
        [string]$Status,
        [string]$Detail
    )
    $env:PYTHONPATH = "src" + [System.IO.Path]::PathSeparator + $env:PYTHONPATH
    & python -m src.app.supervisor_slack_alert --component $Component --status $Status --detail $Detail --env-file $EnvFile | Out-Null
}

function Invoke-AutomationLifecycleNotice {
    param(
        [string]$Status,
        [string]$Detail
    )
    try {
        $env:PYTHONPATH = "src" + [System.IO.Path]::PathSeparator + $env:PYTHONPATH
        & python -m src.app.supervisor_slack_alert `
            --component "TASK588_AUTOTRADE" `
            --status $Status `
            --detail $Detail `
            --env-file $EnvFile `
            --message-type "PAPER_AUTOTRADE_LIFECYCLE" | Out-Null
    } catch {
        Write-Warning "[LIFECYCLE NOTICE] failed: $($_.Exception.Message)"
    }
}

function Invoke-PowerAction {
    param([string]$Action)
    $normalized = $Action.Trim().ToLowerInvariant()
    if ($normalized -eq "none" -or $normalized -eq "") { return }
    if ($normalized -eq "sleep") {
        rundll32.exe powrprof.dll,SetSuspendState 0,1,0
    } elseif ($normalized -eq "hibernate") {
        shutdown.exe /h
    } elseif ($normalized -eq "shutdown") {
        Write-Warning "[POWER ACTION] shutdown is disabled by workstation policy; hibernating instead."
        shutdown.exe /h
    } else {
        Write-Warning "[POWER ACTION] unsupported action=$Action"
    }
}

$runCount = 0
$lastEodSessionDate = ""
$lifecycleEndNoticeSent = $false
Write-Host "[SUPERVISOR START] NASDAQ paper loop interval=${IntervalMinutes}m db=$DbPath env_file=$EnvFile"
Write-Host "[SESSION] calendar=$CalendarCsv trade_start_offset=${TradeStartOffsetMinutes}m trade_end_buffer=${TradeEndBufferMinutes}m eod_delay=${EodDelayMinutes}m"
Invoke-AutomationLifecycleNotice -Status "STARTED" -Detail "모의투자 자동매매 시작합니다"

while ($true) {
    $easternNow = Get-NasdaqNowEastern
    try {
        $calendar = Get-NasdaqCalendarStatus
        $inSession = ([int]$calendar.trading_window_open_flag -eq 1)
    } catch {
        Write-Warning "[CALENDAR] failed: $($_.Exception.Message)"
        Write-SupervisorStatus -Status "CALENDAR_FAILED" -Reason "NASDAQ_CALENDAR_STATUS_FAILED" -RunCount $runCount -ExitCode -1 -EasternNow $easternNow
        Invoke-SupervisorFailureAlert -Component "NASDAQ_CALENDAR" -Status "CALENDAR_FAILED" -Detail $_.Exception.Message
        Start-Sleep -Seconds ($OutsideMarketSleepMinutes * 60)
        continue
    }

    if ($inSession) {
        if ($MaxRuns -gt 0 -and $runCount -ge $MaxRuns) {
            Write-Host "[SUPERVISOR STOP] reached max market runs: $MaxRuns"
            Write-SupervisorStatus -Status "STOPPED" -Reason "MAX_RUNS_REACHED" -RunCount $runCount -ExitCode 0 -EasternNow $easternNow
            break
        }
        $runCount += 1
        Write-Host "[RUN $runCount] NASDAQ session open at $($easternNow.ToString("yyyy-MM-dd HH:mm:ss")) ET"
        $exitCode = Invoke-Task588Once
        if ($exitCode -eq 0) {
            Write-SupervisorStatus -Status "TASK588_OK" -Reason $calendar.reason -RunCount $runCount -ExitCode $exitCode -EasternNow $easternNow
        } else {
            Write-Warning "[RUN $runCount] Task588 failed exit_code=$exitCode"
            Write-SupervisorStatus -Status "TASK588_FAILED" -Reason "NON_ZERO_EXIT" -RunCount $runCount -ExitCode $exitCode -EasternNow $easternNow
            Invoke-SupervisorFailureAlert -Component "TASK588" -Status "NON_ZERO_EXIT" -Detail "exit_code=$exitCode"
        }
        if ($IntervalMinutes -eq 0) {
            Write-Host "[SUPERVISOR STOP] IntervalMinutes=0 test mode"
            break
        }
        Start-Sleep -Seconds ($IntervalMinutes * 60)
    } else {
        Write-Host "[WAIT] outside NASDAQ trading window at $($easternNow.ToString("yyyy-MM-dd HH:mm:ss")) ET reason=$($calendar.reason)"
        if ([int]$calendar.eod_due_flag -eq 1 -and $lastEodSessionDate -ne [string]$calendar.session_date) {
            $eodExitCode = Invoke-EodReport -SessionDate ([string]$calendar.session_date)
            if ($eodExitCode -eq 0) {
                $lastEodSessionDate = [string]$calendar.session_date
                Write-SupervisorStatus -Status "EOD_REPORT_OK" -Reason "EOD_DUE_AFTER_CLOSE" -RunCount $runCount -ExitCode $eodExitCode -EasternNow $easternNow
                if (-not $lifecycleEndNoticeSent) {
                    Invoke-AutomationLifecycleNotice -Status "ENDED" -Detail "모의투자 자동매매 종료합니다"
                    $lifecycleEndNoticeSent = $true
                }
                Invoke-PowerAction -Action $PowerActionAfterEod
            } else {
                Write-Warning "[EOD] Task589 failed exit_code=$eodExitCode"
                Write-SupervisorStatus -Status "EOD_REPORT_FAILED" -Reason "TASK589_NON_ZERO_EXIT" -RunCount $runCount -ExitCode $eodExitCode -EasternNow $easternNow
                Invoke-SupervisorFailureAlert -Component "TASK589_EOD" -Status "NON_ZERO_EXIT" -Detail "exit_code=$eodExitCode"
            }
        } else {
            Write-SupervisorStatus -Status "WAITING" -Reason $calendar.reason -RunCount $runCount -ExitCode 0 -EasternNow $easternNow
        }
        Start-Sleep -Seconds ($OutsideMarketSleepMinutes * 60)
    }
}

if (-not $lifecycleEndNoticeSent) {
    Invoke-AutomationLifecycleNotice -Status "ENDED" -Detail "모의투자 자동매매 종료합니다"
}
