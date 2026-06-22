# Task 402 - Multi-Factor Continuation State Discovery

## Required Answers
- Did Task 402 use factor interaction states instead of reject stack only? `YES`
- Did Task 402 use labels for archetype assignment? `NO`
- Did Task 402 use reconstruction or symbol/session matching? `NO`
- Did Task 402 make a deployment claim? `NO`

## Decision
task_402_verdict,evaluation_status,lifecycle_count,archetype_count,stable_positive_oos_archetype_count,best_archetype_candidate,best_archetype_validation_count,best_archetype_recent_oos_count,label_used_for_assignment_flag,symbol_session_inference_used_flag,reconstruction_used_flag,leakage_audit_pass_flag,deployment_claim_flag,strategy_acceptance_status,next_priority
COMPLETE_PASS,MULTIFACTOR_STATE_ARCHETYPE_DISCOVERY_DIAGNOSTIC,20749,38,0,broad_risk_on x theme_leader x healthy_momentum_window x controlled_vol x neutral_tradability,30,,0,0,0,1,0,ARCHETYPE_DISCOVERY_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT,task403_simulate_selected_archetypes_as_forward_live_policy

## Top Archetype Quality
continuation_archetype_id,lifecycle_count,add_scale_success_count,add_scale_success_rate,false_positive_rate,avg_net_return_from_entry,avg_return_from_entry
broad_risk_on x theme_leader x healthy_momentum_window x controlled_vol x neutral_tradability,30,14,0.4666666666666667,0.5333333333333333,0.004992399902978357,0.009100732638219311
broad_risk_on x theme_leader x early_unconfirmed_breakout x high_vol_stress x friction_heavy,35,16,0.45714285714285713,0.5428571428571428,0.006786149406574882,0.013358469815114049
broad_risk_on x theme_leader x early_unconfirmed_breakout x healthy_expansion_vol x friction_heavy,183,58,0.31351351351351353,0.6864864864864865,-0.00012187915542042088,0.005040379533952563
broad_risk_on x theme_leader x healthy_momentum_window x high_vol_stress x friction_heavy,1018,297,0.2883495145631068,0.7116504854368932,-0.0010685201293040149,0.005433876705879788
broad_risk_on x theme_leader x early_unconfirmed_breakout x healthy_expansion_vol x neutral_tradability,156,44,0.28205128205128205,0.717948717948718,-0.0036395871641708498,0.0010193437218231226
broad_risk_on x theme_positive_not_leader x early_unconfirmed_breakout x high_vol_stress x liquid_clean,206,54,0.2523364485981308,0.7476635514018691,-0.008340927828368925,-0.0014414136310339327
broad_risk_on x theme_leader x early_unconfirmed_breakout x controlled_vol x friction_heavy,1428,354,0.24651810584958217,0.7534818941504178,-0.0028622937465460976,0.0008579646353305432
broad_risk_on x theme_positive_not_leader x healthy_momentum_window x controlled_vol x liquid_clean,83,19,0.2261904761904762,0.7738095238095238,-0.002905552703488885,0.0009102173536348359
broad_risk_on x theme_leader x early_unconfirmed_breakout x high_vol_stress x liquid_clean,170,38,0.2222222222222222,0.7777777777777778,-0.006321942796639286,0.000710987508797235
broad_risk_on x theme_leader x early_unconfirmed_breakout x controlled_vol x neutral_tradability,692,147,0.21212121212121213,0.7878787878787878,-0.004842079548493567,-0.001456009863076686
broad_risk_on x theme_leader x early_unconfirmed_breakout x controlled_vol x liquid_clean,1883,385,0.2038115404976178,0.7961884595023823,-0.006052622139022699,-0.002754267856117947
broad_risk_on x weak_theme x late_or_mixed_entry x controlled_vol x liquid_clean,15,3,0.2,0.8,-0.0019167689133919067,0.0019092157705463
broad_risk_on x theme_leader x late_or_mixed_entry x high_vol_stress x friction_heavy,1271,254,0.19781931464174454,0.8021806853582555,-0.007375480094837631,0.00018012985688527317
broad_risk_on x theme_leader x healthy_momentum_window x healthy_expansion_vol x friction_heavy,663,129,0.19311377245508982,0.8068862275449101,-0.004465107522894061,0.0007972797912592358
broad_risk_on x theme_positive_not_leader x early_unconfirmed_breakout x controlled_vol x liquid_clean,2313,442,0.18697123519458544,0.8130287648054145,-0.005493455489159665,-0.0021649518321729872
broad_risk_on x theme_leader x healthy_momentum_window x controlled_vol x friction_heavy,76,14,0.18421052631578946,0.8157894736842105,-0.006806076790863292,-0.0026561526996944154
broad_risk_on x theme_leader x healthy_momentum_window x controlled_vol x liquid_clean,55,10,0.18181818181818182,0.8181818181818182,-0.012864199534300746,-0.009107966370162666
broad_risk_on x theme_leader x healthy_momentum_window x high_vol_stress x liquid_clean,1238,223,0.17868589743589744,0.8213141025641025,-0.005792079654516404,0.001290434668551164
broad_risk_on x weak_theme x late_or_mixed_entry x high_vol_stress x liquid_clean,737,132,0.17765814266487215,0.8223418573351279,-0.0036764128173898554,0.0032065354084212273
broad_risk_on x theme_leader x late_or_mixed_entry x healthy_expansion_vol x friction_heavy,17,3,0.17647058823529413,0.8235294117647058,-0.009548050827523566,-0.0042035034665054115

## OOS Stability
continuation_archetype_id,validation_count,recent_oos_count,validation_add_scale_success_rate,recent_oos_add_scale_success_rate,validation_avg_net_return,recent_oos_avg_net_return,stability_status
broad_risk_on x theme_leader x healthy_momentum_window x high_vol_stress x friction_heavy,162,316,0.3395061728395062,0.2246153846153846,0.004554074430046936,-0.004567789796148712,diagnostic_mixed
broad_risk_on x theme_leader x early_unconfirmed_breakout x controlled_vol x friction_heavy,250,307,0.25396825396825395,0.2077922077922078,-0.0042552212309670025,-0.004574234912751191,diagnostic_mixed
broad_risk_on x theme_leader x early_unconfirmed_breakout x controlled_vol x neutral_tradability,162,127,0.24074074074074073,0.2992125984251969,-0.003409767104106032,-0.0008705192476017906,diagnostic_mixed
broad_risk_on x weak_theme x late_or_mixed_entry x high_vol_stress x liquid_clean,109,185,0.23853211009174313,0.2712765957446808,0.0017966112640289932,0.0004659445673522804,diagnostic_mixed
broad_risk_on x theme_leader x healthy_momentum_window x high_vol_stress x liquid_clean,134,387,0.1925925925925926,0.23214285714285715,0.0007421343617298988,-0.002768241507300945,diagnostic_mixed
broad_risk_on x theme_leader x healthy_momentum_window x healthy_expansion_vol x neutral_tradability,196,67,0.18090452261306533,0.16176470588235295,-0.0047149463781246785,-0.004512527160450859,diagnostic_mixed
broad_risk_on x theme_leader x early_unconfirmed_breakout x healthy_expansion_vol x liquid_clean,77,67,0.1794871794871795,0.10294117647058823,-0.0084502555333006,-0.014804714568767866,diagnostic_mixed
broad_risk_on x theme_leader x late_or_mixed_entry x high_vol_stress x friction_heavy,243,231,0.1762295081967213,0.16738197424892703,-0.007691699059267569,-0.009896131192378227,diagnostic_mixed
broad_risk_on x theme_leader x healthy_momentum_window x healthy_expansion_vol x friction_heavy,131,70,0.17557251908396945,0.22857142857142856,-0.004981480210009045,-0.006309814073342904,diagnostic_mixed
broad_risk_on x theme_positive_not_leader x early_unconfirmed_breakout x controlled_vol x liquid_clean,483,728,0.1696969696969697,0.2193808882907133,-0.004583401365994907,-0.004751267620535521,diagnostic_mixed
broad_risk_on x theme_positive_not_leader x late_or_mixed_entry x high_vol_stress x liquid_clean,160,259,0.16875,0.21348314606741572,-0.0045553734038688756,-0.0030929707756972274,diagnostic_mixed
broad_risk_on x theme_leader x early_unconfirmed_breakout x controlled_vol x liquid_clean,378,548,0.158311345646438,0.2331511839708561,-0.006920025674627103,-0.005394503839572636,diagnostic_mixed
broad_risk_on x theme_leader x late_or_mixed_entry x high_vol_stress x liquid_clean,70,136,0.15714285714285714,0.20863309352517986,-0.004507573351192999,-0.008451985274705146,diagnostic_mixed
broad_risk_on x theme_positive_not_leader x healthy_momentum_window x high_vol_stress x liquid_clean,263,569,0.15613382899628253,0.18057921635434412,-0.0033392392376986246,-0.005234591026661102,diagnostic_mixed
broad_risk_on x weak_theme x early_unconfirmed_breakout x controlled_vol x liquid_clean,89,106,0.14444444444444443,0.2523364485981308,-0.004812792977770074,-0.007766934481816552,diagnostic_mixed
broad_risk_on x theme_leader x healthy_momentum_window x healthy_expansion_vol x liquid_clean,70,109,0.12857142857142856,0.21818181818181817,-0.007077313282869153,-0.0010348179066868438,diagnostic_mixed
broad_risk_on x theme_positive_not_leader x early_unconfirmed_breakout x healthy_expansion_vol x liquid_clean,84,127,0.09302325581395349,0.17692307692307693,-0.007362513198194552,-0.009894964498318677,diagnostic_mixed
broad_risk_on x theme_positive_not_leader x healthy_momentum_window x healthy_expansion_vol x liquid_clean,134,126,0.08088235294117647,0.15625,-0.006149547633829414,-0.0024513902915744906,diagnostic_mixed
broad_risk_on x theme_leader x healthy_momentum_window x high_vol_stress x neutral_tradability,184,147,0.03260869565217391,0.025974025974025976,-0.0071804253824863966,-0.008086718400713663,diagnostic_mixed
broad_risk_on x theme_leader x healthy_momentum_window x controlled_vol x neutral_tradability,1,4,1.0,0.25,0.0561552141204331,-0.004476716431251124,insufficient_oos_sample