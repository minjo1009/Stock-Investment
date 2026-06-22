# Task 347 - Conditional Priority / Slot Allocation Overlay

- decision: NO_TRANSLATION_EDGE
- best_variant: priority_top3
- best_max_positions: 10
- best_sector_cap: none
- anchored_oos_sharpe_delta: 1.17635
- anchored_oos_mdd_delta: -23.391602
- anchored_oos_expectancy_delta: 0.121945
- rolling_positive_windows: 1
- survives_cost_2x: False
- survives_cost_3x: False

## Key Answer
Priority/slot allocation converts subset edge into portfolio improvement only if anchored OOS Sharpe rises, drawdown falls, and that improvement survives rolling windows and cost stress.

## Best Anchored OOS Comparison
| variant | sharpe_delta | mdd_delta | expectancy_delta | return_delta | trade_count |
| --- | --- | --- | --- | --- | --- |
| priority_top3 | 1.17635 | -23.3916 | 0.121945 | 25.6724 | 97 |

## Slot Utilization
| avg_candidates_per_day | avg_selected_per_day | pct_filtered_out | avg_selected_priority_score | priority_concentration |
| --- | --- | --- | --- | --- |
| 8.125 | 4.04167 | 50.2564 | 1.6701 | 0.268041 |