# Task 339: Intraday Signal Strengthening via Edge Localization

- Final decision: `CLEAR_STRONG_SUBSET`.

## Top Signal Subsets

| window_mode | subset_id | subset_definition | deployability | trade_count | oos_lift_vs_baseline | oos_expectancy | expectancy_delta | saved_loss | missed_gain | clean_state_precision | bad_state_recall | holdout_mean_lift | holdout_positive_share | symbol_concentration_share | robustness_score | signal_strength_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| entry_only | entry_only|atr_regime:high_atr|contraction_regime:vol_expanding | atr_regime=high_atr AND contraction_regime=vol_expanding | live_eligible | 33 | 0.051515 | 0.260148 | 0.377037 | 14.4293 | 0 | 0.151515 | 0.5 | 0.00679 | 0.111111 | 0.590524 | 0.406619 | 0.829503 |
| immediate_post_break | immediate_post_break|atr_regime:high_atr|contraction_regime:vol_expanding | atr_regime=high_atr AND contraction_regime=vol_expanding | live_eligible | 33 | 0.047348 | 0.260148 | 0.366319 | 13.6811 | 0 | 0.151515 | 0.53125 | 0.00679 | 0.111111 | 0.590524 | 0.406619 | 0.814553 |
| immediate_post_break | immediate_post_break|atr_regime:high_atr|vwap_response:vwap_hold | atr_regime=high_atr AND vwap_response=vwap_hold | live_eligible | 31 | 0.057124 | 0.069832 | 0.176003 | 8.67627 | 1.41527 | 0.16129 | 0.6875 | 0.077712 | 0.333333 | 0.614941 | 0.594676 | 0.78862 |
| immediate_post_break | immediate_post_break|atr_regime:high_atr|breakout_response:breakout_hold | atr_regime=high_atr AND breakout_response=breakout_hold | live_eligible | 29 | 0.068247 | -0.002246 | 0.103925 | 8.67627 | 3.6452 | 0.172414 | 0.6875 | 0.095348 | 0.333333 | 0.655128 | 0.6011 | 0.781269 |
| entry_only | entry_only|atr_regime:high_atr|setup_type:range_compression | atr_regime=high_atr AND setup_type=range_compression | live_eligible | 28 | 0.078571 | -0.104548 | 0.012341 | 11.422 | 10.6218 | 0.178571 | 0.470588 | 0.054343 | 0.444444 | 0.56355 | 0.611453 | 0.756629 |
| entry_only | entry_only|atr_regime:high_atr|breakout_subtype:RANGE_COMPRESSION|HIGH_TOUCH | atr_regime=high_atr AND breakout_subtype=RANGE_COMPRESSION|HIGH_TOUCH | live_eligible | 28 | 0.078571 | -0.104548 | 0.012341 | 11.422 | 10.6218 | 0.178571 | 0.470588 | 0.054343 | 0.444444 | 0.56355 | 0.611453 | 0.756629 |
| immediate_post_break | immediate_post_break|atr_regime:high_atr|setup_type:range_compression | atr_regime=high_atr AND setup_type=range_compression | live_eligible | 28 | 0.074405 | -0.104548 | 0.001623 | 10.6737 | 10.6218 | 0.178571 | 0.5 | 0.054343 | 0.444444 | 0.56355 | 0.611453 | 0.74168 |
| immediate_post_break | immediate_post_break|atr_regime:high_atr|breakout_subtype:RANGE_COMPRESSION|HIGH_TOUCH | atr_regime=high_atr AND breakout_subtype=RANGE_COMPRESSION|HIGH_TOUCH | live_eligible | 28 | 0.074405 | -0.104548 | 0.001623 | 10.6737 | 10.6218 | 0.178571 | 0.5 | 0.054343 | 0.444444 | 0.56355 | 0.611453 | 0.74168 |
| entry_only | entry_only|atr_regime:high_atr | atr_regime=high_atr | live_eligible | 38 | 0.031579 | 0.094212 | 0.211101 | 9.42452 | 0 | 0.131579 | 0.647059 | 0.003968 | 0.1 | 0.591898 | 0.397931 | 0.721434 |
| entry_only | entry_only|atr_regime:high_atr|time_of_day:mid_session | atr_regime=high_atr AND time_of_day=mid_session | live_eligible | 38 | 0.031579 | 0.094212 | 0.211101 | 9.42452 | 0 | 0.131579 | 0.647059 | 0.003968 | 0.1 | 0.591898 | 0.397931 | 0.721434 |

## Subset Strategy Performance

| window_mode | subset_id | subset_definition | deployability | scope | baseline_trade_count | subset_trade_count | baseline_expectancy | subset_expectancy | baseline_return_proxy | subset_return_proxy | saved_loss | missed_gain | trade_retention_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| entry_only | entry_only|atr_regime:high_atr|contraction_regime:vol_expanding | atr_regime=high_atr AND contraction_regime=vol_expanding | live_eligible | anchored_oos | 50 | 33 | -0.116889 | 0.260148 | -5.84447 | 8.58487 | 14.4293 | 0 | 0.66 |
| entry_only | entry_only|atr_regime:high_atr|contraction_regime:vol_expanding | atr_regime=high_atr AND contraction_regime=vol_expanding | live_eligible | full_period | 390 | 116 | 0.49594 | 0.298509 | 193.416 | 34.627 | 105.899 | 264.689 | 0.297436 |
| immediate_post_break | immediate_post_break|atr_regime:high_atr|contraction_regime:vol_expanding | atr_regime=high_atr AND contraction_regime=vol_expanding | live_eligible | anchored_oos | 48 | 33 | -0.106171 | 0.260148 | -5.09621 | 8.58487 | 13.6811 | 0 | 0.6875 |
| immediate_post_break | immediate_post_break|atr_regime:high_atr|contraction_regime:vol_expanding | atr_regime=high_atr AND contraction_regime=vol_expanding | live_eligible | full_period | 350 | 111 | 0.458518 | 0.25718 | 160.481 | 28.547 | 98.9556 | 230.89 | 0.317143 |
| immediate_post_break | immediate_post_break|atr_regime:high_atr|vwap_response:vwap_hold | atr_regime=high_atr AND vwap_response=vwap_hold | live_eligible | anchored_oos | 48 | 31 | -0.106171 | 0.069832 | -5.09621 | 2.16479 | 8.67627 | 1.41527 | 0.645833 |
| immediate_post_break | immediate_post_break|atr_regime:high_atr|vwap_response:vwap_hold | atr_regime=high_atr AND vwap_response=vwap_hold | live_eligible | full_period | 350 | 168 | 0.458518 | 0.483554 | 160.481 | 81.2371 | 82.9855 | 162.23 | 0.48 |
| immediate_post_break | immediate_post_break|atr_regime:high_atr|breakout_response:breakout_hold | atr_regime=high_atr AND breakout_response=breakout_hold | live_eligible | anchored_oos | 48 | 29 | -0.106171 | -0.002246 | -5.09621 | -0.065141 | 8.67627 | 3.6452 | 0.604167 |
| immediate_post_break | immediate_post_break|atr_regime:high_atr|breakout_response:breakout_hold | atr_regime=high_atr AND breakout_response=breakout_hold | live_eligible | full_period | 350 | 130 | 0.458518 | 0.733445 | 160.481 | 95.3479 | 105.345 | 170.478 | 0.371429 |
| entry_only | entry_only|atr_regime:high_atr|setup_type:range_compression | atr_regime=high_atr AND setup_type=range_compression | live_eligible | anchored_oos | 50 | 28 | -0.116889 | -0.104548 | -5.84447 | -2.92735 | 11.422 | 10.6218 | 0.56 |
| entry_only | entry_only|atr_regime:high_atr|setup_type:range_compression | atr_regime=high_atr AND setup_type=range_compression | live_eligible | full_period | 390 | 167 | 0.49594 | 0.529876 | 193.416 | 88.4893 | 89.5099 | 197.676 | 0.428205 |
| entry_only | entry_only|atr_regime:high_atr|breakout_subtype:RANGE_COMPRESSION|HIGH_TOUCH | atr_regime=high_atr AND breakout_subtype=RANGE_COMPRESSION|HIGH_TOUCH | live_eligible | anchored_oos | 50 | 28 | -0.116889 | -0.104548 | -5.84447 | -2.92735 | 11.422 | 10.6218 | 0.56 |
| entry_only | entry_only|atr_regime:high_atr|breakout_subtype:RANGE_COMPRESSION|HIGH_TOUCH | atr_regime=high_atr AND breakout_subtype=RANGE_COMPRESSION|HIGH_TOUCH | live_eligible | full_period | 390 | 167 | 0.49594 | 0.529876 | 193.416 | 88.4893 | 89.5099 | 197.676 | 0.428205 |
| immediate_post_break | immediate_post_break|atr_regime:high_atr|setup_type:range_compression | atr_regime=high_atr AND setup_type=range_compression | live_eligible | anchored_oos | 48 | 28 | -0.106171 | -0.104548 | -5.09621 | -2.92735 | 10.6737 | 10.6218 | 0.583333 |
| immediate_post_break | immediate_post_break|atr_regime:high_atr|setup_type:range_compression | atr_regime=high_atr AND setup_type=range_compression | live_eligible | full_period | 350 | 155 | 0.458518 | 0.423847 | 160.481 | 65.6963 | 83.1409 | 181.165 | 0.442857 |
| immediate_post_break | immediate_post_break|atr_regime:high_atr|breakout_subtype:RANGE_COMPRESSION|HIGH_TOUCH | atr_regime=high_atr AND breakout_subtype=RANGE_COMPRESSION|HIGH_TOUCH | live_eligible | anchored_oos | 48 | 28 | -0.106171 | -0.104548 | -5.09621 | -2.92735 | 10.6737 | 10.6218 | 0.583333 |
| immediate_post_break | immediate_post_break|atr_regime:high_atr|breakout_subtype:RANGE_COMPRESSION|HIGH_TOUCH | atr_regime=high_atr AND breakout_subtype=RANGE_COMPRESSION|HIGH_TOUCH | live_eligible | full_period | 350 | 155 | 0.458518 | 0.423847 | 160.481 | 65.6963 | 83.1409 | 181.165 | 0.442857 |
| entry_only | entry_only|atr_regime:high_atr | atr_regime=high_atr | live_eligible | anchored_oos | 50 | 38 | -0.116889 | 0.094212 | -5.84447 | 3.58006 | 9.42452 | 0 | 0.76 |
| entry_only | entry_only|atr_regime:high_atr | atr_regime=high_atr | live_eligible | full_period | 390 | 203 | 0.49594 | 0.492386 | 193.416 | 99.9544 | 77.8338 | 171.296 | 0.520513 |
| entry_only | entry_only|atr_regime:high_atr|time_of_day:mid_session | atr_regime=high_atr AND time_of_day=mid_session | live_eligible | anchored_oos | 50 | 38 | -0.116889 | 0.094212 | -5.84447 | 3.58006 | 9.42452 | 0 | 0.76 |
| entry_only | entry_only|atr_regime:high_atr|time_of_day:mid_session | atr_regime=high_atr AND time_of_day=mid_session | live_eligible | full_period | 390 | 168 | 0.49594 | 0.409052 | 193.416 | 68.7207 | 90.5894 | 215.285 | 0.430769 |

## Holdout Results

| subset_id | holdout_type | holdout_value | trade_count | lift_vs_baseline | expectancy_delta | status |
| --- | --- | --- | --- | --- | --- | --- |
| entry_only|time_of_day:mid_session | symbol | AAPL | 0 |  |  | insufficient_sample |
| entry_only|time_of_day:mid_session | symbol | AVGO | 20 | 0 | 0 | ok |
| entry_only|time_of_day:mid_session | symbol | META | 14 | 0 | 0 | ok |
| entry_only|time_of_day:mid_session | symbol | NFLX | 2 |  |  | insufficient_sample |
| entry_only|time_of_day:mid_session | symbol | QCOM | 12 | 0 | 0 | ok |
| entry_only|time_of_day:mid_session | sector_holdout | others | 0 |  |  | insufficient_sample |
| entry_only|time_of_day:mid_session | sector_holdout | semis | 32 | 0 | 0 | ok |
| entry_only|time_of_day:mid_session | sector_holdout | software_internet | 16 | 0 | 0 | ok |
| entry_only|time_of_day:mid_session | time_split_oos | 2025-11 | 5 | 0 | 0.003623 | ok |
| entry_only|time_of_day:mid_session | time_split_oos | 2025-12 | 5 | 0 | 0 | ok |
| entry_only|time_of_day:mid_session | time_split_oos | 2026-01 | 19 | 0 | 0 | ok |
| entry_only|time_of_day:mid_session | time_split_oos | 2026-02 | 2 |  |  | insufficient_sample |
| entry_only|time_of_day:mid_session | time_split_oos | 2026-03 | 10 | 0 | 0 | ok |
| entry_only|time_of_day:mid_session | time_split_oos | 2026-04 | 7 | 0 | 0 | ok |
| entry_only|time_of_day:mid_session | scenario_holdout | PIVOT_HIGH | 12 |  |  | insufficient_sample |
| entry_only|time_of_day:mid_session | scenario_holdout | RANGE_COMPRESSION | 36 | 0 | 0 | ok |
| entry_only|sector_group:semis | symbol | AAPL | 0 |  |  | insufficient_sample |
| entry_only|sector_group:semis | symbol | AVGO | 20 | 0 | 0 | ok |
| entry_only|sector_group:semis | symbol | META | 0 |  |  | insufficient_sample |
| entry_only|sector_group:semis | symbol | NFLX | 0 |  |  | insufficient_sample |

## Final Answer

- This report localizes where intraday signal is already strong instead of trying to improve global signal quality.
- `live_eligible` subsets exclude ex-post behavior-state conditions.
- `diagnostic_only` subsets may still explain where signal concentrates even if they are not directly tradable.