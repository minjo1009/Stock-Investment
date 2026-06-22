# Task659 Theme Specific Relation Engine

## Decision Summary

- Verdict: `FULL_PERIOD_THEME_RELATION_RESEARCH_CANDIDATE_OOS_EFFECT_NOT_PROVEN`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Task639 baseline: $7639.62, max drawdown -23.76 percent.
- Best candidate: `theme_conflict_hold5` = $8308.82, max drawdown -21.97 percent.
- Promotion candidates: 0.

## Quant Expert Report

Task659 implements macro-to-theme exposure translation, driver-level conflict flags, theme macro company relation states, and only Task656-allowed soft action tests.

### Data Source And Source Readiness

Inputs are Task657 release-time repaired macro-tagged execution rows and a manually fixed Task658 exposure matrix. No new market data source is introduced.

### Exact Join Keys

`lifecycle_id`, `timing_mode`, and `exit_mode` from Task657 tagged execution panel.

### Leakage Audit

Exposure matrix is fixed before performance evaluation. Labels and returns are evaluation-only.

### Split/OOS Metrics

| candidate_name | split_name | initial_capital_usd | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct | entry_reduce_failure_rate | qqq_final_capital_usd | beats_qqq_flag | label_used_in_assignment_flag | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_task639_core | recent_oos | 1000.0 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 |
| theme_conflict_hold10 | recent_oos | 1000.0 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 |
| theme_conflict_hold5 | recent_oos | 1000.0 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 |
| theme_conflict_delay60m | recent_oos | 1000.0 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 |
| theme_conflict_vwap | recent_oos | 1000.0 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 |
| theme_multi_conflict_hold10 | recent_oos | 1000.0 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 |
| theme_nonresilient_conflict_hold10 | recent_oos | 1000.0 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 |
| diagnostic_skip_nonresilient_conflict | recent_oos | 1000.0 | 315 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.2 | 1124.192829329964 | 1 | 0 | 0 |
| baseline_task639_core | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 |
| theme_conflict_hold10 | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 |
| theme_conflict_hold5 | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 |
| theme_conflict_delay60m | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 |
| theme_conflict_vwap | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 |
| theme_multi_conflict_hold10 | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 |
| theme_nonresilient_conflict_hold10 | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 |
| diagnostic_skip_nonresilient_conflict | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | 0.4 | 1049.908329847512 | 1 | 0 | 0 |

### Failure Decomposition

| split_name | theme_id | theme_macro_relation_state | trade_count | avg_return_pct | win_rate | entry_reduce_failure_rate | large_loss_rate | sparse_cell_flag | evaluation_only_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| recent_oos | ai_semiconductors | macro_theme_aligned_company_positive | 67 | 19.273140385752328 | 0.7014925373134329 | 0.2835820895522388 | 0.11940298507462686 | 0 | 1 |
| recent_oos | industrial_automation_robotics | macro_theme_aligned_company_positive | 44 | 2.8185897611617787 | 0.38636363636363635 | 0.4090909090909091 | 0.25 | 0 | 1 |
| recent_oos | power_grid_electrification | macro_theme_aligned_company_positive | 35 | 7.9643102015649365 | 0.5714285714285714 | 0.37142857142857144 | 0.17142857142857143 | 0 | 1 |
| recent_oos | aerospace_defense_space | macro_theme_neutral_company_positive | 30 | -5.085749442915473 | 0.36666666666666664 | 0.4666666666666667 | 0.23333333333333334 | 0 | 1 |
| recent_oos | cloud_ai_platforms | macro_theme_aligned_company_positive | 20 | 4.815522137119589 | 0.5 | 0.35 | 0.0 | 0 | 1 |
| recent_oos | cybersecurity | macro_theme_neutral_company_positive | 19 | 18.562088913645873 | 0.7894736842105263 | 0.10526315789473684 | 0.05263157894736842 | 0 | 1 |
| recent_oos | biotech_glp1_healthcare | macro_theme_aligned_company_positive | 17 | -2.1400742792573535 | 0.35294117647058826 | 0.6470588235294118 | 0.47058823529411764 | 0 | 1 |
| recent_oos | power_grid_electrification | single_driver_conflict_company_positive | 17 | 11.406122631708413 | 0.6470588235294118 | 0.35294117647058826 | 0.29411764705882354 | 0 | 1 |
| recent_oos | power_grid_electrification | sparse_theme_macro_cell | 17 | 13.245717515405147 | 0.7647058823529411 | 0.23529411764705882 | 0.11764705882352941 | 1 | 1 |
| recent_oos | crypto_fintech | macro_theme_aligned_company_positive | 12 | -19.53897910509862 | 0.08333333333333333 | 0.8333333333333334 | 0.8333333333333334 | 0 | 1 |
| recent_oos | ai_semiconductors | sparse_theme_macro_cell | 10 | 24.725071870853075 | 0.8 | 0.2 | 0.1 | 1 | 1 |
| recent_oos | industrial_automation_robotics | sparse_theme_macro_cell | 10 | -10.88096055257433 | 0.0 | 1.0 | 0.6 | 1 | 1 |
| recent_oos | data_devops_software | macro_theme_aligned_company_positive | 8 | 22.502424368947878 | 1.0 | 0.0 | 0.0 | 0 | 1 |
| recent_oos | cybersecurity | sparse_theme_macro_cell | 7 | 7.366254743508193 | 0.5714285714285714 | 0.42857142857142855 | 0.2857142857142857 | 1 | 1 |
| recent_oos | aerospace_defense_space | sparse_theme_macro_cell | 6 | -8.667850283922464 | 0.16666666666666666 | 0.8333333333333334 | 0.8333333333333334 | 1 | 1 |
| recent_oos | crypto_fintech | sparse_theme_macro_cell | 4 | -17.287277654005695 | 0.0 | 0.75 | 0.75 | 1 | 1 |
| recent_oos | cybersecurity | macro_theme_aligned_company_positive | 4 | 56.55262516964413 | 1.0 | 0.0 | 0.0 | 0 | 1 |
| recent_oos | ev_autonomy_mobility | macro_theme_aligned_company_positive | 3 | -17.78697956466726 | 0.0 | 1.0 | 0.6666666666666666 | 0 | 1 |
| recent_oos | biotech_glp1_healthcare | sparse_theme_macro_cell | 1 | -12.649608861841449 | 0.0 | 1.0 | 1.0 | 1 | 1 |
| recent_oos | cloud_ai_platforms | sparse_theme_macro_cell | 1 | 34.34768222308415 | 1.0 | 0.0 | 0.0 | 1 | 1 |

### Candidate Grid

| candidate_name | split_name | initial_capital_usd | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct | entry_reduce_failure_rate | qqq_final_capital_usd | beats_qqq_flag | label_used_in_assignment_flag | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| theme_conflict_hold5 | all | 1000.0 | 1621 | 55 | 8308.816978033587 | 730.8816978033586 | -21.969748723881754 | 0.32727272727272727 | 1606.8278306897957 | 1 | 0 | 0 |
| theme_conflict_delay60m | all | 1000.0 | 1621 | 54 | 7647.5204989849135 | 664.7520498984914 | -23.755747663170702 | 0.37037037037037035 | 1606.8278306897957 | 1 | 0 | 0 |
| baseline_task639_core | all | 1000.0 | 1621 | 54 | 7639.620310821465 | 663.9620310821465 | -23.755747663170702 | 0.37037037037037035 | 1606.8278306897957 | 1 | 0 | 0 |
| theme_multi_conflict_hold10 | all | 1000.0 | 1621 | 54 | 7639.620310821465 | 663.9620310821465 | -23.755747663170702 | 0.37037037037037035 | 1606.8278306897957 | 1 | 0 | 0 |
| theme_conflict_vwap | all | 1000.0 | 1621 | 54 | 7604.199956221074 | 660.4199956221074 | -23.755747663170702 | 0.37037037037037035 | 1606.8278306897957 | 1 | 0 | 0 |
| theme_conflict_hold10 | all | 1000.0 | 1621 | 55 | 6456.234402766213 | 545.6234402766213 | -22.10464642272446 | 0.34545454545454546 | 1606.8278306897957 | 1 | 0 | 0 |
| theme_nonresilient_conflict_hold10 | all | 1000.0 | 1621 | 55 | 6456.234402766213 | 545.6234402766213 | -22.10464642272446 | 0.34545454545454546 | 1606.8278306897957 | 1 | 0 | 0 |
| diagnostic_skip_nonresilient_conflict | all | 1000.0 | 1586 | 54 | 6256.248825386125 | 525.6248825386125 | -23.755747663170702 | 0.3888888888888889 | 1606.8278306897957 | 1 | 0 | 0 |

### Promotion Eligibility

| candidate_name | final_capital_usd | max_drawdown_pct | beats_task639_baseline_flag | drawdown_better_than_task639_flag | validation_beats_qqq_flag | recent_oos_beats_qqq_flag | validation_improves_task639_flag | recent_oos_improves_task639_flag | oos_effect_nonzero_flag | promotion_allowed_flag | full_period_research_candidate_flag | promotion_candidate_flag | task639_reference_final_capital_usd | task639_reference_max_drawdown_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| theme_conflict_hold5 | 8308.816978033587 | -21.969748723881754 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 1 | 0 | 7639.620310821465 | -23.755747663170705 |
| theme_conflict_delay60m | 7647.5204989849135 | -23.755747663170702 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 7639.620310821465 | -23.755747663170705 |
| baseline_task639_core | 7639.620310821465 | -23.755747663170702 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 7639.620310821465 | -23.755747663170705 |
| theme_multi_conflict_hold10 | 7639.620310821465 | -23.755747663170702 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 7639.620310821465 | -23.755747663170705 |
| theme_conflict_vwap | 7604.199956221074 | -23.755747663170702 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 7639.620310821465 | -23.755747663170705 |
| theme_conflict_hold10 | 6456.234402766213 | -22.10464642272446 | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 7639.620310821465 | -23.755747663170705 |
| theme_nonresilient_conflict_hold10 | 6456.234402766213 | -22.10464642272446 | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 7639.620310821465 | -23.755747663170705 |
| diagnostic_skip_nonresilient_conflict | 6256.248825386125 | -23.755747663170702 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 7639.620310821465 | -23.755747663170705 |

### Not Do Matrix

| blocker | violation_count | pass_flag |
| --- | --- | --- |
| macro_standalone_entry | 0 | 1 |
| macro_hard_block | 0 | 1 |
| macro_full_entry_promotion | 0 | 1 |
| macro_size_boost | 0 | 1 |
| diagnostic_skip_promoted | 0 | 1 |
| forbidden_macro_authority | 0 | 1 |

## No-Background Decision-Maker Report

We made the engine smarter: macro now passes through theme exposure first.

But smarter does not automatically mean better. The backtest still has to beat Task639.

If it does not, Task639 stays the baseline and the relation engine stays diagnostic.

## Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| theme_exposure_matrix_built | 1 | themes=10 | all active themes mapped |
| driver_conflicts_split | 1 | rates/oil/dollar/credit/liquidity | driver conflicts not collapsed into one macro bucket |
| relation_state_panel_built | 1 | diagnostic_rows=60 | relation diagnostics present |
| not_do_matrix_pass | 1 | violations=0 | no forbidden macro authority |
| best_candidate_beats_task639_return | 1 | best=$8308.82; baseline=$7639.62 | beat Task639 return |
| best_candidate_improves_drawdown | 1 | best_dd=-21.97; baseline_dd=-23.76 | improve drawdown |
| promotion_candidate_found | 0 | promotion_candidates=0 | candidate passes return drawdown OOS and permission gates |
| trading_promotion | 0 | research backtest only | requires accepted strategy gates and live readiness |

## Artifact Manifest

- `theme_macro_exposure_matrix.csv`
- `theme_macro_company_state_panel.csv`
- `task659_driver_conflict_panel.csv`
- `theme_macro_cell_diagnostics.csv`
- `theme_specific_soft_wrapper_grid.csv`
- `task659_split_account_grid.csv`
- `task659_permission_audit.csv`
- `promotion_eligibility_report.csv`
- `not_do_matrix.csv`
- `task_659_pass_fail_matrix.csv`
- `task_659_decision.csv`
- `artifact_manifest.csv`
