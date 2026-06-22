# Task T203 - Capital Accounting Consistency Repair

## Baseline vs Multi-entry (after reserve accounting)
| Metric | Baseline | Multi-entry |
|---|---:|---:|
| trade_count | 92 | 238 |
| net_pnl | 7174.1905 | 1608.9132 |
| win_rate | 0.554348 | 0.52521 |
| expectancy | 77.9803 | 6.7601 |
| profit_factor | 1.168271 | 1.047368 |
| mdd_pct | 12.18607 | 7.341967 |

## Validation
- baseline: {'negative_cash': False, 'capital_overlap_violation': False, 'same_bar_fill_violation': False, 'lookahead_violation': False}
- multi_entry_v1: {'negative_cash': False, 'capital_overlap_violation': False, 'same_bar_fill_violation': False, 'lookahead_violation': False}

## Final: DEGRADED EDGE
