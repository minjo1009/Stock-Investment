# Task667 Dynamic Risk Development

## Decision Summary

- Verdict: `DYNAMIC_RISK_TESTED_NO_PROMOTION_CANDIDATE`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Baseline: `$7639.62`, MDD `-23.76%`.
- Best candidate: `task666_active_relation_cap3_reference` = `$10887.47`, MDD `-30.52%`.
- Best promotion-allowed candidate: `task666_active_relation_cap3_reference` = `$10887.47`, MDD `-30.52%`.
- Promotion candidates: `0`.

## Quant Expert Report

Task667 tests dynamic relation caps, scarce-slot admission hurdles, and risk-proxy sizing while preserving Task639 entry timing and exits.

### Candidate Grid

| candidate_name | split_name | candidate_type | initial_capital_usd | source_trade_count | accepted_trade_count | avg_size_multiplier | final_capital_usd | capital_return_pct | max_drawdown_pct | entry_reduce_failure_rate | qqq_final_capital_usd | beats_qqq_flag | diagnostic_only_flag | return_tuned_flag | fixed_hold_or_timing_override_flag | label_used_in_assignment_flag | return_used_in_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| task666_active_relation_cap3_reference | all | reference | 1000.0 | 1621 | 51 | 1.0 | 10887.474713480713 | 988.7474713480714 | -30.524857842425657 | 0.3333333333333333 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| diagnostic_dynamic_relation_cap_market_account | all | diagnostic_path_control | 1000.0 | 1621 | 50 | 1.0 | 8793.344016040966 | 779.3344016040967 | -32.429733675122606 | 0.36 | 1606.8278306897957 | 1 | 1 | 0 | 0 | 0 | 0 |
| slot_hurdle_weak_only_scarce_slot | all | predeclared_slot_hurdle | 1000.0 | 1621 | 49 | 1.0 | 8055.759591918491 | 705.5759591918492 | -35.53286010207651 | 0.32653061224489793 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| dynamic_relation_cap_market_only | all | predeclared_dynamic_cap | 1000.0 | 1621 | 51 | 1.0 | 7899.063842567857 | 689.9063842567857 | -32.429733675122606 | 0.3333333333333333 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| dynamic_cap_slot_hurdle_combo | all | predeclared_combo | 1000.0 | 1621 | 49 | 1.0 | 7824.016864698112 | 682.4016864698111 | -37.36840871710736 | 0.3469387755102041 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| relation_cap3_contextual_risk_sizing | all | predeclared_sizing | 1000.0 | 1621 | 51 | 0.9002352941176471 | 7804.214364941086 | 680.4214364941087 | -29.02155635046225 | 0.3333333333333333 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| baseline_task639 | all | baseline | 1000.0 | 1621 | 54 | 1.0 | 7639.620310821465 | 663.9620310821465 | -23.755747663170702 | 0.35185185185185186 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| relation_cap3_risk_proxy_sizing | all | predeclared_sizing | 1000.0 | 1621 | 51 | 0.8004166666666668 | 6832.029057164225 | 583.2029057164226 | -26.9994792293511 | 0.3333333333333333 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| dynamic_cap_hurdle_risk_sizing_combo | all | predeclared_combo | 1000.0 | 1621 | 49 | 0.8961632653061224 | 5949.69605860855 | 494.9696058608549 | -33.44757042447556 | 0.3469387755102041 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| slot_hurdle_quality_scarce_slot | all | predeclared_slot_hurdle | 1000.0 | 1621 | 47 | 1.0 | 5677.341759444566 | 467.73417594445664 | -31.35964789744744 | 0.3829787234042553 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| diagnostic_equity_drawdown_deleverage | all | diagnostic_path_control | 1000.0 | 1621 | 42 | 0.6519196428571428 | 3289.3311607568644 | 228.93311607568646 | -24.047560994094486 | 0.42857142857142855 | 1606.8278306897957 | 1 | 1 | 0 | 0 | 0 | 0 |
| task666_active_relation_cap3_reference | recent_oos | reference | 1000.0 | 332 | 10 | 1.0 | 1541.4394915288256 | 54.14394915288256 | -1.0957772237519925 | 0.2 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| dynamic_relation_cap_market_only | recent_oos | predeclared_dynamic_cap | 1000.0 | 332 | 10 | 1.0 | 1541.4394915288256 | 54.14394915288256 | -1.0957772237519925 | 0.2 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| slot_hurdle_quality_scarce_slot | recent_oos | predeclared_slot_hurdle | 1000.0 | 332 | 10 | 1.0 | 1541.4394915288256 | 54.14394915288256 | -1.0957772237519925 | 0.2 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| slot_hurdle_weak_only_scarce_slot | recent_oos | predeclared_slot_hurdle | 1000.0 | 332 | 10 | 1.0 | 1541.4394915288256 | 54.14394915288256 | -1.0957772237519925 | 0.2 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| relation_cap3_contextual_risk_sizing | recent_oos | predeclared_sizing | 1000.0 | 332 | 10 | 1.0 | 1541.4394915288256 | 54.14394915288256 | -1.0957772237519925 | 0.2 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| dynamic_cap_slot_hurdle_combo | recent_oos | predeclared_combo | 1000.0 | 332 | 10 | 1.0 | 1541.4394915288256 | 54.14394915288256 | -1.0957772237519925 | 0.2 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| dynamic_cap_hurdle_risk_sizing_combo | recent_oos | predeclared_combo | 1000.0 | 332 | 10 | 1.0 | 1541.4394915288256 | 54.14394915288256 | -1.0957772237519925 | 0.2 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| diagnostic_dynamic_relation_cap_market_account | recent_oos | diagnostic_path_control | 1000.0 | 332 | 10 | 1.0 | 1541.4394915288256 | 54.14394915288256 | -1.0957772237519925 | 0.2 | 1124.192829329964 | 1 | 1 | 0 | 0 | 0 | 0 |
| baseline_task639 | recent_oos | baseline | 1000.0 | 332 | 10 | 1.0 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | 0.1 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |

### Promotion Report

| candidate_name | all_final_capital_usd | all_max_drawdown_pct | all_accepted_trade_count | all_avg_size_multiplier | all_entry_reduce_failure_rate | all_beats_qqq_flag | recent_oos_final_capital_usd | recent_oos_max_drawdown_pct | recent_oos_accepted_trade_count | recent_oos_avg_size_multiplier | recent_oos_entry_reduce_failure_rate | recent_oos_beats_qqq_flag | validation_final_capital_usd | validation_max_drawdown_pct | validation_accepted_trade_count | validation_avg_size_multiplier | validation_entry_reduce_failure_rate | validation_beats_qqq_flag | beats_all_task639_flag | all_drawdown_not_worse_flag | validation_improves_task639_flag | recent_oos_improves_task639_flag | validation_drawdown_not_worse_flag | recent_oos_drawdown_not_worse_flag | promotion_allowed_flag | promotion_candidate_flag | failure_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| task666_active_relation_cap3_reference | 10887.474713480713 | -30.524857842425657 | 51.0 | 1.0 | 0.3333333333333333 | 1.0 | 1541.4394915288256 | -1.0957772237519925 | 10.0 | 1.0 | 0.2 | 1.0 | 1327.5223368015004 | -5.866934869678831 | 13.0 | 1.0 | 0.15384615384615385 | 1.0 | 1 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | full_period_drawdown_worse |
| diagnostic_dynamic_relation_cap_market_account | 8793.344016040966 | -32.429733675122606 | 50.0 | 1.0 | 0.36 | 1.0 | 1541.4394915288256 | -1.0957772237519925 | 10.0 | 1.0 | 0.2 | 1.0 | 1441.1653829501581 | -5.866934869678831 | 13.0 | 1.0 | 0.15384615384615385 | 1.0 | 1 | 0 | 1 | 1 | 1 | 0 | 0 | 0 | diagnostic_or_return_tuned_not_promotion_eligible |
| slot_hurdle_weak_only_scarce_slot | 8055.759591918491 | -35.53286010207651 | 49.0 | 1.0 | 0.32653061224489793 | 1.0 | 1541.4394915288256 | -1.0957772237519925 | 10.0 | 1.0 | 0.2 | 1.0 | 1327.5223368015004 | -5.866934869678831 | 13.0 | 1.0 | 0.15384615384615385 | 1.0 | 1 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | full_period_drawdown_worse |
| dynamic_relation_cap_market_only | 7899.063842567857 | -32.429733675122606 | 51.0 | 1.0 | 0.3333333333333333 | 1.0 | 1541.4394915288256 | -1.0957772237519925 | 10.0 | 1.0 | 0.2 | 1.0 | 1441.1653829501581 | -5.866934869678831 | 13.0 | 1.0 | 0.15384615384615385 | 1.0 | 1 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | full_period_drawdown_worse |
| dynamic_cap_slot_hurdle_combo | 7824.016864698112 | -37.36840871710736 | 49.0 | 1.0 | 0.3469387755102041 | 1.0 | 1541.4394915288256 | -1.0957772237519925 | 10.0 | 1.0 | 0.2 | 1.0 | 1441.1653829501581 | -5.866934869678831 | 13.0 | 1.0 | 0.15384615384615385 | 1.0 | 1 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | full_period_drawdown_worse |
| relation_cap3_contextual_risk_sizing | 7804.214364941086 | -29.02155635046225 | 51.0 | 0.9002352941176471 | 0.3333333333333333 | 1.0 | 1541.4394915288256 | -1.0957772237519925 | 10.0 | 1.0 | 0.2 | 1.0 | 1303.7125884659954 | -5.866934869678831 | 13.0 | 0.9692307692307693 | 0.15384615384615385 | 1.0 | 1 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | full_period_drawdown_worse |
| baseline_task639 | 7639.620310821465 | -23.755747663170702 | 54.0 | 1.0 | 0.35185185185185186 | 1.0 | 1531.9029143138666 | -0.811391994497368 | 10.0 | 1.0 | 0.1 | 1.0 | 1069.2312936091898 | -7.363321689343804 | 15.0 | 1.0 | 0.4 | 1.0 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 0 | full_period_return_not_better |
| relation_cap3_risk_proxy_sizing | 6832.029057164225 | -26.9994792293511 | 51.0 | 0.8004166666666668 | 0.3333333333333333 | 1.0 | 1436.0388237121424 | -1.1215957692505385 | 10.0 | 0.94725 | 0.2 | 1.0 | 1264.6185938750202 | -5.453676450048894 | 13.0 | 0.9084615384615383 | 0.15384615384615385 | 1.0 | 0 | 0 | 1 | 0 | 1 | 0 | 1 | 0 | full_period_return_not_better |
| dynamic_cap_hurdle_risk_sizing_combo | 5949.69605860855 | -33.44757042447556 | 49.0 | 0.8961632653061224 | 0.3469387755102041 | 1.0 | 1541.4394915288256 | -1.0957772237519925 | 10.0 | 1.0 | 0.2 | 1.0 | 1394.6270253849216 | -5.866934869678831 | 13.0 | 0.9692307692307693 | 0.15384615384615385 | 1.0 | 0 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | full_period_return_not_better |
| slot_hurdle_quality_scarce_slot | 5677.341759444566 | -31.35964789744744 | 47.0 | 1.0 | 0.3829787234042553 | 1.0 | 1541.4394915288256 | -1.0957772237519925 | 10.0 | 1.0 | 0.2 | 1.0 | 1368.1546457838026 | -5.531838794604981 | 14.0 | 1.0 | 0.14285714285714285 | 1.0 | 0 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | full_period_return_not_better |
| diagnostic_equity_drawdown_deleverage | 3289.3311607568644 | -24.047560994094486 | 42.0 | 0.6519196428571428 | 0.42857142857142855 | 1.0 | 1436.0388237121424 | -1.1215957692505385 | 10.0 | 0.94725 | 0.2 | 1.0 | 1264.6185938750202 | -5.453676450048894 | 13.0 | 0.9084615384615383 | 0.15384615384615385 | 1.0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | diagnostic_or_return_tuned_not_promotion_eligible |

### MDD Windows

| candidate_name | split_scope | mdd_peak_ts | mdd_trough_ts | peak_equity | trough_equity | max_drawdown_pct |
| --- | --- | --- | --- | --- | --- | --- |
| dynamic_cap_slot_hurdle_combo | all | 2025-02-05 00:00:00+00:00 | 2025-05-30 00:00:00+00:00 | 5.268540322830838 | 3.299770641569803 | -37.36840871710736 |
| slot_hurdle_weak_only_scarce_slot | all | 2025-02-05 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | 5.268540322830838 | 3.3964772604978664 | -35.53286010207651 |
| dynamic_cap_hurdle_risk_sizing_combo | all | 2025-02-05 00:00:00+00:00 | 2025-05-30 00:00:00+00:00 | 4.141828547659916 | 2.756487527320332 | -33.44757042447556 |
| diagnostic_dynamic_relation_cap_market_account | all | 2025-02-06 00:00:00+00:00 | 2025-05-30 00:00:00+00:00 | 5.421009611845537 | 3.6629906322212316 | -32.429733675122606 |
| dynamic_relation_cap_market_only | all | 2025-02-06 00:00:00+00:00 | 2025-05-30 00:00:00+00:00 | 5.421009611845537 | 3.6629906322212316 | -32.429733675122606 |
| slot_hurdle_quality_scarce_slot | all | 2025-02-05 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | 4.30767199956448 | 2.9568012279241254 | -31.35964789744744 |
| task666_active_relation_cap3_reference | all | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | 5.421009611845537 | 3.7662541342054556 | -30.524857842425657 |
| relation_cap3_contextual_risk_sizing | all | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | 4.2266493836241255 | 3.000009951019184 | -29.02155635046225 |
| relation_cap3_risk_proxy_sizing | all | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | 4.019524374990636 | 2.934273726246335 | -26.9994792293511 |
| diagnostic_equity_drawdown_deleverage | all | 2025-02-06 00:00:00+00:00 | 2025-07-10 00:00:00+00:00 | 4.019524374990636 | 3.052926799242268 | -24.047560994094486 |
| baseline_task639 | all | 2025-02-07 00:00:00+00:00 | 2025-05-30 00:00:00+00:00 | 5.27633237788818 | 4.02290017232689 | -23.755747663170702 |
| diagnostic_equity_drawdown_deleverage | recent_oos | 2026-06-05 00:00:00+00:00 | 2026-06-05 00:00:00+00:00 | 1.4360388237121424 | 1.3913658095112156 | -1.1215957692505385 |
| relation_cap3_risk_proxy_sizing | recent_oos | 2026-06-05 00:00:00+00:00 | 2026-06-05 00:00:00+00:00 | 1.4360388237121424 | 1.3913658095112156 | -1.1215957692505385 |
| diagnostic_dynamic_relation_cap_market_account | recent_oos | 2026-04-10 00:00:00+00:00 | 2026-04-10 00:00:00+00:00 | 1.1280880968702642 | 1.0055804131477368 | -1.0957772237519925 |
| dynamic_cap_hurdle_risk_sizing_combo | recent_oos | 2026-04-10 00:00:00+00:00 | 2026-04-10 00:00:00+00:00 | 1.1280880968702642 | 1.0055804131477368 | -1.0957772237519925 |
| dynamic_cap_slot_hurdle_combo | recent_oos | 2026-04-10 00:00:00+00:00 | 2026-04-10 00:00:00+00:00 | 1.1280880968702642 | 1.0055804131477368 | -1.0957772237519925 |
| dynamic_relation_cap_market_only | recent_oos | 2026-04-10 00:00:00+00:00 | 2026-04-10 00:00:00+00:00 | 1.1280880968702642 | 1.0055804131477368 | -1.0957772237519925 |
| relation_cap3_contextual_risk_sizing | recent_oos | 2026-04-10 00:00:00+00:00 | 2026-04-10 00:00:00+00:00 | 1.1280880968702642 | 1.0055804131477368 | -1.0957772237519925 |
| slot_hurdle_quality_scarce_slot | recent_oos | 2026-04-10 00:00:00+00:00 | 2026-04-10 00:00:00+00:00 | 1.1280880968702642 | 1.0055804131477368 | -1.0957772237519925 |
| slot_hurdle_weak_only_scarce_slot | recent_oos | 2026-04-10 00:00:00+00:00 | 2026-04-10 00:00:00+00:00 | 1.1280880968702642 | 1.0055804131477368 | -1.0957772237519925 |

### MDD Interval Audit

| candidate_name | audit_group | group_value | active_trade_count | avg_return_costed_pct | sum_position_capital_fraction | avg_size_multiplier |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_task639 | mechanism_relation_state | company_positive_needs_confirmation | 5 | -7.360368966944139 | 4.723718035445517 | 1.0 |
| baseline_task639 | mechanism_relation_state | company_quality_price_confirmed | 3 | 16.17119537974209 | 2.865982746157018 | 1.0 |
| baseline_task639 | mechanism_relation_state | sparse_mechanism_cell | 2 | 4.5650776469290495 | 1.3988812790206688 | 1.0 |
| baseline_task639 | mechanism_relation_state | mechanism_offsetting_company_positive | 1 | 31.211509826119787 | 0.8432139122849055 | 1.0 |
| baseline_task639 | mechanism_relation_state | mechanism_reinforcing_company_positive | 1 | -26.97397380304668 | 0.9594273668570181 | 1.0 |
| baseline_task639 | symbol | AMGN | 3 | -8.816575360197094 | 3.0279978286122193 | 1.0 |
| baseline_task639 | symbol | AMZN | 2 | -25.384416137098842 | 2.0235300937618397 | 1.0 |
| baseline_task639 | symbol | DDOG | 2 | -24.697119082177664 | 1.9188547337140363 | 1.0 |
| baseline_task639 | symbol | ASML | 1 | 1.6413255206218897 | 0.8226849150279566 | 1.0 |
| baseline_task639 | symbol | ASTS | 1 | 83.88178484477822 | 0.8577439721002594 | 1.0 |
| baseline_task639 | symbol | ETN | 1 | 31.211509826119787 | 0.8432139122849055 | 1.0 |
| baseline_task639 | symbol | NOC | 1 | 3.40718929389442 | 0.8577439721002594 | 1.0 |
| baseline_task639 | symbol | TEAM | 1 | 31.55041965516675 | 0.4394539121636507 | 1.0 |
| baseline_task639 | theme_id | biotech_glp1_healthcare | 3 | -8.816575360197094 | 3.0279978286122193 | 1.0 |
| baseline_task639 | theme_id | data_devops_software | 3 | -5.947939503062861 | 2.358308645877687 | 1.0 |
| baseline_task639 | theme_id | aerospace_defense_space | 2 | 43.64448706933632 | 1.7154879442005189 | 1.0 |
| baseline_task639 | theme_id | cloud_ai_platforms | 2 | -25.384416137098842 | 2.0235300937618397 | 1.0 |
| baseline_task639 | theme_id | ai_semiconductors | 1 | 1.6413255206218897 | 0.8226849150279566 | 1.0 |
| baseline_task639 | theme_id | power_grid_electrification | 1 | 31.211509826119787 | 0.8432139122849055 | 1.0 |
| diagnostic_dynamic_relation_cap_market_account | mechanism_relation_state | mechanism_reinforcing_company_positive | 5 | -7.55245228120888 | 4.966650574434183 | 1.0 |

## No-Background Decision-Maker Report

이번 작업은 active relation cap3를 더 똑똑하게 만들 수 있는지 본 테스트입니다.

시장 상태가 안 좋거나 계좌가 이미 맞고 있을 때 더 작게 들어가고, 마지막 slot은 더 까다롭게 쓰게 했습니다.

수익과 낙폭이 동시에 좋아져야 승격입니다. 하나만 좋아지면 연구용입니다.

## Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| no_fixed_hold_or_timing_override | 1 | violations=0 | preserve Task639 entry timing and exits |
| dynamic_cap_tested | 1 | market_account_dynamic,market_dynamic,none,static3 | dynamic relation cap candidates exist |
| slot_hurdle_tested | 1 | drawdown_hurdle,none,scarce_slot_quality,weak_scarce_slot | slot hurdle candidates exist |
| sizing_tested | 1 | contextual_risk_scaled,drawdown_scaled,equal,risk_proxy_scaled | risk proxy sizing candidates exist |
| allocation_audit_built | 1 | rows=28688 | allocation panel exists |
| sizing_audit_built | 1 | rows=800 | sizing audit exists |
| mdd_audit_built | 1 | rows=221 | MDD interval audit exists |
| no_return_tuned_promotion | 1 | return_tuned_promoted=0 | return-tuned candidate cannot promote |
| promotion_candidate_found | 0 | promotion_candidates=0 | candidate improves return drawdown validation and recent OOS |
| strategy_accepted | 0 | research diagnostic only | requires accepted strategy gates and live readiness |

## Artifact Manifest

- `task667_candidate_specs.csv`
- `task667_candidate_grid.csv`
- `task667_accepted_trades.csv`
- `task667_allocation_panel.csv`
- `task667_equity_curve.csv`
- `task667_sizing_audit.csv`
- `task667_promotion_report.csv`
- `task667_mdd_windows.csv`
- `task667_mdd_interval_audit.csv`
- `task667_promotion_blocker_report.md`
- `task_667_gpt_review_packet.md`
- `task_667_gpt_review_response.md`
- `task_667_decision.csv`
- `task_667_pass_fail_matrix.csv`
- `artifact_manifest.csv`
