# Task 335: Information Layer Expansion

- Final decision: `NO_INFORMATION_EDGE`.
- Best bad-state feature set: `core_only` via `band_probability`.
- Best clean-state feature set: `core_only` via `band_probability`.

## Feature Family Definitions

| family_name | phase | status | feature_count_defined | feature_count_available | features_defined | features_available | rationale |
| --- | --- | --- | --- | --- | --- | --- | --- |
| core | phase_1 | available | 10 | 10 | ret_20d_pre|dist_to_sma200_pct|rs_percentile_20d|sector_breadth|vol_contraction_ratio|breakout_strength_pct|extension_pressure_state|trend_quality_state|participation_quality_state|noise_pressure_state | ret_20d_pre|dist_to_sma200_pct|rs_percentile_20d|sector_breadth|vol_contraction_ratio|breakout_strength_pct|extension_pressure_state|trend_quality_state|participation_quality_state|noise_pressure_state | Task 334 core pre-entry feature set retained as baseline. |
| intraday_structure_proxy | phase_1 | available | 6 | 6 | gap_over_planned_entry_pct|pre_breakout_distance_pct|breakout_strength_pct|close_location_pre|range_width_10_pre|squeeze_quality | gap_over_planned_entry_pct|pre_breakout_distance_pct|breakout_strength_pct|close_location_pre|range_width_10_pre|squeeze_quality | Daily/history proxies for breakout execution quality without minute-level data. |
| volume_participation | phase_1 | available | 4 | 4 | volume_confirmation_pre|vol_contraction_ratio|dollar_volume_pre|turnover_pre | volume_confirmation_pre|vol_contraction_ratio|dollar_volume_pre|turnover_pre | Proxy for real demand and participation quality using pre-entry volume context. |
| market_structure | phase_1 | available | 5 | 5 | breadth_above_sma20|breadth_above_sma50|breadth_positive_20d|dispersion_20d|mean_pairwise_corr | breadth_above_sma20|breadth_above_sma50|breadth_positive_20d|dispersion_20d|mean_pairwise_corr | Overall market context and cohesion before breakout. |
| setup_context | phase_1 | available | 5 | 5 | pre_breakout_distance_pct|recent_failed_breakouts_20d|breakout_strength_pct|gap_over_planned_entry_pct|range_width_10_pre | pre_breakout_distance_pct|recent_failed_breakouts_20d|breakout_strength_pct|gap_over_planned_entry_pct|range_width_10_pre | Breakout setup quality and nearby failure pressure. |
| crowding_concentration | phase_1 | available | 5 | 5 | top_sector_dominance_score|semis_concentration_ratio|tech_concentration_ratio|sector_crowding_high|sector_rs_percentile | top_sector_dominance_score|semis_concentration_ratio|tech_concentration_ratio|sector_crowding_high|sector_rs_percentile | Crowding and concentration pressure before breakout. |
| intraday_structure_true | phase_2_definition_only | definition_only | 5 | 0 | intraday_volume_surge|breakout_bar_volume_percentile|intraday_range_expansion_ratio|vwap_deviation_at_breakout|same_session_follow_through |  | Phase 2 slot for real intraday breakout-quality measures once historical intraday data exists. |
| volume_participation_true | phase_2_definition_only | definition_only | 3 | 0 | breakout_window_volume_concentration|volume_persistence_after_breakout|volume_imbalance_proxy |  | Phase 2 slot for true breakout-window participation measures once intraday data exists. |

## Feature Family Ablation

| target | scope | model | accuracy | majority_baseline_accuracy | lift_vs_baseline | bad_state_recall | clean_state_precision | family_name | feature_count | status | feature_set | selected_best_2_members | selected_best_3_members | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bad_state | anchored_oos | band_probability | 0.761194 | 0.761194 | 0 | 1 |  | core_only | 10 | available | core_only |  |  | discard |
| bad_state | anchored_oos | logistic | 0.567164 | 0.761194 | -0.19403 | 0.568627 |  | core_only | 10 | available | core_only |  |  | discard |
| bad_state | anchored_oos | majority | 0.761194 | 0.761194 | 0 | 1 |  | core_only | 10 | available | core_only |  |  | discard |
| clean_state | anchored_oos | band_probability | 0.825871 | 0.825871 | 0 |  | 0 | core_only | 10 | available | core_only |  |  | discard |
| clean_state | anchored_oos | logistic | 0.825871 | 0.825871 | 0 |  | 0 | core_only | 10 | available | core_only |  |  | discard |
| clean_state | anchored_oos | majority | 0.825871 | 0.825871 | 0 |  | 0 | core_only | 10 | available | core_only |  |  | discard |
| continuation_quality_rank | anchored_oos | band_probability | 0.761194 | 0.761194 | 0 |  |  | core_only | 10 | available | core_only |  |  |  |
| continuation_quality_rank | anchored_oos | logistic | 0.736318 | 0.761194 | -0.024876 |  |  | core_only | 10 | available | core_only |  |  |  |
| continuation_quality_rank | anchored_oos | majority | 0.761194 | 0.761194 | 0 |  |  | core_only | 10 | available | core_only |  |  |  |
| multiclass | anchored_oos | band_probability | 0.283582 | 0.333333 | -0.049751 |  |  | core_only | 10 | available | core_only |  |  |  |
| multiclass | anchored_oos | logistic | 0.109453 | 0.333333 | -0.223881 |  |  | core_only | 10 | available | core_only |  |  |  |
| multiclass | anchored_oos | majority | 0.333333 | 0.333333 | 0 |  |  | core_only | 10 | available | core_only |  |  |  |
| bad_state | anchored_oos | band_probability | 0.761194 | 0.761194 | 0 | 1 |  | core_plus_best_2_families | 20 | available | core_plus_best_2_families | core_plus_crowding_concentration|core_plus_intraday_structure_proxy |  | discard |
| bad_state | anchored_oos | logistic | 0.58209 | 0.761194 | -0.179104 | 0.764706 |  | core_plus_best_2_families | 20 | available | core_plus_best_2_families | core_plus_crowding_concentration|core_plus_intraday_structure_proxy |  | discard |
| bad_state | anchored_oos | majority | 0.761194 | 0.761194 | 0 | 1 |  | core_plus_best_2_families | 20 | available | core_plus_best_2_families | core_plus_crowding_concentration|core_plus_intraday_structure_proxy |  | discard |
| clean_state | anchored_oos | band_probability | 0.825871 | 0.825871 | 0 |  | 0 | core_plus_best_2_families | 20 | available | core_plus_best_2_families | core_plus_crowding_concentration|core_plus_intraday_structure_proxy |  | discard |
| clean_state | anchored_oos | logistic | 0.825871 | 0.825871 | 0 |  | 0 | core_plus_best_2_families | 20 | available | core_plus_best_2_families | core_plus_crowding_concentration|core_plus_intraday_structure_proxy |  | discard |
| clean_state | anchored_oos | majority | 0.825871 | 0.825871 | 0 |  | 0 | core_plus_best_2_families | 20 | available | core_plus_best_2_families | core_plus_crowding_concentration|core_plus_intraday_structure_proxy |  | discard |
| continuation_quality_rank | anchored_oos | band_probability | 0.761194 | 0.761194 | 0 |  |  | core_plus_best_2_families | 20 | available | core_plus_best_2_families | core_plus_crowding_concentration|core_plus_intraday_structure_proxy |  |  |
| continuation_quality_rank | anchored_oos | logistic | 0.761194 | 0.761194 | 0 |  |  | core_plus_best_2_families | 20 | available | core_plus_best_2_families | core_plus_crowding_concentration|core_plus_intraday_structure_proxy |  |  |
| continuation_quality_rank | anchored_oos | majority | 0.761194 | 0.761194 | 0 |  |  | core_plus_best_2_families | 20 | available | core_plus_best_2_families | core_plus_crowding_concentration|core_plus_intraday_structure_proxy |  |  |
| multiclass | anchored_oos | band_probability | 0.333333 | 0.333333 | 0 |  |  | core_plus_best_2_families | 20 | available | core_plus_best_2_families | core_plus_crowding_concentration|core_plus_intraday_structure_proxy |  |  |
| multiclass | anchored_oos | logistic | 0.119403 | 0.333333 | -0.21393 |  |  | core_plus_best_2_families | 20 | available | core_plus_best_2_families | core_plus_crowding_concentration|core_plus_intraday_structure_proxy |  |  |
| multiclass | anchored_oos | majority | 0.333333 | 0.333333 | 0 |  |  | core_plus_best_2_families | 20 | available | core_plus_best_2_families | core_plus_crowding_concentration|core_plus_intraday_structure_proxy |  |  |

## Prediction Metrics

| target | scope | model | accuracy | majority_baseline_accuracy | lift_vs_baseline | bad_state_recall | clean_state_precision | family_name | feature_count | feature_set | saved_loss_proxy | missed_gain_proxy | oos_expectancy_delta_proxy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bad_state | anchored_oos | band_probability | 0.761194 | 0.761194 | 0 | 1 |  | core_only | 10 | core_only | 119.808 | 68.0434 | 0.257538 |
| bad_state | anchored_oos | logistic | 0.567164 | 0.761194 | -0.19403 | 0.568627 |  | core_only | 10 | core_only | 119.808 | 68.0434 | 0.257538 |
| bad_state | anchored_oos | majority | 0.761194 | 0.761194 | 0 | 1 |  | core_only | 10 | core_only | 119.808 | 68.0434 | 0.257538 |
| clean_state | anchored_oos | band_probability | 0.825871 | 0.825871 | 0 |  | 0 | core_only | 10 | core_only | 119.808 | 68.0434 | 0.257538 |
| clean_state | anchored_oos | logistic | 0.825871 | 0.825871 | 0 |  | 0 | core_only | 10 | core_only | 119.808 | 68.0434 | 0.257538 |
| clean_state | anchored_oos | majority | 0.825871 | 0.825871 | 0 |  | 0 | core_only | 10 | core_only | 119.808 | 68.0434 | 0.257538 |
| continuation_quality_rank | anchored_oos | band_probability | 0.761194 | 0.761194 | 0 |  |  | core_only | 10 | core_only | 119.808 | 68.0434 | 0.257538 |
| continuation_quality_rank | anchored_oos | logistic | 0.736318 | 0.761194 | -0.024876 |  |  | core_only | 10 | core_only | 119.808 | 68.0434 | 0.257538 |
| continuation_quality_rank | anchored_oos | majority | 0.761194 | 0.761194 | 0 |  |  | core_only | 10 | core_only | 119.808 | 68.0434 | 0.257538 |
| multiclass | anchored_oos | band_probability | 0.283582 | 0.333333 | -0.049751 |  |  | core_only | 10 | core_only | 119.808 | 68.0434 | 0.257538 |
| multiclass | anchored_oos | logistic | 0.109453 | 0.333333 | -0.223881 |  |  | core_only | 10 | core_only | 119.808 | 68.0434 | 0.257538 |
| multiclass | anchored_oos | majority | 0.333333 | 0.333333 | 0 |  |  | core_only | 10 | core_only | 119.808 | 68.0434 | 0.257538 |
| bad_state | anchored_oos | band_probability | 0.761194 | 0.761194 | 0 | 1 |  | core_plus_best_2_families | 20 | core_plus_best_2_families | 119.808 | 68.0434 | 0.257538 |
| bad_state | anchored_oos | logistic | 0.58209 | 0.761194 | -0.179104 | 0.764706 |  | core_plus_best_2_families | 20 | core_plus_best_2_families | 119.808 | 68.0434 | 0.257538 |
| bad_state | anchored_oos | majority | 0.761194 | 0.761194 | 0 | 1 |  | core_plus_best_2_families | 20 | core_plus_best_2_families | 119.808 | 68.0434 | 0.257538 |
| clean_state | anchored_oos | band_probability | 0.825871 | 0.825871 | 0 |  | 0 | core_plus_best_2_families | 20 | core_plus_best_2_families | 119.808 | 68.0434 | 0.257538 |
| clean_state | anchored_oos | logistic | 0.825871 | 0.825871 | 0 |  | 0 | core_plus_best_2_families | 20 | core_plus_best_2_families | 119.808 | 68.0434 | 0.257538 |
| clean_state | anchored_oos | majority | 0.825871 | 0.825871 | 0 |  | 0 | core_plus_best_2_families | 20 | core_plus_best_2_families | 119.808 | 68.0434 | 0.257538 |
| continuation_quality_rank | anchored_oos | band_probability | 0.761194 | 0.761194 | 0 |  |  | core_plus_best_2_families | 20 | core_plus_best_2_families | 119.808 | 68.0434 | 0.257538 |
| continuation_quality_rank | anchored_oos | logistic | 0.761194 | 0.761194 | 0 |  |  | core_plus_best_2_families | 20 | core_plus_best_2_families | 119.808 | 68.0434 | 0.257538 |
| continuation_quality_rank | anchored_oos | majority | 0.761194 | 0.761194 | 0 |  |  | core_plus_best_2_families | 20 | core_plus_best_2_families | 119.808 | 68.0434 | 0.257538 |
| multiclass | anchored_oos | band_probability | 0.333333 | 0.333333 | 0 |  |  | core_plus_best_2_families | 20 | core_plus_best_2_families | 119.808 | 68.0434 | 0.257538 |
| multiclass | anchored_oos | logistic | 0.119403 | 0.333333 | -0.21393 |  |  | core_plus_best_2_families | 20 | core_plus_best_2_families | 119.808 | 68.0434 | 0.257538 |
| multiclass | anchored_oos | majority | 0.333333 | 0.333333 | 0 |  |  | core_plus_best_2_families | 20 | core_plus_best_2_families | 119.808 | 68.0434 | 0.257538 |

## Holdout Results

| target | scope | model | accuracy | majority_baseline_accuracy | lift_vs_baseline | bad_state_recall | clean_state_precision | family_name | feature_count | holdout_type | holdout_value | status | feature_set |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bad_state | train | band_probability | 0.651741 | 0.691542 | -0.039801 | 0.942446 |  | core_only | 10 | symbol | QCOM | ok |  |
| bad_state | train | band_probability | 0.564246 | 0.564246 | 0 | 1 |  | core_only | 10 | symbol | AVGO | ok |  |
| bad_state | train | band_probability | 0.488235 | 0.511765 | -0.023529 | 1 |  | core_only | 10 | symbol | COST | ok |  |
| bad_state | train | band_probability | 0.544379 | 0.544379 | 0 | 1 |  | core_only | 10 | symbol | AAPL | ok |  |
| bad_state | train | band_probability | 0.460606 | 0.539394 | -0.078788 | 1 |  | core_only | 10 | symbol | AMD | ok |  |
| bad_state | train | band_probability | 0.770186 | 0.757764 | 0.012422 | 1 |  | core_only | 10 | symbol | AMZN | ok |  |
| bad_state | train | band_probability | 0.557692 | 0.557692 | 0 | 1 |  | core_only | 10 | symbol | MSFT | ok |  |
| bad_state | train | band_probability | 0.433566 | 0.566434 | -0.132867 | 1 |  | core_only | 10 | symbol | GOOGL | ok |  |
| bad_state | train | band_probability | 0.546763 | 0.546763 | 0 | 1 |  | core_only | 10 | symbol | META | ok |  |
| bad_state | train | band_probability | 0.560976 | 0.560976 | 0 | 1 |  | core_only | 10 | symbol | NFLX | ok |  |
| bad_state | train | band_probability | 0.281553 | 0.718447 | -0.436893 | 1 |  | core_only | 10 | symbol | NVDA | ok |  |
| bad_state | train | band_probability | 0.676923 | 0.676923 | 0 | 1 |  | core_only | 10 | symbol | TSLA | ok |  |
| bad_state | train | band_probability | 0.591413 | 0.576177 | 0.015235 | 0.944712 |  | core_only | 10 | sector_bucket | software/internet | ok |  |
| bad_state | train | band_probability | 0.532407 | 0.532407 | 0 | 1 |  | core_only | 10 | sector_bucket | semis | ok |  |
| bad_state | train | band_probability | 0.581197 | 0.581197 | 0 | 1 |  | core_only | 10 | sector_bucket | other tech | ok |  |
| bad_state | train | band_probability | 0.488235 | 0.511765 | -0.023529 | 1 |  | core_only | 10 | sector_bucket | other | ok |  |
| bad_state | train | band_probability | 0.553222 | 0.553222 | 0 | 1 |  | core_only | 10 | scenario_family | RANGE_COMPRESSION | ok |  |
| bad_state | train | band_probability | 0.549618 | 0.549618 | 0 | 1 |  | core_only | 10 | scenario_family | PIVOT_HIGH | ok |  |
| bad_state | anchored_oos | band_probability | 0.578947 | 0.578947 | 0 | 1 |  |  |  | time_split_oos | 2025-11 | ok | core_only |
| bad_state | anchored_oos | band_probability | 1 | 1 | 0 | 1 |  |  |  | time_split_oos | 2025-12 | ok | core_only |
| bad_state | anchored_oos | band_probability | 0.847458 | 0.847458 | 0 | 1 |  |  |  | time_split_oos | 2026-01 | ok | core_only |
| bad_state | anchored_oos | band_probability | 0.909091 | 0.909091 | 0 | 1 |  |  |  | time_split_oos | 2026-02 | ok | core_only |
| bad_state | anchored_oos | band_probability | 1 | 1 | 0 | 1 |  |  |  | time_split_oos | 2026-03 | ok | core_only |
| bad_state | anchored_oos | band_probability | 0.45283 | 0.54717 | -0.09434 | 1 |  |  |  | time_split_oos | 2026-04 | ok | core_only |

## Economic Action Test

| scope | policy_name | baseline_expectancy | diagnostic_expectancy | baseline_return_proxy | diagnostic_return_proxy | trade_count | diagnostic_trade_count | saved_loss | missed_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anchored_oos | bad_skip_clean_fullsize | -0.257538 | 0 | -51.7651 | 0 | 201 | 0 | 119.808 | 68.0434 |
| full_period | bad_skip_clean_fullsize | 0.585221 | 0 | 1152.3 | 0 | 1969 | 0 | 808.65 | 1960.95 |
| train | bad_skip_clean_fullsize | 0.691788 | 0 | 1227.23 | 0 | 1774 | 0 | 686.066 | 1913.3 |

## Final Answer

- Current conclusion: `NO_INFORMATION_EDGE`.
- Phase 1 used repo-historical proxy families only.
- Phase 2 blind spot remains true intraday breakout-quality information such as VWAP deviation and same-session continuation.
- Next step is Phase 2 intraday ingestion only if the best Phase 1 family set shows partial edge with acceptable holdout robustness.