# Task 356 - Event-Shock Regime Audit

- decision: NEW_REGIME_BREAKDOWN
- best_match_episode: russia_invasion_shock
- best_match_similarity_score: 0.271576
- best_shock_rule: shock_skip_rule

## Final Interpretation
1. This task compares the current anchored OOS failure window against explicit historical shock episodes rather than searching for new alpha.
2. Final decision: `NEW_REGIME_BREAKDOWN`
3. Best historical match: `russia_invasion_shock`
4. Best fixed shock-aware rule: `shock_skip_rule`

## Event Episode Library
| episode_name | family | start_date | end_date | pool_trade_count | selected_trade_count | selected_net_pnl_r | selected_expectancy | selected_cost_adjusted_expectancy | selected_pnl_retention_ratio | selected_gross_pnl_r | opening_drive_net_pnl_r | post_confirmation_net_pnl_r | timing_sensitivity_open_minus_post | avg_same_day_candidate_count | avg_same_day_sector_candidate_count | first_30m_share | semis_share | strong_execution_share | execution_bucket_mix | sector_mix | combined_stress_retention |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| russia_invasion_shock | war_shock | 2022-02-24 | 2022-04-30 | 39 | 7 | -0.232504 | -0.002143 | -0.033215 | 15.4965 | -0.015004 | -0.490558 | -0.232504 | -0.258054 | 9.20513 | 8.28205 | 0.205128 | 0.487179 | 0.461538 | unknown:0.538;strong:0.462 | semis:0.487;others:0.41;software_internet:0.103 | 6.61264 |
| banking_stress_shock | financial_stress | 2023-03-08 | 2023-04-14 | 13 | 2 | -0.017583 | 0.028709 | -0.008791 | -0.306227 | 0.057417 | -0.017583 | -0.017583 | 0 | 14.3846 | 14.3846 | 0 | 0 | 0.307692 | unknown:0.692;strong:0.308 | software_internet:1.0 | -1.61245 |
| macro_rate_shock | macro_rate_shock | 2022-06-10 | 2022-07-31 | 31 | 5 | -0.227481 | -0.021496 | -0.045496 | 2.11648 | -0.107481 | -0.227481 | -0.227481 | 0 | 8.74193 | 8.29032 | 0 | 0.548387 | 0.548387 | strong:0.548;unknown:0.452 | semis:0.548;others:0.323;software_internet:0.129 | 3.23296 |
| post_risk_off_rebound_shock | post_risk_off_rebound | 2022-10-13 | 2022-11-30 | 57 | 6 | -0.003751 | 0.018125 | -0.000625 | -0.034491 | 0.108749 | -0.003751 | -0.003751 | 0 | 16.3333 | 9.5614 | 0.122807 | 0.298246 | 0.526316 | strong:0.526;unknown:0.439;mixed:0.035 | software_internet:0.526;semis:0.298;others:0.175 | -1.6866 |
| current_failure_window | current_failure | 2025-12-01 | 2026-01-31 | 50 | 7 | -0.629882 | -0.06534 | -0.089983 | 1.37715 | -0.457382 | -0.487287 | -0.629882 | 0.142595 | 11.16 | 9.36 | 0.4 | 0.62 | 0.78 | strong:0.78;unknown:0.22 | semis:0.62;others:0.38 | 1.60539 |

## Shock Regime Similarity
| current_episode | comparison_episode | trade_count_current | trade_count_comparison | dispersion_similarity | correlation_similarity | same_day_intensity_similarity | same_day_sector_intensity_similarity | gap_state_overlap | breadth_state_overlap | sector_leadership_overlap | shock_regime_similarity_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_failure_window | russia_invasion_shock | 50 | 39 | 0 | 0 | 0.944147 | 0.956882 | 0 | 0 | 0 | 0.271576 |
| current_failure_window | macro_rate_shock | 50 | 31 | 0 | 0 | 0.930912 | 0.957213 | 0 | 0 | 0 | 0.269732 |
| current_failure_window | post_risk_off_rebound_shock | 50 | 57 | 0 | 0 | 0.85219 | 0.991944 | 0 | 0 | 0 | 0.263448 |
| current_failure_window | banking_stress_shock | 50 | 13 | 0 | 0 | 0.907868 | 0.799015 | 0 | 0 | 0 | 0.243841 |

## Current vs Russia War
| current_episode | comparison_episode | trade_count_current | trade_count_comparison | dispersion_similarity | correlation_similarity | same_day_intensity_similarity | same_day_sector_intensity_similarity | gap_state_overlap | breadth_state_overlap | sector_leadership_overlap | shock_regime_similarity_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_failure_window | russia_invasion_shock | 50 | 39 | 0 | 0 | 0.944147 | 0.956882 | 0 | 0 | 0 | 0.271576 |

## Shock Family Comparison
| episode_name | family | start_date | end_date | pool_trade_count | selected_trade_count | selected_net_pnl_r | selected_expectancy | selected_cost_adjusted_expectancy | selected_pnl_retention_ratio | selected_gross_pnl_r | opening_drive_net_pnl_r | post_confirmation_net_pnl_r | timing_sensitivity_open_minus_post | avg_same_day_candidate_count | avg_same_day_sector_candidate_count | first_30m_share | semis_share | strong_execution_share | execution_bucket_mix | sector_mix | combined_stress_retention | shock_regime_similarity_score | current_window_net_pnl_r | current_window_semis_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| russia_invasion_shock | war_shock | 2022-02-24 | 2022-04-30 | 39 | 7 | -0.232504 | -0.002143 | -0.033215 | 15.4965 | -0.015004 | -0.490558 | -0.232504 | -0.258054 | 9.20513 | 8.28205 | 0.205128 | 0.487179 | 0.461538 | unknown:0.538;strong:0.462 | semis:0.487;others:0.41;software_internet:0.103 | 6.61264 | 0.271576 | -0.629882 | 0.62 |
| macro_rate_shock | macro_rate_shock | 2022-06-10 | 2022-07-31 | 31 | 5 | -0.227481 | -0.021496 | -0.045496 | 2.11648 | -0.107481 | -0.227481 | -0.227481 | 0 | 8.74193 | 8.29032 | 0 | 0.548387 | 0.548387 | strong:0.548;unknown:0.452 | semis:0.548;others:0.323;software_internet:0.129 | 3.23296 | 0.269732 | -0.629882 | 0.62 |
| post_risk_off_rebound_shock | post_risk_off_rebound | 2022-10-13 | 2022-11-30 | 57 | 6 | -0.003751 | 0.018125 | -0.000625 | -0.034491 | 0.108749 | -0.003751 | -0.003751 | 0 | 16.3333 | 9.5614 | 0.122807 | 0.298246 | 0.526316 | strong:0.526;unknown:0.439;mixed:0.035 | software_internet:0.526;semis:0.298;others:0.175 | -1.6866 | 0.263448 | -0.629882 | 0.62 |
| banking_stress_shock | financial_stress | 2023-03-08 | 2023-04-14 | 13 | 2 | -0.017583 | 0.028709 | -0.008791 | -0.306227 | 0.057417 | -0.017583 | -0.017583 | 0 | 14.3846 | 14.3846 | 0 | 0 | 0.307692 | unknown:0.692;strong:0.308 | software_internet:1.0 | -1.61245 | 0.243841 | -0.629882 | 0.62 |
| current_failure_window | current_failure | 2025-12-01 | 2026-01-31 | 50 | 7 | -0.629882 | -0.06534 | -0.089983 | 1.37715 | -0.457382 | -0.487287 | -0.629882 | 0.142595 | 11.16 | 9.36 | 0.4 | 0.62 | 0.78 | strong:0.78;unknown:0.22 | semis:0.62;others:0.38 | 1.60539 |  | -0.629882 | 0.62 |

## Shock-Conditional Deployment
| deployment_rule | episode_name | family | trade_count | net_pnl_r | cost_adjusted_expectancy | pnl_retention_ratio | rolling_oos_robustness | anchored_oos_cost_adjusted_expectancy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| shock_skip_rule | all_historical_shocks | aggregate | 0 | 0 |  |  | 0 |  |
| shock_competition_relax | all_historical_shocks | aggregate | 52 | -0.20753 | -0.003991 | -0.892715 | 0 |  |
| shock_semis_cap | all_historical_shocks | aggregate | 20 | -0.386666 | -0.019333 | -6.92534 | 0 |  |
| baseline_deployment | all_historical_shocks | aggregate | 20 | -0.481318 | -0.024066 | -11.0187 | 0 |  |
| shock_timing_downgrade | all_historical_shocks | aggregate | 20 | -0.739373 | -0.036969 | 3.12139 | 0 |  |
| shock_skip_rule | banking_stress_shock | financial_stress | 0 | 0 |  |  | 0 |  |
| shock_competition_relax | banking_stress_shock | financial_stress | 6 | -0.008264 | -0.001377 | -0.123826 | 0 |  |
| baseline_deployment | banking_stress_shock | financial_stress | 2 | -0.017583 | -0.008791 | -0.306227 | 0 |  |
| shock_timing_downgrade | banking_stress_shock | financial_stress | 2 | -0.017583 | -0.008791 | -0.306227 | 0 |  |
| shock_semis_cap | banking_stress_shock | financial_stress | 2 | -0.017583 | -0.008791 | -0.306227 | 0 |  |
| shock_skip_rule | current_failure_window | current_failure | 0 | 0 |  |  | 0 |  |
| shock_semis_cap | current_failure_window | current_failure | 7 | -0.246795 | -0.035256 | 1.94641 | 0 | -0.035256 |
| shock_timing_downgrade | current_failure_window | current_failure | 7 | -0.487287 | -0.069612 | 1.44473 | 0 | -0.069612 |
| shock_competition_relax | current_failure_window | current_failure | 19 | -0.607525 | -0.031975 | 1.34252 | 0 | -0.031975 |
| baseline_deployment | current_failure_window | current_failure | 7 | -0.629882 | -0.089983 | 1.37715 | 0 | -0.089983 |
| shock_skip_rule | macro_rate_shock | macro_rate_shock | 0 | 0 |  |  | 0 |  |
| shock_competition_relax | macro_rate_shock | macro_rate_shock | 13 | -0.083531 | -0.006425 | -7.28296 | 0 |  |
| shock_semis_cap | macro_rate_shock | macro_rate_shock | 5 | -0.19514 | -0.039028 | 2.16485 | 0 |  |
| baseline_deployment | macro_rate_shock | macro_rate_shock | 5 | -0.227481 | -0.045496 | 2.11648 | 0 |  |
| shock_timing_downgrade | macro_rate_shock | macro_rate_shock | 5 | -0.227481 | -0.045496 | 2.11648 | 0 |  |
| shock_competition_relax | post_risk_off_rebound_shock | post_risk_off_rebound | 16 | 0.027655 | 0.001728 | 0.21248 | 0 |  |
| shock_skip_rule | post_risk_off_rebound_shock | post_risk_off_rebound | 0 | 0 |  |  | 0 |  |
| baseline_deployment | post_risk_off_rebound_shock | post_risk_off_rebound | 6 | -0.003751 | -0.000625 | -0.034491 | 0 |  |
| shock_timing_downgrade | post_risk_off_rebound_shock | post_risk_off_rebound | 6 | -0.003751 | -0.000625 | -0.034491 | 0 |  |
| shock_semis_cap | post_risk_off_rebound_shock | post_risk_off_rebound | 6 | -0.066833 | -0.011139 | -5.60818 | 0 |  |
| shock_skip_rule | russia_invasion_shock | war_shock | 0 | 0 |  |  | 0 |  |
| shock_semis_cap | russia_invasion_shock | war_shock | 7 | -0.107111 | -0.015302 | -1.39759 | 0 |  |
| shock_competition_relax | russia_invasion_shock | war_shock | 17 | -0.143391 | -0.008435 | -5.94757 | 0 |  |
| baseline_deployment | russia_invasion_shock | war_shock | 7 | -0.232504 | -0.033215 | 15.4965 | 0 |  |
| shock_timing_downgrade | russia_invasion_shock | war_shock | 7 | -0.490558 | -0.07008 | 1.65977 | 0 |  |