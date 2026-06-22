# Task728 Five Layer Interaction Logic Contract

## Decision Summary

- Verdict: `FIVE_LAYER_INTERACTION_LOGIC_CONTRACT_DEFINED_NOT_BACKTEST_READY`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Backtest permission: `FAIL`
- Observed interaction cells: 210
- Observed rule families: 12

## Quant Expert Report

Task728 corrects the Task727 weakness: it does not reduce the brain to a few keyword fields. It inventories the actual Task713-717 five-layer state axes, defines each layer's contract, creates typed interaction rule families, and assigns every observed five-layer state cell to an interaction rule candidate without using outcomes.

### Corrected Five Layer Contract

| layer | role | must_output | hard_constraint | consumer_layer | standalone_trade_signal_allowed_flag |
| --- | --- | --- | --- | --- | --- |
| L1_Evidence | source credibility and novelty filter | source credibility, directness, novelty, contamination, timestamp validity, source gap | must not claim economics; only permits or caps L2 interpretation | L2_Economic | 0 |
| L2_Economic | business transmission thesis | revenue path, margin path, backlog conversion, funding, dilution, policy demand, valuation pressure | must be capped by L1 and must declare missing denominator or contradiction | L3_Price and L5_Risk | 0 |
| L3_Price | market processing and acceptance | acceptance, incomplete pricing, already extended, overhang absorption, positioning support | confirms or challenges L2 thesis; never replaces L2 evidence | L4_Portfolio and L5_Risk | 0 |
| L4_Portfolio | same timestamp capital competition | slot leader/contender, cohort rank, theme cluster, exposure pressure | compares only candidates in the same timestamp cohort; no global rank | L5_Risk | 0 |
| L5_Risk | invalidation and budget gate | review state, invalidation condition, risk budget, sizing cap reason | final actionability is review-only until raw evidence and interaction gates pass | downstream backtest gate | 0 |

### Rule Family Catalog

| rule_family_id | layer_scope | relation_type | precondition_template | output_state_template | implementation_mode | assignment_allowed_flag | backtest_allowed_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L1_L2_GATE_001 | L1->L2 | prerequisite | source_gap or no_source_evidence blocks all positive economic transmission claims | economic_claim_source_blocked | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L1_L2_GATE_002 | L1->L2 | confidence_cap | thin or weak evidence caps revenue/margin/backlog states even when L2 has a positive path | economic_claim_capped_by_evidence | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L1_L2_GATE_003 | L1->L2 | blocker | ownership/Form4/13D/13G/13F or governance noise cannot support L2 economic claim | source_family_blocks_economic_claim | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L1_L2_CONTRA_004 | L1xL2 | offsetting | reaffirmation or stale evidence conflicts with revenue acceleration language | stale_or_reaffirmed_economic_claim | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L1_L2_CONTRA_005 | L1xL2 | confidence_cap | indirect evidence plus strong economic state requires source packet review | indirect_strong_economic_review | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L1_L2_FIN_006 | L1xL2 | escalation | financing context plus growth path requires use-of-proceeds and dilution interpretation | financing_growth_bridge_needed | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L1_L2_FIN_007 | L1xL2 | blocker | funding need with unabsorbed dilution offsets revenue or backlog path | dilution_offsets_growth_claim | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L2_L3_PRICE_008 | L2xL3 | reinforcing | economic path plus accepted price/tape proxy forms coherent thesis candidate | economic_price_reinforcing | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L2_L3_PRICE_009 | L2xL3 | prerequisite | positive economic path with incomplete acceptance requires confirmation | positive_thesis_needs_price_acceptance | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L2_L3_PRICE_010 | L2xL3 | offsetting | accepted price without clear economic path is momentum without thesis | price_without_economic_thesis | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L2_L3_PRICE_011 | L2xL3 | confidence_cap | near-high unconfirmed or extension pressure caps otherwise positive thesis | extension_caps_thesis | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L2_L5_INV_012 | L2xL5 | invalidation | economic claim must map to thesis-specific invalidation, not generic review text | thesis_specific_invalidation_required | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L2_L5_INV_013 | L2xL5 | blocker | overhang thesis invalid if follow-up price does not absorb financing | overhang_absorption_required | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L3_L4_SLOT_014 | L3xL4 | reinforcing | price accepted plus same-timestamp slot leader supports review priority | accepted_slot_leader | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L3_L4_SLOT_015 | L3xL4 | confidence_cap | price incomplete plus contender status requires cohort superiority proof | contender_needs_absorption_and_superiority | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L3_L4_SLOT_016 | L3xL4 | offsetting | accepted but clustered or extension risk limits slot claim | accepted_but_cluster_or_extension_capped | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L4_L5_RISK_017 | L4xL5 | sizing_modifier | theme cluster medium/high caps risk budget even for slot leaders | cluster_capped_budget | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L4_L5_RISK_018 | L4xL5 | blocker | no slot claim or no competition proof stays research-only | no_slot_no_budget | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L1_L2_L3_019 | L1xL2xL3 | escalation | direct company evidence + positive economics + incomplete price means watch for confirmation | direct_positive_wait_for_price | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L1_L2_L3_020 | L1xL2xL3 | reinforcing | direct strong evidence + positive economics + accepted price forms high-quality review candidate | evidence_economic_price_stack | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L1_L2_L3_021 | L1xL2xL3 | blocker | weak/noise evidence + positive economics + accepted price cannot be promoted without source repair | price_cannot_rescue_weak_source | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L2_L3_L4_022 | L2xL3xL4 | reinforcing | positive economics + accepted price + slot leader supports cohort leader review | cohort_leader_thesis_stack | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L2_L3_L4_023 | L2xL3xL4 | confidence_cap | positive economics + incomplete price + contender needs delayed confirmation | cohort_contender_delayed_confirmation | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| L2_L3_L4_024 | L2xL3xL4 | sizing_modifier | positive economics + accepted price + cluster high limits size | accepted_cluster_size_cap | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| ALL_025 | L1xL2xL3xL4xL5 | prerequisite | all positive layers still require raw source, denominator, and leakage gates | full_stack_gate_required | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| ALL_026 | L1xL2xL3xL4xL5 | blocker | any source gap or generic research-only risk state blocks backtest eligibility | full_stack_source_or_risk_block | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| ALL_027 | L1xL2xL3xL4xL5 | invalidation | final brain must cite which earlier layer would falsify the thesis | full_stack_invalidation_trace | typed_state_axes_not_one_off_if_chain | 0 | 0 |
| ALL_028 | L1xL2xL3xL4xL5 | sizing_modifier | cluster, overhang, extension, and low evidence strength jointly cap risk budget | full_stack_size_cap_trace | typed_state_axes_not_one_off_if_chain | 0 | 0 |

### Rule Coverage Audit

| rule_family_id | layer_scope | relation_type | observed_cell_count | candidate_count | coverage_status |
| --- | --- | --- | --- | --- | --- |
| L1_L2_GATE_001 | L1->L2 | prerequisite | 0 | 0 | DEFINED_NOT_OBSERVED_OR_NEEDS_NEXT_PASS |
| L1_L2_GATE_002 | L1->L2 | confidence_cap | 26 | 561 | OBSERVED_IN_CURRENT_PANEL |
| L1_L2_GATE_003 | L1->L2 | blocker | 0 | 0 | DEFINED_NOT_OBSERVED_OR_NEEDS_NEXT_PASS |
| L1_L2_CONTRA_004 | L1xL2 | offsetting | 39 | 261 | OBSERVED_IN_CURRENT_PANEL |
| L1_L2_CONTRA_005 | L1xL2 | confidence_cap | 33 | 592 | OBSERVED_IN_CURRENT_PANEL |
| L1_L2_FIN_006 | L1xL2 | escalation | 0 | 0 | DEFINED_NOT_OBSERVED_OR_NEEDS_NEXT_PASS |
| L1_L2_FIN_007 | L1xL2 | blocker | 0 | 0 | DEFINED_NOT_OBSERVED_OR_NEEDS_NEXT_PASS |
| L2_L3_PRICE_008 | L2xL3 | reinforcing | 12 | 117 | OBSERVED_IN_CURRENT_PANEL |
| L2_L3_PRICE_009 | L2xL3 | prerequisite | 26 | 214 | OBSERVED_IN_CURRENT_PANEL |
| L2_L3_PRICE_010 | L2xL3 | offsetting | 0 | 0 | DEFINED_NOT_OBSERVED_OR_NEEDS_NEXT_PASS |
| L2_L3_PRICE_011 | L2xL3 | confidence_cap | 0 | 0 | DEFINED_NOT_OBSERVED_OR_NEEDS_NEXT_PASS |
| L2_L5_INV_012 | L2xL5 | invalidation | 30 | 165 | OBSERVED_IN_CURRENT_PANEL |
| L2_L5_INV_013 | L2xL5 | blocker | 8 | 39 | OBSERVED_IN_CURRENT_PANEL |
| L3_L4_SLOT_014 | L3xL4 | reinforcing | 0 | 0 | DEFINED_NOT_OBSERVED_OR_NEEDS_NEXT_PASS |
| L3_L4_SLOT_015 | L3xL4 | confidence_cap | 0 | 0 | DEFINED_NOT_OBSERVED_OR_NEEDS_NEXT_PASS |
| L3_L4_SLOT_016 | L3xL4 | offsetting | 0 | 0 | DEFINED_NOT_OBSERVED_OR_NEEDS_NEXT_PASS |
| L4_L5_RISK_017 | L4xL5 | sizing_modifier | 5 | 9 | OBSERVED_IN_CURRENT_PANEL |
| L4_L5_RISK_018 | L4xL5 | blocker | 0 | 0 | DEFINED_NOT_OBSERVED_OR_NEEDS_NEXT_PASS |
| L1_L2_L3_019 | L1xL2xL3 | escalation | 0 | 0 | DEFINED_NOT_OBSERVED_OR_NEEDS_NEXT_PASS |
| L1_L2_L3_020 | L1xL2xL3 | reinforcing | 0 | 0 | DEFINED_NOT_OBSERVED_OR_NEEDS_NEXT_PASS |
| L1_L2_L3_021 | L1xL2xL3 | blocker | 0 | 0 | DEFINED_NOT_OBSERVED_OR_NEEDS_NEXT_PASS |
| L2_L3_L4_022 | L2xL3xL4 | reinforcing | 4 | 125 | OBSERVED_IN_CURRENT_PANEL |
| L2_L3_L4_023 | L2xL3xL4 | confidence_cap | 12 | 351 | OBSERVED_IN_CURRENT_PANEL |
| L2_L3_L4_024 | L2xL3xL4 | sizing_modifier | 3 | 11 | OBSERVED_IN_CURRENT_PANEL |
| ALL_025 | L1xL2xL3xL4xL5 | prerequisite | 0 | 0 | DEFINED_NOT_OBSERVED_OR_NEEDS_NEXT_PASS |
| ALL_026 | L1xL2xL3xL4xL5 | blocker | 12 | 2820 | OBSERVED_IN_CURRENT_PANEL |
| ALL_027 | L1xL2xL3xL4xL5 | invalidation | 0 | 0 | DEFINED_NOT_OBSERVED_OR_NEEDS_NEXT_PASS |
| ALL_028 | L1xL2xL3xL4xL5 | sizing_modifier | 0 | 0 | DEFINED_NOT_OBSERVED_OR_NEEDS_NEXT_PASS |

## No-Background Decision-Maker Report

- 결론: 이번엔 키워드 몇 개가 아니라 5개 Layer 전체 상호작용으로 다시 잡았습니다.
- Evidence가 Economic을 허용/차단하고, Economic이 Price에서 확인되고, Price와 Slot이 경쟁하며, Risk가 최종 예산과 무효화를 겁니다.
- 관측된 5-Layer 조합마다 rule family를 붙였습니다.
- 그래도 아직 백테스트는 금지입니다. 앞단 source-certified primitive fact와 denominator가 아직 없기 때문입니다.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| layer_inventory_completed | PRIMARY_PASS | 1 | rows=35 | >=25 |
| corrected_five_layer_contract_completed | PRIMARY_PASS | 1 | rows=5 | 5 |
| interaction_rule_family_catalog_completed | PRIMARY_PASS | 1 | rows=28 | >=25 |
| observed_interaction_cells_generated | PRIMARY_PASS | 1 | rows=210 | >=100 |
| rule_candidate_assignments_generated | PRIMARY_PASS | 1 | rows=210 | same as observed cells |
| relation_type_diversity | PRIMARY_PASS | 1 | unique=7 | >=5 |
| coverage_multiple_families_observed | PRIMARY_PASS | 1 | observed=12 | >=10 |
| leakage_all_pass | PRIMARY_PASS | 1 | min=1 | 1 |
| governance_all_pass | PRIMARY_PASS | 1 | min=1 | 1 |
| backtest_permission | NOT_ACCEPTED | 0 | FAIL | PASS only after source-certified primitive fact and denominator gates |

## Artifact Manifest

- `task728_layer_state_inventory.csv`
- `task728_corrected_five_layer_contract.csv`
- `task728_interaction_rule_family_catalog.csv`
- `task728_observed_five_layer_interaction_cells.csv`
- `task728_rule_candidate_assignments.csv`
- `task728_rule_coverage_audit.csv`
- `task728_dangerous_surface_audit.csv`
- `task728_gpt_institutional_review_packet.csv`
- `task728_leakage_guardrail.csv`
- `task728_governance_audit.csv`
- `task_728_decision.csv`
- `task_728_pass_fail_matrix.csv`
- `artifact_manifest.csv`