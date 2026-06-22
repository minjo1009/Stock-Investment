# Task 354 - Regime Sleeve Deployment Realism

- decision: RESEARCH_ONLY
- best_structure: sizing_template_aggressive
- best_allocator: structural_balance_allocator
- best_allocator_timing: post_confirmation_allocator
- best_net_pnl_r: 29.544324

## Final Interpretation
1. This task evaluates deployment realism, not new alpha discovery.
2. Best allocator structure: `sizing_template_aggressive / structural_balance_allocator`
3. Final decision: `RESEARCH_ONLY`
4. Tiny-capital pilot ready: `False`

## Allocator Comparison
| structure_name | allocator_name | trade_count | signals_seen | signals_selected | selection_rate | avg_rank_of_selected_signal | expectancy | cost_adjusted_expectancy | sharpe_proxy | mdd_pct | capital_utilization | concentration | gross_pnl_r | net_pnl_r | gross_return_pct | net_return_pct | annualized_pnl_proxy | pnl_per_trade | pnl_per_active_day | max_peak_to_trough_pnl_drawdown | anchored_oos_net_pnl_r | rolling_window_net_pnl_r | rolling_oos_robustness | anchored_oos_cost_adjusted_expectancy | pnl_retention_ratio | pnl_lost_due_to_competition | allocator_timing | capital_bucket | capital_fraction | max_positions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sizing_template_aggressive | structural_balance_allocator | 217 | 1391 | 217 | 0.156003 | 1 | 0.173545 | 0.136149 | 0.563039 | 3.13041 | 0.750865 | 0.193287 | 37.6593 | 29.5443 | 45.1488 | 33.8546 | 6.16582 | 0.136149 | 0.136149 | 3.13041 | -1.28962 | 5.30283 | 0.75 | -0.107468 | 0.784516 | 0 | post_confirmation_allocator | bucket_20pct | 0.2 | 1 |
| sizing_template_aggressive | regime_priority_allocator | 217 | 1391 | 217 | 0.156003 | 1 | 0.173305 | 0.135805 | 0.558545 | 3.13041 | 0.750865 | 0.193167 | 37.6072 | 29.4697 | 45.0731 | 33.7546 | 6.14954 | 0.135805 | 0.135805 | 3.13041 | -1.28962 | 5.28417 | 0.75 | -0.107468 | 0.783618 | 0 | post_confirmation_allocator | bucket_20pct | 0.2 | 1 |
| sizing_template_aggressive | convexity_weighted_allocator | 217 | 1391 | 217 | 0.156003 | 1 | 0.173305 | 0.135805 | 0.558545 | 3.13041 | 0.750865 | 0.193167 | 37.6072 | 29.4697 | 45.0731 | 33.7546 | 6.14954 | 0.135805 | 0.135805 | 3.13041 | -1.28962 | 5.28417 | 0.75 | -0.107468 | 0.783618 | 0 | post_confirmation_allocator | bucket_20pct | 0.2 | 1 |
| sizing_template_aggressive | regime_priority_allocator | 217 | 1391 | 217 | 0.156003 | 1 | 0.167567 | 0.130793 | 0.541153 | 3.1484 | 0.750865 | 0.193129 | 36.362 | 28.382 | 43.2902 | 32.3178 | 5.91455 | 0.130793 | 0.130793 | 3.1484 | -1.14702 | 5.06676 | 0.75 | -0.095585 | 0.78054 | 0 | opening_drive_allocator | bucket_20pct | 0.2 | 1 |
| sizing_template_aggressive | convexity_weighted_allocator | 217 | 1391 | 217 | 0.156003 | 1 | 0.167567 | 0.130793 | 0.541153 | 3.1484 | 0.750865 | 0.193129 | 36.362 | 28.382 | 43.2902 | 32.3178 | 5.91455 | 0.130793 | 0.130793 | 3.1484 | -1.14702 | 5.06676 | 0.75 | -0.095585 | 0.78054 | 0 | opening_drive_allocator | bucket_20pct | 0.2 | 1 |
| sizing_template_aggressive | capital_efficiency_allocator | 217 | 1391 | 217 | 0.156003 | 1 | 0.167595 | 0.130095 | 0.55897 | 3.4438 | 0.750865 | 0.193103 | 36.3681 | 28.2306 | 43.2958 | 32.1154 | 5.88129 | 0.130095 | 0.130095 | 3.4438 | -1.28962 | 5.31691 | 0.75 | -0.107468 | 0.776246 | 0 | post_confirmation_allocator | bucket_20pct | 0.2 | 1 |
| sizing_template_aggressive | structural_balance_allocator | 217 | 1391 | 217 | 0.156003 | 1 | 0.166725 | 0.129951 | 0.537476 | 3.25733 | 0.750865 | 0.193556 | 36.1794 | 28.1994 | 43.0291 | 32.0766 | 5.87491 | 0.129951 | 0.129951 | 3.25733 | -1.14702 | 5.06676 | 0.75 | -0.095585 | 0.779432 | 0 | opening_drive_allocator | bucket_20pct | 0.2 | 1 |
| sizing_template_aggressive | capital_efficiency_allocator | 217 | 1391 | 217 | 0.156003 | 1 | 0.161857 | 0.125082 | 0.540777 | 3.58436 | 0.750865 | 0.193064 | 35.1229 | 27.1429 | 41.5348 | 30.6961 | 5.64689 | 0.125082 | 0.125082 | 3.58436 | -1.14702 | 5.0995 | 0.75 | -0.095585 | 0.772798 | 0 | opening_drive_allocator | bucket_20pct | 0.2 | 1 |
| sizing_template_aggressive | structural_balance_allocator | 581 | 1391 | 581 | 0.417685 | 1.89501 | 0.05769 | 0.045306 | 0.560833 | 2.81077 | 0.750865 | 0.179931 | 33.5179 | 26.3229 | 39.6659 | 29.9756 | 5.52712 | 0.045306 | 0.121304 | 2.81077 | -1.31224 | 4.45907 | 0.75 | -0.038595 | 0.785338 | 0 | post_confirmation_allocator | bucket_20pct | 0.2 | 3 |
| sizing_template_aggressive | regime_priority_allocator | 581 | 1391 | 581 | 0.417685 | 1.89501 | 0.057658 | 0.045261 | 0.558865 | 2.81077 | 0.750865 | 0.179885 | 33.4993 | 26.2968 | 39.64 | 29.9418 | 5.52148 | 0.045261 | 0.121184 | 2.81077 | -1.31224 | 4.45256 | 0.75 | -0.038595 | 0.784996 | 0 | post_confirmation_allocator | bucket_20pct | 0.2 | 3 |
| sizing_template_aggressive | convexity_weighted_allocator | 581 | 1391 | 581 | 0.417685 | 1.89501 | 0.057658 | 0.045261 | 0.558865 | 2.81077 | 0.750865 | 0.179885 | 33.4993 | 26.2968 | 39.64 | 29.9418 | 5.52148 | 0.045261 | 0.121184 | 2.81077 | -1.31224 | 4.45256 | 0.75 | -0.038595 | 0.784996 | 0 | post_confirmation_allocator | bucket_20pct | 0.2 | 3 |
| sizing_template_aggressive | regime_priority_allocator | 581 | 1391 | 581 | 0.417685 | 1.89501 | 0.055965 | 0.043814 | 0.543762 | 2.79685 | 0.750865 | 0.179921 | 32.5157 | 25.4557 | 38.2764 | 28.856 | 5.33995 | 0.043814 | 0.117307 | 2.79685 | -1.18934 | 4.30018 | 0.75 | -0.034981 | 0.782874 | 0 | opening_drive_allocator | bucket_20pct | 0.2 | 3 |

## Concurrent Signal Competition
| structure_name | allocator_name | allocator_timing | capital_bucket | capital_fraction | max_positions | signals_seen | signals_selected | selection_rate | avg_rank_of_selected_signal | gross_pnl_r | net_pnl_r | pnl_lost_due_to_competition | rolling_oos_robustness | anchored_oos_net_pnl_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sizing_template_aggressive | structural_balance_allocator | post_confirmation_allocator | bucket_20pct | 0.2 | 1 | 1391 | 217 | 0.156003 | 1 | 37.6593 | 29.5443 | 0 | 0.75 | -1.28962 |
| sizing_template_aggressive | regime_priority_allocator | post_confirmation_allocator | bucket_20pct | 0.2 | 1 | 1391 | 217 | 0.156003 | 1 | 37.6072 | 29.4697 | 0 | 0.75 | -1.28962 |
| sizing_template_aggressive | convexity_weighted_allocator | post_confirmation_allocator | bucket_20pct | 0.2 | 1 | 1391 | 217 | 0.156003 | 1 | 37.6072 | 29.4697 | 0 | 0.75 | -1.28962 |
| sizing_template_aggressive | regime_priority_allocator | opening_drive_allocator | bucket_20pct | 0.2 | 1 | 1391 | 217 | 0.156003 | 1 | 36.362 | 28.382 | 0 | 0.75 | -1.14702 |
| sizing_template_aggressive | convexity_weighted_allocator | opening_drive_allocator | bucket_20pct | 0.2 | 1 | 1391 | 217 | 0.156003 | 1 | 36.362 | 28.382 | 0 | 0.75 | -1.14702 |
| sizing_template_aggressive | capital_efficiency_allocator | post_confirmation_allocator | bucket_20pct | 0.2 | 1 | 1391 | 217 | 0.156003 | 1 | 36.3681 | 28.2306 | 0 | 0.75 | -1.28962 |
| sizing_template_aggressive | structural_balance_allocator | opening_drive_allocator | bucket_20pct | 0.2 | 1 | 1391 | 217 | 0.156003 | 1 | 36.1794 | 28.1994 | 0 | 0.75 | -1.14702 |
| sizing_template_aggressive | capital_efficiency_allocator | opening_drive_allocator | bucket_20pct | 0.2 | 1 | 1391 | 217 | 0.156003 | 1 | 35.1229 | 27.1429 | 0 | 0.75 | -1.14702 |
| sizing_template_aggressive | structural_balance_allocator | post_confirmation_allocator | bucket_20pct | 0.2 | 3 | 1391 | 581 | 0.417685 | 1.89501 | 33.5179 | 26.3229 | 0 | 0.75 | -1.31224 |
| sizing_template_aggressive | regime_priority_allocator | post_confirmation_allocator | bucket_20pct | 0.2 | 3 | 1391 | 581 | 0.417685 | 1.89501 | 33.4993 | 26.2968 | 0 | 0.75 | -1.31224 |
| sizing_template_aggressive | convexity_weighted_allocator | post_confirmation_allocator | bucket_20pct | 0.2 | 3 | 1391 | 581 | 0.417685 | 1.89501 | 33.4993 | 26.2968 | 0 | 0.75 | -1.31224 |
| sizing_template_aggressive | regime_priority_allocator | opening_drive_allocator | bucket_20pct | 0.2 | 3 | 1391 | 581 | 0.417685 | 1.89501 | 32.5157 | 25.4557 | 0 | 0.75 | -1.18934 |

## Execution Realism Stress
| structure_name | allocator_name | trade_count | signals_seen | signals_selected | selection_rate | avg_rank_of_selected_signal | expectancy | cost_adjusted_expectancy | sharpe_proxy | mdd_pct | capital_utilization | concentration | gross_pnl_r | net_pnl_r | gross_return_pct | net_return_pct | annualized_pnl_proxy | pnl_per_trade | pnl_per_active_day | max_peak_to_trough_pnl_drawdown | anchored_oos_net_pnl_r | rolling_window_net_pnl_r | rolling_oos_robustness | anchored_oos_cost_adjusted_expectancy | pnl_retention_ratio | pnl_lost_due_to_competition | stress_scenario | raw_net_pnl_r | stress_group | slippage_adjusted_expectancy | expected_live_slippage | execution_fragility | stress_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sizing_template_aggressive | best_config | 217 | 217 | 217 | 1 |  | 0.173545 | 0.136149 | 0.563039 | 3.13041 | 0.750865 | 0.193287 | 37.6593 | 29.5443 | 45.1488 | 33.8546 | 6.16582 | 0.136149 | 0.136149 | 3.13041 | -1.28962 | 5.30283 | 0.75 | -0.107468 | 0.784516 |  | baseline | 29.5443 | execution_realism | 0.136149 | elevated | low | True |
| sizing_template_aggressive | best_config | 217 | 217 | 217 | 1 |  | 0.169743 | 0.094951 | 0.405627 | 4.19957 | 0.750865 | 0.192558 | 36.8343 | 20.6043 | 43.9625 | 22.425 | 4.23911 | 0.094951 | 0.094951 | 4.19957 | -1.78712 | 3.6072 | 0.75 | -0.148926 | 0.559378 |  | combined_stress | 29.5443 | execution_realism | 0.094951 | elevated | medium | True |
| sizing_template_aggressive | best_config | 217 | 217 | 217 | 1 |  | 0.171402 | 0.134006 | 0.555435 | 3.18855 | 0.750865 | 0.192741 | 37.1943 | 29.0793 | 44.4794 | 33.237 | 6.06513 | 0.134006 | 0.134006 | 3.18855 | -1.37212 | 5.18283 | 0.75 | -0.114343 | 0.781822 |  | confirmation_delay_penalty | 29.5443 | execution_realism | 0.134006 | elevated | low | True |
| sizing_template_aggressive | best_config | 217 | 217 | 217 | 1 |  | 0.173545 | 0.098753 | 0.421043 | 4.09399 | 0.750865 | 0.193287 | 37.6593 | 21.4293 | 45.1488 | 23.4348 | 4.41494 | 0.098753 | 0.098753 | 4.09399 | -1.64962 | 3.8197 | 0.75 | -0.137468 | 0.569031 |  | higher_slippage | 29.5443 | execution_realism | 0.098753 | elevated | medium | True |
| sizing_template_aggressive | best_config | 217 | 217 | 217 | 1 |  | 0.171886 | 0.13449 | 0.557036 | 3.17886 | 0.750865 | 0.192661 | 37.2993 | 29.1843 | 44.6296 | 33.3756 | 6.08776 | 0.13449 | 0.13449 | 3.17886 | -1.34462 | 5.21033 | 0.75 | -0.112051 | 0.782436 |  | opening_penalty | 29.5443 | execution_realism | 0.13449 | elevated | low | True |

## Overlap Netting
| netting_mode | trade_count | raw_net_pnl_r | netted_net_pnl_r | net_pnl_delta | drawdown_delta | concentration_delta | pnl_retention_ratio | rolling_oos_robustness | anchored_oos_net_pnl_r |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| allow_duplicate_exposure | 217 | 29.5443 | 29.5443 | 0 | 0 | 0 | 1 | 0.75 | -1.28962 |
| sector_cap_netting | 217 | 29.5443 | 29.5443 | 0 | 0 | 0 | 1 | 0.75 | -1.28962 |
| symbol_netting | 217 | 29.5443 | 29.5443 | 0 | 0 | 0 | 1 | 0.75 | -1.28962 |

## Shadow / Pilot Readiness
| gate_name | status | evidence_value | threshold |
| --- | --- | --- | --- |
| net_pnl_positive | True | 29.5443 | > 0 |
| anchored_oos_net_pnl_positive | False | -1.28962 | > 0 |
| rolling_pnl_persistence | True | 0.75 | >= 0.75 |
| combined_stress_retention | True | 0.559378 | >= 0.50 |
| symbol_netting_retention | True | 1 | >= 0.70 |
| shadow_monitor_ready | False |  | all core gates |
| tiny_capital_pilot_ready | False |  | all gates |

## Live Timing Reconstruction Sample
| event_id | trade_id | symbol | entry_ts | exit_ts | day_key | current_split | sector_group | session_timing_bucket | execution_quality_bucket | same_day_candidate_count | same_day_sector_candidate_count | realized_R | allocator_timing | feature_availability_group | regime_score_at_decision_time | artifact_score_at_decision_time | top_regime_score_at_decision_time | eligible_at_decision_time | delayed_signal_penalty_flag | regime_score_percentile_at_decision_time | artifact_score_percentile_at_decision_time | timing_tier | artifact_tier | single_best_binary | top_regime_basket_binary | regime_conditioned_overlay_balanced | sizing_template_aggressive | artifact_half_plus |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | META|2021-06-07|2021-06-07|333.779999 | META | 2021-06-07 00:00:00+00:00 | 2021-07-19 00:00:00+00:00 | 2021-06-07 | train | software_internet | mid_session | strong | 10 | 10 | 0.230647 | opening_drive_allocator | opening_window_available | 1.45735 | 0.390673 | 0 | True | False | 0.559669 | 0.648095 | active | active | False | True | True | True | True |
| 190 | META|2021-06-07|2021-06-07|333.779999 | META | 2021-06-07 00:00:00+00:00 | 2021-07-07 00:00:00+00:00 | 2021-06-07 | train | software_internet | mid_session | strong | 10 | 10 | 0.851322 | opening_drive_allocator | opening_window_available | 1.45735 | 0.390673 | 0 | True | False | 0.559669 | 0.648095 | active | active | False | True | True | True | True |
| 381 | META|2021-06-07|2021-06-07|333.779999 | META | 2021-06-07 00:00:00+00:00 | 2021-07-07 00:00:00+00:00 | 2021-06-07 | train | software_internet | mid_session | strong | 10 | 10 | 1.31177 | opening_drive_allocator | opening_window_available | 1.45735 | 0.390673 | 0 | True | False | 0.559669 | 0.648095 | active | active | False | True | True | True | True |
| 596 | META|2021-06-07|2021-06-07|333.779999 | META | 2021-06-07 00:00:00+00:00 | 2021-07-19 00:00:00+00:00 | 2021-06-07 | train | software_internet | mid_session | strong | 10 | 10 | 0.184517 | opening_drive_allocator | opening_window_available | 1.45735 | 0.390673 | 0 | True | False | 0.559669 | 0.648095 | active | active | False | True | True | True | True |
| 779 | META|2021-06-07|2021-06-07|333.779999 | META | 2021-06-07 00:00:00+00:00 | 2021-07-07 00:00:00+00:00 | 2021-06-07 | train | software_internet | mid_session | strong | 10 | 10 | 1.04942 | opening_drive_allocator | opening_window_available | 1.45735 | 0.390673 | 0 | True | False | 0.559669 | 0.648095 | active | active | False | True | True | True | True |
| 988 | META|2021-06-07|2021-06-07|333.779999 | META | 2021-06-07 00:00:00+00:00 | 2021-07-19 00:00:00+00:00 | 2021-06-07 | train | software_internet | mid_session | strong | 10 | 10 | 0.149686 | opening_drive_allocator | opening_window_available | 1.45735 | 0.390673 | 0 | True | False | 0.559669 | 0.648095 | active | active | False | True | True | True | True |
| 1157 | META|2021-06-07|2021-06-07|333.779999 | META | 2021-06-07 00:00:00+00:00 | 2021-07-07 00:00:00+00:00 | 2021-06-07 | train | software_internet | mid_session | strong | 10 | 10 | 1.04942 | opening_drive_allocator | opening_window_available | 1.45735 | 0.390673 | 0 | True | False | 0.559669 | 0.648095 | active | active | False | True | True | True | True |
| 1334 | META|2021-06-07|2021-06-07|333.779999 | META | 2021-06-07 00:00:00+00:00 | 2021-07-19 00:00:00+00:00 | 2021-06-07 | train | software_internet | mid_session | strong | 10 | 10 | 0.307529 | opening_drive_allocator | opening_window_available | 1.45735 | 0.390673 | 0 | True | False | 0.559669 | 0.648095 | active | active | False | True | True | True | True |
| 1532 | META|2021-06-07|2021-06-07|333.779999 | META | 2021-06-07 00:00:00+00:00 | 2021-07-19 00:00:00+00:00 | 2021-06-07 | train | software_internet | mid_session | strong | 10 | 10 | 0.230647 | opening_drive_allocator | opening_window_available | 1.45735 | 0.390673 | 0 | True | False | 0.559669 | 0.648095 | active | active | False | True | True | True | True |
| 1751 | META|2021-06-07|2021-06-07|333.779999 | META | 2021-06-07 00:00:00+00:00 | 2021-07-19 00:00:00+00:00 | 2021-06-07 | train | software_internet | mid_session | strong | 10 | 10 | 0.230647 | opening_drive_allocator | opening_window_available | 1.45735 | 0.390673 | 0 | True | False | 0.559669 | 0.648095 | active | active | False | True | True | True | True |
| 2 | META|2021-06-07|2021-06-07|333.779999 | META | 2021-06-07 00:00:00+00:00 | 2021-07-19 00:00:00+00:00 | 2021-06-07 | train | software_internet | mid_session | strong | 10 | 10 | 0.230647 | post_confirmation_allocator | post_breakout_confirmation | 1.45735 | 0.390673 | 0 | True | False | 0.540259 | 0.625809 | active | active | False | True | True | True | True |
| 190 | META|2021-06-07|2021-06-07|333.779999 | META | 2021-06-07 00:00:00+00:00 | 2021-07-07 00:00:00+00:00 | 2021-06-07 | train | software_internet | mid_session | strong | 10 | 10 | 0.851322 | post_confirmation_allocator | post_breakout_confirmation | 1.45735 | 0.390673 | 0 | True | False | 0.540259 | 0.625809 | active | active | False | True | True | True | True |