# Task685 Data Management Source Readiness Audit

## Decision Summary

- Verdict: DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Key metrics: universe source-gap rows 1621/1621, universe assignment-ready rows 0, active cap3 assignment-ready rows 0/51, guarded challenger accepted rows 0.
- What changed: no trading logic changed; this task audits why Task682/Task684 engine changes could fail to change final guarded results.
- Next action: Fix data/source certification contract before further relation-engine trading-rule promotion.

## Quant Expert Report

### Data source and source readiness

Task685 reads Task684 stack, accepted trades, allocation, and simulation artifacts. The audit finds that source data is present in many rows, but assignment certification is absent. This means source-aware engines are still research-only.

| scope | row_count | source_integrity_field_present_flag | assignment_flag_fields_present_flag | source_gap_research_only_count | asof_valid_count | used_for_assignment_count | assignment_ready_count | macro_series_available_median | macro_release_timestamp_repaired_count | macro_asof_provisional_count | macro_asof_certified_count | linked_event_nonzero_count | source_text_certified_nonzero_count | content_prediction_certified_nonzero_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| universe_stack | 1621 | 1 | 1 | 1621 | 1621 | 0 | 0 | 15.0000 | 1621 | 1621 | 0 | 1621 | 1621 | 1621 |
| active_cap3_accepted | 51 | 1 | 1 | 51 | 51 | 0 | 0 | 15.0000 | 51 | 51 | 0 | 51 | 51 | 51 |
| all_allocation_rows | 7824 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0000 | 0 | 0 | 0 | 0 | 0 | 0 |

### Exact join keys

- Upstream panels preserve `lifecycle_id`, `symbol`, `entry_ts`, `theme_id`, and `split_name`.
- This audit does not create new joins for trading assignment.
- Guarded identity is checked by `candidate_name`, `split_scope`, `allocation_reason`, and `accepted_flag`.

### Leakage audit

- Task685 does not create assignment ranks.
- Return fields are only reported as evaluation-only in active trade audit.
- No label, future price, symbol blacklist, or theme blacklist is introduced.

### Root cause

| issue_id | file_path | line_reference | observed_code_contract | observed_effect | required_fix_direction | trading_status |
| --- | --- | --- | --- | --- | --- | --- |
| used_for_assignment_flag_hardcoded_zero | src/backtest/build_task661_mechanism_relation_engine.py | 213-214 | asof_valid_flag is copied from macro_asof_provisional_for_diagnostic_flag; used_for_assignment_flag is hard-coded to 0. | Every downstream relation/context row becomes diagnostic-only for assignment readiness. | Create a row-level source certification contract before setting used_for_assignment_flag=1. | FORBIDDEN_UNTIL_FIXED_AND_VALIDATED |
| macro_asof_provisional_all_available_rows | src/backtest/build_task655_macro_asof_release_repair.py | 251-257 | macro_release_timestamp_repaired_flag and macro_asof_provisional_for_diagnostic_flag are set from macro_series_available_count > 0. | Macro context exists, but it is repaired/provisional rather than raw release-asof certified. | Separate raw release timestamp, vintage timestamp, repair provenance, and assignment certification. | FORBIDDEN_UNTIL_FIXED_AND_VALIDATED |
| source_integrity_requires_assignment_flag | src/backtest/build_task672_current_data_state_axis_panel.py | 135-139 | source_integrity_state becomes source_gap_research_only unless both asof_valid_flag and used_for_assignment_flag are 1. | Rows with data still get demoted when assignment certification is missing. | Keep this gate strict, but fix upstream certification instead of bypassing it. | GATE_IS_CORRECT_UPSTREAM_IS_NOT_READY |
| guarded_candidate_preserves_baseline_by_construction | src/backtest/build_task684_interaction_context_prediction_stack.py | 565-654 | Guarded selection preserves active baseline first and admits challengers only after strict superiority checks. | With source readiness weak, challengers cannot earn replacement rights, so guarded result can equal active cap3. | After source readiness is fixed, retest challenger admission and replacement reasons by same entry_ts cohort. | RESEARCH_ONLY |

### Guarded identity audit

| audit_item | metric_value | detail |
| --- | --- | --- |
| final_capital_identity_check | 0.0000 | guarded=10887.47; active=10887.47 |
| mdd_identity_check | 0.0000 | guarded=-30.52; active=-30.52 |
| accepted_baseline_context_preserved | 51.0000 | Accepted guarded trades that are preserved active cap3 baseline rows. |
| accepted_context_superiority_challenger | 0.0000 | Challenger rows admitted by superiority logic. |
| allocation_reason::superiority_no_replaceable_incumbent | 1506.0000 | Guarded all-scope allocation reason count. |
| allocation_reason::accepted_baseline_context_preserved | 51.0000 | Guarded all-scope allocation reason count. |
| allocation_reason::superiority_failed_archetype_context | 30.0000 | Guarded all-scope allocation reason count. |
| allocation_reason::superiority_failed_source | 20.0000 | Guarded all-scope allocation reason count. |
| allocation_reason::relation_cap3 | 14.0000 | Guarded all-scope allocation reason count. |

### Split/OOS source readiness

| split_name | row_count | source_gap_research_only_count | assignment_ready_count | asof_valid_count | used_for_assignment_count | macro_series_available_median | macro_provisional_count | macro_repaired_count | linked_event_nonzero_count | source_text_certified_nonzero_count | content_prediction_certified_nonzero_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| recent_oos | 332 | 332 | 0 | 332 | 0 | 15.0000 | 332 | 332 | 332 | 332 | 332 |
| train_design | 634 | 634 | 0 | 634 | 0 | 15.0000 | 634 | 634 | 634 | 634 | 634 |
| validation | 655 | 655 | 0 | 655 | 0 | 15.0000 | 655 | 655 | 655 | 655 | 655 |

### Failure decomposition

- The five engines can describe context, but they cannot prove assignment-ready source status.
- `source_integrity_state` is `source_gap_research_only` when `used_for_assignment_flag=0`.
- Guarded candidate preserves active cap3 first. With no certified challenger path, final result can equal active cap3.

### Cost/slippage stress where PnL changed

Not applicable. Task685 changes no PnL simulation and creates no new candidate.

### Remaining blockers

- Row-level source certification contract is missing.
- Macro as-of data is repaired/provisional, not raw release-asof certified.
- Microstructure remains pending for these assignment decisions.
- Challenger admission must be retested only after source certification is fixed.

## No-Background Decision-Maker Report

- What happened: the five engines did not change guarded results because the data layer still says the rows are research-only.
- Why it matters: better labels cannot safely control trades until the source readiness gate says the input was actually usable at that time.
- Whether this changes capital/deployment readiness: no. Status remains NOT_ACCEPTED and FORBIDDEN.
- Plain-language next step: fix the source certification pipe first, then rerun the five engines.

## Artifact Manifest

- Inputs: Task684 stack, accepted trades, allocation, simulation result.
- Outputs: source readiness summary, flag distribution, active cap3 audit, root cause table, guarded identity audit, split readiness table, decision, pass/fail, manifest.
- Row counts: summary 3, root cause 4, guarded identity 9, split readiness 3.
- Validation commands: `python src/backtest/build_task685_data_management_source_readiness_audit.py`; `python -m unittest tests.test_task685_data_management_source_readiness_audit`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| source_gap_audit_complete | PRIMARY_PASS | 1 | source_gap=1621/1621 | identify source gap scope |
| assignment_ready_zero_detected | PRIMARY_PASS | 1 | assignment_ready=0 | 0 ready rows |
| active_cap3_not_assignment_ready | PRIMARY_PASS | 1 | active_ready=0 | active cap3 also not ready |
| guarded_identity_explained | PRIMARY_PASS | 1 | accepted_context_superiority_challenger=0 | no challenger admitted |
| no_strategy_promotion | PRIMARY_PASS | 1 | Task685 audit only | NOT_ACCEPTED/FORBIDDEN |
