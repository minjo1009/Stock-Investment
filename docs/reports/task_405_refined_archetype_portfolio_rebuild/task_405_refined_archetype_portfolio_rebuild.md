# Task 405 - Refined Archetype Portfolio Rebuild

## Required Answers
- Did refined archetypes reduce entry_reduce_failure? See decision table.
- Did we test multiple archetype portfolios? `YES`
- Is this deployment-ready? `NO`

## Decision
task_405_verdict,evaluation_status,task401_exact_label_coverage_sufficient,refined_archetype_count,refined_archetype_set_count,best_refined_archetype_set_name,baseline_entry_reduce_failure_rate,best_set_entry_reduce_failure_rate,entry_reduce_failure_reduced_flag,label_used_for_assignment_flag,symbol_session_inference_used_flag,leakage_audit_pass_flag,deployment_claim_flag,strategy_acceptance_status,next_priority
COMPLETE_PASS,REFINED_ARCHETYPE_PORTFOLIO_REBUILD_DIAGNOSTIC,YES,71,6,entry_failure_suppressed_set,0.3480064112097027,0.30069476609541457,1,0,0,1,0,NOT_DEPLOYMENT_READY,task406_task401_labeled_refined_archetype_validation

## Set Quality
refined_archetype_set_name,lifecycle_count,add_scale_success_rate,false_positive_rate,entry_reduce_failure_rate,avg_net_return_from_entry,compounded_net_pnl,validation_count,validation_add_scale_success_rate,validation_entry_reduce_failure_rate,recent_oos_count,recent_oos_add_scale_success_rate,recent_oos_entry_reduce_failure_rate
add_scale_retention_set,18770,0.25716568993074057,0.7428343100692595,0.3551411827384124,-0.003120738544445641,-1.0,3917,0.23257595098289507,0.35460811845800355,3736,0.2979122055674518,0.3573340471092077
balanced_capacity_set,42934,0.21763637210602318,0.7823636278939768,0.35799133553826806,-0.003046787030499752,-1.0,8535,0.19941417691857058,0.35067369654364383,8908,0.24124382577458464,0.35945217781769195
entry_failure_suppressed_set,10795,0.10773506252894859,0.8922649374710514,0.30069476609541457,-0.003013207205642821,-0.9999999999999986,2310,0.1025974025974026,0.30952380952380953,1641,0.1590493601462523,0.28153564899451555
low_concentration_set,41526,0.2148774261908202,0.7851225738091798,0.352213071328806,-0.0030138758586915047,-1.0,8224,0.19917315175097275,0.3419260700389105,8303,0.2422016138745032,0.35035529326749365
top_10_refined_archetype_set,8865,0.30919345741680765,0.6908065425831923,0.35995487873660464,-0.004073288454654031,-1.0,1748,0.3009153318077803,0.37128146453089245,1931,0.32936302433972037,0.36147074054893835
top_20_refined_archetype_set,21241,0.25366037380537637,0.7463396261946236,0.35422061108234076,-0.0029485821462851467,-1.0,4220,0.23696682464454977,0.345260663507109,4298,0.28617961842717543,0.35435086086551887

## False Positive Audit
refined_archetype_set_name,failure_group,lifecycle_count,avg_net_return_from_entry
add_scale_retention_set,add_only_weak,3953,-0.001816104502148963
add_scale_retention_set,add_scale_success,4827,0.02493941843388248
add_scale_retention_set,entry_reduce_failure,6666,-0.020684382514653214
add_scale_retention_set,post_cost_false_positive,1916,-0.01988614090209997
add_scale_retention_set,post_cost_positive_no_add_scale,1408,0.0029859131026287733
balanced_capacity_set,add_only_weak,9112,9.39709196318045e-06
balanced_capacity_set,add_scale_success,9344,0.024687859827616843
balanced_capacity_set,entry_reduce_failure,15370,-0.01904357293498276
balanced_capacity_set,post_cost_false_positive,4846,-0.016959639580785047
balanced_capacity_set,post_cost_positive_no_add_scale,4262,0.0031220991366665203
entry_failure_suppressed_set,add_only_weak,2065,0.004347740175136793
entry_failure_suppressed_set,add_scale_success,1163,0.023640934031140915
entry_failure_suppressed_set,entry_reduce_failure,3246,-0.01599049363770372
entry_failure_suppressed_set,post_cost_false_positive,2177,-0.009937854135338252
entry_failure_suppressed_set,post_cost_positive_no_add_scale,2144,0.002117439027905335
low_concentration_set,add_only_weak,8717,1.6028756297073067e-05
low_concentration_set,add_scale_success,8923,0.024761552193665905
low_concentration_set,entry_reduce_failure,14626,-0.01903928073901241
low_concentration_set,post_cost_false_positive,4910,-0.016470715858831336
low_concentration_set,post_cost_positive_no_add_scale,4350,0.0030111432540026427
top_10_refined_archetype_set,add_only_weak,1891,-0.005143302770110567
top_10_refined_archetype_set,add_scale_success,2741,0.02558546187011098
top_10_refined_archetype_set,entry_reduce_failure,3191,-0.023859027518053355
top_10_refined_archetype_set,post_cost_false_positive,778,-0.026974536831621553
top_10_refined_archetype_set,post_cost_positive_no_add_scale,264,0.0022987835867678504
top_20_refined_archetype_set,add_only_weak,4466,-0.0014410922364917376
top_20_refined_archetype_set,add_scale_success,5388,0.02514329988511312
top_20_refined_archetype_set,entry_reduce_failure,7524,-0.020476842386248185
top_20_refined_archetype_set,post_cost_false_positive,2186,-0.019516366827182385
top_20_refined_archetype_set,post_cost_positive_no_add_scale,1677,0.003019394619136447