# Task663 Relation Selection Backtest

## Decision Summary

- Verdict: `RELATION_SELECTION_TESTED_NO_PROMOTION_CANDIDATE`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Baseline: `$7639.62`, max drawdown `-23.76%`.
- Best full-period selection: `predeclared_exclude_sparse_existing_exit` = `$8533.89`, max drawdown `-32.70%`.
- Best candidate improving both OOS splits: `diagnostic_exclude_company_quality_price_confirmed`.
- Promotion candidates: `0`.

## Quant Expert Report

Task663 connects Task661 relation states to trading by selecting or withholding existing Task639 candidates only. It does not add fixed-hold exits, timing overrides, size boosts, or standalone macro entries.

### Data Source And Source Readiness

Input is the Task661 mechanism state panel rebuilt from Task659. No new external data is introduced.

### Exact Join Keys

`lifecycle_id`, `entry_ts`, `timing_mode`, `exit_mode`, and `split_name`.

### Leakage Audit

Returns are evaluation-only. Diagnostic candidates are marked `diagnostic_only_flag=1` and cannot be promoted.

### Candidate Grid

| candidate_name | split_name | candidate_type | initial_capital_usd | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct | entry_reduce_failure_rate | qqq_final_capital_usd | beats_qqq_flag | relation_state_used_for_selection_flag | diagnostic_only_flag | fixed_hold_or_timing_override_flag | label_used_in_assignment_flag | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| predeclared_exclude_sparse_existing_exit | all | predeclared_data_quality_selection | 1000.0 | 1465 | 50 | 8533.889412035187 | 753.3889412035187 | -32.70106787087056 | 0.26 | 1606.8278306897957 | 1 | 1 | 0 | 0 | 0 | 0 |
| baseline_task639_core | all | baseline | 1000.0 | 1621 | 54 | 7639.620310821465 | 663.9620310821465 | -23.755747663170702 | 0.37037037037037035 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| diagnostic_exclude_company_quality_price_confirmed | all | diagnostic_state_selection | 1000.0 | 1221 | 47 | 4961.890187114215 | 396.1890187114215 | -31.809120103640797 | 0.3191489361702128 | 1606.8278306897957 | 1 | 1 | 1 | 0 | 0 | 0 |
| diagnostic_state_positive_ex_quality_confirmed | all | diagnostic_state_selection | 1000.0 | 1065 | 45 | 4145.70551537549 | 314.570551537549 | -29.548644354063423 | 0.28888888888888886 | 1606.8278306897957 | 1 | 1 | 1 | 0 | 0 | 0 |
| predeclared_reinforcing_or_offsetting_existing_exit | all | predeclared_state_selection | 1000.0 | 505 | 42 | 1479.163115648116 | 47.9163115648116 | -37.67596890657304 | 0.47619047619047616 | 1606.8278306897957 | 0 | 1 | 0 | 0 | 0 | 0 |
| predeclared_reinforcing_only_existing_exit | all | predeclared_state_selection | 1000.0 | 463 | 41 | 1230.1512508684639 | 23.01512508684638 | -38.39493558493857 | 0.5121951219512195 | 1606.8278306897957 | 0 | 1 | 0 | 0 | 0 | 0 |
| predeclared_reinforcing_or_offsetting_existing_exit | recent_oos | predeclared_state_selection | 1000.0 | 116 | 11 | 1875.1554533252483 | 87.51554533252485 | -4.320725429884453 | 0.2727272727272727 | 1138.0195487861092 | 1 | 1 | 0 | 0 | 0 | 0 |
| diagnostic_exclude_company_quality_price_confirmed | recent_oos | diagnostic_state_selection | 1000.0 | 254 | 11 | 1875.1554533252483 | 87.51554533252485 | -4.320725429884453 | 0.2727272727272727 | 1138.0195487861092 | 1 | 1 | 1 | 0 | 0 | 0 |
| diagnostic_state_positive_ex_quality_confirmed | recent_oos | diagnostic_state_selection | 1000.0 | 209 | 11 | 1875.1554533252483 | 87.51554533252485 | -4.320725429884453 | 0.2727272727272727 | 1138.0195487861092 | 1 | 1 | 1 | 0 | 0 | 0 |
| predeclared_reinforcing_only_existing_exit | recent_oos | predeclared_state_selection | 1000.0 | 92 | 11 | 1751.5485200561052 | 75.15485200561052 | -4.320725429884453 | 0.2727272727272727 | 1138.0195487861092 | 1 | 1 | 0 | 0 | 0 | 0 |
| baseline_task639_core | recent_oos | baseline | 1000.0 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| predeclared_exclude_sparse_existing_exit | recent_oos | predeclared_data_quality_selection | 1000.0 | 287 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 1 | 0 | 0 | 0 | 0 |
| diagnostic_exclude_company_quality_price_confirmed | validation | diagnostic_state_selection | 1000.0 | 491 | 13 | 1304.40199798408 | 30.440199798407996 | -5.780061968077943 | 0.15384615384615385 | 1049.908329847512 | 1 | 1 | 1 | 0 | 0 | 0 |
| diagnostic_state_positive_ex_quality_confirmed | validation | diagnostic_state_selection | 1000.0 | 474 | 13 | 1304.40199798408 | 30.440199798407996 | -5.780061968077943 | 0.15384615384615385 | 1049.908329847512 | 1 | 1 | 1 | 0 | 0 | 0 |
| predeclared_reinforcing_only_existing_exit | validation | predeclared_state_selection | 1000.0 | 181 | 12 | 1098.816620099173 | 9.881662009917292 | -5.896340848131154 | 0.25 | 1049.908329847512 | 1 | 1 | 0 | 0 | 0 | 0 |
| predeclared_reinforcing_or_offsetting_existing_exit | validation | predeclared_state_selection | 1000.0 | 181 | 12 | 1098.816620099173 | 9.881662009917292 | -5.896340848131154 | 0.25 | 1049.908329847512 | 1 | 1 | 0 | 0 | 0 | 0 |
| baseline_task639_core | validation | baseline | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |
| predeclared_exclude_sparse_existing_exit | validation | predeclared_data_quality_selection | 1000.0 | 638 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 1 | 0 | 0 | 0 | 0 |

### Promotion Report

| candidate_name | all_final_capital_usd | all_max_drawdown_pct | all_accepted_trade_count | all_entry_reduce_failure_rate | all_beats_qqq_flag | recent_oos_final_capital_usd | recent_oos_max_drawdown_pct | recent_oos_accepted_trade_count | recent_oos_entry_reduce_failure_rate | recent_oos_beats_qqq_flag | validation_final_capital_usd | validation_max_drawdown_pct | validation_accepted_trade_count | validation_entry_reduce_failure_rate | validation_beats_qqq_flag | beats_all_task639_flag | all_drawdown_not_worse_flag | validation_improves_task639_flag | recent_oos_improves_task639_flag | validation_drawdown_not_worse_flag | recent_oos_drawdown_not_worse_flag | promotion_allowed_flag | promotion_candidate_flag | failure_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| predeclared_exclude_sparse_existing_exit | 8533.889412035187 | -32.70106787087056 | 50.0 | 0.26 | 1.0 | 1531.9029143138666 | -0.811391994497368 | 10.0 | 0.2 | 1.0 | 1069.2312936091898 | -7.363321689343804 | 15.0 | 0.4 | 1.0 | 1 | 0 | 0 | 0 | 1 | 1 | 1 | 0 | full_period_drawdown_worse |
| baseline_task639_core | 7639.620310821465 | -23.755747663170702 | 54.0 | 0.37037037037037035 | 1.0 | 1531.9029143138666 | -0.811391994497368 | 10.0 | 0.2 | 1.0 | 1069.2312936091898 | -7.363321689343804 | 15.0 | 0.4 | 1.0 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 0 | full_period_return_not_better |
| diagnostic_exclude_company_quality_price_confirmed | 4961.890187114215 | -31.809120103640797 | 47.0 | 0.3191489361702128 | 1.0 | 1875.1554533252483 | -4.320725429884453 | 11.0 | 0.2727272727272727 | 1.0 | 1304.40199798408 | -5.780061968077943 | 13.0 | 0.15384615384615385 | 1.0 | 0 | 0 | 1 | 1 | 1 | 0 | 0 | 0 | diagnostic_only_not_promotion_eligible |
| diagnostic_state_positive_ex_quality_confirmed | 4145.70551537549 | -29.548644354063423 | 45.0 | 0.28888888888888886 | 1.0 | 1875.1554533252483 | -4.320725429884453 | 11.0 | 0.2727272727272727 | 1.0 | 1304.40199798408 | -5.780061968077943 | 13.0 | 0.15384615384615385 | 1.0 | 0 | 0 | 1 | 1 | 1 | 0 | 0 | 0 | diagnostic_only_not_promotion_eligible |
| predeclared_reinforcing_or_offsetting_existing_exit | 1479.163115648116 | -37.67596890657304 | 42.0 | 0.47619047619047616 | 0.0 | 1875.1554533252483 | -4.320725429884453 | 11.0 | 0.2727272727272727 | 1.0 | 1098.816620099173 | -5.896340848131154 | 12.0 | 0.25 | 1.0 | 0 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | full_period_return_not_better |
| predeclared_reinforcing_only_existing_exit | 1230.1512508684639 | -38.39493558493857 | 41.0 | 0.5121951219512195 | 0.0 | 1751.5485200561052 | -4.320725429884453 | 11.0 | 0.2727272727272727 | 1.0 | 1098.816620099173 | -5.896340848131154 | 12.0 | 0.25 | 1.0 | 0 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | full_period_return_not_better |

### Relation State Diagnostics

| split_name | mechanism_relation_state | trade_count | avg_return_pct | win_rate | entry_reduce_failure_rate | large_loss_rate | evaluation_only_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| recent_oos | mechanism_reinforcing_company_positive | 92 | 18.475886296342882 | 0.5869565217391305 | 0.358695652173913 | 0.15217391304347827 | 1 |
| recent_oos | mechanism_offsetting_company_positive | 24 | 10.857675076744428 | 0.7083333333333334 | 0.2916666666666667 | 0.25 | 1 |
| recent_oos | sparse_mechanism_cell | 45 | 9.767792409255474 | 0.5777777777777777 | 0.37777777777777777 | 0.24444444444444444 | 1 |
| recent_oos | company_positive_needs_confirmation | 93 | 6.110406008129817 | 0.5913978494623656 | 0.3118279569892473 | 0.21505376344086022 | 1 |
| recent_oos | company_quality_price_confirmed | 78 | -4.949350156601596 | 0.32051282051282054 | 0.5769230769230769 | 0.34615384615384615 | 1 |
| train_design | mechanism_offsetting_company_positive | 18 | 15.468343523972935 | 0.7777777777777778 | 0.16666666666666666 | 0.16666666666666666 | 1 |
| train_design | company_positive_needs_confirmation | 174 | 7.5187445678152125 | 0.5229885057471264 | 0.41379310344827586 | 0.3103448275862069 | 1 |
| train_design | company_quality_price_confirmed | 158 | 6.114144963042134 | 0.46835443037974683 | 0.5063291139240507 | 0.43037974683544306 | 1 |
| train_design | sparse_mechanism_cell | 94 | 3.9145967743048424 | 0.5531914893617021 | 0.3829787234042553 | 0.30851063829787234 | 1 |
| train_design | mechanism_reinforcing_company_positive | 190 | 1.4540552381175789 | 0.5 | 0.4631578947368421 | 0.4 | 1 |
| validation | mechanism_reinforcing_company_positive | 181 | 8.206319710335507 | 0.6298342541436464 | 0.2983425414364641 | 0.2154696132596685 | 1 |
| validation | company_positive_needs_confirmation | 293 | 5.83260933985938 | 0.6143344709897611 | 0.3242320819112628 | 0.22866894197952217 | 1 |
| validation | company_quality_price_confirmed | 164 | 4.028689133557878 | 0.5121951219512195 | 0.4024390243902439 | 0.2682926829268293 | 1 |
| validation | sparse_mechanism_cell | 17 | -15.384735250790554 | 0.058823529411764705 | 0.8823529411764706 | 0.7058823529411765 | 1 |

### Failure Analysis

| candidate_name | what_improved | what_failed | plain_read |
| --- | --- | --- | --- |
| predeclared_exclude_sparse_existing_exit | full_return | full_period_drawdown_worse | Sparse removal boosts full return but worsens full drawdown and does not change OOS account. |
| diagnostic_exclude_company_quality_price_confirmed | validation_return,recent_oos_return | diagnostic_only_not_promotion_eligible | OOS improves, but this is diagnostic and full-period return/drawdown fail. |
| diagnostic_state_positive_ex_quality_confirmed | validation_return,recent_oos_return | diagnostic_only_not_promotion_eligible | OOS improves, but this is diagnostic and full-period return/drawdown fail. |
| predeclared_reinforcing_or_offsetting_existing_exit | validation_return,recent_oos_return | full_period_return_not_better | Reinforcing states help OOS but fail full-period robustness and drawdown. |
| predeclared_reinforcing_only_existing_exit | validation_return,recent_oos_return | full_period_return_not_better | Reinforcing states help OOS but fail full-period robustness and drawdown. |

## No-Background Decision-Maker Report

관계형 엔진을 실제 매매 선택에 연결해봤습니다.

결과는 움직였습니다. 즉 분류가 완전히 쓸모없는 건 아닙니다.

하지만 돈 넣을 후보는 아직 없습니다.

OOS를 좋게 만드는 후보는 전체기간 수익과 낙폭이 깨졌고, 전체기간을 좋게 만드는 후보는 OOS 개선이 없거나 낙폭이 깨졌습니다.

## Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| no_fixed_hold_or_timing_override | 1 | violations=0 | relation selection must keep existing Task639 timing and exit |
| relation_selection_candidates_tested | 1 | candidates=6 | baseline plus multiple relation-selection candidates |
| oos_movement_observed | 1 | both_oos_improvers=4 | at least one candidate changes validation and recent OOS result |
| promotion_candidate_found | 0 | promotion_candidates=0 | candidate must improve full return, drawdown, validation, and recent OOS |
| strategy_accepted | 0 | research diagnostic only | requires accepted strategy gates and live readiness |

## Artifact Manifest

- `relation_selection_candidate_specs.csv`
- `relation_selection_candidate_grid.csv`
- `relation_selection_promotion_report.csv`
- `relation_state_oos_diagnostics.csv`
- `relation_selection_failure_analysis.csv`
- `task_663_decision.csv`
- `task_663_pass_fail_matrix.csv`
- `artifact_manifest.csv`
