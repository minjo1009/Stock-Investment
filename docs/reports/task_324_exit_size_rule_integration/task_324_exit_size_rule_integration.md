# Task 324 Exit/Size Rule Integration

## Executive Summary
- Scenario pool size: 10
- Variants tested: baseline, exit_only, size_only_50, size_only_30, exit_plus_size_50, exit_plus_size_30
- Primary OOS window: anchored_oos

## Baseline vs Variants
| Variant | Full Return | OOS Return | MDD | Sharpe | Expectancy | Trade Count | Recommendation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| baseline | 173.96 | -5.16 | 10.12 | -1.199 | -0.271 | 20.1 | REJECT |
| exit_only | 164.28 | -3.89 | 8.90 | -0.947 | -0.201 | 20.3 | KEEP_AS_DEFENSIVE_OVERLAY |
| size_only_50 | 177.19 | -4.70 | 9.49 | -1.109 | -0.246 | 20.1 | PROMOTE_TO_NEXT_STAGE |
| size_only_30 | 175.79 | -4.88 | 9.75 | -1.144 | -0.257 | 20.1 | PROMOTE_TO_NEXT_STAGE |
| exit_plus_size_50 | 166.74 | -3.69 | 8.61 | -0.905 | -0.191 | 20.3 | KEEP_AS_DEFENSIVE_OVERLAY |
| exit_plus_size_30 | 165.72 | -3.77 | 8.73 | -0.922 | -0.195 | 20.3 | KEEP_AS_DEFENSIVE_OVERLAY |

## OOS Result
| Variant | OOS Return Delta | MDD Delta | Expectancy Delta | Win Rate Delta |
| --- | ---: | ---: | ---: | ---: |
| baseline | 0.00 | 0.00 | 0.000 | 0.000 |
| exit_only | 1.27 | -1.22 | 0.070 | 0.041 |
| exit_plus_size_30 | 1.39 | -1.39 | 0.076 | 0.041 |
| exit_plus_size_50 | 1.46 | -1.51 | 0.080 | 0.041 |
| size_only_30 | 0.28 | -0.37 | 0.015 | 0.000 |
| size_only_50 | 0.46 | -0.63 | 0.025 | 0.000 |

## Full-period Result
| variant | evaluation_scope | scenario_count | cagr_pct | sharpe | max_drawdown_pct | total_return_pct | total_r | expectancy_r | win_rate | trade_count | avg_holding_days | avg_loss_r | avg_win_r | profit_factor | max_losing_streak | oos_return_delta | mdd_delta | expectancy_delta | win_rate_delta |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | full_period | 10 | 22.080149 | 1.233935 | 12.049290 | 173.961051 | 115.229943 | 0.581862 | 0.490451 | 196.900000 | 15.515472 | -0.793112 | 2.050619 | 2.436129 | 8.800000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| exit_only | full_period | 10 | 21.007815 | 1.187950 | 11.841076 | 164.280080 | 108.482420 | 0.458237 | 0.521180 | 235.600000 | 10.946175 | -0.693446 | 1.530197 | 2.364372 | 7.100000 | -9.680971 | -0.208214 | -0.123625 | 0.030729 |
| exit_plus_size_30 | full_period | 10 | 21.135880 | 1.196439 | 11.727323 | 165.723304 | 108.988235 | 0.460359 | 0.521180 | 235.600000 | 10.946175 | -0.687600 | 1.528903 | 2.382957 | 7.100000 | -8.237747 | -0.321967 | -0.121503 | 0.030729 |
| exit_plus_size_50 | full_period | 10 | 21.226861 | 1.202122 | 11.651182 | 166.744865 | 109.329980 | 0.461791 | 0.521911 | 235.600000 | 10.946175 | -0.684821 | 1.525622 | 2.395595 | 6.900000 | -7.216186 | -0.398108 | -0.120071 | 0.031460 |
| size_only_30 | full_period | 10 | 22.239297 | 1.243821 | 11.895172 | 175.785799 | 115.876950 | 0.585131 | 0.490451 | 196.900000 | 15.515472 | -0.785097 | 2.048985 | 2.459749 | 8.800000 | 1.824748 | -0.154118 | 0.003269 | 0.000000 |
| size_only_50 | full_period | 10 | 22.361269 | 1.250630 | 11.804731 | 177.189264 | 116.321748 | 0.587378 | 0.490451 | 196.900000 | 15.515472 | -0.779599 | 2.047882 | 2.476331 | 8.800000 | 3.228213 | -0.244559 | 0.005516 | 0.000000 |

## Rule Trigger Analysis
| variant | rule | trigger_count | avg_r_before | avg_r_after | saved_loss | missed_gain |
| --- | --- | --- | --- | --- | --- | --- |
| exit_only | exit_only | 37 | -0.870863 | -0.424709 | 16.751539 | 0.000000 |
| exit_plus_size_30 | exit_plus_size_30 | 39 | -0.802564 | -0.349548 | 18.040798 | 0.129322 |
| exit_plus_size_50 | exit_plus_size_50 | 39 | -0.802564 | -0.327661 | 18.985654 | 0.220608 |
| size_only_30 | size_only_30 | 14 | -0.757717 | -0.550759 | 3.026722 | 0.129322 |
| size_only_50 | size_only_50 | 14 | -0.757717 | -0.404856 | 5.160652 | 0.220608 |

## Saved Loss vs Missed Gain
- `baseline`: saved loss `0.000` vs missed gain `0.000`
- `exit_only`: saved loss `16.752` vs missed gain `0.000`
- `size_only_50`: saved loss `5.161` vs missed gain `0.221`
- `size_only_30`: saved loss `3.027` vs missed gain `0.129`
- `exit_plus_size_50`: saved loss `18.986` vs missed gain `0.221`
- `exit_plus_size_30`: saved loss `18.041` vs missed gain `0.129`

## Robustness Review
- `baseline` robustness: `low`
- `exit_only` robustness: `medium`
- `size_only_50` robustness: `high`
- `size_only_30` robustness: `high`
- `exit_plus_size_50` robustness: `medium`
- `exit_plus_size_30` robustness: `medium`

## Final Recommendation
- `baseline` -> `REJECT`
- `exit_only` -> `KEEP_AS_DEFENSIVE_OVERLAY`
- `size_only_50` -> `PROMOTE_TO_NEXT_STAGE`
- `size_only_30` -> `PROMOTE_TO_NEXT_STAGE`
- `exit_plus_size_50` -> `KEEP_AS_DEFENSIVE_OVERLAY`
- `exit_plus_size_30` -> `KEEP_AS_DEFENSIVE_OVERLAY`
