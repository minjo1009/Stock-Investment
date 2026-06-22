# Task668 Regime Theme Playbook

## Decision Summary

- Verdict: `REGIME_THEME_PLAYBOOK_TESTED_NO_PROMOTION_CANDIDATE`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Baseline: `$7639.62`, MDD `-23.76%`.
- Best candidate: `active_relation_cap3_reference` = `$10887.47`, MDD `-30.52%`.
- Promotion candidates: `0`.

## Quant Expert Report

Task668 adds market state, theme leadership/rotation state, company catalyst quality, price acceptance, and relation state into a playbook layer. It preserves Task639 entry timing and exits.

### Candidate Grid

| candidate_name | split_name | candidate_type | initial_capital_usd | source_trade_count | accepted_trade_count | avg_size_multiplier | final_capital_usd | capital_return_pct | max_drawdown_pct | entry_reduce_failure_rate | qqq_final_capital_usd | beats_qqq_flag | diagnostic_only_flag | return_tuned_flag | fixed_hold_or_timing_override_flag | label_used_in_assignment_flag | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| active_relation_cap3_reference | all | reference | 1000.0 | 1621 | 51 | 1.0 | 10887.474713480713 | 988.7474713480714 | -30.524857842425657 | 0.3333333333333333 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| relation_priority_playbook_lite_sizing | all | predeclared_playbook_sizing | 1000.0 | 1621 | 51 | 0.9323529411764705 | 10183.615927393126 | 918.3615927393125 | -28.61213359654865 | 0.3333333333333333 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| baseline_task639 | all | baseline | 1000.0 | 1621 | 54 | 1.0 | 7639.620310821465 | 663.9620310821465 | -23.755747663170702 | 0.35185185185185186 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| playbook_priority_only | all | predeclared_playbook_priority | 1000.0 | 1621 | 51 | 1.0 | 7585.473449655701 | 658.5473449655701 | -27.39107520958347 | 0.37254901960784315 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| playbook_priority_lite_sizing | all | predeclared_playbook_sizing | 1000.0 | 1621 | 51 | 0.9352941176470588 | 7162.954375227895 | 616.2954375227895 | -25.473908307011584 | 0.37254901960784315 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| relation_priority_block_research_only | all | predeclared_playbook_filter | 1000.0 | 1621 | 50 | 1.0 | 6003.618767530641 | 500.3618767530641 | -36.49683272433539 | 0.34 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| playbook_dynamic_cap | all | predeclared_playbook_cap | 1000.0 | 1621 | 46 | 1.0 | 5173.940688581928 | 417.39406885819284 | -18.758042531894326 | 0.3695652173913043 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| playbook_contextual_sizing | all | predeclared_playbook_sizing | 1000.0 | 1621 | 51 | 0.7834313725490196 | 4516.131131173615 | 351.61311311736154 | -20.894240403450148 | 0.37254901960784315 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| playbook_block_research_only | all | predeclared_playbook_filter | 1000.0 | 1621 | 42 | 0.8561904761904762 | 3570.132743535869 | 257.0132743535869 | -22.95937566909021 | 0.38095238095238093 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| playbook_priority_cap_sizing | all | predeclared_playbook_combo | 1000.0 | 1621 | 46 | 0.7789130434782608 | 3106.670420157094 | 210.66704201570943 | -16.39484760752351 | 0.3695652173913043 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| playbook_dynamic_cap | recent_oos | predeclared_playbook_cap | 1000.0 | 332 | 11 | 1.0 | 1667.2809903209381 | 66.72809903209382 | -3.525899653039477 | 0.18181818181818182 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| playbook_priority_cap_sizing | recent_oos | predeclared_playbook_combo | 1000.0 | 332 | 11 | 0.875 | 1581.8359801820704 | 58.18359801820705 | -2.9117736523479376 | 0.18181818181818182 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| active_relation_cap3_reference | recent_oos | reference | 1000.0 | 332 | 10 | 1.0 | 1541.4394915288256 | 54.14394915288256 | -1.0957772237519925 | 0.2 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| relation_priority_playbook_lite_sizing | recent_oos | predeclared_playbook_sizing | 1000.0 | 332 | 10 | 1.0 | 1541.4394915288256 | 54.14394915288256 | -1.0957772237519925 | 0.2 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| relation_priority_block_research_only | recent_oos | predeclared_playbook_filter | 1000.0 | 332 | 10 | 1.0 | 1541.4394915288256 | 54.14394915288256 | -1.0957772237519925 | 0.2 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| playbook_block_research_only | recent_oos | predeclared_playbook_filter | 1000.0 | 332 | 11 | 0.9818181818181819 | 1535.8995887310816 | 53.58995887310816 | -2.9117736523479376 | 0.2727272727272727 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| baseline_task639 | recent_oos | baseline | 1000.0 | 332 | 10 | 1.0 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.1 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| playbook_priority_only | recent_oos | predeclared_playbook_priority | 1000.0 | 332 | 11 | 1.0 | 1489.3083455052943 | 48.930834550529426 | -4.8618878385964575 | 0.36363636363636365 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| playbook_priority_lite_sizing | recent_oos | predeclared_playbook_sizing | 1000.0 | 332 | 11 | 0.9727272727272727 | 1466.4856373271239 | 46.648563732712375 | -4.8618878385964575 | 0.36363636363636365 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| playbook_contextual_sizing | recent_oos | predeclared_playbook_sizing | 1000.0 | 332 | 11 | 0.9477272727272728 | 1445.5648214971343 | 44.55648214971344 | -4.8618878385964575 | 0.36363636363636365 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |

### Playbook Performance

| candidate_name | split_scope | playbook_id | trade_count | avg_return_pct | win_rate | entry_reduce_failure_rate | avg_size_multiplier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| active_relation_cap3_reference | all | normal_participation | 20 | 23.63617411227888 | 0.65 | 0.3 | 1.0 |
| active_relation_cap3_reference | all | confirmation_required | 12 | 67.24337833470747 | 0.75 | 0.25 | 1.0 |
| active_relation_cap3_reference | all | rotation_selective | 7 | 16.283858578058958 | 0.5714285714285714 | 0.42857142857142855 | 1.0 |
| active_relation_cap3_reference | all | defensive_research_only | 5 | 2.153745820710992 | 0.4 | 0.6 | 1.0 |
| active_relation_cap3_reference | all | research_only_sparse | 5 | 7.3372083060575255 | 0.6 | 0.4 | 1.0 |
| active_relation_cap3_reference | all | narrow_leader_selective | 2 | 148.81295552164278 | 1.0 | 0.0 | 1.0 |
| baseline_task639 | all | normal_participation | 21 | 17.569383995133435 | 0.5714285714285714 | 0.38095238095238093 | 1.0 |
| baseline_task639 | all | rotation_selective | 11 | 14.892796604014602 | 0.7272727272727273 | 0.2727272727272727 | 1.0 |
| baseline_task639 | all | research_only_sparse | 8 | 5.29342894510292 | 0.5 | 0.5 | 1.0 |
| baseline_task639 | all | confirmation_required | 7 | 69.41281562374994 | 0.7142857142857143 | 0.2857142857142857 | 1.0 |
| baseline_task639 | all | defensive_research_only | 5 | 13.758864407768739 | 0.6 | 0.4 | 1.0 |
| baseline_task639 | all | narrow_leader_selective | 2 | 148.81295552164278 | 1.0 | 0.0 | 1.0 |
| playbook_block_research_only | all | normal_participation | 21 | 19.603922525836005 | 0.6666666666666666 | 0.3333333333333333 | 0.8661904761904763 |
| playbook_block_research_only | all | rotation_selective | 12 | 9.07506144114358 | 0.3333333333333333 | 0.5833333333333334 | 1.0 |
| playbook_block_research_only | all | narrow_leader_selective | 5 | 56.73277602571821 | 0.8 | 0.2 | 0.5640000000000001 |
| playbook_block_research_only | all | confirmation_required | 3 | 80.88934892222036 | 0.6666666666666666 | 0.3333333333333333 | 0.65 |
| playbook_block_research_only | all | aggressive_leadership | 1 | 20.95612055963608 | 1.0 | 0.0 | 1.0 |
| playbook_contextual_sizing | all | normal_participation | 20 | 24.874540821881933 | 0.7 | 0.2 | 0.865 |
| playbook_contextual_sizing | all | rotation_selective | 15 | 3.876679980346678 | 0.4 | 0.6 | 1.0 |
| playbook_contextual_sizing | all | research_only_sparse | 6 | 5.297120989789821 | 0.5 | 0.5 | 0.40833333333333327 |

### Transition Matrix

| market_state | theme_state | playbook_id | candidate_count |
| --- | --- | --- | --- |
| mixed_rotation_tape | neutral_participation | normal_participation | 352 |
| mixed_rotation_tape | leadership_fading | confirmation_required | 158 |
| broad_risk_on | neutral_participation | normal_participation | 156 |
| mixed_rotation_tape | re_acceleration | rotation_selective | 141 |
| broad_risk_off | neutral_participation | normal_participation | 119 |
| mixed_rotation_tape | re_acceleration | normal_participation | 71 |
| mixed_rotation_tape | leadership_expanding | rotation_selective | 65 |
| broad_risk_on | leadership_fading | confirmation_required | 62 |
| broad_risk_off | leadership_fading | defensive_research_only | 59 |
| mixed_rotation_tape | leadership_expanding | normal_participation | 50 |
| mixed_rotation_tape | neutral_participation | research_only_sparse | 42 |
| broad_risk_off | leadership_fading | confirmation_required | 37 |
| mixed_rotation_tape | re_acceleration | research_only_sparse | 29 |
| mixed_rotation_tape | leadership_expanding | research_only_sparse | 25 |
| broad_risk_off | leadership_fading | research_only_sparse | 24 |
| broad_risk_on | re_acceleration | rotation_selective | 23 |
| mixed_rotation_tape | defensive_rotation | rotation_selective | 22 |
| broad_risk_on | re_acceleration | aggressive_leadership | 21 |
| mixed_rotation_tape | defensive_rotation | normal_participation | 16 |
| broad_risk_off | re_acceleration | normal_participation | 15 |

### MDD Interval Audit

| candidate_name | audit_group | group_value | active_trade_count | avg_return_costed_pct | avg_size_multiplier |
| --- | --- | --- | --- | --- | --- |
| active_relation_cap3_reference | mechanism_relation_state | mechanism_reinforcing_company_positive | 5 | -6.123643082981395 | 1.0 |
| active_relation_cap3_reference | mechanism_relation_state | company_positive_needs_confirmation | 3 | -9.922034893694581 | 1.0 |
| active_relation_cap3_reference | mechanism_relation_state | mechanism_offsetting_company_positive | 3 | 2.5736983732513985 | 1.0 |
| active_relation_cap3_reference | mechanism_relation_state | company_quality_price_confirmed | 2 | 36.87072850836575 | 1.0 |
| active_relation_cap3_reference | mechanism_relation_state | sparse_mechanism_cell | 2 | 6.734318379962153 | 1.0 |
| active_relation_cap3_reference | playbook_id | rotation_selective | 5 | 11.64069469339794 | 1.0 |
| active_relation_cap3_reference | playbook_id | normal_participation | 4 | -19.700507478601057 | 1.0 |
| active_relation_cap3_reference | playbook_id | confirmation_required | 2 | 30.69326664723683 | 1.0 |
| active_relation_cap3_reference | playbook_id | defensive_research_only | 2 | -9.854872403282071 | 1.0 |
| active_relation_cap3_reference | playbook_id | research_only_sparse | 2 | 6.734318379962153 | 1.0 |
| active_relation_cap3_reference | theme_id | data_devops_software | 4 | -6.075771991968086 | 1.0 |
| active_relation_cap3_reference | theme_id | power_grid_electrification | 4 | 14.161575167370454 | 1.0 |
| active_relation_cap3_reference | theme_id | biotech_glp1_healthcare | 3 | -9.873846868298243 | 1.0 |
| active_relation_cap3_reference | theme_id | cybersecurity | 3 | -17.352196047024556 | 1.0 |
| active_relation_cap3_reference | theme_id | aerospace_defense_space | 1 | 83.88178484477822 | 1.0 |
| active_relation_cap3_reference | theme_state | neutral_participation | 5 | -11.055406655992064 | 1.0 |
| active_relation_cap3_reference | theme_state | leadership_fading | 4 | 10.41919712197738 | 1.0 |
| active_relation_cap3_reference | theme_state | re_acceleration | 4 | 17.085950323759103 | 1.0 |
| active_relation_cap3_reference | theme_state | defensive_rotation | 2 | -10.098343851283161 | 1.0 |
| baseline_task639 | mechanism_relation_state | company_positive_needs_confirmation | 5 | -7.360368966944139 | 1.0 |

## No-Background Decision-Maker Report

이번 작업은 장 좋음/나쁨만 보는 게 아니라 돈이 어느 테마로 이동하는지까지 넣은 playbook 테스트입니다.

테마가 진짜 주도 중인지, 좁게 오른 것인지, 약해지는 중인지, 방어성 이동인지 나눴습니다.

수익과 낙폭과 OOS가 모두 좋아져야 승격입니다. 아직 승격 후보는 없습니다.

## Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| no_fixed_hold_or_timing_override | 1 | violations=0 | preserve Task639 timing and exits |
| playbook_panel_built | 1 | accepted_rows=737 | playbook assigned to accepted trades |
| capacity_decision_panel_built | 1 | rows=26080 | accepted and rejected decisions logged |
| playbook_performance_built | 1 | rows=134 | performance by playbook and split |
| transition_matrix_built | 1 | rows=45 | market/theme/playbook transition matrix |
| mdd_audit_built | 1 | rows=197 | MDD interval audit |
| no_return_tuned_promotion | 1 | return_tuned_promoted=0 | no return-tuned candidate can promote |
| promotion_candidate_found | 0 | promotion_candidates=0 | return drawdown validation recent OOS all pass |
| strategy_accepted | 0 | research diagnostic only | accepted gates and live readiness |

## Artifact Manifest

- `task668_candidate_specs.csv`
- `task668_playbook_panel.csv`
- `task668_candidate_grid.csv`
- `task668_accepted_trades.csv`
- `task668_capacity_decision_panel.csv`
- `task668_equity_curve.csv`
- `task668_playbook_performance.csv`
- `task668_transition_matrix.csv`
- `task668_mdd_windows.csv`
- `task668_mdd_interval_audit.csv`
- `task668_promotion_report.csv`
- `task668_promotion_blocker_report.md`
- `task_668_gpt_review_packet.md`
- `task_668_gpt_review_response.md`
- `task_668_decision.csv`
- `task_668_pass_fail_matrix.csv`
- `artifact_manifest.csv`
