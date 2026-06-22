# Task662 OOS Effect Forensics

## Decision Summary

- Verdict: `OOS_EFFECT_ABSENT_BECAUSE_ACTION_REACH_AND_EXIT_MAPPING_FAIL`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Root cause: OOS actions either do not overlap accepted trades or replace profitable existing_exit winners with shorter/weaker exits.

## Quant Expert Report

Task662 explains why Task661's relation engine did not create distinct validation/recent OOS account improvement.

### Data Source And Source Readiness

Input is Task661 mechanism state rebuilt from the Task659 panel. No new market data or source text is introduced.

### Exact Join Keys

`lifecycle_id`, `split_name`, `timing_mode`, and `exit_mode`.

### Leakage Audit

This task is diagnostic only. Returns are used only to explain why prior candidates failed.

### Action Reach

| split_name | task639_core_rows | baseline_accepted_count | baseline_allowed_rows | reduce_duration_rows | strength_hold_candidate_rows | confirmation_required_rows | research_only_rows | baseline_allowed_accepted | reduce_duration_accepted | strength_hold_candidate_accepted | confirmation_required_accepted | accepted_trade_ids_with_action_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| validation | 655 | 15 | 457 | 0 | 181 | 0 | 17 | 11 | 0 | 4 | 0 | 4 |
| recent_oos | 332 | 10 | 171 | 24 | 92 | 0 | 45 | 6 | 0 | 4 | 0 | 4 |

### Candidate Accepted Delta

| candidate_name | split_name | baseline_accepted_count | candidate_accepted_count | common_accepted_count | modified_common_accepted_count | added_accepted_count | removed_accepted_count | common_return_delta_pct_point_sum | candidate_capital_pnl_pct | candidate_max_drawdown_pct | candidate_entry_reduce_failure_rate | effect_summary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mechanism_reduce_hold5 | validation | 15 | 15 | 15 | 0 | 0 | 0 | 0.0 | 8.45801214785804 | -6.723031656174594 | 0.4 | no_accepted_trade_effect |
| mechanism_reduce_hold10 | validation | 15 | 15 | 15 | 0 | 0 | 0 | 0.0 | 8.45801214785804 | -6.723031656174594 | 0.4 | no_accepted_trade_effect |
| mechanism_confirm_delay60m | validation | 15 | 15 | 15 | 0 | 0 | 0 | 0.0 | 8.45801214785804 | -6.723031656174594 | 0.4 | no_accepted_trade_effect |
| mechanism_confirm_vwap | validation | 15 | 15 | 15 | 0 | 0 | 0 | 0.0 | 8.45801214785804 | -6.723031656174594 | 0.4 | no_accepted_trade_effect |
| mechanism_strength_hold20 | validation | 15 | 20 | 13 | 3 | 7 | 2 | -15.888449302466839 | -14.340829442523173 | -18.850608396399892 | 0.45 | accepted_winners_cut_or_returns_reduced |
| mechanism_combo_hold5_confirm_strength20 | validation | 15 | 20 | 13 | 3 | 7 | 2 | -15.888449302466839 | -14.340829442523173 | -18.850608396399892 | 0.45 | accepted_winners_cut_or_returns_reduced |
| diagnostic_skip_mechanism_blocker | validation | 15 | 15 | 15 | 0 | 0 | 0 | 0.0 | 8.45801214785804 | -6.723031656174594 | 0.4 | no_accepted_trade_effect |
| mechanism_any_action_hold5 | validation | 15 | 22 | 14 | 4 | 8 | 1 | 22.128389716990057 | 4.8706865839401425 | -5.221840501415109 | 0.36363636363636365 | capacity_released_adds_trades |
| mechanism_reduce_hold5 | recent_oos | 10 | 10 | 10 | 0 | 0 | 0 | 0.0 | 54.450617960823045 | -0.7349232756767576 | 0.2 | no_accepted_trade_effect |
| mechanism_reduce_hold10 | recent_oos | 10 | 10 | 10 | 0 | 0 | 0 | 0.0 | 54.450617960823045 | -0.7349232756767576 | 0.2 | no_accepted_trade_effect |
| mechanism_confirm_delay60m | recent_oos | 10 | 10 | 10 | 0 | 0 | 0 | 0.0 | 54.450617960823045 | -0.7349232756767576 | 0.2 | no_accepted_trade_effect |
| mechanism_confirm_vwap | recent_oos | 10 | 10 | 10 | 0 | 0 | 0 | 0.0 | 54.450617960823045 | -0.7349232756767576 | 0.2 | no_accepted_trade_effect |
| mechanism_strength_hold20 | recent_oos | 10 | 13 | 10 | 4 | 3 | 0 | -143.0647287159001 | 8.884363105043992 | -12.887826296688921 | 0.38461538461538464 | accepted_winners_cut_or_returns_reduced |
| mechanism_combo_hold5_confirm_strength20 | recent_oos | 10 | 13 | 10 | 4 | 3 | 0 | -143.0647287159001 | 8.884363105043992 | -12.887826296688921 | 0.38461538461538464 | accepted_winners_cut_or_returns_reduced |
| diagnostic_skip_mechanism_blocker | recent_oos | 10 | 10 | 10 | 0 | 0 | 0 | 0.0 | 54.450617960823045 | -0.7349232756767576 | 0.2 | no_accepted_trade_effect |
| mechanism_any_action_hold5 | recent_oos | 10 | 17 | 10 | 4 | 7 | 0 | -208.4623162544562 | 18.064149144110676 | -2.6262569316028217 | 0.23529411764705882 | accepted_winners_cut_or_returns_reduced |

### Winner Cut Audit

| candidate_name | split_name | lifecycle_id | symbol | theme_id | base_timing_mode | base_exit_mode | candidate_timing_mode | candidate_exit_mode | base_return_pct | candidate_return_pct | return_delta_pct_point | base_action_family |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mechanism_any_action_hold5 | recent_oos | TASK617/ARM/20260416T144500Z | ARM | ai_semiconductors | delay1d | existing_exit | delay1d | hold5 | 104.83827997990105 | 18.65723015439073 | -86.18104982551031 | STRENGTH_HOLD_CANDIDATE |
| mechanism_any_action_hold5 | recent_oos | TASK617/MRVL/20260416T150000Z | MRVL | ai_semiconductors | delay1d | existing_exit | delay1d | hold5 | 78.61162703012192 | 3.87770417850434 | -74.73392285161758 | STRENGTH_HOLD_CANDIDATE |
| mechanism_combo_hold5_confirm_strength20 | recent_oos | TASK617/ARM/20260416T144500Z | ARM | ai_semiconductors | delay1d | existing_exit | delay1d | hold20 | 104.83827997990105 | 33.29152277006255 | -71.54675720983849 | STRENGTH_HOLD_CANDIDATE |
| mechanism_strength_hold20 | recent_oos | TASK617/ARM/20260416T144500Z | ARM | ai_semiconductors | delay1d | existing_exit | delay1d | hold20 | 104.83827997990105 | 33.29152277006255 | -71.54675720983849 | STRENGTH_HOLD_CANDIDATE |
| mechanism_strength_hold20 | recent_oos | TASK617/MRVL/20260416T150000Z | MRVL | ai_semiconductors | delay1d | existing_exit | delay1d | hold20 | 78.61162703012192 | 19.49699060173999 | -59.11463642838193 | STRENGTH_HOLD_CANDIDATE |
| mechanism_combo_hold5_confirm_strength20 | recent_oos | TASK617/MRVL/20260416T150000Z | MRVL | ai_semiconductors | delay1d | existing_exit | delay1d | hold20 | 78.61162703012192 | 19.49699060173999 | -59.11463642838193 | STRENGTH_HOLD_CANDIDATE |
| mechanism_any_action_hold5 | recent_oos | TASK617/AMD/20260416T144500Z | AMD | ai_semiconductors | delay1d | existing_exit | delay1d | hold5 | 66.20812357030424 | 15.18531162677285 | -51.02281194353139 | STRENGTH_HOLD_CANDIDATE |
| mechanism_strength_hold20 | validation | TASK617/ASML/20250701T133000Z | ASML | ai_semiconductors | delay1d | existing_exit | delay1d | hold20 | 20.90931737599928 | -11.13257031564833 | -32.04188769164761 | STRENGTH_HOLD_CANDIDATE |
| mechanism_combo_hold5_confirm_strength20 | validation | TASK617/ASML/20250701T133000Z | ASML | ai_semiconductors | delay1d | existing_exit | delay1d | hold20 | 20.90931737599928 | -11.13257031564833 | -32.04188769164761 | STRENGTH_HOLD_CANDIDATE |
| mechanism_strength_hold20 | recent_oos | TASK617/AMD/20260416T144500Z | AMD | ai_semiconductors | delay1d | existing_exit | delay1d | hold20 | 66.20812357030424 | 47.55879500594964 | -18.649328564354594 | STRENGTH_HOLD_CANDIDATE |
| mechanism_combo_hold5_confirm_strength20 | recent_oos | TASK617/AMD/20260416T144500Z | AMD | ai_semiconductors | delay1d | existing_exit | delay1d | hold20 | 66.20812357030424 | 47.55879500594964 | -18.649328564354594 | STRENGTH_HOLD_CANDIDATE |
| mechanism_any_action_hold5 | validation | TASK617/ASML/20250701T133000Z | ASML | ai_semiconductors | delay1d | existing_exit | delay1d | hold5 | 20.90931737599928 | 2.5108975566082 | -18.398419819391084 | STRENGTH_HOLD_CANDIDATE |
| mechanism_strength_hold20 | validation | TASK617/MDB/20250904T144500Z | MDB | data_devops_software | delay1d | existing_exit | delay1d | hold20 | 0.8030636374521 | -2.38774208273467 | -3.19080572018677 | STRENGTH_HOLD_CANDIDATE |
| mechanism_combo_hold5_confirm_strength20 | validation | TASK617/MDB/20250904T144500Z | MDB | data_devops_software | delay1d | existing_exit | delay1d | hold20 | 0.8030636374521 | -2.38774208273467 | -3.19080572018677 | STRENGTH_HOLD_CANDIDATE |
| mechanism_any_action_hold5 | validation | TASK617/MDB/20250904T144500Z | MDB | data_devops_software | delay1d | existing_exit | delay1d | hold5 | 0.8030636374521 | 0.34329352250956 | -0.45977011494254 | STRENGTH_HOLD_CANDIDATE |
| mechanism_any_action_hold5 | recent_oos | TASK617/AVGO/20260416T133000Z | AVGO | ai_semiconductors | delay1d | existing_exit | delay1d | hold5 | -4.92235657378101 | -1.4468882075779101 | 3.4754683662031 | STRENGTH_HOLD_CANDIDATE |
| mechanism_strength_hold20 | recent_oos | TASK617/AVGO/20260416T133000Z | AVGO | ai_semiconductors | delay1d | existing_exit | delay1d | hold20 | -4.92235657378101 | 1.32363691289394 | 6.24599348667495 | STRENGTH_HOLD_CANDIDATE |
| mechanism_combo_hold5_confirm_strength20 | recent_oos | TASK617/AVGO/20260416T133000Z | AVGO | ai_semiconductors | delay1d | existing_exit | delay1d | hold20 | -4.92235657378101 | 1.32363691289394 | 6.24599348667495 | STRENGTH_HOLD_CANDIDATE |
| mechanism_any_action_hold5 | validation | TASK617/PLTR/20250925T134500Z | PLTR | data_devops_software | delay1d | existing_exit | delay1d | hold5 | -13.79981817543989 | 1.4083716254135399 | 15.20818980085343 | STRENGTH_HOLD_CANDIDATE |
| mechanism_strength_hold20 | validation | TASK617/PLTR/20250925T134500Z | PLTR | data_devops_software | delay1d | existing_exit | delay1d | hold20 | -13.79981817543989 | 5.54442593392765 | 19.34424410936754 | STRENGTH_HOLD_CANDIDATE |

## No-Background Decision-Maker Report

OOS에 신호가 없던 게 아닙니다.

신호는 있었는데 실제 계좌에서 돈이 걸린 accepted trade와 잘 안 겹쳤거나, 큰 승자를 짧은 exit으로 바꿔서 수익을 줄였습니다.

그래서 다음은 더 많은 macro 점수가 아니라 accepted trade 기준 exit/회전 감사입니다.

## Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| oos_action_rows_exist | 1 | recent_strength=92; recent_reduce=24 | recent OOS has action-classified rows |
| validation_reduce_duration_exists | 0 | validation_reduce=0 | validation has reduce-duration opportunities |
| accepted_trade_overlap_exists | 1 | recent_accepted_action_overlap=4 | action rows overlap capacity-accepted trades |
| accepted_delta_audited | 1 | rows=16 | candidate accepted-trade deltas exist |
| winner_cut_detected | 1 | winner_cut_rows=22 | audit should identify whether action cuts winners |
| strategy_accepted | 0 | forensics only | requires OOS action improvement and live readiness |

## Artifact Manifest

- `task662_oos_action_reach.csv`
- `task662_candidate_accepted_delta.csv`
- `task662_winner_cut_audit.csv`
- `task_662_decision.csv`
- `task_662_pass_fail_matrix.csv`
- `artifact_manifest.csv`
