param(
    [string]$ProjectRoot = "",
    [string]$TaskName = "TraderBrainL0BackfillWorkerRecovery4148",
    [int]$IntervalMinutes = 15,
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Global -ErrorAction SilentlyContinue) {
    $global:PSNativeCommandUseErrorActionPreference = $false
}

if ($ProjectRoot -eq "") {
    $ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}

$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$ScriptPath = Join-Path $ProjectRoot "scripts\run_l0_backfill_worker_recovery_4148.py"
$WrapperPath = Join-Path $ProjectRoot "scripts\run_l0_backfill_worker_recovery_once_4148.ps1"
$ArtifactDir = Join-Path $ProjectRoot "data\artifacts\task_4148_l0_backfill_worker_recovery_health_gate"
$ArtifactPath = Join-Path $ArtifactDir "windows_task_scheduler_registration.json"

if (-not (Test-Path -LiteralPath $ScriptPath)) {
    throw "missing recovery script: $ScriptPath"
}
if (-not (Test-Path -LiteralPath $WrapperPath)) {
    throw "missing scheduler wrapper: $WrapperPath"
}

New-Item -ItemType Directory -Force -Path $ArtifactDir | Out-Null

$taskArgument = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$WrapperPath`" -ProjectRoot `"$ProjectRoot`""
$action = "powershell.exe $taskArgument"

$query = @()
$exists = $false
try {
    $query = schtasks.exe /Query /TN $TaskName /FO LIST 2>&1
    $exists = $LASTEXITCODE -eq 0
} catch {
    $query = @($_.Exception.Message)
    $exists = $false
}

if ($Apply) {
    if ($IntervalMinutes -lt 5) {
        throw "IntervalMinutes must be >= 5"
    }
    $startBoundary = (Get-Date).AddMinutes(1).ToString("yyyy-MM-ddTHH:mm:ss")
    $escapedArgument = [Security.SecurityElement]::Escape($taskArgument)
    $xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>TASK-4148 L0 backfill worker recovery guard. Diagnostic-only; no broker, live order, paper promotion, or real-capital authority.</Description>
  </RegistrationInfo>
  <Triggers>
    <TimeTrigger>
      <Repetition>
        <Interval>PT$($IntervalMinutes)M</Interval>
        <Duration>P3650D</Duration>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>$startBoundary</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>$escapedArgument</Arguments>
    </Exec>
  </Actions>
</Task>
"@
    Register-ScheduledTask -TaskName $TaskName -Xml $xml -Force | Out-Null
    $query = schtasks.exe /Query /TN $TaskName /FO LIST /V 2>&1
    $exists = $LASTEXITCODE -eq 0
}

$payload = [ordered]@{
    task_id = "TASK-4148"
    generated_at = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    scheduler_task_name = $TaskName
    interval_minutes = $IntervalMinutes
    apply = [int][bool]$Apply
    registered = [int]$exists
    action = $action
    project_root = $ProjectRoot
    script_path = $ScriptPath
    wrapper_path = $WrapperPath
    diagnostic_only_flag = 1
    trade_authority_flag = 0
    broker_mutation_permitted_flag = 0
    real_capital_permitted_flag = 0
    query_tail = ($query -join "`n")
}

$payload | ConvertTo-Json -Depth 5 | Set-Content -Path $ArtifactPath -Encoding UTF8
Write-Output ("TASK-4148 scheduler_registered={0} task_name={1} interval_minutes={2} artifact=windows_task_scheduler_registration.json" -f ([int]$exists), $TaskName, $IntervalMinutes)
