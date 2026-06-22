# Task 360 - Read-only Shadow Integration & Historical Replay Evaluation

- shadow_enabled: True
- baseline_preserved: True
- baseline_metrics_unchanged: True
- baseline_net_pnl_r: 29.544324
- shadow_proxy_net_pnl_r: -4.892553
- benchmark_net_pnl_r: 3.242802

## Summary
1. Baseline continuation sleeve behavior remains unchanged.
2. Shadow mode computes read-only state/factor/exposure/staged decisions on copied rows.
3. Shadow proxy metrics are diagnostic only and do not alter actual fills or baseline PnL.

## Engine Summary
| mode | net_pnl_r | anchored_oos_net_pnl_r | trade_count | rolling_oos_robustness | blocked_entries | blocked_adds | reduced_entries | reduced_adds | state_distribution | baseline_preserved |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 29.5443 | -1.28962 | 217 | 0.75 | 0 | 0 | 0 | 0 |  | True |
| shadow_gated_proxy | -4.89255 | -0.556491 | 217 | 0 | 0 | 200 | 203 | 5 | CROWDED:0.0184|DISLOCATION:0.9032|ELEVATED:0.0138|NORMAL:0.0645 | True |
| full_dislocation_benchmark | 3.2428 | -0.075796 | 170 | 0.75 |  |  |  |  |  | True |

## Window Comparison
| window_name | baseline_trade_count | shadow_blocked_entries | shadow_blocked_adds | shadow_reduced_entries | shadow_reduced_adds | avg_continuation_risk_score | state_label_distribution | factor_violation_rate | dislocation_add_block_rate | baseline_net_pnl_r | shadow_gated_pnl_proxy_r | failure_window_loss_reduction_proxy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_period | 217 | 0 | 200 | 203 | 5 | 0.855576 | CROWDED:0.0184|DISLOCATION:0.9032|ELEVATED:0.0138|NORMAL:0.0645 | 0 | 0.903226 | 141.542 | 12.475 | -80.9188 |
| anchored_oos | 12 | 0 | 11 | 11 | 0 | 0.8325 | CROWDED:0.0833|DISLOCATION:0.8333|NORMAL:0.0833 | 0 | 0.833333 | -4.53293 | -1.24008 | -6.64036 |
| 2025-12 | 2 | 0 | 2 | 2 | 0 | 0.915 | DISLOCATION:1.0 | 0 | 1 | -1.21381 | -0.084966 | -1.12884 |
| 2026-01 | 5 | 0 | 4 | 4 | 0 | 0.778 | DISLOCATION:0.8|NORMAL:0.2 | 0 | 0.8 | -2.71892 | -0.982636 | -2.96502 |
| semis_bucket | 81 | 0 | 81 | 81 | 0 | 0.93 | DISLOCATION:1.0 | 0 | 1 | 54.3496 | 3.80447 | -35.7629 |
| non_semis_bucket | 136 | 0 | 119 | 122 | 5 | 0.81125 | CROWDED:0.0294|DISLOCATION:0.8456|ELEVATED:0.0221|NORMAL:0.1029 | 0 | 0.845588 | 87.1929 | 8.67053 | -45.1559 |

## Factor Diagnostics
| factor_name | violation_count | violation_rate | avg_risk_score | blocked_entry_rate |
| --- | --- | --- | --- | --- |
| STATE::CROWDED | 0 | 0 | 0.67 | 0 |
| STATE::DISLOCATION | 0 | 0 | 0.912398 | 0 |
| STATE::ELEVATED | 0 | 0 | 0.45 | 0 |
| STATE::NORMAL | 0 | 0 | 0.2 | 0 |