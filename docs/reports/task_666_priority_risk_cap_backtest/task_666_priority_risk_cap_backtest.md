# Task666 Priority Risk Cap Backtest

## Decision Summary

- Verdict: `PRIORITY_RISK_CAP_TESTED_NO_PROMOTION_CANDIDATE`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Baseline: `$7639.62`, MDD `-23.76%`.
- Best candidate: `diagnostic_block_mdd_bad_added_themes` = `$11233.49`, MDD `-31.70%`.
- Promotion candidates: `0`.

## Quant Expert Report

Task666 tests non-return-tuned risk caps on top of relation priority. It does not change entry timing, exits, fixed holds, or sizing.

### Data Source And Source Readiness

Input is the Task661 mechanism state panel rebuilt from Task659. No new source is introduced.

### Exact Join Keys

`lifecycle_id`, `entry_ts`, `simulated_exit_ts`, and theme/relation state fields.

### Leakage Audit

Promotion-eligible caps are predeclared structural caps. The MDD-bad-theme block is marked diagnostic and return-tuned.

### Candidate Grid

| candidate_name | split_name | candidate_type | initial_capital_usd | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct | entry_reduce_failure_rate | qqq_final_capital_usd | beats_qqq_flag | diagnostic_only_flag | return_tuned_flag | fixed_hold_or_timing_override_flag | label_used_in_assignment_flag | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| diagnostic_block_mdd_bad_added_themes | all | diagnostic_risk_cap | 1000.0 | 1621 | 49 | 11233.491646100794 | 1023.3491646100795 | -31.695259032189472 | 0.24489795918367346 | 1606.8278306897957 | 1 | 1 | 1 | 0 | 0 | 0 |
| priority_active_relation_cap3 | all | predeclared_risk_cap | 1000.0 | 1621 | 51 | 10887.474713480713 | 988.7474713480714 | -30.524857842425657 | 0.3333333333333333 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| priority_highvol_theme_cap1 | all | predeclared_risk_cap | 1000.0 | 1621 | 54 | 9165.938483945756 | 816.5938483945757 | -31.082547450372854 | 0.2777777777777778 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| priority_no_cap | all | priority_reference | 1000.0 | 1621 | 54 | 8797.725195699932 | 779.7725195699933 | -33.631456638622645 | 0.2962962962962963 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| priority_theme_cap2 | all | predeclared_risk_cap | 1000.0 | 1621 | 54 | 8797.725195699932 | 779.7725195699933 | -33.631456638622645 | 0.2962962962962963 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| priority_relation_cap2 | all | predeclared_risk_cap | 1000.0 | 1621 | 54 | 8797.725195699932 | 779.7725195699933 | -33.631456638622645 | 0.2962962962962963 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| priority_theme_cap2_no_sparse | all | predeclared_risk_cap | 1000.0 | 1621 | 50 | 8439.95138896185 | 743.995138896185 | -32.70106787087056 | 0.28 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| baseline_task639 | all | baseline | 1000.0 | 1621 | 54 | 7639.620310821465 | 663.9620310821465 | -23.755747663170702 | 0.35185185185185186 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| priority_theme_relation_cap1 | all | predeclared_risk_cap | 1000.0 | 1621 | 54 | 7497.408308148235 | 649.7408308148235 | -33.631456638622645 | 0.3148148148148148 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| priority_theme_cap1 | all | predeclared_risk_cap | 1000.0 | 1621 | 53 | 7439.908811670501 | 643.99088116705 | -35.514013367755496 | 0.3018867924528302 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| diagnostic_active_highvol_cap2 | all | diagnostic_risk_cap | 1000.0 | 1621 | 55 | 7423.792469500605 | 642.3792469500605 | -34.04060312231789 | 0.32727272727272727 | 1606.8278306897957 | 1 | 1 | 1 | 0 | 0 | 0 |
| priority_active_theme_cap2 | all | predeclared_risk_cap | 1000.0 | 1621 | 45 | 4496.079554890022 | 349.6079554890023 | -28.63141595542532 | 0.3111111111111111 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| priority_active_theme2_relation3_combo | all | predeclared_risk_cap | 1000.0 | 1621 | 46 | 4257.186203610073 | 325.71862036100725 | -28.63141595542532 | 0.34782608695652173 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| priority_active_theme_relation_cap1 | all | predeclared_risk_cap | 1000.0 | 1621 | 47 | 1972.8284912258266 | 97.28284912258268 | -31.835455734918217 | 0.46808510638297873 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| priority_theme_cap2 | recent_oos | predeclared_risk_cap | 1000.0 | 332 | 12 | 1583.8006563289198 | 58.38006563289198 | -5.084500304136874 | 0.16666666666666666 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| priority_theme_cap2_no_sparse | recent_oos | predeclared_risk_cap | 1000.0 | 332 | 12 | 1583.8006563289198 | 58.38006563289198 | -5.084500304136874 | 0.16666666666666666 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| priority_active_theme_cap2 | recent_oos | predeclared_risk_cap | 1000.0 | 332 | 12 | 1583.8006563289198 | 58.38006563289198 | -5.084500304136874 | 0.16666666666666666 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| priority_active_relation_cap3 | recent_oos | predeclared_risk_cap | 1000.0 | 332 | 10 | 1541.4394915288256 | 54.14394915288256 | -1.0957772237519925 | 0.2 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| priority_no_cap | recent_oos | priority_reference | 1000.0 | 332 | 10 | 1539.817826636232 | 53.98178266362319 | -0.8092509033778783 | 0.1 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| priority_highvol_theme_cap1 | recent_oos | predeclared_risk_cap | 1000.0 | 332 | 10 | 1539.817826636232 | 53.98178266362319 | -0.8092509033778783 | 0.1 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |

### Promotion Report

| candidate_name | all_final_capital_usd | all_max_drawdown_pct | all_accepted_trade_count | all_entry_reduce_failure_rate | all_beats_qqq_flag | recent_oos_final_capital_usd | recent_oos_max_drawdown_pct | recent_oos_accepted_trade_count | recent_oos_entry_reduce_failure_rate | recent_oos_beats_qqq_flag | validation_final_capital_usd | validation_max_drawdown_pct | validation_accepted_trade_count | validation_entry_reduce_failure_rate | validation_beats_qqq_flag | beats_all_task639_flag | all_drawdown_not_worse_flag | validation_improves_task639_flag | recent_oos_improves_task639_flag | validation_drawdown_not_worse_flag | recent_oos_drawdown_not_worse_flag | promotion_allowed_flag | promotion_candidate_flag | failure_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| diagnostic_block_mdd_bad_added_themes | 11233.491646100794 | -31.695259032189472 | 49.0 | 0.24489795918367346 | 1.0 | 1539.817826636232 | -0.8092509033778783 | 10.0 | 0.1 | 1.0 | 1392.2169224441068 | -2.762219447090497 | 12.0 | 0.08333333333333333 | 1.0 | 1 | 0 | 1 | 1 | 1 | 1 | 0 | 0 | diagnostic_or_return_tuned_not_promotion_eligible |
| priority_active_relation_cap3 | 10887.474713480713 | -30.524857842425657 | 51.0 | 0.3333333333333333 | 1.0 | 1541.4394915288256 | -1.0957772237519925 | 10.0 | 0.2 | 1.0 | 1327.5223368015004 | -5.866934869678831 | 13.0 | 0.15384615384615385 | 1.0 | 1 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | full_period_drawdown_worse |
| priority_highvol_theme_cap1 | 9165.938483945756 | -31.082547450372854 | 54.0 | 0.2777777777777778 | 1.0 | 1539.817826636232 | -0.8092509033778783 | 10.0 | 0.1 | 1.0 | 1304.40199798408 | -5.780061968077943 | 13.0 | 0.15384615384615385 | 1.0 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 0 | full_period_drawdown_worse |
| priority_no_cap | 8797.725195699932 | -33.631456638622645 | 54.0 | 0.2962962962962963 | 1.0 | 1539.817826636232 | -0.8092509033778783 | 10.0 | 0.1 | 1.0 | 1304.40199798408 | -5.780061968077943 | 13.0 | 0.15384615384615385 | 1.0 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 0 | full_period_drawdown_worse |
| priority_theme_cap2 | 8797.725195699932 | -33.631456638622645 | 54.0 | 0.2962962962962963 | 1.0 | 1583.8006563289198 | -5.084500304136874 | 12.0 | 0.16666666666666666 | 1.0 | 1288.9560742986164 | -5.780061968077943 | 13.0 | 0.23076923076923078 | 1.0 | 1 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | full_period_drawdown_worse |
| priority_relation_cap2 | 8797.725195699932 | -33.631456638622645 | 54.0 | 0.2962962962962963 | 1.0 | 1496.561278563998 | -3.8879308156665737 | 11.0 | 0.2727272727272727 | 1.0 | 1331.788831908557 | -5.622183082178466 | 13.0 | 0.15384615384615385 | 1.0 | 1 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | full_period_drawdown_worse |
| priority_theme_cap2_no_sparse | 8439.95138896185 | -32.70106787087056 | 50.0 | 0.28 | 1.0 | 1583.8006563289198 | -5.084500304136874 | 12.0 | 0.16666666666666666 | 1.0 | 1288.9560742986164 | -5.780061968077943 | 13.0 | 0.23076923076923078 | 1.0 | 1 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | full_period_drawdown_worse |
| baseline_task639 | 7639.620310821465 | -23.755747663170702 | 54.0 | 0.35185185185185186 | 1.0 | 1531.9029143138666 | -0.811391994497368 | 10.0 | 0.1 | 1.0 | 1069.2312936091898 | -7.363321689343804 | 15.0 | 0.4 | 1.0 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 0 | full_period_return_not_better |
| priority_theme_relation_cap1 | 7497.408308148235 | -33.631456638622645 | 54.0 | 0.3148148148148148 | 1.0 | 1281.431428695114 | -12.046709082519037 | 13.0 | 0.38461538461538464 | 1.0 | 1225.3126161833902 | -6.5293343131868635 | 14.0 | 0.35714285714285715 | 1.0 | 0 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | full_period_return_not_better |
| priority_theme_cap1 | 7439.908811670501 | -35.514013367755496 | 53.0 | 0.3018867924528302 | 1.0 | 1281.431428695114 | -12.046709082519037 | 13.0 | 0.38461538461538464 | 1.0 | 1225.3126161833902 | -6.5293343131868635 | 14.0 | 0.35714285714285715 | 1.0 | 0 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | full_period_return_not_better |
| diagnostic_active_highvol_cap2 | 7423.792469500605 | -34.04060312231789 | 55.0 | 0.32727272727272727 | 1.0 | 1539.817826636232 | -0.8092509033778783 | 10.0 | 0.1 | 1.0 | 1304.40199798408 | -5.780061968077943 | 13.0 | 0.15384615384615385 | 1.0 | 0 | 0 | 1 | 1 | 1 | 1 | 0 | 0 | diagnostic_or_return_tuned_not_promotion_eligible |
| priority_active_theme_cap2 | 4496.079554890022 | -28.63141595542532 | 45.0 | 0.3111111111111111 | 1.0 | 1583.8006563289198 | -5.084500304136874 | 12.0 | 0.16666666666666666 | 1.0 | 1288.9560742986164 | -5.780061968077943 | 13.0 | 0.23076923076923078 | 1.0 | 0 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | full_period_return_not_better |
| priority_active_theme2_relation3_combo | 4257.186203610073 | -28.63141595542532 | 46.0 | 0.34782608695652173 | 1.0 | 1453.9564846024332 | -4.0915344040228785 | 12.0 | 0.25 | 1.0 | 1327.5223368015004 | -5.866934869678831 | 13.0 | 0.15384615384615385 | 1.0 | 0 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | full_period_return_not_better |
| priority_active_theme_relation_cap1 | 1972.8284912258266 | -31.835455734918217 | 47.0 | 0.46808510638297873 | 1.0 | 1256.0557770787684 | -14.206367687008237 | 13.0 | 0.38461538461538464 | 1.0 | 1182.6717778523157 | -5.622183082178466 | 13.0 | 0.23076923076923078 | 1.0 | 0 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | full_period_return_not_better |

### Cap Audit

| candidate_name | split_scope | accepted_count | unique_theme_count | top_theme | top_theme_count | high_vol_theme_count | entry_reduce_failure_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_task639 | all | 54 | 8 | aerospace_defense_space | 16 | 15 | 0.35185185185185186 |
| diagnostic_active_highvol_cap2 | all | 55 | 7 | aerospace_defense_space | 19 | 14 | 0.32727272727272727 |
| diagnostic_block_mdd_bad_added_themes | all | 49 | 4 | aerospace_defense_space | 21 | 0 | 0.24489795918367346 |
| priority_active_relation_cap3 | all | 51 | 9 | aerospace_defense_space | 11 | 19 | 0.3333333333333333 |
| priority_active_theme2_relation3_combo | all | 46 | 9 | aerospace_defense_space | 11 | 16 | 0.34782608695652173 |
| priority_active_theme_cap2 | all | 45 | 7 | aerospace_defense_space | 10 | 18 | 0.3111111111111111 |
| priority_active_theme_relation_cap1 | all | 47 | 9 | power_grid_electrification | 11 | 14 | 0.46808510638297873 |
| priority_highvol_theme_cap1 | all | 54 | 7 | aerospace_defense_space | 16 | 19 | 0.2777777777777778 |
| priority_no_cap | all | 54 | 7 | aerospace_defense_space | 13 | 21 | 0.2962962962962963 |
| priority_relation_cap2 | all | 54 | 7 | aerospace_defense_space | 13 | 21 | 0.2962962962962963 |
| priority_theme_cap1 | all | 53 | 8 | aerospace_defense_space | 14 | 20 | 0.3018867924528302 |
| priority_theme_cap2 | all | 54 | 7 | aerospace_defense_space | 13 | 21 | 0.2962962962962963 |
| priority_theme_cap2_no_sparse | all | 50 | 7 | aerospace_defense_space | 13 | 13 | 0.28 |
| priority_theme_relation_cap1 | all | 54 | 8 | aerospace_defense_space | 14 | 23 | 0.3148148148148148 |
| baseline_task639 | recent_oos | 10 | 4 | ai_semiconductors | 4 | 0 | 0.1 |
| diagnostic_active_highvol_cap2 | recent_oos | 10 | 3 | ai_semiconductors | 5 | 0 | 0.1 |
| diagnostic_block_mdd_bad_added_themes | recent_oos | 10 | 3 | ai_semiconductors | 5 | 0 | 0.1 |
| priority_active_relation_cap3 | recent_oos | 10 | 4 | industrial_automation_robotics | 4 | 0 | 0.2 |
| priority_active_theme2_relation3_combo | recent_oos | 12 | 6 | ai_semiconductors | 4 | 1 | 0.25 |
| priority_active_theme_cap2 | recent_oos | 12 | 8 | industrial_automation_robotics | 3 | 3 | 0.16666666666666666 |

## No-Background Decision-Maker Report

좋은 우선순위는 살리고, 나쁜 slot 교체만 막는 risk cap을 테스트했습니다.

좋은 후보까지 너무 많이 막으면 수익도 같이 죽습니다.

그래서 수익, MDD, validation, recent OOS가 모두 좋아질 때만 승격합니다.

## Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| no_fixed_hold_or_timing_override | 1 | violations=0 | risk caps preserve timing and exit |
| risk_cap_candidates_tested | 1 | candidates=14 | multiple cap candidates |
| displacement_audit_built | 1 | rows=394 | added/removed trade audit exists |
| no_return_tuned_promotion | 1 | return_tuned_promoted=0 | diagnostic return-tuned candidates cannot promote |
| promotion_candidate_found | 0 | promotion_candidates=0 | candidate improves return drawdown validation and recent OOS |
| strategy_accepted | 0 | research diagnostic only | requires accepted strategy gates and live readiness |

## Artifact Manifest

- `priority_risk_cap_specs.csv`
- `priority_risk_cap_candidate_grid.csv`
- `priority_risk_cap_accepted_trades.csv`
- `task666_capacity_allocation_panel.csv`
- `task666_theme_concentration_audit.csv`
- `task666_relation_concentration_audit.csv`
- `task666_displacement_pairs.csv`
- `task666_mdd_contribution_report.csv`
- `task666_promotion_blockers.md`
- `task_666_gpt_review_packet.md`
- `task_666_gpt_review_response.md`
- `priority_risk_cap_audit.csv`
- `priority_risk_cap_promotion_report.csv`
- `task_666_decision.csv`
- `task_666_pass_fail_matrix.csv`
- `artifact_manifest.csv`
