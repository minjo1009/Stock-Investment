# Task 340: Strong Subset Validation

- Final decision: `REJECT_SUBSET`.
- Decision reason: subset fails one or more core robustness checks across time, concentration, cost, or significance

## Rolling OOS Validation

| window_id | train_start | train_end | oos_start | oos_end | oos_trade_count | subset_trade_count | subset_trade_ratio | oos_expectancy | oos_lift | win_rate | expectancy_delta | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| window_1 | 2021-06-01 | 2022-12-31 | 2023-01-01 | 2023-12-31 | 76 | 10 | 0.131579 | 0.686548 | -0.081579 | 1 | -0.480149 | ok |
| window_2 | 2021-06-01 | 2023-12-31 | 2024-01-01 | 2024-12-31 | 62 | 18 | 0.290323 | 0.077845 | -0.016129 | 0.555556 | -0.239986 | ok |
| window_3 | 2021-06-01 | 2024-12-31 | 2025-01-01 | 2025-12-31 | 75 | 17 | 0.226667 | 1.74672 | 0.061961 | 0.705882 | 0.781224 | ok |
| window_4 | 2021-06-01 | 2025-10-31 | 2025-11-01 | 2026-04-30 | 50 | 33 | 0.66 | 0.260148 | 0.051515 | 0.545455 | 0.377037 | ok |

## Symbol/Sector Breakdown

| scope | dimension_type | dimension_value | baseline_trade_count | subset_trade_count | subset_expectancy | expectancy_delta | return_proxy | symbol_contribution_share | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anchored_oos | symbol | AAPL | 2 | 0 |  |  | 0 | 0 | insufficient_sample |
| anchored_oos | symbol | AVGO | 20 | 17 | -0.284164 | 0.107742 | -4.8308 | 0.590524 | ok |
| anchored_oos | symbol | META | 14 | 14 | 0.798981 | 0 | 11.1857 | 0.341413 | ok |
| anchored_oos | symbol | NFLX | 2 | 2 | 1.11496 | 0 | 2.22993 | 0.068062 | ok |
| anchored_oos | symbol | QCOM | 12 | 0 |  |  | 0 | 0 | insufficient_sample |
| anchored_oos | sector_group | others | 2 | 0 |  |  | 0 | 0 | insufficient_sample |
| anchored_oos | sector_group | semis | 32 | 17 | -0.284164 | 0.294332 | -4.8308 | 0.590524 | ok |
| anchored_oos | sector_group | software_internet | 16 | 16 | 0.838479 | 0 | 13.4157 | 0.409476 | ok |
| anchored_oos | size_proxy_bucket | large_proxy | 36 | 31 | 0.204998 | 0.132794 | 6.35494 | 0.931938 | ok |
| anchored_oos | size_proxy_bucket | mid_proxy | 2 | 2 | 1.11496 | 0 | 2.22993 | 0.068062 | ok |
| anchored_oos | size_proxy_bucket | small_proxy | 12 | 0 |  |  | 0 | 0 | insufficient_sample |
| anchored_oos | scenario_family | PIVOT_HIGH | 14 | 8 | 1.06311 | 0.787169 | 8.50488 | 0.388812 | ok |
| anchored_oos | scenario_family | RANGE_COMPRESSION | 36 | 25 | 0.003199 | 0.272856 | 0.079987 | 0.611188 | ok |
| anchored_oos | breakout_subtype | PIVOT_HIGH|HIGH_TOUCH | 14 | 8 | 1.06311 | 0.787169 | 8.50488 | 0.388812 | ok |
| anchored_oos | breakout_subtype | RANGE_COMPRESSION|HIGH_TOUCH | 36 | 25 | 0.003199 | 0.272856 | 0.079987 | 0.611188 | ok |
| full_period | symbol | AAPL | 44 | 0 |  |  | 0 | 0 | insufficient_sample |
| full_period | symbol | AMD | 51 | 8 | -0.827361 | -1.08554 | -6.61889 | 0.050172 | ok |
| full_period | symbol | AMZN | 19 | 2 | 1.4991 | 1.5638 | 2.99819 | 0.022109 | ok |
| full_period | symbol | AVGO | 27 | 17 | -0.284164 | -1.05787 | -4.8308 | 0.142671 | ok |
| full_period | symbol | COST | 49 | 14 | 0.682768 | 0.06468 | 9.55875 | 0.145283 | ok |
| full_period | symbol | GOOGL | 46 | 15 | 2.26655 | 1.07193 | 33.9982 | 0.250709 | ok |
| full_period | symbol | META | 41 | 19 | 0.660857 | 0.194701 | 12.5563 | 0.092592 | ok |
| full_period | symbol | MSFT | 41 | 0 |  |  | 0 | 0 | insufficient_sample |
| full_period | symbol | NFLX | 2 | 2 | 1.11496 | 0 | 2.22993 | 0.016444 | ok |
| full_period | symbol | NVDA | 8 | 8 | 1.25463 | 0 | 10.037 | 0.074015 | ok |
| full_period | symbol | QCOM | 56 | 29 | -0.80306 | -0.0612 | -23.2888 | 0.191161 | ok |
| full_period | symbol | TSLA | 6 | 2 | -1.00649 | -0.335934 | -2.01297 | 0.014844 | ok |
| full_period | sector_group | others | 99 | 16 | 0.471611 | -0.040636 | 7.54578 | 0.160127 | ok |
| full_period | sector_group | semis | 142 | 62 | -0.39841 | -0.416367 | -24.7014 | 0.458019 | ok |
| full_period | sector_group | software_internet | 149 | 38 | 1.3627 | 0.422069 | 51.7826 | 0.381854 | ok |

## Execution Stress Test

| scope | scenario | slippage_rate | fee_rate | expectancy_after_cost | return_proxy_after_cost | win_rate_after_cost | trade_count | edge_survives_cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anchored_oos | Scenario 0 (baseline) | 0 | 0 | 0.260148 | 8.58487 | 0.545455 | 33 | True |
| anchored_oos | Scenario 1 (0.05%) | 0.0005 | 0.0005 | 0.160148 | 5.28487 | 0.545455 | 33 | True |
| anchored_oos | Scenario 2 (0.10%) | 0.001 | 0.0005 | 0.110148 | 3.63487 | 0.484848 | 33 | True |
| anchored_oos | Scenario 3 (0.20%) | 0.002 | 0.001 | -0.039852 | -1.31513 | 0.363636 | 33 | False |
| full_period | Scenario 0 (baseline) | 0 | 0 | 0.298509 | 34.627 | 0.517241 | 116 | True |
| full_period | Scenario 1 (0.05%) | 0.0005 | 0.0005 | 0.198509 | 23.027 | 0.5 | 116 | True |
| full_period | Scenario 2 (0.10%) | 0.001 | 0.0005 | 0.148509 | 17.227 | 0.482759 | 116 | True |
| full_period | Scenario 3 (0.20%) | 0.002 | 0.001 | -0.001491 | -0.172999 | 0.413793 | 116 | False |

## Subset Strategy Performance

| scope | subset_trade_count | trade_frequency_per_year | expectancy | total_return_proxy | cagr_proxy | sharpe_proxy | max_drawdown_proxy | win_rate | status | baseline_trade_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anchored_oos | 33 | 89.2833 | 0.260148 | 8.66059 | 25.1973 | 1.00111 | 9.81896 | 0.545455 | ok | 50 |
| full_period | 116 | 26.1215 | 0.298509 | 39.5152 | 7.78705 | 0.277983 | 24.798 | 0.517241 | ok | 390 |

## Statistical Significance

| test_name | observed_stat | null_mean | null_std | p_value | percentile_rank | status |
| --- | --- | --- | --- | --- | --- | --- |
| permutation_test | 0.377037 | -0.016853 | 0.358355 | 0.151 | 84.9 | ok |
| random_subset_comparison | 0.377037 | -0.016402 | 0.369697 | 0.141 | 85.9 | ok |
| distribution_mean | 0.260148 |  |  |  |  | ok |
| distribution_median | 0.108247 |  |  |  |  | ok |
| distribution_skewness | 1.10761 |  |  |  |  | ok |
| distribution_top3_abs_share | 0.292787 |  |  |  |  | ok |
| distribution_negative_tail_share | 0.454545 |  |  |  |  | ok |

## Final Answer

- The strongest subset is validated as a fixed rule: `entry_only + high_atr + vol_expanding`.
- Rolling validation uses train-refit thresholds only and does not change the subset definition.
- Engine integration is feasible only if pre-entry daily features remain available at decision time with no lookahead.