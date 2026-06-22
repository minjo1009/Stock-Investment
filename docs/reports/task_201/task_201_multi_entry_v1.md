# Task T201 - Multi-Entry Lifecycle Implementation

## Metrics
| Metric | Baseline | MULTI_ENTRY_V1 |
|---|---:|---:|
| trades | 45 | 238 |
| net_pnl | -534.126 | 88238.9298 |
| win_rate | 0.333333 | 0.605042 |
| avg_win | 182.7245 | 811.6859 |
| avg_loss | -109.1664 | -304.7217 |
| expectancy | -11.8695 | 370.7518 |
| profit_factor | 0.836908 | 4.080555 |

## Tranche Stats
- E1 hits: 85
- E2 hits: 41
- E3 hits: 44

## Notes
- R is risk budget: 1R = equity * risk_per_trade
- shares = tranche_risk_budget / stop_distance
