# Task679 Top5 Qualification Engine

## Decision Summary

- Verdict: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Key metrics: active cap3 $10,887.47 / MDD -30.52%; best Task679 candidate `active_relation_cap3_reference` $10,887.47 / MDD -30.52%.
- What changed: entry-time winner archetype candidates, top5 qualification tiers, and mandatory winner-preservation guardrail were implemented.
- Next action: do not promote until a top5 rule preserves active cap3 big winners and improves split/OOS return plus drawdown.

## Quant Expert Report

### Data source and source readiness

- Inputs: Task672 current-data state panel and QQQ benchmark.
- No quote, trade, NBBO, or microstructure data is used.
- No GPT output is used as a source, label, or assignment input.

### Exact join keys

- Candidate replay uses original lifecycle rows and `lifecycle_id`.
- Preservation guardrail compares accepted sets by `lifecycle_id`.

### Leakage audit

- Top5 qualification uses entry-time state columns only.
- `return_used_in_assignment_flag`, `label_used_in_assignment_flag`, and `future_price_used_in_assignment_flag` are zero.
- Return fields in performance tables are evaluation-only.

### Split/OOS metrics

| candidate_name | split_name | initial_capital_usd | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct | entry_reduce_failure_rate | qqq_final_capital_usd | beats_qqq_flag | rank_column | block_non_top5_flag | diagnostic_only_flag | return_used_in_assignment_flag | label_used_in_assignment_flag | future_price_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| active_relation_cap3_reference | all | 1000.0000 | 1621 | 51 | 10887.4747 | 988.7475 | -30.5249 | 0.3333 | 1606.8278 | 1 | priority_rank | 0 | 0 | 0 | 0 | 0 |
| top5_preserve_active_cap3_tiebreak | all | 1000.0000 | 1621 | 51 | 8708.7992 | 770.8799 | -30.6095 | 0.3529 | 1606.8278 | 1 | top5_preserve_active_cap3_rank | 0 | 0 | 0 | 0 | 0 |
| top5_elite_contender_only_probe | all | 1000.0000 | 729 | 47 | 6824.9351 | 582.4935 | -19.9309 | 0.2340 | 1606.8278 | 1 | top5_priority_rank | 1 | 1 | 0 | 0 | 0 |
| top5_qualification_priority_v1 | all | 1000.0000 | 1621 | 52 | 6499.9039 | 549.9904 | -31.0539 | 0.3462 | 1606.8278 | 1 | top5_priority_rank | 0 | 0 | 0 | 0 | 0 |
| top5_qualification_priority_v1 | recent_oos | 1000.0000 | 332 | 11 | 1663.4768 | 66.3477 | -7.3158 | 0.3636 | 1124.1928 | 1 | top5_priority_rank | 0 | 0 | 0 | 0 | 0 |
| active_relation_cap3_reference | recent_oos | 1000.0000 | 332 | 10 | 1541.4395 | 54.1439 | -1.0958 | 0.2000 | 1124.1928 | 1 | priority_rank | 0 | 0 | 0 | 0 | 0 |
| top5_preserve_active_cap3_tiebreak | recent_oos | 1000.0000 | 332 | 11 | 1426.8595 | 42.6859 | -7.3158 | 0.5455 | 1124.1928 | 1 | top5_preserve_active_cap3_rank | 0 | 0 | 0 | 0 | 0 |
| top5_elite_contender_only_probe | recent_oos | 1000.0000 | 146 | 12 | 1305.1534 | 30.5153 | -9.2723 | 0.3333 | 1124.1928 | 1 | top5_priority_rank | 1 | 1 | 0 | 0 | 0 |
| active_relation_cap3_reference | validation | 1000.0000 | 655 | 13 | 1327.5223 | 32.7522 | -5.8669 | 0.1538 | 1049.9083 | 1 | priority_rank | 0 | 0 | 0 | 0 | 0 |
| top5_preserve_active_cap3_tiebreak | validation | 1000.0000 | 655 | 12 | 1319.0531 | 31.9053 | -3.1159 | 0.0833 | 1049.9083 | 1 | top5_preserve_active_cap3_rank | 0 | 0 | 0 | 0 | 0 |
| top5_elite_contender_only_probe | validation | 1000.0000 | 292 | 11 | 1247.2793 | 24.7279 | -2.1357 | 0.0909 | 1049.9083 | 1 | top5_priority_rank | 1 | 1 | 0 | 0 | 0 |
| top5_qualification_priority_v1 | validation | 1000.0000 | 655 | 13 | 1228.8669 | 22.8867 | -2.7804 | 0.1538 | 1049.9083 | 1 | top5_priority_rank | 0 | 0 | 0 | 0 | 0 |

### Entry-time archetype candidate performance

| split_name | axis | axis_value | candidate_count | avg_return_costed_pct_eval_only | win_rate_eval_only | big_winner_count_eval_only | failure_count_eval_only | return_used_in_assignment_flag | label_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | entry_time_archetype_candidate | explosive_fragile_continuation | 40 | 16.2871 | 0.6500 | 3 | 12 | 0 | 0 |
| all | entry_time_archetype_candidate | medium_signal_continuation | 65 | 14.8031 | 0.6154 | 7 | 19 | 0 | 0 |
| all | entry_time_archetype_candidate | theme_rotation_or_narrow_leader | 233 | 7.7304 | 0.5708 | 12 | 64 | 0 | 0 |
| all | entry_time_archetype_candidate | steady_trend_persistence | 661 | 5.3740 | 0.5885 | 28 | 166 | 0 | 0 |
| all | entry_time_archetype_candidate | late_extended_breakout | 266 | 4.8238 | 0.4774 | 20 | 87 | 0 | 0 |
| all | entry_time_archetype_candidate | catalyst_repricing_confirmed | 277 | 0.9360 | 0.4477 | 13 | 97 | 0 | 0 |
| all | entry_time_archetype_candidate | mixed_continuation | 79 | 0.6654 | 0.3797 | 7 | 38 | 0 | 0 |
| recent_oos | entry_time_archetype_candidate | late_extended_breakout | 47 | 15.5393 | 0.5957 | 10 | 12 | 0 | 0 |
| recent_oos | entry_time_archetype_candidate | medium_signal_continuation | 11 | 12.9357 | 0.5455 | 1 | 4 | 0 | 0 |
| recent_oos | entry_time_archetype_candidate | theme_rotation_or_narrow_leader | 56 | 12.2505 | 0.5714 | 5 | 11 | 0 | 0 |
| recent_oos | entry_time_archetype_candidate | steady_trend_persistence | 136 | 8.0719 | 0.5588 | 13 | 24 | 0 | 0 |
| recent_oos | entry_time_archetype_candidate | mixed_continuation | 15 | 7.5491 | 0.4667 | 3 | 6 | 0 | 0 |
| recent_oos | entry_time_archetype_candidate | explosive_fragile_continuation | 10 | 2.7328 | 0.7000 | 0 | 3 | 0 | 0 |
| recent_oos | entry_time_archetype_candidate | catalyst_repricing_confirmed | 57 | -6.6821 | 0.2982 | 0 | 21 | 0 | 0 |
| validation | entry_time_archetype_candidate | medium_signal_continuation | 26 | 8.5589 | 0.6154 | 3 | 7 | 0 | 0 |
| validation | entry_time_archetype_candidate | mixed_continuation | 25 | 6.2016 | 0.3600 | 4 | 7 | 0 | 0 |
| validation | entry_time_archetype_candidate | explosive_fragile_continuation | 22 | 6.1017 | 0.6364 | 1 | 6 | 0 | 0 |
| validation | entry_time_archetype_candidate | steady_trend_persistence | 289 | 5.8949 | 0.6263 | 8 | 70 | 0 | 0 |
| validation | entry_time_archetype_candidate | catalyst_repricing_confirmed | 112 | 4.5031 | 0.5179 | 3 | 25 | 0 | 0 |
| validation | entry_time_archetype_candidate | theme_rotation_or_narrow_leader | 78 | 3.6115 | 0.5769 | 0 | 20 | 0 | 0 |

### Top5 qualification tier performance

| split_name | axis | axis_value | candidate_count | avg_return_costed_pct_eval_only | win_rate_eval_only | big_winner_count_eval_only | failure_count_eval_only | return_used_in_assignment_flag | label_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | top5_qualification_tier | elite_top5_candidate | 279 | 11.2912 | 0.6022 | 19 | 74 | 0 | 0 |
| all | top5_qualification_tier | normal_candidate | 670 | 5.3034 | 0.5701 | 33 | 180 | 0 | 0 |
| all | top5_qualification_tier | research_or_reject | 222 | 3.1797 | 0.4775 | 13 | 82 | 0 | 0 |
| all | top5_qualification_tier | top5_contender | 450 | 2.5615 | 0.4733 | 25 | 147 | 0 | 0 |
| recent_oos | top5_qualification_tier | elite_top5_candidate | 63 | 10.4530 | 0.5397 | 6 | 17 | 0 | 0 |
| recent_oos | top5_qualification_tier | research_or_reject | 58 | 9.2469 | 0.5517 | 5 | 17 | 0 | 0 |
| recent_oos | top5_qualification_tier | normal_candidate | 128 | 8.3568 | 0.5625 | 14 | 22 | 0 | 0 |
| recent_oos | top5_qualification_tier | top5_contender | 83 | 1.8265 | 0.4217 | 7 | 25 | 0 | 0 |
| validation | top5_qualification_tier | normal_candidate | 323 | 6.2716 | 0.6285 | 10 | 75 | 0 | 0 |
| validation | top5_qualification_tier | elite_top5_candidate | 111 | 5.9682 | 0.6216 | 3 | 26 | 0 | 0 |
| validation | top5_qualification_tier | top5_contender | 181 | 3.7625 | 0.5083 | 4 | 43 | 0 | 0 |
| validation | top5_qualification_tier | research_or_reject | 40 | -2.5814 | 0.2500 | 4 | 19 | 0 | 0 |

### Winner preservation guardrail

| candidate_name | active_cap3_trade_count | candidate_trade_count | common_trade_count | removed_active_cap3_trade_count | added_trade_count | removed_active_cap3_avg_return_pct_eval_only | removed_active_cap3_big_winner_count_eval_only | removed_active_cap3_failure_count_eval_only | added_avg_return_pct_eval_only | added_big_winner_count_eval_only | winner_preservation_guardrail_pass_flag | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| top5_elite_contender_only_probe | 51 | 47 | 11 | 40 | 36 | 16.9875 | 6 | 13 | 8.1833 | 2 | 0 | 0 |
| top5_qualification_priority_v1 | 51 | 52 | 31 | 20 | 21 | 15.1084 | 4 | 8 | -1.2044 | 0 | 0 | 0 |
| top5_preserve_active_cap3_tiebreak | 51 | 51 | 38 | 13 | 13 | 18.0431 | 3 | 5 | 8.0913 | 1 | 0 | 0 |
| active_relation_cap3_reference | 51 | 51 | 51 | 0 | 0 | 0.0000 | 0 | 0 | 0.0000 | 0 | 1 | 0 |

### Slot qualification audit

| candidate_name | top5_qualification_tier | accepted_flag | row_count | avg_return_costed_pct_eval_only | big_winner_count_eval_only | failure_count_eval_only | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| active_relation_cap3_reference | elite_top5_candidate | 0 | 269 | 7.4333 | 13 | 74 | 0 |
| active_relation_cap3_reference | normal_candidate | 0 | 649 | 4.9237 | 29 | 172 | 0 |
| active_relation_cap3_reference | research_or_reject | 0 | 214 | 3.1751 | 13 | 79 | 0 |
| active_relation_cap3_reference | top5_contender | 0 | 438 | 2.1663 | 23 | 143 | 0 |
| active_relation_cap3_reference | elite_top5_candidate | 1 | 10 | 115.0692 | 6 | 0 | 0 |
| active_relation_cap3_reference | normal_candidate | 1 | 21 | 17.0374 | 4 | 8 | 0 |
| active_relation_cap3_reference | research_or_reject | 1 | 8 | 3.3038 | 0 | 3 | 0 |
| active_relation_cap3_reference | top5_contender | 1 | 12 | 16.9836 | 2 | 4 | 0 |
| top5_elite_contender_only_probe | elite_top5_candidate | 0 | 250 | 7.6681 | 12 | 71 | 0 |
| top5_elite_contender_only_probe | top5_contender | 0 | 432 | 2.3890 | 24 | 141 | 0 |
| top5_elite_contender_only_probe | elite_top5_candidate | 1 | 29 | 42.5248 | 7 | 3 | 0 |
| top5_elite_contender_only_probe | top5_contender | 1 | 18 | 6.6995 | 1 | 6 | 0 |
| top5_preserve_active_cap3_tiebreak | elite_top5_candidate | 0 | 262 | 7.4089 | 13 | 72 | 0 |
| top5_preserve_active_cap3_tiebreak | normal_candidate | 0 | 657 | 5.0767 | 31 | 176 | 0 |
| top5_preserve_active_cap3_tiebreak | research_or_reject | 0 | 214 | 3.2265 | 13 | 79 | 0 |
| top5_preserve_active_cap3_tiebreak | top5_contender | 0 | 437 | 2.2556 | 23 | 142 | 0 |
| top5_preserve_active_cap3_tiebreak | elite_top5_candidate | 1 | 17 | 71.1241 | 6 | 2 | 0 |
| top5_preserve_active_cap3_tiebreak | normal_candidate | 1 | 13 | 16.7592 | 2 | 4 | 0 |
| top5_preserve_active_cap3_tiebreak | research_or_reject | 1 | 8 | 1.9265 | 0 | 3 | 0 |
| top5_preserve_active_cap3_tiebreak | top5_contender | 1 | 13 | 12.8420 | 2 | 5 | 0 |

### Remaining blockers

- The top5 qualification prototype did not create a deployment-ready promotion.
- Any next rule must preserve active cap3 big winners before it is allowed into a backtest promotion path.

## No-Background Decision-Maker Report

- What happened: Top5 자격을 숫자로 만들고, 큰 승자 제거 여부를 필수 검사로 붙였다.
- Why it matters: 이 전략은 많이 사는 전략이 아니라 상위 5개 자리를 제대로 배정해야 돈이 난다.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: Top5 자격 룰을 더 정교화하되 큰 승자를 자르면 바로 탈락시킨다.

## Artifact Manifest

- Inputs: Task672 panel, QQQ benchmark.
- Outputs: all CSVs in this directory plus `artifact_manifest.csv`.
- Validation commands: `python -m unittest tests.test_task679_top5_qualification_engine`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

| gate_name | pass_flag | observed | required |
| --- | --- | --- | --- |
| top5_columns_built | 1 | columns present | required columns |
| no_return_label_future_assignment | 1 | violations=0 | 0 violations |
| candidate_grid_built | 1 | rows=12 | candidate grid |
| winner_preservation_guardrail_built | 1 | rows=4 | guardrail rows |
| slot_audit_built | 1 | rows=28 | slot audit rows |
| best_beats_active_cap3_return | 0 | best=10887.47, active=10887.47 | best final > active cap3 |
| best_mdd_not_worse_than_active_cap3 | 1 | best=-30.52, active=-30.52 | best MDD not worse |
| best_preserves_big_winners | 1 | removed_big=0 | 0 removed big winners |
| strategy_accepted | 0 | research only | requires robust OOS promotion |
