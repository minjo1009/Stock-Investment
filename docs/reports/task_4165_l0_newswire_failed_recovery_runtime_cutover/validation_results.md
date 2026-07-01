# TASK-4165 Validation Results

## Result

`PASS`

## Commands

| Command | Result |
|---|---|
| `python -m pytest tests/test_l0_public_newswire_collector.py -q` | PASS, 26 passed |
| `python scripts/aggregate_l0_public_newswire_shards.py --skip-raw-dedupe` | PASS, aggregate written |
| `python scripts/validate_l0_public_newswire_sharded_backfill.py` | PASS, warning only for pending/unclassified L1 rows |
| `python scripts/validate_l0_l2_wide_handoff_4146.py` | PASS |
| `python scripts/ops/validate_task_registry.py` | PASS |
| `python scripts/ops/validate_doc_registry.py --soft` | PASS |
| `python scripts/ops/validate_required_artifacts.py --task TASK-4165` | PASS |
| `python scripts/ops/validate_task_scope.py --task TASK-4165` | PASS_WITH_WARNINGS |
| `python scripts/ops/validate_codex_closeout.py --task TASK-4165` | PASS_WITH_WARNINGS |

## Key Checks

| Check | Result |
|---|---|
| public newswire hard failed units | PASS, `0` |
| sharded newswire launcher alive | PASS, PID `16236` |
| PRNewswire source max bytes applied | PASS, `prnewswire=50000000` |
| legacy public newswire recovery restart disabled | PASS |
| L1/L2 handoff reads sharded newswire event ledgers | PASS |
| L1/L2 handoff validator accepts sharded launcher runtime proof | PASS |
| trading authority opened | PASS, `0` |
| paper/live/broker/order opened | PASS, `0` |

## Warnings

| Warning | Meaning |
|---|---|
| `l1_unclassified_or_pending_count > 0` | Some L0 rows remain review/pending, which is expected while backfill continues. This is not a trading signal and not negative evidence. |
| `dirty files outside task manifest ignored for scope gate` | The repository already has many unrelated dirty files. TASK-4165 scope validator ignored files outside the task manifest and confirmed forbidden paths stayed clean. |

## Current Evidence

| Artifact | Path |
|---|---|
| recovery ledger | `data/artifacts/task_4165_l0_newswire_failed_recovery_runtime_cutover/failed_shard_recovery_ledger.csv` |
| recovery summary | `data/artifacts/task_4165_l0_newswire_failed_recovery_runtime_cutover/failed_shard_recovery_summary.json` |
| newswire aggregate | `data/artifacts/l0_public_newswire_backfill_shards/aggregate_progress.json` |
| sharded launcher status | `data/artifacts/l0_public_newswire_backfill_shards/background_process.json` |
| L1/L2 validator report | `data/artifacts/task_4146_l0_l2_wide_packetization_handoff/validator_report.json` |
