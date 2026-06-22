# Task643 Entry Risk Tier Turnover Backtest

## Decision Summary

- Verdict: `FAIL_NO_FULL_GATE_ENTRY_RISK_TIER_TURNOVER_CANDIDATE`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Best config: `base_delay1d_open` / `existing_exit` / `equal_max5`
- Best $1000 final: $7639.62
- Best max drawdown: -23.76%
- Task639 baseline: $7639.62, DD -23.76%

## Quant Expert Report

Task643 tests the Task642 solution order: entry quality confirmation, volatility-aware sizing, signal tier sizing, and exit/capital recycling. The Task639 content signal is kept fixed.

### Source Audit

| task_id | task642_queue_rows | task639_source_trade_count | entry_policy_variant_rows | execution_variant_rows | entry_quality_source_available_rate | atr20_available_rate | label_used_in_assignment_flag | presence_field_used_for_assignment_flag | symbol_blacklist_used_flag | theme_blacklist_used_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Task643 | 5 | 1621 | 2706 | 10824 | 1.0 | 1.0 | 0 | 0 | 0 | 0 |

### Top Full-Period Candidates

| split_name | entry_policy | exit_policy | sizing_policy | round_trip_cost_bps | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | avg_net_return_pct | win_rate | entry_reduce_failure_rate | max_drawdown_pct | qqq_final_capital_usd | beats_qqq_flag | label_used_in_assignment_flag | presence_field_used_for_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | base_delay1d_open | existing_exit | equal_max5 | 50 | 1621 | 54 | 7639.620310821461 | 663.9620310821462 | 26.43398519539194 | 0.5740740740740741 | 0.37037037037037035 | -23.755747663170723 | 1606.8278306897957 | 1 | 0 | 0 |
| all | base_delay1d_open | existing_exit | signal_tier | 50 | 1621 | 54 | 6574.8832119824265 | 557.4883211982426 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -22.50944608350044 | 1606.8278306897957 | 1 | 0 | 0 |
| all | vwap_rs_confirm_60m | existing_exit | equal_max5 | 50 | 561 | 50 | 3726.3408476154677 | 272.6340847615468 | 19.005866532794084 | 0.64 | 0.3 | -35.18245689454535 | 1606.8278306897957 | 1 | 0 | 0 |
| all | vwap_rs_confirm_60m | existing_exit | signal_tier | 50 | 561 | 50 | 3640.533504377447 | 264.0533504377447 | 19.005866532794084 | 0.64 | 0.3 | -43.399390479650265 | 1606.8278306897957 | 1 | 0 | 0 |
| all | base_delay1d_open | hold20 | signal_tier | 50 | 1621 | 104 | 3605.60621652398 | 260.56062165239797 | 7.041822783143231 | 0.625 | 0.3076923076923077 | -43.37835942958402 | 1606.8278306897957 | 1 | 0 | 0 |
| all | base_delay1d_open | existing_exit | atr_bucket | 50 | 1621 | 54 | 3556.4952787395678 | 255.64952787395677 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -30.616209132688454 | 1606.8278306897957 | 1 | 0 | 0 |
| all | base_delay1d_open | hold20 | equal_max5 | 50 | 1621 | 104 | 3487.176741398259 | 248.7176741398259 | 7.041822783143231 | 0.6057692307692307 | 0.3076923076923077 | -16.38831818619686 | 1606.8278306897957 | 1 | 0 | 0 |
| all | base_delay1d_open | existing_exit | atr_signal_tier | 50 | 1621 | 54 | 3277.5301666262158 | 227.75301666262155 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -27.414551679460153 | 1606.8278306897957 | 1 | 0 | 0 |
| all | base_delay1d_open | strength_hold20_trail10 | signal_tier | 50 | 1621 | 132 | 2951.276560252683 | 195.1276560252683 | 4.901007820063782 | 0.5075757575757576 | 0.4166666666666667 | -55.58536634322031 | 1606.8278306897957 | 1 | 0 | 0 |
| all | base_delay1d_open | trail10_hold20 | signal_tier | 50 | 1621 | 132 | 2951.276560252683 | 195.1276560252683 | 4.901007820063782 | 0.5075757575757576 | 0.4166666666666667 | -55.58536634322031 | 1606.8278306897957 | 1 | 0 | 0 |
| all | base_delay1d_open | strength_hold20_trail10 | equal_max5 | 50 | 1621 | 132 | 2747.864712524644 | 174.7864712524644 | 4.901007820063782 | 0.5606060606060606 | 0.36363636363636365 | -32.890361615760455 | 1606.8278306897957 | 1 | 0 | 0 |
| all | base_delay1d_open | trail10_hold20 | equal_max5 | 50 | 1621 | 132 | 2747.864712524644 | 174.7864712524644 | 4.901007820063782 | 0.5606060606060606 | 0.36363636363636365 | -32.890361615760455 | 1606.8278306897957 | 1 | 0 | 0 |
| all | vwap_rs_confirm_60m | existing_exit | atr_bucket | 50 | 561 | 50 | 2336.3038220545764 | 133.63038220545764 | 19.005866532794084 | 0.64 | 0.3 | -39.47696751177091 | 1606.8278306897957 | 1 | 0 | 0 |
| all | vwap_rs_confirm_60m | existing_exit | atr_signal_tier | 50 | 561 | 50 | 2321.7321948330377 | 132.17321948330377 | 19.005866532794084 | 0.64 | 0.3 | -34.328993823548934 | 1606.8278306897957 | 1 | 0 | 0 |
| all | base_delay1d_open | hold20 | atr_signal_tier | 50 | 1621 | 104 | 2296.2726739016634 | 129.62726739016634 | 7.041822783143231 | 0.625 | 0.3076923076923077 | -47.60067866756419 | 1606.8278306897957 | 1 | 0 | 0 |
| all | base_delay1d_open | hold20 | atr_bucket | 50 | 1621 | 104 | 2260.8756380566383 | 126.08756380566382 | 7.041822783143231 | 0.625 | 0.3076923076923077 | -48.561866250193034 | 1606.8278306897957 | 1 | 0 | 0 |
| all | base_delay1d_open | trail10_hold20 | atr_signal_tier | 50 | 1621 | 132 | 2194.1526063076617 | 119.41526063076617 | 4.901007820063782 | 0.5075757575757576 | 0.4166666666666667 | -54.6127276316602 | 1606.8278306897957 | 1 | 0 | 0 |
| all | base_delay1d_open | strength_hold20_trail10 | atr_signal_tier | 50 | 1621 | 132 | 2194.1526063076617 | 119.41526063076617 | 4.901007820063782 | 0.5075757575757576 | 0.4166666666666667 | -54.6127276316602 | 1606.8278306897957 | 1 | 0 | 0 |
| all | base_delay1d_open | strength_hold20_trail10 | atr_bucket | 50 | 1621 | 132 | 2048.9330317853783 | 104.89330317853782 | 4.901007820063782 | 0.5075757575757576 | 0.4166666666666667 | -56.60923323442423 | 1606.8278306897957 | 1 | 0 | 0 |
| all | base_delay1d_open | trail10_hold20 | atr_bucket | 50 | 1621 | 132 | 2048.9330317853783 | 104.89330317853782 | 4.901007820063782 | 0.5075757575757576 | 0.4166666666666667 | -56.60923323442423 | 1606.8278306897957 | 1 | 0 | 0 |

### Matching OOS Grid

| split_name | entry_policy | exit_policy | sizing_policy | round_trip_cost_bps | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | avg_net_return_pct | win_rate | entry_reduce_failure_rate | max_drawdown_pct | qqq_final_capital_usd | beats_qqq_flag | label_used_in_assignment_flag | presence_field_used_for_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| recent_oos | vwap_rs_confirm_60m | existing_exit | signal_tier | 50 | 104 | 10 | 1653.315936674679 | 65.3315936674679 | 29.038203004708613 | 0.7 | 0.2 | -27.56886990960933 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_or_volume_confirm_60m | existing_exit | signal_tier | 50 | 62 | 10 | 1614.2241945780793 | 61.42241945780793 | 28.942499772018632 | 0.8 | 0.0 | -30.442133588185015 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_or_volume_confirm_60m | existing_exit | equal_max5 | 50 | 62 | 10 | 1594.781635672568 | 59.47816356725679 | 28.942499772018632 | 0.8 | 0.1 | -0.9099052233734306 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_rs_confirm_60m | existing_exit | equal_max5 | 50 | 104 | 10 | 1590.4170330863167 | 59.041703308631675 | 29.038203004708613 | 0.7 | 0.3 | -1.514990397242455 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | strict_or_vwap_rs_volume_60m | existing_exit | signal_tier | 50 | 58 | 10 | 1565.7261082162831 | 56.572610821628324 | 27.004356143763335 | 0.9 | 0.0 | -32.14904281035294 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | strict_or_vwap_rs_volume_60m | existing_exit | equal_max5 | 50 | 58 | 10 | 1559.328997032508 | 55.9328997032508 | 27.004356143763335 | 0.9 | 0.1 | -0.5449913256884042 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | base_delay1d_open | existing_exit | equal_max5 | 50 | 332 | 10 | 1531.902914313866 | 53.190291431386605 | 25.782652943638873 | 0.6 | 0.2 | -0.811391994497368 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | strict_or_vwap_rs_volume_60m | hold20 | equal_max5 | 50 | 58 | 16 | 1512.6092277075293 | 51.260922770752934 | 14.921994461932265 | 0.8125 | 0.1875 | -2.4520787337377725 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | strict_or_vwap_rs_volume_60m | hold20 | signal_tier | 50 | 58 | 16 | 1502.5406659112339 | 50.25406659112339 | 14.921994461932265 | 0.8125 | 0.1875 | -41.94505863692106 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_or_volume_confirm_60m | hold20 | equal_max5 | 50 | 62 | 16 | 1495.4832932348506 | 49.54832932348508 | 14.343107338241817 | 0.75 | 0.1875 | -2.4520787337377725 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | base_delay1d_open | existing_exit | signal_tier | 50 | 332 | 10 | 1491.7338760769114 | 49.17338760769114 | 25.782652943638873 | 0.5 | 0.1 | -30.85158086845865 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_or_volume_confirm_60m | hold20 | signal_tier | 50 | 62 | 16 | 1465.244087709108 | 46.524408770910796 | 14.343107338241817 | 0.8125 | 0.1875 | -41.88038532618017 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_rs_confirm_60m | hold20 | signal_tier | 50 | 104 | 20 | 1448.6790403704063 | 44.86790403704062 | 10.253818895395547 | 0.55 | 0.4 | -30.973791306362088 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_rs_confirm_60m | hold20 | equal_max5 | 50 | 104 | 20 | 1425.9799699998257 | 42.59799699998257 | 10.253818895395547 | 0.65 | 0.35 | -5.152007729936148 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_or_volume_confirm_60m | existing_exit | atr_signal_tier | 50 | 62 | 10 | 1425.3739388381869 | 42.537393883818694 | 28.942499772018632 | 0.8 | 0.0 | -35.23344837277526 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | base_delay1d_open | existing_exit | atr_signal_tier | 50 | 332 | 10 | 1420.3901122640602 | 42.03901122640603 | 25.782652943638873 | 0.5 | 0.1 | -35.68771169058894 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_rs_confirm_60m | existing_exit | atr_signal_tier | 50 | 104 | 10 | 1408.6870880418498 | 40.86870880418498 | 29.038203004708613 | 0.7 | 0.2 | -33.204679004327986 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | strict_or_vwap_rs_volume_60m | existing_exit | atr_signal_tier | 50 | 58 | 10 | 1405.7451913029736 | 40.57451913029735 | 27.004356143763335 | 0.9 | 0.0 | -40.56256159976409 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | base_delay1d_open | existing_exit | atr_bucket | 50 | 332 | 10 | 1393.5199728623825 | 39.35199728623824 | 25.782652943638873 | 0.5 | 0.1 | -36.729615441368814 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_or_volume_confirm_60m | existing_exit | atr_bucket | 50 | 62 | 10 | 1391.924343981928 | 39.1924343981928 | 28.942499772018632 | 0.8 | 0.0 | -36.45330933931339 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_rs_confirm_60m | existing_exit | atr_bucket | 50 | 104 | 10 | 1377.227775238334 | 37.722777523833415 | 29.038203004708613 | 0.7 | 0.2 | -34.59583788498398 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | strict_or_vwap_rs_volume_60m | existing_exit | atr_bucket | 50 | 58 | 10 | 1371.1220881935126 | 37.11220881935127 | 27.004356143763335 | 0.9 | 0.0 | -41.36006577351314 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | strict_or_vwap_rs_volume_60m | hold20 | atr_signal_tier | 50 | 58 | 16 | 1356.6256440531927 | 35.66256440531927 | 14.921994461932265 | 0.8125 | 0.1875 | -43.32974988499916 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | strict_or_vwap_rs_volume_60m | hold20 | atr_bucket | 50 | 58 | 16 | 1338.847543833898 | 33.884754383389804 | 14.921994461932265 | 0.8125 | 0.1875 | -41.9247407967509 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_or_volume_confirm_60m | hold20 | atr_signal_tier | 50 | 62 | 16 | 1326.4641692043283 | 32.64641692043284 | 14.343107338241817 | 0.8125 | 0.1875 | -43.456758504822545 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_or_volume_confirm_60m | hold20 | atr_bucket | 50 | 62 | 16 | 1319.796167378867 | 31.979616737886694 | 14.343107338241817 | 0.8125 | 0.1875 | -41.86004485189895 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_rs_confirm_60m | hold20 | atr_signal_tier | 50 | 104 | 20 | 1254.1955210023095 | 25.419552100230945 | 10.253818895395547 | 0.55 | 0.4 | -36.591372135643766 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_rs_confirm_60m | hold20 | atr_bucket | 50 | 104 | 20 | 1244.366937301705 | 24.4366937301705 | 10.253818895395547 | 0.55 | 0.4 | -32.11297729325619 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_or_volume_confirm_60m | trail10_hold20 | signal_tier | 50 | 62 | 17 | 1182.964548305952 | 18.296454830595188 | 5.861760337639764 | 0.6470588235294118 | 0.35294117647058826 | -43.997920087718526 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_or_volume_confirm_60m | strength_hold20_trail10 | signal_tier | 50 | 62 | 17 | 1182.964548305952 | 18.296454830595188 | 5.861760337639764 | 0.6470588235294118 | 0.35294117647058826 | -43.997920087718526 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_or_volume_confirm_60m | trail10_hold20 | equal_max5 | 50 | 62 | 17 | 1171.083638474959 | 17.108363847495877 | 5.861760337639764 | 0.7647058823529411 | 0.17647058823529413 | -12.5696124779764 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_or_volume_confirm_60m | strength_hold20_trail10 | equal_max5 | 50 | 62 | 17 | 1171.083638474959 | 17.108363847495877 | 5.861760337639764 | 0.7647058823529411 | 0.17647058823529413 | -12.5696124779764 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | strict_or_vwap_rs_volume_60m | trail10_hold20 | signal_tier | 50 | 58 | 18 | 1163.9833476617675 | 16.39833476617676 | 3.5745154923226767 | 0.6111111111111112 | 0.3888888888888889 | -49.66132319820213 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | strict_or_vwap_rs_volume_60m | strength_hold20_trail10 | signal_tier | 50 | 58 | 18 | 1163.9833476617675 | 16.39833476617676 | 3.5745154923226767 | 0.6111111111111112 | 0.3888888888888889 | -49.66132319820213 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_or_volume_confirm_60m | trail10_hold20 | atr_signal_tier | 50 | 62 | 17 | 1158.873372643793 | 15.887337264379298 | 5.861760337639764 | 0.6470588235294118 | 0.35294117647058826 | -47.3888132734404 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | vwap_or_volume_confirm_60m | strength_hold20_trail10 | atr_signal_tier | 50 | 62 | 17 | 1158.873372643793 | 15.887337264379298 | 5.861760337639764 | 0.6470588235294118 | 0.35294117647058826 | -47.3888132734404 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | base_delay1d_open | hold20 | atr_signal_tier | 50 | 332 | 23 | 1155.4529126417922 | 15.545291264179228 | 2.8083560886871144 | 0.5652173913043478 | 0.391304347826087 | -48.23205317728423 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | base_delay1d_open | hold20 | signal_tier | 50 | 332 | 23 | 1139.1233418552129 | 13.912334185521292 | 2.8083560886871144 | 0.5652173913043478 | 0.391304347826087 | -43.910516650326784 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | base_delay1d_open | trail10_hold20 | atr_signal_tier | 50 | 332 | 25 | 1138.0750820375981 | 13.807508203759822 | 2.4249134456780723 | 0.48 | 0.52 | -46.51149454968255 | 1124.192829329964 | 1 | 0 | 0 |
| recent_oos | base_delay1d_open | strength_hold20_trail10 | atr_signal_tier | 50 | 332 | 25 | 1138.0750820375981 | 13.807508203759822 | 2.4249134456780723 | 0.48 | 0.52 | -46.51149454968255 | 1124.192829329964 | 1 | 0 | 0 |

### Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| source_features_available | 1 | atr=100.00%; entry_variants=2706 | ATR risk and entry quality variant data must exist |
| best_candidate_beats_task639_return | 0 | best=$7639.62; task639=$7639.62 | full-period final capital above Task639 |
| best_candidate_reduces_task639_drawdown | 0 | best_dd=-23.76%; task639_dd=-23.76% | max drawdown less severe than Task639 |
| same_config_validation_and_recent_beat_qqq | 1 | validation=$1069.23/QQQ $1049.91; recent=$1531.90/QQQ $1124.19 | same config must beat QQQ in validation and recent OOS |
| no_blacklist_or_label_shortcut | 1 | symbol_blacklist=0; theme_blacklist=0; label_assignment=0 | no blacklists or after-the-fact labels |
| trading_promotion | 0 | research backtest only | requires live-readable rule lock, latency audit, paper-shadow replay, and source readiness |

## No-Background Decision-Maker Report

- We tested the planned fixes without using symbol blacklists or loss labels.
- A candidate must beat Task639 return, reduce drawdown, and also beat QQQ in validation and recent OOS with the same config.
- Even if a candidate passes research gates, real trading remains forbidden until live source and paper-shadow gates pass.

## Artifact Manifest

- `task_643_task639_risk_feature_panel.csv`
- `task_643_entry_quality_panel.csv`
- `task_643_execution_variant_panel.csv`
- `task_643_account_grid.csv`
- `task_643_oos_grid.csv`
- `task_643_source_audit.csv`
- `task_643_pass_fail_matrix.csv`
- `task_643_decision.csv`
- `task_643_gpt_review_packet.txt`
- `task_643_gpt_review_response.md`
- `artifact_manifest.csv`
