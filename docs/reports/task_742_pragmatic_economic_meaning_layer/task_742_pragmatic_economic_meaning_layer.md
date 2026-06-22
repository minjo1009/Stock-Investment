# Task742 Pragmatic Economic Meaning Layer

## Decision Summary

- Verdict: `PRAGMATIC_ECONOMIC_MEANING_LAYER_BUILT_REVIEW_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Backtest permission: `FAIL`
- Output packets: 3443
- Relation-ready review packets: 2159
- Directional edge candidates: 4
- Structural mixed edge candidates: 231
- Context-only attachments: 1924
- Hard blockers: 0
- Soft uncertainty packets: 2689

## Quant Expert Report

Task742 supersedes the Task741 blocker-heavy interpretation for economic meaning review. It does not delete Task741 denominators. It reclassifies unavailable high-grade sources as soft uncertainty unless the row lacks primitive identity, raw source trace, or as-of safety. Available source primitives, SEC companyfacts, and as-of price context are used to create direction hints, confidence bands, ambiguity flags, needed confirmations, and relation-readiness tiers. Directional, structural mixed, and context-only packets are separated so neutral or unknown rows cannot become directional edges. These are research objects only, not trade instructions.

### Quality Metrics

| metric | value | unit |
| --- | --- | --- |
| packet_count | 3443.0 | count |
| relation_ready_count | 2159.0 | count |
| relation_ready_rate | 0.627069 | ratio |
| usable_without_missing_source_count | 2159.0 | count |
| usable_without_missing_source_rate | 0.627069 | ratio |
| hard_blocker_count | 0.0 | count |
| soft_uncertainty_count | 2689.0 | count |
| directional_edge_candidate_count | 4.0 | count |
| structural_edge_candidate_count | 231.0 | count |
| context_attachment_only_count | 1924.0 | count |
| not_ready_tier_count | 1284.0 | count |
| positive_hint_count | 3.0 | count |
| negative_hint_count | 1.0 | count |
| mixed_hint_count | 248.0 | count |
| neutral_hint_count | 1935.0 | count |
| unknown_hint_count | 1256.0 | count |
| trade_output_violation_count | 0.0 | count |

### Interpretation Distribution

| source_circuit | interpretation_state | economic_direction_hint | confidence_band | relation_ready_tier | row_count | relation_ready_count | hard_blocker_count | directional_edge_candidate_count | structural_edge_candidate_count | context_attachment_only_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| form4_insider_behavior | form4_sale_plan_or_compensation_context | neutral | medium | context_only | 1910 | 1910 | 0 | 0 | 0 | 1910 |
| ownership_float_structure | ownership_market_scale_context_only | unknown | low | not_ready | 620 | 0 | 0 | 0 | 0 | 0 |
| ownership_float_structure | ownership_context_too_thin | unknown | low | not_ready | 606 | 0 | 0 | 0 | 0 | 0 |
| activist_control | ownership_active_control_context | mixed | medium | structural_mixed | 231 | 231 | 0 | 0 | 231 | 0 |
| financial_results_guidance | financial_results_source_only_context | unknown | low | not_ready | 30 | 0 | 0 | 0 | 0 | 0 |
| ownership_float_structure | ownership_active_control_context | mixed | low | not_ready | 17 | 0 | 0 | 0 | 0 | 0 |
| ownership_float_structure | ownership_percent_source_context | neutral | medium | context_only | 10 | 10 | 0 | 0 | 0 | 10 |
| form4_insider_behavior | form4_non_directional_insider_context | neutral | low | not_ready | 6 | 0 | 0 | 0 | 0 | 0 |
| generic_8k_classifier | generic_8k_non_operating_context | neutral | low | not_ready | 5 | 0 | 0 | 0 | 0 | 0 |
| activist_control | ownership_passive_large_holder_context | neutral | medium | context_only | 4 | 4 | 0 | 0 | 0 | 4 |
| credit_financing | financing_growth_funding_size_known | positive | medium | directional | 3 | 3 | 0 | 3 | 0 | 0 |
| credit_financing | financing_dilution_overhang_size_known | negative | medium | directional | 1 | 1 | 0 | 1 | 0 | 0 |

### Blocker Reclassification

| task741_blocker_state | source_circuit | task742_reclassification | row_count | relation_ready_count | usable_without_missing_source_count |
| --- | --- | --- | --- | --- | --- |
| exact_person_history_missing | form4_insider_behavior | soft_uncertainty | 1916 | 1910 | 1910 |
| insider_total_holdings_missing | form4_insider_behavior | soft_uncertainty | 1916 | 1910 | 1910 |
| free_float_missing | ownership_float_structure | soft_uncertainty | 1253 | 10 | 10 |
| prior_holder_percent_missing | ownership_float_structure | soft_uncertainty | 1253 | 10 | 10 |
| ownership_percent_missing | ownership_float_structure | soft_uncertainty | 1243 | 0 | 0 |
| prior_holder_percent_missing | activist_control | soft_uncertainty | 235 | 235 | 235 |
| free_float_missing | activist_control | soft_uncertainty | 235 | 235 | 235 |
| prior_guidance_database_missing | financial_results_guidance | soft_uncertainty | 30 | 0 | 0 |
| consensus_estimates_missing | financial_results_guidance | soft_uncertainty | 30 | 0 | 0 |
| ownership_after_missing | form4_insider_behavior | not_used_in_pragmatic_judgment | 6 | 0 | 0 |
| dilution_terms_incomplete | credit_financing | soft_uncertainty | 1 | 1 | 1 |

### Guardrail

| gate | pass_flag | observed | expected |
| --- | --- | --- | --- |
| no_forbidden_columns_created | 1 | checked | no forbidden output columns |
| no_trade_score_backtest_outputs | 1 | rows=0 | 0 |
| missing_not_converted_to_hard_blocker | 1 | rows=0 | 0 |
| identity_trace_present | 1 | rows=0 | 0 |
| direction_hint_domain_valid | 1 | rows=0 | 0 |
| neutral_unknown_no_directional_edge | 1 | rows=0 | 0 |
| directional_tier_positive_negative_only | 1 | rows=0 | 0 |
| asof_snapshot_change_inference_forbidden | 1 | rows=0 | 0 |
| direction_hint_not_trade_instruction | 1 | rows=0 | 0 |
| relation_ready_is_review_only | 1 | backtest_eligible_sum=0 | 0 |

### GPT Review

| review_scope | status | summary | applied_to_code_flag | gpt_is_source_of_truth_flag |
| --- | --- | --- | --- | --- |
| pragmatic_available_data_economic_meaning_redesign | CHROME_GPT_INSTITUTIONAL_REVIEW_REQUESTED_AND_APPLIED | Task742 follows the institutional review prompt and follow-up GPT panel critique: keep unavailable high-grade sources as uncertainty, not blanket blockers; split relation readiness into directional, structural mixed, context-only, and not-ready tiers; forbid treating direction hints as trades; and forbid change inference from as-of snapshots. | 1 | 0 |

## No-Background Decision-Maker Report

Task741 was too strict: too many rows became blocker-heavy even when current data still allowed a useful economic read. Task742 keeps missing data visible, but it does not let missing perfect data kill every judgment. The result is still not a buy/sell model. It is a cleaner bridge into the relation engine.

## Artifact Manifest

- `task742_pragmatic_economic_meaning_packets.csv/jsonl`
- `task742_quality_metrics.csv`
- `task742_interpretation_distribution.csv`
- `task742_blocker_reclassification.csv`
- `task742_guardrail.csv`
- `task742_gpt_review_summary.csv`
- `task_742_decision.csv`
- `task_742_pass_fail_matrix.csv`

## Pass Fail Matrix

| gate | pass_flag | observed | expected |
| --- | --- | --- | --- |
| all_task741_packets_reinterpreted | 1 | task741=3443, task742=3443 | equal |
| some_relation_ready_packets_created | 1 | rows=2159 | >0 |
| relation_ready_tier_created | 1 | tiers=4 | >=3 |
| neutral_unknown_not_directional | 1 | checked | 0 rows |
| hard_blockers_not_dominant | 1 | rate=0.000000 | <0.05 |
| guardrail_all_pass | 1 | min=1 | 1 |
| backtest_permission | 0 | FAIL | pragmatic meaning packets are review-only |
