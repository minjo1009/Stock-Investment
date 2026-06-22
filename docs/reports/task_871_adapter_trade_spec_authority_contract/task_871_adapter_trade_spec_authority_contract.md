# Task871 Adapter Trade-Spec Authority Contract

## Decision Summary

- Verdict: executed as controlled trade-spec authority.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Problem: current adapter input has no `symbol`, `side`, `entry`, `exit`, or `position_size`.
- Clarification: this was intentional in Task830/836 because dry adapter input was not allowed to create trades.
- Fix: create a separate controlled trade-spec layer with explicit authority, inputs, and blockers.

## Quant Expert Report

Allowed future trade-spec fields:

```text
trade_spec_id
adapter_input_id
candidate_bundle_id
source_graph_id
symbol
side
tradable_after_ts
entry_policy_id
exit_policy_id
position_policy_id
max_holding_policy_id
benchmark_id
initial_capital
source_rule_id
validation_authority
blocked_reason
```

Forbidden:

- inferred lifecycle matching;
- symbol/date/price/time proximity fallback;
- side from future return;
- position size from score/rank/PnL;
- missing label as negative;
- GPT-only symbol or side decision;
- implicit buy/sell jump from source text.

Authority rule:

```text
candidate bundle may justify a trade-spec candidate only through an explicit bundle-to-symbol policy and explicit side policy.
```

## No-Background Decision-Maker Report

The missing fields are not an accident in the code. They are the next layer. This task defines how those fields can be added safely.

Execution update:

- `controlled_trade_specs.csv` was produced in `data/artifacts/task_870_879_full_controlled_replay/`.
- Required fields now exist: `symbol`, `side`, `tradable_after_ts`, `entry_policy_id`, `exit_policy_id`, `position_policy_id`, and `allocated_capital`.
- The fields remain diagnostic only and do not create acceptance or deployment readiness.

## Artifact Manifest

- Output: `trade_spec_authority_contract.csv`.
- Execution output: `data/artifacts/task_870_879_full_controlled_replay/controlled_trade_specs.csv`.
- Validation command: `python scripts/trader_brain_870_879_full_replay_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
