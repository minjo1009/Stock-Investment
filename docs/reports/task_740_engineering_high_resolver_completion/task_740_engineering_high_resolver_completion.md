# Task740 Engineering-High Resolver Completion

## Decision Summary

- Verdict: `ENGINEERING_HIGH_SOURCE_SEMANTIC_LAYER_CONDITIONALLY_CLOSED_REVIEW_ONLY`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Backtest permission: `FAIL`
- Engineering-high requirements: 3443
- Primitive rows: 3443
- Resolver rows: 3443
- Unresolved join blockers: 4729
- Source semantic layer: `CONDITIONALLY_CLOSED_SOURCE_ONLY`
- Economic denominator layer: `OPEN_JOIN_BLOCKED`

## Quant Expert Report

Task740 processes every Task739 engineering-high requirement through source-text primitive extraction and source-only resolver states. It explicitly preserves unresolved denominator, comparator, timing, and economic-join blockers. It does not create scores, ranks, trading actions, allocation, or backtest eligibility.

### Quality Metrics

| metric | value | unit |
| --- | --- | --- |
| engineering_high_requirement_count | 3443.0 | count |
| primitive_extraction_coverage | 1.0 | ratio |
| source_only_or_join_closed_rate | 1.0 | ratio |
| unresolved_join_needed_rate | 0.998548 | ratio |
| unknown_resolver_state_rate | 0.364508 | ratio |
| guardrail_trade_output_count | 0.0 | count |
| transaction_code_resolution_rate | 0.996868 | ratio |
| form4_10b5_1_strict_classification_rate | 0.0 | ratio |
| open_market_vs_award_split_rate | 1.0 | ratio |
| ownership_percent_extraction_rate | 0.164651 | ratio |
| active_passive_resolution_rate | 0.15793 | ratio |
| generic_8k_family_classification_rate | 1.0 | ratio |
| financing_instrument_resolution_rate | 1.0 | ratio |
| financial_guidance_language_detection_rate | 0.066667 | ratio |
| unresolved_join_blocker_count | 4729.0 | count |

### Resolver Distribution

| source_circuit | requirement_family | resolver_state | completion_state | row_count |
| --- | --- | --- | --- | --- |
| form4_insider_behavior | form4_plan_pattern_enrichment | form4_pattern_enrichment_closed_source_only | unresolved_join_needed | 1910 |
| ownership_float_structure | ownership_change_enrichment | ownership_change_unknown | unresolved_join_needed | 1243 |
| activist_control | activist_ownership_change_enrichment | passive_ownership_context | unresolved_join_needed | 202 |
| financial_results_guidance | financial_results_expectation_enrichment | financial_results_context_resolved_source_only | unresolved_join_needed | 30 |
| activist_control | activist_control_intent_enrichment | passive_ownership_context | unresolved_join_needed | 21 |
| ownership_float_structure | ownership_change_enrichment | ownership_structure_resolved_source_only | unresolved_join_needed | 10 |
| form4_insider_behavior | form4_transaction_code_enrichment | form4_transaction_code_unknown | unresolved_join_needed | 6 |
| activist_control | activist_ownership_change_enrichment | active_control_intent_review | unresolved_join_needed | 6 |
| generic_8k_classifier | generic_8k_item_classifier_enrichment | generic_8k_classified | source_only_resolved | 5 |
| activist_control | activist_ownership_change_enrichment | control_intent_unknown | unresolved_join_needed | 3 |
| activist_control | activist_control_intent_enrichment | control_intent_unknown | unresolved_join_needed | 3 |
| credit_financing | financing_terms_enrichment | growth_funding_review | unresolved_join_needed | 3 |
| credit_financing | financing_terms_enrichment | dilution_overhang_review | unresolved_join_needed | 1 |

### Completion Distribution

| completion_state | row_count | backtest_eligible_count |
| --- | --- | --- |
| unresolved_join_needed | 3438 | 0 |
| source_only_resolved | 5 | 0 |

### Guardrail

| gate | pass_flag | observed | expected |
| --- | --- | --- | --- |
| no_forbidden_columns_created | 1 | checked | no score/rank/trade/outcome columns |
| resolver_outputs_review_only | 1 | rows=0 | 0 |
| primitive_outputs_review_only | 1 | rows=0 | 0 |
| blockers_review_only | 1 | rows=0 | 0 |
| unknown_not_bearish | 1 | rows=0 | 0 |
| generic_8k_not_operating_supported_by_default | 1 | rows=0 | 0 |
| all_resolvers_have_completion_state | 1 | checked | all non-empty |

### GPT Review

| review_scope | status | summary | applied_to_code_flag | gpt_is_source_of_truth_flag |
| --- | --- | --- | --- | --- |
| overall_brain_strategy_review | EXISTING_TAB_CAPTURED | Institutional GPT review said Task740 can conditionally close the source-semantic layer by extracting available primitives, emitting source-only resolver states, and explicitly preserving denominator/join blockers. | 1 | 0 |
| circuit_detail_review | EXISTING_TAB_CAPTURED | GPT required Form4 open-market/10b5-1/award splits, ownership 13D/13G active/passive/control splits, financial results language extraction, generic 8-K routing, and financing term resolution without bullish/bearish or trade-ready outputs. | 1 | 0 |

## No-Background Decision-Maker Report

The source-semantic part is now conditionally closed for engineering-high circuits. The code can read available raw text and separate Form4, ownership, 13D/13G, financing, 8-K, and results/guidance states. What remains open is the economic denominator layer: holdings history, float, market cap, cash/debt, prior guidance, consensus, and price absorption.

## Artifact Manifest

- `task740_extracted_primitives.csv/jsonl`
- `task740_resolver_outputs.csv/jsonl`
- `task740_unresolved_join_blockers.csv/jsonl`
- `task740_quality_metrics.csv`
- `task740_resolver_distribution.csv`
- `task740_completion_distribution.csv`
- `task740_coverage_report.csv`
- `task740_guardrail.csv`
- `task740_gpt_review_summary.csv`
- `task_740_decision.csv`
- `task_740_pass_fail_matrix.csv`

## Pass Fail Matrix

| gate | pass_flag | observed | expected |
| --- | --- | --- | --- |
| engineering_high_requirements_processed | 1 | trace=3443, primitives=3443, resolvers=3443 | all equal |
| coverage_report_created | 1 | all_engineering_high_requirements_processed | all processed |
| quality_metrics_created | 1 | rows=15 | >=8 |
| unresolved_join_blockers_created | 1 | rows=4729 | >0 |
| completion_states_valid | 1 | source_only_resolved\|unresolved_join_needed | valid states |
| guardrail_all_pass | 1 | min=1 | 1 |
| backtest_permission | 0 | FAIL | source semantic closure only |
