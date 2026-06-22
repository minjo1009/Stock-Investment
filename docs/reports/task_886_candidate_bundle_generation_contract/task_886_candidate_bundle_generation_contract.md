# Task886 Candidate Bundle Generation Contract

## Decision Summary

- Verdict: planned.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Purpose: define how historical candidate bundles are generated from rolling graph snapshots.

## Quant Expert Report

Candidate bundles may include:

- candidate_bundle_id;
- graph_snapshot_id;
- theme;
- candidate symbols;
- thesis;
- confirmation evidence;
- contradiction evidence;
- invalidation rule;
- uncertainty state;
- bundle_asof_ts.

Candidate bundles are not trades. They do not contain price targets, realized returns, ranks, or final position size.

## No-Background Decision-Maker Report

This is where the brain forms a thesis. It still does not buy anything.

## Artifact Manifest

- Planned output: `candidate_bundle_generation_contract.csv`.
- Validation command: `python scripts/trader_brain_881_890_historical_brain_backtest_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
