# Task 391 - Intraday Canonical OOS & Long-History Validation

## Decision
task_391_verdict,validation_status,canonical_lifecycle_count,train_count,validation_count,recent_oos_count,add_scale_recent_oos_pass_flag,reduce_recent_oos_pass_flag,sample_ready_flag,reconstruction_used_flag,symbol_session_inference_used_flag,threshold_relaxation_flag,deployment_claim_flag,next_priority
COMPLETE_PASS,OOS_DIAGNOSTIC_PASS,103962,62377,20792,20793,1,1,1,0,0,0,0,extend_history_and_add_macro_regime_overlay

## Robustness Summary
check_name,anchored_split,sample_count,metric_value,pass_flag
add_scale_vs_entry_only,recent_oos,4145,0.040103567988043196,1
add_scale_vs_entry_only,train,11427,0.03859232643359452,1
add_scale_vs_entry_only,validation,3534,0.03724517874462982,1
reduce_weakening,recent_oos,0,0.01057724656533271,1
reduce_weakening,train,0,0.010683861102618639,1
reduce_weakening,validation,0,0.011492388522152189,1
top_theme_set,recent_oos,0,"ai_semiconductors,crypto_fintech,industrial_automation_robotics",1
top_theme_set,train,0,"ai_semiconductors,cloud_ai_platforms,crypto_fintech",1
top_theme_set,validation,0,"ai_semiconductors,crypto_fintech,aerospace_defense_space",1

## Split Reinforcement Quality
anchored_split,reinforcement_group,lifecycle_count,avg_return_from_entry,median_return_from_entry,positive_rate,add_rate,scale_rate,reduce_rate,avg_bars_held
recent_oos,add_scale,4145,0.027496460354691405,0.0238506605019814,0.9196366177498253,1.0,1.0,0.5669694852084789,22.310738411367343
recent_oos,add_only,4529,0.002620793886943262,0.0060671861029504,0.6549946294307196,1.0,0.0,0.5336197636949517,21.63845327604726
recent_oos,entry_only_or_reduce,11489,-0.012607107633351792,-0.0096271826333175,0.21941747572815534,0.0,0.0,0.6011819333051921,19.902321654706626
train,add_scale,11427,0.026704717033410923,0.0232598600512583,0.8973297279026534,1.0,1.0,0.5586445834037519,21.813925976001354
train,add_only,13741,0.0030726864052440313,0.0066347566466045,0.6742684723879026,1.0,0.0,0.4907024068486422,21.51336748298365
train,entry_only_or_reduce,35164,-0.011887609400183595,-0.0085059506816814,0.23501047062713545,0.0,0.0,0.5832965942907528,20.065799625261764
validation,add_scale,3534,0.02718616032002707,0.023172596636451603,0.9161660294920808,1.0,1.0,0.5182960131075914,22.226379027853632
validation,add_only,4461,0.0043657132436363,0.0075451932998217,0.7232065687121867,1.0,0.0,0.44511668107173724,22.25086430423509
validation,entry_only_or_reduce,12150,-0.010059018424602746,-0.00681313837135205,0.26275795872660374,0.0,0.0,0.5530315149576068,21.0