# Task T102 - CRB range_pct Validation

## Objective
- Validate max_range_pct 0.12 vs 0.10 while keeping N=20, compression=0.65, touch=2.

## Comparison
| Metric | 0.10 | 0.12 | Delta |
|---|---:|---:|---:|
| final_signal_count | 5 | 9 | 4 |
| pass_rate_vs_breakout | 0.004634 | 0.008341 | 0.003707 |
| win_rate_20 | 1.0 | 0.555556 | -0.444444 |
| avg_return_20 | 0.038711 | -0.014359 | -0.05307 |
| net_return_sum_20 | 0.193553 | -0.12923 | -0.322783 |

## Decision
- status: WARNING
- answer: NO
- note: Single-parameter validation only; no multi-parameter tuning applied.
