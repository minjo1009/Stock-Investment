# Task1748-1767 Pre-Entry Risk Budget

## Decision Summary

- Verdict: `preentry_risk_budget_implemented_diagnostic_only`.
- Best policy: `preentry_risk_budget_top3_v1`.
- Best final equity: 3088.6343.
- Best CAGR: 0.244229.
- Best MDD: -0.213011.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

| Policy | Final | CAGR | MDD | Base Final | Base MDD | Delta Final | Delta MDD | Trades | CAGR Target | MDD Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `preentry_risk_budget_top3_v1` | 3088.6343 | 0.244229 | -0.213011 | 3525.2985 | -0.32335 | -436.6642 | 0.110339 | 159 | 0 | 1 |
| `preentry_risk_budget_top5_v1` | 2533.6127 | 0.197378 | -0.142405 | 2638.334 | -0.286708 | -104.7213 | 0.144303 | 214 | 0 | 1 |

Split/OOS diagnostics:

| Policy | Window | Final | Return | MDD |
| --- | --- | ---: | ---: | ---: |
| `preentry_risk_budget_top3_v1` | IS_2021_2023 | 1952.7104 | 0.95271 | -0.213011 |
| `preentry_risk_budget_top3_v1` | OOS_2024_2026Q1 | 3088.6343 | 2.088634 | -0.181702 |
| `preentry_risk_budget_top5_v1` | IS_2021_2023 | 1641.5045 | 0.641504 | -0.142405 |
| `preentry_risk_budget_top5_v1` | OOS_2024_2026Q1 | 2533.6127 | 1.533613 | -0.11285 |

Attribution:

- `risk_budget_state`: full_size count=211 pnl= cagr= mdd=
- `risk_budget_state`: cluster_soft_cap count=92 pnl= cagr= mdd=
- `risk_budget_state`: quarter_size_preplanned_reduce count=38 pnl= cagr= mdd=
- `risk_budget_state`: new_candidate_quarter_size count=22 pnl= cagr= mdd=
- `risk_budget_state`: half_size_risk_budget count=10 pnl= cagr= mdd=
- `risk_budget_state`: no_entry count=4 pnl= cagr= mdd=
- `factor_cluster`: semis_growth_beta count=107 pnl= cagr= mdd=
- `factor_cluster`: cyclical_beta count=102 pnl= cagr= mdd=
- `factor_cluster`: mixed_other count=69 pnl= cagr= mdd=
- `factor_cluster`: speculative_growth count=45 pnl= cagr= mdd=
- `factor_cluster`: financial_beta count=44 pnl= cagr= mdd=
- `factor_cluster`: defensive_quality count=10 pnl= cagr= mdd=
- `state_pnl`: cluster_soft_cap count=92 pnl=1231.6555 cagr= mdd=
- `state_pnl`: full_size count=211 pnl=2295.1108 cagr= mdd=
- `state_pnl`: half_size_risk_budget count=10 pnl=-41.9984 cagr= mdd=
- `state_pnl`: new_candidate_quarter_size count=22 pnl=47.0304 cagr= mdd=
- `state_pnl`: quarter_size_preplanned_reduce count=38 pnl=90.448 cagr= mdd=
- `target_failure`: preentry_risk_budget_top3_v1 count= pnl= cagr=0.244229 mdd=-0.213011
- `target_failure`: preentry_risk_budget_top5_v1 count= pnl= cagr=0.197378 mdd=-0.142405

## No-Background Decision-Maker Report

1. Risk budget is assigned before entry.
2. The replay keeps Task1698 trade outcomes but changes initial sizing/no-entry only.
3. This tests whether firm-style pre-trade risk planning is better than late reduce.
4. The result remains diagnostic and does not approve strategy.

## Artifact Manifest

- `task1748_expert_review.csv`
- `task1750_preentry_risk_budget_panel.csv`
- `task1751_budget_action_panel.csv`
- `task1752_preentry_budget_replay_trades.csv/equity`
- `task1753_preentry_budget_replay_metrics.csv`
- `task1754_split_oos_metrics.csv`
- `task1755_failure_attribution.csv`
- `task1766_acceptance_gate.csv`
- `task1767_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1748_1767_preentry_risk_budget_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```