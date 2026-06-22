# Task1698-1717 L2/L4 Bad-Trade Gate

## Decision Summary

- Verdict: `l2_l4_bad_trade_gate_implemented_diagnostic_only`.
- Best policy: `bad_trade_gate_top3_v1`.
- Best final equity: 3525.2985.
- Best CAGR: 0.276522.
- Best MDD: -0.32335.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

| Policy | Final | CAGR | MDD | Base Final | Base MDD | Delta Final | Delta MDD | Trades | Hold | Reduce | Exit | Beats Base | QQQ Beat | CAGR Target | MDD Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bad_trade_gate_top3_v1` | 3525.2985 | 0.276522 | -0.32335 | 2740.1193 | -0.2539 | 785.1792 | -0.06945 | 160 | 90 | 41 | 29 | 0 | 1 | 0 | 0 |
| `bad_trade_gate_top5_v1` | 2638.334 | 0.206812 | -0.286708 | 2054.2962 | -0.236762 | 584.0378 | -0.049946 | 217 | 137 | 47 | 33 | 0 | 1 | 0 | 1 |

Split/OOS diagnostics:

| Policy | Window | Final | Return | MDD |
| --- | --- | ---: | ---: | ---: |
| `bad_trade_gate_top3_v1` | IS_2021_2023 | 1901.5913 | 0.901591 | -0.32335 |
| `bad_trade_gate_top3_v1` | OOS_2024_2026Q1 | 3525.2985 | 2.525298 | -0.181702 |
| `bad_trade_gate_top5_v1` | IS_2021_2023 | 1560.7613 | 0.560761 | -0.286708 |
| `bad_trade_gate_top5_v1` | OOS_2024_2026Q1 | 2638.334 | 1.638334 | -0.122011 |

## No-Background Decision-Maker Report

1. The gate is implemented as one frozen policy family, not a broad parameter search.
2. L2 now separates terminal/listing/dilution risk from ordinary or theme volatility.
3. L4 now preserves baseline winners unless a severe pre-entry risk or much stronger payoff candidate appears.
4. L5 now exits only on thesis-break evidence, not isolated price noise.
5. This remains diagnostic and does not approve strategy.

## Failure / Blocker Summary

- `collapse_risk_bucket`: ordinary_pass count=2465 cagr= mdd= delta_final=
- `collapse_risk_bucket`: terminal_business_risk count=427 cagr= mdd= delta_final=
- `collapse_risk_bucket`: ordinary_volatility count=179 cagr= mdd= delta_final=
- `collapse_risk_bucket`: dilution_pressure count=15 cagr= mdd= delta_final=
- `collapse_risk_bucket`: theme_volatility count=14 cagr= mdd= delta_final=
- `pre_entry_gate`: allow count=2658 cagr= mdd= delta_final=
- `pre_entry_gate`: block count=427 cagr= mdd= delta_final=
- `pre_entry_gate`: cap count=15 cagr= mdd= delta_final=
- `payoff_quality_bucket`: low_payoff_candidate count=1856 cagr= mdd= delta_final=
- `payoff_quality_bucket`: blocked_terminal_or_listing_risk count=427 cagr= mdd= delta_final=
- `payoff_quality_bucket`: watch_or_cap_candidate count=354 cagr= mdd= delta_final=
- `payoff_quality_bucket`: eligible_payoff_candidate count=239 cagr= mdd= delta_final=
- `payoff_quality_bucket`: top3_payoff_candidate count=224 cagr= mdd= delta_final=
- `selection_reason`: baseline_preserved count=345 cagr= mdd= delta_final=
- `selection_reason`: high_confidence_open_slot_filled_by_payoff_rank count=32 cagr= mdd= delta_final=
- `runtime_action`: hold count=227 cagr= mdd= delta_final=
- `runtime_action`: reduce count=88 cagr= mdd= delta_final=
- `runtime_action`: exit count=62 cagr= mdd= delta_final=
- `target_or_baseline_failure`: bad_trade_gate_top3_v1 count= cagr=0.276522 mdd=-0.32335 delta_final=785.1792
- `target_or_baseline_failure`: bad_trade_gate_top5_v1 count= cagr=0.206812 mdd=-0.286708 delta_final=584.0378

## Artifact Manifest

- `task1698_expert_review.csv`
- `task1699_collapse_risk_v2_panel.csv`
- `task1700_payoff_quality_v2_panel.csv`
- `task1701_risk_payoff_mechanism_edges.csv`
- `task1702_top3_top5_candidate_compressor.csv`
- `task1703_thesis_break_action_panel.csv`
- `task1704_bad_trade_gate_replay_trades.csv/equity`
- `task1705_bad_trade_gate_replay_metrics.csv`
- `task1706_split_oos_metrics.csv`
- `task1707_failure_attribution.csv`
- `task1716_acceptance_gate.csv`
- `task1717_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1698_1717_l2_l4_bad_trade_gate_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```