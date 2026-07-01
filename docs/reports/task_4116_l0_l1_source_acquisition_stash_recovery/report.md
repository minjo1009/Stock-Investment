# TASK-4116 L0/L1 Source Acquisition Stash Recovery

## Goal

Recover the notebook Codex L0/L1 source acquisition, DB loading, and automation
logic from `stash@{0}` without applying unrelated stash content.

## Result

Verdict: `PASS_FOR_SELECTIVE_RECOVERY`.

The useful work was found in `stash@{0}`. It was not missing. The current
worktree lacked most of the implementation because it was stored in the stash
created at `2026-06-29 12:48:38 +0900`.

Recovered surfaces:

- scheduler config and local override template
- L0 source registries for official releases, GDELT, Marketaux, and public news
- L0/L1 news normalization and readiness logic
- source acquisition modules under `tools/db/source_acquisition`
- runner/start scripts for L0 bar, news, public news, microstructure, and reference snapshots
- microstructure export/backfill support code
- Task646 microstructure backfill command plan and audit CSV evidence

Excluded surfaces:

- unrelated iOS/frontend work
- unrelated historical task code
- generated `data/**` payloads
- machine conflict `-DESKTOP-*` copies
- broker, order, live trading, paper promotion, and strategy-live paths

## Operator How-To Pointers

Primary entry points after recovery:

- status snapshot: `python scripts/report_l0_collection_status.py`
- conservative scheduler config: `configs/db_source_acquisition_scheduler.json`
- local override example: `configs/local_templates/db_source_acquisition_scheduler.override.example.json`
- DB scheduler launcher: `scripts/run_db_source_acquisition_scheduler.ps1`
- Windows task installer: `scripts/install_db_source_acquisition_scheduler_task.ps1`
- news collector: `scripts/run_l0_news_background_collector.py`
- public context/newswire/macro collectors: `scripts/run_l0_public_*`
- microstructure collector: `scripts/run_l0_microstructure_background_collector.py`
- microstructure backfill plan: `docs/reports/task_646_full_microstructure_data_lake/task_646_backfill_command_plan.csv`

## Validation Notes

Readiness validators pass after two recovery repairs:

- restored missing `src/data/env_loader.py`
- updated microstructure readiness validation to use current `ops/operating_state.yaml`
  instead of removed `docs/ownership/readiness_registry.yaml`
- made the source acquisition hardening audit path configurable so TASK-4116
  writes validation evidence into this task report folder instead of `data/**`

The effective scheduler config audit was written to:

`docs/reports/task_4116_l0_l1_source_acquisition_stash_recovery/effective_scheduler_config_audit.json`

The audit shows the existing local override is present and enables diagnostic
collection jobs with network access, while permission gates remain closed.

## Safety Boundary

- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- Broker mutation remains forbidden.
- Live order remains forbidden.
- Paper promotion remains forbidden unless explicitly accepted.
- Missing or stale data remains `UNKNOWN/BLOCKER`.
