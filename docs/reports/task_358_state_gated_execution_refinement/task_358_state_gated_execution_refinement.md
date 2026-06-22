# Task 358 - Practical State-Gated Execution Refinement

- decision: DISLOCATION_AWARE_STAGED_SLEEVE
- best_practical_framework: confirmation_sensitive_mode
- anchored_oos_improvement_vs_baseline: 1.120956

## Final Interpretation
1. This task refines Task 357 toward a practical non-skip state-gated + staged execution sleeve.
2. Final decision: `DISLOCATION_AWARE_STAGED_SLEEVE`
3. Best practical framework: `confirmation_sensitive_mode`

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
| structure_name | allocator_name | trade_count | signals_seen | signals_selected | selection_rate | avg_rank_of_selected_signal | expectancy | cost_adjusted_expectancy | sharpe_proxy | mdd_pct | capital_utilization | concentration | gross_pnl_r | net_pnl_r | gross_return_pct | net_return_pct | annualized_pnl_proxy | pnl_per_trade | pnl_per_active_day | max_peak_to_trough_pnl_drawdown | anchored_oos_net_pnl_r | rolling_window_net_pnl_r | rolling_oos_robustness | anchored_oos_cost_adjusted_expectancy | pnl_retention_ratio | pnl_lost_due_to_competition | framework_name | allocator_variant | anchored_oos_drawdown | semis_loss_share | first30_or_unknown_loss_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sizing_template_aggressive | marginal_utility_allocator | 170 | 170 | 170 | 1 |  | 0.024766 | 0.019075 | 0.48892 | 0.629628 | 0.728111 | 0.197742 | 4.2103 | 3.2428 | 4.29347 | 3.28952 | 0.666343 | 0.019075 | 0.020524 | 0.629628 | -0.075796 | 0.654464 | 0.75 | -0.009475 | 0.770207 |  | full_dislocation_mode | marginal_utility_allocator | 0.629628 | 0 | 0.779204 |
| sizing_template_aggressive | marginal_utility_allocator | 237 | 237 | 237 | 1 |  | 0.015545 | 0.011364 | 0.509392 | 0.536991 | 1 | 0.164424 | 3.68411 | 2.69337 | 3.74885 | 2.72614 | 0.553431 | 0.011364 | 0.012412 | 0.536991 | -0.168661 | 0.515485 | 0.75 | -0.012974 | 0.731075 |  | confirmation_sensitive_mode | marginal_utility_allocator | 0.536991 | 0.482877 | 0.782105 |
| sizing_template_aggressive | marginal_utility_allocator | 237 | 237 | 237 | 1 |  | 0.016285 | 0.011813 | 0.498513 | 0.58285 | 1 | 0.165237 | 3.85944 | 2.79969 | 3.93035 | 2.83488 | 0.575264 | 0.011813 | 0.012902 | 0.58285 | -0.179001 | 0.538573 | 0.75 | -0.013769 | 0.725414 |  | reduced_dislocation_mode | marginal_utility_allocator | 0.58285 | 0.482877 | 0.782105 |
| sizing_template_aggressive | marginal_utility_allocator | 237 | 237 | 237 | 1 |  | 0.017022 | 0.012512 | 0.530946 | 0.556832 | 1 | 0.155075 | 4.03412 | 2.96537 | 4.11204 | 3.0054 | 0.609462 | 0.012512 | 0.013665 | 0.556832 | -0.220181 | 0.560144 | 0.75 | -0.016937 | 0.735072 |  | portfolio_utility_mode | marginal_utility_allocator | 0.556832 | 0.482877 | 0.782105 |
| sizing_template_aggressive | marginal_utility_allocator | 217 | 217 | 217 | 1 |  | 0.173545 | 0.136149 | 0.563039 | 3.13041 | 1 | 0.193287 | 37.6593 | 29.5443 | 45.1488 | 33.8546 | 6.16582 | 0.136149 | 0.136149 | 3.13041 | -1.28962 | 5.30283 | 0.75 | -0.107468 | 0.784516 |  | current_baseline_sleeve | baseline_rank_allocator | 3.13041 | 0.490485 | 0.778672 |

## Semis Budget Comparison
| framework_name | trade_count | semis_trade_share | anchored_semis_trade_share | avg_semis_budget_used | blocked_by_semis_budget_count |
| --- | --- | --- | --- | --- | --- |
| reduced_dislocation_mode | 237 | 0.35865 | 0.307692 | 0.000141 | 0 |
| confirmation_sensitive_mode | 237 | 0.35865 | 0.307692 | 0.000127 | 0 |
| portfolio_utility_mode | 237 | 0.35865 | 0.307692 | 0.000127 | 0 |

## Staged Execution Playbook
| framework_name | participation_stage | trade_count | avg_probe_weight | avg_add_weight | expectancy | semis_share |
| --- | --- | --- | --- | --- | --- | --- |
| current_baseline_sleeve | full_participation | 217 | 1 | 0 | 0.652269 | 0.373272 |
| reduced_dislocation_mode | probe_only | 237 | 0.353586 | 0 | 0.64636 | 0.35865 |
| confirmation_sensitive_mode | probe_only | 237 | 0.32616 | 0 | 0.64636 | 0.35865 |
| portfolio_utility_mode | probe_only | 237 | 0.337342 | 0 | 0.64636 | 0.35865 |

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