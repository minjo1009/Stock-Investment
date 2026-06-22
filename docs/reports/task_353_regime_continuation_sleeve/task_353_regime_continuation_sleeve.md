# Task 353 - Regime-Dependent Continuation Sleeve Monetization

- decision: REGIME_STACKABLE_ALPHA
- best_structure: single_best_binary
- best_cost_adjusted_expectancy: 0.970209
- best_rolling_oos_robustness: 1.0

## Final Interpretation
1. The next question is not whether continuation alpha exists, but whether top-ranked regimes can be monetized as an offensive sleeve.
2. Best monetization structure: `single_best_binary`
3. Final decision: `REGIME_STACKABLE_ALPHA`
4. Shadow-monitor ready: `True`

## Selected Regime Candidates
| selection_bucket | regime_id | candidate_type | trade_count | cost_adjusted_expectancy | rolling_robustness | structural_share | artifact_dependence | continuation_quality_score | artifact_adjusted_weight |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| top5_overall | market_breadth_state=broad|broad_participation_state=narrow_participation | interaction | 552 | 0.764634 | 1 | 0.18757 | 0.81243 | 0.742647 | 0.139298 |
| top5_overall | volatility_state=low_vol|liquidity_state=liquidity_contracting | interaction | 480 | 0.704124 | 0.75 | 0.227167 | 0.772833 | 0.736765 | 0.167369 |
| top5_overall | liquidity_state=liquidity_contracting | single_axis | 970 | 0.515474 | 0.75 | 0.309892 | 0.690108 | 0.720588 | 0.223304 |
| top5_overall | market_breadth_state=broad | single_axis | 737 | 0.715468 | 1 | 0.199035 | 0.800965 | 0.714706 | 0.142252 |
| top5_overall | session_timing_bucket=first_30m|execution_quality_bucket=strong | interaction | 83 | 0.689567 | 0.5 | 0.348735 | 0.651265 | 0.702206 | 0.244884 |
| top3_single_axis | session_timing_bucket=first_30m | single_axis | 92 | 0.573321 | 0.5 | 0.348735 | 0.651265 | 0.696324 | 0.242833 |

## Basket Comparison
| structure_name | structure_group | trade_count | annual_trade_frequency | expectancy | sharpe_proxy | mdd_pct | return_contribution | cost_adjusted_expectancy | cost_2x_expectancy | turnover_proxy | capital_utilization | concentration | rolling_oos_robustness | anchored_oos_expectancy | anchored_oos_cost_adjusted_expectancy | monetization_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single_best_binary | basket | 3148 | 648.875 | 1.12021 | 0.434938 | 81.4476 | 3526.42 | 0.970209 | 0.820209 | 10.8927 | 0.380623 | 0.168808 | 1 | 1.12596 | 0.975958 | 0.8918 |
| top_regime_basket_binary | basket | 9005 | 1853 | 0.797699 | 0.50585 | 98.5251 | 7183.28 | 0.647699 | 0.497699 | 31.1592 | 0.750865 | 0.139935 | 0.75 | 0.808185 | 0.658185 | 0.792305 |
| score_ranked_top3 | basket | 632 | 130.05 | 0.640037 | 0.942585 | 29.8129 | 404.503 | 0.490037 | 0.340037 | 2.18685 | 0.750865 | 0.151719 | 0.75 | 0.705426 | 0.555426 | 0.763085 |
| regime_conditioned_overlay_balanced | basket | 9005 | 1853 | 1.02446 | 0.382066 | 98.4856 | 9225.22 | 0.846813 | 0.66917 | 31.1592 | 0.750865 | 0.145267 | 0.75 | 1.04853 | 0.867996 | 0.818491 |

## Sizing Template Comparison
| structure_name | structure_group | trade_count | annual_trade_frequency | expectancy | sharpe_proxy | mdd_pct | return_contribution | cost_adjusted_expectancy | cost_2x_expectancy | turnover_proxy | capital_utilization | concentration | rolling_oos_robustness | anchored_oos_expectancy | anchored_oos_cost_adjusted_expectancy | monetization_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sizing_template_aggressive | sizing | 9005 | 1853 | 1.33726 | 0.406168 | 99.5167 | 12042 | 1.10829 | 0.87933 | 31.1592 | 0.750865 | 0.148699 | 0.75 | 1.37075 | 1.13745 | 0.84158 |
| sizing_template_balanced | sizing | 9005 | 1853 | 1.02446 | 0.480057 | 98.4018 | 9225.22 | 0.846813 | 0.66917 | 31.1592 | 0.750865 | 0.145267 | 0.75 | 1.04853 | 0.867996 | 0.818491 |
| sizing_template_persistence_adjusted | sizing | 9005 | 1853 | 0.597307 | 0.394254 | 95.8671 | 5378.75 | 0.494548 | 0.391789 | 31.1592 | 0.750865 | 0.193857 | 0.75 | 0.61363 | 0.51175 | 0.760969 |

## Artifact-Adjusted Sleeve
| structure_name | structure_group | trade_count | annual_trade_frequency | expectancy | sharpe_proxy | mdd_pct | return_contribution | cost_adjusted_expectancy | cost_2x_expectancy | turnover_proxy | capital_utilization | concentration | rolling_oos_robustness | anchored_oos_expectancy | anchored_oos_cost_adjusted_expectancy | monetization_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| artifact_half_plus | artifact_adjusted | 4410 | 907.978 | 0.824283 | 0.567449 | 95.0784 | 3635.09 | 0.674283 | 0.524283 | 15.2595 | 0.387543 | 0.237396 | 0.75 | 0.802567 | 0.652567 | 0.796289 |
| raw_top_basket | artifact_adjusted | 9005 | 1853 | 0.797699 | 0.50585 | 98.5251 | 7183.28 | 0.647699 | 0.497699 | 31.1592 | 0.750865 | 0.139935 | 0.75 | 0.808185 | 0.658185 | 0.792305 |
| artifact_core | artifact_adjusted | 1752 | 390.67 | 1.16069 | 0.410791 | 63.2476 | 2033.54 | 1.01069 | 0.860694 | 6.06228 | 0.17301 | 0.294687 | 0.5 | 1.3756 | 1.2256 | 0.739354 |

## Economic Utility
| best_structure | trade_count | annual_trade_frequency | capital_utilization | usable_capital_bucket | concentration_risk | execution_fragility | expected_live_slippage | shadow_monitor_suitability | likely_live_decay_risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single_best_binary | 3148 | 648.875 | 0.380623 | moderate | low | low | contained | True | moderate |

## OOS Validation
| structure_name | structure_group | trade_count | annual_trade_frequency | expectancy | sharpe_proxy | mdd_pct | return_contribution | cost_adjusted_expectancy | cost_2x_expectancy | turnover_proxy | capital_utilization | concentration | rolling_oos_robustness | anchored_oos_expectancy | anchored_oos_cost_adjusted_expectancy | monetization_score | scope | window_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| single_best_binary | oos_validation | 3148 | 648.875 | 1.12021 | 0.434938 | 81.4476 | 3526.42 | 0.970209 | 0.820209 | 10.8927 | 0.380623 | 0.168808 | 1 | 1.12596 | 0.975958 | 0.8918 | full_period |  |
| single_best_binary | oos_validation | 2434 | 750.227 | 1.12596 | 0.56006 | 81.4476 | 2740.58 | 0.975958 | 0.825958 | 8.42215 | 0.287197 | 0.221641 | 1 | 1.12596 | 0.975958 | 0.892289 | anchored_oos |  |
| single_best_binary | oos_validation | 619 | 672.886 | 1.36485 | 1.64638 | 31.4676 | 844.844 | 1.21485 | 1.06485 | 2.14187 | 0.100346 | 0.25571 | 1 | 1.36485 | 1.21485 | 0.849443 | rolling_window | window_1 |
| single_best_binary | oos_validation | 1167 | 1264.83 | 1.15322 | 1.39846 | 82.2582 | 1345.81 | 1.00322 | 0.853223 | 4.03806 | 0.103806 | 0.354879 | 1 | 1.15322 | 1.00322 | 0.83607 | rolling_window | window_2 |
| single_best_binary | oos_validation | 522 | 685.829 | 0.966226 | 2.11336 | 53.4311 | 504.37 | 0.816226 | 0.666226 | 1.80623 | 0.072664 | 0.25689 | 1 | 0.966226 | 0.816226 | 0.80589 | rolling_window | window_3 |
| single_best_binary | oos_validation | 126 | 23010.8 | 0.361552 | -7.93725 | 44.5618 | 45.5556 | 0.211552 | 0.061552 | 0.435986 | 0.010381 | 0.634105 | 1 | 0.361552 | 0.211552 | 0.632815 | rolling_window | window_4 |