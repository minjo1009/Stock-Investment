# Task 334: Behavior State Monetization

## Core Answer

- Final production candidate status: `NO_EDGE`.
- Best bad-state predictor: `core_feature_set::band_probability`.

## Cluster Truth Stability

| cluster_label | cluster_label_base | train_trade_count | oos_trade_count | train_cluster_share | oos_cluster_share | train_oos_cluster_share_shift | train_expectancy_R | oos_expectancy_R | cluster_expectancy_persistence | train_path_entropy | oos_path_entropy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dead_breakout | dead_breakout | 301 | 47 | 0.169673 | 0.233831 | 0.064158 | -0.083891 | -0.883462 | 10.5311 | 0.936516 | 0.488909 |
| dead_breakout_3 | dead_breakout | 32 | 10 | 0.018038 | 0.049751 | 0.031713 | -1.35336 | -1.64211 | 1.21336 | -0 | -0 |
| weak_breakout | weak_breakout | 505 | 67 | 0.284667 | 0.333333 | 0.048666 | -0.469311 | -0.466634 | 0.994295 | 1.88129 | 2.00795 |
| dead_breakout_2 | dead_breakout | 142 | 29 | 0.080045 | 0.144279 | 0.064234 | -1.0963 | -0.969957 | 0.884757 | 0.283398 | 0.929364 |
| uneven_continuation | uneven_continuation | 439 | 2 | 0.247463 | 0.00995 | -0.237513 | 1.88147 | 1.32122 | 0.702229 | 1.95644 | -0 |
| failed_pop | failed_pop | 82 | 11 | 0.046223 | 0.054726 | 0.008503 | 1.63835 | 0.991226 | 0.605014 | 1.38935 | 0.94566 |
| clean_continuation | clean_continuation | 263 | 35 | 0.148253 | 0.174129 | 0.025877 | 2.4823 | 1.48646 | 0.598824 | 1.73438 | -0 |
| clean_continuation_2 | clean_continuation | 10 | 0 | 0.005637 | 0 | -0.005637 | 7.53138 | 0 | 0 | -0 | 0 |

## Predictability Ceiling

| target | scope | model | accuracy | majority_baseline_accuracy | lift_vs_baseline | precision_positive | recall_positive | feature_family | feature_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bad_state | anchored_oos | band_probability | 0.761194 | 0.761194 | 0 | 0.761194 | 1 | core_feature_set | 10 |
| bad_state | anchored_oos | band_probability | 0.761194 | 0.761194 | 0 | 0.761194 | 1 | axis_state_only | 4 |
| bad_state | anchored_oos | band_probability | 0.761194 | 0.761194 | 0 | 0.761194 | 1 | scenario_family_only | 1 |
| bad_state | anchored_oos | logistic | 0.761194 | 0.761194 | 0 | 0.761194 | 1 | scenario_family_only | 1 |
| bad_state | anchored_oos | majority | 0.761194 | 0.761194 | 0 | 0.761194 | 1 | baseline | 0 |
| bad_state | anchored_oos | logistic | 0.626866 | 0.761194 | -0.134328 | 0.724138 | 0.823529 | axis_state_only | 4 |
| bad_state | anchored_oos | logistic | 0.567164 | 0.761194 | -0.19403 | 0.805556 | 0.568627 | core_feature_set | 10 |
| clean_state | anchored_oos | band_probability | 0.825871 | 0.825871 | 0 | 0 | 0 | core_feature_set | 10 |
| clean_state | anchored_oos | band_probability | 0.825871 | 0.825871 | 0 | 0 | 0 | axis_state_only | 4 |
| clean_state | anchored_oos | band_probability | 0.825871 | 0.825871 | 0 | 0 | 0 | scenario_family_only | 1 |
| clean_state | anchored_oos | logistic | 0.825871 | 0.825871 | 0 | 0 | 0 | core_feature_set | 10 |
| clean_state | anchored_oos | logistic | 0.825871 | 0.825871 | 0 | 0 | 0 | axis_state_only | 4 |
| clean_state | anchored_oos | logistic | 0.825871 | 0.825871 | 0 | 0 | 0 | scenario_family_only | 1 |
| clean_state | anchored_oos | majority | 0.825871 | 0.825871 | 0 | 0 | 0 | baseline | 0 |
| multiclass | anchored_oos | band_probability | 0.333333 | 0.333333 | 0 |  |  | scenario_family_only | 1 |
| multiclass | anchored_oos | logistic | 0.333333 | 0.333333 | 0 |  |  | scenario_family_only | 1 |
| multiclass | anchored_oos | majority | 0.333333 | 0.333333 | 0 |  |  | baseline | 0 |
| multiclass | anchored_oos | band_probability | 0.263682 | 0.333333 | -0.069652 |  |  | axis_state_only | 4 |
| multiclass | anchored_oos | band_probability | 0.19403 | 0.333333 | -0.139303 |  |  | core_feature_set | 10 |
| multiclass | anchored_oos | logistic | 0.129353 | 0.333333 | -0.20398 |  |  | axis_state_only | 4 |
| multiclass | anchored_oos | logistic | 0.109453 | 0.333333 | -0.223881 |  |  | core_feature_set | 10 |

## Target Design Comparison

| target | best_feature_family | best_model | accuracy | lift_vs_baseline | recall_positive | precision_positive |
| --- | --- | --- | --- | --- | --- | --- |
| bad_state | core_feature_set | band_probability | 0.761194 | 0 | 1 | 0.761194 |
| clean_state | core_feature_set | band_probability | 0.825871 | 0 | 0 | 0 |

## Feature Family Expansion

| target | family_name | base_lift | family_lift | lift_delta | base_recall_positive | family_recall_positive | recall_delta | accepted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bad_state | market_structure | -0.19403 | -0.179104 | 0.014926 | 0.568627 | 0.699346 | 0.130719 | True |
| bad_state | crowding | -0.19403 | -0.19403 | 0 | 0.568627 | 0.568627 | 0 | False |
| bad_state | setup_context | -0.19403 | -0.328358 | -0.134328 | 0.568627 | 0.392157 | -0.17647 | False |
| clean_state | market_structure | 0 | 0 | 0 | 0 | 0 | 0 | False |
| clean_state | setup_context | 0 | 0 | 0 | 0 | 0 | 0 | False |
| clean_state | crowding | 0 | 0 | 0 | 0 | 0 | 0 | False |

## Holdout Audit

| target | holdout_type | holdout_value | accuracy | lift_vs_baseline | recall_positive |
| --- | --- | --- | --- | --- | --- |
| bad_state | sector_bucket | software/internet | 0.538781 | -0.037396 | 0.519231 |
| bad_state | sector_bucket | semis | 0.444444 | -0.087963 | 0.510145 |
| bad_state | sector_bucket | other tech | 0.435897 | -0.145299 | 0.522059 |
| bad_state | sector_bucket | other | 0.470588 | -0.041176 | 0.674699 |
| bad_state | symbol | QCOM | 0.422886 | -0.268657 | 0.446043 |
| bad_state | symbol | AVGO | 0.497207 | -0.067039 | 0.811881 |
| bad_state | symbol | COST | 0.470588 | -0.041176 | 0.674699 |
| bad_state | symbol | AAPL | 0.431953 | -0.112426 | 0.586957 |
| bad_state | symbol | AMD | 0.454545 | -0.084848 | 0.552632 |
| bad_state | symbol | AMZN | 0.602484 | -0.15528 | 0.606557 |
| bad_state | symbol | MSFT | 0.596154 | 0.038462 | 0.83908 |
| bad_state | symbol | GOOGL | 0.405594 | -0.160839 | 0.935484 |
| bad_state | symbol | META | 0.359712 | -0.18705 | 0.618421 |
| bad_state | symbol | NFLX | 0.544715 | -0.01626 | 0.753623 |

## Economic Action Diagnostic

| scope | policy_name | baseline_expectancy | diagnostic_expectancy | baseline_return_proxy | diagnostic_return_proxy | trade_count | diagnostic_trade_count | saved_loss | missed_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anchored_oos | bad_skip_clean_overweight | -0.257538 | 0 | -51.7651 | 0 | 201 | 0 | 119.808 | 68.0434 |
| full_period | bad_skip_clean_overweight | 0.585221 | 2.14819 | 1152.3 | 1671.29 | 1969 | 778 | 787.958 | 330.666 |
| train | bad_skip_clean_overweight | 0.691788 | 2.19269 | 1227.23 | 1705.91 | 1774 | 778 | 668.149 | 254.66 |