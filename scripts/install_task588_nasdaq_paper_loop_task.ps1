param(
    [string]$TaskName = "ForeignStockQuantPaperLoop",
    [int]$IntervalMinutes = 5,
    [string]$DbPath = "trading.db",
    [string]$EnvFile = "config/kis_paper.env",
    [string]$CalendarCsv = "config/nasdaq_market_calendar.csv",
    [int]$TradeStartOffsetMinutes = 5,
    [int]$TradeEndBufferMinutes = 10,
    [int]$EodDelayMinutes = 30,
    [ValidateSet("None", "Sleep", "Hibernate")]
    [string]$PowerActionAfterEod = "Hibernate",
    [string]$Symbols = "",
    [switch]$StartNow
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runner = Join-Path $projectRoot "scripts/run_task588_nasdaq_paper_loop.ps1"
if (-not (Test-Path $runner)) {
    throw "Missing runner script: $runner"
}

$quotedRoot = $projectRoot.Replace("'", "''")
$quotedRunner = $runner.Replace("'", "''")
$quotedDb = $DbPath.Replace("'", "''")
$quotedEnv = $EnvFile.Replace("'", "''")
$quotedCalendarCsv = $CalendarCsv.Replace("'", "''")
$quotedSymbols = $Symbols.Replace("'", "''")
$command = "Set-Location '$quotedRoot'; & '$quotedRunner' -IntervalMinutes $IntervalMinutes -DbPath '$quotedDb' -EnvFile '$quotedEnv' -CalendarCsv '$quotedCalendarCsv' -TradeStartOffsetMinutes $TradeStartOffsetMinutes -TradeEndBufferMinutes $TradeEndBufferMinutes -EodDelayMinutes $EodDelayMinutes -PowerActionAfterEod $PowerActionAfterEod -Symbols '$quotedSymbols'"

function Install-StartupFallback {
    $startup = [Environment]::GetFolderPath("Startup")
    if (-not $startup) {
        throw "Could not resolve user Startup folder."
    }
    $legacyCmdPath = Join-Path $startup "$TaskName.cmd"
    if (Test-Path $legacyCmdPath) {
        Remove-Item -LiteralPath $legacyCmdPath -Force
    }
    $vbsPath = Join-Path $startup "$TaskName.vbs"
    $runnerArgs = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""$runner"" -IntervalMinutes $IntervalMinutes -DbPath ""$DbPath"" -EnvFile ""$EnvFile"" -CalendarCsv ""$CalendarCsv"" -TradeStartOffsetMinutes $TradeStartOffsetMinutes -TradeEndBufferMinutes $TradeEndBufferMinutes -EodDelayMinutes $EodDelayMinutes -PowerActionAfterEod $PowerActionAfterEod"
    if ($Symbols.Trim() -ne "") {
        $runnerArgs += " -Symbols ""$Symbols"""
    }
    $vbsCommand = $runnerArgs.Replace('"', '""')
    $vbsText = @"
Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = "$projectRoot"
shell.Run "$vbsCommand", 0, False
"@
    Set-Content -Path $vbsPath -Value $vbsText -Encoding Unicode
    [pscustomobject]@{
        InstallMode = "StartupFolderFallback"
        TaskName = $TaskName
        State = "READY_AT_NEXT_LOGON"
        Path = $vbsPath
    }
}

try {
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command $command"
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -MultipleInstances IgnoreNew `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 5)

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Runs Task588 KIS paper trading during NASDAQ calendar trading windows, posts Slack reports, and applies a hibernate-first post-EOD power policy." `
        -Force | Out-Null

    if ($StartNow) {
        Start-ScheduledTask -TaskName $TaskName
    }

    Get-ScheduledTask -TaskName $TaskName | Select-Object @{Name = "InstallMode"; Expression = { "ScheduledTask" } }, TaskName, State, TaskPath
} catch {
    $fallback = Install-StartupFallback
    if ($StartNow) {
        $startArgs = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""$runner"" -IntervalMinutes $IntervalMinutes -DbPath ""$DbPath"" -EnvFile ""$EnvFile"" -CalendarCsv ""$CalendarCsv"" -TradeStartOffsetMinutes $TradeStartOffsetMinutes -TradeEndBufferMinutes $TradeEndBufferMinutes -EodDelayMinutes $EodDelayMinutes -PowerActionAfterEod $PowerActionAfterEod"
        if ($Symbols.Trim() -ne "") {
            $startArgs += " -Symbols ""$Symbols"""
        }
        Start-Process `
            -FilePath "powershell.exe" `
            -ArgumentList $startArgs `
            -WorkingDirectory $projectRoot `
            -WindowStyle Hidden
    }
    $fallback
}
