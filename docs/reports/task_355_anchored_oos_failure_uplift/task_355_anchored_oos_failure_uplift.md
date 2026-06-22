# Task 355 - Anchored OOS Failure Uplift

- decision: PARTIAL_UPLIFT_RESEARCH
- best_candidate: combo_earlier_timing_plus_max3
- best_anchored_oos_net_pnl_r: -1.189342

## Final Interpretation
1. This task localizes why Task 354 failed anchored OOS and tests only a small fixed set of deployment uplifts.
2. Best uplift candidate: `combo_earlier_timing_plus_max3`
3. Final decision: `PARTIAL_UPLIFT_RESEARCH`

## Anchored OOS Loss Decomposition
| dimension | bucket | trade_count | gross_pnl_r | loss_share | expectancy |
| --- | --- | --- | --- | --- | --- |
| execution_quality_bucket | strong | 6 | -3.96307 | 0.522253 | -0.660512 |
| month | 2026-01 | 5 | -2.71892 | 0.496796 | -0.543785 |
| quarter | 2026Q1 | 5 | -2.71892 | 0.496796 | -0.543785 |
| sector_group | semis | 4 | -3.98883 | 0.490485 | -0.997207 |
| session_timing_bucket | unknown | 6 | -0.569857 | 0.477747 | -0.094976 |
| execution_quality_bucket | unknown | 6 | -0.569857 | 0.477747 | -0.094976 |
| month | 2026-04 | 4 | -0.8843 | 0.353949 | -0.221075 |
| quarter | 2026Q2 | 4 | -0.8843 | 0.353949 | -0.221075 |
| same_day_candidate_count | 7 | 3 | -2.50782 | 0.333941 | -0.835939 |
| session_timing_bucket | first_30m | 4 | -2.16314 | 0.300925 | -0.540786 |
| sector_group | others | 5 | -0.75063 | 0.280333 | -0.150126 |
| symbol | AMD | 2 | -2.24021 | 0.275467 | -1.12011 |
| symbol | COST | 3 | -0.545384 | 0.229527 | -0.181795 |
| symbol | NFLX | 1 | -1.8638 | 0.229182 | -1.8638 |
| sector_group | software_internet | 3 | 0.206526 | 0.229182 | 0.068842 |

## Anchored OOS Cluster Diagnostics
| cluster_month | sector_group | session_timing_bucket | execution_quality_bucket | selection_status | trade_count | gross_pnl_r | expectancy | avg_rank_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2025-11 | software_internet | first_30m | strong | selected | 1 | 0.284099 | 0.284099 |  |
| 2025-11 | software_internet | first_30m | strong | missed | 3 | 0.836604 | 0.278868 |  |
| 2025-12 | semis | first_30m | strong | missed | 7 | -4.54972 | -0.64996 |  |
| 2025-12 | others | first_30m | strong | missed | 9 | -3.40881 | -0.378757 |  |
| 2025-12 | semis | mid_session | strong | missed | 2 | -1.99748 | -0.998739 |  |
| 2025-12 | semis | first_30m | strong | selected | 1 | -0.800631 | -0.800631 |  |
| 2025-12 | others | first_30m | strong | selected | 1 | -0.413176 | -0.413176 |  |
| 2026-01 | semis | unknown | unknown | missed | 8 | -7.78389 | -0.972986 |  |
| 2026-01 | semis | mid_session | strong | missed | 9 | -7.72828 | -0.858698 |  |
| 2026-01 | others | last_hour | strong | missed | 6 | -3.75954 | -0.626589 |  |
| 2026-01 | semis | first_30m | strong | missed | 1 | -1.23344 | -1.23344 |  |
| 2026-01 | semis | first_30m | strong | selected | 1 | -1.23344 | -1.23344 |  |
| 2026-01 | semis | unknown | unknown | selected | 1 | -1.00678 | -1.00678 |  |
| 2026-01 | semis | mid_session | strong | selected | 1 | -0.947983 | -0.947983 |  |
| 2026-01 | others | last_hour | strong | selected | 1 | -0.851948 | -0.851948 |  |

## Uplift Candidate Comparison
| structure_name | allocator_name | trade_count | signals_seen | signals_selected | selection_rate | avg_rank_of_selected_signal | expectancy | cost_adjusted_expectancy | sharpe_proxy | mdd_pct | capital_utilization | concentration | gross_pnl_r | net_pnl_r | gross_return_pct | net_return_pct | annualized_pnl_proxy | pnl_per_trade | pnl_per_active_day | max_peak_to_trough_pnl_drawdown | anchored_oos_net_pnl_r | rolling_window_net_pnl_r | rolling_oos_robustness | anchored_oos_cost_adjusted_expectancy | pnl_retention_ratio | pnl_lost_due_to_competition | candidate_name | uplift_type | combined_stress_retention | allocator_timing | max_positions | deployment_uplift_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sizing_template_aggressive | structural_balance_allocator | 581 | 581 | 581 | 1 |  | 0.055594 | 0.043443 | 0.540404 | 2.79685 | 0.750865 | 0.180308 | 32.3002 | 25.2402 | 37.9789 | 28.5788 | 5.2934 | 0.043443 | 0.116315 | 2.79685 | -1.18934 | 4.26694 | 0.75 | -0.034981 | 0.781426 |  | combo_earlier_timing_plus_max3 | two_factor | 0.488287 | opening_drive_allocator | 3 | 0.30016 |
| sizing_template_aggressive | structural_balance_allocator | 581 | 581 | 581 | 1 |  | 0.05769 | 0.045306 | 0.560833 | 2.81077 | 0.750865 | 0.179931 | 33.5179 | 26.3229 | 39.6659 | 29.9756 | 5.52712 | 0.045306 | 0.121304 | 2.81077 | -1.31224 | 4.45907 | 0.75 | -0.038595 | 0.785338 |  | uplift_less_concentrated_slotting | single_factor | 0.56104 | post_confirmation_allocator | 3 | 0.249033 |
| sizing_template_aggressive | convexity_weighted_allocator | 581 | 581 | 581 | 1 |  | 0.057658 | 0.045261 | 0.558865 | 2.81077 | 0.750865 | 0.179885 | 33.4993 | 26.2968 | 39.64 | 29.9418 | 5.52148 | 0.045261 | 0.121184 | 2.81077 | -1.31224 | 4.45256 | 0.75 | -0.038595 | 0.784996 |  | combo_convexity_plus_max3 | two_factor | 0.560446 | post_confirmation_allocator | 3 | 0.248974 |
| sizing_template_aggressive | structural_balance_allocator | 217 | 217 | 217 | 1 |  | 0.158568 | 0.124974 | 0.590385 | 2.63172 | 0.750865 | 0.181839 | 34.4093 | 27.1193 | 40.6484 | 30.7752 | 5.66 | 0.124974 | 0.124974 | 2.63172 | -1.08824 | 4.91123 | 0.75 | -0.090686 | 0.788139 |  | uplift_capped_aggression | single_factor | 0.567286 | post_confirmation_allocator | 1 | 0.211716 |
| sizing_template_aggressive | convexity_weighted_allocator | 217 | 217 | 217 | 1 |  | 0.167567 | 0.130793 | 0.541153 | 3.1484 | 0.750865 | 0.193129 | 36.362 | 28.382 | 43.2902 | 32.3178 | 5.91455 | 0.130793 | 0.130793 | 3.1484 | -1.14702 | 5.06676 | 0.75 | -0.095585 | 0.78054 |  | combo_earlier_timing_plus_convexity | two_factor | 0.485858 | opening_drive_allocator | 1 | 0.160061 |
| sizing_template_aggressive | structural_balance_allocator | 217 | 217 | 217 | 1 |  | 0.166725 | 0.129951 | 0.537476 | 3.25733 | 0.750865 | 0.193556 | 36.1794 | 28.1994 | 43.0291 | 32.0766 | 5.87491 | 0.129951 | 0.129951 | 3.25733 | -1.14702 | 5.06676 | 0.75 | -0.095585 | 0.779432 |  | uplift_earlier_timing | single_factor | 0.482816 | opening_drive_allocator | 1 | 0.158123 |
| sizing_template_aggressive | convexity_weighted_allocator | 217 | 217 | 217 | 1 |  | 0.173305 | 0.135805 | 0.558545 | 3.13041 | 0.750865 | 0.193167 | 37.6072 | 29.4697 | 45.0731 | 33.7546 | 6.14954 | 0.135805 | 0.135805 | 3.13041 | -1.28962 | 5.28417 | 0.75 | -0.107468 | 0.783618 |  | uplift_convexity_allocator | single_factor | 0.557831 | post_confirmation_allocator | 1 | 0.080783 |
| sizing_template_aggressive | structural_balance_allocator | 217 | 217 | 217 | 1 |  | 0.173545 | 0.136149 | 0.563039 | 3.13041 | 0.750865 | 0.193287 | 37.6593 | 29.5443 | 45.1488 | 33.8546 | 6.16582 | 0.136149 | 0.136149 | 3.13041 | -1.28962 | 5.30283 | 0.75 | -0.107468 | 0.784516 |  | baseline_task354_best | baseline | 0.559378 |  |  | 0 |
| sizing_template_aggressive | structural_balance_allocator | 581 | 581 | 581 | 1 |  | 0.158134 | 0.124674 | 0.634644 | 6.40892 | 0.750865 | 0.168611 | 91.8759 | 72.4359 | 148.774 | 104.887 | 15.8568 | 0.124674 | 0.333806 | 6.40892 | -3.32261 | 12.4751 | 0.75 | -0.097724 | 0.78841 |  | combo_capped_aggression_plus_max3 | two_factor | 0.567776 | post_confirmation_allocator | 3 | -0.756237 |

## Uplift Scorecard
| candidate_name | uplift_type | anchored_oos_net_pnl_improvement | anchored_oos_expectancy_improvement | drawdown_relief | rolling_robustness_preserved | stress_retention_preserved | deployment_uplift_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| combo_earlier_timing_plus_max3 | two_factor | 0.100275 | 0.072487 | 0.33356 | True | False | 0.30016 |
| uplift_less_concentrated_slotting | single_factor | -0.02262 | 0.068873 | 0.319641 | True | True | 0.249033 |
| combo_convexity_plus_max3 | two_factor | -0.02262 | 0.068873 | 0.319641 | True | True | 0.248974 |
| uplift_capped_aggression | single_factor | 0.20138 | 0.016782 | 0.49869 | True | True | 0.211716 |
| combo_earlier_timing_plus_convexity | two_factor | 0.142594 | 0.011883 | -0.017988 | True | False | 0.160061 |
| uplift_earlier_timing | single_factor | 0.142594 | 0.011883 | -0.126922 | True | False | 0.158123 |
| uplift_convexity_allocator | single_factor | 0 | 0 | 0 | True | True | 0.080783 |
| combo_capped_aggression_plus_max3 | two_factor | -2.03299 | 0.009744 | -3.27851 | True | True | -0.756237 |