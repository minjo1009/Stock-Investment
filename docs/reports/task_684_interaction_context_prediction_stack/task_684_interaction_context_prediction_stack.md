# Task684 Interaction Context Prediction Stack

## Decision Summary

- Verdict: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Key metrics: active cap3 $10,887.47 / MDD -30.52%; best `active_relation_cap3_reference` $10,887.47 / MDD -30.52%.
- What changed: the same five engines were rebuilt as interaction-aware artifacts. Catalyst is linked to price/relation/leadership absorption, archetype is linked to mixed sub-contexts, same-symbol is interpreter-only, and cohort slot qualification compares context packets only inside `entry_ts`.
- Next action: research-only review of interaction candidates; no deployment.

## Quant Expert Report

### Data source and source readiness

- Inputs: Task682 stack and current Task672-derived fields.
- No new raw data, microstructure, quote, trade, NBBO, label, future price, symbol blacklist, or theme blacklist.
- GPT is not used as source truth or assignment input.

### Exact join keys

- Five engine outputs join by `lifecycle_id`.
- Slot qualification groups by `entry_ts`.
- Displacement guardrail compares `lifecycle_id` sets.

### Leakage audit

- All return/label/future-price assignment flags are zero.
- `classify_winner_archetype`, `classify_top5_tier`, and `top5_priority_rank` are not used.
- `priority_rank` is only the final tie-breaker inside the context packet.

### Split/OOS metrics

| candidate_name | split_name | initial_capital_usd | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct | entry_reduce_failure_rate | qqq_final_capital_usd | beats_qqq_flag | interaction_assignment_flag | guarded_superiority_flag | return_used_in_assignment_flag | label_used_in_assignment_flag | future_price_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| active_relation_cap3_reference | all | 1000.0000 | 1621 | 51 | 10887.4747 | 988.7475 | -30.5249 | 0.3333 | 1606.8278 | 1 | 0 | 0 | 0 | 0 | 0 |
| interaction_context_superiority_guarded_v3 | all | 1000.0000 | 1621 | 51 | 10887.4747 | 988.7475 | -30.5249 | 0.3333 | 1606.8278 | 1 | 1 | 1 | 0 | 0 | 0 |
| interaction_context_packet_v3 | all | 1000.0000 | 1621 | 51 | 8202.1572 | 720.2157 | -30.8422 | 0.3333 | 1606.8278 | 1 | 1 | 0 | 0 | 0 | 0 |
| active_relation_cap3_reference | recent_oos | 1000.0000 | 332 | 10 | 1541.4395 | 54.1439 | -1.0958 | 0.2000 | 1124.1928 | 1 | 0 | 0 | 0 | 0 | 0 |
| interaction_context_superiority_guarded_v3 | recent_oos | 1000.0000 | 332 | 10 | 1541.4395 | 54.1439 | -1.0958 | 0.2000 | 1124.1928 | 1 | 1 | 1 | 0 | 0 | 0 |
| interaction_context_packet_v3 | recent_oos | 1000.0000 | 332 | 10 | 1525.9832 | 52.5983 | -2.0348 | 0.3000 | 1124.1928 | 1 | 1 | 0 | 0 | 0 | 0 |
| interaction_context_packet_v3 | validation | 1000.0000 | 655 | 13 | 1466.4933 | 46.6493 | -3.8975 | 0.1538 | 1049.9083 | 1 | 1 | 0 | 0 | 0 | 0 |
| active_relation_cap3_reference | validation | 1000.0000 | 655 | 13 | 1327.5223 | 32.7522 | -5.8669 | 0.1538 | 1049.9083 | 1 | 0 | 0 | 0 | 0 | 0 |
| interaction_context_superiority_guarded_v3 | validation | 1000.0000 | 655 | 13 | 1327.5223 | 32.7522 | -5.6222 | 0.1538 | 1049.9083 | 1 | 1 | 1 | 0 | 0 | 0 |

### Guardrail audit

| candidate_name | active_cap3_trade_count | candidate_trade_count | common_trade_count | removed_active_cap3_trade_count | removed_active_cap3_big_winner_count_eval_only | removed_active_cap3_avg_return_pct_eval_only | added_trade_count | added_avg_return_pct_eval_only | added_big_winner_count_eval_only | winner_preservation_guardrail_pass_flag | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| active_relation_cap3_reference | 51 | 51 | 51 | 0 | 0 | 0.0000 | 0 | 0.0000 | 0 | 1 | 0 |
| interaction_context_packet_v3 | 51 | 51 | 37 | 14 | 3 | 18.0647 | 14 | 4.6210 | 1 | 0 | 0 |
| interaction_context_superiority_guarded_v3 | 51 | 51 | 51 | 0 | 0 | 0.0000 | 0 | 0.0000 | 0 | 1 | 0 |

### Superiority audit

| candidate_name | split_name | allocation_reason | row_count | accepted_count | avg_return_pct_eval_only | big_winner_count_eval_only | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| active_relation_cap3_reference | all | accepted | 51 | 51 | 34.0924 | 12 | 0 |
| active_relation_cap3_reference | all | max_positions_full | 1534 | 0 | 4.0954 | 75 | 0 |
| active_relation_cap3_reference | all | relation_concentration_cap | 36 | 0 | 15.0276 | 3 | 0 |
| interaction_context_packet_v3 | all | accepted_context_packet | 51 | 51 | 30.4019 | 10 | 0 |
| interaction_context_packet_v3 | all | max_positions_full | 1551 | 0 | 4.3196 | 79 | 0 |
| interaction_context_packet_v3 | all | relation_cap3 | 19 | 0 | 16.4113 | 1 | 0 |
| interaction_context_superiority_guarded_v3 | all | accepted_baseline_context_preserved | 51 | 51 | 34.0924 | 12 | 0 |
| interaction_context_superiority_guarded_v3 | all | relation_cap3 | 14 | 0 | 22.9909 | 1 | 0 |
| interaction_context_superiority_guarded_v3 | all | superiority_failed_archetype_context | 30 | 0 | 5.3016 | 3 | 0 |
| interaction_context_superiority_guarded_v3 | all | superiority_failed_source | 20 | 0 | 15.2540 | 0 | 0 |
| interaction_context_superiority_guarded_v3 | all | superiority_no_replaceable_incumbent | 1506 | 0 | 4.0089 | 74 | 0 |
| active_relation_cap3_reference | recent_oos | accepted | 10 | 10 | 24.7253 | 3 | 0 |
| active_relation_cap3_reference | recent_oos | max_positions_full | 313 | 0 | 6.7889 | 28 | 0 |
| active_relation_cap3_reference | recent_oos | relation_concentration_cap | 9 | 0 | 4.8847 | 1 | 0 |
| interaction_context_packet_v3 | recent_oos | accepted_context_packet | 10 | 10 | 24.1597 | 3 | 0 |
| interaction_context_packet_v3 | recent_oos | max_positions_full | 307 | 0 | 7.0193 | 28 | 0 |
| interaction_context_packet_v3 | recent_oos | relation_cap3 | 15 | 0 | 1.3066 | 1 | 0 |
| interaction_context_superiority_guarded_v3 | recent_oos | accepted_baseline_context_preserved | 10 | 10 | 24.7253 | 3 | 0 |
| interaction_context_superiority_guarded_v3 | recent_oos | relation_cap3 | 6 | 0 | -2.6253 | 0 | 0 |
| interaction_context_superiority_guarded_v3 | recent_oos | superiority_no_replaceable_incumbent | 316 | 0 | 6.9134 | 29 | 0 |
| active_relation_cap3_reference | validation | accepted | 13 | 13 | 12.2258 | 1 | 0 |
| active_relation_cap3_reference | validation | max_positions_full | 625 | 0 | 4.8954 | 20 | 0 |
| active_relation_cap3_reference | validation | relation_concentration_cap | 17 | 0 | 2.7902 | 0 | 0 |
| interaction_context_packet_v3 | validation | accepted_context_packet | 13 | 13 | 16.9025 | 2 | 0 |
| interaction_context_packet_v3 | validation | max_positions_full | 631 | 0 | 4.7802 | 18 | 0 |
| interaction_context_packet_v3 | validation | relation_cap3 | 11 | 0 | 2.7194 | 1 | 0 |
| interaction_context_superiority_guarded_v3 | validation | accepted_baseline_context_preserved | 13 | 13 | 12.2258 | 1 | 0 |
| interaction_context_superiority_guarded_v3 | validation | superiority_no_replaceable_incumbent | 642 | 0 | 4.8396 | 20 | 0 |

### Forbidden input audit

| check_name | violation_count | pass_flag | required_value |
| --- | --- | --- | --- |
| leadership_interaction_return_used | 0 | 1 | 0 violations |
| catalyst_interaction_return_used | 0 | 1 | 0 violations |
| archetype_interaction_return_used | 0 | 1 | 0 violations |
| same_symbol_interaction_return_used | 0 | 1 | 0 violations |
| stack_interaction_return_used | 0 | 1 | 0 violations |
| stack_interaction_label_used | 0 | 1 | 0 violations |
| stack_interaction_future_price_used | 0 | 1 | 0 violations |
| allocation_return_used | 0 | 1 | 0 violations |
| symbol_blacklist_used | 0 | 1 | 0 violations |
| theme_blacklist_used | 0 | 1 | 0 violations |
| microstructure_used | 0 | 1 | 0 violations |

### Remaining blockers

- This is still research-only.
- If a non-active candidate wins, it must still survive split/OOS review, cost review, and code review before any promotion.
- If it fails, the interaction artifacts still identify which context comparisons are too weak.

## No-Background Decision-Maker Report

- What happened: the five engines now talk to each other instead of acting like isolated labels.
- Why it matters: `mixed`, `low catalyst`, and `same-symbol downgrade` are no longer treated as simple bad labels.
- Whether this changes capital readiness: no. FORBIDDEN remains.
- Plain-language next step: inspect whether the interaction candidate actually beats active cap3 without killing active cap3 winners.

## Artifact Manifest

- Inputs: Task682 stack.
- Outputs: five interaction artifacts, stack panel, simulation, accepted trades, slot qualification, equity curves, guardrail, superiority audit, forbidden audit, decision, pass/fail, manifest.
- Validation commands: `python src/backtest/build_task684_interaction_context_prediction_stack.py`; `python -m unittest tests.test_task684_interaction_context_prediction_stack`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

| gate_name | pass_flag | observed | required |
| --- | --- | --- | --- |
| five_interaction_engine_artifacts_built | 1 | columns present | all interaction columns |
| cohort_only_assignment | 1 | rows=7824 | cohort allocation rows |
| no_forbidden_assignment_inputs | 1 | violations=0 | 0 violations |
| no_global_top5_rank | 1 | absent | no global rank |
| best_beats_active_cap3 | 0 | best=10887.47, active=10887.47 | best > active |
| best_mdd_not_worse | 1 | best=-30.52, active=-30.52 | MDD not worse |
| best_preserves_active_big_winners | 1 | removed_big=0 | 0 removed |
| strategy_not_deployment_ready | 1 | research only | real capital forbidden |
