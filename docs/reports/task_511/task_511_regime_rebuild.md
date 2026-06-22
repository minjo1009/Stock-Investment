# Task T511 - Regime Detail Rebuild (Execution-Driven)

## Performance Comparison
| Metric | Baseline | Regime V1 | Regime V2 |
|---|---:|---:|---:|
| Initial Capital | $100,000.00 | $100,000.00 | $100,000.00 |
| Final Capital | $96,342.61 | $101,131.51 | $136,064.42 |
| Total Return | -3.66% | +1.13% | +36.06% |
| CAGR | -0.74% | +0.23% | +6.35% |
| MDD | -28.01% | -24.54% | -23.01% |
| Sharpe | -0.3184 | -0.1905 | 0.1323 |
| Trade Count | 955 | 964 | 340 |

## Loss Cause Decomposition (Regime V2)
| Group | Count | PnL | PF |
|---|---:|---:|---:|
| exit:hard_stop | 150 | -51862.06 | 0.091 |
| exit:time_stop | 181 | +88477.21 | 13.753 |
| exit:regime_flip | 9 | -550.73 | 0.248 |
| family:momentum | 320 | +37722.10 | 1.605 |
| family:mean_reversion | 20 | -1657.68 | 0.296 |
| bucket:C | 91 | -7088.93 | 0.562 |
| bucket:A | 159 | +30211.31 | 2.164 |
| bucket:B | 90 | +12942.04 | 1.573 |

## Validation
- baseline: {'no_negative_cash': True, 'no_capital_overlap': True, 'no_lookahead': True, 'no_same_bar_fill': True}
- regime_switch_v1: {'no_negative_cash': True, 'no_capital_overlap': True, 'no_lookahead': True, 'no_same_bar_fill': True}
- regime_switch_v2: {'no_negative_cash': True, 'no_capital_overlap': True, 'no_lookahead': True, 'no_same_bar_fill': True}
- mdd_guard_pass(v2): True

## Final Decision: PASS
