# Task883 Historical Evidence Source-Time Panel

## Decision Summary

- Verdict: planned.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Purpose: define the historical source-time panel needed to reconstruct what the Trader Brain knew at each decision date.

## Quant Expert Report

Required columns:

```text
evidence_id
source_family
symbol
theme
published_ts
received_ts
available_to_brain_ts
source_url_or_file
source_hash
primitive_candidate_state
source_gap_flag
```

The panel must block any evidence where `available_to_brain_ts` is after the decision timestamp.

## No-Background Decision-Maker Report

The brain cannot use news, filings, or facts that were not known yet. This task builds that historical knowledge boundary.

## Artifact Manifest

- Planned output: `historical_evidence_source_time_panel_contract.csv`.
- Validation command: `python scripts/trader_brain_881_890_historical_brain_backtest_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
