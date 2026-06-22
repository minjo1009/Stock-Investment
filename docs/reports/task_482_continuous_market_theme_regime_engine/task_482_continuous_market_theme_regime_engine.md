# Task 482 - Continuous Multi-Horizon Market/Theme Regime Engine

## Quant Expert Report
- Builds daily-only market/theme regime scores from regular-session intraday bars aggregated to daily OHLCV.
- D-day score rows use D-1 daily data only via `asof_date` and `score_date` separation.
- Scores are continuous weighted component scores, not -1/0/1 rules.
- Intraday confirmation and symbol continuation are explicitly excluded from regime scoring.

## No-Background Decision-Maker Report
- This creates the missing first layer: market/theme regime before intraday trading decisions.
- It is diagnostic only and does not approve deployment.

## Task Decision
task_482_verdict,evaluation_status,source_symbol_count,source_date_count,market_score_date_count,theme_score_row_count,market_risk_on_state_share,theme_leadership_state_share,task480_regime_join_rate,whipsaw_short_dwell_count,d_minus_1_daily_only_flag,continuous_weighted_score_flag,intraday_confirmation_used_for_regime_flag,symbol_continuation_used_for_regime_flag,deployment_claim_flag,strategy_acceptance_status
COMPLETE_PASS,CONTINUOUS_DAILY_ONLY_MARKET_THEME_REGIME_ENGINE_COMPLETE,159,590,589,5910,0.266553480475382,0.22927241962774958,0.9996316758747698,156,1,1,0,0,0,REGIME_ENGINE_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY

## Join Audit
snapshot_lifecycle_count,joined_lifecycle_count,join_rate,join_key,symbol_date_price_time_fallback_used_flag,intraday_state_used_for_regime_flag,symbol_continuation_used_for_regime_flag
32580,32568,0.9996316758747698,score_date_plus_theme_id_exact,0,0,0

## Regime Quality Sample
market_regime_state,lifecycle_count,avg_net_return_pct,win_rate,add_scale_success_rate,entry_reduce_failure_rate,grouping,theme_regime_state,market_theme_combo,split_name
mixed_transition,8226,-0.35729080982820327,0.38840262582056895,0.24203744225626064,0.387551665451009,market_regime_state,,,
risk_off_emerging,2248,0.06060791776618607,0.45907473309608543,0.2624555160142349,0.3389679715302491,market_regime_state,,,
risk_off_persistent,8935,-0.24034926181412195,0.42451035254616676,0.26838276440962505,0.38019026301063236,market_regime_state,,,
risk_on_emerging,3137,-0.19582548467674782,0.3952821166719796,0.24609499521836148,0.3669110615237488,market_regime_state,,,
risk_on_persistent,5436,-0.12647950030076666,0.4155629139072848,0.261037527593819,0.35209713024282563,market_regime_state,,,
volatility_stress,4586,-0.3719543627445706,0.4014391626689926,0.2980811164413432,0.3754906236371566,market_regime_state,,,
,2101,-0.18698747462081763,0.4183722037125179,0.2370299857210852,0.3755354593050928,theme_regime_state,emerging_theme_rotation,,
,17196,-0.2960696694976449,0.40806001395673414,0.2655268667131891,0.3784601070016283,theme_regime_state,fading_theme,,
,2539,-0.30838401888621775,0.3954312721543915,0.23001181567546278,0.35959038991729025,theme_regime_state,mixed_theme,,
,2542,-0.21050405611049988,0.42643587726199844,0.2907159716758458,0.37057435090479934,theme_regime_state,narrow_leader_only,,
,5648,-0.16840333224189946,0.4056303116147309,0.28505665722379603,0.3813739376770538,theme_regime_state,persistent_theme_leadership,,
,2542,-0.08051652143313673,0.4268292682926829,0.21243115656963021,0.32572777340676634,theme_regime_state,weak_theme,,
,635,-0.3868953039248462,0.3826771653543307,0.215748031496063,0.3984251968503937,market_theme_combo,,mixed_transition x emerging_theme_rotation,
,4071,-0.3617115515589322,0.39326946696143456,0.2328666175386883,0.38663718987963647,market_theme_combo,,mixed_transition x fading_theme,
,830,-0.5546775443484715,0.3759036144578313,0.21325301204819277,0.37710843373493974,market_theme_combo,,mixed_transition x mixed_theme,
,354,-0.2957087812264086,0.3954802259887006,0.2627118644067797,0.3587570621468927,market_theme_combo,,mixed_transition x narrow_leader_only,
,1801,-0.2836202800981929,0.38478622987229316,0.2848417545807885,0.3947806774014436,market_theme_combo,,mixed_transition x persistent_theme_leadership,
,535,-0.2710365653044563,0.3850467289719626,0.22990654205607478,0.3925233644859813,market_theme_combo,,mixed_transition x weak_theme,
,238,-0.11373538174886727,0.48739495798319327,0.20588235294117646,0.3445378151260504,market_theme_combo,,risk_off_emerging x emerging_theme_rotation,
,1201,0.1067174023899068,0.4462947543713572,0.2839300582847627,0.3488759367194005,market_theme_combo,,risk_off_emerging x fading_theme,
,161,0.11173701556888421,0.45962732919254656,0.20496894409937888,0.32298136645962733,market_theme_combo,,risk_off_emerging x mixed_theme,
,86,-0.7057511324402701,0.3372093023255814,0.18604651162790697,0.5116279069767442,market_theme_combo,,risk_off_emerging x narrow_leader_only,
,437,0.06417475134147123,0.47368421052631576,0.2723112128146453,0.32723112128146453,market_theme_combo,,risk_off_emerging x persistent_theme_leadership,
,125,0.3984687301711094,0.56,0.256,0.176,market_theme_combo,,risk_off_emerging x weak_theme,
,306,-0.23349758715197258,0.434640522875817,0.21895424836601307,0.3562091503267974,market_theme_combo,,risk_off_persistent x emerging_theme_rotation,
,5784,-0.30295747471342793,0.4170124481327801,0.2672890733056708,0.38087828492392806,market_theme_combo,,risk_off_persistent x fading_theme,
,332,-0.3822252299308603,0.39457831325301207,0.28012048192771083,0.41566265060240964,market_theme_combo,,risk_off_persistent x mixed_theme,
,1228,-0.17156572114787758,0.43322475570032576,0.2890879478827362,0.39006514657980457,market_theme_combo,,risk_off_persistent x narrow_leader_only,
,904,-0.09676918301092352,0.4225663716814159,0.26991150442477874,0.38716814159292035,market_theme_combo,,risk_off_persistent x persistent_theme_leadership,
,381,0.265869985433872,0.5328083989501312,0.2440944881889764,0.30971128608923887,market_theme_combo,,risk_off_persistent x weak_theme,
,304,-0.06746517218689319,0.41776315789473684,0.2565789473684211,0.3980263157894737,market_theme_combo,,risk_on_emerging x emerging_theme_rotation,
,1239,-0.3062671516374487,0.36238902340597257,0.21630347054075869,0.3922518159806295,market_theme_combo,,risk_on_emerging x fading_theme,
,482,-0.17103323277618493,0.4211618257261411,0.24481327800829875,0.32987551867219916,market_theme_combo,,risk_on_emerging x mixed_theme,
,5,-2.328064090475044,0.0,0.4,0.4,market_theme_combo,,risk_on_emerging x narrow_leader_only,
,780,-0.21028710936222234,0.41410256410256413,0.2935897435897436,0.37435897435897436,market_theme_combo,,risk_on_emerging x persistent_theme_leadership,
,327,0.13385979127121234,0.42201834862385323,0.23547400611620795,0.2782874617737003,market_theme_combo,,risk_on_emerging x weak_theme,
,539,0.06209084455654268,0.44712430426716143,0.287569573283859,0.35064935064935066,market_theme_combo,,risk_on_persistent x emerging_theme_rotation,
,1841,-0.25460252314271703,0.41499185225420965,0.2585551330798479,0.3590439978272678,market_theme_combo,,risk_on_persistent x fading_theme,
,586,-0.0240084268395056,0.42150170648464164,0.24744027303754265,0.3122866894197952,market_theme_combo,,risk_on_persistent x mixed_theme,
,52,-0.00170612796440386,0.4423076923076923,0.34615384615384615,0.36538461538461536,market_theme_combo,,risk_on_persistent x narrow_leader_only,