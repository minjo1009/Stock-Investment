# Task686 Source Certification Contract Repair

## Decision Summary

- Verdict: DATA_INFRASTRUCTURE_REPAIR_COMPLETE_STRATEGY_NOT_PROMOTED.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Key metrics: source-gap rows 0/1621, allocation-ready rows 1621/1621, macro-certified rows 0, macro-used rows 0, guarded challenger accepted rows 0.
- What changed: Task661 now separates company/content/theme-price/macro/relation/portfolio certification; Task672 no longer collapses certified company rows into source-gap; Task684 allocation preserves provenance columns.
- Next action: Develop conditional displacement hurdle after source certification repair, without using macro provisional as certified.

## Quant Expert Report

### Data source and source readiness

Task686 repairs the source-certification contract. Macro remains provisional and is not used for assignment. Company/content/theme-price certification can now create partial assignment readiness.

| scope | row_count | source_gap_research_only_count | company_certified_macro_provisional_count | allocation_assignment_ready_count | company_source_certified_count | content_prediction_certified_count | theme_price_certified_count | relation_certified_count | macro_assignment_certified_count | macro_used_for_assignment_count | macro_provisional_used_as_certified_count | missing_source_used_as_negative_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| task672_core_panel | 1621 | 0 | 1621 | 1621 | 1621 | 1621 | 1621 | 1024 | 0 | 0 | 0 | 0 |
| recent_oos | 332 | 0 | 332 | 332 | 332 | 332 | 332 | 187 | 0 | 0 | 0 | 0 |
| train_design | 634 | 0 | 634 | 634 | 634 | 634 | 634 | 363 | 0 | 0 | 0 | 0 |
| validation | 655 | 0 | 655 | 655 | 655 | 655 | 655 | 474 | 0 | 0 | 0 | 0 |

### Exact join keys

- `lifecycle_id` and `entry_ts` remain the replay keys.
- Task684 allocation now carries provenance fields forward to the cohort-slot audit surface.

### Leakage audit

- Return, label, and future price flags remain zero for assignment.
- `macro_provisional_used_as_certified` is zero.
- `missing_source_used_as_negative` is zero.
- GPT review is saved as interpretive design review only, not source truth.

### Macro assignment audit

| scope | row_count | macro_assignment_certified_count | macro_used_for_assignment_count | macro_provisional_for_diagnostic_count | macro_provisional_used_as_certified_count | missing_source_used_as_negative_count |
| --- | --- | --- | --- | --- | --- | --- |
| task672_core_panel | 1621 | 0 | 0 | 1621 | 0 | 0 |
| task684_allocation | 7824 | 0 | 0 | 5216 | 0 | 0 |
| task684_guarded_all | 1621 | 0 | 0 | 1621 | 0 | 0 |

### Allocation provenance audit

| column_name | present_flag | non_null_count |
| --- | --- | --- |
| source_integrity_state | 1 | 5216 |
| asof_valid_flag | 1 | 5216 |
| used_for_assignment_flag | 1 | 5216 |
| company_source_assignment_certified_flag | 1 | 5216 |
| content_prediction_assignment_certified_flag | 1 | 5216 |
| macro_assignment_certified_flag | 1 | 5216 |
| macro_used_for_assignment_flag | 1 | 5216 |
| theme_price_assignment_certified_flag | 1 | 5216 |
| relation_assignment_certified_flag | 1 | 5216 |
| portfolio_capacity_assignment_certified_flag | 1 | 5216 |
| allocation_assignment_ready_flag | 1 | 5216 |
| assignment_certification_scope | 1 | 5216 |
| assignment_block_reason | 1 | 5216 |
| macro_asof_provisional_for_diagnostic_flag | 1 | 5216 |
| macro_provisional_used_as_certified | 1 | 5216 |
| missing_source_used_as_negative | 1 | 5216 |
| return_used_in_assignment_flag | 1 | 5216 |
| label_used_in_assignment_flag_task661 | 1 | 5216 |
| future_price_used_in_assignment | 1 | 5216 |

### Guarded post-repair audit

| audit_item | metric_value | detail |
| --- | --- | --- |
| final_capital_delta_vs_active | 0.0000 | guarded=10887.47; active=10887.47 |
| mdd_delta_vs_active | 0.0000 | guarded=-30.52; active=-30.52 |
| accepted_context_superiority_challenger | 0.0000 | Challengers accepted by guarded superiority after source certification repair. |
| superiority_failed_source | 20.0000 | Now means sparse source/action block, not all-row assignment-readiness collapse. |
| allocation_reason::superiority_no_replaceable_incumbent | 1506.0000 | Guarded all-scope allocation reason count after repair. |
| allocation_reason::accepted_baseline_context_preserved | 51.0000 | Guarded all-scope allocation reason count after repair. |
| allocation_reason::superiority_failed_archetype_context | 30.0000 | Guarded all-scope allocation reason count after repair. |
| allocation_reason::superiority_failed_source | 20.0000 | Guarded all-scope allocation reason count after repair. |
| allocation_reason::relation_cap3 | 14.0000 | Guarded all-scope allocation reason count after repair. |
| superiority_audit_rows | 28.0000 | Task684 superiority audit rows available after rerun. |

### GPT review pack

| reviewer | captured_scope | source_type | finding | accepted_implementation |
| --- | --- | --- | --- | --- |
| Chrome ChatGPT external reviewer | Task685 source certification repair design | external_model_interpretation_not_source_truth | Problem is source certification contract, not merely model weakness. | Split company/content/theme_price/macro/relation/portfolio assignment certification flags. |
| Chrome ChatGPT external reviewer | Macro provisional handling | external_model_interpretation_not_source_truth | Macro provisional must not grant action, size, cap, block, or superiority authority. | Keep macro_assignment_certified_flag=0 and macro_used_for_assignment_flag=0. |
| Chrome ChatGPT external reviewer | Allocation provenance | external_model_interpretation_not_source_truth | Allocation must preserve source/asof/provenance columns. | Task684 allocation now carries source_integrity_state and assignment certification flags. |

### Split/OOS metrics

Task686 does not promote a new strategy. Task684 post-repair still has the same all-period final capital for guarded and active cap3 because challenger displacement remains zero. This is now a slot-displacement logic blocker, not the all-row source-readiness collapse found in Task685.

### Failure decomposition

- Fixed: all Task672 core rows no longer show `source_gap_research_only`.
- Fixed: allocation output preserves source/asof/provenance fields.
- Preserved: macro provisional is not treated as certified.
- Remaining: guarded displacement still accepts zero challengers.

### Cost/slippage stress where PnL changed

Not applicable. No strategy is accepted or promoted by Task686.

### Remaining blockers

- Macro raw release/vintage certification is still missing.
- Guarded cohort replacement needs a conditional displacement hurdle.
- Strategy remains NOT_ACCEPTED and real capital remains FORBIDDEN.

## No-Background Decision-Maker Report

- What happened: the data pipe no longer marks every candidate as research-only.
- Why it matters: the five engines can now carry certified company/source context into allocation records.
- Whether this changes capital/deployment readiness: no. The strategy still did not improve over active cap3.
- Plain-language next step: now fix the slot replacement rule. The old data blocker is removed.

## Artifact Manifest

- Inputs: Task672 state panel, Task684 allocation/simulation/superiority artifacts, Chrome GPT review.
- Outputs: source certification summary, macro assignment audit, allocation provenance audit, guarded post-repair audit, GPT review pack, decision, pass/fail, manifest.
- Row counts: source summary 4, macro audit 3, provenance 19, guarded audit 10.
- Validation commands: `python src/backtest/build_task686_source_certification_contract_repair.py`; `python -m unittest tests.test_task686_source_certification_contract_repair`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| source_gap_collapse_fixed | PRIMARY_PASS | 1 | source_gap=0 | 0 source_gap rows |
| partial_assignment_ready_opened | PRIMARY_PASS | 1 | ready=1621/1621 | all Task672 core rows ready |
| macro_not_promoted | PRIMARY_PASS | 1 | macro_cert=0, macro_used=0 | macro remains diagnostic |
| no_macro_provisional_bypass | PRIMARY_PASS | 1 | macro_provisional_used_as_certified=0 | 0 bypass |
| allocation_provenance_preserved | PRIMARY_PASS | 1 | missing=[] | all provenance columns present |
| guarded_still_not_strategy_promotion | PRIMARY_PASS | 1 | challenger_accepted=0 | document remaining slot displacement blocker |
