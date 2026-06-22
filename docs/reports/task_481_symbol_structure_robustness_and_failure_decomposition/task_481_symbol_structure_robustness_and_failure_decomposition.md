# Task 481 - Symbol-Structure Robustness And Failure Decomposition

## Quant Expert Report
- Audits whether Task480 good symbol-structure configurations are stable across split/month/symbol/theme.
- Decomposes overextension plus volume climax, add-only weak outcomes, and entry-reduce failure root causes.
- Builds diagnostic-only policy candidates without overwriting labels.

## No-Background Decision-Maker Report
- This task checks whether the promising 15-minute chart structures are real enough to study further.
- It does not approve deployment.

## Task Decision
task_481_verdict,evaluation_status,exact_labeled_lifecycle_count,baseline_avg_net_return_pct,baseline_win_rate,baseline_add_scale_success_rate,baseline_entry_reduce_failure_rate,overextended_audit_rows,top_config_split_rows,add_only_decomposition_rows,entry_reduce_high_risk_structure_count,best_policy_candidate_name,best_policy_candidate_avg_net_return_pct,label_overwrite_flag,inferred_lifecycle_matching_used_flag,symbol_date_price_time_fallback_used_flag,leakage_audit_pass,deployment_claim_flag,strategy_acceptance_status
COMPLETE_PASS,SYMBOL_STRUCTURE_ROBUSTNESS_AND_FAILURE_DECOMPOSITION_DIAGNOSTIC,32580,-0.24476692081301715,0.41012891344383057,0.26206261510128914,0.37265193370165745,25,104,3,17,ALLOW_OVEREXTENDED_VOLUME_CLIMAX,0.781488797735704,0,0,0,1,0,DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY

## Policy Candidate Backtest Diagnostic
policy_candidate_name,lifecycle_count,avg_net_return_pct,win_rate,add_scale_success_rate,entry_reduce_failure_rate,false_positive_rate
ALLOW_OVEREXTENDED_VOLUME_CLIMAX,172,0.781488797735704,0.5290697674418605,0.5290697674418605,0.23837209302325582,0.4011627906976744
ALLOW_VOLUME_CONFIRMED_CLEAN_BREAKOUT,4554,-0.1413202107125206,0.41238471673254284,0.3458498023715415,0.3908651734738691,0.6144049187527448
REJECT_THIN_QUIET_FAILED_RECLAIM,19141,-0.32028135329864893,0.4007627605663236,0.2210438326106264,0.3687372655556136,0.6792748550232485
REJECT_ONE_BAR_POP_SHOCK,9846,-0.31493716611599526,0.40006093845216334,0.226691042047532,0.37294332723948814,0.6775340239691245
WATCH_STRONG_CLOSE_BUT_QUIET,12441,-0.30148838983658766,0.4021380917932642,0.24740776464914396,0.37384454625833935,0.6639337673820432

## Add Only Weak Decomposition
add_only_diagnostic_class,lifecycle_count,avg_net_return_pct,win_rate,near_scale_add_only_available_flag
failed_add_only,2736,-1.4990260765378898,0.0,0
profitable_add_only,2984,0.9942185960717699,1.0,0
weak_positive_add_only,1108,0.2697802369935867,1.0,0

## Entry Reduce Avoidable Vs Unavoidable
avoidability_bucket,lifecycle_count,avg_net_return_pct,severe_loss_rate
avoidable_ohlcv_structure,12133,-2.296039744393948,0.8065606197972471
not_separated_by_current_ohlcv_structure,8,-2.8846391011297063,1.0