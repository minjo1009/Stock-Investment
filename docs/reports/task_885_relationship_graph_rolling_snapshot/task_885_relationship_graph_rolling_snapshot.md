# Task885 Relationship Graph Rolling Snapshot

## Decision Summary

- Verdict: planned.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Purpose: define rolling relationship graph snapshots for each historical decision date.

## Quant Expert Report

Each snapshot must include:

- graph_snapshot_id;
- decision_asof_ts;
- node ids;
- edge ids;
- edge as-of timestamps;
- contradiction state;
- weakest layer;
- source gap count.

No snapshot may include an edge with `edge_asof_ts > decision_asof_ts`.

## No-Background Decision-Maker Report

This turns the brain from static notes into a time-aware relationship map. It is the core of using the brain like a trader.

## Artifact Manifest

- Planned output: `rolling_graph_snapshot_contract.csv`.
- Validation command: `python scripts/trader_brain_881_890_historical_brain_backtest_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
