# Validation Results - TASK-4193

## Passed

- `python -m py_compile scripts/run_task4193_l0_overnight_backfill_supervisor.py scripts/validate_task4193_l0_overnight_backfill_supervisor.py`
- `python scripts/validate_task4193_l0_overnight_backfill_supervisor.py`
  - supervisor PID alive: `16040`
  - public newswire PID alive: `21952`
  - market/macro PID alive: `20296`
  - 5m bar PID alive: `2088`
- `python scripts/validate_l0_l2_hardening_4147.py`
- `python scripts/ops/validate_prime_task_contracts.py --task TASK-4193`
- `python scripts/ops/validate_task_registry.py`
- `python scripts/ops/validate_required_artifacts.py --task TASK-4193`

## Passed With Warnings

- `python scripts/ops/validate_doc_registry.py --soft`
- `python scripts/ops/validate_task_scope.py --task TASK-4193`
- `python scripts/ops/validate_codex_closeout.py --task TASK-4193`

## Warning Meaning

- Existing dirty files outside the TASK-4193 manifest were ignored by the scope gate.
- Existing unregistered TASK-4194 markdown files were already present outside this task.
- TASK-4193 forbidden paths were clean.

## Verdict

`PASS_WITH_WARNINGS`
