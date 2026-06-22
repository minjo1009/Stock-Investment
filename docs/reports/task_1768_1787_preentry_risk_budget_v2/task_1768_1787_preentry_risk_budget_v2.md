# Task1768-1787 Pre-Entry Risk Budget V2

## Decision Summary

- Verdict: `preentry_risk_budget_v2_implemented_diagnostic_only`.
- Best policy: `preentry_risk_budget_v2_top3_v1`.
- Best final equity: 3440.6109.
- Best CAGR: 0.270522.
- Best MDD: -0.289135.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

| Policy | Final | CAGR | MDD | Base Final | Base MDD | Delta Final | Delta MDD | Trades | CAGR Target | MDD Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `preentry_risk_budget_v2_top3_v1` | 3440.6109 | 0.270522 | -0.289135 | 3088.6343 | -0.213011 | 351.9766 | -0.076124 | 160 | 0 | 1 |
| `preentry_risk_budget_v2_top5_v1` | 2648.0462 | 0.207672 | -0.227907 | 2533.6127 | -0.142405 | 114.4335 | -0.085502 | 217 | 0 | 1 |

Split/OOS diagnostics:

| Policy | Window | Final | Return | MDD |
| --- | --- | ---: | ---: | ---: |
| `preentry_risk_budget_v2_top3_v1` | IS_2021_2023 | 1915.6558 | 0.915656 | -0.289135 |
| `preentry_risk_budget_v2_top3_v1` | OOS_2024_2026Q1 | 3440.6109 | 2.440611 | -0.183115 |
| `preentry_risk_budget_v2_top5_v1` | IS_2021_2023 | 1597.9485 | 0.597948 | -0.227907 |
| `preentry_risk_budget_v2_top5_v1` | OOS_2024_2026Q1 | 2648.0462 | 1.648046 | -0.121128 |

Attribution:

- `risk_budget_state_v2`: full_size_continuous count=234 pnl= cagr= mdd=
- `risk_budget_state_v2`: soft_cap_continuous count=61 pnl= cagr= mdd=
- `risk_budget_state_v2`: half_size_continuous count=48 pnl= cagr= mdd=
- `risk_budget_state_v2`: quarter_size_continuous count=34 pnl= cagr= mdd=
- `factor_cluster`: semis_growth_beta count=107 pnl= cagr= mdd=
- `factor_cluster`: cyclical_beta count=102 pnl= cagr= mdd=
- `factor_cluster`: mixed_other count=69 pnl= cagr= mdd=
- `factor_cluster`: speculative_growth count=45 pnl= cagr= mdd=
- `factor_cluster`: financial_beta count=44 pnl= cagr= mdd=
- `factor_cluster`: defensive_quality count=10 pnl= cagr= mdd=
- `state_pnl`: full_size_continuous count=234 pnl=3449.2209 cagr= mdd=
- `state_pnl`: half_size_continuous count=48 pnl=218.0335 cagr= mdd=
- `state_pnl`: quarter_size_continuous count=34 pnl=83.0492 cagr= mdd=
- `state_pnl`: soft_cap_continuous count=61 pnl=338.3551 cagr= mdd=
- `target_failure`: preentry_risk_budget_v2_top3_v1 count= pnl= cagr=0.270522 mdd=-0.289135
- `target_failure`: preentry_risk_budget_v2_top5_v1 count= pnl= cagr=0.207672 mdd=-0.227907

## No-Background Decision-Maker Report

1. V2 moves from coarse buckets to continuous pre-entry sizing.
2. It adds 63-day same-cluster correlation pressure.
3. It tries to restore return while keeping the MDD gain from Task1748.
4. The result remains diagnostic and does not approve strategy.

## Artifact Manifest

- `task1768_expert_review.csv`
- `task1770_preentry_risk_budget_v2_panel.csv`
- `task1771_budget_action_panel.csv`
- `task1772_preentry_budget_v2_replay_trades.csv/equity`
- `task1773_preentry_budget_v2_replay_metrics.csv`
- `task1774_split_oos_metrics.csv`
- `task1775_failure_attribution.csv`
- `task1786_acceptance_gate.csv`
- `task1787_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1768_1787_preentry_risk_budget_v2_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```