param(
    [string]$TaskName = "TraderTerminalMobileServer",
    [int]$Port = 5173,
    [switch]$StartNow
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runner = Join-Path $projectRoot "scripts/start_trader_terminal_lan.ps1"
if (-not (Test-Path $runner)) {
    throw "Missing runner script: $runner"
}

$quotedRunner = $runner.Replace("'", "''")
$command = "& '$quotedRunner' -Port $Port -SkipCatalogBuild -StopExisting"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command $command"
$triggers = @(
    (New-ScheduledTaskTrigger -AtLogOn)
    (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At "22:20")
    (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At "23:20")
)
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
    -Description "Starts the Trader Terminal LAN/PWA server when the trading workstation wakes or logs on." `
    -Force | Out-Null

if ($StartNow) {
    Start-ScheduledTask -TaskName $TaskName
}

[pscustomobject]@{
    TaskName = $TaskName
    State = (Get-ScheduledTask -TaskName $TaskName).State
    Port = $Port
    WakeToRun = (Get-ScheduledTask -TaskName $TaskName).Settings.WakeToRun
    Url = "http://127.0.0.1:$Port"
}
