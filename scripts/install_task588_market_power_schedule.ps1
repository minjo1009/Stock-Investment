param(
    [string]$TaskName = "ForeignStockQuantPaperWake",
    [int]$IntervalMinutes = 5,
    [string]$DbPath = "trading.db",
    [string]$EnvFile = "config/kis_paper.env",
    [string]$CalendarCsv = "config/nasdaq_market_calendar.csv",
    [int]$WakeOffsetMinutes = 10,
    [ValidateSet("None", "Sleep", "Hibernate")]
    [string]$PowerActionAfterEod = "Hibernate"
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runner = Join-Path $projectRoot "scripts/run_task588_nasdaq_paper_loop.ps1"
$calendarPath = Join-Path $projectRoot $CalendarCsv
if (-not (Test-Path $calendarPath)) {
    throw "Missing NASDAQ calendar CSV: $calendarPath"
}

$eastern = [TimeZoneInfo]::FindSystemTimeZoneById("Eastern Standard Time")
$localTz = [TimeZoneInfo]::Local
$sampleDates = @(
    [datetime]::SpecifyKind((Get-Date -Year (Get-Date).Year -Month 1 -Day 15 -Hour 9 -Minute 30 -Second 0), [DateTimeKind]::Unspecified),
    [datetime]::SpecifyKind((Get-Date -Year (Get-Date).Year -Month 7 -Day 15 -Hour 9 -Minute 30 -Second 0), [DateTimeKind]::Unspecified)
)
$wakeTimes = New-Object System.Collections.Generic.List[string]
foreach ($openEt in $sampleDates) {
    $wakeEt = $openEt.AddMinutes(-1 * $WakeOffsetMinutes)
    $wakeLocal = [TimeZoneInfo]::ConvertTime($wakeEt, $eastern, $localTz)
    $timeText = $wakeLocal.ToString("HH:mm")
    if (-not $wakeTimes.Contains($timeText)) {
        $wakeTimes.Add($timeText)
    }
}
$triggers = @(
    $wakeTimes | ForEach-Object {
        New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $_
    }
)

$quotedRoot = $projectRoot.Replace("'", "''")
$quotedRunner = $runner.Replace("'", "''")
$quotedDb = $DbPath.Replace("'", "''")
$quotedEnv = $EnvFile.Replace("'", "''")
$quotedCalendar = $CalendarCsv.Replace("'", "''")
$command = "Set-Location '$quotedRoot'; & '$quotedRunner' -IntervalMinutes $IntervalMinutes -DbPath '$quotedDb' -EnvFile '$quotedEnv' -CalendarCsv '$quotedCalendar' -PowerActionAfterEod $PowerActionAfterEod"

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command $command"
$settings = New-ScheduledTaskSettingsSet `
    -WakeToRun `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $triggers `
    -Settings $settings `
    -Description "Wakes Windows from sleep/hibernate before Nasdaq open local-time DST windows and starts the calendar-guarded paper supervisor. Holidays are blocked by the supervisor calendar. Post-EOD power policy is hibernate-first; full shutdown is intentionally not used." `
    -Force | Out-Null

[pscustomobject]@{
    TaskName = $TaskName
    State = (Get-ScheduledTask -TaskName $TaskName).State
    TriggerCount = $triggers.Count
    WakeTimesLocal = ($wakeTimes -join ",")
    PowerActionAfterEod = $PowerActionAfterEod
    HibernateWakeNote = "Windows WakeToRun covers sleep/hibernate. Full shutdown is intentionally not used for this trading workstation."
}
