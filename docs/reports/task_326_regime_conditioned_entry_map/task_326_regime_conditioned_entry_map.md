# Task 326: Regime-Conditioned Entry Map

## Core Answer

Entry was treated as conditional on regime, not as a global score problem.

## OOS Regime Baseline

| regime | trade_count | total_r | expectancy_r | win_rate | average_r | drawdown_proxy | avg_holding_days | avg_follow_through_3d_pct | avg_follow_through_5d_pct | avg_retrace_3d_pct | avg_retrace_5d_pct | top_sector | top_sector_share | top_scenario_family | top_scenario_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| failed_recovery | 2 | -2.46687 | -1.23344 | 0 | -1.23344 | -1.23344 | 13 | 0.021373 | 0.09208 | 0.031649 | 0.009177 | semis | 1 | PIVOT_HIGH | 1 |
| high_vol_chop | 10 | -9.27339 | -0.927339 | 0 | -0.927339 | -8.26721 | 2.9 | 0.046428 | 0.046428 | 0.087381 | 0.080875 | semis | 1 | RANGE_COMPRESSION | 0.8 |
| rebound_chop | 89 | -43.7464 | -0.491532 | 0.157303 | -0.491532 | -44.7791 | 9.42697 | 0.042645 | 0.055501 | 0.032346 | 0.039843 | semis | 0.516854 | RANGE_COMPRESSION | 0.752809 |
| late_extension | 71 | -28.3316 | -0.399037 | 0.295775 | -0.399037 | -29.3157 | 7.28169 | 0.043566 | 0.046786 | 0.035597 | 0.052433 | software/internet | 0.549296 | RANGE_COMPRESSION | 0.802817 |
| risk_off_reversal | 29 | 32.0532 | 1.10528 | 0.655172 | 1.10528 | -1.01987 | 7.62069 | 0.05018 | 0.083982 | 0.019399 | 0.026201 | software/internet | 0.586207 | RANGE_COMPRESSION | 0.724138 |

## Conditional Feature Directions

| feature | regime | direction | best_band | worst_band | expectancy_edge_r | actionable |
| --- | --- | --- | --- | --- | --- | --- |
| vol_contraction_ratio | failed_recovery | no clear edge | low | mid | 2.0494 | True |
| ret_20d_pre | failed_recovery | mid preferred | mid | low | 1.92472 | True |
| rs_percentile_20d | failed_recovery | high is good | high | low | 1.63967 | True |
| gap_over_planned_entry_pct | failed_recovery | low is good | low | high | 1.2429 | True |
| dist_to_sma200_pct | failed_recovery | no clear edge | high | mid | 0.944958 | True |
| sector_breadth | failed_recovery | no clear edge | high | mid | 0.748624 | True |
| breakout_strength_pct | failed_recovery | mid preferred | mid | high | 0.724552 | True |
| sector_breadth | high_vol_chop | no clear edge | low | mid | 1.19451 | True |
| gap_over_planned_entry_pct | high_vol_chop | mid preferred | mid | low | 0.808346 | True |
| breakout_strength_pct | high_vol_chop | no clear edge | low | mid | 0.796833 | True |
| vol_contraction_ratio | high_vol_chop | mid preferred | mid | low | 0.735989 | True |
| ret_20d_pre | high_vol_chop | no clear edge | low | mid | 0.541482 | True |
| dist_to_sma200_pct | high_vol_chop | no clear edge | high | mid | 0.332341 | True |
| rs_percentile_20d | high_vol_chop | no clear edge | low | mid | 0.113552 | False |
| rs_percentile_20d | late_extension | no clear edge | high | mid | 1.21005 | True |
| sector_breadth | late_extension | no clear edge | high | mid | 0.608405 | True |
| breakout_strength_pct | late_extension | high is good | high | low | 0.580919 | True |
| gap_over_planned_entry_pct | late_extension | no clear edge | high | mid | 0.478722 | True |
| vol_contraction_ratio | late_extension | low is good | low | high | 0.374028 | True |
| dist_to_sma200_pct | late_extension | high is good | high | low | 0.275663 | True |
| ret_20d_pre | late_extension | high is good | high | low | 0.165608 | True |
| rs_percentile_20d | narrow_leadership_trend | no clear edge | high | mid | 2.39228 | True |
| breakout_strength_pct | narrow_leadership_trend | mid preferred | mid | low | 2.37948 | True |
| dist_to_sma200_pct | narrow_leadership_trend | high is good | high | low | 1.98714 | True |
| gap_over_planned_entry_pct | narrow_leadership_trend | mid preferred | mid | low | 1.87137 | True |
| sector_breadth | narrow_leadership_trend | mid preferred | mid | low | 1.79713 | True |
| ret_20d_pre | narrow_leadership_trend | no clear edge | high | mid | 1.60688 | True |
| vol_contraction_ratio | narrow_leadership_trend | mid preferred | mid | high | 1.58004 | True |
| dist_to_sma200_pct | rebound_chop | mid preferred | mid | high | 0.909328 | True |
| sector_breadth | rebound_chop | no clear edge | high | mid | 0.853705 | True |
| rs_percentile_20d | rebound_chop | high is good | high | low | 0.514358 | True |
| vol_contraction_ratio | rebound_chop | high is good | high | low | 0.417123 | True |
| breakout_strength_pct | rebound_chop | high is good | high | low | 0.347326 | True |
| ret_20d_pre | rebound_chop | high is good | high | low | 0.328931 | True |
| gap_over_planned_entry_pct | rebound_chop | high is good | high | low | 0.201078 | True |
| breakout_strength_pct | risk_off_reversal | no clear edge | high | mid | 0.894367 | True |
| gap_over_planned_entry_pct | risk_off_reversal | no clear edge | low | mid | 0.782908 | True |
| vol_contraction_ratio | risk_off_reversal | no clear edge | low | mid | 0.760901 | True |
| rs_percentile_20d | risk_off_reversal | low is good | low | high | 0.733253 | True |
| ret_20d_pre | risk_off_reversal | low is good | low | high | 0.421043 | True |
| dist_to_sma200_pct | risk_off_reversal | no clear edge | low | mid | 0.360819 | True |
| sector_breadth | risk_off_reversal | mid preferred | mid | high | 0.29239 | True |

## Extracted Rules

| rule_id | regime_state | action | size_multiplier | feature | operator | values | condition_count | rationale | train_regime_expectancy_r | train_band_expectancy_r | train_trade_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| failed_recovery_skip_ret_20d_pre_low | failed_recovery | skip | 0 | ret_20d_pre | band_in | low | 1 | avoid ret_20d_pre=low in failed_recovery | 0.026847 | -1.05909 | 8 |
| failed_recovery_reduce_without_vol_contraction_ratio_low | failed_recovery | reduce | 0.5 | vol_contraction_ratio | band_not_in | low | 1 | prefer vol_contraction_ratio=low in failed_recovery | 0.026847 | 1.41546 | 5 |
| high_vol_chop_skip_sector_breadth_mid | high_vol_chop | skip | 0 | sector_breadth | band_in | mid | 1 | avoid sector_breadth=mid in high_vol_chop | 0.256199 | -0.676537 | 18 |
| high_vol_chop_reduce_without_dist_to_sma200_pct_high | high_vol_chop | reduce | 0.5 | dist_to_sma200_pct | band_not_in | high | 1 | prefer dist_to_sma200_pct=high in high_vol_chop | 0.256199 | 0.556498 | 15 |
| late_extension_skip_rs_percentile_20d_mid | late_extension | skip | 0 | rs_percentile_20d | band_in | mid | 1 | avoid rs_percentile_20d=mid in late_extension | 0.666688 | -0.237773 | 123 |
| late_extension_reduce_without_rs_percentile_20d_high | late_extension | reduce | 0.5 | rs_percentile_20d | band_not_in | high | 1 | prefer rs_percentile_20d=high in late_extension | 0.666688 | 0.972278 | 201 |
| narrow_leadership_trend_skip_rs_percentile_20d_mid | narrow_leadership_trend | skip | 0 | rs_percentile_20d | band_in | mid | 1 | avoid rs_percentile_20d=mid in narrow_leadership_trend | 1.16448 | -0.858464 | 10 |
| narrow_leadership_trend_reduce_without_ret_20d_pre_high | narrow_leadership_trend | reduce | 0.5 | ret_20d_pre | band_not_in | high | 1 | prefer ret_20d_pre=high in narrow_leadership_trend | 1.16448 | 2.05398 | 54 |
| rebound_chop_skip_dist_to_sma200_pct_high | rebound_chop | skip | 0 | dist_to_sma200_pct | band_in | high | 1 | avoid dist_to_sma200_pct=high in rebound_chop | 0.831317 | 0.079111 | 120 |
| rebound_chop_reduce_without_sector_breadth_high | rebound_chop | reduce | 0.5 | sector_breadth | band_not_in | high | 1 | prefer sector_breadth=high in rebound_chop | 0.831317 | 1.25591 | 223 |
| risk_off_reversal_skip_vol_contraction_ratio_mid | risk_off_reversal | skip | 0 | vol_contraction_ratio | band_in | mid | 1 | avoid vol_contraction_ratio=mid in risk_off_reversal | 0.463633 | 0.008196 | 76 |
| risk_off_reversal_reduce_without_rs_percentile_20d_low | risk_off_reversal | reduce | 0.5 | rs_percentile_20d | band_not_in | low | 1 | prefer rs_percentile_20d=low in risk_off_reversal | 0.463633 | 0.965068 | 69 |

## Integrated Summary

| variant | scope | cagr_pct | sharpe | max_drawdown_pct | total_return_pct | total_r | expectancy_r | win_rate | trade_count | avg_holding_days | avg_loss_r | avg_win_r | profit_factor | max_losing_streak | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | anchored_oos | -10.7024 | -1.1988 | 10.1213 | -5.15865 | -5.17651 | -0.271175 | 0.262535 | 20.1 | 8.093 | -0.809192 | 1.19657 | 0.538455 | 6.7 | BASELINE |
| regime_conditioned_entry_filter | anchored_oos | -6.47915 | -1.52431 | 4.53355 | -3.07574 | -6.10629 | -0.365869 | 0.208834 | 17.7 | 7.0438 | -0.822701 | 1.27409 | 0.428465 | 6.8 | REJECT |
| regime_conditioned_entry_filter + size50 | anchored_oos | -6.06332 | -1.44362 | 4.32221 | -2.87532 | -5.65542 | -0.339494 | 0.208834 | 17.7 | 7.0438 | -0.78957 | 1.27409 | 0.445072 | 6.8 | REJECT |
| baseline | full_period | 22.0801 | 1.23394 | 12.0493 | 173.961 | 115.23 | 0.581862 | 0.490451 | 196.9 | 15.5155 | -0.793112 | 2.05062 | 2.43613 | 8.8 | BASELINE |
| regime_conditioned_entry_filter | full_period | 12.4538 | 1.43039 | 6.5338 | 80.413 | 122.74 | 0.712341 | 0.538943 | 172.5 | 16.0895 | -0.803102 | 2.05139 | 2.95547 | 8.2 | REJECT |
| regime_conditioned_entry_filter + size50 | full_period | 12.5529 | 1.44613 | 6.3903 | 81.2086 | 123.631 | 0.717576 | 0.538943 | 172.5 | 16.0895 | -0.786694 | 2.04703 | 3.01404 | 8.2 | REJECT |