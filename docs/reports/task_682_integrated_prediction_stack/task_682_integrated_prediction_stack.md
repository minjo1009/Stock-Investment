# Task682 Integrated Prediction Stack

## Decision Summary

- Verdict: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- What changed: the five-engine prediction stack was implemented as separate artifacts and linked through cohort slot qualification.
- Quality rewrite: catalyst now separates low/overhang/density, archetype uses entry-time structure, same-symbol context compares prior symbol signatures, and displacement hurdle v2 requires incumbent vulnerability before replacement.
- Key metrics: active cap3 $10,887.47 / MDD -30.52%; best candidate `active_relation_cap3_reference` $10,887.47 / MDD -30.52%.
- Next action: keep as research-only until split/OOS gates and active cap3 winner preservation both pass.

## Quant Expert Report

### Data source and source readiness

- Input: Task672 current-data state panel.
- Microstructure, quote, trade, and NBBO are not used.
- GPT is not used as market data, source truth, label, or assignment input.

### Exact join keys

- Five engine panels join on `lifecycle_id`.
- Cohort slot qualification groups by `entry_ts`.
- Accepted-trade displacement compares `lifecycle_id` sets.
- `integrated_cohort_slot_displacement_hurdle_v2` uses active cap3 as a baseline slot set, but only allows replacement when source safety, archetype advantage, price/leadership advantage, catalyst non-deterioration, concentration non-deterioration, and incumbent vulnerability are all satisfied.

### Leakage audit

- Return, label, and future price assignment flags are zero.
- `classify_winner_archetype` is not used for assignment.
- `classify_top5_tier` and `top5_priority_rank` are not used.
- Active cap3 big-winner guardrail is evaluation-only.
- Displacement vulnerability uses only entry-time source/relation/catalyst/setup fields and does not use realized return.

### Split/OOS metrics

| candidate_name | split_name | initial_capital_usd | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct | entry_reduce_failure_rate | qqq_final_capital_usd | beats_qqq_flag | cohort_slot_assignment_flag | source_strict_flag | return_used_in_assignment_flag | label_used_in_assignment_flag | future_price_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| active_relation_cap3_reference | all | 1000.0000 | 1621 | 51 | 10887.4747 | 988.7475 | -30.5249 | 0.3333 | 1606.8278 | 1 | 0 | 0 | 0 | 0 | 0 |
| integrated_cohort_slot_displacement_hurdle_v2 | all | 1000.0000 | 1621 | 51 | 10887.4747 | 988.7475 | -30.5249 | 0.3333 | 1606.8278 | 1 | 1 | 0 | 0 | 0 | 0 |
| integrated_cohort_slot_source_strict_probe | all | 1000.0000 | 1621 | 47 | 7078.8437 | 607.8844 | -34.3566 | 0.3404 | 1606.8278 | 1 | 1 | 1 | 0 | 0 | 0 |
| integrated_cohort_slot_v1 | all | 1000.0000 | 1621 | 51 | 6946.1840 | 594.6184 | -29.1191 | 0.3529 | 1606.8278 | 1 | 1 | 0 | 0 | 0 | 0 |
| active_relation_cap3_reference | recent_oos | 1000.0000 | 332 | 10 | 1541.4395 | 54.1439 | -1.0958 | 0.2000 | 1124.1928 | 1 | 0 | 0 | 0 | 0 | 0 |
| integrated_cohort_slot_displacement_hurdle_v2 | recent_oos | 1000.0000 | 332 | 10 | 1541.4395 | 54.1439 | -1.2711 | 0.2000 | 1124.1928 | 1 | 1 | 0 | 0 | 0 | 0 |
| integrated_cohort_slot_v1 | recent_oos | 1000.0000 | 332 | 10 | 1297.5398 | 29.7540 | -1.4064 | 0.3000 | 1124.1928 | 1 | 1 | 0 | 0 | 0 | 0 |
| integrated_cohort_slot_source_strict_probe | recent_oos | 1000.0000 | 332 | 10 | 1297.5398 | 29.7540 | -1.4064 | 0.3000 | 1124.1928 | 1 | 1 | 1 | 0 | 0 | 0 |
| integrated_cohort_slot_v1 | validation | 1000.0000 | 655 | 12 | 1361.1519 | 36.1152 | -3.8047 | 0.1667 | 1049.9083 | 1 | 1 | 0 | 0 | 0 | 0 |
| integrated_cohort_slot_source_strict_probe | validation | 1000.0000 | 655 | 12 | 1361.1519 | 36.1152 | -3.8047 | 0.1667 | 1049.9083 | 1 | 1 | 1 | 0 | 0 | 0 |
| active_relation_cap3_reference | validation | 1000.0000 | 655 | 13 | 1327.5223 | 32.7522 | -5.8669 | 0.1538 | 1049.9083 | 1 | 0 | 0 | 0 | 0 | 0 |
| integrated_cohort_slot_displacement_hurdle_v2 | validation | 1000.0000 | 655 | 13 | 1327.5223 | 32.7522 | -5.6222 | 0.1538 | 1049.9083 | 1 | 1 | 0 | 0 | 0 | 0 |

### Winner preservation guardrail

| candidate_name | active_cap3_trade_count | candidate_trade_count | common_trade_count | removed_active_cap3_trade_count | added_trade_count | removed_active_cap3_avg_return_pct_eval_only | removed_active_cap3_big_winner_count_eval_only | removed_active_cap3_failure_count_eval_only | added_avg_return_pct_eval_only | added_big_winner_count_eval_only | winner_preservation_guardrail_pass_flag | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| integrated_cohort_slot_v1 | 51 | 51 | 31 | 20 | 20 | 15.4361 | 4 | 7 | 0.7081 | 0 | 0 | 0 |
| integrated_cohort_slot_source_strict_probe | 51 | 47 | 26 | 25 | 21 | 13.2596 | 3 | 10 | 1.7871 | 1 | 0 | 0 |
| active_relation_cap3_reference | 51 | 51 | 51 | 0 | 0 | 0.0000 | 0 | 0 | 0.0000 | 0 | 1 | 0 |
| integrated_cohort_slot_displacement_hurdle_v2 | 51 | 51 | 51 | 0 | 0 | 0.0000 | 0 | 0 | 0.0000 | 0 | 1 | 0 |

### Displacement pairs

| candidate_name | removed_count | removed_avg_return_pct_eval_only | removed_big_winner_count_eval_only | added_count | added_avg_return_pct_eval_only | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- |
| integrated_cohort_slot_displacement_hurdle_v2 | 0 | 0.0000 | 0 | 0 | 0.0000 | 0 |
| integrated_cohort_slot_source_strict_probe | 25 | 13.2596 | 3 | 21 | 1.7871 | 0 |
| integrated_cohort_slot_v1 | 20 | 15.4361 | 4 | 20 | 0.7081 | 0 |

### Slot summary

| candidate_name | split_name | allocation_reason | row_count | accepted_count | avg_return_pct_eval_only | big_winner_count_eval_only | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| active_relation_cap3_reference | all | accepted | 51 | 51 | 34.0924 | 12 | 0 |
| active_relation_cap3_reference | all | max_positions_full | 1534 | 0 | 4.0954 | 75 | 0 |
| active_relation_cap3_reference | all | relation_concentration_cap | 36 | 0 | 15.0276 | 3 | 0 |
| integrated_cohort_slot_displacement_hurdle_v2 | all | accepted | 51 | 51 | 34.0924 | 12 | 0 |
| integrated_cohort_slot_displacement_hurdle_v2 | all | displacement_failed_no_archetype_advantage | 22 | 0 | 6.8858 | 2 | 0 |
| integrated_cohort_slot_displacement_hurdle_v2 | all | displacement_failed_sparse_source | 7 | 0 | 18.5888 | 0 | 0 |
| integrated_cohort_slot_displacement_hurdle_v2 | all | displacement_no_baseline_incumbent | 1527 | 0 | 4.0733 | 75 | 0 |
| integrated_cohort_slot_displacement_hurdle_v2 | all | relation_cap3 | 14 | 0 | 22.9909 | 1 | 0 |
| integrated_cohort_slot_source_strict_probe | all | accepted | 47 | 47 | 30.7393 | 10 | 0 |
| integrated_cohort_slot_source_strict_probe | all | max_positions_full | 1534 | 0 | 4.2604 | 78 | 0 |
| integrated_cohort_slot_source_strict_probe | all | relation_cap3 | 26 | 0 | 16.8695 | 2 | 0 |
| integrated_cohort_slot_source_strict_probe | all | source_strict_sparse_block | 14 | 0 | 10.2354 | 0 | 0 |
| integrated_cohort_slot_v1 | all | accepted | 51 | 51 | 28.3167 | 8 | 0 |
| integrated_cohort_slot_v1 | all | max_positions_full | 1539 | 0 | 4.2524 | 79 | 0 |
| integrated_cohort_slot_v1 | all | relation_cap3 | 31 | 0 | 18.5013 | 3 | 0 |
| active_relation_cap3_reference | recent_oos | accepted | 10 | 10 | 24.7253 | 3 | 0 |
| active_relation_cap3_reference | recent_oos | max_positions_full | 313 | 0 | 6.7889 | 28 | 0 |
| active_relation_cap3_reference | recent_oos | relation_concentration_cap | 9 | 0 | 4.8847 | 1 | 0 |
| integrated_cohort_slot_displacement_hurdle_v2 | recent_oos | accepted | 10 | 10 | 24.7253 | 3 | 0 |
| integrated_cohort_slot_displacement_hurdle_v2 | recent_oos | displacement_no_baseline_incumbent | 316 | 0 | 6.9134 | 29 | 0 |
| integrated_cohort_slot_displacement_hurdle_v2 | recent_oos | relation_cap3 | 6 | 0 | -2.6253 | 0 | 0 |
| integrated_cohort_slot_source_strict_probe | recent_oos | accepted | 10 | 10 | 13.9319 | 2 | 0 |
| integrated_cohort_slot_source_strict_probe | recent_oos | max_positions_full | 309 | 0 | 7.2777 | 29 | 0 |
| integrated_cohort_slot_source_strict_probe | recent_oos | relation_cap3 | 13 | 0 | 2.1552 | 1 | 0 |
| integrated_cohort_slot_v1 | recent_oos | accepted | 10 | 10 | 13.9319 | 2 | 0 |
| integrated_cohort_slot_v1 | recent_oos | max_positions_full | 309 | 0 | 7.2777 | 29 | 0 |
| integrated_cohort_slot_v1 | recent_oos | relation_cap3 | 13 | 0 | 2.1552 | 1 | 0 |
| active_relation_cap3_reference | validation | accepted | 13 | 13 | 12.2258 | 1 | 0 |
| active_relation_cap3_reference | validation | max_positions_full | 625 | 0 | 4.8954 | 20 | 0 |
| active_relation_cap3_reference | validation | relation_concentration_cap | 17 | 0 | 2.7902 | 0 | 0 |

### Forbidden input audit

| check_name | violation_count | pass_flag | required_value |
| --- | --- | --- | --- |
| leadership_return_used_in_assignment_flag | 0 | 1 | 0 violations |
| catalyst_return_used_in_assignment_flag | 0 | 1 | 0 violations |
| archetype_return_used_in_assignment_flag | 0 | 1 | 0 violations |
| same_symbol_return_used_in_assignment_flag | 0 | 1 | 0 violations |
| stack_return_used_in_assignment_flag | 0 | 1 | 0 violations |
| stack_label_used_in_assignment_flag | 0 | 1 | 0 violations |
| stack_future_price_used_in_assignment_flag | 0 | 1 | 0 violations |
| symbol_blacklist_used | 0 | 1 | 0 violations |
| theme_blacklist_used | 0 | 1 | 0 violations |
| microstructure_used_in_assignment | 0 | 1 | 0 violations |
| allocation_return_used_in_assignment_flag | 0 | 1 | 0 violations |

### Remaining blockers

- The integrated stack is a research candidate, not deployment logic.
- Displacement hurdle v2 preserved active cap3 winners, but did not improve final capital versus active cap3.
- The remaining blocker is predictive improvement inside the five engines without turning active cap3 preservation into a disguised global rank.

## No-Background Decision-Maker Report

- What happened: the five required engines were built separately and connected in order.
- Why it matters: we stopped using one global top5 score and started comparing candidates only inside the same entry-time cohort.
- Whether this changes capital readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: inspect whether the cohort slot engine protects winners without diluting alpha.

## Artifact Manifest

- Inputs: Task672 panel and QQQ benchmark.
- Outputs: five engine artifacts, integrated stack, simulation results, guardrail audit, report, manifest.
- Validation commands: `python -m unittest tests.test_task682_integrated_prediction_stack`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

| gate_name | pass_flag | observed | required |
| --- | --- | --- | --- |
| five_engine_columns_built | 1 | columns present | all engine outputs |
| cohort_slot_assignment_built | 1 | rows=2608 | cohort allocation rows |
| no_forbidden_assignment_inputs | 1 | violations=0 | 0 violations |
| task678_assignment_reuse_removed | 1 | old assignment column absent | no Task678 assignment column |
| global_top5_rank_removed | 1 | global top5 rank absent | no global top5 rank |
| best_beats_active_cap3_return | 0 | best=10887.47, active=10887.47 | best final > active cap3 |
| best_mdd_not_worse_than_active_cap3 | 1 | best=-30.52, active=-30.52 | best MDD not worse |
| best_preserves_active_big_winners | 1 | removed_big=0 | 0 removed big winners |
| strategy_accepted | 0 | research only | split/OOS promotion required |
