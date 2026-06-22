# Task 341: Strong Subset Refinement & Regime-Specific Edge Strengthening

Final decision: **REGIME_CONDITIONAL_EDGE**

## Window Failure vs Success


Failure and success windows were compared inside the fixed `entry_only + high_atr + vol_expanding` subset to isolate what changed across time.

## Best Refinement Read

| window_id | window_group | subset_trade_count | subset_expectancy | expectancy_delta |
| --- | --- | --- | --- | --- |
| window_1 | failure_window | 0 |  |  |
| window_2 | success_window | 10 | 1.01295 | 0.935104 |
| window_3 | failure_window | 5 | -0.361447 | -2.10817 |
| window_4 | success_window | 19 | 0.815959 | 0.555811 |

- Best candidate: `candidate_C`
- Anchored OOS expectancy delta vs base subset: `1.467233`
- Rolling positive windows: `4`
- Converted failure windows: `2`
- Holdout mean lift: `0.604018`
- Symbol concentration share: `1.0`

## Regime Conditioning

- Strongest live-eligible regime signature: `sector_group=software_internet AND scenario_family=PIVOT_HIGH`

## Size Overlay


## Interpretation

- The key difference between failure and success windows is summarized by the subset refinement tables and the resulting regime signature above.
- The best refinement candidate was `candidate_C`, but the final classification remained `REGIME_CONDITIONAL_EDGE` after rolling, holdout, and cost checks.
- Next step: engine gating for a live-eligible regime overlay
| policy_name | trade_count | expectancy | return_proxy | saved_loss | missed_gain | max_drawdown_proxy |
| --- | --- | --- | --- | --- | --- | --- |
| base_subset_only | 33 | 0.260148 | 8.58487 | 0 | 0 | 0 |
| refined_binary | 5 | 1.72738 | 8.6369 | 12.0891 | 12.037 | 0 |
| size_overlay | 33 | 0.391798 | 12.9293 | 0 | 0 | 0 |
