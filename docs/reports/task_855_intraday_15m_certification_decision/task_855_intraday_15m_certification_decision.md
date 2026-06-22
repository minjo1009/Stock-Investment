# Task855 Intraday 15m Certification Decision

## Decision Summary

- Verdict: completed.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Data readiness: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- What changed: existing 15m files were classified as partial-no-replay due to mixed schema and missing session/adjustment certification.
- Next action: normalize exact schema or redownload affected slices after explicit approval.

## Quant Expert Report

15m certification cannot pass if timestamps cannot be mapped to session calendar or if required fields are silently filled.

Observed schemas:

- 146 files: `timestamp, open, high, low, close, volume`.
- 24 files: `timestamp, open, high, low, close, volume, trade_count, vwap`.

Decision:

- `us_intraday`: `redownload_required` until exact schema normalization, adjustment policy, and regular-session calendar are certified.

## No-Background Decision-Maker Report

This task decides whether intraday data is usable or only partly usable.

## Artifact Manifest

- Outputs: `data/artifacts/task_850_859_data_certification/schema_fingerprint_inventory.csv`, `coverage_gap_report.csv`, and `redownload_queue.csv`.
- Validation command: `python scripts/trader_brain_851_859_data_certification_validate.py`.
Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
