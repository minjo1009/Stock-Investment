# Task T202 - Realistic Lifecycle Backtest Engine

## Engine Design Summary
- deterministic t->t+1 execution
- strict cash and global risk cap
- conservative intrabar stop-first rule

## Backtest Result (Baseline vs Multi-entry)
| Metric | Baseline | Multi-entry V1 |
|---|---:|---:|
| trade_count | 89 | 242 |
| net_pnl | 688.28 | 5843.929 |
| win_rate | 0.573034 | 0.545455 |
| avg_win | 768.4614 | 294.7658 |
| avg_loss | -1013.2435 | -300.5923 |
| expectancy | 7.7335 | 24.1485 |
| profit_factor | 1.017876 | 1.17674 |
| mdd_pct | 11.994793 | 6.946082 |

## Validation Checklist
- baseline: {'negative_cash': False, 'capital_overlap_violation': True, 'same_bar_fill_violation': False, 'lookahead_violation': False}
- multi_entry_v1: {'negative_cash': False, 'capital_overlap_violation': True, 'same_bar_fill_violation': False, 'lookahead_violation': False}

## Final Judgment
- INVALID (artifact)
