# Task735 Generic 8-K Classifier Repair

## Decision Summary

- Verdict: `GENERIC_8K_CLASSIFIER_REPAIRED_REVIEW_ONLY`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Backtest permission: `FAIL`
- Status phrase: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Generic 8-K rows: 95
- Agreement families: 8
- Operating candidates: 0
- Operating supported: 0
- Task734 prior candidates checked: 9

## Quant Expert Report

Task735 repairs the upstream generic 8-K classifier. Agreement, purchase agreement, material definitive agreement, and item 1.01 are no longer sufficient for operating support. The source remains alive, but operating permission requires agreement-family classification and operating transmission evidence.

### Agreement Family Distribution

| agreement_family_state | operating_transmission_state | permission_state | event_count | operating_candidate_count | operating_supported_count | backtest_eligible_count |
| --- | --- | --- | --- | --- | --- | --- |
| financial_results_context | no_operating_transmission | review_required | 41 | 0 | 0 | 0 |
| governance_board_context | no_operating_transmission | modifier_only | 37 | 0 | 0 | 0 |
| financing_credit_context | no_operating_transmission | review_required | 6 | 0 | 0 | 0 |
| unclassified_generic_8k_context | no_operating_transmission | review_required | 5 | 0 | 0 | 0 |
| severance_or_change_in_control_context | no_operating_transmission | modifier_only | 2 | 0 | 0 | 0 |
| strategic_investment_context | no_operating_transmission | review_required | 2 | 0 | 0 | 0 |
| compensation_award_context | no_operating_transmission | not_applicable | 1 | 0 | 0 | 0 |
| strategic_mna_context | no_operating_transmission | review_required | 1 | 0 | 0 | 0 |

### Task734 Prior Candidate Reclassification

| event_id | lifecycle_id | symbol | theme_id | entry_ts | split_name | prior_rule_id | refined_context_family | refined_permission_state | agreement_family_state | operating_transmission_state | permission_state | connection_rule_id | operating_candidate_flag | operating_supported_flag | task735_repair_state | required_next_evidence | subtype_trace | used_for_trading_flag | backtest_eligible_flag | outcome_used_for_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SEC_INTEL\|GEV\|2024-05-17\|8-K\|0001996810-24-000011 | TASK617\|GEV\|20240529T160000Z | GEV | power_grid_electrification | 2024-05-29 16:00:00+00:00 | train_design | OPERATING_LANGUAGE_8K_NEEDS_ITEM_AND_ECONOMIC_DETAIL | compensation_context | not_applicable | governance_board_context | no_operating_transmission | modifier_only | GOVERNANCE_NEVER_OPERATING | 0 | 0 | false_positive_repaired_to_non_operating_context | board, proxy, bylaw, or director-change context only | board_director_proxy_or_bylaws_language | 0 | 0 | 0 |
| SEC_INTEL\|TER\|2024-05-31\|8-K\|0001193125-24-151782 | TASK617\|TER\|20240611T143000Z | TER | industrial_automation_robotics | 2024-06-11 14:30:00+00:00 | train_design | OPERATING_LANGUAGE_8K_NEEDS_ITEM_AND_ECONOMIC_DETAIL | strategic_transaction_context | review_required | strategic_investment_context | no_operating_transmission | review_required | INVESTMENT_TRANSACTION_REVIEW_REQUIRED | 0 | 0 | false_positive_repaired_to_review_circuit | business-unit economics, strategic fit, capital allocation, and operating path | investment_or_equity_purchase_language | 0 | 0 | 0 |
| SEC_INTEL\|TER\|2024-05-31\|8-K\|0001193125-24-151782 | TASK617\|TER\|20240612T133000Z | TER | industrial_automation_robotics | 2024-06-12 13:30:00+00:00 | train_design | OPERATING_LANGUAGE_8K_NEEDS_ITEM_AND_ECONOMIC_DETAIL | strategic_transaction_context | review_required | strategic_investment_context | no_operating_transmission | review_required | INVESTMENT_TRANSACTION_REVIEW_REQUIRED | 0 | 0 | false_positive_repaired_to_review_circuit | business-unit economics, strategic fit, capital allocation, and operating path | investment_or_equity_purchase_language | 0 | 0 | 0 |
| SEC_INTEL\|RKLB\|2024-08-23\|8-K\|0001193125-24-206216 | TASK617\|RKLB\|20240828T134500Z | RKLB | aerospace_defense_space | 2024-08-28 13:45:00+00:00 | train_design | OPERATING_LANGUAGE_8K_NEEDS_ITEM_AND_ECONOMIC_DETAIL | governance_board_context | not_applicable | governance_board_context | no_operating_transmission | modifier_only | GOVERNANCE_NEVER_OPERATING | 0 | 0 | false_positive_repaired_to_non_operating_context | board, proxy, bylaw, or director-change context only | board_director_proxy_or_bylaws_language | 0 | 0 | 0 |
| SEC_INTEL\|RKLB\|2024-08-23\|8-K\|0001193125-24-206216 | TASK617\|RKLB\|20240829T134500Z | RKLB | aerospace_defense_space | 2024-08-29 13:45:00+00:00 | train_design | OPERATING_LANGUAGE_8K_NEEDS_ITEM_AND_ECONOMIC_DETAIL | governance_board_context | not_applicable | governance_board_context | no_operating_transmission | modifier_only | GOVERNANCE_NEVER_OPERATING | 0 | 0 | false_positive_repaired_to_non_operating_context | board, proxy, bylaw, or director-change context only | board_director_proxy_or_bylaws_language | 0 | 0 | 0 |
| SEC_INTEL\|RKLB\|2024-08-23\|8-K\|0001193125-24-206216 | TASK617\|RKLB\|20240904T140000Z | RKLB | aerospace_defense_space | 2024-09-04 14:00:00+00:00 | train_design | OPERATING_LANGUAGE_8K_NEEDS_ITEM_AND_ECONOMIC_DETAIL | governance_board_context | not_applicable | governance_board_context | no_operating_transmission | modifier_only | GOVERNANCE_NEVER_OPERATING | 0 | 0 | false_positive_repaired_to_non_operating_context | board, proxy, bylaw, or director-change context only | board_director_proxy_or_bylaws_language | 0 | 0 | 0 |
| SEC_INTEL\|GEV\|2024-09-10\|8-K\|0001996810-24-000078 | TASK617\|GEV\|20240911T164500Z | GEV | power_grid_electrification | 2024-09-11 16:45:00+00:00 | train_design | OPERATING_LANGUAGE_8K_NEEDS_ITEM_AND_ECONOMIC_DETAIL | governance_compensation_context | not_applicable | severance_or_change_in_control_context | no_operating_transmission | modifier_only | SEVERANCE_NEVER_OPERATING | 0 | 0 | false_positive_repaired_to_non_operating_context | severance/change-in-control terms are governance compensation context | severance_or_change_in_control_language | 0 | 0 | 0 |
| SEC_INTEL\|GEV\|2024-09-10\|8-K\|0001996810-24-000078 | TASK617\|GEV\|20240917T143000Z | GEV | power_grid_electrification | 2024-09-17 14:30:00+00:00 | train_design | OPERATING_LANGUAGE_8K_NEEDS_ITEM_AND_ECONOMIC_DETAIL | governance_compensation_context | not_applicable | severance_or_change_in_control_context | no_operating_transmission | modifier_only | SEVERANCE_NEVER_OPERATING | 0 | 0 | false_positive_repaired_to_non_operating_context | severance/change-in-control terms are governance compensation context | severance_or_change_in_control_language | 0 | 0 | 0 |
| SEC_INTEL\|RKLB\|2025-05-27\|8-K\|0001628280-25-027920 | TASK617\|RKLB\|20250604T173000Z | RKLB | aerospace_defense_space | 2025-06-04 17:30:00+00:00 | train_design | OPERATING_LANGUAGE_8K_NEEDS_ITEM_AND_ECONOMIC_DETAIL | strategic_mna_context | connection_candidate | strategic_mna_context | no_operating_transmission | review_required | MNA_REQUIRES_TRANSMISSION | 0 | 0 | mna_preserved_without_operating_support | acquired business operating transmission evidence | acquisition_merger_or_business_purchase_language | 0 | 0 | 0 |

### Guardrail

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| all_generic_8k_classified | PRIMARY_PASS | 1 | rows=95 | 95 |
| all_have_family_state | PRIMARY_PASS | 1 | checked | no blank |
| all_have_transmission_state | PRIMARY_PASS | 1 | checked | no blank |
| all_have_permission_rule | PRIMARY_PASS | 1 | checked | no blank permission/rule |
| agreement_alone_not_supported | PRIMARY_PASS | 1 | 0 | 0 |
| compensation_governance_not_operating | PRIMARY_PASS | 1 | 0 | 0 |
| financing_routed_not_operating | PRIMARY_PASS | 1 | 0 | 0 |
| task734_prior_nine_reclassified | PRIMARY_PASS | 1 | rows=9 | 9 |
| task734_prior_zero_supported | PRIMARY_PASS | 1 | 0 | 0 |
| task734_false_positives_repaired | PRIMARY_PASS | 1 | 8 | >=8 |
| trading_flags_zero | PRIMARY_PASS | 1 | trading=0,backtest=0 | 0 |

### GPT Review

| review_scope | status | summary | applied_to_code_flag | gpt_is_source_of_truth_flag |
| --- | --- | --- | --- | --- |
| overall_brain_strategy_review | EXISTING_TAB_CAPTURED | Institutional GPT review with five roles approved Task735 as an upstream generic 8-K classifier repair, not a PnL or allocation task. It said item 1.01 and material definitive agreement are classifier inputs only, not operating evidence. | 1 | 0 |
| circuit_detail_review | EXISTING_TAB_CAPTURED | GPT detail review required agreement_family_state, operating_transmission_state, permission_state, traceable rule_id, and guardrails that prevent agreement/purchase-agreement wording, governance, compensation, severance, financing, or M&A boilerplate from becoming operating-supported without explicit transmission evidence. | 1 | 0 |

## No-Background Decision-Maker Report

- Conclusion: generic 8-K agreement wording is now split before any operating claim.
- Compensation, governance, severance, financing, and investment agreement sources stay alive but do not create operating candidates.
- M&A stays as strategic review unless operating transmission is visible.
- Backtest remains blocked.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| classification_created | PRIMARY_PASS | 1 | rows=95 | 95 |
| distribution_created | PRIMARY_PASS | 1 | rows=8 | >0 |
| prior_reclass_created | PRIMARY_PASS | 1 | rows=9 | 9 |
| guardrail_all_pass | PRIMARY_PASS | 1 | min=1 | 1 |
| backtest_permission | NOT_ACCEPTED | 0 | FAIL | classifier repair only |

## Artifact Manifest

- `task735_generic_8k_classification.csv`
- `task735_agreement_family_distribution.csv`
- `task735_task734_prior_candidate_reclassification.csv`
- `task735_guardrail.csv`
- `task735_gpt_review_summary.csv`
- `task_735_decision.csv`
- `task_735_pass_fail_matrix.csv`
- `task735_generic_8k_classification.jsonl`
- `task735_task734_prior_candidate_reclassification.jsonl`
- `artifact_manifest.csv`