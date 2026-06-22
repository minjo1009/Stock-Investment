# Task 357 - Endogenous State-Gated Continuation Allocator

- decision: STATE_GATED_CONTINUATION
- best_framework_name: full_dislocation_mode
- best_anchored_oos_net_pnl_r: -0.564779

## Final Interpretation
1. This task redesigns the continuation sleeve as a state-aware allocator rather than searching for new alpha.
2. Final decision: `STATE_GATED_CONTINUATION`
3. Best framework: `full_dislocation_mode`

## State Detector Diagnostics
| scope | bucket_a | bucket_b | trade_count | trade_share | semis_share | first_30m_or_unknown_share |
| --- | --- | --- | --- | --- | --- | --- |
| by_split | anchored_oos | crowded_dislocation_state | 41 | 0.465909 | 0.756098 | 0.707317 |
| by_split | anchored_oos | normal_continuation_state | 33 | 0.375 | 0 | 0.636364 |
| by_split | anchored_oos | uncertain_transition_state | 14 | 0.159091 | 0 | 0.428571 |
| by_split | train | crowded_dislocation_state | 452 | 0.346892 | 0.809735 | 0.829646 |
| by_split | train | normal_continuation_state | 557 | 0.427475 | 0.197487 | 0.662478 |
| by_split | train | uncertain_transition_state | 294 | 0.225633 | 0.289116 | 0.965986 |
| current_failure_window | 2025-12-01 | crowded_dislocation_state | 41 | 0.82 | 0.756098 | 0.707317 |
| current_failure_window | 2025-12-01 | normal_continuation_state | 7 | 0.14 | 0 | 0 |
| current_failure_window | 2025-12-01 | uncertain_transition_state | 2 | 0.04 | 0 | 1 |

## Framework Comparison
| structure_name | allocator_name | trade_count | signals_seen | signals_selected | selection_rate | avg_rank_of_selected_signal | expectancy | cost_adjusted_expectancy | sharpe_proxy | mdd_pct | capital_utilization | concentration | gross_pnl_r | net_pnl_r | gross_return_pct | net_return_pct | annualized_pnl_proxy | pnl_per_trade | pnl_per_active_day | max_peak_to_trough_pnl_drawdown | anchored_oos_net_pnl_r | rolling_window_net_pnl_r | rolling_oos_robustness | anchored_oos_cost_adjusted_expectancy | pnl_retention_ratio | pnl_lost_due_to_competition | framework_name | allocator_variant | anchored_oos_drawdown | semis_loss_share | first30_or_unknown_loss_share | crowded_state_trade_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sizing_template_aggressive | marginal_utility_allocator | 336 | 336 | 336 | 1 |  | 0.068535 | 0.053587 | 0.581051 | 2.5941 | 0.546713 | 0.240951 | 23.0277 | 18.0052 | 25.7831 | 19.6258 | 3.74553 | 0.053587 | 0.113957 | 2.5941 | -0.564779 | 3.53373 | 0.75 | -0.029725 | 0.781894 |  | full_dislocation_mode | marginal_utility_allocator | 2.5941 | 0 | 0.496195 | 0 |
| sizing_template_aggressive | marginal_utility_allocator | 395 | 395 | 395 | 1 |  | 0.026023 | 0.02004 | 0.519161 | 1.35191 | 0.750865 | 0.262674 | 10.2789 | 7.91582 | 10.8019 | 8.2153 | 1.63327 | 0.02004 | 0.036478 | 1.35191 | -0.723812 | 1.72331 | 0.75 | -0.030159 | 0.7701 |  | state_gated_allocator_plus_staged_execution | marginal_utility_allocator | 1.35191 | 0.280558 | 0.585506 | 0.149367 |
| sizing_template_aggressive | fragility_adjusted_allocator | 395 | 395 | 395 | 1 |  | 0.061324 | 0.04719 | 0.573105 | 1.8017 | 0.750865 | 0.245463 | 24.2231 | 18.64 | 27.3049 | 20.3962 | 3.88228 | 0.04719 | 0.085899 | 1.8017 | -1.00418 | 3.43151 | 0.75 | -0.041841 | 0.769513 |  | state_gated_allocator_plus_semis_factor_cap | fragility_adjusted_allocator | 1.8017 | 0.280558 | 0.585506 | 0.149367 |
| sizing_template_aggressive | baseline_rank_allocator | 217 | 217 | 217 | 1 |  | 0.173545 | 0.136149 | 0.563039 | 3.13041 | 0.750865 | 0.193287 | 37.6593 | 29.5443 | 45.1488 | 33.8546 | 6.16582 | 0.136149 | 0.136149 | 3.13041 | -1.28962 | 5.30283 | 0.75 | -0.107468 | 0.784516 |  | current_baseline_sleeve | baseline_rank_allocator | 3.13041 | 0.490485 | 0.778672 | 0.271889 |
| sizing_template_aggressive | state_gated_allocator | 442 | 442 | 442 | 1 |  | 0.077887 | 0.061225 | 0.569005 | 2.55527 | 0.750865 | 0.179389 | 34.4262 | 27.0612 | 40.8896 | 30.8937 | 5.67964 | 0.061225 | 0.124706 | 2.55527 | -1.38727 | 4.80075 | 0.75 | -0.057803 | 0.786064 |  | state_gated_allocator_only | state_gated_allocator | 2.55527 | 0.280558 | 0.585506 | 0.133484 |

## Factor Netting Effect
| framework_name | trade_count | anchored_trade_count | semis_trade_share | anchored_semis_trade_share | avg_same_day_sector_candidate_count | avg_marginal_penalty |
| --- | --- | --- | --- | --- | --- | --- |
| current_baseline_sleeve | 217 | 12 | 0.373272 | 0.333333 | 6.09677 | 0 |
| state_gated_allocator_only | 442 | 24 | 0.294118 | 0.166667 | 5.89593 | 1.07738 |
| state_gated_allocator_plus_semis_factor_cap | 395 | 24 | 0.210127 | 0.166667 | 5.9443 | 0.921772 |
| state_gated_allocator_plus_staged_execution | 395 | 24 | 0.210127 | 0.166667 | 5.9443 | 0.936709 |

## Staged Execution Comparison
| framework_name | participation_stage | trade_count | avg_stage_weight | expectancy | semis_share | crowded_state_share |
| --- | --- | --- | --- | --- | --- | --- |
| current_baseline_sleeve | full_participation | 217 | 1 | 0.652269 | 0.373272 | 0.271889 |
| state_gated_allocator_plus_staged_execution | delayed_probe | 1 | 0.6 | -1.01478 | 0 | 0 |
| state_gated_allocator_plus_staged_execution | stage_1_probe | 300 | 0.2075 | 0.660947 | 0.243333 | 0.19 |
| state_gated_allocator_plus_staged_execution | stage_2_add | 94 | 1 | 0.529826 | 0.106383 | 0.021277 |

## Failure Cluster Contribution
| dimension | bucket | trade_count | gross_pnl_r | loss_share | expectancy | framework_name |
| --- | --- | --- | --- | --- | --- | --- |
| execution_quality_bucket | strong | 6 | -3.96307 | 0.522253 | -0.660512 | current_baseline_sleeve |
| month | 2026-01 | 5 | -2.71892 | 0.496796 | -0.543785 | current_baseline_sleeve |
| quarter | 2026Q1 | 5 | -2.71892 | 0.496796 | -0.543785 | current_baseline_sleeve |
| sector_group | semis | 4 | -3.98883 | 0.490485 | -0.997207 | current_baseline_sleeve |
| session_timing_bucket | unknown | 6 | -0.569857 | 0.477747 | -0.094976 | current_baseline_sleeve |
| execution_quality_bucket | unknown | 6 | -0.569857 | 0.477747 | -0.094976 | current_baseline_sleeve |
| month | 2026-04 | 4 | -0.8843 | 0.353949 | -0.221075 | current_baseline_sleeve |
| quarter | 2026Q2 | 4 | -0.8843 | 0.353949 | -0.221075 | current_baseline_sleeve |
| same_day_candidate_count | 7 | 3 | -2.50782 | 0.333941 | -0.835939 | current_baseline_sleeve |
| session_timing_bucket | first_30m | 4 | -2.16314 | 0.300925 | -0.540786 | current_baseline_sleeve |
| sector_group | others | 5 | -0.75063 | 0.280333 | -0.150126 | current_baseline_sleeve |
| symbol | AMD | 2 | -2.24021 | 0.275467 | -1.12011 | current_baseline_sleeve |
| symbol | COST | 3 | -0.545384 | 0.229527 | -0.181795 | current_baseline_sleeve |
| symbol | NFLX | 1 | -1.8638 | 0.229182 | -1.8638 | current_baseline_sleeve |
| sector_group | software_internet | 3 | 0.206526 | 0.229182 | 0.068842 | current_baseline_sleeve |
| symbol | QCOM | 2 | -1.74861 | 0.215018 | -0.874307 | current_baseline_sleeve |
| same_day_candidate_count | 10 | 3 | 0.425068 | 0.167375 | 0.141689 | current_baseline_sleeve |
| same_day_candidate_count | 2 | 2 | 0.087785 | 0.151669 | 0.043893 | current_baseline_sleeve |
| month | 2025-12 | 2 | -1.21381 | 0.149256 | -0.606904 | current_baseline_sleeve |
| quarter | 2025Q4 | 3 | -0.929708 | 0.149256 | -0.309903 | current_baseline_sleeve |