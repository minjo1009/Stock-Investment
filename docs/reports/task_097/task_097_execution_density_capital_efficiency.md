# Task T097 - Execution Density & Capital Efficiency Analysis

## 1. Executive Summary
- 3-line summary: ['Sharpe bottleneck is primarily tied to sparse return path and capital underdeployment, not outright alpha collapse.', 'Current utilization is low (avg=0.298787) with many zero-return days (1366).', 'Blocked-trade profile does not indicate winner-overblocking dominance; constraint pressure is mixed with narrow opportunity set.']
- primary cause: Capital deployment inefficiency: low utilization with sparse return path compresses risk-adjusted returns.
- final classification: Mixed

## 2. Context Pack
- files inspected:
  - src/backtest/analysis_capital_backtest_093.py
  - src/backtest/analysis_capital_failure_review_093.py
  - src/backtest/analysis_risk_adoption_095.py
  - src/backtest/analysis_revalidation_096.py
  - src/backtest/analysis_sharpe_gap_review_096.py
  - src/backtest/analysis_sharpe_tuning_096_5.py
  - docs/reports/task_093/task_093_capital_backtest.json
  - docs/reports/task_093_review/task_093_review_failure_analysis.json
  - docs/reports/task_095/task_095_risk_adoption.json
  - docs/reports/task_096/task_096_revalidation.json
  - docs/reports/task_096_review/task_096_review_sharpe_gap.json
  - docs/reports/task_096_5/task_096_5_sharpe_tuning.json
- graphify usage note: Graphify full graph/report not loaded; fixed context pack only.

## 3. Trade Frequency Analysis
- total_trades: 37
- trades_per_year: 9.653036
- trades_per_month: 0.804486
- avg_days_between_trades: 38.888889
- longest_no_trade_period_days: 232
- active_trading_days_ratio: 0.024982

## 4. Capital Utilization Analysis
- average: 0.298787
- median: 0.0
- max: 1.0
- idle_days: 936
- zero_exposure_days: 936
- utilization_by_year: [{'year': 2022, 'avg_utilization': 0.118519}, {'year': 2023, 'avg_utilization': 0.443836}, {'year': 2024, 'avg_utilization': 0.309836}, {'year': 2025, 'avg_utilization': 0.27726}, {'year': 2026, 'avg_utilization': 0.285714}]

## 5. Sparse Return Path Analysis
- zero_return_days: 1366
- positive_days: 20
- negative_days: 14
- active_day_return: 0.004858
- inactive_day_drag: -0.00474
- daily_return_mean/std: 0.000118 / 0.002782

## 6. Opportunity Loss Analysis
- blocked_trades: 2
- blocked_winners: 0
- blocked_losers: 2
- net_block_effect: -148.9515
- blocked_reason_breakdown: {'LOSS_CLUSTER_BREAKER': 2}

## 7. Universe Constraint Analysis
- current_universe_size: 8
- symbols_with_trades: 3
- symbols_without_trades: 5
- sector_count: 2
- expansion_needed: True

## 8. Counterfactual Capital Deployment
| Scenario | Sharpe | Return % | MDD % | Note |
|---|---:|---:|---:|---|
| A_CURRENT_UTILIZATION | 0.673152 | 16.113361 | 2.790222 | Current adopted overlay output. |
| B_IGNORE_IDLE_CASH_SIGNALS_UNCHANGED | 0.558098 | 15.825403 | 3.950773 | No overlay gating/scaling; same trades from base list. |
| C_FULL_SLOT_WHEN_SIGNAL_EXISTS | 0.673152 | 16.113361 | 2.790222 | Relaxed concurrent/sector caps; same signal universe and risk breaker. |
| D_SIZE_UP_WITHIN_EXISTING_CAPS | 0.674804 | 17.724698 | 3.020076 | 10% sizing lift on accepted trades only (same signals, same blocking). |

## 9. Root Cause Map
- primary cause: Capital deployment inefficiency: low utilization with sparse return path compresses risk-adjusted returns.
- secondary causes:
  - Trade frequency is low enough to create long no-return stretches.
  - Universe concentration limits diversification of return streams.
- rejected hypotheses:
  - Risk overlay overblocking problem (blocked winners <= blocked losers).

## 10. Recommended Next Task
- task_id: T097.5
- title: Capital Deployment Simulation (No Alpha Change)
- objective: Run structured deployment simulations to increase active-day density and utilization without changing alpha logic or loosening overlay beyond validated safety bounds.

## 11. Final Answer
Sharpe remains below target mainly because low capital utilization and sparse active return days keep risk-adjusted compounding too thin despite drawdown control.
