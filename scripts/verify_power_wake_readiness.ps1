param(
    [string]$ScheduledTaskName = "ForeignStockQuantPaperWake",
    [string]$AdapterName = ""
)

$ErrorActionPreference = "Stop"

Write-Host "== Scheduled task =="
$task = Get-ScheduledTask -TaskName $ScheduledTaskName
$task | Select-Object TaskName, State | Format-List
$task.Settings | Select-Object WakeToRun, StartWhenAvailable, RunOnlyIfNetworkAvailable, DisallowStartIfOnBatteries, StopIfGoingOnBatteries, ExecutionTimeLimit | Format-List
$task.Triggers | Format-List StartBoundary, DaysOfWeek, Enabled
Get-ScheduledTaskInfo -TaskName $ScheduledTaskName | Format-List LastRunTime, LastTaskResult, NextRunTime, NumberOfMissedRuns

Write-Host "== Wake timers =="
powercfg /query SCHEME_CURRENT SUB_SLEEP RTCWAKE

Write-Host "== Wake-capable devices =="
powercfg /devicequery wake_from_any

Write-Host "== Wake-armed devices =="
powercfg /devicequery wake_armed

Write-Host "== Network adapters =="
Get-NetAdapter | Where-Object { $_.Status -ne "Disabled" } | Select-Object Name, InterfaceDescription, Status, MacAddress, LinkSpeed | Format-Table -AutoSize

if ($AdapterName.Trim() -eq "") {
    $adapter = Get-NetAdapter | Where-Object { $_.InterfaceDescription -like "*Realtek*GbE*" -and $_.Status -ne "Disabled" } | Select-Object -First 1
    if ($null -eq $adapter) {
        $adapter = Get-NetAdapter | Where-Object { $_.Status -eq "Up" } | Select-Object -First 1
    }
    if ($null -ne $adapter) {
        $AdapterName = $adapter.Name
    }
}

Write-Host "== WoL advanced properties =="
Get-NetAdapterAdvancedProperty -Name $AdapterName |
    Where-Object { $_.DisplayName -match "Wake|WOL|Magic|Shutdown|EEE|Energy|Green" -or $_.RegistryKeyword -match "Wake|WOL|Magic|Shutdown|EEE|Energy|Green" } |
    Select-Object Name, DisplayName, DisplayValue, RegistryKeyword |
    Format-Table -AutoSize

Write-Host "== Firmware identity =="
Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer, Model, SystemType | Format-List
Get-CimInstance Win32_BIOS | Select-Object Manufacturer, SMBIOSBIOSVersion, ReleaseDate | Format-List
