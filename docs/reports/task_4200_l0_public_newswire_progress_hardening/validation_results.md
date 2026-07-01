# TASK-4200 Validation Results

## Summary

| Check | Result |
|---|---|
| Python compile | PASS |
| Unit tests | PASS |
| BusinessWire day-shard dry run | PASS |
| Continuous guard one-shot | PASS |
| Public newswire aggregate | PASS |
| Public newswire validator | PASS_WITH_WARNINGS |
| L0 operating status | BLOCKED as expected |
| Codex closeout | PASS_WITH_WARNINGS |

## Commands

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m py_compile tools/db/source_acquisition/public_newswire_shards.py scripts/run_l0_public_newswire_sharded_backfill.py scripts/run_task4193_l0_overnight_backfill_supervisor.py scripts/aggregate_l0_public_newswire_shards.py tests/test_l0_public_newswire_sharded_backfill.py
```

Result: PASS.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest tests.test_l0_public_newswire_sharded_backfill
```

Result: PASS, 8 tests.

```powershell
python scripts/run_l0_public_newswire_sharded_backfill.py --start-month 2020-02 --end-month 2020-02 --sources businesswire --businesswire-shard-granularity day --shard-artifact-root data/artifacts/task_4200_l0_public_newswire_progress_hardening/dry_run_artifacts --shard-raw-root data/raw/task_4200_l0_public_newswire_progress_hardening/dry_run_raw --dry-run
```

Result: PASS. BusinessWire day granularity produced 29 units for 2020-02 and inherited legacy completed state.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_task4195_l0_continuous_backfill_guard_once.ps1
```

Result: PASS. Stale launcher config was restarted into the current config.

```powershell
python scripts/aggregate_l0_public_newswire_shards.py --skip-raw-dedupe
```

Result: PASS. Status RUNNING, progress 59.2704%.

```powershell
python scripts/validate_l0_public_newswire_sharded_backfill.py
```

Result: PASS_WITH_WARNINGS. Warning: `l1_unclassified_or_pending_count > 0`.

```powershell
python scripts/build_l0_operating_status_4190.py
```

Result: PASS command execution, overall status BLOCKED as expected because `L0_PUBLIC_NEWSWIRE_INCOMPLETE` remains open.

```powershell
python scripts/ops/validate_codex_closeout.py --task TASK-4200
```

Result: PASS_WITH_WARNINGS. Required task validators passed; warnings were existing project hygiene/internal cleanliness/task-scope dirty-file warnings.

## Current Snapshot

| Metric | Value |
|---|---:|
| progress_pct | 59.2704 |
| completed_units | 2356 |
| pending_units | 1619 |
| partial_units | 15 |
| failed_units | 0 |
| total_units | 3975 |

## Safety

No broker mutation, live order, paper promotion, real capital enablement, strategy acceptance, or deployment readiness claim was introduced.
