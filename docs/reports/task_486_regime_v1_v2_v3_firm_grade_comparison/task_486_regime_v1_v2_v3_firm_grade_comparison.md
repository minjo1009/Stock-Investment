# Task 486 - Regime v1/v2/v3 Firm-Grade Comparison

## Quant Expert Report

### Core Judgment
v1 was too reactive, v2 was too smoothed, and v3 reframed regime as a continuation-payoff conditioner with benchmark ETF data included. The benchmark data gap is now resolved, but v3 still does not prove deployment-grade regime alpha. Market/theme regime alone remains insufficient; it must condition intraday confirmation and symbol-level continuation structure.

### Version Summary
```csv
version,description,risk_or_positive_state_share,theme_positive_state_share,whipsaw_short_dwell_count,eligible_combo_count,positive_combo_count,best_combo_avg_net_return_pct,missing_benchmark_count,deployment_ready_flag
v1_task482_market_health,continuous daily market/theme health regime,0.266553480475382,0.2292724196277495,156,,,,,0
v2_task483_firm_smoothing,smoothed/hysteresis firm-grade market health regime,0.0831918505942275,0.0857868020304568,2,,,,,0
v3_task484_benchmark_payoff,benchmark-enhanced continuation payoff regime,,,,15,2,0.1715239312284731,0,0
```

### Top Market/Theme Combos, Min 300 Lifecycles
```csv
version,state_or_combo,lifecycle_count,avg_net_return_pct,win_rate,add_scale_success_rate,entry_reduce_failure_rate
v1_task482,risk_off_persistent x weak_theme,381,0.265869985433872,0.5328083989501312,0.2440944881889764,0.3097112860892388
v1_task482,risk_on_emerging x weak_theme,327,0.1338597912712123,0.4220183486238532,0.2354740061162079,0.2782874617737003
v1_task482,risk_off_emerging x fading_theme,1201,0.1067174023899068,0.4462947543713572,0.2839300582847627,0.3488759367194005
v1_task482,risk_off_emerging x persistent_theme_leadership,437,0.0641747513414712,0.4736842105263157,0.2723112128146453,0.3272311212814645
v1_task482,risk_on_persistent x emerging_theme_rotation,539,0.0620908445565426,0.4471243042671614,0.287569573283859,0.3506493506493506
v1_task482,risk_on_persistent x persistent_theme_leadership,1381,-0.0165824135521994,0.4098479362780594,0.3120926864590876,0.3823316437364228
v1_task482,risk_on_persistent x mixed_theme,586,-0.0240084268395056,0.4215017064846416,0.2474402730375426,0.3122866894197952
v1_task482,risk_on_emerging x emerging_theme_rotation,304,-0.0674651721868931,0.4177631578947368,0.2565789473684211,0.3980263157894737
v2_task483,market_stress x theme_fading,1054,0.0409479726902728,0.4857685009487666,0.3064516129032258,0.3301707779886148
v2_task483,risk_off_confirmed x theme_stress_fading,1710,-0.0816964631894491,0.4473684210526316,0.3263157894736842,0.375438596491228
v2_task483,risk_off_confirmed x theme_fading,2286,-0.085004102538491,0.4321959755030621,0.2493438320209973,0.3425196850393701
v2_task483,neutral_mixed x theme_neutral_mixed,3599,-0.1335306862395731,0.4117810502917477,0.2397888302306196,0.3564879133092525
v2_task483,risk_off_confirmed x narrow_leader_unconfirmed,411,-0.1360760842956085,0.4111922141119221,0.2481751824817518,0.3819951338199513
v2_task483,neutral_mixed x theme_leadership_confirmed,1333,-0.1444624964573694,0.4051012753188297,0.3135783945986496,0.4021005251312828
v2_task483,risk_on_transition x theme_neutral_mixed,391,-0.1599423077043314,0.3734015345268542,0.2148337595907928,0.3043478260869565
v2_task483,risk_on_confirmed x theme_fading,614,-0.1766248360090618,0.3908794788273615,0.2068403908794788,0.3745928338762215
v3_task484_benchmark_payoff,late_crowded_risk_on x theme_fading,424,0.1715239312284731,0.4622641509433962,0.3113207547169811,0.3136792452830189
v3_task484_benchmark_payoff,late_crowded_risk_on x theme_neutral,1229,0.017527391407422,0.4214808787632221,0.2514239218877135,0.3596419853539463
v3_task484_benchmark_payoff,early_risk_on_transition x theme_neutral,2748,-0.0805289169609087,0.4112081513828238,0.2645560407569141,0.358806404657933
v3_task484_benchmark_payoff,mixed_recovery x theme_fading,4599,-0.1469211751141353,0.4163948684496629,0.2752772341813437,0.3596434007392911
v3_task484_benchmark_payoff,distribution_transition x theme_neutral,797,-0.1772638584424836,0.465495608531995,0.274780426599749,0.3638644918444165
v3_task484_benchmark_payoff,mixed_recovery x leader_initiation,500,-0.2170577488459041,0.394,0.334,0.384
v3_task484_benchmark_payoff,mixed_recovery x theme_neutral,10644,-0.2479472838286798,0.4129086809470124,0.2403231867718902,0.3724163848177377
v3_task484_benchmark_payoff,mixed_recovery x leader_to_follower_broadening,770,-0.275268862951161,0.3792207792207792,0.2298701298701298,0.3935064935064935
```

### Worst Market/Theme Combos, Min 300 Lifecycles
```csv
version,state_or_combo,lifecycle_count,avg_net_return_pct,win_rate,add_scale_success_rate,entry_reduce_failure_rate
v1_task482,volatility_stress x persistent_theme_leadership,345,-0.5622685870192171,0.3478260869565217,0.2144927536231884,0.3768115942028985
v1_task482,mixed_transition x mixed_theme,830,-0.5546775443484715,0.3759036144578313,0.2132530120481927,0.3771084337349397
v1_task482,mixed_transition x emerging_theme_rotation,635,-0.3868953039248462,0.3826771653543307,0.215748031496063,0.3984251968503937
v1_task482,risk_off_persistent x mixed_theme,332,-0.3822252299308603,0.394578313253012,0.2801204819277108,0.4156626506024096
v1_task482,volatility_stress x fading_theme,3060,-0.3746273303360651,0.4101307189542483,0.3225490196078431,0.380718954248366
v1_task482,mixed_transition x fading_theme,4071,-0.3617115515589322,0.3932694669614345,0.2328666175386883,0.3866371898796364
v1_task482,risk_on_emerging x fading_theme,1239,-0.3062671516374487,0.3623890234059725,0.2163034705407586,0.3922518159806295
v1_task482,risk_off_persistent x fading_theme,5784,-0.3029574747134279,0.4170124481327801,0.2672890733056708,0.380878284923928
v2_task483,market_stress x theme_neutral_mixed,411,-0.564909465886698,0.3576642335766423,0.2530413625304136,0.437956204379562
v2_task483,risk_off_transition x narrow_leader_unconfirmed,302,-0.4406374424970509,0.4072847682119205,0.2781456953642384,0.4172185430463576
v2_task483,risk_on_confirmed x theme_neutral_mixed,738,-0.4038722728941756,0.3658536585365853,0.2289972899728997,0.3902439024390244
v2_task483,market_stress x narrow_leader_unconfirmed,951,-0.3525735017636625,0.434279705573081,0.2860147213459516,0.3701366982124079
v2_task483,risk_off_transition x theme_stress_fading,2021,-0.3456718149776249,0.3819891142998515,0.2924294903513112,0.41316180108857
v2_task483,risk_off_transition x theme_neutral_mixed,1745,-0.3432306711236121,0.4051575931232091,0.2011461318051575,0.3713467048710602
v2_task483,risk_off_transition x theme_fading,2755,-0.3309349906682646,0.3949183303085299,0.2330308529945553,0.3749546279491833
v2_task483,risk_off_confirmed x theme_neutral_mixed,692,-0.3260717095059109,0.4046242774566474,0.2557803468208092,0.3236994219653179
v3_task484_benchmark_payoff,distribution_transition x theme_fading,757,-0.740176712391075,0.3949801849405548,0.3077939233817701,0.4412153236459709
v3_task484_benchmark_payoff,early_risk_on_transition x leader_to_follower_broadening,637,-0.4531888504011494,0.3626373626373626,0.2339089481946624,0.4034536891679748
v3_task484_benchmark_payoff,confirmed_risk_off x leader_initiation,698,-0.3805917830063816,0.4226361031518624,0.2765042979942693,0.3510028653295129
v3_task484_benchmark_payoff,confirmed_risk_off x theme_fading,3084,-0.3371663120178614,0.4020752269779507,0.3268482490272373,0.38715953307393
v3_task484_benchmark_payoff,early_risk_on_transition x theme_fading,560,-0.3166969213636292,0.4178571428571428,0.2125,0.35
v3_task484_benchmark_payoff,confirmed_risk_off x theme_neutral,3402,-0.3004887354100269,0.4041740152851264,0.2489711934156378,0.3885949441504997
v3_task484_benchmark_payoff,mixed_recovery x theme_rotation_failure,330,-0.2851849238711866,0.403030303030303,0.2757575757575757,0.3666666666666666
v3_task484_benchmark_payoff,mixed_recovery x leader_to_follower_broadening,770,-0.275268862951161,0.3792207792207792,0.2298701298701298,0.3935064935064935
```

### Benchmark Source Audit
```csv
required_symbol,required_for,raw_intraday_available_flag,raw_source_path,status
SPY,firm_grade_market_or_sector_benchmark,1,data\raw\us_intraday\SPY.csv,available_exact
QQQ,firm_grade_market_or_sector_benchmark,1,data\raw\us_intraday\QQQ.csv,available_exact
IWM,firm_grade_market_or_sector_benchmark,1,data\raw\us_intraday\IWM.csv,available_exact
XLK,firm_grade_market_or_sector_benchmark,1,data\raw\us_intraday\XLK.csv,available_exact
SMH,firm_grade_market_or_sector_benchmark,1,data\raw\us_intraday\SMH.csv,available_exact
IGV,firm_grade_market_or_sector_benchmark,1,data\raw\us_intraday\IGV.csv,available_exact
HACK,firm_grade_market_or_sector_benchmark,1,data\raw\us_intraday\HACK.csv,available_exact
IBB,firm_grade_market_or_sector_benchmark,1,data\raw\us_intraday\IBB.csv,available_exact
XLI,firm_grade_market_or_sector_benchmark,1,data\raw\us_intraday\XLI.csv,available_exact
XLE,firm_grade_market_or_sector_benchmark,1,data\raw\us_intraday\XLE.csv,available_exact
XLU,firm_grade_market_or_sector_benchmark,1,data\raw\us_intraday\XLU.csv,available_exact
```

### Firm-Grade Implications
1. v1 caught some payoff pockets but was too noisy for live gating.
2. v2 fixed whipsaw but over-smoothed the opportunity set and weakened payoff selection.
3. v3 correctly uses benchmark ETFs and payoff-oriented states, but the best broad combo is still only around +0.17% average net, with false positives still high.
4. The most important next improvement is conditional interaction: benchmark regime x theme broadening x intraday confirmation x symbol 15m continuation structure.
5. Regime should be a permission/allocation layer, not a standalone entry signal.

## No-Background Decision-Maker Report

?? ??? benchmark ETF ???? ????, ??? ??? regime? ?? ????. ??? ??? ?? ?? regime?? ?? ???? ???? ???. ??/?? ?????? ?? continuation? ??? ??? ???.

?? ???:
- v1? ???? ?? ????.
- v2? ?????? ??? ?? ???.
- v3? ??? ?? ????, ?? ?? ???? ???.

?? ??? ??/?? regime ??? ???, ?? regime ??? ?? ?? 15?? continuation ??? ?? ?? ??? ???? ???.
