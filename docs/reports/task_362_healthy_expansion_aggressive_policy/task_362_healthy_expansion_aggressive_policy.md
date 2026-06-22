# Task 362 - Healthy Expansion Aggressive Participation Calibration

## Core Answers
1. Did aggressive healthy-expansion policy improve full-period monetization vs Task 361 quality-aware policy? NO
2. Did it preserve anchored OOS improvement vs baseline? YES
3. Did it avoid relaxing suppression under FRAGILE_CROWDING? YES
4. Did it actually increase add/size activation under HEALTHY_EXPANSION? NO
5. Current bottleneck assessment: classifier too conservative or row-level proxy insufficient

## Policy Comparison
| policy_name | net_pnl_r | anchored_oos_net_pnl_r | trade_count | monetization_retention_ratio |
| --- | --- | --- | --- | --- |
| baseline | 29.5443 | -1.28962 | 217 | 1 |
| old_shadow_policy | -4.89255 | -0.556491 | 217 | -0.1656 |
| quality_aware_shadow_policy | -3.06637 | -0.53014 | 217 | -0.103789 |
| healthy_expansion_aggressive_policy | -4.76057 | -0.556491 | 217 | -0.161133 |

## Quality Label Comparison
| participation_quality_label | trade_count | baseline_pnl_r | old_shadow_proxy_pnl_r | quality_aware_proxy_pnl_r | healthy_aggressive_proxy_pnl_r | avg_quality_aware_size_multiplier | avg_healthy_aggressive_size_multiplier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| HEALTHY_EXPANSION | 17 | 1.06529 | 0.720587 | 0.434182 | 0.720587 | 0.682353 | 0.531765 |
| NEUTRAL_PARTICIPATION | 77 | 45.8921 | 6.05624 | 11.408 | 6.38619 | 0.276623 | 0.163766 |
| FRAGILE_CROWDING | 123 | 94.5851 | 5.69818 | 6.42233 | 5.69818 | 0.07122 | 0.07813 |
| UNKNOWN | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Failure Window Comparison
| window_name | baseline_net_pnl_r | old_shadow_net_pnl_r | quality_aware_net_pnl_r | healthy_aggressive_net_pnl_r | fragile_crowding_share | healthy_expansion_share |
| --- | --- | --- | --- | --- | --- | --- |
| full_period | 141.542 | 12.475 | 18.2645 | 12.8049 | 0.56682 | 0.078341 |
| anchored_oos | -4.53293 | -1.24008 | -0.778714 | -1.24008 | 0.833333 | 0 |
| 2025-12 | -1.21381 | -0.084966 | -0.084966 | -0.084966 | 1 | 0 |
| 2026-01 | -2.71892 | -0.982636 | -0.389362 | -0.982636 | 0.8 | 0 |

## Activation Diagnostics
| participation_quality_label | trade_count_affected | old_shadow_add_count | quality_aware_add_count | healthy_aggressive_add_count | quality_aware_size_floor_activations | healthy_aggressive_size_floor_activations |
| --- | --- | --- | --- | --- | --- | --- |
| HEALTHY_EXPANSION | 17 | 10 | 10 | 3 | 9 | 0 |
| NEUTRAL_PARTICIPATION | 77 | 8 | 8 | 0 | 69 | 1 |
| FRAGILE_CROWDING | 123 | 1 | 0 | 0 | 0 | 1 |

## Violation Checks
| fragile_crowding_relax_violations | dislocation_relax_violations |
| --- | --- |
| 0 | 0 |