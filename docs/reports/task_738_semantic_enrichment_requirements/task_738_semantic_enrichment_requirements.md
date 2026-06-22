# Task738 Semantic Enrichment Requirements

## Decision Summary

- Verdict: `SEMANTIC_ENRICHMENT_REQUIREMENTS_BUILT_REVIEW_ONLY`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Backtest permission: `FAIL`
- Requirements: 4101
- Covered bundles: 235
- Requirement families: 13
- Resolver targets: 12
- High review lane rows: 86
- Normal review lane rows: 4015

## Quant Expert Report

Task738 converts Task737 `semantic_enrichment_needed` bundles into circuit-specific enrichment requirements. It does not create scores, ranks, buy/sell signals, actionability, allocation, or backtest eligibility. The output is a work contract for upstream extractors and semantic resolvers.

### Requirement Family Distribution

| circuit_type | requirement_family | review_lane | requirement_count | bundle_count | source_event_count | can_affect_confidence_count | can_affect_risk_count | can_affect_slot_count | operating_catalyst_created_count | backtest_eligible_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| form4_insider_behavior | form4_plan_pattern_enrichment | normal_review_lane | 1910 | 183 | 565 | 0 | 1910 | 0 | 0 | 0 |
| ownership_float_structure | ownership_change_enrichment | normal_review_lane | 1253 | 174 | 451 | 0 | 1253 | 1253 | 0 | 0 |
| form4_insider_behavior | form4_context_only_trace | normal_review_lane | 600 | 115 | 285 | 0 | 0 | 0 | 0 | 0 |
| activist_control | activist_ownership_change_enrichment | normal_review_lane | 211 | 112 | 69 | 0 | 211 | 211 | 0 | 0 |
| financial_results_guidance | financial_results_expectation_enrichment | high_review_lane | 30 | 30 | 16 | 0 | 30 | 0 | 0 | 0 |
| governance_management | governance_management_change_enrichment | high_review_lane | 28 | 28 | 16 | 0 | 28 | 0 | 0 | 0 |
| activist_control | activist_control_intent_enrichment | high_review_lane | 24 | 22 | 5 | 24 | 24 | 24 | 0 | 0 |
| activist_control | passive_ownership_context | normal_review_lane | 19 | 19 | 7 | 0 | 0 | 19 | 0 | 0 |
| macro_policy_transmission | macro_company_link_enrichment | normal_review_lane | 10 | 10 | 3 | 0 | 0 | 10 | 0 | 0 |
| form4_insider_behavior | form4_transaction_code_enrichment | normal_review_lane | 6 | 6 | 3 | 0 | 6 | 0 | 0 | 0 |
| generic_8k_classifier | generic_8k_item_classifier_enrichment | normal_review_lane | 5 | 5 | 3 | 0 | 5 | 0 | 0 | 0 |
| credit_financing | financing_terms_enrichment | high_review_lane | 4 | 4 | 2 | 0 | 4 | 0 | 0 | 0 |
| governance_management | governance_compensation_context | normal_review_lane | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |

### Resolver Targets

| resolver_target_state | review_lane | requirement_count | bundle_count | requirement_family_set | circuit_type_set | backtest_eligible_count |
| --- | --- | --- | --- | --- | --- | --- |
| insider_pattern_needed | normal_review_lane | 1910 | 183 | form4_plan_pattern_enrichment | form4_insider_behavior | 0 |
| ownership_change_needed | normal_review_lane | 1253 | 174 | ownership_change_enrichment | ownership_float_structure | 0 |
| insider_context_only | normal_review_lane | 600 | 115 | form4_context_only_trace | form4_insider_behavior | 0 |
| activist_ownership_change_needed | normal_review_lane | 211 | 112 | activist_ownership_change_enrichment | activist_control | 0 |
| results_denominator_needed | high_review_lane | 30 | 30 | financial_results_expectation_enrichment | financial_results_guidance | 0 |
| governance_quality_needed | high_review_lane | 28 | 28 | governance_management_change_enrichment | governance_management | 0 |
| control_intent_review | high_review_lane | 24 | 22 | activist_control_intent_enrichment | activist_control | 0 |
| passive_ownership_context | normal_review_lane | 19 | 19 | passive_ownership_context | activist_control | 0 |
| macro_company_link_needed | normal_review_lane | 10 | 10 | macro_company_link_enrichment | macro_policy_transmission | 0 |
| insider_transaction_pattern_needed | normal_review_lane | 6 | 6 | form4_transaction_code_enrichment | form4_insider_behavior | 0 |
| generic_8k_route_needed | normal_review_lane | 5 | 5 | generic_8k_item_classifier_enrichment | generic_8k_classifier | 0 |
| financing_terms_needed | high_review_lane | 4 | 4 | financing_terms_enrichment | credit_financing | 0 |
| governance_quality_needed | normal_review_lane | 1 | 1 | governance_compensation_context | governance_management | 0 |

### Review Lanes

| review_lane | circuit_type | requirement_count | bundle_count | review_lane_is_trading_priority_flag | backtest_eligible_count |
| --- | --- | --- | --- | --- | --- |
| high_review_lane | financial_results_guidance | 30 | 30 | 0 | 0 |
| high_review_lane | governance_management | 28 | 28 | 0 | 0 |
| high_review_lane | activist_control | 24 | 22 | 0 | 0 |
| high_review_lane | credit_financing | 4 | 4 | 0 | 0 |
| normal_review_lane | form4_insider_behavior | 2516 | 211 | 0 | 0 |
| normal_review_lane | ownership_float_structure | 1253 | 174 | 0 | 0 |
| normal_review_lane | activist_control | 230 | 113 | 0 | 0 |
| normal_review_lane | macro_policy_transmission | 10 | 10 | 0 | 0 |
| normal_review_lane | generic_8k_classifier | 5 | 5 | 0 | 0 |
| normal_review_lane | governance_management | 1 | 1 | 0 | 0 |

### Coverage

| scope | bundle_count | expected_source_modifier_count | translation_row_count | requirement_row_count | coverage_state | used_for_trading_flag |
| --- | --- | --- | --- | --- | --- | --- |
| task737_semantic_enrichment_needed_bundles | 235 | 4101 | 4101 | 4101 | all_enrichment_bundles_have_requirement_objects | 0 |

### Guardrail

| gate | pass_flag | observed | expected |
| --- | --- | --- | --- |
| all_enrichment_bundles_covered | 1 | bundles=235 | 235 |
| all_source_modifiers_have_requirements | 1 | rows=4101 | 4101 |
| required_fields_present | 1 | rows=0 | 0 |
| review_lane_not_trading_priority | 1 | rows=0 | 0 |
| no_forbidden_score_rank_trade_columns | 1 | checked | no score/rank/buy/sell/PnL/return columns |
| no_actionability_or_backtest_flags | 1 | rows=0 | 0 |
| unknown_not_adverse | 1 | rows=0 | 0 |
| context_circuits_do_not_create_operating_catalyst | 1 | rows=0 | 0 |
| resolver_targets_present | 1 | targets=12 | >=8 |

### GPT Review

| review_scope | status | summary | applied_to_code_flag | gpt_is_source_of_truth_flag |
| --- | --- | --- | --- | --- |
| overall_brain_strategy_review | EXISTING_TAB_CAPTURED | Institutional GPT review passed Task738 direction as SemanticModifier to EnrichmentRequirement to ResolverTarget to ReviewLane. It explicitly rejected score, rank, buy, sell, and backtest conversion. | 1 | 0 |
| circuit_detail_review | EXISTING_TAB_CAPTURED | GPT specified circuit-specific primitive facts, denominators, comparators, timing checks, interaction fields, resolver targets, review lanes, and guardrails for Form4, 13D/13G, 13F, ownership, generic 8-K, financing, M&A, macro, financial results, and governance. | 1 | 0 |

## No-Background Decision-Maker Report

Task737 showed that 235 candidate bundles had attached information but insufficient interpreted facts. Task738 turns those gaps into exact extractor requirements: what fact to read, what denominator to compare against, what timing check is needed, and which resolver should handle it. This is still research infrastructure, not a trading rule.

## Artifact Manifest

- `task738_enrichment_requirements.csv/jsonl`
- `task738_requirement_family_distribution.csv`
- `task738_resolver_targets.csv/jsonl`
- `task738_review_lane_assignment.csv`
- `task738_missing_primitive_matrix.csv`
- `task738_denominator_requirement_matrix.csv`
- `task738_interaction_requirement_edges.csv/jsonl`
- `task738_coverage_report.csv`
- `task738_guardrail.csv`
- `task738_gpt_review_summary.csv`
- `task_738_decision.csv`
- `task_738_pass_fail_matrix.csv`

## Pass Fail Matrix

| gate | pass_flag | observed | expected |
| --- | --- | --- | --- |
| requirements_created | 1 | rows=4101 | >0 |
| family_distribution_created | 1 | rows=13 | >0 |
| resolver_targets_created | 1 | rows=13 | >0 |
| interaction_edges_created | 1 | rows=9119 | >= requirements |
| coverage_report_created | 1 | all_enrichment_bundles_have_requirement_objects | all covered |
| guardrail_all_pass | 1 | min=1 | 1 |
| backtest_permission | 0 | FAIL | semantic enrichment requirements review only |
