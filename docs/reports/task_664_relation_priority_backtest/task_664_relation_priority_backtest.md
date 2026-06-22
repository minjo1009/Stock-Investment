# Task664 Relation Priority Backtest

## Decision Summary

- Verdict: `RELATION_PRIORITY_TESTED_NO_PROMOTION_CANDIDATE`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Baseline: `$7639.62`, max drawdown `-23.76%`.
- Best priority candidate: `predeclared_relation_ladder` = `$8797.73`, max drawdown `-33.63%`.
- Promotion candidates: `0`.

## Quant Expert Report

Task664 connects relation states to max5 capacity by changing only the ordering of same-entry-timestamp candidates. It does not change entry timing, exits, sizing, or create standalone macro entries.

### Data Source And Source Readiness

Input is the Task661 mechanism state panel rebuilt from Task659. No new data source is introduced.

### Exact Join Keys

`lifecycle_id`, `entry_ts`, `simulated_exit_ts`, and `split_name`.

### Leakage Audit

Predeclared candidates use relation, catalyst, and price acceptance fields only. The recent-weak-state candidate is marked diagnostic and return-tuned, so it cannot promote.

### Candidate Grid

| candidate_name | split_name | candidate_type | initial_capital_usd | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct | entry_reduce_failure_rate | qqq_final_capital_usd | beats_qqq_flag | diagnostic_only_flag | fixed_hold_or_timing_override_flag | return_tuned_flag | label_used_in_assignment_flag | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| predeclared_relation_ladder | all | predeclared_priority | 1000.0 | 1621 | 54 | 8797.725195699932 | 779.7725195699933 | -33.631456638622645 | 0.2962962962962963 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| diagnostic_recent_weak_state_last | all | diagnostic_priority | 1000.0 | 1621 | 54 | 8797.725195699932 | 779.7725195699933 | -33.631456638622645 | 0.2962962962962963 | 1606.8278306897957 | 1 | 1 | 0 | 1 | 0 | 0 |
| predeclared_catalyst_price_ladder | all | predeclared_priority | 1000.0 | 1621 | 55 | 8155.103055938801 | 715.51030559388 | -37.99251560014648 | 0.3090909090909091 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| baseline_chronological | all | baseline | 1000.0 | 1621 | 54 | 7639.620310821465 | 663.9620310821465 | -23.755747663170702 | 0.35185185185185186 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| predeclared_relation_ladder | recent_oos | predeclared_priority | 1000.0 | 332 | 10 | 1539.817826636232 | 53.98178266362319 | -0.8092509033778783 | 0.1 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| predeclared_catalyst_price_ladder | recent_oos | predeclared_priority | 1000.0 | 332 | 10 | 1539.817826636232 | 53.98178266362319 | -0.8092509033778783 | 0.1 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| diagnostic_recent_weak_state_last | recent_oos | diagnostic_priority | 1000.0 | 332 | 10 | 1539.817826636232 | 53.98178266362319 | -0.8092509033778783 | 0.1 | 1124.192829329964 | 1 | 1 | 0 | 1 | 0 | 0 |
| baseline_chronological | recent_oos | baseline | 1000.0 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.1 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| predeclared_catalyst_price_ladder | validation | predeclared_priority | 1000.0 | 655 | 13 | 1402.1861475621602 | 40.21861475621602 | -5.780061968077943 | 0.23076923076923078 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |
| predeclared_relation_ladder | validation | predeclared_priority | 1000.0 | 655 | 13 | 1304.40199798408 | 30.440199798407996 | -5.780061968077943 | 0.15384615384615385 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |
| diagnostic_recent_weak_state_last | validation | diagnostic_priority | 1000.0 | 655 | 13 | 1304.40199798408 | 30.440199798407996 | -5.780061968077943 | 0.15384615384615385 | 1049.908329847512 | 1 | 1 | 0 | 1 | 0 | 0 |
| baseline_chronological | validation | baseline | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |

### Accepted Priority Delta

| candidate_name | split_name | baseline_accepted_count | candidate_accepted_count | common_accepted_count | added_accepted_count | removed_accepted_count | accepted_set_changed_flag | diagnostic_only_flag | return_tuned_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| predeclared_relation_ladder | all | 54 | 54 | 27 | 27 | 27 | 1 | 0 | 0 |
| predeclared_catalyst_price_ladder | all | 54 | 55 | 25 | 30 | 29 | 1 | 0 | 0 |
| diagnostic_recent_weak_state_last | all | 54 | 54 | 27 | 27 | 27 | 1 | 1 | 1 |
| predeclared_relation_ladder | validation | 15 | 13 | 6 | 7 | 9 | 1 | 0 | 0 |
| predeclared_catalyst_price_ladder | validation | 15 | 13 | 5 | 8 | 10 | 1 | 0 | 0 |
| diagnostic_recent_weak_state_last | validation | 15 | 13 | 6 | 7 | 9 | 1 | 1 | 1 |
| predeclared_relation_ladder | recent_oos | 10 | 10 | 9 | 1 | 1 | 1 | 0 | 0 |
| predeclared_catalyst_price_ladder | recent_oos | 10 | 10 | 9 | 1 | 1 | 1 | 0 | 0 |
| diagnostic_recent_weak_state_last | recent_oos | 10 | 10 | 9 | 1 | 1 | 1 | 1 | 1 |

### Slot Collision Audit

| split_name | entry_ts | candidate_count_same_ts | max_positions | relation_state_count | reinforcing_count | offsetting_count | quality_confirmed_count | sparse_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| recent_oos | 2026-05-08 14:30:00+00:00 | 21 | 5 | 3 | 10 | 0 | 7 | 4 |
| recent_oos | 2026-05-13 14:30:00+00:00 | 20 | 5 | 4 | 6 | 3 | 8 | 3 |
| recent_oos | 2026-05-18 14:30:00+00:00 | 19 | 5 | 2 | 0 | 1 | 0 | 18 |
| recent_oos | 2026-04-24 14:30:00+00:00 | 18 | 5 | 2 | 10 | 0 | 8 | 0 |
| recent_oos | 2026-01-23 14:30:00+00:00 | 17 | 5 | 3 | 2 | 0 | 1 | 0 |
| recent_oos | 2026-01-20 14:30:00+00:00 | 15 | 5 | 3 | 1 | 0 | 3 | 0 |
| recent_oos | 2026-01-16 14:30:00+00:00 | 13 | 5 | 2 | 2 | 0 | 11 | 0 |
| recent_oos | 2026-05-14 14:30:00+00:00 | 13 | 5 | 4 | 6 | 2 | 3 | 2 |
| recent_oos | 2026-04-27 14:30:00+00:00 | 12 | 5 | 2 | 11 | 0 | 1 | 0 |
| recent_oos | 2026-05-11 14:30:00+00:00 | 12 | 5 | 3 | 5 | 0 | 1 | 6 |
| recent_oos | 2026-05-15 14:30:00+00:00 | 12 | 5 | 2 | 4 | 0 | 0 | 0 |
| recent_oos | 2026-01-14 14:30:00+00:00 | 11 | 5 | 2 | 2 | 0 | 9 | 0 |
| recent_oos | 2026-01-22 14:30:00+00:00 | 11 | 5 | 3 | 1 | 0 | 1 | 0 |
| recent_oos | 2026-02-26 14:30:00+00:00 | 11 | 5 | 3 | 0 | 0 | 3 | 1 |
| recent_oos | 2026-02-23 14:30:00+00:00 | 10 | 5 | 3 | 0 | 5 | 0 | 3 |
| recent_oos | 2026-01-12 14:30:00+00:00 | 9 | 5 | 1 | 0 | 0 | 9 | 0 |
| recent_oos | 2026-01-15 14:30:00+00:00 | 9 | 5 | 2 | 4 | 0 | 5 | 0 |
| recent_oos | 2026-02-19 14:30:00+00:00 | 9 | 5 | 2 | 1 | 0 | 0 | 0 |
| recent_oos | 2026-02-25 14:30:00+00:00 | 8 | 5 | 2 | 2 | 0 | 0 | 0 |
| recent_oos | 2026-04-20 14:30:00+00:00 | 8 | 5 | 2 | 6 | 0 | 2 | 0 |

### Promotion Report

| candidate_name | all_final_capital_usd | all_max_drawdown_pct | all_accepted_trade_count | all_entry_reduce_failure_rate | all_beats_qqq_flag | recent_oos_final_capital_usd | recent_oos_max_drawdown_pct | recent_oos_accepted_trade_count | recent_oos_entry_reduce_failure_rate | recent_oos_beats_qqq_flag | validation_final_capital_usd | validation_max_drawdown_pct | validation_accepted_trade_count | validation_entry_reduce_failure_rate | validation_beats_qqq_flag | beats_all_task639_flag | all_drawdown_not_worse_flag | validation_improves_task639_flag | recent_oos_improves_task639_flag | validation_drawdown_not_worse_flag | recent_oos_drawdown_not_worse_flag | promotion_allowed_flag | promotion_candidate_flag | failure_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| predeclared_relation_ladder | 8797.725195699932 | -33.631456638622645 | 54.0 | 0.2962962962962963 | 1.0 | 1539.817826636232 | -0.8092509033778783 | 10.0 | 0.1 | 1.0 | 1304.40199798408 | -5.780061968077943 | 13.0 | 0.15384615384615385 | 1.0 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 0 | full_period_drawdown_worse |
| diagnostic_recent_weak_state_last | 8797.725195699932 | -33.631456638622645 | 54.0 | 0.2962962962962963 | 1.0 | 1539.817826636232 | -0.8092509033778783 | 10.0 | 0.1 | 1.0 | 1304.40199798408 | -5.780061968077943 | 13.0 | 0.15384615384615385 | 1.0 | 1 | 0 | 1 | 1 | 1 | 1 | 0 | 0 | diagnostic_or_return_tuned_not_promotion_eligible |
| predeclared_catalyst_price_ladder | 8155.103055938801 | -37.99251560014648 | 55.0 | 0.3090909090909091 | 1.0 | 1539.817826636232 | -0.8092509033778783 | 10.0 | 0.1 | 1.0 | 1402.1861475621602 | -5.780061968077943 | 13.0 | 0.23076923076923078 | 1.0 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 0 | full_period_drawdown_worse |
| baseline_chronological | 7639.620310821465 | -23.755747663170702 | 54.0 | 0.35185185185185186 | 1.0 | 1531.9029143138666 | -0.811391994497368 | 10.0 | 0.1 | 1.0 | 1069.2312936091898 | -7.363321689343804 | 15.0 | 0.4 | 1.0 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 0 | full_period_return_not_better |

## No-Background Decision-Maker Report

관계형 엔진을 매매 슬롯 우선순위에 연결했습니다.

기존 진입과 청산은 그대로입니다.

같은 시간에 후보가 몰릴 때 어떤 종목이 max5 슬롯을 먼저 차지할지만 바꿨습니다.

결과가 좋아지면 relation state가 실제 돈으로 연결되는 것입니다. 아니면 아직 슬롯 우선순위로는 부족한 것입니다.

## Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| no_fixed_hold_or_timing_override | 1 | violations=0 | priority test must keep existing Task639 timing and exit |
| priority_changes_accepted_set | 1 | changed_rows=9 | priority should affect max5 accepted trades |
| no_return_tuned_promotion | 1 | return-tuned promotion count=0 | return-tuned diagnostic candidates cannot be promoted |
| promotion_candidate_found | 0 | promotion_candidates=0 | candidate must improve full return, drawdown, validation, and recent OOS |
| strategy_accepted | 0 | research diagnostic only | requires accepted strategy gates and live readiness |

## Artifact Manifest

- `relation_priority_candidate_specs.csv`
- `relation_priority_ladder.csv`
- `relation_priority_candidate_grid.csv`
- `accepted_priority_delta.csv`
- `slot_collision_audit.csv`
- `relation_priority_promotion_report.csv`
- `task_664_decision.csv`
- `task_664_pass_fail_matrix.csv`
- `artifact_manifest.csv`
