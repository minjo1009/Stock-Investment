# Task727 Economic Interaction Brain Contract

## Decision Summary

- Verdict: `ECONOMIC_INTERACTION_BRAIN_CONTRACT_DEFINED_EXISTING_BRAIN_FAILS`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Backtest permission: `FAIL`
- Critical/blocker gaps: 4

## Quant Expert Report

Task712-720 contains useful layer names, but the current economic brain does not yet meet the user's firm-grade interaction requirement. It promotes co-occurring counts into states such as revenue acceleration or revenue-margin reinforcement without source-backed denominators, guidance surprise, margin effect, contract duration, financing use-of-proceeds, or price acceptance as prerequisites.

### Brain Gap Audit

| task_layer | observed_problem | observed_value | firm_grade_requirement | gap_severity | contract_pass_flag |
| --- | --- | --- | --- | --- | --- |
| Task712 translator context | uses event-count axes as if they were economic meaning | customer_event_count_sum=3057; revenue_backlog_event_count_sum=4192; guidance_margin_event_count_sum=2777; supply_demand_event_count_sum=3090 | primitive facts must be tied to denominators, surprise, duration, margin, customer quality, and source provenance | HIGH | 0 |
| Task714 economic transmission | strong state names are created from count co-occurrence | no_economic_claim_source_gap=2820; revenue_margin_reinforcing=860; policy_demand_tailwind_with_company_link=676; capital_need_overhang_vs_growth_question=358; no_clear_economic_path=242 | economic transmission requires order size versus revenue/guidance/backlog, margin effect, funding quality, and expectation delta | CRITICAL | 0 |
| Task720 watch interaction | interaction axes exist but cashflow/economic axis inherits polluted upstream counts | financing_noise_with_rank_ok_but_no_cashflow_bridge=113; rank_first_but_financing_price_bridge_unresolved=99; financing_noise_with_cluster_check_bridge=78; financing_noise_with_weak_cohort_bridge=38; company_cashflow_vs_unabsorbed_financing_bridge=17 | interaction graph must consume certified economic interpretation objects, not legacy count-derived labels | CRITICAL | 0 |
| Task726 parser repair impact | after source repair almost no clean economic evidence remains | clean_economic_events=1; task722_cashflow_ready=0 | brain must not promote legacy Task712-720 states until source packets are rebuilt with economic interaction fields | BLOCKER | 0 |
| front data extraction | raw text spans are still often filing boilerplate or SEC form snippets | </td></tr></table></td> <td class="SmallFormText">Check this box to indicate that a transaction was made pursuant to a contract, instruction or written plan for the purchase or sale of equity securities of the issuer that is intended to satisfy the affirmative defense conditions of Rule 10b5-1(c). See Instruction 10. </td> </tr> </table> <table width="100%"=73; et=iso-8859-1"><link rel="stylesheet" type="text/css" href="/css/SDR_print.css"><style type="text/css"> .fakeTextBox { border-top: 2px solid #999; border-right: 1px solid #ccc; border-bottom: 1px solid #ccc; border-left: 2px solid #999; padding: 2px; _width: 800px; height: auto; min-width: 200px; min-height: 50px; word-wrap: break-word; font-size: 0.9em; col=43; charset=UTF-8"><link rel="stylesheet" type="text/css" href="/css/SDR_print.css"><style type="text/css"> .fakeTextBox { border-top: 2px solid #999; border-right: 1px solid #ccc; border-bottom: 1px solid #ccc; border-left: 2px solid #999; padding: 2px; _width: 800px; height: auto; min-width: 200px; min-height: 50px; word-wrap: break-word; font-size: 0.9em; col=28 | extract exact operational evidence spans and preserve blocker spans separately | BLOCKER | 0 |

### Contract Layers

| contract_layer | purpose | required_fields | hard_rule | assignment_allowed_flag | backtest_allowed_before_gate_flag |
| --- | --- | --- | --- | --- | --- |
| evidence_object | raw source proof | source_family, event_ts, raw_text_path, evidence_span, blocker_span, numeric_units, provenance_hash | source lineage, as-of timestamp, and exact evidence span must be explicit | 0 | 0 |
| primitive_fact_object | atomic extracted facts | order_award, revenue, backlog, guidance, margin, supply_demand, financing_terms | facts are not trade signals and must keep unknown separate from false | 0 | 0 |
| denominator_object | scale and expectation base | revenue_run_rate, prior_guidance, consensus, backlog_base, market_cap_proxy, capacity_base | missing denominator blocks strong economic claim | 0 | 0 |
| expectation_object | surprise and revision context | raise/reaffirm/cut, prior_guidance_delta, consensus_delta, already_priced_state | reaffirmation is not positive surprise by itself | 0 | 0 |
| economic_meaning_object | business value interpretation | size_materiality, margin_effect, duration, repeatability, customer_quality, capacity_fit | requires primitive fact plus denominator or explicit source statement | 0 | 0 |
| financing_quality_object | capital structure interpretation | use_of_proceeds, dilution_risk, credit_stress, runway_extension, growth_funding | financing is not default bearish or bullish | 0 | 0 |
| interaction_edge_object | cross-factor relationship | reinforcing, offsetting, prerequisite, blocker, confidence_cap | edge must cite both source states | 0 | 0 |
| candidate_thesis_bundle | coherent thesis | base_case, upside_path, risk_path, missing_evidence, invalidation | bundle is review-only until all hard gates pass | 0 | 0 |
| slot_decision_explanation | same timestamp competition | why_this_candidate, why_not_others, cluster_risk, price_acceptance | no global rank; same-cohort only | 0 | 0 |

### Code Restructure Map

| file_path | current_function_or_surface | current_problem | required_restructure | change_status |
| --- | --- | --- | --- | --- |
| src/backtest/build_task713_717_firm_grade_trader_brain.py | revenue_path_state | count co-occurrence | build_economic_meaning_object | CONTRACT_MODULE_DEFINED_PIPELINE_NOT_PROMOTED |
| src/backtest/build_task713_717_firm_grade_trader_brain.py | margin_path_state | guidance_margin_count plus supply_count | build_margin_bridge_object | CONTRACT_MODULE_DEFINED_PIPELINE_NOT_PROMOTED |
| src/backtest/build_task713_717_firm_grade_trader_brain.py | order_backlog_path_state | revenue_backlog_count | build_order_backlog_conversion_object | CONTRACT_MODULE_DEFINED_PIPELINE_NOT_PROMOTED |
| src/backtest/build_task713_717_firm_grade_trader_brain.py | funding_path_state | financing subtype labels | build_financing_quality_object | CONTRACT_MODULE_DEFINED_PIPELINE_NOT_PROMOTED |
| src/backtest/build_task713_717_firm_grade_trader_brain.py | economic_transmission_state | state names from shallow path labels | build_interaction_edges | CONTRACT_MODULE_DEFINED_PIPELINE_NOT_PROMOTED |
| src/backtest/build_task720_watch_bucket_interaction_diagnostics.py | cashflow_evidence_axis | legacy cashflow count axis | consume candidate_thesis_bundle | CONTRACT_MODULE_DEFINED_PIPELINE_NOT_PROMOTED |
| src/backtest/build_task720_watch_bucket_interaction_diagnostics.py | layer_interaction_state | fixed if/else labels | derive typed edge graph | CONTRACT_MODULE_DEFINED_PIPELINE_NOT_PROMOTED |
| src/backtest/build_task636_full_period_content_prediction_backtest.py | score_event_text | parser hygiene only | extract primitive facts with spans and denominators | CONTRACT_MODULE_DEFINED_PIPELINE_NOT_PROMOTED |

### Institutional GPT Review

| reviewer_role | required_review_focus | gpt_review_summary | supplied_project_facts | question_for_gpt | gpt_overall_verdict | gpt_response_captured_flag | gpt_is_source_of_truth_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Goldman Sachs event-driven trader | catalyst materiality and what-is-priced discipline | event_count is not a catalyst; order size must be checked versus revenue, guidance, backlog, market cap, customer quality, duration, repeatability, and cancellation risk. | Task712-720 create strong labels from event counts; Task726 clean economic evidence nearly absent; Task722 cashflow-ready is zero | What must be added to the Economic Interaction Brain before any backtest permission? | FAIL | 1 | 0 |
| Morgan Stanley expectations strategist | guidance/revision/surprise versus consensus or prior outlook | good news is not enough; guidance raise, reaffirmation, cut, consensus delta, and prior guidance bridge must be separated. | Task712-720 create strong labels from event counts; Task726 clean economic evidence nearly absent; Task722 cashflow-ready is zero | What must be added to the Economic Interaction Brain before any backtest permission? | FAIL | 1 | 0 |
| JPMorgan credit and financing trader | use-of-proceeds, dilution, credit stress, balance-sheet relief | financing is neither bullish nor bearish by default; growth funding, survival funding, dilution, covenants, maturity, and coupon must interact with order economics. | Task712-720 create strong labels from event counts; Task726 clean economic evidence nearly absent; Task722 cashflow-ready is zero | What must be added to the Economic Interaction Brain before any backtest permission? | FAIL | 1 | 0 |
| Citadel equity L/S pod PM | same-timestamp relative slot quality and thesis/risk asymmetry | thesis must be an edge graph from order to revenue, margin, cash flow, valuation, price acceptance, peer leadership, and invalidation. | Task712-720 create strong labels from event counts; Task726 clean economic evidence nearly absent; Task722 cashflow-ready is zero | What must be added to the Economic Interaction Brain before any backtest permission? | FAIL | 1 | 0 |
| Millennium risk trader | portfolio cluster, invalidation, crowding, and drawdown containment | slot decision must account for already priced, crowded, liquidity, gap chase, volatility regime, and thesis validity before sizing or entry. | Task712-720 create strong labels from event counts; Task726 clean economic evidence nearly absent; Task722 cashflow-ready is zero | What must be added to the Economic Interaction Brain before any backtest permission? | FAIL | 1 | 0 |

## No-Background Decision-Maker Report

- 기존 뇌는 이름은 그럴듯했지만 아직 카운트 기반입니다.
- 수주/가이던스/마진/financing이 서로 얼마나 맞물리는지 보는 구조가 부족합니다.
- 앞단 source도 아직 충분하지 않습니다.
- 그래서 백테스트가 아니라 primitive fact, denominator, interaction edge를 먼저 만들어야 합니다.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| task712_720_audit_completed | PRIMARY_PASS | 1 | rows=5 | >=5 |
| existing_brain_contract_pass | NOT_ACCEPTED | 0 | min=0 | 1 |
| economic_interaction_contract_defined | PRIMARY_PASS | 1 | rows=9 | >=8 |
| required_schema_defined | PRIMARY_PASS | 1 | rows=28 | >=15 |
| interaction_edge_rulebook_defined | PRIMARY_PASS | 1 | rows=14 | >=10 |
| code_restructure_map_defined | PRIMARY_PASS | 1 | rows=8 | >=6 |
| raw_source_ready_for_backtest | NOT_ACCEPTED | 0 | min=0 | 1 |
| leakage_all_pass | PRIMARY_PASS | 1 | min=1 | 1 |
| governance_all_pass | PRIMARY_PASS | 1 | min=1 | 1 |
| economic_interaction_backtest_gate | NOT_ACCEPTED | 0 | clean_events=1;denominator_fields_present=0;contamination_count=1;interaction_objects_present=0 | clean events, denominators, zero contamination, and interaction objects |
| backtest_permission | NOT_ACCEPTED | 0 | FAIL | PASS only after source-backed interaction objects exist |

## Artifact Manifest

- `task727_brain_gap_audit.csv`
- `task727_economic_interaction_contract.csv`
- `task727_required_schema_fields.csv`
- `task727_interaction_edge_rulebook.csv`
- `task727_code_restructure_map.csv`
- `task727_raw_source_readiness_audit.csv`
- `task727_institutional_review_packet.csv`
- `task727_leakage_guardrail.csv`
- `task727_governance_audit.csv`
- `task_727_decision.csv`
- `task_727_pass_fail_matrix.csv`
- `artifact_manifest.csv`