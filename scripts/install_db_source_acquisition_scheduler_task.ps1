param(
    [string]$TaskName = "TraderBrainDbSourceAcquisitionScheduler",
    [string]$Config = "configs/db_source_acquisition_scheduler.json",
    [int]$IntervalSeconds = 60,
    [switch]$StartNow
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runner = Join-Path $projectRoot "scripts/run_db_source_acquisition_scheduler.ps1"
if (-not (Test-Path $runner)) {
    throw "Missing DB source acquisition runner script: $runner"
}
if (-not (Test-Path (Join-Path $projectRoot $Config))) {
    throw "Missing DB source acquisition scheduler config: $Config"
}

$quotedRoot = $projectRoot.Replace("'", "''")
$quotedRunner = $runner.Replace("'", "''")
$quotedConfig = $Config.Replace("'", "''")
$command = "Set-Location '$quotedRoot'; & '$quotedRunner' -Config '$quotedConfig' -IntervalSeconds $IntervalSeconds"

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
    $runnerArgs = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""$runner"" -Config ""$Config"" -IntervalSeconds $IntervalSeconds"
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
        -Description "Runs the Trader Brain DB source acquisition scheduler. Diagnostic-only; no broker submit, live order, replay, or real-capital permission." `
        -Force | Out-Null

    if ($StartNow) {
        Start-ScheduledTask -TaskName $TaskName
    }

    Get-ScheduledTask -TaskName $TaskName | Select-Object @{Name = "InstallMode"; Expression = { "ScheduledTask" } }, TaskName, State, TaskPath
} catch {
    $fallback = Install-StartupFallback
    if ($StartNow) {
        Start-Process `
            -FilePath "powershell.exe" `
            -ArgumentList "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""$runner"" -Config ""$Config"" -IntervalSeconds $IntervalSeconds" `
            -WorkingDirectory $projectRoot `
            -WindowStyle Hidden
    }
    $fallback
}
