# Task866 Trade Spec Gap Contract

## Decision Summary

- Verdict: completed as blocker contract.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Key blocker: current dry adapter inputs do not contain symbol, side, entry policy, exit policy, or position size.
- Next action: create a controlled trade-spec contract before any strategy replay.

## Quant Expert Report

The trade-spec contract must add only explicitly approved fields. It must not create hidden ranking, scoring, inferred lifecycle matching, or future-return labels.

Required future fields:

```text
adapter_input_id
candidate_bundle_id
symbol
side
tradable_after_ts
entry_policy_id
exit_policy_id
position_policy_id
max_holding_policy_id
source_rule_id
```

## No-Background Decision-Maker Report

The brain has thesis bundles. It does not yet have trade rows. That missing bridge is now explicit.

## Artifact Manifest

- Output: `post_attempt_gap_diagnosis.csv`.
- Validation command: `python scripts/trader_brain_860_869_backtest_cycle_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`

