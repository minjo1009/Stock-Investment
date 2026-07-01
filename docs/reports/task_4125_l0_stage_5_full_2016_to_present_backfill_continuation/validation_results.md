# TASK-4125 Validation Results

## Latest Run

- Stage 5 status: `FULL_2016_TO_PRESENT_BACKFILL_COMPLETE`.
- Provider events: `115`.
- Raw files: `6103`.
- Observed rows: `498382`.
- Coverage complete: `5/5`.

## Required Validation

- `python -m compileall scripts/run_l0_stage5_full_backfill_continuation.py scripts/validate_l0_stage5_full_backfill_continuation.py`
- `python scripts/validate_l0_stage5_full_backfill_continuation.py`
- `python scripts/validate_l0_source_acquisition_project_management.py`
- `python scripts/ops/validate_task_registry.py`
- `python scripts/ops/validate_doc_registry.py --soft`
- `python scripts/ops/validate_required_artifacts.py --task TASK-4125`
- `python scripts/ops/validate_task_scope.py --task TASK-4125`

Closeout remains intentionally open until full 2016-to-present coverage completes and Stage 6 reaudit passes.

## Operator Notes

A combined Federal Register plus Guardian continuation attempt advanced saved collector state but exceeded the previous per-command 600 second runner timeout while Guardian was still running. The runner now records future timeouts as command-ledger failures instead of crashing, and reports can be regenerated from current task-scoped raw/artifact state without additional provider calls.
