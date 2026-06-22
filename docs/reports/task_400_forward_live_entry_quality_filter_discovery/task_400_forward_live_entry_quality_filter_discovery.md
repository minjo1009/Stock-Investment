# Task 400 - Forward-Live Entry Quality Filter Discovery

## Decision
task_400_verdict,evaluation_status,entry_quality_lifecycle_count,validation_count,recent_oos_count,validation_positive_rate,recent_oos_positive_rate,best_non_oracle_candidate_filter,best_non_oracle_validation_positive_rate,best_non_oracle_recent_oos_positive_rate,leakage_audit_pass_flag,threshold_optimization_used_flag,oracle_filter_used_for_acceptance_flag,deployment_claim_flag,strategy_acceptance_status,next_priority
COMPLETE_PASS,ENTRY_FILTER_DIAGNOSTIC_ONLY,21220,3602,5090,0.17240421987784565,0.20884086444007857,exclude_high_fp_symbols,0.2222222222222222,0.24792161520190023,1,0,0,0,NOT_DEPLOYMENT_READY,task401_simulate_best_non_oracle_filter_as_policy

## Label Summary
anchored_split,entry_quality_label,lifecycle_count,positive_rate
recent_oos,add_scale_success,1033,1.0
recent_oos,weak_or_false_positive,3927,0.0
train,add_scale_success,2079,1.0
train,weak_or_false_positive,10182,0.0
validation,add_scale_success,607,1.0
validation,weak_or_false_positive,2922,0.0

## Filter Candidate Audit
candidate_filter_name,anchored_split,candidate_count,positive_rate,false_positive_rate,validation_count,validation_positive_rate,validation_lift_vs_baseline,recent_oos_count,recent_oos_positive_rate,recent_oos_lift_vs_baseline,add_scale_retention_rate,oracle_flag,diagnostic_only_flag
exclude_high_fp_symbols,all,14017,0.22051794249839482,0.7794820575016052,2394,0.2222222222222222,0.049818002344376555,3368,0.24792161520190023,0.03908075076182166,0.8129931614939505,0,1
exclude_high_fp_themes,all,16850,0.19240356083086052,0.8075964391691395,2911,0.18756441085537615,0.015160190977530491,3916,0.21527068437180796,0.006429819931729391,0.8527091004734351,0,1
theme_rank_top3,all,12561,0.19154525913541914,0.8084547408645808,2188,0.18510054844606946,0.012696328568223808,2776,0.20785302593659943,-0.0009878385034791382,0.6328248290373487,0,1
theme_rank_top3_and_positive_theme_return,all,12561,0.19154525913541914,0.8084547408645808,2188,0.18510054844606946,0.012696328568223808,2776,0.20785302593659943,-0.0009878385034791382,0.6328248290373487,0,1
broad_breadth_ge_65pct,all,16458,0.18039859035119699,0.819601409648803,2552,0.17515673981191224,0.002752519934066583,4147,0.21533638775018085,0.00649552331010228,0.7809047869542346,0,1
moderate_intraday_range_below_median,all,10612,0.19148134187712024,0.8085186581228798,1998,0.17317317317317318,0.0007689532953275291,2485,0.2181086519114688,0.009267787471390232,0.5344555497106785,0,1
regular_session_after_1430_utc,all,12350,0.1617813765182186,0.8382186234817814,1944,0.16512345679012347,-0.007280763087722186,2859,0.19167541098286114,-0.017165453457217428,0.5255128879537085,0,1
liquidity_expansion_ge_110,all,13540,0.17001477104874446,0.8299852289512555,2155,0.15591647331786543,-0.016487746559980226,3681,0.21678891605541972,0.00794805161534115,0.6054708048395582,0,1
theme_rank_top3_low_cost,all,6192,0.1532622739018088,0.8467377260981912,1209,0.13895781637717122,-0.03344640350067443,1323,0.18518518518518517,-0.023655679254893397,0.24960547080483955,0,1
low_estimated_cost_below_median,all,10611,0.1471114880784092,0.8528885119215908,2048,0.1337890625,-0.038615157377845655,2488,0.1877009646302251,-0.02113989980985348,0.41057338243029984,0,1
oracle_add_scale_upper_bound,all,3802,1.0,0.0,621,1.0,0.8275957801221543,1063,1.0,0.7911591355599215,1.0,1,1

## Leakage Audit
field,present_in_source,present_in_feature_panel,allowed_as_feature,leakage_pass_flag
exit_ts,1,0,0,1
bars_held,1,0,0,1
add_flag,1,0,0,1
scale_flag,1,0,0,1
reduce_flag,1,0,0,1
exit_reason,1,0,0,1
return_from_entry,1,0,0,1
net_return_from_entry,1,0,0,1
positive_return_flag,1,0,0,1
post_cost_positive_return_flag,1,0,0,1
add_scale_flag,1,0,0,1
lifecycle_path,1,0,0,1
failure_group,1,0,0,1
hindsight_strict_regime_gate_flag,1,0,0,1
theme_day_return,1,0,0,1
theme_rank,1,0,0,1
theme_leadership_regime,1,0,0,1
breadth_positive_rate,1,0,0,1
avg_intraday_range,1,0,0,1
liquidity_ratio_20d,1,0,0,1
lifecycle_id,1,1,1,1
symbol,1,1,1,1
theme,1,1,1,1
role,1,1,1,1
entry_ts,1,1,1,1
anchored_split,1,1,1,1
entry_hour,1,1,1,1
entry_minute,1,1,1,1
entry_time_bucket,1,1,1,1
forward_live_breadth_positive_rate,1,1,1,1
forward_live_avg_symbol_return,1,1,1,1
forward_live_avg_intraday_range,1,1,1,1
forward_live_liquidity_ratio,1,1,1,1
forward_live_breadth_regime,1,1,1,1
forward_live_volatility_regime,1,1,1,1
forward_live_liquidity_regime,1,1,1,1
forward_live_market_regime,1,1,1,1
forward_live_theme_return,1,1,1,1
forward_live_theme_rank,1,1,1,1
forward_live_theme_leadership_regime,1,1,1,1
base_round_trip_cost,1,1,1,1
volatility_penalty,1,1,1,1
spread_penalty,1,1,1,1
estimated_total_cost,1,1,1,1
entry_quality_target,0,1,1,1
entry_quality_label,0,1,1,1