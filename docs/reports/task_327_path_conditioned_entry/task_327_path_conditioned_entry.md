# Task 327 Revised: Regime-Conditioned Path Prediction

## Core Answer

The system predicts failure path probabilities at entry time rather than selecting globally good entries.

## Path Outcome Summary

| path_type | trade_count | expectancy_r | win_rate | avg_r | total_r | pnl_contribution_share |
| --- | --- | --- | --- | --- | --- | --- |
| strong_continuation | 51 | 1.20888 | 0.803922 | 1.20888 | 61.6527 | -1.19101 |
| weak_continuation | 9 | 0.0741124 | 0.777778 | 0.0741124 | 0.667012 | -0.012885 |
| slow_grind | 9 | -0.46618 | 0.222222 | -0.46618 | -4.19562 | 0.081051 |
| volatile_noise | 48 | -0.550327 | 0.0416667 | -0.550327 | -26.4157 | 0.5103 |
| early_failure | 84 | -0.993732 | 0.0238095 | -0.993732 | -83.4735 | 1.61254 |

## Prediction Metrics

| metric_type | scope | accuracy | majority_class_accuracy | accuracy_lift_vs_baseline | precision_strong_continuation | recall_early_failure | actual_path | predicted_path | trade_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| summary | train | 0.514092 | 0.3354 | 0.178692 | 0.563107 | 0.631957 |  |  | 1774 |
| confusion_matrix | train |  |  |  |  |  | early_failure | early_failure | 352 |
| confusion_matrix | train |  |  |  |  |  | early_failure | strong_continuation | 26 |
| confusion_matrix | train |  |  |  |  |  | early_failure | weak_continuation | 179 |
| confusion_matrix | train |  |  |  |  |  | slow_grind | early_failure | 54 |
| confusion_matrix | train |  |  |  |  |  | slow_grind | strong_continuation | 2 |
| confusion_matrix | train |  |  |  |  |  | slow_grind | weak_continuation | 102 |
| confusion_matrix | train |  |  |  |  |  | strong_continuation | early_failure | 99 |
| confusion_matrix | train |  |  |  |  |  | strong_continuation | strong_continuation | 58 |
| confusion_matrix | train |  |  |  |  |  | strong_continuation | weak_continuation | 207 |
| confusion_matrix | train |  |  |  |  |  | volatile_noise | early_failure | 45 |
| confusion_matrix | train |  |  |  |  |  | volatile_noise | strong_continuation | 10 |
| confusion_matrix | train |  |  |  |  |  | volatile_noise | volatile_noise | 8 |
| confusion_matrix | train |  |  |  |  |  | volatile_noise | weak_continuation | 37 |
| confusion_matrix | train |  |  |  |  |  | weak_continuation | early_failure | 94 |
| confusion_matrix | train |  |  |  |  |  | weak_continuation | strong_continuation | 7 |
| confusion_matrix | train |  |  |  |  |  | weak_continuation | weak_continuation | 494 |
| summary | anchored_oos | 0.19403 | 0.41791 | -0.223881 | 0.5 | 0.238095 |  |  | 201 |
| confusion_matrix | anchored_oos |  |  |  |  |  | early_failure | early_failure | 20 |
| confusion_matrix | anchored_oos |  |  |  |  |  | early_failure | weak_continuation | 64 |
| confusion_matrix | anchored_oos |  |  |  |  |  | slow_grind | early_failure | 2 |
| confusion_matrix | anchored_oos |  |  |  |  |  | slow_grind | weak_continuation | 7 |
| confusion_matrix | anchored_oos |  |  |  |  |  | strong_continuation | early_failure | 33 |
| confusion_matrix | anchored_oos |  |  |  |  |  | strong_continuation | strong_continuation | 10 |
| confusion_matrix | anchored_oos |  |  |  |  |  | strong_continuation | weak_continuation | 8 |
| confusion_matrix | anchored_oos |  |  |  |  |  | volatile_noise | early_failure | 2 |
| confusion_matrix | anchored_oos |  |  |  |  |  | volatile_noise | strong_continuation | 10 |
| confusion_matrix | anchored_oos |  |  |  |  |  | volatile_noise | weak_continuation | 36 |
| confusion_matrix | anchored_oos |  |  |  |  |  | weak_continuation | weak_continuation | 9 |
| summary | full_period | 0.482986 | 0.32453 | 0.158456 | 0.552846 | 0.58216 |  |  | 1969 |
| confusion_matrix | full_period |  |  |  |  |  | early_failure | early_failure | 372 |
| confusion_matrix | full_period |  |  |  |  |  | early_failure | strong_continuation | 26 |
| confusion_matrix | full_period |  |  |  |  |  | early_failure | weak_continuation | 241 |
| confusion_matrix | full_period |  |  |  |  |  | slow_grind | early_failure | 56 |
| confusion_matrix | full_period |  |  |  |  |  | slow_grind | strong_continuation | 2 |
| confusion_matrix | full_period |  |  |  |  |  | slow_grind | weak_continuation | 109 |
| confusion_matrix | full_period |  |  |  |  |  | strong_continuation | early_failure | 132 |
| confusion_matrix | full_period |  |  |  |  |  | strong_continuation | strong_continuation | 68 |
| confusion_matrix | full_period |  |  |  |  |  | strong_continuation | weak_continuation | 211 |
| confusion_matrix | full_period |  |  |  |  |  | volatile_noise | early_failure | 47 |
| confusion_matrix | full_period |  |  |  |  |  | volatile_noise | strong_continuation | 20 |
| confusion_matrix | full_period |  |  |  |  |  | volatile_noise | volatile_noise | 8 |
| confusion_matrix | full_period |  |  |  |  |  | volatile_noise | weak_continuation | 73 |
| confusion_matrix | full_period |  |  |  |  |  | weak_continuation | early_failure | 94 |
| confusion_matrix | full_period |  |  |  |  |  | weak_continuation | strong_continuation | 7 |
| confusion_matrix | full_period |  |  |  |  |  | weak_continuation | weak_continuation | 503 |

## Calibration Metrics

| scope | class_name | brier_score | naive_brier_score | ece | avg_predicted_prob | realized_frequency |
| --- | --- | --- | --- | --- | --- | --- |
| train | strong_continuation | 0.150092 | 0.163085 | 0.0666 | 0.207915 | 0.205186 |
| train | weak_continuation | 0.191012 | 0.222907 | 0.094663 | 0.328675 | 0.3354 |
| train | early_failure | 0.180785 | 0.215396 | 0.067287 | 0.294924 | 0.31398 |
| train | volatile_noise | 0.047278 | 0.053192 | 0.025432 | 0.067683 | 0.05637 |
| train | slow_grind | 0.072949 | 0.081132 | 0.031691 | 0.100802 | 0.089064 |
| anchored_oos | strong_continuation | 0.208623 | 0.191708 | 0.220855 | 0.207779 | 0.253731 |
| anchored_oos | weak_continuation | 0.123066 | 0.127234 | 0.281471 | 0.326247 | 0.044776 |
| anchored_oos | early_failure | 0.258046 | 0.254063 | 0.112148 | 0.305762 | 0.41791 |
| anchored_oos | volatile_noise | 0.204748 | 0.215061 | 0.172621 | 0.066185 | 0.238806 |
| anchored_oos | slow_grind | 0.043616 | 0.044733 | 0.049249 | 0.094025 | 0.044776 |
| full_period | strong_continuation | 0.155028 | 0.165178 | 0.03904 | 0.208084 | 0.208735 |
| full_period | weak_continuation | 0.184221 | 0.213477 | 0.102752 | 0.328274 | 0.306755 |
| full_period | early_failure | 0.188542 | 0.219322 | 0.059183 | 0.296019 | 0.32453 |
| full_period | volatile_noise | 0.063482 | 0.069869 | 0.007643 | 0.067522 | 0.075165 |
| full_period | slow_grind | 0.070144 | 0.077639 | 0.031068 | 0.100101 | 0.084815 |

## Integrated Summary

| variant | scope | cagr_pct | sharpe | max_drawdown_pct | total_return_pct | total_r | expectancy_r | win_rate | trade_count | avg_holding_days | avg_loss_r | avg_win_r | profit_factor | max_losing_streak | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | anchored_oos | -10.7024 | -1.1988 | 10.1213 | -5.15865 | -5.17651 | -0.271175 | 0.262535 | 20.1 | 8.093 | -0.809192 | 1.19657 | 0.538455 | 6.7 | BASELINE |
| prob_path_conditioned_entry | anchored_oos | -6.45087 | -1.3866 | 5.37284 | -3.06679 | -5.17651 | -0.271175 | 0.262535 | 20.1 | 8.093 | -0.809192 | 1.19657 | 0.538455 | 6.7 | REJECT |
| prob_path_conditioned_entry + size50 | anchored_oos | -5.96525 | -1.30078 | 5.07046 | -2.83368 | -4.6821 | -0.246341 | 0.262535 | 20.1 | 8.093 | -0.773688 | 1.1942 | 0.562729 | 6.7 | REJECT |
| prob_path_conditioned_size | anchored_oos | -6.45087 | -1.3866 | 5.37284 | -3.06679 | -5.17651 | -0.271175 | 0.262535 | 20.1 | 8.093 | -0.809192 | 1.19657 | 0.538455 | 6.7 | REJECT |
| baseline | full_period | 22.0801 | 1.23394 | 12.0493 | 173.961 | 115.23 | 0.581862 | 0.490451 | 196.9 | 15.5155 | -0.793112 | 2.05062 | 2.43613 | 8.8 | BASELINE |
| prob_path_conditioned_entry | full_period | 12.1015 | 1.28136 | 6.63112 | 77.5056 | 115.842 | 0.587126 | 0.492352 | 196.2 | 15.5524 | -0.792262 | 2.05062 | 2.45768 | 8.8 | REJECT |
| prob_path_conditioned_entry + size50 | full_period | 12.2134 | 1.2957 | 6.50108 | 78.4031 | 116.921 | 0.592594 | 0.492352 | 196.2 | 15.5524 | -0.778781 | 2.04788 | 2.49818 | 8.8 | REJECT |
| prob_path_conditioned_size | full_period | 12.0205 | 1.27097 | 6.66933 | 76.8686 | 115.129 | 0.580975 | 0.490237 | 197 | 15.5113 | -0.793136 | 2.05062 | 2.43402 | 8.8 | REJECT |