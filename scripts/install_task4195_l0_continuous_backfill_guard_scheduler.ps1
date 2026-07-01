param(
    [string]$ProjectRoot = "",
    [string]$TaskName = "TraderBrainL0ContinuousBackfillGuard4195",
    [int]$IntervalMinutes = 5,
    [switch]$Apply,
    [switch]$StartNow,
    [switch]$DisableSuperseded4148
)

$ErrorActionPreference = "Stop"
if (-not $ProjectRoot) {
    $ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}

$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$WrapperPath = Join-Path $ProjectRoot "scripts\run_task4195_l0_continuous_backfill_guard_once.ps1"
$ArtifactDir = Join-Path $ProjectRoot "data\artifacts\task_4195_l0_continuous_backfill_runtime_governance"
$ArtifactPath = Join-Path $ArtifactDir "windows_task_scheduler_registration.json"

if (-not (Test-Path -LiteralPath $WrapperPath)) {
    throw "missing TASK-4195 scheduler wrapper: $WrapperPath"
}
if ($IntervalMinutes -lt 5) {
    throw "IntervalMinutes must be >= 5"
}

New-Item -ItemType Directory -Force -Path $ArtifactDir | Out-Null

$taskArgument = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$WrapperPath`" -ProjectRoot `"$ProjectRoot`""
$query = @()
$exists = $false
try {
    $query = schtasks.exe /Query /TN $TaskName /FO LIST /V 2>&1
    $exists = $LASTEXITCODE -eq 0
} catch {
    $query = @($_.Exception.Message)
    $exists = $false
}

if ($Apply) {
    $startBoundary = (Get-Date).AddMinutes(1).ToString("yyyy-MM-ddTHH:mm:ss")
    $escapedArgument = [Security.SecurityElement]::Escape($taskArgument)
    $xml = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>TASK-4195 continuous L0 backfill guard. Keeps historical backfills alive until completion. Diagnostic-only; no broker, live order, paper promotion, or real-capital authority.</Description>
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
    <ExecutionTimeLimit>PT30M</ExecutionTimeLimit>
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
    if ($DisableSuperseded4148) {
        Disable-ScheduledTask -TaskName "TraderBrainL0BackfillWorkerRecovery4148" -ErrorAction SilentlyContinue | Out-Null
    }
    if ($StartNow) {
        Start-ScheduledTask -TaskName $TaskName
    }
    $query = schtasks.exe /Query /TN $TaskName /FO LIST /V 2>&1
    $exists = $LASTEXITCODE -eq 0
}

$superseded4148 = Get-ScheduledTask -TaskName "TraderBrainL0BackfillWorkerRecovery4148" -ErrorAction SilentlyContinue
$payload = [ordered]@{
    task_id = "TASK-4195"
    generated_at = [DateTimeOffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    scheduler_task_name = $TaskName
    interval_minutes = $IntervalMinutes
    apply = [int][bool]$Apply
    registered = [int]$exists
    start_now = [int][bool]$StartNow
    project_root = $ProjectRoot
    wrapper_path = $WrapperPath
    diagnostic_only_flag = 1
    trade_authority_flag = 0
    broker_mutation_permitted_flag = 0
    live_order_permitted_flag = 0
    paper_promotion_permitted_flag = 0
    real_capital_permitted_flag = 0
    superseded_4148_state = if ($superseded4148) { $superseded4148.State.ToString() } else { "MISSING" }
    query_tail = ($query -join "`n")
}

$payload | ConvertTo-Json -Depth 5 | Set-Content -Path $ArtifactPath -Encoding UTF8
Write-Output ("TASK-4195 scheduler_registered={0} task_name={1} interval_minutes={2} superseded_4148_state={3}" -f ([int]$exists), $TaskName, $IntervalMinutes, $payload.superseded_4148_state)
