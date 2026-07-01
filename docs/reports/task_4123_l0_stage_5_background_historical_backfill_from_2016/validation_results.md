# TASK-4123 Validation Results

## Summary

Result: PASS_WITH_WARNINGS

Stage 5 bounded background historical backfill proof passed. Warnings are from
existing OneDrive/git mmap or reparse-point behavior observed by governance
scope validation, including unreadable start-script reparse paths outside the
active Stage 5 runner path.

## Commands

| Command | Result |
|---|---|
| `python scripts/ops/validate_task_registry.py` | PASS |
| `python scripts/ops/validate_doc_registry.py --soft` | PASS |
| `python -m compileall scripts/run_l0_stage5_background_backfill.py scripts/validate_l0_stage5_background_backfill.py scripts/run_task646_full_microstructure_backfill.py tools/db/source_acquisition/public_market_macro_news_collector.py tools/db/source_acquisition/public_newswire_collector.py` | PASS |
| `python scripts/run_l0_stage5_background_backfill.py` | PASS; 3 commands, 2 events, 6 raw files |
| `python scripts/validate_l0_stage5_background_backfill.py` | PASS |
| `python scripts/validate_l0_source_acquisition_project_management.py` | PASS |
| `python scripts/ops/validate_task_scope.py --task TASK-4123` | PASS_WITH_WARNINGS |
| `python scripts/ops/validate_required_artifacts.py --task TASK-4123` | PASS |
| `python scripts/ops/validate_codex_closeout.py --task TASK-4123` | PASS_WITH_WARNINGS |

## Proof Facts

- `stage5_status`: `BACKGROUND_HISTORICAL_BACKFILL_BOUNDED_PROOF_EXECUTED`
- Bounded background collection started: 1
- Persistent process left running: 0
- Full 2016-to-present run completed: 0
- Commands: 3
- Source events: 2
- Raw files: 6
- Event rows: 2
- Secret failures: 0
- DB mutation: 0

Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
