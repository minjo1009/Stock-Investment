# Task 407 - Raw-Native Vectorized Rebuild

## Quant Expert Report
- Raw-native decisions and lifecycle labels were regenerated without Task401 skeleton.
- Labels use exact newly generated lifecycle IDs only.

## No-Background Decision-Maker Report
- This rebuild tests whether the strategy can be evaluated directly from raw bars.
- It remains diagnostic-only because quote/spread/status raw data is still missing.

## Decision
task_407_verdict,evaluation_status,regular_raw_bar_count,raw_native_decision_count,raw_native_allow_count,raw_native_labeled_lifecycle_count,task401_skeleton_used_flag,inferred_matching_used_flag,label_coverage_rate,best_combo_state_min30,best_combo_avg_net_return_min30,deployment_claim_flag,strategy_acceptance_status
COMPLETE_PASS,RAW_NATIVE_VECTORIZED_REBUILD_DIAGNOSTIC,2201580,168909,84686,32580,0,0,0.3847153012304277,mixed_breadth x weak_theme x late_chase x controlled_vol x neutral_tradability,0.006993849286426981,0,RAW_NATIVE_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY

## Label Quality
lifecycle_outcome_class,lifecycle_count,avg_net_return_from_entry
entry_reduce_failure,12141,-0.022964275868166434
add_scale_success,8538,0.02590474983892046
add_only_weak,6828,-0.0012238877447870592
post_cost_positive_no_add_scale,2660,0.0010768434548766635
post_cost_false_positive,2413,-0.006886962983315938

## Entry Reduce Failure Decomposition
state_value,lifecycle_count,entry_reduce_failure_rate,add_scale_success_rate,avg_net_return_from_entry,state_axis
broad_risk_on,15739,0.3676853675582947,0.2582756210686829,-0.0025413169888616597,market_state
mixed_breadth,12601,0.379096897071661,0.2636298706451869,-0.0025833549192471566,market_state
narrow_risk_on,204,0.3137254901960784,0.3872549019607843,0.007864128386683631,market_state
weak_risk_off,4036,0.3748761149653122,0.26560951437066405,-0.0021800548975811794,market_state
isolated_symbol_strength,976,0.4088114754098361,0.26844262295081966,-0.004286261283560121,theme_state
theme_participation,16321,0.36388701672691626,0.24477666809631762,-0.0023755281718110493,theme_state
true_theme_leader,13333,0.3793594839870997,0.2829820745518638,-0.002318688395350665,theme_state
weak_theme,1950,0.382051282051282,0.2605128205128205,-0.003013130318352837,theme_state
early_confirmation,10258,0.37287970364593487,0.21339442386430105,-0.0032903098477486277,entry_state
exhaustion_breakout,8192,0.3834228515625,0.2645263671875,-0.0031084420408984976,entry_state
healthy_momentum_continuation,4342,0.3671119299861815,0.3028558268079226,-0.0013541412308907918,entry_state
late_chase,4051,0.3806467538879289,0.3056035546778573,-0.0008177148929500794,entry_state
mixed_entry,532,0.37593984962406013,0.32142857142857145,-0.0018379303287054288,entry_state
pullback_reclaim,5205,0.35331412103746396,0.2801152737752161,-0.0019901410168867376,entry_state
controlled_vol,21406,0.3700831542558161,0.2554423993272914,-0.0022782574871109055,risk_state
healthy_expansion,8494,0.3720273133976925,0.2646574052272192,-0.0023144895924137416,risk_state
range_exhaustion,1759,0.3962478681068789,0.33598635588402503,-0.0045850247876929075,risk_state
volatility_stress,921,0.3930510314875136,0.250814332247557,-0.0035313244650065916,risk_state
friction_heavy,6427,0.37980395207717443,0.26575385094134124,-0.0026250855540492423,tradability_state
liquid_clean,8777,0.3724507234818275,0.23914777258744446,-0.0034054331132897164,tradability_state
neutral_tradability,17376,0.3701081952117864,0.2722720994475138,-0.001898259179883917,tradability_state