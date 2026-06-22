# Task661 Mechanism Relation Engine

## Decision Summary

- Verdict: `MECHANISM_ENGINE_BUILT_NO_PROMOTION_CANDIDATE`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Task639 baseline: `$7639.62`, max drawdown `-23.76%`.
- Best Task661 candidate: `baseline_task639_core` = `$7639.62`, max drawdown `-23.76%`.
- Promotion candidates: `0`.

## Quant Expert Report

Task661 addresses five bottlenecks from Task660: economic transmission, catalyst quality, price acceptance, OOS effect audit, and scenario/invalidation proxy states.

Rule scope correction: Task661 does not introduce fixed-hold exits or timing overrides. It is a relation-state diagnostic only.

### Data Source And Source Readiness

Input is the Task659 theme macro company state panel. No new source is introduced and no GPT output is used as source data.

### Exact Join Keys

`lifecycle_id`, `timing_mode`, `exit_mode`, `entry_ts`, and `split_name`.

### Leakage Audit

The institutional transmission template is static and marked `return_tuned_flag=0`. Returns and labels are evaluation-only.

### Candidate Grid

| candidate_name | split_name | initial_capital_usd | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct | entry_reduce_failure_rate | qqq_final_capital_usd | beats_qqq_flag | label_used_in_assignment_flag | return_used_in_assignment_flag | forbidden_macro_authority_flag | diagnostic_skip_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_task639_core | all | 1000.0 | 1621 | 54 | 7639.620310821465 | 663.9620310821465 | -23.755747663170702 | 0.37037037037037035 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 |
| diagnostic_relation_state_only_no_exit_override | all | 1000.0 | 1621 | 54 | 7639.620310821465 | 663.9620310821465 | -23.755747663170702 | 0.37037037037037035 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 |

### Split/OOS Metrics

| candidate_name | split_name | initial_capital_usd | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct | entry_reduce_failure_rate | qqq_final_capital_usd | beats_qqq_flag | label_used_in_assignment_flag | return_used_in_assignment_flag | forbidden_macro_authority_flag | diagnostic_skip_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_task639_core | recent_oos | 1000.0 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 |
| diagnostic_relation_state_only_no_exit_override | recent_oos | 1000.0 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 |
| baseline_task639_core | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 |
| diagnostic_relation_state_only_no_exit_override | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 |

### Mechanism Diagnostics

| split_name | theme_id | mechanism_relation_state | trade_count | avg_return_pct | win_rate | entry_reduce_failure_rate | large_loss_rate | mechanism_sparse_cell_flag | evaluation_only_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| recent_oos | ai_semiconductors | mechanism_reinforcing_company_positive | 48 | 24.373690446856834 | 0.6666666666666666 | 0.3125 | 0.08333333333333333 | 0 | 1 |
| recent_oos | power_grid_electrification | mechanism_offsetting_company_positive | 24 | 10.857675076744428 | 0.7083333333333334 | 0.2916666666666667 | 0.25 | 0 | 1 |
| recent_oos | industrial_automation_robotics | company_positive_needs_confirmation | 23 | -6.760425478879483 | 0.30434782608695654 | 0.5652173913043478 | 0.34782608695652173 | 0 | 1 |
| recent_oos | ai_semiconductors | company_positive_needs_confirmation | 22 | 11.859864140120294 | 0.8181818181818182 | 0.18181818181818182 | 0.18181818181818182 | 0 | 1 |
| recent_oos | power_grid_electrification | company_positive_needs_confirmation | 22 | 22.201296855495414 | 0.8636363636363636 | 0.09090909090909091 | 0.0 | 0 | 1 |
| recent_oos | aerospace_defense_space | company_quality_price_confirmed | 21 | -6.52936105358464 | 0.38095238095238093 | 0.5714285714285714 | 0.3333333333333333 | 0 | 1 |
| recent_oos | cybersecurity | sparse_mechanism_cell | 21 | 17.894713919831062 | 0.7619047619047619 | 0.19047619047619047 | 0.09523809523809523 | 1 | 1 |
| recent_oos | cloud_ai_platforms | company_quality_price_confirmed | 20 | 4.815522137119589 | 0.5 | 0.35 | 0.0 | 0 | 1 |
| recent_oos | power_grid_electrification | mechanism_reinforcing_company_positive | 18 | -4.397848178706795 | 0.2777777777777778 | 0.6666666666666666 | 0.3333333333333333 | 0 | 1 |
| recent_oos | industrial_automation_robotics | mechanism_reinforcing_company_positive | 15 | 14.862868370522387 | 0.4 | 0.4 | 0.26666666666666666 | 0 | 1 |
| recent_oos | aerospace_defense_space | company_positive_needs_confirmation | 12 | -6.570100750609044 | 0.25 | 0.4166666666666667 | 0.25 | 0 | 1 |
| recent_oos | crypto_fintech | company_quality_price_confirmed | 12 | -19.53897910509862 | 0.08333333333333333 | 0.8333333333333334 | 0.8333333333333334 | 0 | 1 |
| recent_oos | industrial_automation_robotics | company_quality_price_confirmed | 12 | -1.4943803220028327 | 0.3333333333333333 | 0.4166666666666667 | 0.25 | 0 | 1 |
| recent_oos | biotech_glp1_healthcare | company_quality_price_confirmed | 10 | -3.9481921012819665 | 0.2 | 0.8 | 0.5 | 0 | 1 |
| recent_oos | biotech_glp1_healthcare | company_positive_needs_confirmation | 8 | -1.1936188245495984 | 0.5 | 0.5 | 0.5 | 0 | 1 |
| recent_oos | ai_semiconductors | sparse_mechanism_cell | 7 | 15.385281717451704 | 0.7142857142857143 | 0.2857142857142857 | 0.14285714285714285 | 1 | 1 |
| recent_oos | data_devops_software | mechanism_reinforcing_company_positive | 7 | 22.836019827818106 | 1.0 | 0.0 | 0.0 | 0 | 1 |
| recent_oos | cybersecurity | company_positive_needs_confirmation | 5 | 5.690896049475329 | 0.6 | 0.2 | 0.2 | 0 | 1 |
| recent_oos | power_grid_electrification | sparse_mechanism_cell | 5 | 5.596134821932052 | 0.6 | 0.4 | 0.2 | 1 | 1 |
| recent_oos | crypto_fintech | sparse_mechanism_cell | 4 | -17.287277654005695 | 0.0 | 0.75 | 0.75 | 1 | 1 |

### OOS Effect Audit

| candidate_name | split_name | changed_trade_count | added_winners | added_losers | removed_winners | removed_losers | modified_count | baseline_avg_return_pct | candidate_avg_return_pct | avg_return_delta_pct_point | evaluation_only_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| diagnostic_relation_state_only_no_exit_override | validation | 0 | 0 | 0 | 0 | 0 | 0 | 5.486202935556607 | 5.486202935556607 | 0.0 | 1 |
| diagnostic_relation_state_only_no_exit_override | recent_oos | 0 | 0 | 0 | 0 | 0 | 0 | 7.77751459657547 | 7.77751459657547 | 0.0 | 1 |

### Promotion Report

| candidate_name | final_capital_usd | max_drawdown_pct | beats_task639_baseline_flag | beats_task659_best_flag | drawdown_better_than_task639_flag | validation_improves_task639_flag | recent_oos_improves_task639_flag | validation_drawdown_not_worse_flag | recent_oos_drawdown_not_worse_flag | validation_beats_qqq_flag | recent_oos_beats_qqq_flag | forbidden_macro_authority_flag | diagnostic_skip_flag | promotion_allowed_flag | full_period_research_candidate_flag | promotion_candidate_flag | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_task639_core | 7639.620310821465 | -23.755747663170702 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | drawdown_not_better |
| diagnostic_relation_state_only_no_exit_override | 7639.620310821465 | -23.755747663170702 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | drawdown_not_better |

## No-Background Decision-Maker Report

We made the engine more professional, but we still do not approve trading.

The engine now asks better questions:

- Is the macro driver really connected to this theme?
- Does that connection hit funding, duration, energy, capex demand, policy, or adoption?
- Is the company news strong or weak?
- Did the price accept the story?
- Did validation and recent OOS actually improve?

If the answer is not proven in OOS, the action stays research-only.

## Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| economic_transmission_template_built | 1 | themes=10 | all active themes have economic mechanism fields |
| catalyst_quality_tier_built | 1 | catalyst_quality_tier present | contract/customer/supply/backlog/guidance/margin tiers |
| price_acceptance_state_built | 1 | price_acceptance_state present | accepted/neutral/rejected tape state |
| oos_effect_requires_distinct_improvement | 0 | promotion_candidates=0 | validation and recent OOS improve Task639 without worse drawdown |
| scenario_invalidation_fields_built | 1 | scenario_base_case and scenario_invalidation_condition present | each row has scenario and invalidation condition |
| all_task639_core_rows_state_assigned | 1 | task639_core_rows=1621 | all core rows assigned mechanism relation state |
| not_do_matrix_pass | 1 | violations=0 | no forbidden macro authority |
| strategy_accepted | 0 | research diagnostic only | requires accepted strategy gates and live readiness |

## Artifact Manifest

- `institutional_transmission_template.csv`
- `theme_mechanism_state_panel.csv`
- `mechanism_relation_diagnostics.csv`
- `mechanism_soft_wrapper_grid.csv`
- `mechanism_split_account_grid.csv`
- `oos_effect_audit.csv`
- `accepted_trade_attribution.csv`
- `promotion_report.csv`
- `not_do_matrix.csv`
- `task_661_pass_fail_matrix.csv`
- `task_661_decision.csv`
- `artifact_manifest.csv`
