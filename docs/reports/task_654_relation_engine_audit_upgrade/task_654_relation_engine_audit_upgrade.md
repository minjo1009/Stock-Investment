# Task654 Relation Engine Audit Upgrade

## Decision Summary

- Verdict: `COVERAGE_JOIN_GAPS_BLOCK_RELATION_ENGINE_AUTHORITY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Task639 reference: $1000 to $7639.62, max drawdown -23.76 percent.
- Task639 core assignment eligible rate: 0.0000.
- Relation promotion candidates: 0.
- What changed: audit infrastructure was added; no trading rule was promoted.
- Next action: repair macro join/vintage coverage before relation states can change execution.

## Quant Expert Report

Task654 implements the Task653 firm-grade checklist as auditable artifacts. The task does not add new source categories and does not change Task639 execution.

### Data Source And Source Readiness

| scope | row_count | lifecycle_count | macro_exact_match_rows | macro_missing_rows | macro_missing_rate | company_assignment_valid_rows | company_source_gap_rows | company_source_gap_rate | latest_vintage_gap_rows | latest_vintage_gap_rate | release_calendar_gap_rows | release_calendar_gap_rate | assignment_eligible_rows | assignment_eligible_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| execution_all_variants | 189102 | 5265 | 17820 | 171282 | 0.9057651426214424 | 86548 | 102554 | 0.5423210753984622 | 189102 | 1.0 | 189102 | 1.0 | 0 | 0.0 |
| execution_delay1d_existing | 5047 | 5047 | 495 | 4552 | 0.9019219338220725 | 2394 | 2653 | 0.5256588072122053 | 5047 | 1.0 | 5047 | 1.0 | 0 | 0.0 |
| task639_core_delay1d_existing | 1621 | 1621 | 258 | 1363 | 0.8408389882788402 | 1621 | 0 | 0.0 | 1621 | 1.0 | 1621 | 1.0 | 0 | 0.0 |
| task651_state_panel | 189102 | 5265 | 17820 | 171282 | 0.9057651426214424 | 86548 | 102554 | 0.5423210753984622 | 189102 | 1.0 | 189102 | 1.0 | 0 | 0.0 |

### Exact Join Keys

`join_contract_audit.csv` contains row-level `macro_join_key`, `company_join_key`, `macro_join_status`, `company_join_status`, `asof_valid_flag`, `latest_vintage_gap_flag`, `used_for_assignment_flag`, and `used_for_diagnostic_only_flag`.

### Leakage Audit

Labels, future returns, and realized outcomes are not used in the audit assignment logic. Missing macro or latest-vintage gaps are not treated as bullish or bearish.

### Split/OOS Metrics

No new strategy PnL was promoted. Promotion eligibility checks continue to compare against Task639, validation QQQ, and recent OOS QQQ.

### Failure Decomposition

| baseline_transition | row_count | accepted_trade_count | final_capital_usd | max_drawdown_pct | avg_return_pct | entry_reduce_failure_rate | macro_missing_or_latest_gap_rows | relation_can_change_execution_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kept_task639_but_relation_diagnostic_only | 1621 | 54 | 7639.620310821465 | -23.755747663170702 | 5.781966072345248 | 0.39481801357186924 | 2984 | 0 |

### Promotion Eligibility

| candidate_name | initial_capital_usd | final_capital_usd | max_drawdown_pct | beats_task639_return_flag | drawdown_better_than_task639_flag | validation_beats_qqq_flag | recent_oos_beats_qqq_flag | source_coverage_pass_flag | latest_vintage_pass_flag | promotion_pass_flag | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_task639_core | 1000.0 | 7639.620310821465 | -23.755747663170705 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | blocked_by_coverage_latest_vintage_or_task639_baseline |
| task651_relation_action_strategy | 1000.0 | 7341.221691631648 | -24.90388284291241 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | blocked_by_coverage_latest_vintage_or_task639_baseline |
| chart_not_fragile_or_unconfirmed | 1000.0 | 6229.593643357528 | -32.898667168151405 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | blocked_by_coverage_latest_vintage_or_task639_baseline |
| chart_not_unconfirmed | 1000.0 | 6143.13573398691 | -32.78178416923156 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | blocked_by_coverage_latest_vintage_or_task639_baseline |
| moderate_or_mixed_company | 1000.0 | 5533.369175810348 | -26.33517848840445 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | blocked_by_coverage_latest_vintage_or_task639_baseline |
| company_not_strong_label | 1000.0 | 5533.369175810348 | -26.33517848840445 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | blocked_by_coverage_latest_vintage_or_task639_baseline |
| confirmed_moderate_or_mixed | 1000.0 | 4512.709646732255 | -26.63731977430012 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | blocked_by_coverage_latest_vintage_or_task639_baseline |
| chart_confirmed_only | 1000.0 | 3977.86011587098 | -36.18749152196053 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | blocked_by_coverage_latest_vintage_or_task639_baseline |
| macro_known_mixed_supportive | 1000.0 | 2660.63824641992 | -17.842685627654898 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | blocked_by_coverage_latest_vintage_or_task639_baseline |
| macro_mixed_only | 1000.0 | 2372.063501858014 | -8.160119418380996 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | blocked_by_coverage_latest_vintage_or_task639_baseline |

### Remaining Blockers

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| coverage_scope_report_built | 1 | scopes=4 | all required scopes present |
| join_contract_required_columns | 1 | columns=24 | join audit must contain required row-level authority fields |
| task639_core_assignment_coverage | 0 | assignment_eligible_rate=0.0000 | >=0.80 before relation can affect Task639 execution |
| baseline_preservation_audit_built | 1 | rows=1621 | Task639 candidate treatment must be auditable |
| taxonomy_permissions_split | 1 | promotion_permission_nonzero=0 | taxonomy names cannot grant promotion |
| action_transition_matrix_built | 1 | rows=51 | state-to-action transitions must be visible |
| relation_assignment_rows_available | 0 | assignment_rows=0 | >0 rows with valid source coverage before relation assignment |
| promotion_eligibility_report_built | 1 | candidates=10 | all relation candidates must be checked |
| relation_promotion_candidate_found | 0 | promotion_candidates=0 | candidate must beat Task639 return and drawdown plus OOS and source gates |
| trading_promotion | 0 | relation remains diagnostic only | all gates above plus live source readiness |

## No-Background Decision-Maker Report

The relation engine still cannot trade by itself. It does not have enough clean row-by-row evidence yet.

Plain version:

- We checked whether the data is really attached.
- We checked whether Task639 trades were preserved or damaged.
- We checked whether strong-sounding names actually deserve trading power.
- Result: not yet.

Task639 stays the baseline. Relation states stay research-only until coverage and join quality are repaired.

## Artifact Manifest

- `coverage_scope_report.csv`
- `join_contract_audit.csv`
- `baseline_preservation_audit.csv`
- `taxonomy_definition_vs_performance.csv`
- `action_transition_matrix.csv`
- `promotion_eligibility_report.csv`
- `single_simulator_comparison.csv`
- `task_654_pass_fail_matrix.csv`
- `task_654_decision.csv`
- `artifact_manifest.csv`
