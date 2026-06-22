# Task T510 - Max-Return Regime Strategy

## Summary Table
| Metric | Baseline | Regime V1 | MaxReturnRegime V1 |
|---|---:|---:|---:|
| Initial Capital | $100,000.00 | $100,000.00 | $100,000.00 |
| Final Capital | $109,593.13 | $104,645.14 | $126,020.58 |
| Total Return | +9.59% | +4.65% | +26.02% |
| CAGR | +1.85% | +0.91% | +4.73% |
| MDD | -31.51% | -30.37% | -27.29% |
| Worst Year | -22.99% | -22.16% | -21.20% |
| TUW (months) | 72 | 72 | 70 |
| Sharpe | -0.2183 | -0.2555 | 0.0582 |
| Trade Count | 694 | 733 | 394 |

## Validation
- baseline: {'no_negative_cash': True, 'no_capital_overlap': True, 'no_lookahead': True, 'no_same_bar_fill': True}
- regime_switch_v1: {'no_negative_cash': True, 'no_capital_overlap': True, 'no_lookahead': True, 'no_same_bar_fill': True}
- max_return_regime_v1: {'no_negative_cash': True, 'no_capital_overlap': True, 'no_lookahead': True, 'no_same_bar_fill': True}
- mdd_guard_pass (max_return_regime_v1): True

## Final Decision: PASS
