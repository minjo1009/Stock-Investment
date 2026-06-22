# Task T500 - Regime Switching V1 (Reality-First)

## Summary Table
| Metric | Baseline | Regime V1 |
|---|---:|---:|
| Initial Capital | $100,000.00 | $100,000.00 |
| Final Capital | $78,431.34 | $144,782.31 |
| Total Return | -21.57% | +44.78% |
| CAGR | -4.74% | +7.68% |
| MDD | -59.14% | -43.53% |
| Worst Year | -18.67% | -5.08% |
| TUW (months) | 73 | 72 |
| Sharpe | -0.0935 | 0.3098 |
| Trade Count | 394 | 460 |

## Runtime Validation
- baseline validation: {'no_negative_cash': True, 'no_capital_overlap': True, 'no_lookahead': True, 'no_same_bar_fill': True}
- regime_switch_v1 validation: {'no_negative_cash': True, 'no_capital_overlap': True, 'no_lookahead': True, 'no_same_bar_fill': True}
- regime_switch_count (v1): 527

## Final Decision: PASS
