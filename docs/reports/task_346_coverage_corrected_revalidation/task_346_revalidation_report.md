# Task 346: Coverage-Corrected Revalidation of Intraday Edge

Final decision: **PARTIAL_ARTIFACT_WITH_REAL_WEAKNESS**

## Edge Reclassification

| layer | classification |
| --- | --- |
| signal | PARTIAL |
| subset | STRONG |
| portfolio | NONE |

## Selected Revalidation Comparison

| task_id | metric | original_value | corrected_value | delta |
| --- | --- | --- | --- | --- |
| task_338 | decision | PARTIAL_INTRADAY_EDGE | PARTIAL_INTRADAY_EDGE |  |
| task_338 | covered_trade_count | 50 | 98 | 48 |
| task_338 | best_lift | 0.1875 | 0.020833 | -0.166667 |
| task_338 | best_expectancy | 0.467782 | -0.322607 | -0.790389 |
| task_338 | best_accuracy | 0.9 | 0.867347 | -0.032653 |
| task_339 | decision | CLEAR_STRONG_SUBSET | CLEAR_STRONG_SUBSET |  |
| task_339 | best_subset_id | entry_only|atr_regime:high_atr|contraction_regime:vol_expanding | entry_only|contraction_regime:vol_expanding|sector_group:software_internet |  |
| task_339 | top_score | 0.829503 | 0.926031 | 0.0965274 |
| task_339 | top_oos_lift | 0.051515 | 0.409014 | 0.357499 |
| task_339 | top_expectancy_delta | 0.377037 | 1.02517 | 0.648137 |
| task_339 | top_trade_count | 33 | 24 | -9 |
| task_340 | decision | REJECT_SUBSET | STRONG_EDGE_READY_FOR_DEPLOYMENT |  |
| task_340 | positive_windows | 4 | 4 | 0 |
| task_340 | anchored_expectancy | 0.260148 | 0.185608 | -0.07454 |
| task_340 | perm_p_value | 0.151 | 0.003 | -0.148 |
| task_340 | random_percentile | 85.9 | 99.3 | 13.4 |
| task_340 | scenario1_expectancy | 0.160148 | 0.085608 | -0.07454 |
| task_341 | decision | REGIME_CONDITIONAL_EDGE | REJECT_REFINED |  |
| task_341 | best_candidate_id | candidate_C | candidate_A |  |
| task_341 | best_candidate_expectancy | 1.72738 | -0.532974 | -2.26035 |

## Subset Consistency

| check_name | original_value | corrected_value | delta | status |
| --- | --- | --- | --- | --- |
| high_atr_plus_vol_expanding_subset | 0.260148 | 0.185608 | -0.07454 | remains_strong |
| high_atr_plus_vol_expanding_positive_windows | 4 | 4 | 0 | unchanged_or_weaker |
| software_internet_regime_rule | sector_group=software_internet AND scenario_family=PIVOT_HIGH | sector_group=software_internet AND scenario_family=PIVOT_HIGH |  | still_holds |
| software_internet_regime_expectancy | 0.840873 | 0.840873 | 0 | stable_or_weaker |
| software_internet_trade_count | 16 | 25 | 9 | expanded |

## Failure Attribution

| layer | data_artifact_pct | real_signal_weakness_pct | basis_metric | rationale |
| --- | --- | --- | --- | --- |
| signal | 48.98 | 51.02 | anchored_oos_covered_trade_gain | Coverage correction directly expanded the OOS sample used for signal estimation. |
| subset | 44.83 | 55.17 | software_internet_oos_trade_gain | Subset validation depended on the software/internet conditional sample that was previously under-covered. |
| portfolio | 10 | 90 | portfolio_decision_change | Hybrid-full overlay still reflects substantial real weakness because uncovered trades remain neutral and cost stress remains binding. |
| overall | 34.6 | 65.4 | average_layer_attribution | Overall attribution averages signal, subset, and portfolio layers to separate coverage artifact from remaining live weakness. |

## Interpretation

- Task 345 coverage correction materially increases the anchored OOS sample used by the intraday evaluation stack.
- Task 346 isolates whether that larger covered universe changes the signal, subset, and portfolio conclusions without changing any strategy logic.
- Final answer: `PARTIAL_ARTIFACT_WITH_REAL_WEAKNESS`.