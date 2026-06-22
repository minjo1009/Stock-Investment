# Task858 Market Calendar Corporate Action Plan

## Decision Summary

- Verdict: completed.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Data readiness: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- What changed: existing calendar and corporate-action readiness were audited.
- Next action: acquire or build certified calendar coverage and corporate-action source before replay.

## Quant Expert Report

Tradable-after timestamps require session calendar. Adjusted replay claims require split/dividend evidence or an explicitly accepted adjusted provider contract.

Audit:

- Existing `config/nasdaq_market_calendar.csv` covers 2026 holidays/early closes only.
- Required range starts `2021-01-01`; therefore calendar is blocked.
- No corporate-action source was found in expected raw paths.

## No-Background Decision-Maker Report

This task prevents future leakage and false adjusted-price claims.

## Artifact Manifest

- Outputs: `data/artifacts/task_850_859_data_certification/market_calendar_audit.csv` and `corporate_action_audit.csv`.
- Validation command: `python scripts/trader_brain_851_859_data_certification_validate.py`.
Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
