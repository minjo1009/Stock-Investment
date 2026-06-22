# Task T093 - Capital-Based Portfolio Backtest

## 1. Summary
- strategy_id: D_PORTFOLIO_SECTOR_FILTER
- primary_scenario: A_BASE_10K_HIGH_COST
- final_capital: 11582.54
- total_return_pct: 15.825403
- max_drawdown_pct: 32.824341
- sharpe: 0.282975
- decision: FAIL

## 2. Scenario Comparison
| Scenario | Final Capital | Return % | MDD % | Sharpe | PF | Trades | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| A_BASE_10K_LOW_COST | 11898.73 | 18.9873 | 32.4745 | 0.292990 | 2.238228 | 39 | FAIL |
| A_BASE_10K_HIGH_COST | 11582.54 | 15.8254 | 32.8243 | 0.282975 | 1.947915 | 39 | FAIL |
| B_STRESS_1K_LOW_COST | 1127.98 | 12.7976 | 16.7835 | 0.233226 | 2.842741 | 18 | FAIL |
| B_STRESS_1K_HIGH_COST | 1118.67 | 11.8669 | 16.9002 | 0.221906 | 2.601131 | 18 | FAIL |

## 3. Equity Curve Analysis
- trade_points: 78
- daily_points: 1408
- recovery_comment: Equity curve is evaluated on trade events and daily resample; drawdown/recovery are capital-based.

## 4. Trade Distribution
- win_rate: 46.153846
- avg_trade_return_pct: 2.085104
- tail_risk_comment: Tail risk is assessed from realized trade distribution under constrained sizing and capped exposure.

## 5. Cost Impact
- pnl_before_cost: 1962.49
- pnl_after_cost: 1582.54
- cost_impact_pct: 19.360608

## 6. Risk Evaluation
- exposure_ratio: 0.299617
- capital_utilization: 0.325241
- skipped_trades: 0
- No dominant capital-failure mode detected in this scenario.

## 7. Failure Modes
- No dominant capital-failure mode detected in this scenario.

## 8. Decision
- status: FAIL
- answer: NO

## 9. Final Answer
Is the strategy profitable under realistic capital constraints? NO
