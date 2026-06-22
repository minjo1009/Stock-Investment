# Task1788-1807 Winner Defense Budget

## Decision Summary

- Verdict: `winner_defense_budget_implemented_diagnostic_only`.
- Best policy: `winner_defense_budget_top3_v1`.
- Best final equity: 3920.9554.
- Best CAGR: 0.303105.
- Best MDD: -0.314619.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

| Policy | Final | CAGR | MDD | Base Final | Base MDD | Delta Final | Delta MDD | Trades | CAGR Target | MDD Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `winner_defense_budget_top3_v1` | 3920.9554 | 0.303105 | -0.314619 | 3440.6109 | -0.289135 | 480.3445 | -0.025484 | 160 | 1 | 0 |
| `winner_defense_budget_top5_v1` | 2960.4142 | 0.234049 | -0.247497 | 2648.0462 | -0.227907 | 312.368 | -0.01959 | 215 | 0 | 1 |

Split/OOS diagnostics:

| Policy | Window | Final | Return | MDD |
| --- | --- | ---: | ---: | ---: |
| `winner_defense_budget_top3_v1` | IS_2021_2023 | 2015.5753 | 1.015575 | -0.314619 |
| `winner_defense_budget_top3_v1` | OOS_2024_2026Q1 | 3920.9554 | 2.920955 | -0.189598 |
| `winner_defense_budget_top5_v1` | IS_2021_2023 | 1680.9806 | 0.680981 | -0.247497 |
| `winner_defense_budget_top5_v1` | OOS_2024_2026Q1 | 2960.4142 | 1.960414 | -0.127638 |

Attribution:

- `volatility_cause`: ordinary_noise count=203 pnl= cagr= mdd=
- `volatility_cause`: normal_winner_volatility count=86 pnl= cagr= mdd=
- `volatility_cause`: leader_momentum_volatility count=74 pnl= cagr= mdd=
- `volatility_cause`: market_beta_selloff count=5 pnl= cagr= mdd=
- `volatility_cause`: issuer_specific_expectation_break count=4 pnl= cagr= mdd=
- `volatility_cause`: terminal_or_financing_thesis_risk count=4 pnl= cagr= mdd=
- `volatility_cause`: company_specific_drawdown count=1 pnl= cagr= mdd=
- `winner_defense_bucket`: qualified_winner_defense count=114 pnl= cagr= mdd=
- `winner_defense_bucket`: strong_winner_defense count=111 pnl= cagr= mdd=
- `winner_defense_bucket`: ordinary_defense count=89 pnl= cagr= mdd=
- `winner_defense_bucket`: weak_or_no_defense count=63 pnl= cagr= mdd=
- `factor_cluster`: semis_growth_beta count=107 pnl= cagr= mdd=
- `factor_cluster`: cyclical_beta count=102 pnl= cagr= mdd=
- `factor_cluster`: mixed_other count=69 pnl= cagr= mdd=
- `factor_cluster`: speculative_growth count=45 pnl= cagr= mdd=
- `factor_cluster`: financial_beta count=44 pnl= cagr= mdd=
- `factor_cluster`: defensive_quality count=10 pnl= cagr= mdd=
- `bucket_pnl`: ordinary_defense count=89 pnl=-212.993 cagr= mdd=
- `bucket_pnl`: qualified_winner_defense count=114 pnl=1052.1732 cagr= mdd=
- `bucket_pnl`: strong_winner_defense count=111 pnl=3264.7527 cagr= mdd=
- `bucket_pnl`: weak_or_no_defense count=61 pnl=777.4364 cagr= mdd=
- `target_failure`: winner_defense_budget_top3_v1 count= pnl= cagr=0.303105 mdd=-0.314619
- `target_failure`: winner_defense_budget_top5_v1 count= pnl= cagr=0.234049 mdd=-0.247497

## No-Background Decision-Maker Report

1. V3 adds winner defense before risk-budget sizing.
2. It separates normal winner volatility from terminal or issuer-specific damage.
3. It lets high-quality winners regain size only when payoff, expectation, absorption, and relative strength support it.
4. Survival, financing, dilution, and terminal risk cannot be overridden by winner defense.
5. The result remains diagnostic and does not approve strategy.

## Artifact Manifest

- `task1788_expert_review.csv`
- `task1790_winner_defense_panel.csv`
- `task1791_winner_defense_action_panel.csv`
- `task1792_winner_defense_replay_trades.csv/equity`
- `task1793_winner_defense_replay_metrics.csv`
- `task1794_split_oos_metrics.csv`
- `task1795_failure_attribution.csv`
- `task1806_acceptance_gate.csv`
- `task1807_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1788_1807_winner_defense_budget_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```