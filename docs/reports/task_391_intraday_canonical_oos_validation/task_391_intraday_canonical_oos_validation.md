# Task 391 - Intraday Canonical OOS & Long-History Validation

## Decision
task_391_verdict,validation_status,canonical_lifecycle_count,train_count,validation_count,recent_oos_count,add_scale_recent_oos_pass_flag,reduce_recent_oos_pass_flag,sample_ready_flag,reconstruction_used_flag,symbol_session_inference_used_flag,threshold_relaxation_flag,deployment_claim_flag,next_priority
COMPLETE_PASS,OOS_DIAGNOSTIC_PASS,13095,7857,2619,2619,1,1,1,0,0,0,0,extend_history_and_add_macro_regime_overlay

## Robustness Summary
check_name,anchored_split,sample_count,metric_value,pass_flag
add_scale_vs_entry_only,recent_oos,738,0.04902507421576678,1
add_scale_vs_entry_only,train,1781,0.040067300391566224,1
add_scale_vs_entry_only,validation,629,0.043293613463592305,1
reduce_weakening,recent_oos,0,0.005700230034626247,1
reduce_weakening,train,0,0.012134585651958466,1
reduce_weakening,validation,0,0.010030613474614085,1
top_theme_set,recent_oos,0,"ai_semiconductors,cloud_ai_platforms,aerospace_defense_space",1
top_theme_set,train,0,"aerospace_defense_space,ai_semiconductors,ev_autonomy_mobility",1
top_theme_set,validation,0,"aerospace_defense_space,industrial_automation_robotics,biotech_glp1_healthcare",1

## Split Reinforcement Quality
anchored_split,reinforcement_group,lifecycle_count,avg_return_from_entry,median_return_from_entry,positive_rate,add_rate,scale_rate,reduce_rate,avg_bars_held
recent_oos,add_scale,738,0.0319468045475722,0.026774141918193002,0.9254742547425474,1.0,1.0,0.6476964769647696,22.24390243902439
recent_oos,add_only,530,0.0016954497488001637,0.00487703446054975,0.6226415094339622,1.0,0.0,0.5943396226415094,20.72641509433962
recent_oos,entry_only_or_reduce,1351,-0.01707826966819458,-0.0165680473372781,0.14137675795706883,0.0,0.0,0.691339748334567,17.74241302738712
train,add_scale,1781,0.028346635624603787,0.0240089335566722,0.9253228523301515,1.0,1.0,0.4974733295901179,22.341942728804042
train,add_only,1791,0.004774079314323782,0.0076497587383783,0.7336683417085427,1.0,0.0,0.46119486320491343,22.42434394193188
train,entry_only_or_reduce,4285,-0.011720664766962438,-0.0086935522820574,0.2308051341890315,0.0,0.0,0.598833138856476,20.08728121353559
validation,add_scale,629,0.02852701451383821,0.023780232436394,0.8744038155802861,1.0,1.0,0.5834658187599364,21.406995230524643
validation,add_only,582,0.0012002228116800937,0.00535491825023875,0.6254295532646048,1.0,0.0,0.5085910652920962,21.058419243986254
validation,entry_only_or_reduce,1408,-0.014766598949754095,-0.013027936815976499,0.16477272727272727,0.0,0.0,0.6271306818181818,18.52840909090909