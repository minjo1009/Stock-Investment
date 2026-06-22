# Task 336: True Intraday Information Feasibility

- Final decision: `NO_INTRADAY_EDGE`.
- Covered trade count: `390`.

## Coverage Summary

| coverage_status | trade_count |
| --- | --- |
| insufficient_window | 1579 |
| covered | 390 |

## Intraday Feature Definitions

| family_name | feature_name | available_in_entry_only | available_in_immediate_post_break | coverage_total_trades | coverage_covered_trades | coverage_missing_symbol | coverage_missing_date | coverage_insufficient_window | phase |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| volume_participation | breakout_window_volume_surge | True | True | 1969 | 390 | 0 | 0 | 1579 | phase_1_subset_feasibility |
| volume_participation | relative_volume_percentile | True | True | 1969 | 390 | 0 | 0 | 1579 | phase_1_subset_feasibility |
| volume_participation | volume_persistence_3bars | True | True | 1969 | 390 | 0 | 0 | 1579 | phase_1_subset_feasibility |
| volume_participation | volume_decay_rate | True | True | 1969 | 390 | 0 | 0 | 1579 | phase_1_subset_feasibility |
| price_structure | breakout_bar_range_expansion | True | True | 1969 | 390 | 0 | 0 | 1579 | phase_1_subset_feasibility |
| price_structure | breakout_bar_close_location | True | True | 1969 | 390 | 0 | 0 | 1579 | phase_1_subset_feasibility |
| price_structure | multi_bar_follow_through_3bars | True | True | 1969 | 390 | 0 | 0 | 1579 | phase_1_subset_feasibility |
| price_structure | intraday_pullback_depth_3bars | True | True | 1969 | 390 | 0 | 0 | 1579 | phase_1_subset_feasibility |
| vwap_positioning | price_vs_session_vwap_at_breakout | True | True | 1969 | 390 | 0 | 0 | 1579 | phase_1_subset_feasibility |
| vwap_positioning | vwap_deviation_at_breakout | True | True | 1969 | 390 | 0 | 0 | 1579 | phase_1_subset_feasibility |
| vwap_positioning | vwap_reversion_flag_3bars | True | True | 1969 | 390 | 0 | 0 | 1579 | phase_1_subset_feasibility |
| vwap_positioning | vwap_slope_prebreak | True | True | 1969 | 390 | 0 | 0 | 1579 | phase_1_subset_feasibility |
| immediate_follow_through_quality | return_next_3bars | False | True | 1969 | 390 | 0 | 0 | 1579 | phase_1_subset_feasibility |
| immediate_follow_through_quality | return_next_5bars | False | True | 1969 | 390 | 0 | 0 | 1579 | phase_1_subset_feasibility |
| immediate_follow_through_quality | adverse_excursion_next_3bars | False | True | 1969 | 390 | 0 | 0 | 1579 | phase_1_subset_feasibility |
| immediate_follow_through_quality | breakout_hold_duration_bars | False | True | 1969 | 390 | 0 | 0 | 1579 | phase_1_subset_feasibility |
| micro_failure_signals | failed_break_count_prebreak | True | True | 1969 | 390 | 0 | 0 | 1579 | phase_1_subset_feasibility |
| micro_failure_signals | rejection_wick_ratio | True | True | 1969 | 390 | 0 | 0 | 1579 | phase_1_subset_feasibility |
| micro_failure_signals | false_break_attempts_prebreak | True | True | 1969 | 390 | 0 | 0 | 1579 | phase_1_subset_feasibility |
| phase_2_prerequisite | full_historical_intraday_ingestion | False | False | 1969 | 390 | 0 | 0 | 1579 | phase_2_full_historical_archive_required |

## Prediction Metrics

| window_mode | feature_set | target | model | scope | accuracy | majority_baseline_accuracy | lift_vs_baseline | bad_state_recall | clean_state_precision | ranking_correlation | coverage_trade_count | coverage_ratio | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| entry_only | core_only | bad_state | majority | eval |  |  |  |  |  |  | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | bad_state | band_probability | eval |  |  |  |  |  |  | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | bad_state | logistic | eval |  |  |  |  |  |  | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | clean_state | majority | eval |  |  |  |  |  |  | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | clean_state | band_probability | eval |  |  |  |  |  |  | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | clean_state | logistic | eval |  |  |  |  |  |  | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | continuation_quality_rank | majority | eval |  |  |  |  |  |  | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | continuation_quality_rank | band_probability | eval |  |  |  |  |  |  | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | continuation_quality_rank | logistic | eval |  |  |  |  |  |  | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | bad_state | majority | eval |  |  |  |  |  |  | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | bad_state | band_probability | eval |  |  |  |  |  |  | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | bad_state | logistic | eval |  |  |  |  |  |  | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | clean_state | majority | eval |  |  |  |  |  |  | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | clean_state | band_probability | eval |  |  |  |  |  |  | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | clean_state | logistic | eval |  |  |  |  |  |  | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | continuation_quality_rank | majority | eval |  |  |  |  |  |  | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | continuation_quality_rank | band_probability | eval |  |  |  |  |  |  | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | continuation_quality_rank | logistic | eval |  |  |  |  |  |  | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | bad_state | majority | full_period |  |  |  |  |  |  | 390 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | bad_state | band_probability | full_period |  |  |  |  |  |  | 390 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | bad_state | logistic | full_period |  |  |  |  |  |  | 390 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | clean_state | majority | full_period |  |  |  |  |  |  | 390 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | clean_state | band_probability | full_period |  |  |  |  |  |  | 390 | 0 | insufficient_intraday_coverage |
| entry_only | core_only | clean_state | logistic | full_period |  |  |  |  |  |  | 390 | 0 | insufficient_intraday_coverage |

## Holdout Results

| window_mode | feature_set | target | model | holdout_type | holdout_value | coverage_trade_count | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| entry_only | core_only | bad_state | band_probability | symbol |  | 0 | insufficient_intraday_coverage |
| entry_only | core_only | bad_state | band_probability | sector_bucket |  | 0 | insufficient_intraday_coverage |
| entry_only | core_only | bad_state | band_probability | scenario |  | 0 | insufficient_intraday_coverage |
| entry_only | core_only | bad_state | band_probability | time_split_oos |  | 0 | insufficient_intraday_coverage |
| entry_only | core_only | clean_state | band_probability | symbol |  | 0 | insufficient_intraday_coverage |
| entry_only | core_only | clean_state | band_probability | sector_bucket |  | 0 | insufficient_intraday_coverage |
| entry_only | core_only | clean_state | band_probability | scenario |  | 0 | insufficient_intraday_coverage |
| entry_only | core_only | clean_state | band_probability | time_split_oos |  | 0 | insufficient_intraday_coverage |
| entry_only | intraday_only_entry_only | bad_state | band_probability | symbol |  | 0 | insufficient_intraday_coverage |
| entry_only | intraday_only_entry_only | bad_state | band_probability | sector_bucket |  | 0 | insufficient_intraday_coverage |
| entry_only | intraday_only_entry_only | bad_state | band_probability | scenario |  | 0 | insufficient_intraday_coverage |
| entry_only | intraday_only_entry_only | bad_state | band_probability | time_split_oos |  | 0 | insufficient_intraday_coverage |
| entry_only | intraday_only_entry_only | clean_state | band_probability | symbol |  | 0 | insufficient_intraday_coverage |
| entry_only | intraday_only_entry_only | clean_state | band_probability | sector_bucket |  | 0 | insufficient_intraday_coverage |
| entry_only | intraday_only_entry_only | clean_state | band_probability | scenario |  | 0 | insufficient_intraday_coverage |
| entry_only | intraday_only_entry_only | clean_state | band_probability | time_split_oos |  | 0 | insufficient_intraday_coverage |
| entry_only | intraday_only_immediate_post_break | bad_state | band_probability | symbol |  | 0 | insufficient_intraday_coverage |
| entry_only | intraday_only_immediate_post_break | bad_state | band_probability | sector_bucket |  | 0 | insufficient_intraday_coverage |
| entry_only | intraday_only_immediate_post_break | bad_state | band_probability | scenario |  | 0 | insufficient_intraday_coverage |
| entry_only | intraday_only_immediate_post_break | bad_state | band_probability | time_split_oos |  | 0 | insufficient_intraday_coverage |
| entry_only | intraday_only_immediate_post_break | clean_state | band_probability | symbol |  | 0 | insufficient_intraday_coverage |
| entry_only | intraday_only_immediate_post_break | clean_state | band_probability | sector_bucket |  | 0 | insufficient_intraday_coverage |
| entry_only | intraday_only_immediate_post_break | clean_state | band_probability | scenario |  | 0 | insufficient_intraday_coverage |
| entry_only | intraday_only_immediate_post_break | clean_state | band_probability | time_split_oos |  | 0 | insufficient_intraday_coverage |

## Economic Action Test

| window_mode | feature_set | policy_name | scope | baseline_expectancy | diagnostic_expectancy | baseline_return_proxy | diagnostic_return_proxy | saved_loss | missed_gain | trade_count | diagnostic_trade_count | coverage_trade_count | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| entry_only | core_only | bad_skip_clean_fullsize | anchored_oos |  |  |  |  |  |  | 0 | 0 | 0 | insufficient_intraday_coverage |
| entry_only | intraday_only_entry_only | bad_skip_clean_fullsize | anchored_oos |  |  |  |  |  |  | 0 | 0 | 0 | insufficient_intraday_coverage |
| entry_only | intraday_only_immediate_post_break | bad_skip_clean_fullsize | anchored_oos |  |  |  |  |  |  | 0 | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_plus_intraday_entry_only | bad_skip_clean_fullsize | anchored_oos |  |  |  |  |  |  | 0 | 0 | 0 | insufficient_intraday_coverage |
| entry_only | core_plus_intraday_immediate_post_break | bad_skip_clean_fullsize | anchored_oos |  |  |  |  |  |  | 0 | 0 | 0 | insufficient_intraday_coverage |
| entry_only | intraday_plus_volume | bad_skip_clean_fullsize | anchored_oos |  |  |  |  |  |  | 0 | 0 | 0 | insufficient_intraday_coverage |
| entry_only | intraday_plus_vwap | bad_skip_clean_fullsize | anchored_oos |  |  |  |  |  |  | 0 | 0 | 0 | insufficient_intraday_coverage |
| entry_only | all_combined_entry_only | bad_skip_clean_fullsize | anchored_oos |  |  |  |  |  |  | 0 | 0 | 0 | insufficient_intraday_coverage |
| entry_only | all_combined_immediate_post_break | bad_skip_clean_fullsize | anchored_oos |  |  |  |  |  |  | 0 | 0 | 0 | insufficient_intraday_coverage |
| immediate_post_break | core_only | bad_skip_clean_fullsize | anchored_oos |  |  |  |  |  |  | 0 | 0 | 0 | insufficient_intraday_coverage |
| immediate_post_break | intraday_only_entry_only | bad_skip_clean_fullsize | anchored_oos |  |  |  |  |  |  | 0 | 0 | 0 | insufficient_intraday_coverage |
| immediate_post_break | intraday_only_immediate_post_break | bad_skip_clean_fullsize | anchored_oos |  |  |  |  |  |  | 0 | 0 | 0 | insufficient_intraday_coverage |
| immediate_post_break | core_plus_intraday_entry_only | bad_skip_clean_fullsize | anchored_oos |  |  |  |  |  |  | 0 | 0 | 0 | insufficient_intraday_coverage |
| immediate_post_break | core_plus_intraday_immediate_post_break | bad_skip_clean_fullsize | anchored_oos |  |  |  |  |  |  | 0 | 0 | 0 | insufficient_intraday_coverage |
| immediate_post_break | intraday_plus_volume | bad_skip_clean_fullsize | anchored_oos |  |  |  |  |  |  | 0 | 0 | 0 | insufficient_intraday_coverage |
| immediate_post_break | intraday_plus_vwap | bad_skip_clean_fullsize | anchored_oos |  |  |  |  |  |  | 0 | 0 | 0 | insufficient_intraday_coverage |
| immediate_post_break | all_combined_entry_only | bad_skip_clean_fullsize | anchored_oos |  |  |  |  |  |  | 0 | 0 | 0 | insufficient_intraday_coverage |
| immediate_post_break | all_combined_immediate_post_break | bad_skip_clean_fullsize | anchored_oos |  |  |  |  |  |  | 0 | 0 | 0 | insufficient_intraday_coverage |

## Final Answer

- Entry-only track is the deployable-relevance test.
- Immediate-post-break track is the micro-confirmation feasibility test.
- If current intraday archive has no overlap or no stable signal, Phase 2 historical intraday ingestion is required before any production conclusion.