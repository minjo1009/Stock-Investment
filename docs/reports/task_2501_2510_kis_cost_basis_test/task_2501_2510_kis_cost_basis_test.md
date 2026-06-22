# Task2501-2510 KIS Cost Basis Test

## Decision Summary

- Verdict: `kis_cost_passes_return_but_fails_mdd_gate`.
- Cost basis: Korea Investment Securities US online commission 0.25% buy, 0.25% sell, SEC Fee 0.00206% on sell.
- Repriced policy: `kis_cost_repriced_exit_chain_repaired_soft_boost_cap_top2_v1`.
- Final equity: 6016.930785.
- CAGR: 0.42410471.
- MDD: -0.30814728.
- OOS CAGR: 0.63358875.
- OOS MDD: -0.17175083.
- Joint target met: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Cost contract:

- Buy commission rate: 0.0025.
- Sell commission rate: 0.0025.
- Sell SEC Fee rate: 2.06e-05.
- Simple roundtrip bps: 50.206.
- Embedded Task2381 roundtrip bps: 20.0.
- Source: https://www.truefriend.com/main/bond/research/_static/TF03ca050000.jsp.
- SEC Fee notice: https://m.truefriend.com/main/bond/research/Guide04.jsp?cmd=TF03ca040002&num=10795.

Segment metrics:

- `IS_2021_2023`: CAGR 0.32758547, MDD -0.30814728, final 2336.672507.
- `VALIDATION_2024`: CAGR 0.39940686, MDD -0.09032509, final 3269.203486.
- `OOS_2025_2026Q1`: CAGR 0.63358875, MDD -0.17175083, final 6016.930785.

Acceptance checks:

- `kis_full_period_cagr_30pct`: pass 1, KIS-cost full-period CAGR must remain >= 30%.
- `kis_full_period_mdd_minus30pct`: pass 0, KIS-cost full-period MDD must remain >= -30%.
- `kis_oos_cagr_30pct`: pass 1, KIS-cost OOS CAGR must remain >= 30%.
- `kis_oos_mdd_minus30pct`: pass 1, KIS-cost OOS MDD must remain >= -30%.
- `strategy_status_unchanged`: pass 1, Cost test must not change acceptance/deployment/real-capital status.

This is a current KIS forward-cost diagnostic applied to the frozen historical replay. It does not certify historical fee vintages, paper readiness, broker truth, or live deployment.

## No-Background Decision-Maker Report

Conclusion first: KIS cost does not kill CAGR, but it pushes MDD past the -30% line.

The strategy still earns strongly after KIS official online cost assumptions, but realistic broker cost makes drawdown control weaker. That means the next repair should focus on cost-aware MDD/risk control, not more return chasing.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2501_2510_kis_cost_basis_test/`.
- Validator: `python scripts/trader_brain_2501_2510_kis_cost_basis_test_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
