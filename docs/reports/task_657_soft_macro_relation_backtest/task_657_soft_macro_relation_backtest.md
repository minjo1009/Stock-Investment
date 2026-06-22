# Task657 Soft Macro Relation Backtest

## Decision Summary

- Verdict: `NO_SOFT_MACRO_RELATION_UPGRADE_KEEP_TASK639_BASELINE`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Task639 baseline: $7639.62, max drawdown -23.76 percent.
- Best candidate: `baseline_task639_core` = $7639.62, max drawdown -23.76 percent.
- Promotion candidates: 0.
- What changed: Task656 pragmatic macro context was retested as soft relation modifiers only.

## Quant Expert Report

Task657 joins Task638 execution variants with Task655 release-time repaired macro context. It tests only Task656-allowed soft uses: skip/confirm/delay/shorter-hold style candidates. It does not use macro for standalone entries, hard blocks, full entry, or size boosts.

### Data Source And Source Readiness

Macro context comes from Task655 and is release-time repaired but latest-vintage caveated. Therefore it is soft modifier only.

### Exact Join Keys

`lifecycle_id`, `timing_mode`, and `exit_mode`.

### Leakage Audit

Labels and realized returns are not used for assignment. Returns are used only in evaluation tables.

### Split/OOS Metrics

| candidate_name | split_name | initial_capital_usd | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct | entry_reduce_failure_rate | qqq_final_capital_usd | beats_qqq_flag | label_used_in_assignment_flag | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_task639_core | recent_oos | 1000.0 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 |
| soft_skip_macro_pressure | recent_oos | 1000.0 | 296 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 |
| soft_keep_supportive_mixed_only | recent_oos | 1000.0 | 296 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 |
| soft_supportive_only | recent_oos | 1000.0 | 57 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 |
| soft_delay_pressure_1d_to_60m | recent_oos | 1000.0 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 |
| soft_delay_pressure_1d_to_vwap | recent_oos | 1000.0 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 |
| soft_pressure_hold5 | recent_oos | 1000.0 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 |
| soft_pressure_hold10 | recent_oos | 1000.0 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 |
| baseline_task639_core | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 |
| soft_skip_macro_pressure | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 |
| soft_keep_supportive_mixed_only | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 |
| soft_delay_pressure_1d_to_60m | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 |
| soft_delay_pressure_1d_to_vwap | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 |
| soft_pressure_hold5 | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 |
| soft_pressure_hold10 | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 |
| soft_supportive_only | validation | 1000.0 | 318 | 14 | 920.4573360433743 | -7.954266395662568 | -12.321770529580146 | 0.42857142857142855 | 1049.908329847512 | 0 | 0 | 0 |

### Failure Decomposition

| soft_macro_state | row_count | avg_return_pct | win_rate | entry_reduce_failure_rate | large_loss_rate | evaluation_only_flag |
| --- | --- | --- | --- | --- | --- | --- |
| macro_mixed | 848 | 7.576770949224159 | 0.5872641509433962 | 0.3490566037735849 | 0.2417452830188679 | 1 |
| macro_supportive | 720 | 3.06328951654524 | 0.4888888888888889 | 0.45416666666666666 | 0.3527777777777778 | 1 |
| macro_pressure | 53 | 13.998052573905431 | 0.6037735849056604 | 0.32075471698113206 | 0.20754716981132076 | 1 |

### Candidate Grid

| candidate_name | split_name | initial_capital_usd | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct | entry_reduce_failure_rate | qqq_final_capital_usd | beats_qqq_flag | label_used_in_assignment_flag | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_task639_core | all | 1000.0 | 1621 | 54 | 7639.620310821465 | 663.9620310821465 | -23.755747663170702 | 0.37037037037037035 | 1606.8278306897957 | 1 | 0 | 0 |
| soft_pressure_hold10 | all | 1000.0 | 1621 | 56 | 7625.352530586147 | 662.5352530586147 | -23.159538452719552 | 0.3392857142857143 | 1606.8278306897957 | 1 | 0 | 0 |
| soft_pressure_hold5 | all | 1000.0 | 1621 | 58 | 7231.32558388273 | 623.132558388273 | -24.14219283457134 | 0.3620689655172414 | 1606.8278306897957 | 1 | 0 | 0 |
| soft_skip_macro_pressure | all | 1000.0 | 1568 | 54 | 6950.432105980643 | 595.0432105980643 | -23.755747663170702 | 0.35185185185185186 | 1606.8278306897957 | 1 | 0 | 0 |
| soft_keep_supportive_mixed_only | all | 1000.0 | 1568 | 54 | 6950.432105980643 | 595.0432105980643 | -23.755747663170702 | 0.35185185185185186 | 1606.8278306897957 | 1 | 0 | 0 |
| soft_delay_pressure_1d_to_60m | all | 1000.0 | 1621 | 54 | 6509.969019396349 | 550.9969019396349 | -24.414351121916045 | 0.37037037037037035 | 1606.8278306897957 | 1 | 0 | 0 |
| soft_delay_pressure_1d_to_vwap | all | 1000.0 | 1621 | 54 | 6480.32929688637 | 548.032929688637 | -24.63048086682814 | 0.37037037037037035 | 1606.8278306897957 | 1 | 0 | 0 |
| soft_supportive_only | all | 1000.0 | 720 | 43 | 4095.1951559591953 | 309.51951559591953 | -18.528864749517858 | 0.4186046511627907 | 1605.986094488825 | 1 | 0 | 0 |

### Promotion Eligibility

| candidate_name | final_capital_usd | max_drawdown_pct | beats_task639_baseline_flag | drawdown_better_than_task639_flag | validation_beats_qqq_flag | recent_oos_beats_qqq_flag | soft_permission_pass_flag | promotion_candidate_flag | task639_reference_final_capital_usd | task639_reference_max_drawdown_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_task639_core | 7639.620310821465 | -23.755747663170702 | 0 | 0 | 1 | 1 | 1 | 0 | 7639.620310821465 | -23.755747663170705 |
| soft_pressure_hold10 | 7625.352530586147 | -23.159538452719552 | 0 | 1 | 1 | 1 | 1 | 0 | 7639.620310821465 | -23.755747663170705 |
| soft_pressure_hold5 | 7231.32558388273 | -24.14219283457134 | 0 | 0 | 1 | 1 | 1 | 0 | 7639.620310821465 | -23.755747663170705 |
| soft_skip_macro_pressure | 6950.432105980643 | -23.755747663170702 | 0 | 0 | 1 | 1 | 1 | 0 | 7639.620310821465 | -23.755747663170705 |
| soft_keep_supportive_mixed_only | 6950.432105980643 | -23.755747663170702 | 0 | 0 | 1 | 1 | 1 | 0 | 7639.620310821465 | -23.755747663170705 |
| soft_delay_pressure_1d_to_60m | 6509.969019396349 | -24.414351121916045 | 0 | 0 | 1 | 1 | 1 | 0 | 7639.620310821465 | -23.755747663170705 |
| soft_delay_pressure_1d_to_vwap | 6480.32929688637 | -24.63048086682814 | 0 | 0 | 1 | 1 | 1 | 0 | 7639.620310821465 | -23.755747663170705 |
| soft_supportive_only | 4095.1951559591953 | -18.528864749517858 | 0 | 1 | 0 | 1 | 1 | 0 | 7639.620310821465 | -23.755747663170705 |

### Remaining Blockers

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| baseline_built | 1 | baseline=$7639.62 | Task639 baseline must be present |
| soft_macro_candidates_built | 1 | candidates=8 | multiple soft macro candidates |
| permission_audit_pass | 1 | forbidden=0 | no hard block/full entry/size boost/standalone macro authority |
| best_soft_candidate_beats_task639_return | 0 | best_soft=$7625.35; baseline=$7639.62 | soft candidate must beat Task639 return |
| best_soft_candidate_improves_drawdown | 1 | best_soft_dd=-23.16; baseline_dd=-23.76 | soft candidate must improve drawdown |
| promotion_candidate_found | 0 | promotion_candidates=0 | must beat baseline return/drawdown plus validation/recent QQQ and permission gates |
| trading_promotion | 0 | research backtest only | requires acceptance gates and live readiness |

## No-Background Decision-Maker Report

We reran the relation engine with macro attached.

Macro was allowed to be careful, not powerful.

The result tells us whether being more careful around bad macro helped more than it hurt.

## Artifact Manifest

- `task_657_macro_tagged_execution_panel.csv`
- `task_657_candidate_account_grid.csv`
- `task_657_split_account_grid.csv`
- `task_657_macro_diagnostics.csv`
- `task_657_permission_audit.csv`
- `task_657_promotion_report.csv`
- `task_657_pass_fail_matrix.csv`
- `task_657_decision.csv`
- `artifact_manifest.csv`
