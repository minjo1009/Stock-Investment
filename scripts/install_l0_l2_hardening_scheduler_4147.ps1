param(
    [string]$TaskName = "TraderBrainL0L2Hardening4147",
    [int]$IntervalMinutes = 15,
    [switch]$StartNow
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runner = Join-Path $projectRoot "scripts/run_l0_l2_hardening_once_4147.ps1"
$proofPath = Join-Path $projectRoot "data/artifacts/task_4147_l0_l2_hardening_gpt_review_and_implementation/windows_task_scheduler_registration.json"

if (-not (Test-Path $runner)) {
    throw "Missing TASK-4147 runner: $runner"
}

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$runner`" -ProjectRoot `"$projectRoot`""

$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
    -RepetitionDuration (New-TimeSpan -Days 3650)
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
    -Description "Runs TASK-4147 L0-L2 hardening refresh every 15 minutes. Diagnostic-only; no signal, order, broker, paper/live, or real-capital authority." `
    -Force | Out-Null

if ($StartNow) {
    Start-ScheduledTask -TaskName $TaskName
}

$task = Get-ScheduledTask -TaskName $TaskName
$proof = [ordered]@{
    task_id = "TASK-4147"
    task_name = $TaskName
    status = "REGISTERED"
    registered_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    interval_minutes = $IntervalMinutes
    runner = $runner
    project_root = $projectRoot
    task_state = $task.State.ToString()
    diagnostic_only_flag = 1
    trade_authority_flag = 0
    broker_mutation_permitted_flag = 0
    real_capital_permitted_flag = 0
}

$proofDir = Split-Path -Parent $proofPath
if (-not (Test-Path $proofDir)) {
    New-Item -ItemType Directory -Path $proofDir -Force | Out-Null
}
$proof | ConvertTo-Json -Depth 5 | Set-Content -Path $proofPath -Encoding UTF8
$proof
