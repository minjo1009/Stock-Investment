# Validation Results - TASK-4117

| Command | Result | Notes |
|---|---|---|
| `python -m compileall -q scripts/report_l0_collection_status.py scripts/validate_l0_source_acquisition_project_management.py tools/db/source_acquisition/l0_collection_status.py` | PASS | Syntax/package compile check passed. |
| `python scripts/validate_l0_source_acquisition_project_management.py` | PASS_WITH_WARNINGS | Project-management invariants passed. Warnings: three restored OneDrive files are not locally materialized before execution. |
| `python scripts/report_l0_collection_status.py --status-json docs/reports/task_4117_l0_source_acquisition_project_management_integration/l0_collection_status.json --status-md docs/reports/task_4117_l0_source_acquisition_project_management_integration/l0_collection_status.md` | PASS | Generated status snapshot; active task TASK-4117 and next stage 1 reported. |
| `python scripts/ops/validate_task_registry.py` | PASS | Task registry shape and profiles valid. |
| `python scripts/ops/validate_doc_registry.py --strict` | PASS | New docs registered; pre-existing unregistered docs classified as UNKNOWN/HISTORICAL/SUPERSEDED. |
| `python scripts/ops/validate_required_artifacts.py --task TASK-4117` | PASS | Required report, manifest, and validation artifacts exist. |
| `python scripts/ops/validate_task_scope.py --task TASK-4117` | PASS_WITH_WARNINGS | Scope passed and forbidden paths clean. Git status/diff had OneDrive mmap warnings. |
| `python scripts/ops/validate_codex_closeout.py --task TASK-4117` | PASS_WITH_WARNINGS | Closeout passed after registry flags were closed. Remaining warning is task scope git status/diff mmap noise under OneDrive. |

## Warnings

- OneDrive local materialization warnings remain for:
  - `tools/db/source_acquisition/public_newswire_collector.py`
  - `tools/db/source_acquisition/public_market_macro_news_collector.py`
  - `configs/source_registry/l0_public_news_capability_sources.json`
- These are execution-readiness blockers for those specific collectors until the
  files are materialized locally. They are not negative evidence about source
  availability.
- `git status` still reports `fatal: mmap failed: Invalid argument` under
  OneDrive; task scope validator still passed with forbidden paths clean.
