# Task678 Active Cap3 Winner Archetype

## Decision Summary

- Verdict: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- What changed: active relation cap3 was decomposed into winner archetypes, same-symbol divergence, catalyst paths, winner preservation, slot competition, and max5 versus max10 capacity.
- Key metrics: Task639 max5 $7,639.62 / MDD -23.76%; active cap3 max5 $10,887.47 / MDD -30.52%; Task639 max10 $4,709.13 / MDD -21.97%; active cap3 max10 $3,397.55 / MDD -23.14%.
- Next action: do not add another cap until winner archetype preservation and slot competition rules are predeclared and OOS-tested.

## Quant Expert Report

### Data source and source readiness

- Inputs: Task672 current-data state axis panel, Task676 accepted trades, QQQ daily benchmark.
- Quote, trade, NBBO, and microstructure are not used.
- GPT is not used as a source of truth or an assignment input.

### Exact join keys

- Portfolio replay uses `lifecycle_id`, `entry_ts`, and existing `simulated_exit_ts`.
- Winner preservation compares accepted-trade sets by `lifecycle_id`.
- Slot competition merges allocation rows back to the candidate panel by `lifecycle_id` only.

### Leakage audit

- Archetype, catalyst path, capacity, and slot logic use entry-time/current panel columns only.
- Return fields are evaluation-only and marked with `return_used_in_assignment_flag=0`.
- Labels, future price, symbol blacklist, and theme blacklist are not used.

### Split/OOS metrics

| candidate_name | split_name | max_positions | initial_capital_usd | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct | entry_reduce_failure_rate | qqq_final_capital_usd | beats_qqq_flag | diagnostic_only_flag | return_used_in_assignment_flag | label_used_in_assignment_flag | future_price_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| active_relation_cap3_reference | all | 5 | 1000.0000 | 1621 | 51 | 10887.4747 | 988.7475 | -30.5249 | 0.3333 | 1606.8278 | 1 | 0 | 0 | 0 | 0 |
| baseline_task639 | all | 5 | 1000.0000 | 1621 | 54 | 7639.6203 | 663.9620 | -23.7557 | 0.3519 | 1606.8278 | 1 | 0 | 0 | 0 | 0 |
| baseline_task639_max10 | all | 10 | 1000.0000 | 1621 | 101 | 4709.1285 | 370.9129 | -21.9743 | 0.3564 | 1606.8278 | 1 | 1 | 0 | 0 | 0 |
| active_relation_cap3_max10 | all | 10 | 1000.0000 | 1621 | 91 | 3397.5511 | 239.7551 | -23.1449 | 0.3626 | 1606.8278 | 1 | 1 | 0 | 0 | 0 |
| active_relation_cap3_reference | recent_oos | 5 | 1000.0000 | 332 | 10 | 1541.4395 | 54.1439 | -1.0958 | 0.2000 | 1124.1928 | 1 | 0 | 0 | 0 | 0 |
| baseline_task639 | recent_oos | 5 | 1000.0000 | 332 | 10 | 1531.9029 | 53.1903 | -0.8114 | 0.1000 | 1124.1928 | 1 | 0 | 0 | 0 | 0 |
| active_relation_cap3_max10 | recent_oos | 10 | 1000.0000 | 332 | 22 | 1390.3791 | 39.0379 | -3.4776 | 0.2727 | 1124.1928 | 1 | 1 | 0 | 0 | 0 |
| baseline_task639_max10 | recent_oos | 10 | 1000.0000 | 332 | 23 | 1370.9685 | 37.0968 | -3.7963 | 0.3043 | 1124.1928 | 1 | 1 | 0 | 0 | 0 |
| active_relation_cap3_reference | validation | 5 | 1000.0000 | 655 | 13 | 1327.5223 | 32.7522 | -5.8669 | 0.1538 | 1049.9083 | 1 | 0 | 0 | 0 | 0 |
| active_relation_cap3_max10 | validation | 10 | 1000.0000 | 655 | 26 | 1202.1157 | 20.2116 | -8.5711 | 0.2692 | 1049.9083 | 1 | 1 | 0 | 0 | 0 |
| baseline_task639 | validation | 5 | 1000.0000 | 655 | 15 | 1069.2313 | 6.9231 | -7.3633 | 0.4000 | 1049.9083 | 1 | 0 | 0 | 0 | 0 |
| baseline_task639_max10 | validation | 10 | 1000.0000 | 655 | 28 | 1010.8721 | 1.0872 | -5.4059 | 0.4286 | 1049.9083 | 0 | 1 | 0 | 0 | 0 |

### Winner archetype study

| winner_archetype | trade_count | avg_return_costed_pct_eval_only | median_return_costed_pct_eval_only | total_return_costed_pct_eval_only | win_rate_eval_only | big_winner_count_eval_only | failure_count_eval_only | return_used_in_assignment_flag | label_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| explosive_fragile_continuation | 3 | 148.5916 | 210.6111 | 445.7747 | 0.6667 | 2 | 1 | 0 | 0 |
| late_extended_breakout | 14 | 30.7649 | 33.1727 | 430.7087 | 0.7143 | 4 | 3 | 0 | 0 |
| theme_rotation_or_narrow_leader | 6 | 69.7286 | 45.2646 | 418.3716 | 1.0000 | 2 | 0 | 0 | 0 |
| medium_signal_continuation | 3 | 101.9099 | 50.2217 | 305.7298 | 1.0000 | 2 | 0 | 0 | 0 |
| steady_trend_persistence | 19 | 4.0190 | 2.0275 | 76.3612 | 0.5263 | 1 | 8 | 0 | 0 |

### Same-symbol divergence

| symbol | trade_count | best_return_costed_pct_eval_only | best_entry_ts | best_archetype | best_setup | best_relation | worst_return_costed_pct_eval_only | worst_entry_ts | worst_archetype | worst_setup | worst_relation | spread_pct_points_eval_only | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RKLB | 4 | 257.5838 | 2024-09-12 14:30:00+00:00 | explosive_fragile_continuation | fragile_setup | company_positive_confirmation_needed | 1.4104 | 2025-08-27 14:30:00+00:00 | medium_signal_continuation | medium_quality_setup | company_positive_confirmation_needed | 256.1734 | 0 |
| ASTS | 6 | 154.7198 | 2024-06-27 14:30:00+00:00 | theme_rotation_or_narrow_leader | high_quality_setup | company_price_confirmed_macro_secondary | -20.7120 | 2024-09-11 14:30:00+00:00 | catalyst_repricing_confirmed | high_quality_setup | company_price_confirmed_macro_secondary | 175.4318 | 0 |
| TER | 4 | 102.8735 | 2025-11-21 14:30:00+00:00 | catalyst_repricing_confirmed | medium_quality_setup | company_price_confirmed_macro_secondary | -2.0712 | 2026-02-19 14:30:00+00:00 | mixed_continuation | high_quality_setup | relation_reinforcing | 104.9447 | 0 |
| DDOG | 5 | 62.3931 | 2026-05-06 14:30:00+00:00 | late_extended_breakout | high_quality_setup | relation_reinforcing | -26.9740 | 2024-12-18 14:30:00+00:00 | late_extended_breakout | high_quality_setup | relation_reinforcing | 89.3671 | 0 |
| CRWD | 2 | 48.5096 | 2026-04-29 14:30:00+00:00 | late_extended_breakout | high_quality_setup | relation_reinforcing | -18.7598 | 2025-02-05 14:30:00+00:00 | steady_trend_persistence | high_quality_setup | relation_reinforcing | 67.2694 | 0 |
| GEV | 5 | 48.9252 | 2025-05-19 14:30:00+00:00 | theme_rotation_or_narrow_leader | high_quality_setup | relation_reinforcing | -12.5447 | 2026-05-14 14:30:00+00:00 | mixed_continuation | medium_quality_setup | relation_offsetting | 61.4699 | 0 |
| AMD | 2 | 65.7081 | 2026-04-20 14:30:00+00:00 | steady_trend_persistence | high_quality_setup | relation_reinforcing | 37.5290 | 2025-08-18 14:30:00+00:00 | late_extended_breakout | high_quality_setup | relation_reinforcing | 28.1792 | 0 |
| GE | 5 | 28.8165 | 2024-03-06 14:30:00+00:00 | late_extended_breakout | high_quality_setup | relation_reinforcing | 2.0275 | 2024-04-08 14:30:00+00:00 | steady_trend_persistence | research_only_setup | relation_sparse_research_only | 26.7891 | 0 |

### Catalyst path study

| catalyst_path | company_catalyst_state | relation_transmission_state | trade_count | avg_return_costed_pct_eval_only | win_rate_eval_only | big_winner_count_eval_only | failure_count_eval_only | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| supply_demand_or_backlog | multi_signal_medium_catalyst | company_positive_confirmation_needed | 13 | 59.8803 | 0.6923 | 4 | 3 | 0 |
| contract_plus_supply_or_backlog | hard_company_catalyst | company_price_confirmed_macro_secondary | 3 | 93.1617 | 0.6667 | 2 | 0 | 0 |
| contract_plus_supply_or_backlog | multi_dimension_high_quality_catalyst | company_price_confirmed_macro_secondary | 4 | 48.9839 | 0.5000 | 2 | 2 | 0 |
| contract_plus_supply_or_backlog | multi_dimension_high_quality_catalyst | relation_reinforcing | 8 | 15.6045 | 0.6250 | 2 | 3 | 0 |
| supply_demand_or_backlog | hard_company_catalyst | company_price_confirmed_macro_secondary | 1 | 102.8735 | 1.0000 | 1 | 0 | 0 |
| supply_demand_or_backlog | hard_company_catalyst | relation_reinforcing | 11 | 15.8538 | 0.6364 | 1 | 3 | 0 |
| supply_demand_or_backlog | multi_signal_medium_catalyst | relation_offsetting | 1 | 40.5971 | 1.0000 | 0 | 0 | 0 |
| contract_plus_supply_or_backlog | hard_company_catalyst | relation_sparse_research_only | 2 | 38.7465 | 1.0000 | 0 | 0 | 0 |

### Winner preservation audit

| candidate_name | active_cap3_trade_count | candidate_trade_count | removed_active_cap3_trade_count | removed_active_cap3_avg_return_pct_eval_only | removed_active_cap3_big_winner_count_eval_only | removed_active_cap3_failure_count_eval_only | winner_preservation_pass_flag | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| capacity_driver_cap2 | 51 | 48 | 34 | 31.2080 | 7 | 10 | 0 | 0 |
| action_permission_research_block | 51 | 42 | 39 | 26.6598 | 7 | 12 | 0 | 0 |
| capacity_combined_conservative | 51 | 44 | 38 | 26.3538 | 7 | 12 | 0 | 0 |
| capacity_theme_cap2 | 51 | 44 | 29 | 28.9897 | 6 | 12 | 0 | 0 |
| capacity_relation_cap2 | 51 | 51 | 27 | 25.7452 | 6 | 10 | 0 | 0 |
| capacity_fragile_cap1 | 51 | 54 | 28 | 21.5432 | 5 | 7 | 0 | 0 |
| baseline_task639 | 51 | 54 | 25 | 21.4422 | 5 | 8 | 0 | 0 |
| setup_slot_priority_research_block | 51 | 50 | 26 | 16.1696 | 3 | 11 | 0 | 0 |

### Slot competition study

| candidate_name | max_positions | entry_ts | candidate_count_at_ts | accepted_count_at_ts | blocked_count_at_ts | accepted_avg_return_pct_eval_only | blocked_avg_return_pct_eval_only | blocked_big_winner_count_eval_only | blocked_failure_count_eval_only | max_positions_full_blocks | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| active_relation_cap3_max10 | 10 | 2025-06-13 14:30:00+00:00 | 17 | 0 | 17 | 0.0000 | 24.0649 | 4 | 2 | 17 | 0 |
| active_relation_cap3_reference | 5 | 2025-06-13 14:30:00+00:00 | 17 | 0 | 17 | 0.0000 | 24.0649 | 4 | 2 | 17 | 0 |
| baseline_task639 | 5 | 2025-06-13 14:30:00+00:00 | 17 | 0 | 17 | 0.0000 | 24.0649 | 4 | 2 | 17 | 0 |
| baseline_task639_max10 | 10 | 2025-06-13 14:30:00+00:00 | 17 | 0 | 17 | 0.0000 | 24.0649 | 4 | 2 | 17 | 0 |
| active_relation_cap3_max10 | 10 | 2025-05-15 14:30:00+00:00 | 25 | 0 | 25 | 0.0000 | 23.1744 | 3 | 0 | 25 | 0 |
| active_relation_cap3_reference | 5 | 2025-05-15 14:30:00+00:00 | 25 | 0 | 25 | 0.0000 | 23.1744 | 3 | 0 | 25 | 0 |
| baseline_task639 | 5 | 2025-05-15 14:30:00+00:00 | 25 | 0 | 25 | 0.0000 | 23.1744 | 3 | 0 | 25 | 0 |
| baseline_task639_max10 | 10 | 2025-05-15 14:30:00+00:00 | 25 | 0 | 25 | 0.0000 | 23.1744 | 3 | 0 | 25 | 0 |

### Max10 delta

| bucket | trade_count | avg_return_costed_pct_eval_only | win_rate_eval_only | big_winner_count_eval_only | failure_count_eval_only | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- |
| common | 30 | 50.2582 | 0.7333 | 9 | 5 | 0 |
| added_by_max10 | 61 | 0.5790 | 0.4918 | 0 | 19 | 0 |
| removed_by_max10 | 21 | 10.9984 | 0.5238 | 3 | 10 | 0 |

### Cost/slippage stress

- The replay preserves the existing 50 bps cost treatment from Task673-677.
- No new exit, hold period, timing, or slippage override is introduced.

### Remaining blockers

- The winner archetype taxonomy is diagnostic and not yet a trading rule.
- Max10 is a capacity probe, not a deployment recommendation.
- Promotion requires predeclared rules, split/OOS validation, leakage audit, and cost stress.

## No-Background Decision-Maker Report

- What happened: active cap3 was returned to the center and decomposed by how winners are made, not by how losses can be capped.
- Why it matters: prior conservative layers likely damaged the few trades that created most of the profit.
- Whether this changes capital readiness: no. It remains NOT_ACCEPTED and FORBIDDEN for real capital.
- Plain-language next step: preserve the big-winner patterns first, then design risk control around not killing those winners.

## Artifact Manifest

- Inputs: Task672 panel, Task676 accepted trades, QQQ benchmark.
- Outputs: all CSVs in this directory plus `artifact_manifest.csv`.
- Validation commands: `python -m unittest tests.test_task678_active_cap3_winner_archetype`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

| gate_name | pass_flag | observed | required |
| --- | --- | --- | --- |
| winner_archetype_study_built | 1 | rows=7 | winner archetype rows |
| same_symbol_divergence_built | 1 | rows=11 | same symbol divergence rows |
| catalyst_path_study_built | 1 | rows=14 | catalyst path rows |
| winner_preservation_audit_built | 1 | rows=10 | preservation rows |
| slot_competition_study_built | 1 | rows=840 | slot competition rows |
| max10_comparison_built | 1 | max10 present | active cap3 max10 |
| max10_beats_active_cap3_max5_return | 0 | max10=3397.55, max5=10887.47 | max10 final greater than max5 |
| max10_mdd_not_worse_than_active_cap3_max5 | 1 | max10=-23.14, max5=-30.52 | max10 MDD not worse |
| strategy_accepted | 0 | research only | promotion gates require new predeclared rules and OOS validation |
