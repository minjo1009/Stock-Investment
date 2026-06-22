# Task893 Source-Time Recovery

## Decision Summary

- Verdict: implemented.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: existing historical source-event data was no longer left as a rejected blob. Recoverable Task372 `SOURCE_CAPTURED` rows were normalized into a source-time panel.
- Recovered source-time rows: 139.
- Rejected event rows: 359.
- Covered symbols: 11.
- Covered symbols in the 10x7 universe: 8.
- Remaining source gap: `raw_external_document_missing`.
- Bridge authority: `diagnostic_recovered_internal_event_only`.
- First real historical brain replay: `no_go_until_external_source_or_owner_approved_internal_event_scope`.

## Quant Expert Report

Task891 diagnosed the AS-IS / TO-BE gap. Task892 blocked non-compliant artifacts from silently entering the brain backtest. Task893 implements the missing recovery step for the most relevant existing dataset:

- Input: `docs/reports/task_372_historical_source_backfill/task_372_historical_source_event_dataset.csv`.
- Recovered rows: only historical-period `SOURCE_CAPTURED` rows without synthetic lineage markers.
- Excluded rows: `REPLAY_DERIVED`, `SESSION_DERIVED`, harness fixtures, and period-outside rows.
- Join keys preserved: `source_event_id`, `symbol`, `event_timestamp`, `created_at`.
- Source-time fields produced: `published_ts`, `received_ts`, `available_to_brain_ts`.
- Leakage guard: `available_to_brain_ts` is the max of published and received timestamps, never earlier.
- Source hash: deterministic row-level hash over the original row and source file.

This does not turn internal events into external evidence. Each recovered row carries `source_gap_flag=raw_external_document_missing`, which forces the next layer to preserve the missing-source condition instead of pretending the raw document exists.

## No-Background Decision-Maker Report

The project did have usable historical timing material. The previous bridge correctly blocked unsafe files, but it did not yet recover the usable part. This task recovers 139 safe internal event rows and separates 359 unsafe rows.

This improves the pipeline because the brain layer now has a real source-time seed panel. It still does not approve a strategy, live trading, or a full historical backtest.

## Artifact Manifest

- Script: `scripts/trader_brain_893_source_time_recovery.py`.
- Validator: `scripts/trader_brain_893_source_time_recovery_validate.py`.
- Test: `tests/test_trader_brain_893_source_time_recovery.py`.
- Recovered panel: `data/artifacts/task_893_source_time_recovery/recovered_source_time_panel.csv`.
- Rejection ledger: `data/artifacts/task_893_source_time_recovery/rejected_event_source_rows.csv`.
- Backlog: `data/artifacts/task_893_source_time_recovery/source_time_recovery_backlog.csv`.
- Summary: `data/artifacts/task_893_source_time_recovery/task_893_source_time_recovery_summary.json`.
- Validation command: `python scripts/trader_brain_893_source_time_recovery_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
