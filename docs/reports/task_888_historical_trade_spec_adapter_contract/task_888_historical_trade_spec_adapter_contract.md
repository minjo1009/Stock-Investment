# Task888 Historical Trade-Spec Adapter Contract

## Decision Summary

- Verdict: planned.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Purpose: convert historical brain decisions into trade specs without hidden inference.

## Quant Expert Report

Required trade-spec fields:

```text
trade_spec_id
decision_id
candidate_bundle_id
graph_snapshot_id
symbol
side
decision_asof_ts
tradable_after_ts
entry_policy_id
exit_policy_id
position_policy_id
allocated_capital
blocked_reason
```

If symbol, side, timing, or position cannot be produced by the policy contract, the row must be blocked.

## No-Background Decision-Maker Report

This is the bridge from brain decision to replay input. It must be explicit.

## Artifact Manifest

- Planned output: `historical_trade_spec_adapter_contract.csv`.
- Validation command: `python scripts/trader_brain_881_890_historical_brain_backtest_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
