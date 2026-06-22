# Task889 Replay Harness Config Data Gate

## Decision Summary

- Verdict: planned.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Purpose: freeze replay harness config, market data gate, costs, slippage, and baselines.

## Quant Expert Report

Required config:

- replay period and split ids;
- calendar id;
- corporate action adjustment policy;
- daily and 15m data manifests;
- QQQ benchmark;
- cash handling;
- max positions;
- cost model;
- slippage model;
- trade delay;
- exit policy;
- artifact audit id.

No replay can start if any required data source is missing or reference-only.

## No-Background Decision-Maker Report

This stops the backtest from quietly changing assumptions after seeing results.

## Artifact Manifest

- Planned output: `replay_harness_config_data_gate.csv`.
- Validation command: `python scripts/trader_brain_881_890_historical_brain_backtest_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
