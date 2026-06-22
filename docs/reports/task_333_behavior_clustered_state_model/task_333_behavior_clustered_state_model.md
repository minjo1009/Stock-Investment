# Task 333: Behavior Clustered State Model

- Final decision: `BEHAVIOR_STATE_NEEDS_REFINEMENT`.
- Selected cluster model: `agglomerative` with `K=8`.
- Best OOS predictor: `band_probability_aggregation` with OOS lift `0.000`.

## Cluster Model Candidates

| method | k | within_cluster_behavior_variance | path_entropy | between_cluster_expectancy_dispersion | oos_cluster_assignment_stability | oos_linkage_retention | min_train_cluster_count | min_oos_cluster_count | sparsity_risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kmeans | 4 | 25.5498 | 1.28743 | 1.48985 | 0.885194 | 1.13656 | 92 | 4 | 0.25 |
| kmeans | 5 | 29.2811 | 1.09019 | 3.08708 | 0.683224 | 0.779716 | 14 | 0 | 0.2 |
| kmeans | 6 | 28.2475 | 1.03896 | 2.94785 | 0.755941 | 1.09399 | 14 | 0 | 0.166667 |
| kmeans | 7 | 29.9152 | 1.12222 | 2.76793 | 0.69638 | 0.879484 | 14 | 0 | 0.428571 |
| kmeans | 8 | 30.4811 | 1.08418 | 2.63832 | 0.66776 | 0.646352 | 14 | 0 | 0.5 |
| agglomerative | 4 | 27.6957 | 1.3417 | 1.52816 | 0.886585 | -0.116989 | 86 | 2 | 0.25 |
| agglomerative | 5 | 30.7275 | 1.07842 | 2.9592 | 0.903442 | -0.064102 | 10 | 0 | 0.2 |
| agglomerative | 6 | 29.4659 | 1.0267 | 2.8295 | 0.798185 | 1.01022 | 10 | 0 | 0.166667 |
| agglomerative | 7 | 30.5775 | 1.14631 | 2.69525 | 0.75685 | 1.53724 | 10 | 0 | 0.285714 |
| agglomerative | 8 | 26.9495 | 1.02267 | 2.70431 | 0.75685 | 1.9412 | 10 | 0 | 0.25 |
| gaussian_mixture | 4 | 34.0629 | 1.55923 | 1.35708 | 0.764742 | -0.03733 | 178 | 0 | 0.5 |
| gaussian_mixture | 5 | 34.5311 | 1.52649 | 1.37768 | 0.741007 | 0.497052 | 58 | 1 | 0.4 |
| gaussian_mixture | 6 | 33.2205 | 1.31023 | 2.95968 | 0.817704 | 0.220364 | 14 | 0 | 0.5 |
| gaussian_mixture | 7 | 27.9958 | 1.06021 | 2.6675 | 0.789188 | 0.034617 | 10 | 0 | 0.714286 |
| gaussian_mixture | 8 | 35.4609 | 1.10899 | 2.91609 | 0.74032 | 0.192012 | 14 | 0 | 0.625 |

## Behavior vs Axis State Comparison

| framework | payoff_separation | within_state_behavior_variance | path_entropy | OOS_retention | density | sparsity_risk | interpretability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| behavior_clusters | 2.70431 | 3.82359 | 1.02267 | 1.9412 | 221.75 | 0.25 | medium_high |
| task_329_state_model | 0.496093 | 3.82359 | 1.50612 | -0.472453 | 98.5556 | 0.611111 | high |
| task_332_candidate_C | 0.659272 | 3.82359 | 1.66472 | 0.243899 | 77.1304 | 0.608696 | medium |

## Prediction Metrics

| scope | model | accuracy | majority_baseline_accuracy | lift_vs_baseline | precision_bad_clusters | recall_bad_clusters | precision_clean_continuation | recall_clean_continuation | brier_score_mean | ece_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anchored_oos | band_probability_aggregation | 0.333333 | 0.333333 | 0 | 0 | 0 | 0 | 0 | 0.121537 | 0.068157 |
| anchored_oos | majority_baseline | 0.333333 | 0.333333 | 0 | 0 | 0 | 0 | 0 | 0.190476 | 0.190476 |
| anchored_oos | logistic_regression | 0.109453 | 0.333333 | -0.223881 | 0 | 0 | 0 | 0 | 0.132558 | 0.112136 |
| anchored_oos | decision_tree | 0.079602 | 0.333333 | -0.253731 | 0 | 0 | 0 | 0 | 0.132883 | 0.10071 |

## Diagnostic Action Test

| scope | model | baseline_expectancy | diagnostic_expectancy | baseline_return_proxy | diagnostic_return_proxy | trade_count | diagnostic_trade_count | saved_loss | missed_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anchored_oos | logistic_regression | -0.257538 | -0.225402 | -51.7651 | -36.5151 | 201 | 162 | 24.6835 | 9.4336 |
| anchored_oos | majority_baseline | -0.257538 | -0.257538 | -51.7651 | -51.7651 | 201 | 201 | 0 | 0 |
| anchored_oos | band_probability_aggregation | -0.257538 | -0.257538 | -51.7651 | -51.7651 | 201 | 201 | 0 | 0 |
| anchored_oos | decision_tree | -0.257538 | -0.351112 | -51.7651 | -63.2002 | 201 | 180 | 3.71498 | 15.1502 |
| full_period | logistic_regression | 0.585221 | 0.635139 | 1152.3 | 1056.87 | 1969 | 1664 | 154.464 | 249.893 |
| full_period | majority_baseline | 0.585221 | 0.585221 | 1152.3 | 1152.3 | 1969 | 1969 | 0 | 0 |
| full_period | band_probability_aggregation | 0.585221 | 0.585221 | 1152.3 | 1152.3 | 1969 | 1969 | 0 | 0 |
| full_period | decision_tree | 0.585221 | 0.567023 | 1152.3 | 1029.15 | 1969 | 1815 | 65.7201 | 188.873 |