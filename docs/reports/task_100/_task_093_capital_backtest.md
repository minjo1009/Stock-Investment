# Task T093 - Capital-Based Portfolio Backtest

## 1. Summary
- strategy_id: D_PORTFOLIO_SECTOR_FILTER
- primary_scenario: A_BASE_10K_HIGH_COST
- final_capital: 11365.66
- total_return_pct: 13.656615
- max_drawdown_pct: 34.164099
- sharpe: 0.282787
- decision: FAIL

## 2. Scenario Comparison
| Scenario | Final Capital | Return % | MDD % | Sharpe | PF | Trades | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| A_BASE_10K_LOW_COST | 11719.25 | 17.1925 | 33.2853 | 0.292396 | 1.953686 | 45 | FAIL |
| A_BASE_10K_HIGH_COST | 11365.66 | 13.6566 | 34.1641 | 0.282787 | 1.693698 | 45 | FAIL |
| B_STRESS_1K_LOW_COST | 1116.48 | 11.6482 | 16.9253 | 0.202823 | 2.477201 | 22 | FAIL |
| B_STRESS_1K_HIGH_COST | 1105.22 | 10.5224 | 17.0961 | 0.191316 | 2.230880 | 22 | FAIL |

## 3. Equity Curve Analysis
- trade_points: 90
- daily_points: 1431
- recovery_comment: Equity curve is evaluated on trade events and daily resample; drawdown/recovery are capital-based.

## 4. Trade Distribution
- win_rate: 42.222222
- avg_trade_return_pct: 1.539796
- tail_risk_comment: Tail risk is assessed from realized trade distribution under constrained sizing and capped exposure.

## 5. Cost Impact
- pnl_before_cost: 1813.72
- pnl_after_cost: 1365.66
- cost_impact_pct: 24.703923

## 6. Risk Evaluation
- exposure_ratio: 0.289568
- capital_utilization: 0.314907
- skipped_trades: 0
- No dominant capital-failure mode detected in this scenario.

## 7. Failure Modes
- No dominant capital-failure mode detected in this scenario.

## 8. Decision
- status: FAIL
- answer: NO

## 9. Final Answer
Is the strategy profitable under realistic capital constraints? NO
