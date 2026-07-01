param(
  [string]$TaskId = "TASK-4159",
  [string]$ShardArtifactRoot = "data/artifacts/l0_public_newswire_backfill_shards",
  [string]$ShardRawRoot = "data/raw/l0_public_newswire_backfill_shards",
  [string]$LegacyArtifactRoot = "data/artifacts/l0_public_newswire_backfill",
  [string]$TaskArtifactRoot = "data/artifacts/task_4159_l0_public_newswire_controlled_acceleration",
  [switch]$AllowBusinessWireCap4,
  [switch]$Apply,
  [int]$StableMinutesRequired = 120
)

$ErrorActionPreference = "Stop"

function Read-Json($Path) {
  if (-not (Test-Path $Path)) {
    return $null
  }
  return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

function Process-Alive($PidValue) {
  if (-not $PidValue) {
    return $false
  }
  return [bool](Get-Process -Id $PidValue -ErrorAction SilentlyContinue)
}

$runtimeRoot = Join-Path $TaskArtifactRoot "runtime_logs"
New-Item -ItemType Directory -Force -Path $runtimeRoot | Out-Null
$aggregatePath = Join-Path $ShardArtifactRoot "aggregate_progress.json"
$inventoryPath = Join-Path $ShardArtifactRoot "shard_inventory.json"
$backgroundPath = Join-Path $ShardArtifactRoot "background_process.json"

& python scripts/aggregate_l0_public_newswire_shards.py `
  --shard-artifact-root $ShardArtifactRoot `
  --shard-raw-root $ShardRawRoot `
  --legacy-artifact-root $LegacyArtifactRoot `
  --inventory-path $inventoryPath `
  --out $aggregatePath `
  --skip-raw-dedupe | Out-Null

$validationText = & python scripts/validate_l0_public_newswire_sharded_backfill.py `
  --shard-artifact-root $ShardArtifactRoot `
  --shard-raw-root $ShardRawRoot `
  --inventory-path $inventoryPath `
  --aggregate-progress $aggregatePath 2>&1
$validationPassed = ($LASTEXITCODE -eq 0)

$aggregate = Read-Json $aggregatePath
$background = Read-Json $backgroundPath
$backgroundAlive = Process-Alive $background.pid
$bySource = $aggregate.by_source
$gnPending = [int]$bySource.globenewswire.pending_units
$bwPending = [int]$bySource.businesswire.pending_units
$prPending = [int]$bySource.prnewswire.pending_units
$failedShardCount = @($aggregate.failed_shards).Count
$staleWorkerCount = @($aggregate.stale_workers).Count
$activeWorkers = @($aggregate.active_workers)
$activeBySource = @{}
foreach ($worker in $activeWorkers) {
  $source = [string]$worker.source
  if (-not $activeBySource.ContainsKey($source)) {
    $activeBySource[$source] = 0
  }
  $activeBySource[$source] += 1
}

$currentConcurrency = [int]$background.concurrency
$currentBwCap = [int]$background.source_lane_caps.businesswire
$stableStartedAt = $null
$stableMinutes = 0
try {
  $stableStartedAt = [DateTimeOffset]::Parse([string]$background.started_at)
  $stableMinutes = [int](([DateTimeOffset]::UtcNow - $stableStartedAt).TotalMinutes)
} catch {
  $stableMinutes = 0
}

$safety = $aggregate.safety
$safetyClosed = (
  ([int]$safety.broker_mutation_count -eq 0) -and
  ([int]$safety.order_count -eq 0) -and
  ([int]$safety.live_order_count -eq 0) -and
  ([int]$safety.paper_promotion_count -eq 0) -and
  ([int]$safety.real_capital_flag_count -eq 0) -and
  ([int]$safety.trade_authority_count -eq 0)
)

$canPromoteBw4 = (
  $AllowBusinessWireCap4.IsPresent -and
  $validationPassed -and
  $backgroundAlive -and
  $safetyClosed -and
  ($gnPending -eq 0) -and
  ($bwPending -gt 0) -and
  ($prPending -gt 0) -and
  ($currentConcurrency -lt 5) -and
  ($stableMinutes -ge $StableMinutesRequired)
)

$decision = "NO_CHANGE"
$reason = "controlled baseline remains active"
if ($gnPending -eq 0 -and $currentConcurrency -eq 4) {
  $decision = "DYNAMIC_REBALANCE_EXPECTED"
  $reason = "GlobeNewswire pending is zero; launcher should naturally allocate returned lane to BusinessWire up to current concurrency"
}
if ($AllowBusinessWireCap4.IsPresent -and -not $canPromoteBw4) {
  $decision = "BW4_BLOCKED"
  $blocked = @()
  if (-not $validationPassed) { $blocked += "validator_failed" }
  if (-not $backgroundAlive) { $blocked += "launcher_not_alive" }
  if (-not $safetyClosed) { $blocked += "safety_not_closed" }
  if ($gnPending -ne 0) { $blocked += "globenewswire_not_complete" }
  if ($currentConcurrency -ge 5) { $blocked += "already_concurrency_5_or_higher" }
  if ($stableMinutes -lt $StableMinutesRequired) { $blocked += "stable_minutes_below_threshold" }
  $reason = ($blocked -join ",")
}
if ($canPromoteBw4) {
  $decision = "BW4_PROMOTION_READY"
  $reason = "all safety and stability gates cleared"
}

$status = [ordered]@{
  schema_version = "l0_public_newswire_controlled_acceleration_decision_v1"
  task_id = $TaskId
  updated_at = [DateTimeOffset]::UtcNow.ToString("o")
  apply_requested = [int]$Apply.IsPresent
  allow_businesswire_cap4 = [int]$AllowBusinessWireCap4.IsPresent
  decision = $decision
  reason = $reason
  aggregate_status = $aggregate.status
  progress_pct = $aggregate.progress_pct
  completed_units = $aggregate.completed_units
  pending_units = $aggregate.pending_units
  by_source_pending = [ordered]@{
    businesswire = $bwPending
    globenewswire = $gnPending
    prnewswire = $prPending
  }
  active_workers_by_source = $activeBySource
  failed_shard_count = $failedShardCount
  stale_worker_count = $staleWorkerCount
  stable_minutes = $stableMinutes
  background_pid = $background.pid
  background_alive = $backgroundAlive
  current_concurrency = $currentConcurrency
  current_businesswire_cap = $currentBwCap
  validator_passed = $validationPassed
  safety_closed = $safetyClosed
  diagnostic_only_flag = 1
  trade_authority_flag = 0
  broker_mutation_permitted_flag = 0
  real_capital_permitted_flag = 0
}

$statusPath = Join-Path $TaskArtifactRoot "controlled_acceleration_decision.json"
$status | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path $statusPath

if ($Apply.IsPresent -and $canPromoteBw4) {
  $stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
  $stopPath = Join-Path $ShardArtifactRoot "STOP"
  New-Item -ItemType File -Force -Path $stopPath | Out-Null
  Start-Sleep -Seconds 10
  if ($background.pid) {
    Stop-Process -Id $background.pid -Force -ErrorAction SilentlyContinue
  }
  Remove-Item -LiteralPath $stopPath -Force -ErrorAction SilentlyContinue
  $stdout = Join-Path $runtimeRoot "launcher_bw4_$stamp.stdout.log"
  $stderr = Join-Path $runtimeRoot "launcher_bw4_$stamp.stderr.log"
  $launcherArgs = @(
    "scripts/run_l0_public_newswire_sharded_backfill.py",
    "--start-month", "2016-01",
    "--end-month", "2026-06",
    "--sources", "businesswire,globenewswire,prnewswire",
    "--mode", "stable",
    "--concurrency", "5",
    "--schedule-strategy", "source_round_robin",
    "--source-base-lanes", "businesswire=3,globenewswire=0,prnewswire=1",
    "--source-lane-caps", "businesswire=4,globenewswire=0,prnewswire=1",
    "--source-max-fetches", "businesswire=120,globenewswire=80,prnewswire=160",
    "--source-max-items", "businesswire=150,globenewswire=150,prnewswire=200",
    "--source-request-sleep-seconds", "businesswire=1.0,globenewswire=1.0,prnewswire=1.0",
    "--source-max-worker-seconds", "businesswire=1800,globenewswire=1800,prnewswire=3600",
    "--stale-progress-seconds", "900",
    "--max-recycles-per-shard", "2",
    "--poll-seconds", "5"
  )
  $launcher = Start-Process -FilePath "python" -ArgumentList $launcherArgs -WorkingDirectory (Get-Location) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru -WindowStyle Hidden
  $backgroundMeta = [ordered]@{
    schema_version = "l0_public_newswire_sharded_launcher_process_v4"
    task_id = $TaskId
    supersedes_task_id = "TASK-4159"
    provider = "public_newswire_feeds"
    pid = $launcher.Id
    started_at = [DateTimeOffset]::UtcNow.ToString("o")
    mode = "stable_controlled_bw4"
    concurrency = 5
    schedule_strategy = "source_round_robin_dynamic_rebalance"
    source_base_lanes = [ordered]@{ businesswire = 3; globenewswire = 0; prnewswire = 1 }
    source_lane_caps = [ordered]@{ businesswire = 4; globenewswire = 0; prnewswire = 1 }
    source_max_fetches = [ordered]@{ businesswire = 120; globenewswire = 80; prnewswire = 160 }
    source_max_items = [ordered]@{ businesswire = 150; globenewswire = 150; prnewswire = 200 }
    request_sleep_seconds = [ordered]@{ businesswire = 1.0; globenewswire = 1.0; prnewswire = 1.0 }
    source_max_worker_seconds = [ordered]@{ businesswire = 1800; globenewswire = 1800; prnewswire = 3600 }
    stale_progress_seconds = 900
    stdout_path = $stdout
    stderr_path = $stderr
    inventory_path = "data/artifacts/l0_public_newswire_backfill_shards/shard_inventory.json"
    aggregate_progress_path = "data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json"
    stop_path = "data/artifacts/l0_public_newswire_backfill_shards/STOP"
    diagnostic_only_flag = 1
    trade_authority_flag = 0
    broker_mutation_permitted_flag = 0
    real_capital_permitted_flag = 0
  }
  $backgroundMeta | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path $backgroundPath
  $status["applied_launcher_pid"] = $launcher.Id
  $status["decision"] = "BW4_PROMOTION_APPLIED"
  $status | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path $statusPath
}

$status | ConvertTo-Json -Depth 8
