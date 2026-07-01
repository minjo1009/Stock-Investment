# TASK-4159 Validation Results

| Command | Result | Notes |
|---|---|---|
| `python -m py_compile scripts/run_l0_public_newswire_sharded_backfill.py scripts/aggregate_l0_public_newswire_shards.py scripts/validate_l0_public_newswire_sharded_backfill.py` | PASS | launcher/aggregate/validator syntax checked |
| `python -m unittest tests.test_l0_public_newswire_sharded_backfill` | PASS | 6 tests |
| `python scripts/run_l0_public_newswire_sharded_backfill.py --start-month 2016-01 --end-month 2026-06 --sources businesswire,globenewswire,prnewswire --mode smoke --concurrency 4 --source-base-lanes businesswire=2,globenewswire=1,prnewswire=1 --source-lane-caps businesswire=4,globenewswire=1,prnewswire=1 --source-max-fetches businesswire=120,globenewswire=80,prnewswire=160 --source-max-items businesswire=150,globenewswire=150,prnewswire=200 --source-request-sleep-seconds businesswire=1.0,globenewswire=1.0,prnewswire=1.0 --source-max-worker-seconds businesswire=1800,globenewswire=1800,prnewswire=3600 --stale-progress-seconds 900 --dry-run` | PASS | controlled config accepted |
| `python scripts/aggregate_l0_public_newswire_shards.py --shard-artifact-root data/artifacts/l0_public_newswire_backfill_shards --shard-raw-root data/raw/l0_public_newswire_backfill_shards --legacy-artifact-root data/artifacts/l0_public_newswire_backfill --inventory-path data/artifacts/l0_public_newswire_backfill_shards/shard_inventory.json --out data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json --skip-raw-dedupe` | PASS | status RUNNING, progress 45.8912 |
| `python scripts/validate_l0_public_newswire_sharded_backfill.py --shard-artifact-root data/artifacts/l0_public_newswire_backfill_shards --shard-raw-root data/raw/l0_public_newswire_backfill_shards --inventory-path data/artifacts/l0_public_newswire_backfill_shards/shard_inventory.json --aggregate-progress data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json` | PASS | WARN only: `l1_unclassified_or_pending_count > 0` |
| `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_l0_public_newswire_sharded_progress_monitor.ps1 ... -MaxIterations 1` | PASS | latest monitor status says background_alive true |
| `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/control_l0_public_newswire_acceleration.ps1 ... -AllowBusinessWireCap4` | PASS | decision `BW4_BLOCKED`; blockers are GN incomplete and stable time below threshold |

Latest validation snapshot:

`data/artifacts/task_4159_l0_public_newswire_controlled_acceleration/validation_snapshots/validation_20260630T235921Z.txt`

```text
# L0 PUBLIC NEWSWIRE SHARDED BACKFILL VALIDATION
PASS shards_checked: 379
PASS unique_paths_seen: 1516
PASS safety_flags_closed
WARN l1_unclassified_or_pending_count > 0
RESULT: PASS
```

Latest controlled acceleration decision:

`data/artifacts/task_4159_l0_public_newswire_controlled_acceleration/controlled_acceleration_decision.json`

```text
decision: BW4_BLOCKED
reason: globenewswire_not_complete,stable_minutes_below_threshold
validator_passed: true
safety_closed: true
```
