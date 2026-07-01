# Validation Results - TASK-4195

## Passed

- `python -m py_compile scripts/run_task4193_l0_overnight_backfill_supervisor.py scripts/validate_task4195_l0_continuous_backfill_guard.py scripts/build_l0_operating_status_4190.py`
- `python scripts/validate_task4195_l0_continuous_backfill_guard.py`
  - `TraderBrainL0ContinuousBackfillGuard4195` exists, enabled, `Last Result=0`
  - `TraderBrainL0BackfillWorkerRecovery4148` disabled
  - `Task3893OfficialBackfillAutoLoop` disabled
  - `Task3899FullOfficialBackfillWorker` disabled
  - `Task3899FullOfficialBackfillProgressReport` disabled
  - public newswire, market/macro, and 5m collector PIDs alive
  - safety flags closed
- `python scripts/build_l0_operating_status_4190.py --contract ops/l0_operating_contract.yaml`
- `python scripts/ops/validate_task_registry.py`
- `python scripts/ops/validate_prime_task_contracts.py --task TASK-4195`
- `python scripts/ops/validate_required_artifacts.py --task TASK-4195`

## Passed With Warnings

- `python scripts/ops/validate_doc_registry.py --soft`
- `python scripts/ops/validate_task_scope.py --task TASK-4195`
- `PYTHONDONTWRITEBYTECODE=1 python scripts/ops/validate_codex_closeout.py --task TASK-4195`

## Warning Meaning

- Existing dirty files outside the TASK-4195 manifest were ignored by the scope gate.
- Existing unregistered task_4196 markdown files were already present outside this task.
- Existing root machine-conflict DB remains blocked for owner review.
- TASK-4195 forbidden paths were clean.

## Verdict

`PASS_WITH_WARNINGS`
