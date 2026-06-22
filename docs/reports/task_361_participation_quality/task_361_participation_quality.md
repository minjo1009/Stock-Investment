# Task 361 - Participation Quality / Crowding Fragility Modeling

## Core Answers
1. Did Task 360 suppress healthy expansion too aggressively? YES
2. Did fragile crowding explain failure windows better than generic crowding? YES
3. Should future allocator calibration relax suppression under healthy expansion? YES

## Participation Quality Distribution
| participation_quality_label | trade_count | trade_share | avg_expansion_score | avg_fragility_score | avg_confidence |
| --- | --- | --- | --- | --- | --- |
| HEALTHY_EXPANSION | 17 | 0.078341 | 0.588307 | 0.407804 | 1 |
| NEUTRAL_PARTICIPATION | 77 | 0.354839 | 0.48425 | 0.495223 | 1 |
| FRAGILE_CROWDING | 123 | 0.56682 | 0.386714 | 0.590735 | 1 |
| UNKNOWN | 0 | 0 | 0 | 0 | 0 |

## Baseline vs Shadow PnL by Label
| participation_quality_label | trade_count | baseline_pnl_r | old_shadow_proxy_pnl_r | quality_aware_proxy_pnl_r | avg_old_shadow_size_multiplier | avg_quality_aware_size_multiplier |
| --- | --- | --- | --- | --- | --- | --- |
| HEALTHY_EXPANSION | 17 | 1.06529 | 0.720587 | 0.434182 | 0.531765 | 0.682353 |
| NEUTRAL_PARTICIPATION | 77 | 45.8921 | 6.05624 | 11.408 | 0.161039 | 0.276623 |
| FRAGILE_CROWDING | 123 | 94.5851 | 5.69818 | 6.42233 | 0.07813 | 0.07122 |
| UNKNOWN | 0 | 0 | 0 | 0 | 0 | 0 |

## Failure Window Comparison
| window_name | trade_count | baseline_pnl_r | old_shadow_proxy_pnl_r | quality_aware_proxy_pnl_r | healthy_expansion_share | fragile_crowding_share | label_distribution |
| --- | --- | --- | --- | --- | --- | --- | --- |
| full_period | 217 | 141.542 | 12.475 | 18.2645 | 0.078341 | 0.56682 | FRAGILE_CROWDING:0.5668|HEALTHY_EXPANSION:0.0783|NEUTRAL_PARTICIPATION:0.3548 |
| anchored_oos | 12 | -4.53293 | -1.24008 | -0.778714 | 0 | 0.833333 | FRAGILE_CROWDING:0.8333|NEUTRAL_PARTICIPATION:0.1667 |
| 2025-12 | 2 | -1.21381 | -0.084966 | -0.084966 | 0 | 1 | FRAGILE_CROWDING:1.0 |
| 2026-01 | 5 | -2.71892 | -0.982636 | -0.389362 | 0 | 0.8 | FRAGILE_CROWDING:0.8|NEUTRAL_PARTICIPATION:0.2 |
| semis_bucket | 81 | 54.3496 | 3.80447 | 5.80051 | 0.024691 | 0.654321 | FRAGILE_CROWDING:0.6543|HEALTHY_EXPANSION:0.0247|NEUTRAL_PARTICIPATION:0.321 |
| non_semis_bucket | 136 | 87.1929 | 8.67053 | 12.464 | 0.110294 | 0.514706 | FRAGILE_CROWDING:0.5147|HEALTHY_EXPANSION:0.1103|NEUTRAL_PARTICIPATION:0.375 |

## Add Behavior by Label
| participation_quality_label | policy_name | trade_count | ADD_ALLOWED | PROBE_ONLY | BLOCK |
| --- | --- | --- | --- | --- | --- |
| HEALTHY_EXPANSION | old_shadow_policy | 17 | 10 | 7 | 0 |
| HEALTHY_EXPANSION | quality_aware_shadow_policy | 17 | 10 | 7 | 0 |
| NEUTRAL_PARTICIPATION | old_shadow_policy | 77 | 8 | 69 | 0 |
| NEUTRAL_PARTICIPATION | quality_aware_shadow_policy | 77 | 8 | 69 | 0 |
| FRAGILE_CROWDING | old_shadow_policy | 123 | 1 | 122 | 0 |
| FRAGILE_CROWDING | quality_aware_shadow_policy | 123 | 0 | 123 | 0 |

## Shadow Policy Comparison
| policy_name | net_pnl_r | anchored_oos_net_pnl_r | trade_count | monetization_retention_ratio |
| --- | --- | --- | --- | --- |
| baseline | 29.5443 | -1.28962 | 217 | 1 |
| old_shadow_policy | -4.89255 | -0.556491 | 217 | -0.1656 |
| quality_aware_shadow_policy | -3.06637 | -0.53014 | 217 | -0.103789 |