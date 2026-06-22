# Task856 Microstructure Scope Decision

## Decision Summary

- Verdict: completed.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Data readiness: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- What changed: Alpaca SIP parquet is classified as reference-only/research-only and excluded from first controlled replay common inputs.
- Next action: use only in later narrow slippage diagnostics after daily+15m replay is stable.

## Quant Expert Report

Current Alpaca SIP parquet has strong provider/feed/type/symbol/date/chunk partitioning, but only AFRM and AMD were observed and historical flags do not support live-ready claims.

Observed coverage:

- quotes: 24,649 parquet files, AFRM/AMD, `2024-01-02` to `2026-06-03`.
- trades: 4,353 parquet files, AFRM/AMD, `2024-01-02` to `2026-05-19`.
- observed sample flags: `receive_time_available_flag=0`, `historical_live_ready_flag=0`.

## No-Background Decision-Maker Report

This task prevents tick data from making the first replay too complex too early.

## Artifact Manifest

- Outputs: `data/artifacts/task_850_859_data_certification/microstructure_readiness_audit.csv`.
- Validation command: `python scripts/trader_brain_851_859_data_certification_validate.py`.
Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
