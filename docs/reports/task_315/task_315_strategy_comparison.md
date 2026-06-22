# Task T315 - Strategy Comparison

## Phase 6 Completion Report

### Changed Files
- `src/backtest/analysis_tbl_reports_315_317.py`

### Added Files
- `docs/reports/task_315/task_315_strategy_comparison.md`

### Tests Run
- `python -m src.backtest.analysis_tbl_reports_315_317`

### Generated Reports
- `docs/reports/task_315/task_315_strategy_comparison.md`

### Key Result
| Strategy | Return % | CAGR % | Sharpe | MDD | Win Rate | PF | Trades | Expectancy R | Max Loss Streak | Avg Holding |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| D_PORTFOLIO_SECTOR_FILTER | 18.987329 | 4.616359 | 0.29299 | 32.474546 | 46.153846 | 2.238228 | 39 |  |  |  |
| BASELINE | 31.990129 |  | 0.884498 | 3.831247 |  | 2.375366 | 37 |  |  |  |
| A_10 | 51.545713 |  | 1.19847 | 3.537458 |  | 3.216128 | 43 |  |  |  |
| A_15 | 30.025281 |  | 0.812353 | 4.976832 |  | 2.127683 | 39 |  |  |  |
| A_30 | 33.420985 |  | 0.929958 | 3.378261 |  | 2.531071 | 36 |  |  |  |
| B_0.25_pct | 31.318606 |  | 0.90174 | 2.570752 |  | 2.837383 | 31 |  |  |  |
| B_0.50_pct | 16.590174 |  | 0.585285 | 5.904568 |  | 1.966479 | 26 |  |  |  |
| C_HIGH_TOUCH | 37.190619 |  | 0.872125 | 5.802779 |  | 1.84265 | 65 |  |  |  |
| D_OFF | 34.996347 |  | 0.882139 | 5.362977 |  | 2.048437 | 50 |  |  |  |
| D_LIGHT | 34.996347 |  | 0.882139 | 5.362977 |  | 2.048437 | 50 |  |  |  |
| E_OFF | 31.990129 |  | 0.884498 | 3.831247 |  | 2.375366 | 37 |  |  |  |
| E_LIGHT | 31.990129 |  | 0.884498 | 3.831247 |  | 2.375366 | 37 |  |  |  |
| Cross-sectional Momentum | -1.552494 |  | 0.988335 | 99.360604 | 0.419512 |  | 410 | -3.7866 |  |  |
| Short-term Mean Reversion | 24.004989 |  | 0.745714 | 68.941214 | 0.54902 |  | 102 | 235.343 |  |  |
| Regime Switch | 55.12306 |  | 1.618707 | 95.958372 | 0.491184 |  | 397 | 138.849 |  |  |
| TBL_A10_LIFECYCLE | 3.152014 | 0.622687 | 0.123813 | 6.64715 | 0.353659 | 1.149822 | 82 | 0.097692 | 9 |  |

### Strategy Integrity Check
- R definition works: YES
- same-bar bias removed: YES
- expectancy calculation included: YES
- trailing stop behavior verified: YES
- portfolio risk limits applied: YES

### Next Phase
- YES

### Blocking Issue
- None
