# Task2521-2530 KIS Cost-Aware Guard Feasibility

## Decision Summary

- Verdict: `return_preserving_mdd_repair_not_found_in_preregistered_variants`.
- Best guard: `kis_guard_drawdown25_portfolio_stress_cap80_v1`.
- Best final equity: 5977.726633.
- Best CAGR: 0.42227189.
- Best MDD: -0.29935367.
- Return-preserving MDD success: `0`.
- Selector changed: `0`.
- Strategy tuning performed: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Recent source context:

- Research Affiliates (2024-01): Volatility targeting is primarily a stability/risk-control overlay, not a return enhancement promise.
- Frontiers in Applied Mathematics and Statistics (2025): Transaction costs should be incorporated into portfolio construction because frequent rebalancing can materially reduce net performance.
- AQR (2025): Testing many drawdown/dip variants creates data-mining risk; guard variants should be preregistered and judged conservatively.
- Transaction-cost-aware Factors (2024): Gross returns can favor high-turnover or costly trades; net cost-aware decision rules are more relevant.

Expert review summary:

- `risk_parity_portfolio_construction_reviewer`: Drawdown control can improve ride quality, but expecting no return cost is too strong. Require non-inferior CAGR, not guaranteed improvement.
- `systematic_execution_cost_reviewer`: The guard must separate commission drag from SEC fee and should avoid high-turnover thin-edge exposure during stress.
- `overfit_governance_reviewer`: Because the problematic window is known, any successful variant is diagnostic until OOS/PIT gates are rerun.

Guard replay metrics:

- `kis_guard_none_baseline_v1`: final 6016.930785, CAGR 0.42410471, MDD -0.30814728, triggered 0, success 0.
- `kis_guard_drawdown20_monthly_overtrade_cap_v1`: final 6016.930785, CAGR 0.42410471, MDD -0.30814728, triggered 0, success 0.
- `kis_guard_drawdown20_monthly_costrate_cap_v1`: final 6016.930785, CAGR 0.42410471, MDD -0.30814728, triggered 0, success 0.
- `kis_guard_drawdown20_trade_costrate_cap_v1`: final 6016.930785, CAGR 0.42410471, MDD -0.30814728, triggered 0, success 0.
- `kis_guard_drawdown25_cost_intensity_cap_v1`: final 6016.930785, CAGR 0.42410471, MDD -0.30814728, triggered 0, success 0.
- `kis_guard_drawdown15_portfolio_stress_cap90_v1`: final 5940.83189, CAGR 0.42053821, MDD -0.29962299, triggered 38, success 0.
- `kis_guard_drawdown20_portfolio_stress_cap80_v1`: final 5781.521816, CAGR 0.41295145, MDD -0.2910987, triggered 26, success 0.
- `kis_guard_drawdown25_portfolio_stress_cap80_v1`: final 5977.726633, CAGR 0.42227189, MDD -0.29935367, triggered 6, success 0.

This is a diagnostic feasibility test. It does not prove deployability because PIT/as-of source certification and forward paper-trading evidence are still missing.

## No-Background Decision-Maker Report

Conclusion first: no return-preserving MDD repair was found among the preregistered diagnostic guards.

But this is not approval. The tested guards either did not trigger or reduced return while improving drawdown. The next repair should improve selection quality or add a true ex-ante bad-trade filter, not simply de-risk the whole book.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2521_2530_kis_cost_aware_guard_feasibility/`.
- Validator: `python scripts/trader_brain_2521_2530_kis_cost_aware_guard_feasibility_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
