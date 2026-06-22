# Task T093-REVIEW - Failure Analysis

## 1. Executive Summary
- primary_failure_reason: Drawdown clustering from repeated loss sequences under moderate exposure creates poor risk-adjusted returns.
- secondary_contributors: Loss-side volatility is too high relative to daily equity smoothness (Sharpe compression)., Concentration around a narrow sector set amplifies downside episodes., Capital efficiency is moderate, but return path variance dominates performance quality.

## 2. Drawdown Analysis
| Start | Trough | End | DD % | DD Amount | Duration(d) | Recovery(d) |
|---|---|---|---:|---:|---:|---:|
| 2024-01-02T00:00:00+00:00 | 2024-02-06T00:00:00+00:00 | 2025-08-21T00:00:00+00:00 | 32.8243 | 5173.7264 | 596 | 597 |
| 2025-10-10T00:00:00+00:00 | 2026-02-04T00:00:00+00:00 | None | 32.6101 | 5604.8115 | 117 | None |
| 2023-01-27T00:00:00+00:00 | 2023-02-09T00:00:00+00:00 | 2023-06-07T00:00:00+00:00 | 15.3638 | 1745.7244 | 130 | 131 |

## 3. Trade Distribution
- win_rate: 46.153846
- avg_win: 180.668651
- avg_loss: -79.499783
- skewness: 1.469513
- tail_loss_threshold_5pct: -118.74761

## 4. Loss Clustering
- loss_streak_max: 5
- {'start': '2022-04-06T00:00:00+00:00', 'end': '2022-12-20T00:00:00+00:00', 'length': 5, 'total_loss': -381.773}
- {'start': '2024-07-17T00:00:00+00:00', 'end': '2024-11-19T00:00:00+00:00', 'length': 5, 'total_loss': -273.9067}
- {'start': '2025-10-14T00:00:00+00:00', 'end': '2025-11-06T00:00:00+00:00', 'length': 3, 'total_loss': -357.8524}
- {'start': '2023-07-03T00:00:00+00:00', 'end': '2023-07-26T00:00:00+00:00', 'length': 2, 'total_loss': -128.6383}
- {'start': '2023-11-30T00:00:00+00:00', 'end': '2023-12-04T00:00:00+00:00', 'length': 2, 'total_loss': -223.9427}

## 5. Position Sizing Impact
- risk_per_trade_pct: 1.0
- max_position_size_pct: 30.0
- portfolio_max_exposure_pct: 100.0
- per_symbol_cap_pct: 30.0
- exposure_peak: 29.9617
- avg_notional: 1854.0179
- sizing_drawdown_proxy_corr: 0.983229

## 6. Portfolio Risk
- top3_symbol_notional_share: 1.0
- top_sector_notional_share: 1.0
- symbol_concentration_hhi: 0.389263
- max_concurrent_positions: 3
- avg_concurrent_positions: 1.24359
- symbol_exposure_table: [{'symbol': 'MSFT', 'notional': 36684.4291}, {'symbol': 'NVDA', 'notional': 23052.6263}, {'symbol': 'AMD', 'notional': 12569.6439}]
- sector_exposure_table: [{'sector': 'XLK', 'notional': 72306.6992}]

## 7. Capital Efficiency
- capital_utilization: 0.325241
- exposure_ratio: 0.299617
- idle_equity_day_ratio: 0.948864
- return_vs_exposure_corr_proxy: 0.045764
- data_note: Regime-tagged loss clustering by BULL/BEAR is unavailable in T093 payload; used temporal clusters instead.

## 8. Root Cause Map
- Primary Cause: Drawdown clustering from repeated loss sequences under moderate exposure creates poor risk-adjusted returns.
- Secondary Causes: ['Loss-side volatility is too high relative to daily equity smoothness (Sharpe compression).', 'Concentration around a narrow sector set amplifies downside episodes.', 'Capital efficiency is moderate, but return path variance dominates performance quality.']
- Minor Factors: ['Symbol-level concentration index is elevated.', 'Longest drawdown recovery is prolonged.', 'Observed loss streaks are long enough to induce behavioral/operational stress.']

## 9. Decision
- status: FAIL

## 10. Final Answer
- Clustered downside episodes with slow recovery dominate equity volatility, compressing Sharpe under capital constraints.
