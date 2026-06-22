# Task665 Priority MDD Attribution

## Decision Summary

- Verdict: `PRIORITY_MDD_ATTRIBUTION_COMPLETE_RISK_CAP_REQUIRED`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Baseline: `$7639.62`, MDD `-23.76%`.
- Priority: `$8797.73`, MDD `-33.63%`.
- Added/removed accepted trades: `27` / `27`.
- Negative displacement pairs: `22`.

## Quant Expert Report

Task665 attributes Task664's higher return but worse drawdown. It does not change entry, exit, timing, sizing, or priority rules.

### Data Source And Source Readiness

Input is the Task661 mechanism state panel rebuilt from Task659. No new source is introduced.

### Exact Join Keys

`lifecycle_id`, `entry_ts`, `simulated_exit_ts`, and accepted-trade membership.

### Leakage Audit

Returns are used only for post-trade attribution. No assignment rule is changed in this task.

### MDD Interval Summary

| candidate_name | final_capital_usd | max_drawdown_pct | accepted_trade_count | entry_reduce_failure_rate | mdd_peak_ts | mdd_peak_equity_usd | mdd_trough_ts | mdd_trough_equity_usd | mdd_interval_days | mdd_worse_than_baseline_pct_point | final_capital_delta_vs_baseline_usd | priority_mdd_penalty_pct_point |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_chronological | 7639.620310821464 | -23.755747663170702 | 54 | 0.35185185185185186 | 2025-02-07 14:30:00+00:00 | 5276.33237788818 | 2025-05-30 00:00:00+00:00 | 4022.90017232689 | 111.39583333333333 | 0.0 | 0.0 |  |
| predeclared_relation_ladder | 8797.725195699932 | -33.631456638622645 | 54 | 0.2962962962962963 | 2025-02-06 14:30:00+00:00 | 6362.895571756265 | 2025-06-03 00:00:00+00:00 | 4222.9611065802155 | 116.39583333333333 | -9.875708975451943 | 1158.1048848784676 | -9.875708975451943 |

### Accepted Trade Delta

| lifecycle_id | symbol | theme_id | entry_ts | simulated_exit_ts | mechanism_relation_state | catalyst_quality_tier | price_acceptance_state | baseline_accepted_flag | priority_accepted_flag | delta_class | baseline_return_pct | priority_return_pct | return_delta_pct_point | entry_in_priority_mdd_interval_flag | exit_in_priority_mdd_interval_flag | open_during_priority_mdd_trough_flag | evaluation_only_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TASK617/RKLB/20260526T133000Z | RKLB | aerospace_defense_space | 2026-05-28 14:30:00+00:00 | 2026-06-05 00:00:00+00:00 | company_positive_needs_confirmation | medium_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | -25.7021450019404 | -25.7021450019404 | 0 | 0 | 0 | 1 |
| TASK617/FTNT/20250220T190000Z | FTNT | cybersecurity | 2025-02-24 14:30:00+00:00 | 2025-04-04 00:00:00+00:00 | mechanism_reinforcing_company_positive | very_strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | -23.01189231526931 | -23.01189231526931 | 1 | 1 | 0 | 1 |
| TASK617/CEG/20250115T144500Z | CEG | power_grid_electrification | 2025-01-17 14:30:00+00:00 | 2025-02-27 00:00:00+00:00 | mechanism_offsetting_company_positive | strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | -22.49525155030457 | -22.49525155030457 | 0 | 1 | 0 | 1 |
| TASK617/PLTR/20250220T194500Z | PLTR | data_devops_software | 2025-02-24 14:30:00+00:00 | 2025-03-10 00:00:00+00:00 | mechanism_reinforcing_company_positive | very_strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | -20.83792298560464 | -20.83792298560464 | 1 | 1 | 0 | 1 |
| TASK617/CRWD/20250203T151500Z | CRWD | cybersecurity | 2025-02-05 14:30:00+00:00 | 2025-03-07 00:00:00+00:00 | mechanism_reinforcing_company_positive | very_strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | -18.75980392156863 | -18.75980392156863 | 0 | 1 | 0 | 1 |
| TASK617/PLTR/20250204T143000Z | PLTR | data_devops_software | 2025-02-06 14:30:00+00:00 | 2025-02-24 00:00:00+00:00 | mechanism_reinforcing_company_positive | strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | -10.79775092474997 | -10.79775092474997 | 1 | 1 | 0 | 1 |
| TASK617/OKTA/20250304T143000Z | OKTA | cybersecurity | 2025-03-06 14:30:00+00:00 | 2025-05-30 00:00:00+00:00 | company_positive_needs_confirmation | medium_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | -10.284891904235732 | -10.284891904235732 | 1 | 1 | 0 | 1 |
| TASK617/AMGN/20250305T144500Z | AMGN | biotech_glp1_healthcare | 2025-03-07 14:30:00+00:00 | 2025-06-02 00:00:00+00:00 | company_positive_needs_confirmation | medium_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | -10.0563598745196 | -10.0563598745196 | 1 | 1 | 0 | 1 |
| TASK617/OKTA/20250306T150000Z | OKTA | cybersecurity | 2025-03-10 14:30:00+00:00 | 2025-06-03 00:00:00+00:00 | company_positive_needs_confirmation | medium_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | -7.19309085865774 | -7.19309085865774 | 1 | 1 | 1 | 1 |
| TASK617/LLY/20251118T161500Z | LLY | biotech_glp1_healthcare | 2025-11-20 14:30:00+00:00 | 2026-02-18 00:00:00+00:00 | company_positive_needs_confirmation | medium_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | -2.88546173518949 | -2.88546173518949 | 0 | 0 | 0 | 1 |
| TASK617/TER/20260217T151500Z | TER | industrial_automation_robotics | 2026-02-19 14:30:00+00:00 | 2026-04-29 00:00:00+00:00 | mechanism_reinforcing_company_positive | strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | -2.07124048237816 | -2.07124048237816 | 0 | 0 | 0 | 1 |
| TASK617/CEG/20250528T133000Z | CEG | power_grid_electrification | 2025-05-30 14:30:00+00:00 | 2025-08-25 00:00:00+00:00 | mechanism_offsetting_company_positive | very_strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | 2.56528335971967 | 2.56528335971967 | 1 | 0 | 1 | 1 |
| TASK617/MDB/20250902T134500Z | MDB | data_devops_software | 2025-09-04 14:30:00+00:00 | 2025-11-26 00:00:00+00:00 | mechanism_reinforcing_company_positive | very_strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | 4.20795334493119 | 4.20795334493119 | 0 | 0 | 0 | 1 |
| TASK617/ROK/20250826T133000Z | ROK | industrial_automation_robotics | 2025-08-28 14:30:00+00:00 | 2025-11-20 00:00:00+00:00 | mechanism_reinforcing_company_positive | strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | 4.36050668850632 | 4.36050668850632 | 0 | 0 | 0 | 1 |
| TASK617/DDOG/20250529T144500Z | DDOG | data_devops_software | 2025-06-02 14:30:00+00:00 | 2025-08-26 00:00:00+00:00 | mechanism_reinforcing_company_positive | very_strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | 7.06194944251107 | 7.06194944251107 | 1 | 0 | 1 | 1 |
| TASK617/ETN/20260217T160000Z | ETN | power_grid_electrification | 2026-02-19 14:30:00+00:00 | 2026-05-14 00:00:00+00:00 | company_positive_needs_confirmation | medium_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | 7.178101874278529 | 7.178101874278529 | 0 | 0 | 0 | 1 |
| TASK617/DDOG/20250605T134500Z | DDOG | data_devops_software | 2025-06-09 14:30:00+00:00 | 2025-09-03 00:00:00+00:00 | mechanism_reinforcing_company_positive | strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | 7.842190346256929 | 7.842190346256929 | 0 | 0 | 0 | 1 |
| TASK617/AMGN/20251118T183000Z | AMGN | biotech_glp1_healthcare | 2025-11-20 14:30:00+00:00 | 2026-02-18 00:00:00+00:00 | company_positive_needs_confirmation | medium_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | 9.72002295816251 | 9.72002295816251 | 0 | 0 | 0 | 1 |
| TASK617/GEV/20260223T200000Z | GEV | power_grid_electrification | 2026-02-25 14:30:00+00:00 | 2026-05-20 00:00:00+00:00 | mechanism_reinforcing_company_positive | strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | 14.87907047382805 | 14.87907047382805 | 0 | 0 | 0 | 1 |
| TASK617/PH/20251124T150000Z | PH | industrial_automation_robotics | 2025-11-26 14:30:00+00:00 | 2026-02-24 00:00:00+00:00 | mechanism_reinforcing_company_positive | strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | 19.51361301252773 | 19.51361301252773 | 0 | 0 | 0 | 1 |

### Active Trade Inventory

| lifecycle_id | symbol | theme_id | entry_ts | simulated_exit_ts | mechanism_relation_state | catalyst_quality_tier | price_acceptance_state | baseline_accepted_flag | priority_accepted_flag | delta_class | baseline_return_pct | priority_return_pct | return_delta_pct_point | entry_in_priority_mdd_interval_flag | exit_in_priority_mdd_interval_flag | open_during_priority_mdd_trough_flag | evaluation_only_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TASK617/FTNT/20250220T190000Z | FTNT | cybersecurity | 2025-02-24 14:30:00+00:00 | 2025-04-04 00:00:00+00:00 | mechanism_reinforcing_company_positive | very_strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | -23.01189231526931 | -23.01189231526931 | 1 | 1 | 0 | 1 |
| TASK617/CEG/20250115T144500Z | CEG | power_grid_electrification | 2025-01-17 14:30:00+00:00 | 2025-02-27 00:00:00+00:00 | mechanism_offsetting_company_positive | strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | -22.49525155030457 | -22.49525155030457 | 0 | 1 | 0 | 1 |
| TASK617/PLTR/20250220T194500Z | PLTR | data_devops_software | 2025-02-24 14:30:00+00:00 | 2025-03-10 00:00:00+00:00 | mechanism_reinforcing_company_positive | very_strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | -20.83792298560464 | -20.83792298560464 | 1 | 1 | 0 | 1 |
| TASK617/CRWD/20250203T151500Z | CRWD | cybersecurity | 2025-02-05 14:30:00+00:00 | 2025-03-07 00:00:00+00:00 | mechanism_reinforcing_company_positive | very_strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | -18.75980392156863 | -18.75980392156863 | 0 | 1 | 0 | 1 |
| TASK617/PLTR/20250204T143000Z | PLTR | data_devops_software | 2025-02-06 14:30:00+00:00 | 2025-02-24 00:00:00+00:00 | mechanism_reinforcing_company_positive | strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | -10.79775092474997 | -10.79775092474997 | 1 | 1 | 0 | 1 |
| TASK617/OKTA/20250304T143000Z | OKTA | cybersecurity | 2025-03-06 14:30:00+00:00 | 2025-05-30 00:00:00+00:00 | company_positive_needs_confirmation | medium_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | -10.284891904235732 | -10.284891904235732 | 1 | 1 | 0 | 1 |
| TASK617/AMGN/20250305T144500Z | AMGN | biotech_glp1_healthcare | 2025-03-07 14:30:00+00:00 | 2025-06-02 00:00:00+00:00 | company_positive_needs_confirmation | medium_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | -10.0563598745196 | -10.0563598745196 | 1 | 1 | 0 | 1 |
| TASK617/OKTA/20250306T150000Z | OKTA | cybersecurity | 2025-03-10 14:30:00+00:00 | 2025-06-03 00:00:00+00:00 | company_positive_needs_confirmation | medium_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | -7.19309085865774 | -7.19309085865774 | 1 | 1 | 1 | 1 |
| TASK617/CEG/20250528T133000Z | CEG | power_grid_electrification | 2025-05-30 14:30:00+00:00 | 2025-08-25 00:00:00+00:00 | mechanism_offsetting_company_positive | very_strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | 2.56528335971967 | 2.56528335971967 | 1 | 0 | 1 | 1 |
| TASK617/DDOG/20250529T144500Z | DDOG | data_devops_software | 2025-06-02 14:30:00+00:00 | 2025-08-26 00:00:00+00:00 | mechanism_reinforcing_company_positive | very_strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | 7.06194944251107 | 7.06194944251107 | 1 | 0 | 1 | 1 |
| TASK617/GEV/20250528T133000Z | GEV | power_grid_electrification | 2025-05-30 14:30:00+00:00 | 2025-08-25 00:00:00+00:00 | mechanism_offsetting_company_positive | very_strong_catalyst | price_acceptance_strong | 0 | 1 | added_by_priority | 0.0 | 27.651063310339097 | 27.651063310339097 | 1 | 0 | 1 | 1 |
| TASK617/AMGN/20250304T143000Z | AMGN | biotech_glp1_healthcare | 2025-03-06 14:30:00+00:00 | 2025-05-30 00:00:00+00:00 | company_positive_needs_confirmation | medium_catalyst | price_acceptance_strong | 1 | 1 | preserved | -9.42485290232841 | -9.42485290232841 | 0.0 | 1 | 1 | 0 | 1 |
| TASK617/DDOG/20241216T144500Z | DDOG | data_devops_software | 2024-12-18 14:30:00+00:00 | 2025-02-25 00:00:00+00:00 | mechanism_reinforcing_company_positive | strong_catalyst | price_acceptance_strong | 1 | 1 | preserved | -26.97397380304668 | -26.97397380304668 | 0.0 | 0 | 1 | 0 | 1 |
| TASK617/DDOG/20241217T154500Z | DDOG | data_devops_software | 2024-12-19 14:30:00+00:00 | 2025-02-24 00:00:00+00:00 | sparse_mechanism_cell | medium_catalyst | price_acceptance_accepted | 1 | 1 | preserved | -22.42026436130865 | -22.42026436130865 | 0.0 | 0 | 1 | 0 | 1 |
| TASK617/NOC/20250403T133000Z | NOC | aerospace_defense_space | 2025-04-07 14:30:00+00:00 | 2025-07-02 00:00:00+00:00 | company_positive_needs_confirmation | medium_catalyst | price_acceptance_strong | 1 | 1 | preserved | 3.40718929389442 | 3.40718929389442 | 0.0 | 1 | 0 | 1 | 1 |
| TASK617/ASTS/20250409T171500Z | ASTS | aerospace_defense_space | 2025-04-11 14:30:00+00:00 | 2025-07-09 00:00:00+00:00 | company_quality_price_confirmed | very_strong_catalyst | price_acceptance_strong | 1 | 0 | removed_by_priority | 83.88178484477822 | 0.0 | -83.88178484477822 | 1 | 0 | 1 | 1 |
| TASK617/TEAM/20241107T144500Z | TEAM | data_devops_software | 2024-11-11 14:30:00+00:00 | 2025-02-07 00:00:00+00:00 | sparse_mechanism_cell | strong_catalyst | price_acceptance_strong | 1 | 0 | removed_by_priority | 31.55041965516675 | 0.0 | -31.55041965516675 | 0 | 1 | 0 | 1 |
| TASK617/ETN/20250501T141500Z | ETN | power_grid_electrification | 2025-05-05 14:30:00+00:00 | 2025-07-30 00:00:00+00:00 | mechanism_offsetting_company_positive | medium_catalyst | price_acceptance_strong | 1 | 0 | removed_by_priority | 31.211509826119787 | 0.0 | -31.211509826119787 | 1 | 0 | 1 | 1 |
| TASK617/ARM/20250528T163000Z | ARM | ai_semiconductors | 2025-05-30 14:30:00+00:00 | 2025-08-25 00:00:00+00:00 | sparse_mechanism_cell | very_strong_catalyst | price_acceptance_strong | 1 | 0 | removed_by_priority | 7.4695933863355295 | 0.0 | -7.4695933863355295 | 1 | 0 | 1 | 1 |
| TASK617/ASML/20250515T153000Z | ASML | ai_semiconductors | 2025-05-19 14:30:00+00:00 | 2025-08-13 00:00:00+00:00 | company_positive_needs_confirmation | medium_catalyst | price_acceptance_strong | 1 | 0 | removed_by_priority | 1.6413255206218897 | 0.0 | -1.6413255206218897 | 1 | 0 | 1 | 1 |

### Slot Displacement Pairs

| entry_ts | pair_type | added_lifecycle_id | added_symbol | added_theme_id | added_relation_state | added_priority_rank | added_return_pct | removed_lifecycle_id | removed_symbol | removed_theme_id | removed_relation_state | removed_priority_rank | removed_return_pct | pair_return_delta_pct_point | entry_in_priority_mdd_interval_flag | exit_in_priority_mdd_interval_flag | open_during_priority_mdd_trough_flag | evaluation_only_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2025-04-11 14:30:00+00:00 | unpaired_capacity_path_effect |  |  |  |  |  | 0.0 | TASK617/ASTS/20250409T171500Z | ASTS | aerospace_defense_space | company_quality_price_confirmed | 50 | 83.88178484477822 | -83.88178484477822 | 1 | 0 | 1 | 1 |
| 2026-05-08 14:30:00+00:00 | unpaired_capacity_path_effect |  |  |  |  |  | 0.0 | TASK617/ARM/20260506T150000Z | ARM | ai_semiconductors | mechanism_reinforcing_company_positive | 50 | 57.56138553823275 | -57.56138553823275 | 0 | 0 | 0 | 1 |
| 2025-08-18 14:30:00+00:00 | unpaired_capacity_path_effect |  |  |  |  |  | 0.0 | TASK617/AMD/20250814T133000Z | AMD | ai_semiconductors | mechanism_reinforcing_company_positive | 50 | 37.52896770179718 | -37.52896770179718 | 0 | 0 | 0 | 1 |
| 2024-11-11 14:30:00+00:00 | unpaired_capacity_path_effect |  |  |  |  |  | 0.0 | TASK617/TEAM/20241107T144500Z | TEAM | data_devops_software | sparse_mechanism_cell | 50 | 31.55041965516675 | -31.55041965516675 | 0 | 1 | 0 | 1 |
| 2025-05-05 14:30:00+00:00 | unpaired_capacity_path_effect |  |  |  |  |  | 0.0 | TASK617/ETN/20250501T141500Z | ETN | power_grid_electrification | mechanism_offsetting_company_positive | 50 | 31.211509826119787 | -31.211509826119787 | 1 | 0 | 1 | 1 |
| 2025-07-30 14:30:00+00:00 | unpaired_capacity_path_effect |  |  |  |  |  | 0.0 | TASK617/AMD/20250728T134500Z | AMD | ai_semiconductors | company_positive_needs_confirmation | 50 | 30.603009468338787 | -30.603009468338787 | 0 | 0 | 0 | 1 |
| 2026-02-11 14:30:00+00:00 | unpaired_capacity_path_effect |  |  |  |  |  | 0.0 | TASK617/GEV/20260209T143000Z | GEV | power_grid_electrification | company_positive_needs_confirmation | 50 | 26.56184173491059 | -26.56184173491059 | 0 | 0 | 0 | 1 |
| 2026-05-28 14:30:00+00:00 | unpaired_capacity_path_effect | TASK617/RKLB/20260526T133000Z | RKLB | aerospace_defense_space | company_positive_needs_confirmation | 30 | -25.7021450019404 |  |  |  |  |  | 0.0 | -25.7021450019404 | 0 | 0 | 0 | 1 |
| 2025-01-17 14:30:00+00:00 | unpaired_capacity_path_effect | TASK617/CEG/20250115T144500Z | CEG | power_grid_electrification | mechanism_offsetting_company_positive | 20 | -22.49525155030457 |  |  |  |  |  | 0.0 | -22.49525155030457 | 0 | 1 | 0 | 1 |
| 2025-02-24 14:30:00+00:00 | unpaired_capacity_path_effect | TASK617/PLTR/20250220T194500Z | PLTR | data_devops_software | mechanism_reinforcing_company_positive | 10 | -20.83792298560464 |  |  |  |  |  | 0.0 | -20.83792298560464 | 1 | 1 | 0 | 1 |
| 2025-02-24 14:30:00+00:00 | same_timestamp_displacement | TASK617/FTNT/20250220T190000Z | FTNT | cybersecurity | mechanism_reinforcing_company_positive | 10 | -23.01189231526931 | TASK617/AMGN/20250220T143000Z | AMGN | biotech_glp1_healthcare | company_quality_price_confirmed | 50 | -10.14032782804672 | -12.871564487222592 | 1 | 1 | 0 | 1 |
| 2026-05-08 14:30:00+00:00 | unpaired_capacity_path_effect |  |  |  |  |  | 0.0 | TASK617/AMD/20260506T133000Z | AMD | ai_semiconductors | mechanism_reinforcing_company_positive | 50 | 10.91690173272684 | -10.91690173272684 | 0 | 0 | 0 | 1 |
| 2025-10-02 14:30:00+00:00 | unpaired_capacity_path_effect |  |  |  |  |  | 0.0 | TASK617/RTX/20250930T133000Z | RTX | aerospace_defense_space | company_positive_needs_confirmation | 50 | 10.287363195607108 | -10.287363195607108 | 0 | 0 | 0 | 1 |
| 2025-03-06 14:30:00+00:00 | unpaired_capacity_path_effect | TASK617/OKTA/20250304T143000Z | OKTA | cybersecurity | company_positive_needs_confirmation | 30 | -10.284891904235732 |  |  |  |  |  | 0.0 | -10.284891904235732 | 1 | 1 | 0 | 1 |
| 2025-03-07 14:30:00+00:00 | unpaired_capacity_path_effect | TASK617/AMGN/20250305T144500Z | AMGN | biotech_glp1_healthcare | company_positive_needs_confirmation | 30 | -10.0563598745196 |  |  |  |  |  | 0.0 | -10.0563598745196 | 1 | 1 | 0 | 1 |
| 2025-07-09 14:30:00+00:00 | unpaired_capacity_path_effect |  |  |  |  |  | 0.0 | TASK617/AFRM/20250707T134500Z | AFRM | crypto_fintech | company_quality_price_confirmed | 50 | 7.74727006392045 | -7.74727006392045 | 0 | 0 | 0 | 1 |
| 2025-03-10 14:30:00+00:00 | unpaired_capacity_path_effect | TASK617/OKTA/20250306T150000Z | OKTA | cybersecurity | company_positive_needs_confirmation | 30 | -7.19309085865774 |  |  |  |  |  | 0.0 | -7.19309085865774 | 1 | 1 | 1 | 1 |
| 2025-12-26 14:30:00+00:00 | unpaired_capacity_path_effect |  |  |  |  |  | 0.0 | TASK617/ASTS/20251223T143000Z | ASTS | aerospace_defense_space | company_quality_price_confirmed | 50 | 6.2792223645495 | -6.2792223645495 | 0 | 0 | 0 | 1 |
| 2025-05-30 14:30:00+00:00 | same_timestamp_displacement | TASK617/CEG/20250528T133000Z | CEG | power_grid_electrification | mechanism_offsetting_company_positive | 20 | 2.56528335971967 | TASK617/ARM/20250528T163000Z | ARM | ai_semiconductors | sparse_mechanism_cell | 50 | 7.4695933863355295 | -4.90431002661586 | 1 | 0 | 1 | 1 |
| 2025-11-20 14:30:00+00:00 | unpaired_capacity_path_effect | TASK617/LLY/20251118T161500Z | LLY | biotech_glp1_healthcare | company_positive_needs_confirmation | 30 | -2.88546173518949 |  |  |  |  |  | 0.0 | -2.88546173518949 | 0 | 0 | 0 | 1 |

### MDD Attribution

| bucket | row_count | avg_return_delta_pct_point | sum_return_delta_pct_point | open_during_priority_mdd_trough_count | entry_in_priority_mdd_interval_count | exit_in_priority_mdd_interval_count |
| --- | --- | --- | --- | --- | --- | --- |
| added_by_priority | 27 | 13.709575315355574 | 370.1585335146005 | 4 | 9 | 8 |
| preserved | 27 | 0.0 | 0.0 | 1 | 2 | 3 |
| removed_by_priority | 27 | -5.831719263367556 | -157.456420110924 | 4 | 7 | 5 |
| negative_displacement_pairs | 22 | -20.685147297883574 | -455.07324055343867 | 5 | 9 | 7 |

### Risk Findings

| finding_id | finding | evidence | research_implication | promotion_status |
| --- | --- | --- | --- | --- |
| F1 | priority_changes_capacity_path | added=27 removed=27 | Priority affects actual accepted trades, so the relation engine is connected to capital allocation. | research_useful |
| F2 | drawdown_penalty_blocks_promotion | priority final capital improves but MDD worsens versus baseline | Need risk caps before promotion; return improvement alone is insufficient. | promotion_blocker |
| F3 | negative_displacement_pairs_exist | negative_pairs=22 | Next risk cap should target bad displacement conditions, not broad relation-state filtering. | research_useful |

## No-Background Decision-Maker Report

수익은 늘었는데 낙폭도 커진 이유를 뜯었습니다.

핵심은 relation priority가 실제 accepted trade를 바꿨다는 점입니다.

그런데 일부 slot 교체가 낙폭 구간에서 위험을 키웠습니다.

그래서 다음은 새 매수/청산이 아니라, 나쁜 slot 교체를 막는 risk cap입니다.

## Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| mdd_interval_identified | 1 | 2025-02-06 14:30:00+00:00 to 2025-06-03 00:00:00+00:00 | priority peak and trough timestamps |
| accepted_delta_built | 1 | rows=81 | accepted trade delta rows |
| displacement_pairs_built | 1 | rows=47 | slot displacement pair rows |
| drawdown_not_worse | 0 | mdd_penalty=-9.88 | priority must not worsen MDD before promotion |
| strategy_accepted | 0 | diagnostic attribution only | requires accepted strategy gates and live readiness |

## Artifact Manifest

- `priority_equity_curve_comparison.csv`
- `priority_mdd_interval_summary.csv`
- `accepted_trade_delta.csv`
- `priority_mdd_active_trade_inventory.csv`
- `slot_displacement_pairs.csv`
- `mdd_interval_trade_attribution.csv`
- `risk_cap_research_findings.csv`
- `task_665_decision.csv`
- `task_665_pass_fail_matrix.csv`
- `artifact_manifest.csv`
