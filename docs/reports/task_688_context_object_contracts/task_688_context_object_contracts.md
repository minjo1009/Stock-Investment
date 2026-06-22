# Task688 Context Object Contracts

## Decision Summary

- Verdict: CONTEXT_OBJECT_CONTRACTS_BUILT_NO_TRADING_PROMOTION.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Key metrics: candidates 1621, evidence objects 12968, interpretation objects 9726, state edges 9726, bundles 1621, slot explanations 1621.
- What changed: created the five-layer context contract before any new return test.
- Next action: Review object quality by layer, then improve economic interpretation and edges before another allocation backtest.

## Quant Expert Report

### Data source and source readiness

Input is Task684 interaction stack keyed by `lifecycle_id`, `symbol`, `entry_ts`, `theme_id`, and `split_name`. This task creates no inferred lifecycle match and no new source fallback.

### Exact join keys

- Evidence, interpretation, edge, bundle, and slot explanation objects all retain `lifecycle_id`.
- Candidate-level bundle and slot explanation are one row per `lifecycle_id`.
- Macro remains diagnostic-only and cannot grant slot authority.

### Leakage audit

- Object contracts exclude PnL/outcome columns.
- All object layers set outcome/future/label usage flags to zero.
- This task does not run a backtest, compare returns, or promote a strategy.

### Five-layer contract

1. Evidence object: stores source facts and assignment authority.
2. Economic interpretation object: translates evidence into direction, magnitude proxy, duration, directness, surprise proxy, priced-in risk, and confidence.
3. State graph edge: records reinforcing, offsetting, prerequisite, diagnostic, or sizing-modifier relationships.
4. Candidate context bundle: combines ex-ante objects per lifecycle and marks missing/diagnostic/pending evidence.
5. Slot decision explanation: explains candidate role, slot claim, risk basis, and replacement hurdle without using outcomes.

### Evidence summary

| evidence_type | authority_scope | source_quality | row_count |
| --- | --- | --- | --- |
| chart_price_volume | assignment_certified | certified | 1621 |
| company_source_event_presence | assignment_certified | certified | 1621 |
| content_interpretation_signals | assignment_certified | certified | 1621 |
| macro_context_diagnostic | diagnostic_only | diagnostic_available | 1621 |
| market_context | assignment_certified | certified | 1621 |
| microstructure_pending | raw_pending_not_assignment | raw_pending | 1621 |
| portfolio_slot_capacity | assignment_certified | certified | 1621 |
| theme_market_leadership | assignment_certified | certified | 1621 |

### Edge summary

| from_node | to_node | edge_type | authority_scope | row_count |
| --- | --- | --- | --- | --- |
| company_catalyst | price_acceptance | confirmation_required | assignment_certified | 1210 |
| company_catalyst | price_acceptance | prerequisite_unproven | assignment_certified | 13 |
| company_catalyst | price_acceptance | reinforcing | assignment_certified | 398 |
| company_catalyst | relation_transmission | confirmation_required | assignment_certified | 560 |
| company_catalyst | relation_transmission | prerequisite_unproven | assignment_certified | 464 |
| company_catalyst | relation_transmission | prerequisite_unproven | research_only | 134 |
| company_catalyst | relation_transmission | reinforcing | research_only | 463 |
| macro_context | market_context | diagnostic_context | diagnostic_only | 1621 |
| market_context | theme_leadership | confirmation_required | assignment_certified | 999 |
| market_context | theme_leadership | offsetting | assignment_certified | 256 |
| market_context | theme_leadership | prerequisite_unproven | assignment_certified | 12 |
| market_context | theme_leadership | reinforcing | assignment_certified | 267 |
| market_context | theme_leadership | reinforcing_negative | assignment_certified | 87 |
| portfolio_capacity | slot_decision | reinforcing | assignment_certified | 178 |
| portfolio_capacity | slot_decision | sizing_modifier | assignment_certified | 1443 |
| theme_leadership | price_acceptance | offsetting | assignment_certified | 210 |
| theme_leadership | price_acceptance | prerequisite_unproven | assignment_certified | 68 |
| theme_leadership | price_acceptance | reinforcing | assignment_certified | 1343 |

### Slot role summary

| candidate_role | row_count |
| --- | --- |
| confirmation_required_candidate | 648 |
| normal_candidate | 156 |
| priority_candidate | 789 |
| research_only | 28 |

### Split/OOS metrics

Not applicable. This task is not a return test.

### Failure decomposition

- The object contract now makes weak layers visible instead of hiding them inside one ranking score.
- Economic interpretation still uses existing proxy fields; contract size, customer quality, backlog conversion, expectation surprise, and true priced-in analysis remain improvement targets.
- Microstructure is present only as pending evidence and is not eligible for slot assignment.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Upgrade economic interpretation content quality.
- Upgrade state graph edge logic by sector and driver.
- Add certified microstructure when raw feature builder is ready.
- Only after those changes, rerun allocation/backtest.

## No-Background Decision-Maker Report

- What happened: we stopped tuning returns and built the missing reasoning structure.
- Why it matters: now each candidate has a paper trail: evidence, meaning, relationship, bundle, and slot explanation.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: inspect which layer is weak before changing any trading rule.

## Artifact Manifest

- Inputs: `docs/reports/task_684_interaction_context_prediction_stack/task684_interaction_stack_panel.csv`.
- Outputs: evidence objects, economic interpretation objects, state graph edges, candidate bundles, slot explanations, integrity audit, decision, pass/fail, manifest.
- Row counts: evidence 12968, interpretations 9726, edges 9726, bundles 1621, slot explanations 1621.
- Validation commands: `python src/backtest/build_task688_context_object_contracts.py`; `python -m unittest tests.test_task688_context_object_contracts`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| five_layer_artifacts_present | PRIMARY_PASS | 1 | evidence_objects=12968; economic_interpretation_objects=9726; state_graph_edges=9726; candidate_context_bundles=1621; slot_decision_explanations=1621 | all five object layers must have rows |
| bundle_row_count_matches_candidates | PRIMARY_PASS | 1 | bundles=1621; candidates=1621 | one bundle per candidate lifecycle |
| slot_explanation_row_count_matches_candidates | PRIMARY_PASS | 1 | slot_explanations=1621; candidates=1621 | one slot explanation per candidate lifecycle |
| object_ids_unique | PRIMARY_PASS | 1 | object ids checked across five layers | all object ids unique inside each layer |
| no_outcome_columns_in_object_contracts | PRIMARY_PASS | 1 | none | PnL/outcome columns excluded from object contracts |
| macro_edges_are_diagnostic_only | PRIMARY_PASS | 1 | macro edges assignment eligible count=0 | macro context cannot grant slot authority until certified |
| missing_sources_not_used_as_negative | PRIMARY_PASS | 1 | evidence_missing_negative_sum=0; bundle_forbidden_sum=0 | missing source cannot become a negative signal |
| no_strategy_promotion | PRIMARY_PASS | 1 | no PnL simulation or allocation rule promotion was run | context contracts only |
