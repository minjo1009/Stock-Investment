# Task 325: Regime & Entry Quality Rebuild

## Executive Summary

- Task 324 showed post-entry rescue helps, but it does not fix the source of weak entries.
- Rebuilt regime filter bad states: `failed_recovery`.
- Rebuilt regime filter weak states: `high_vol_chop, late_extension, rebound_chop`.
- Entry quality score was reduced to `rs_percentile_20d, sector_breadth, dist_to_sma200_pct, ret_20d_pre, vol_contraction_ratio`.

## What Task 324 Proved

- Size overlay can soften drawdowns, but OOS stayed negative.
- That pushed this task toward pre-entry regime and quality repair rather than more exit logic.

## Why Regime and Entry Remain Broken

- Worst rebuilt OOS regime: `failed_recovery` with expectancy `-1.233R` across `2` trades.
- Best rebuilt OOS regime: `risk_off_reversal` with expectancy `1.105R` across `29` trades.
- Strongest entry discriminators: `rs_percentile_20d, sector_breadth, dist_to_sma200_pct`.

## New Regime Map

| regime | trade_count | total_r | expectancy_r | win_rate | average_r | drawdown_proxy | avg_holding_days | avg_follow_through_3d_pct | avg_follow_through_5d_pct | avg_retrace_3d_pct | avg_retrace_5d_pct | top_sector | top_sector_share | top_scenario_family | top_scenario_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| failed_recovery | 2 | -2.46687 | -1.23344 | 0 | -1.23344 | -1.23344 | 13 | 0.021373 | 0.09208 | 0.031649 | 0.009177 | semis | 1 | PIVOT_HIGH | 1 |
| high_vol_chop | 10 | -9.27339 | -0.927339 | 0 | -0.927339 | -8.26721 | 2.9 | 0.046428 | 0.046428 | 0.087381 | 0.080875 | semis | 1 | RANGE_COMPRESSION | 0.8 |
| rebound_chop | 89 | -43.7464 | -0.491532 | 0.157303 | -0.491532 | -44.7791 | 9.42697 | 0.042645 | 0.055501 | 0.032346 | 0.039843 | semis | 0.516854 | RANGE_COMPRESSION | 0.752809 |
| late_extension | 71 | -28.3316 | -0.399037 | 0.295775 | -0.399037 | -29.3157 | 7.28169 | 0.043566 | 0.046786 | 0.035597 | 0.052433 | software/internet | 0.549296 | RANGE_COMPRESSION | 0.802817 |
| risk_off_reversal | 29 | 32.0532 | 1.10528 | 0.655172 | 1.10528 | -1.01987 | 7.62069 | 0.05018 | 0.083982 | 0.019399 | 0.026201 | software/internet | 0.586207 | RANGE_COMPRESSION | 0.724138 |

## Entry Quality Separation Layer

| feature | importance | stability | direction |
| --- | --- | --- | --- |
| rs_percentile_20d | 0.316308 | 0.975 | lower_is_better |
| sector_breadth | 0.287798 | 0.5 | higher_is_better |
| dist_to_sma200_pct | 0.283803 | 0.9 | lower_is_better |
| ret_20d_pre | 0.235357 | 0.375 | higher_is_better |
| vol_contraction_ratio | 0.231924 | 0.375 | lower_is_better |

## Regime × Entry Interaction

| regime_state | entry_quality_band | trade_count | expectancy | win_rate | total_r | drawdown_proxy |
| --- | --- | --- | --- | --- | --- | --- |
| failed_recovery | low | 2 | -1.23344 | 0 | -2.46687 | -1.23344 |
| high_vol_chop | low | 10 | -0.927339 | 0 | -9.27339 | -8.26721 |
| late_extension | high | 32 | -0.179471 | 0.3125 | -5.74306 | -6.93528 |
| late_extension | low | 22 | -0.76674 | 0.0909091 | -16.8683 | -16.4551 |
| late_extension | mid | 17 | -0.336488 | 0.529412 | -5.7203 | -5.6931 |
| rebound_chop | high | 7 | -0.658783 | 0 | -4.61148 | -3.75954 |
| rebound_chop | low | 31 | -0.0343834 | 0.387097 | -1.06588 | -2.5785 |
| rebound_chop | mid | 51 | -0.746451 | 0.0392157 | -38.069 | -37.0622 |
| risk_off_reversal | high | 7 | 1.73405 | 1 | 12.1383 | 0 |
| risk_off_reversal | low | 2 | 3.62914 | 1 | 7.25828 | 0 |
| risk_off_reversal | mid | 20 | 0.632829 | 0.5 | 12.6566 | -1.01987 |

## Integrated Filter Test

| variant | scope | cagr_pct | sharpe | max_drawdown_pct | total_return_pct | total_r | expectancy_r | win_rate | trade_count | avg_holding_days | avg_loss_r | avg_win_r | profit_factor | max_losing_streak | recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | anchored_oos | -10.7024 | -1.1988 | 10.1213 | -5.15865 | -5.17651 | -0.271175 | 0.262535 | 20.1 | 8.093 | -0.809192 | 1.19657 | 0.538455 | 6.7 | REJECT |
| entry_quality_filter_only | anchored_oos | -4.31966 | -0.87545 | 4.17141 | -2.03668 | -4.33641 | -0.283388 | 0.246301 | 15.3 | 6.97343 | -0.827084 | 1.37763 | 0.534701 | 7.4 | REJECT |
| regime_filter_only | anchored_oos | -4.97432 | -1.09104 | 5.20423 | -2.35606 | -5.15215 | -0.27016 | 0.262535 | 20.1 | 8.08466 | -0.807569 | 1.19657 | 0.540186 | 6.7 | DEFENSIVE_ONLY |
| regime_plus_entry_filter | anchored_oos | -3.16162 | -0.841995 | 3.44322 | -1.48598 | -4.33641 | -0.283388 | 0.246301 | 15.3 | 6.97343 | -0.827084 | 1.37763 | 0.534701 | 7.4 | REJECT |
| regime_plus_entry_plus_size50 | anchored_oos | -2.68714 | -0.729155 | 3.23147 | -1.26164 | -3.88554 | -0.252992 | 0.246301 | 15.3 | 6.97343 | -0.78679 | 1.37763 | 0.562363 | 7.4 | DEFENSIVE_ONLY |
| baseline | full_period | 22.0801 | 1.23394 | 12.0493 | 173.961 | 115.23 | 0.581862 | 0.490451 | 196.9 | 15.5155 | -0.793112 | 2.05062 | 2.43613 | 8.8 | REJECT |
| entry_quality_filter_only | full_period | 17.6413 | 1.27367 | 8.84775 | 126.569 | 104.162 | 0.599796 | 0.488744 | 172.6 | 15.3241 | -0.772884 | 2.08223 | 2.5156 | 8.2 | REJECT |
| regime_filter_only | full_period | 12.6035 | 1.21772 | 7.42973 | 81.8929 | 114.96 | 0.584341 | 0.489728 | 195.7 | 15.4889 | -0.788518 | 2.05139 | 2.44577 | 8.5 | DEFENSIVE_ONLY |
| regime_plus_entry_filter | full_period | 11.6984 | 1.17985 | 7.38598 | 74.6889 | 102.962 | 0.597044 | 0.484273 | 171.4 | 15.3076 | -0.767135 | 2.09208 | 2.50232 | 8 | REJECT |
| regime_plus_entry_plus_size50 | full_period | 11.693 | 1.18218 | 7.44849 | 74.6432 | 103.147 | 0.598155 | 0.484273 | 171.4 | 15.3076 | -0.761982 | 2.08895 | 2.51579 | 8 | DEFENSIVE_ONLY |

## Robustness Review

| variant | scope | dimension | group_count | positive_delta_groups | positive_delta_share | dominant_group_share | robustness_level |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry_quality_filter_only | anchored_oos | scenario | 10 | 8 | 0.8 | 0.137353 | high |
| entry_quality_filter_only | anchored_oos | sector | 4 | 3 | 0.75 | 0.763342 | low |
| entry_quality_filter_only | anchored_oos | regime | 5 | 3 | 0.6 | 0.278782 | high |
| entry_quality_filter_only | anchored_oos | month | 27 | 7 | 0.259259 | 0.235156 | low |
| entry_quality_filter_only | anchored_oos | symbol_group | 12 | 3 | 0.25 | 0.270078 | low |
| regime_filter_only | anchored_oos | scenario | 10 | 2 | 0.2 | 0.5 | low |
| regime_filter_only | anchored_oos | sector | 4 | 1 | 0.25 | 1 | low |
| regime_filter_only | anchored_oos | regime | 5 | 1 | 0.2 | 0.525959 | low |
| regime_filter_only | anchored_oos | month | 25 | 1 | 0.04 | 0.525959 | low |
| regime_filter_only | anchored_oos | symbol_group | 12 | 1 | 0.083333 | 1 | low |
| regime_plus_entry_filter | anchored_oos | scenario | 10 | 8 | 0.8 | 0.137353 | high |
| regime_plus_entry_filter | anchored_oos | sector | 4 | 3 | 0.75 | 0.763342 | low |
| regime_plus_entry_filter | anchored_oos | regime | 5 | 3 | 0.6 | 0.278782 | high |
| regime_plus_entry_filter | anchored_oos | month | 27 | 7 | 0.259259 | 0.235156 | low |
| regime_plus_entry_filter | anchored_oos | symbol_group | 12 | 3 | 0.25 | 0.270078 | low |
| regime_plus_entry_plus_size50 | anchored_oos | scenario | 10 | 8 | 0.8 | 0.11799 | high |
| regime_plus_entry_plus_size50 | anchored_oos | sector | 4 | 3 | 0.75 | 0.574182 | low |
| regime_plus_entry_plus_size50 | anchored_oos | regime | 5 | 3 | 0.6 | 0.321283 | high |
| regime_plus_entry_plus_size50 | anchored_oos | month | 27 | 8 | 0.296296 | 0.22027 | low |
| regime_plus_entry_plus_size50 | anchored_oos | symbol_group | 12 | 3 | 0.25 | 0.298778 | low |
| entry_quality_filter_only | full_period | scenario | 10 | 0 | 0 | 0.169017 | low |
| entry_quality_filter_only | full_period | sector | 4 | 1 | 0.25 | 0.742307 | low |
| entry_quality_filter_only | full_period | regime | 6 | 3 | 0.5 | 0.562722 | low |
| entry_quality_filter_only | full_period | month | 316 | 88 | 0.278481 | 0.064338 | low |
| entry_quality_filter_only | full_period | symbol_group | 12 | 4 | 0.333333 | 0.166348 | low |
| regime_filter_only | full_period | scenario | 10 | 5 | 0.5 | 0.16205 | medium |
| regime_filter_only | full_period | sector | 4 | 1 | 0.25 | 0.511271 | low |
| regime_filter_only | full_period | regime | 6 | 2 | 0.333333 | 0.55167 | low |
| regime_filter_only | full_period | month | 292 | 12 | 0.041096 | 0.121854 | low |
| regime_filter_only | full_period | symbol_group | 12 | 5 | 0.416667 | 0.344979 | low |
| regime_plus_entry_filter | full_period | scenario | 10 | 0 | 0 | 0.166278 | low |
| regime_plus_entry_filter | full_period | sector | 4 | 1 | 0.25 | 0.691253 | low |
| regime_plus_entry_filter | full_period | regime | 6 | 3 | 0.5 | 0.502695 | medium |
| regime_plus_entry_filter | full_period | month | 317 | 90 | 0.283912 | 0.061222 | low |
| regime_plus_entry_filter | full_period | symbol_group | 12 | 4 | 0.333333 | 0.156696 | low |
| regime_plus_entry_plus_size50 | full_period | scenario | 10 | 0 | 0 | 0.165574 | low |
| regime_plus_entry_plus_size50 | full_period | sector | 4 | 1 | 0.25 | 0.692941 | low |
| regime_plus_entry_plus_size50 | full_period | regime | 6 | 3 | 0.5 | 0.496587 | medium |
| regime_plus_entry_plus_size50 | full_period | month | 317 | 91 | 0.287066 | 0.060786 | low |
| regime_plus_entry_plus_size50 | full_period | symbol_group | 12 | 4 | 0.333333 | 0.142327 | low |

## Final Recommendation

- regime filter: `DEFENSIVE_ONLY`
- entry filter: `REJECT`
- regime + entry: `REJECT`
- regime + entry + size50: `DEFENSIVE_ONLY`

The target here is not a prettier rescue layer. It is fewer low-quality entries at the source.