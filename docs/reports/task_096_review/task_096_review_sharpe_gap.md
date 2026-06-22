# Task T096-REVIEW - Sharpe Gap Attribution

## 1. Executive Summary
- 3-line summary:
  - overlay Sharpe improved to 0.673152 but missed target 0.7 by 0.0268.
  - primary cause: Return generation remains lumpy (many zero-return days) while residual negative-day volatility stays high, so the mean/std balance is still below the Sharpe 0.7 threshold.
  - secondary causes: Loss clustering improved but not eliminated: negative streaks still persist after overlay., Decorrelation + light loss breaker reduces utilization, limiting smooth compounding days., Volatility contribution remains concentrated in a few symbols, creating equity-curve noise.

## 2. Graphify Context Pack
- communities_used: [{'community_id': 1, 'label': 'Paper Ops / Evidence Loop'}, {'community_id': 10, 'label': 'Backtest Analytics / Task Reports'}, {'community_id': 13, 'label': 'Backtest Analytics / Task Reports'}, {'community_id': 22, 'label': 'Backtest Analytics / Task Reports'}]
- files_inspected_count: 15
- god_nodes_noted: [{'id': 'src_backtest_engine_full_py', 'label': 'engine_full.py', 'source_file': 'src\\backtest\\engine_full.py', 'degree': 30, 'external_reference': False}, {'id': 'engine_full_run_full_backtest_universe_with_stats', 'label': 'run_full_backtest_universe_with_stats()', 'source_file': 'src\\backtest\\engine_full.py', 'degree': 26, 'external_reference': False}, {'id': 'engine_full_run_full_backtest_with_stats', 'label': 'run_full_backtest_with_stats()', 'source_file': 'src\\backtest\\engine_full.py', 'degree': 24, 'external_reference': False}]
- excluded_areas: ['src/app (broker runtime path)', 'src/integration (KIS adapter)', 'tests/fixtures/kis/real raw responses', 'live/paper execution scripts']

## 3. Baseline vs Overlay Snapshot
| Metric | Baseline | Overlay | Delta |
|---|---:|---:|---:|
| Return % | 15.825403 | 16.113361 | 0.287958 |
| MDD % | 3.950773 | 2.790222 | -1.160551 |
| Sharpe | 0.558098 | 0.673152 | 0.115054 |
| Annualized Volatility | 0.053254 | 0.044163 | -0.009091 |
| Trade Count | 39 | 37 | -2 |
| Capital Utilization | 0.325241 | 0.233147 | -0.092094 |

## 4. Daily Return Volatility Analysis
- mean_daily_return: 0.000118
- daily_std: 0.002782
- annualized_volatility: 0.044163
- positive_days: 20
- negative_days: 14
- zero_return_days: 1366
- worst_day: -0.027902
- best_day: 0.059204

## 5. Sparse Profit / Capital Utilization Analysis
- active_days: 465
- idle_days: 936
- utilization_ratio: 0.331906
- zero_return_days: 1366

## 6. Residual Loss Clustering
- max_negative_streak: 1
- drawdown_clusters: [{'start': '2026-02-04T00:00:00+00:00', 'trough': '2026-02-04T00:00:00+00:00', 'end': None, 'duration_days': 0, 'recovery_days': None, 'drawdown_pct': 2.790222, 'drawdown_amount': 333.281296}, {'start': '2024-01-03T00:00:00+00:00', 'trough': '2024-01-03T00:00:00+00:00', 'end': '2024-02-06T00:00:00+00:00', 'duration_days': 34, 'recovery_days': 62, 'drawdown_pct': 2.189091, 'drawdown_amount': 240.937709}, {'start': '2024-07-17T00:00:00+00:00', 'trough': '2024-10-31T00:00:00+00:00', 'end': '2025-07-01T00:00:00+00:00', 'duration_days': 349, 'recovery_days': 460, 'drawdown_pct': 1.503652, 'drawdown_amount': 171.189111}, {'start': '2022-08-08T00:00:00+00:00', 'trough': '2022-12-16T00:00:00+00:00', 'end': '2023-02-23T00:00:00+00:00', 'duration_days': 199, 'recovery_days': 323, 'drawdown_pct': 1.344065, 'drawdown_amount': 133.008905}, {'start': '2023-11-30T00:00:00+00:00', 'trough': '2023-12-04T00:00:00+00:00', 'end': '2023-12-06T00:00:00+00:00', 'duration_days': 6, 'recovery_days': 9, 'drawdown_pct': 1.216061, 'drawdown_amount': 133.836737}]

## 7. Symbol-Level Attribution
| Symbol | Return | Return % | Vol % | DD Loss % | Trades |
|---|---:|---:|---:|---:|---:|
| NVDA | 1483.149492 | 92.044698 | 58.749648 | 29.789761 | 13 |
| MSFT | 242.15766 | 15.028376 | 23.377544 | 32.639428 | 15 |
| AMD | -113.971001 | -7.073074 | 17.872808 | 37.570811 | 9 |

## 8. Sector-Level Attribution
| Sector | Return | Return % | Vol % | DD Loss % | Trades |
|---|---:|---:|---:|---:|---:|
| XLK | 1611.336151 | 100.0 | 100.0 | 100.0 | 37 |

## 9. Trade Payoff Distribution
- trade_count: 37
- win_rate: 48.648649
- avg_win: 153.850825
- avg_loss: -60.946247
- payoff_ratio: 2.524369
- tail_loss_count: 2
- tail_win_count: 2
- skewness: 2.130031

## 10. Overlay Side Effects
- blocked_entries_count=2, blocked_by_reason={'LOSS_CLUSTER_BREAKER': 2}
- blocked_trades=2, blocked_winners=0, blocked_losers=2, blocked_avg_pnl=-74.47575
- return_change=0.287958%, mdd_change=-1.160551%, sharpe_change=0.115054
- trade_count_change=-2, capital_utilization_change=-0.092094

## 11. Root Cause Map
- Primary Cause: Return generation remains lumpy (many zero-return days) while residual negative-day volatility stays high, so the mean/std balance is still below the Sharpe 0.7 threshold.
- Secondary Causes:
  - Loss clustering improved but not eliminated: negative streaks still persist after overlay.
  - Decorrelation + light loss breaker reduces utilization, limiting smooth compounding days.
  - Volatility contribution remains concentrated in a few symbols, creating equity-curve noise.
- Minor Factors:
  - Blocked-trade logic removed both losers and some winners, muting net Sharpe lift.
  - Single-sector concentration risk remains present in selected universe slices.

## 12. Next Task Recommendation
- task_id: T096.5
- objective: Sharpe gap closure test via non-alpha smoothing diagnostics (same strategy/signal), focusing on return path regularity and residual volatility concentration.
- acceptance_criteria:
  - Sharpe >= 0.70 while preserving MDD <= T096 overlay MDD + 0.3%
  - No increase in max negative daily streak
  - No degradation in T092 alignment (must remain PASS)
  - Blocked-winner ratio does not exceed blocked-loser ratio by more than 10%

## 13. Final Answer
Sharpe stayed below 0.7 because residual return-path lumpiness and remaining downside volatility still outweigh the overlay-driven drawdown reduction.
