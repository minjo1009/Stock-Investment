# Task 403 - Multi-Archetype Continuation Portfolio Discovery

## Required Answers
- Did we use inferred lifecycle matching? `NO`
- Did we select only one best combo? `NO`
- Are unlabeled rows treated as negative? `NO`
- Did we make a deployment claim? `NO`

## Decision
task_403_verdict,evaluation_status,task401_label_coverage_sufficient,task401_exact_label_coverage_rate,archetype_candidate_count,practical_archetype_candidate_count,archetype_set_count,unique_archetype_combo_tested_count,best_archetype_set_name,best_archetype_set_add_scale_success_rate,best_archetype_set_false_positive_rate,selected_only_one_combo_flag,symbol_date_price_time_fallback_used_flag,label_used_for_archetype_assignment_flag,leakage_audit_pass_flag,deployment_claim_flag,strategy_acceptance_status,next_priority
COMPLETE_PASS,MULTI_ARCHETYPE_PORTFOLIO_DISCOVERY_DIAGNOSTIC,NO,0.0,38,14,6,30,high_precision_low_capacity_set,0.2580565195835399,0.7419434804164601,0,0,0,1,0,NOT_DEPLOYMENT_READY,validate_selected_archetype_sets_only_after_exact_label_coverage_is_sufficient

## Archetype Set Quality
archetype_set_name,lifecycle_count,add_scale_success_count,add_scale_success_rate,false_positive_rate,avg_net_return_from_entry,compounded_net_pnl,add_scale_retention_rate
balanced_precision_recall_set,15797,3102,0.19227669993181679,0.8077233000681833,-0.005494607078879594,-1.0,0.19227669993181679
broad_capacity_set,19498,3549,0.17789473684210527,0.8221052631578948,-0.005980201593660073,-1.0,0.17789473684210527
defensive_low_fp_set,12207,2636,0.21270071814734123,0.7872992818526587,-0.00485178693620857,-1.0,0.21270071814734123
high_precision_low_capacity_set,3996,1041,0.2580565195835399,0.7419434804164601,-0.0029448447932480582,-0.999998364395513,0.2580565195835399
top_10_archetype_set,11069,2319,0.20607837909890697,0.7939216209010931,-0.004870327731035323,-1.0,0.20607837909890697
top_20_archetype_set,16754,3302,0.19276123759486283,0.8072387624051371,-0.0055675583184617615,-1.0,0.19276123759486283

## Concentration Audit
archetype_set_name,lifecycle_count,theme_count,symbol_count,max_theme_share,max_symbol_share,concentration_risk_flag
balanced_precision_recall_set,15797,10,145,0.18205988478825094,0.01449642337152624,0
broad_capacity_set,19498,10,145,0.17345368755769822,0.013898861421684275,0
defensive_low_fp_set,12207,10,145,0.20283443925616448,0.0162202015237159,0
high_precision_low_capacity_set,3996,10,145,0.22597597597597596,0.01826826826826827,0
top_10_archetype_set,11069,10,145,0.19071280151775227,0.015087180413768182,0
top_20_archetype_set,16754,10,145,0.1799570251880148,0.014265250089530859,0