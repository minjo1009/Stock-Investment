# Task892 Repo Source-Time Bridge

## Decision Summary

- Verdict: implemented.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Purpose: prevent ambiguous repo source/evidence artifacts from entering the historical brain backtest.
- Accepted source-time rows: 0.
- Rejected source artifacts: all non-compliant Task891 inventory rows.
- First real historical brain replay: `no_go`.

## Quant Expert Report

Task891 found many source/evidence-like artifacts but no direct Task883-compliant raw historical source-time evidence. Task892 converts that diagnosis into a bridge gate:

- compliant rows go to `accepted_source_time_panel.csv`;
- non-compliant artifacts go to `rejected_source_artifact_ledger.csv`;
- rejection is not negative evidence;
- rejected artifacts may be revisited only through explicit row-level mapping.

This closes a dangerous gap: old candidate, event, or source-like files can no longer silently become historical brain evidence.

## No-Background Decision-Maker Report

The project has old evidence-like files, but they are not safe to use as historical brain inputs yet. This task blocks them cleanly instead of letting them leak into a backtest.

## Artifact Manifest

- Script: `scripts/trader_brain_892_repo_source_time_bridge.py`.
- Validator: `scripts/trader_brain_892_repo_source_time_bridge_validate.py`.
- Accepted panel: `data/artifacts/task_892_repo_source_time_bridge/accepted_source_time_panel.csv`.
- Rejection ledger: `data/artifacts/task_892_repo_source_time_bridge/rejected_source_artifact_ledger.csv`.
- Summary: `data/artifacts/task_892_repo_source_time_bridge/task_892_source_bridge_summary.json`.
- Validation command: `python scripts/trader_brain_892_repo_source_time_bridge_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
