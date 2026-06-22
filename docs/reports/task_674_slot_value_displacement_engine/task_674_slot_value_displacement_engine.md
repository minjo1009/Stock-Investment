# Task674 Slot Value Displacement Engine

## Decision Summary

- Verdict: `SLOT_VALUE_LADDER_TESTED_NO_PROMOTION_YET`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

## Quant Expert Report

This task uses current entry-time data only. It does not use microstructure, future returns, future labels, symbol blacklist, or theme blacklist for assignment.

### Candidate Grid

| candidate_name | candidate_type | split_name | initial_capital_usd | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct | entry_reduce_failure_rate | qqq_final_capital_usd | beats_qqq_flag | diagnostic_only_flag | return_tuned_flag | fixed_hold_or_timing_override_flag | label_used_in_assignment_flag | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| active_relation_cap3_reference | reference | all | 1000.0 | 1621 | 51 | 10887.474713480713 | 988.7474713480714 | -30.524857842425657 | 0.3333333333333333 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| setup_slot_priority_only | task674_slot_value | all | 1000.0 | 1621 | 53 | 8527.512405637917 | 752.7512405637917 | -35.77505324217282 | 0.2830188679245283 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| setup_slot_priority_research_block | task674_slot_value | all | 1000.0 | 1621 | 50 | 8425.98246015405 | 742.5982460154048 | -33.79887595220386 | 0.26 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| baseline_task639 | baseline | all | 1000.0 | 1621 | 54 | 7639.620310821465 | 663.9620310821465 | -23.755747663170702 | 0.35185185185185186 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| capacity_fragile_cap1 | task676_capacity_cap | all | 1000.0 | 1621 | 54 | 5518.5893221805745 | 451.8589322180574 | -34.67330331498538 | 0.35185185185185186 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| capacity_theme_cap2 | task676_capacity_cap | all | 1000.0 | 1621 | 44 | 4406.079458262445 | 340.6079458262445 | -31.23009899533543 | 0.29545454545454547 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| capacity_relation_cap2 | task676_capacity_cap | all | 1000.0 | 1621 | 51 | 4081.1140153771566 | 308.11140153771566 | -32.15323401536726 | 0.3137254901960784 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| action_permission_research_block | task677_action_permission | all | 1000.0 | 1621 | 42 | 3865.930758836104 | 286.59307588361037 | -20.010033696148323 | 0.40476190476190477 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| capacity_driver_cap2 | task676_capacity_cap | all | 1000.0 | 1621 | 48 | 3815.7871418096533 | 281.57871418096533 | -32.42919299164343 | 0.3958333333333333 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| capacity_combined_conservative | task676_capacity_cap | all | 1000.0 | 1621 | 44 | 3571.1836131997165 | 257.11836131997165 | -24.067316403426474 | 0.45454545454545453 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| active_relation_cap3_reference | reference | recent_oos | 1000.0 | 332 | 10 | 1541.4394915288256 | 54.14394915288256 | -1.0957772237519925 | 0.2 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| baseline_task639 | baseline | recent_oos | 1000.0 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.1 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| capacity_relation_cap2 | task676_capacity_cap | recent_oos | 1000.0 | 332 | 11 | 1426.7775769878683 | 42.677757698786834 | -3.525899653039477 | 0.2727272727272727 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| capacity_driver_cap2 | task676_capacity_cap | recent_oos | 1000.0 | 332 | 10 | 1397.1044484126041 | 39.710444841260404 | -1.0751838033332684 | 0.3 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| capacity_combined_conservative | task676_capacity_cap | recent_oos | 1000.0 | 332 | 11 | 1305.6988786097638 | 30.569887860976387 | -4.893914433804126 | 0.36363636363636365 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| setup_slot_priority_only | task674_slot_value | recent_oos | 1000.0 | 332 | 11 | 1293.441503743922 | 29.34415037439222 | -4.0915344040228785 | 0.2727272727272727 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| setup_slot_priority_research_block | task674_slot_value | recent_oos | 1000.0 | 332 | 11 | 1293.441503743922 | 29.34415037439222 | -4.0915344040228785 | 0.2727272727272727 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| capacity_fragile_cap1 | task676_capacity_cap | recent_oos | 1000.0 | 332 | 11 | 1293.441503743922 | 29.34415037439222 | -4.0915344040228785 | 0.2727272727272727 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| action_permission_research_block | task677_action_permission | recent_oos | 1000.0 | 332 | 11 | 1265.886059873446 | 26.588605987344582 | -4.893914433804126 | 0.36363636363636365 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| capacity_theme_cap2 | task676_capacity_cap | recent_oos | 1000.0 | 332 | 11 | 1247.0158727393211 | 24.701587273932123 | -4.971866104900635 | 0.2727272727272727 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| setup_slot_priority_only | task674_slot_value | validation | 1000.0 | 655 | 12 | 1363.9462180806004 | 36.39462180806004 | -2.85996363508797 | 0.16666666666666666 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |
| setup_slot_priority_research_block | task674_slot_value | validation | 1000.0 | 655 | 12 | 1363.9462180806004 | 36.39462180806004 | -2.85996363508797 | 0.16666666666666666 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |
| capacity_theme_cap2 | task676_capacity_cap | validation | 1000.0 | 655 | 12 | 1363.9462180806004 | 36.39462180806004 | -2.85996363508797 | 0.16666666666666666 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |
| capacity_fragile_cap1 | task676_capacity_cap | validation | 1000.0 | 655 | 12 | 1363.9462180806004 | 36.39462180806004 | -2.85996363508797 | 0.16666666666666666 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |
| active_relation_cap3_reference | reference | validation | 1000.0 | 655 | 13 | 1327.5223368015004 | 32.752233680150034 | -5.866934869678831 | 0.15384615384615385 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |
| capacity_relation_cap2 | task676_capacity_cap | validation | 1000.0 | 655 | 13 | 1324.7341007175282 | 32.47341007175282 | -2.75416115525694 | 0.15384615384615385 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |
| capacity_driver_cap2 | task676_capacity_cap | validation | 1000.0 | 655 | 12 | 1293.562523362714 | 29.356252336271417 | -2.85996363508797 | 0.16666666666666666 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |
| action_permission_research_block | task677_action_permission | validation | 1000.0 | 655 | 12 | 1184.2034411944824 | 18.420344119448238 | -2.7210459389163555 | 0.08333333333333333 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |
| capacity_combined_conservative | task676_capacity_cap | validation | 1000.0 | 655 | 12 | 1168.657466690524 | 16.865746669052406 | -2.7563190302042018 | 0.08333333333333333 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |
| baseline_task639 | baseline | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |

### Displacement

| candidate_name | split_name | baseline_accepted_count | candidate_accepted_count | common_accepted_count | added_accepted_count | removed_accepted_count | accepted_set_changed_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| action_permission_research_block | all | 54 | 42 | 10 | 32 | 44 | 1 |
| active_relation_cap3_reference | all | 54 | 51 | 26 | 25 | 28 | 1 |
| baseline_task639 | all | 54 | 54 | 54 | 0 | 0 | 0 |
| capacity_combined_conservative | all | 54 | 44 | 12 | 32 | 42 | 1 |
| capacity_driver_cap2 | all | 54 | 48 | 13 | 35 | 41 | 1 |
| capacity_fragile_cap1 | all | 54 | 54 | 25 | 29 | 29 | 1 |
| capacity_relation_cap2 | all | 54 | 51 | 17 | 34 | 37 | 1 |
| capacity_theme_cap2 | all | 54 | 44 | 13 | 31 | 41 | 1 |
| setup_slot_priority_only | all | 54 | 53 | 24 | 29 | 30 | 1 |
| setup_slot_priority_research_block | all | 54 | 50 | 20 | 30 | 34 | 1 |
| action_permission_research_block | recent_oos | 10 | 11 | 4 | 7 | 6 | 1 |
| active_relation_cap3_reference | recent_oos | 10 | 10 | 7 | 3 | 3 | 1 |
| baseline_task639 | recent_oos | 10 | 10 | 10 | 0 | 0 | 0 |
| capacity_combined_conservative | recent_oos | 10 | 11 | 4 | 7 | 6 | 1 |
| capacity_driver_cap2 | recent_oos | 10 | 10 | 6 | 4 | 4 | 1 |
| capacity_fragile_cap1 | recent_oos | 10 | 11 | 7 | 4 | 3 | 1 |
| capacity_relation_cap2 | recent_oos | 10 | 11 | 5 | 6 | 5 | 1 |
| capacity_theme_cap2 | recent_oos | 10 | 11 | 7 | 4 | 3 | 1 |
| setup_slot_priority_only | recent_oos | 10 | 11 | 7 | 4 | 3 | 1 |
| setup_slot_priority_research_block | recent_oos | 10 | 11 | 7 | 4 | 3 | 1 |
| action_permission_research_block | validation | 15 | 12 | 5 | 7 | 10 | 1 |
| active_relation_cap3_reference | validation | 15 | 13 | 9 | 4 | 6 | 1 |
| baseline_task639 | validation | 15 | 15 | 15 | 0 | 0 | 0 |
| capacity_combined_conservative | validation | 15 | 12 | 5 | 7 | 10 | 1 |
| capacity_driver_cap2 | validation | 15 | 12 | 3 | 9 | 12 | 1 |
| capacity_fragile_cap1 | validation | 15 | 12 | 3 | 9 | 12 | 1 |
| capacity_relation_cap2 | validation | 15 | 13 | 6 | 7 | 9 | 1 |
| capacity_theme_cap2 | validation | 15 | 12 | 3 | 9 | 12 | 1 |
| setup_slot_priority_only | validation | 15 | 12 | 3 | 9 | 12 | 1 |
| setup_slot_priority_research_block | validation | 15 | 12 | 3 | 9 | 12 | 1 |

### Pass Fail

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| candidate_grid_built | 1 | rows=30 | slot ladder candidate grid |
| same_timestamp_ladder_only | 1 | entry/exit/cost unchanged | only ordering changed |
| rank_ladder_not_weighted_score | 1 | predeclared rank columns | no tuned score weights |
| displacement_audit_built | 1 | rows=30 | Task639 displacement audit |
| winner_damage_audit_built | 1 | rows=60 | added removed trade audit |
| strategy_accepted | 0 | research only | Task676 promotion gates required |

## No-Background Decision-Maker Report

이번 작업은 바로 실전 매매로 승격하지 않습니다.

상태를 더 쪼개고, 슬롯 경쟁과 동시 노출을 분리해서 다음 매매 룰 후보가 과최적화인지 확인하는 단계입니다.

## Artifact Manifest

- See `artifact_manifest.csv`.
