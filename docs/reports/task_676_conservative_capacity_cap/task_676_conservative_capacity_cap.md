# Task676 Conservative Capacity Cap

## Decision Summary

- Verdict: `CONSERVATIVE_CAP_TESTED_PROMOTION_GATE_EVALUATED`
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

### Promotion

| candidate_name | all_final_capital_usd | all_max_drawdown_pct | validation_final_capital_usd | validation_max_drawdown_pct | recent_oos_final_capital_usd | recent_oos_max_drawdown_pct | beats_task639_final_flag | mdd_not_worse_than_task639_flag | validation_not_worse_flag | recent_oos_not_worse_flag | promotion_candidate_flag | failure_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| active_relation_cap3_reference | 10887.474713480713 | -30.524857842425657 | 1327.5223368015004 | -5.866934869678831 | 1541.4394915288256 | -1.0957772237519925 | 1 | 0 | 1 | 0 | 0 | mdd_worse_than_task639+recent_oos_not_worse_gate_failed |
| setup_slot_priority_only | 8527.512405637917 | -35.77505324217282 | 1363.9462180806004 | -2.85996363508797 | 1293.441503743922 | -4.0915344040228785 | 1 | 0 | 1 | 0 | 0 | mdd_worse_than_task639+recent_oos_not_worse_gate_failed |
| setup_slot_priority_research_block | 8425.98246015405 | -33.79887595220386 | 1363.9462180806004 | -2.85996363508797 | 1293.441503743922 | -4.0915344040228785 | 1 | 0 | 1 | 0 | 0 | mdd_worse_than_task639+recent_oos_not_worse_gate_failed |
| baseline_task639 | 7639.620310821465 | -23.755747663170702 | 1069.2312936091898 | -7.363321689343804 | 1531.9029143138666 | -0.811391994497368 | 0 | 1 | 1 | 1 | 0 | final_not_above_task639 |
| capacity_fragile_cap1 | 5518.5893221805745 | -34.67330331498538 | 1363.9462180806004 | -2.85996363508797 | 1293.441503743922 | -4.0915344040228785 | 0 | 0 | 1 | 0 | 0 | final_not_above_task639+mdd_worse_than_task639+recent_oos_not_worse_gate_failed |
| capacity_theme_cap2 | 4406.079458262445 | -31.23009899533543 | 1363.9462180806004 | -2.85996363508797 | 1247.0158727393211 | -4.971866104900635 | 0 | 0 | 1 | 0 | 0 | final_not_above_task639+mdd_worse_than_task639+recent_oos_not_worse_gate_failed |
| capacity_relation_cap2 | 4081.1140153771566 | -32.15323401536726 | 1324.7341007175282 | -2.75416115525694 | 1426.7775769878683 | -3.525899653039477 | 0 | 0 | 1 | 0 | 0 | final_not_above_task639+mdd_worse_than_task639+recent_oos_not_worse_gate_failed |
| action_permission_research_block | 3865.930758836104 | -20.010033696148323 | 1184.2034411944824 | -2.7210459389163555 | 1265.886059873446 | -4.893914433804126 | 0 | 1 | 1 | 0 | 0 | final_not_above_task639+recent_oos_not_worse_gate_failed |
| capacity_driver_cap2 | 3815.7871418096533 | -32.42919299164343 | 1293.562523362714 | -2.85996363508797 | 1397.1044484126041 | -1.0751838033332684 | 0 | 0 | 1 | 0 | 0 | final_not_above_task639+mdd_worse_than_task639+recent_oos_not_worse_gate_failed |
| capacity_combined_conservative | 3571.1836131997165 | -24.067316403426474 | 1168.657466690524 | -2.7563190302042018 | 1305.6988786097638 | -4.893914433804126 | 0 | 0 | 1 | 0 | 0 | final_not_above_task639+mdd_worse_than_task639+recent_oos_not_worse_gate_failed |

### Capacity Reasons

| candidate_name | split_name | allocation_reason | candidate_count | accepted_count | blocked_count |
| --- | --- | --- | --- | --- | --- |
| action_permission_research_block | all | accepted | 42 | 42 | 0 |
| action_permission_research_block | all | driver_concentration_cap | 46 | 0 | 46 |
| action_permission_research_block | all | max_positions_full | 1281 | 0 | 1281 |
| action_permission_research_block | all | relation_concentration_cap | 197 | 0 | 197 |
| action_permission_research_block | all | research_only_permission | 33 | 0 | 33 |
| action_permission_research_block | all | theme_concentration_cap | 22 | 0 | 22 |
| active_relation_cap3_reference | all | accepted | 51 | 51 | 0 |
| active_relation_cap3_reference | all | max_positions_full | 1534 | 0 | 1534 |
| active_relation_cap3_reference | all | relation_concentration_cap | 36 | 0 | 36 |
| baseline_task639 | all | accepted | 54 | 54 | 0 |
| baseline_task639 | all | max_positions_full | 1567 | 0 | 1567 |
| capacity_combined_conservative | all | accepted | 44 | 44 | 0 |
| capacity_combined_conservative | all | driver_concentration_cap | 31 | 0 | 31 |
| capacity_combined_conservative | all | max_positions_full | 1416 | 0 | 1416 |
| capacity_combined_conservative | all | relation_concentration_cap | 101 | 0 | 101 |
| capacity_combined_conservative | all | theme_concentration_cap | 29 | 0 | 29 |
| capacity_driver_cap2 | all | accepted | 48 | 48 | 0 |
| capacity_driver_cap2 | all | driver_concentration_cap | 65 | 0 | 65 |
| capacity_driver_cap2 | all | max_positions_full | 1508 | 0 | 1508 |
| capacity_fragile_cap1 | all | accepted | 54 | 54 | 0 |
| capacity_fragile_cap1 | all | fragile_cluster_cap | 2 | 0 | 2 |
| capacity_fragile_cap1 | all | max_positions_full | 1565 | 0 | 1565 |
| capacity_relation_cap2 | all | accepted | 51 | 51 | 0 |
| capacity_relation_cap2 | all | max_positions_full | 1485 | 0 | 1485 |
| capacity_relation_cap2 | all | relation_concentration_cap | 85 | 0 | 85 |
| capacity_theme_cap2 | all | accepted | 44 | 44 | 0 |
| capacity_theme_cap2 | all | max_positions_full | 1534 | 0 | 1534 |
| capacity_theme_cap2 | all | theme_concentration_cap | 43 | 0 | 43 |
| setup_slot_priority_only | all | accepted | 53 | 53 | 0 |
| setup_slot_priority_only | all | max_positions_full | 1568 | 0 | 1568 |
| setup_slot_priority_research_block | all | accepted | 50 | 50 | 0 |
| setup_slot_priority_research_block | all | max_positions_full | 1557 | 0 | 1557 |
| setup_slot_priority_research_block | all | research_only_permission | 14 | 0 | 14 |
| action_permission_research_block | recent_oos | accepted | 11 | 11 | 0 |
| action_permission_research_block | recent_oos | driver_concentration_cap | 21 | 0 | 21 |
| action_permission_research_block | recent_oos | max_positions_full | 151 | 0 | 151 |
| action_permission_research_block | recent_oos | relation_concentration_cap | 132 | 0 | 132 |
| action_permission_research_block | recent_oos | research_only_permission | 16 | 0 | 16 |
| action_permission_research_block | recent_oos | theme_concentration_cap | 1 | 0 | 1 |
| active_relation_cap3_reference | recent_oos | accepted | 10 | 10 | 0 |

### Forbidden

| check_name | violation_count | pass_flag | required_value |
| --- | --- | --- | --- |
| return_used_in_setup_assignment_flag | 0 | 1 | 0 violations |
| label_used_in_setup_assignment_flag | 0 | 1 | 0 violations |
| future_price_used_in_setup_assignment_flag | 0 | 1 | 0 violations |
| proxy_risk_used_as_hard_rule_flag | 0 | 1 | 0 violations |
| slot_value_rank_tuned_flag | 0 | 1 | 0 violations |
| symbol_blacklist_used | 0 | 1 | 0 violations |
| theme_blacklist_used | 0 | 1 | 0 violations |
| fixed_hold_or_timing_override | 0 | 1 | 0 violations |
| return_tuned_candidates | 0 | 1 | 0 violations |

### Pass Fail

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| capacity_backtest_built | 1 | rows=10 | capacity promotion report |
| capacity_reason_audit_built | 1 | rows=93 | capacity reason audit |
| forbidden_inputs_clean | 1 | violations=0 | 0 violations |
| promotion_candidate_found | 0 | promotion_candidates=0 | must beat Task639 final MDD validation recent |
| strategy_accepted | 0 | not accepted | separate acceptance gate |

## No-Background Decision-Maker Report

이번 작업은 바로 실전 매매로 승격하지 않습니다.

상태를 더 쪼개고, 슬롯 경쟁과 동시 노출을 분리해서 다음 매매 룰 후보가 과최적화인지 확인하는 단계입니다.

## Artifact Manifest

- See `artifact_manifest.csv`.
