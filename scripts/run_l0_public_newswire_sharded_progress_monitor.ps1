param(
  [string]$TaskId = "TASK-4157",
  [int]$IntervalSeconds = 3600,
  [int]$MaxIterations = 0,
  [string]$ShardArtifactRoot = "data/artifacts/l0_public_newswire_backfill_shards",
  [string]$ShardRawRoot = "data/raw/l0_public_newswire_backfill_shards",
  [string]$LegacyArtifactRoot = "data/artifacts/l0_public_newswire_backfill",
  [string]$TaskArtifactRoot = "data/artifacts/task_4157_l0_public_newswire_sharded_backfill",
  [switch]$EnableControlledAccelerationDecision
)

$ErrorActionPreference = "Continue"
$snapshotRoot = Join-Path $TaskArtifactRoot "progress_snapshots"
$validationRoot = Join-Path $TaskArtifactRoot "validation_snapshots"
$runtimeRoot = Join-Path $TaskArtifactRoot "runtime_logs"
New-Item -ItemType Directory -Force -Path $snapshotRoot, $validationRoot, $runtimeRoot | Out-Null

$monitorMetaPath = Join-Path $TaskArtifactRoot "progress_monitor_status.json"
$stopPath = Join-Path $ShardArtifactRoot "MONITOR_STOP"
$iteration = 0

while ($true) {
  $iteration += 1
  $stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
  $aggregatePath = Join-Path $ShardArtifactRoot "aggregate_progress.json"
  $snapshotPath = Join-Path $snapshotRoot "aggregate_progress_$stamp.json"
  $validationPath = Join-Path $validationRoot "validation_$stamp.txt"

  $aggregateArgs = @(
    "scripts/aggregate_l0_public_newswire_shards.py",
    "--shard-artifact-root", $ShardArtifactRoot,
    "--shard-raw-root", $ShardRawRoot,
    "--legacy-artifact-root", $LegacyArtifactRoot,
    "--inventory-path", (Join-Path $ShardArtifactRoot "shard_inventory.json"),
    "--out", $aggregatePath,
    "--skip-raw-dedupe"
  )
  & python @aggregateArgs | Tee-Object -FilePath (Join-Path $runtimeRoot "monitor_aggregate_$stamp.log")
  if (Test-Path $aggregatePath) {
    Copy-Item -Force -Path $aggregatePath -Destination $snapshotPath
  }

  $validateArgs = @(
    "scripts/validate_l0_public_newswire_sharded_backfill.py",
    "--shard-artifact-root", $ShardArtifactRoot,
    "--shard-raw-root", $ShardRawRoot,
    "--inventory-path", (Join-Path $ShardArtifactRoot "shard_inventory.json"),
    "--aggregate-progress", $aggregatePath
  )
  & python @validateArgs *>&1 | Tee-Object -FilePath $validationPath

  $controllerDecisionPath = Join-Path $TaskArtifactRoot "controlled_acceleration_decision.json"
  $controllerPath = "scripts/control_l0_public_newswire_acceleration.ps1"
  if ($EnableControlledAccelerationDecision -and (Test-Path $controllerPath)) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $controllerPath `
      -TaskId $TaskId `
      -ShardArtifactRoot $ShardArtifactRoot `
      -ShardRawRoot $ShardRawRoot `
      -LegacyArtifactRoot $LegacyArtifactRoot `
      -TaskArtifactRoot $TaskArtifactRoot `
      -AllowBusinessWireCap4 *>&1 | Tee-Object -FilePath (Join-Path $runtimeRoot "monitor_controller_$stamp.log")
  }

  $backgroundPid = $null
  $backgroundAlive = $false
  $backgroundProcessPath = Join-Path $ShardArtifactRoot "background_process.json"
  if (Test-Path $backgroundProcessPath) {
    try {
      $backgroundPid = (Get-Content $backgroundProcessPath | ConvertFrom-Json).pid
      $backgroundAlive = [bool](Get-Process -Id $backgroundPid -ErrorAction SilentlyContinue)
    } catch {
      $backgroundAlive = $false
    }
  }

  $status = [ordered]@{
    schema_version = "l0_public_newswire_sharded_progress_monitor_v1"
    task_id = $TaskId
    updated_at = (Get-Date).ToUniversalTime().ToString("o")
    iteration = $iteration
    interval_seconds = $IntervalSeconds
    aggregate_progress_path = $aggregatePath
    latest_snapshot_path = $snapshotPath
    latest_validation_path = $validationPath
    controlled_acceleration_decision_path = $controllerDecisionPath
    background_pid = $backgroundPid
    background_alive = $backgroundAlive
    diagnostic_only_flag = 1
    trade_authority_flag = 0
    broker_mutation_permitted_flag = 0
    real_capital_permitted_flag = 0
  }
  $status | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 -Path $monitorMetaPath

  if ((Test-Path $stopPath) -or (($MaxIterations -gt 0) -and ($iteration -ge $MaxIterations))) {
    break
  }
  Start-Sleep -Seconds $IntervalSeconds
}
