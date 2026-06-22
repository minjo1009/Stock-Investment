# Task 363 - Healthy Continuation Add-Relay & Lifecycle Replay Foundation

## Core Answers
1. Where does HEALTHY_EXPANSION add activation fail? healthy_policy
2. Is the classifier too conservative? YES
3. Is staged gate blocking too much? NO
4. Is healthy-aggressive policy actually more aggressive after all gates? NO
5. Does lifecycle grouping suggest row-level proxy is insufficient? NO

## Add Relay Summary
| healthy_row_count | healthy_lifecycle_count | healthy_baseline_pnl_share | dominant_failing_gate | healthy_staged_gate_block_rate | old_shadow_add_count | quality_aware_add_count | healthy_aggressive_add_count | multi_row_lifecycle_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 17 | 17 | 0.007526 | healthy_policy | 0 | 19 | 18 | 3 | 0 |

## HEALTHY_EXPANSION Relay Trace
| trade_id | timestamp | symbol | participation_quality_label | participation_expansion_score | participation_fragility_score | participation_confidence | state_label | continuation_risk_score | factor_budget_allowed | factor_budget_multiplier | exposure_allow_add | staged_gate_stage | staged_add_allowed | healthy_policy_label | final_add_allowed | final_size_multiplier | baseline_realized_R | shadow_realized_R_proxy | quality_aware_realized_R_proxy | healthy_aggressive_realized_R_proxy | final_add_relay_outcome | final_add_relay_block_stage | first_blocking_reason | all_blocking_reasons |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMD|2021-07-28|2021-07-28|94.099998 | 2021-07-28 00:00:00+00:00 | AMD | HEALTHY_EXPANSION | 0.579976 | 0.434181 | 1 | DISLOCATION | 0.93 | True | 1 | False | stage_1_probe | False | KEEP_SUPPRESSED | False | 0.07 | 2.06063 | 0.144244 | 0.72122 | 0.144244 | probe_only | exposure_add_gate | state_label=DISLOCATION | state_label=DISLOCATION|exposure_allow_add_false|staged_gate_stage=stage_1_probe|healthy_policy_label=KEEP_SUPPRESSED |
| AAPL|2021-08-16|2021-08-16|148.039993 | 2021-08-16 00:00:00+00:00 | AAPL | HEALTHY_EXPANSION | 0.587636 | 0.440831 | 1 | NORMAL | 0.2 | True | 1 | True | stage_2_add | True | KEEP_SUPPRESSED | False | 1 | -0.889318 | -0.889318 | -0.889318 | -0.889318 | probe_only | healthy_policy | healthy_policy_label=KEEP_SUPPRESSED | healthy_policy_label=KEEP_SUPPRESSED |
| META|2021-08-30|2021-08-30|373.739990 | 2021-08-30 00:00:00+00:00 | META | HEALTHY_EXPANSION | 0.598293 | 0.444317 | 1 | DISLOCATION | 0.9 | True | 1 | False | stage_1_probe | False | KEEP_SUPPRESSED | False | 0.07 | -0.50178 | -0.0351246 | -0.175623 | -0.0351246 | probe_only | exposure_add_gate | state_label=DISLOCATION | state_label=DISLOCATION|exposure_allow_add_false|staged_gate_stage=stage_1_probe|healthy_policy_label=KEEP_SUPPRESSED |
| AAPL|2021-08-31|2021-08-31|150.860001 | 2021-08-31 00:00:00+00:00 | AAPL | HEALTHY_EXPANSION | 0.622028 | 0.36727 | 1 | DISLOCATION | 0.9 | True | 1 | False | stage_1_probe | False | KEEP_SUPPRESSED | False | 0.07 | -0.609234 | -0.0426464 | -0.213232 | -0.0426464 | probe_only | exposure_add_gate | state_label=DISLOCATION | state_label=DISLOCATION|exposure_allow_add_false|staged_gate_stage=stage_1_probe|healthy_policy_label=KEEP_SUPPRESSED |
| AAPL|2021-11-18|2021-11-18|155.000000 | 2021-11-18 00:00:00+00:00 | AAPL | HEALTHY_EXPANSION | 0.661095 | 0.378514 | 1 | ELEVATED | 0.45 | True | 1 | True | stage_2_add | True | NO_CHANGE | True | 0.75 | 4.70149 | 3.52612 | 3.52612 | 3.52612 | add_relay_pass |  |  |  |
| META|2022-07-22|2022-07-22|172.720001 | 2022-07-22 00:00:00+00:00 | META | HEALTHY_EXPANSION | 0.550748 | 0.398393 | 1 | NORMAL | 0.2 | True | 1 | True | stage_2_add | True | KEEP_SUPPRESSED | False | 1 | -1.006 | -1.006 | -1.006 | -1.006 | probe_only | healthy_policy | healthy_policy_label=KEEP_SUPPRESSED | healthy_policy_label=KEEP_SUPPRESSED |
| COST|2022-08-16|2022-08-16|551.039978 | 2022-08-16 00:00:00+00:00 | COST | HEALTHY_EXPANSION | 0.54886 | 0.419239 | 1 | NORMAL | 0.2 | True | 1 | True | stage_2_add | True | KEEP_SUPPRESSED | False | 1 | -1.01313 | -1.01313 | -1.01313 | -1.01313 | probe_only | healthy_policy | healthy_policy_label=KEEP_SUPPRESSED | healthy_policy_label=KEEP_SUPPRESSED |
| COST|2023-05-26|2023-05-26|506.029999 | 2023-05-26 00:00:00+00:00 | COST | HEALTHY_EXPANSION | 0.695863 | 0.365314 | 1 | CROWDED | 0.67 | True | 1 | False | stage_2_add | True | NO_CHANGE | True | 0.4 | 0.715454 | 0.286182 | 0.500818 | 0.286182 | probe_only | exposure_add_gate | exposure_allow_add_false | exposure_allow_add_false |
| GOOGL|2023-07-13|2023-07-13|122.610001 | 2023-07-13 00:00:00+00:00 | GOOGL | HEALTHY_EXPANSION | 0.58064 | 0.461263 | 1 | DISLOCATION | 0.9 | True | 1 | False | stage_1_probe | False | KEEP_SUPPRESSED | False | 0.07 | 1.17048 | 0.0819333 | 0.409667 | 0.0819333 | probe_only | exposure_add_gate | state_label=DISLOCATION | state_label=DISLOCATION|exposure_allow_add_false|staged_gate_stage=stage_1_probe|healthy_policy_label=KEEP_SUPPRESSED |
| NFLX|2023-07-14|2023-07-14|45.167000 | 2023-07-14 00:00:00+00:00 | NFLX | HEALTHY_EXPANSION | 0.618111 | 0.427358 | 1 | DISLOCATION | 0.9 | True | 1 | False | stage_1_probe | False | KEEP_SUPPRESSED | False | 0.07 | -0.619776 | -0.0433843 | -0.216922 | -0.0433843 | probe_only | exposure_add_gate | state_label=DISLOCATION | state_label=DISLOCATION|exposure_allow_add_false|staged_gate_stage=stage_1_probe|healthy_policy_label=KEEP_SUPPRESSED |
| MSFT|2023-07-18|2023-07-18|351.429993 | 2023-07-18 00:00:00+00:00 | MSFT | HEALTHY_EXPANSION | 0.515033 | 0.427357 | 1 | NORMAL | 0.2 | True | 1 | True | stage_2_add | True | KEEP_SUPPRESSED | False | 1 | -0.636917 | -0.636917 | -0.636917 | -0.636917 | probe_only | healthy_policy | healthy_policy_label=KEEP_SUPPRESSED | healthy_policy_label=KEEP_SUPPRESSED |
| GOOGL|2024-06-21|2024-06-21|180.410004 | 2024-06-21 00:00:00+00:00 | GOOGL | HEALTHY_EXPANSION | 0.53088 | 0.429262 | 1 | NORMAL | 0.2 | True | 1 | True | stage_2_add | True | KEEP_SUPPRESSED | False | 1 | 0.150551 | 0.150551 | 0.150551 | 0.150551 | probe_only | healthy_policy | healthy_policy_label=KEEP_SUPPRESSED | healthy_policy_label=KEEP_SUPPRESSED |
| QCOM|2024-10-14|2024-10-14|172.800003 | 2024-10-14 00:00:00+00:00 | QCOM | HEALTHY_EXPANSION | 0.568321 | 0.390287 | 1 | DISLOCATION | 0.93 | True | 1 | False | stage_1_probe | False | KEEP_SUPPRESSED | False | 0.07 | -1.01182 | -0.0708272 | -0.354136 | -0.0708272 | probe_only | exposure_add_gate | state_label=DISLOCATION | state_label=DISLOCATION|exposure_allow_add_false|staged_gate_stage=stage_1_probe|healthy_policy_label=KEEP_SUPPRESSED |
| GOOGL|2025-01-31|2025-01-31|202.289993 | 2025-01-31 00:00:00+00:00 | GOOGL | HEALTHY_EXPANSION | 0.556569 | 0.465273 | 1 | DISLOCATION | 0.9 | True | 1 | False | stage_1_probe | False | KEEP_SUPPRESSED | False | 0.07 | -1.18541 | -0.0829786 | -0.414893 | -0.0829786 | probe_only | exposure_add_gate | state_label=DISLOCATION | state_label=DISLOCATION|exposure_allow_add_false|staged_gate_stage=stage_1_probe|healthy_policy_label=KEEP_SUPPRESSED |
| GOOGL|2025-05-21|2025-05-21|169.350006 | 2025-05-21 00:00:00+00:00 | GOOGL | HEALTHY_EXPANSION | 0.526574 | 0.41674 | 1 | NORMAL | 0.2 | True | 1 | True | stage_2_add | True | KEEP_SUPPRESSED | False | 1 | -0.320619 | -0.320619 | -0.320619 | -0.320619 | probe_only | healthy_policy | healthy_policy_label=KEEP_SUPPRESSED | healthy_policy_label=KEEP_SUPPRESSED |
| COST|2025-05-30|2025-05-30|1039.469971 | 2025-05-30 00:00:00+00:00 | COST | HEALTHY_EXPANSION | 0.690304 | 0.284387 | 1 | CROWDED | 0.67 | True | 1 | False | stage_2_add | True | NO_CHANGE | True | 0.4 | -1.01969 | -0.407875 | -0.713782 | -0.407875 | probe_only | exposure_add_gate | exposure_allow_add_false | exposure_allow_add_false |
| AMZN|2025-06-05|2025-06-05|208.949997 | 2025-06-05 00:00:00+00:00 | AMZN | HEALTHY_EXPANSION | 0.570295 | 0.382684 | 1 | NORMAL | 0.2 | True | 1 | True | stage_2_add | True | KEEP_SUPPRESSED | False | 1 | 1.08038 | 1.08038 | 1.08038 | 1.08038 | probe_only | healthy_policy | healthy_policy_label=KEEP_SUPPRESSED | healthy_policy_label=KEEP_SUPPRESSED |

## Gate Drop-Off Summary
| quality_label | gate_name | stage_name | input_count | pass_count | block_count | pass_rate |
| --- | --- | --- | --- | --- | --- | --- |
| FRAGILE_CROWDING | participation_quality | participation_quality | 123 | 0 | 123 | 0 |
| FRAGILE_CROWDING | state_gate | state_gate | 0 | 0 | 0 | 0 |
| FRAGILE_CROWDING | factor_budget | factor_budget | 0 | 0 | 0 | 0 |
| FRAGILE_CROWDING | exposure_gate | exposure_gate | 0 | 0 | 0 | 0 |
| FRAGILE_CROWDING | staged_gate | staged_gate | 0 | 0 | 0 | 0 |
| FRAGILE_CROWDING | healthy_policy | healthy_aggressive_gate | 0 | 0 | 0 | 0 |
| HEALTHY_EXPANSION | participation_quality | participation_quality | 17 | 17 | 0 | 1 |
| HEALTHY_EXPANSION | state_gate | state_gate | 17 | 10 | 7 | 0.588235 |
| HEALTHY_EXPANSION | factor_budget | factor_budget | 10 | 10 | 0 | 1 |
| HEALTHY_EXPANSION | exposure_gate | exposure_gate | 10 | 8 | 2 | 0.8 |
| HEALTHY_EXPANSION | staged_gate | staged_gate | 8 | 8 | 0 | 1 |
| HEALTHY_EXPANSION | healthy_policy | healthy_aggressive_gate | 8 | 1 | 7 | 0.125 |
| NEUTRAL_PARTICIPATION | participation_quality | participation_quality | 77 | 0 | 77 | 0 |
| NEUTRAL_PARTICIPATION | state_gate | state_gate | 0 | 0 | 0 | 0 |
| NEUTRAL_PARTICIPATION | factor_budget | factor_budget | 0 | 0 | 0 | 0 |
| NEUTRAL_PARTICIPATION | exposure_gate | exposure_gate | 0 | 0 | 0 | 0 |
| NEUTRAL_PARTICIPATION | staged_gate | staged_gate | 0 | 0 | 0 | 0 |
| NEUTRAL_PARTICIPATION | healthy_policy | healthy_aggressive_gate | 0 | 0 | 0 | 0 |

## Blocking Reasons
| quality_label | gate_name | blocking_reason | block_count | relay_stage | reason | reason_count | trade_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FRAGILE_CROWDING | exposure_gate | exposure_allow_add_false | 122 | exposure_gate | exposure_allow_add_false | 122 | 122 |
| FRAGILE_CROWDING | final_block_stage | exposure_add_gate | 122 | final_block_stage | exposure_add_gate | 122 | 122 |
| FRAGILE_CROWDING | final_block_stage | healthy_policy | 1 | final_block_stage | healthy_policy | 1 | 1 |
| FRAGILE_CROWDING | healthy_aggressive_policy | dislocation_never_relaxes | 121 | healthy_aggressive_policy | dislocation_never_relaxes | 121 | 121 |
| FRAGILE_CROWDING | healthy_aggressive_policy | fragile_crowding_never_relaxes | 2 | healthy_aggressive_policy | fragile_crowding_never_relaxes | 2 | 2 |
| FRAGILE_CROWDING | healthy_policy | healthy_policy_label=KEEP_SUPPRESSED | 123 | healthy_policy | healthy_policy_label=KEEP_SUPPRESSED | 123 | 123 |
| FRAGILE_CROWDING | participation_quality | continuation_persistence_support | 123 | participation_quality | continuation_persistence_support | 123 | 123 |
| FRAGILE_CROWDING | participation_quality | quality_label=FRAGILE_CROWDING | 123 | participation_quality | quality_label=FRAGILE_CROWDING | 123 | 123 |
| FRAGILE_CROWDING | participation_quality | high_factor_concentration | 121 | participation_quality | high_factor_concentration | 121 | 121 |
| FRAGILE_CROWDING | participation_quality | late_or_uncertain_participation | 106 | participation_quality | late_or_uncertain_participation | 106 | 106 |
| FRAGILE_CROWDING | participation_quality | same_day_signal_crowding | 66 | participation_quality | same_day_signal_crowding | 66 | 66 |
| FRAGILE_CROWDING | participation_quality | strong_dip_absorption | 8 | participation_quality | strong_dip_absorption | 8 | 8 |
| FRAGILE_CROWDING | participation_quality | expansion_minus_fragility=-0.105 | 3 | participation_quality | expansion_minus_fragility=-0.105 | 3 | 3 |
| FRAGILE_CROWDING | participation_quality | expansion_minus_fragility=-0.124 | 3 | participation_quality | expansion_minus_fragility=-0.124 | 3 | 3 |
| FRAGILE_CROWDING | participation_quality | expansion_minus_fragility=-0.083 | 2 | participation_quality | expansion_minus_fragility=-0.083 | 2 | 2 |
| FRAGILE_CROWDING | participation_quality | expansion_minus_fragility=-0.089 | 2 | participation_quality | expansion_minus_fragility=-0.089 | 2 | 2 |
| FRAGILE_CROWDING | participation_quality | expansion_minus_fragility=-0.125 | 2 | participation_quality | expansion_minus_fragility=-0.125 | 2 | 2 |
| FRAGILE_CROWDING | participation_quality | expansion_minus_fragility=-0.126 | 2 | participation_quality | expansion_minus_fragility=-0.126 | 2 | 2 |
| FRAGILE_CROWDING | participation_quality | expansion_minus_fragility=-0.133 | 2 | participation_quality | expansion_minus_fragility=-0.133 | 2 | 2 |
| FRAGILE_CROWDING | participation_quality | expansion_minus_fragility=-0.176 | 2 | participation_quality | expansion_minus_fragility=-0.176 | 2 | 2 |
| FRAGILE_CROWDING | participation_quality | expansion_minus_fragility=-0.179 | 2 | participation_quality | expansion_minus_fragility=-0.179 | 2 | 2 |
| FRAGILE_CROWDING | participation_quality | expansion_minus_fragility=-0.189 | 2 | participation_quality | expansion_minus_fragility=-0.189 | 2 | 2 |
| FRAGILE_CROWDING | participation_quality | expansion_minus_fragility=-0.190 | 2 | participation_quality | expansion_minus_fragility=-0.190 | 2 | 2 |
| FRAGILE_CROWDING | participation_quality | expansion_minus_fragility=-0.237 | 2 | participation_quality | expansion_minus_fragility=-0.237 | 2 | 2 |
| FRAGILE_CROWDING | participation_quality | expansion_minus_fragility=-0.342 | 2 | participation_quality | expansion_minus_fragility=-0.342 | 2 | 2 |

## Lifecycle Quality Summary
| lifecycle_quality_type | lifecycle_count | avg_row_count | baseline_pnl_r_sum | old_shadow_pnl_proxy_sum | quality_aware_pnl_proxy_sum | healthy_aggressive_pnl_proxy_sum | avg_add_allowed_count_old_shadow | avg_add_allowed_count_quality_aware | avg_add_allowed_count_healthy_aggressive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fragile | 123 | 1 | 94.5851 | 5.69817 | 6.42233 | 5.69817 | 0.00813 | 0 | 0 |
| healthy | 17 | 1 | 1.06529 | 0.720587 | 0.434181 | 0.720587 | 0.588235 | 0.588235 | 0.176471 |
| neutral_only | 77 | 1 | 45.8921 | 6.05624 | 11.408 | 6.38619 | 0.103896 | 0.103896 | 0 |