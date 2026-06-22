# Task645 Microstructure + Content Source Upgrade

## Decision Summary

- Verdict: `FEATURE_VALIDATION_PARTIAL_COVERAGE_NO_PROMOTION`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Best research config: `base` / `micro_fragile_reduce`
- Best final: $7670.99
- Best DD: -23.37%
- Task639: $7639.62, DD -23.76%

## Quant Expert Report

Task645 adds entry-time historical SIP microstructure and deeper source/content interpretation. The assignment logic does not use outcomes, labels, GPT facts, symbol blacklists, or missing-data-as-negative shortcuts.

### Source Audit

| task_id | base_signal_rows | execution_rows | quote_covered_rows | quote_covered_row_rate | trade_covered_rows | trade_covered_row_rate | quote_source_symbol_count | trade_source_symbol_count | content_linked_rows | content_source_lanes | gpt_design_captured_flag | label_used_in_assignment_flag | gpt_or_plugin_used_as_source_flag | missing_microstructure_used_as_negative_flag | historical_live_ready_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Task645 | 1621 | 10824 | 30 | 0.01850709438618137 | 8 | 0.004935225169648365 | 57 | 20 | 1621 | 3 | 1 | 0 | 0 | 0 | 0 |

### Feature Diagnostics

| split_name | feature_group | micro_continuation_state | row_count | avg_return_pct | median_return_pct | win_rate | entry_reduce_failure_rate | label_used_for_assignment_flag | content_quality_tier_task645 | combined_quality_micro_state |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | combined_quality_micro_state |  | 4 | 26.742620910724508 | 29.191161598650844 | 0.75 | 0.25 | 0 |  | strong_content_clean_micro |
| all | combined_quality_micro_state |  | 971 | 7.150446562255255 | 5.21111934276989 | 0.592173017507724 | 0.33779608650875387 | 0 |  | mixed_or_missing |
| all | combined_quality_micro_state |  | 334 | 5.653047518604756 | -0.45540142938170003 | 0.49101796407185627 | 0.46107784431137727 | 0 |  | risk_reversal_content |
| all | combined_quality_micro_state |  | 307 | 1.424136845538352 | -3.69974534777803 | 0.44625407166123776 | 0.504885993485342 | 0 |  | strong_content_unconfirmed_micro |
| all | combined_quality_micro_state |  | 5 | -0.5629950230736902 | 1.47610339159052 | 0.6 | 0.4 | 0 |  | weak_content_fragile_micro |
| all | content_quality_tier_task645 |  | 899 | 7.271584739051749 | 5.40712478690352 | 0.6017797552836485 | 0.3270300333704116 | 0 | moderate_content_quality |  |
| all | content_quality_tier_task645 |  | 334 | 5.653047518604756 | -0.45540142938170003 | 0.49101796407185627 | 0.46107784431137727 | 0 | risk_or_reversal_candidate |  |
| all | content_quality_tier_task645 |  | 77 | 5.235246187363167 | -1.67801142987156 | 0.4805194805194805 | 0.4675324675324675 | 0 | weak_presence_only_quality |  |
| all | content_quality_tier_task645 |  | 310 | 1.761018719038916 | -3.58828501362341 | 0.45161290322580644 | 0.5032258064516129 | 0 | strong_contract_quality |  |
| all | content_quality_tier_task645 |  | 1 | -1.73530767889181 | -1.73530767889181 | 0.0 | 0.0 | 0 | compound_contract_supply_quality |  |
| all | micro_continuation_state | real_continuation | 6 | 15.299308329683878 | 14.570498519445888 | 0.6666666666666666 | 0.3333333333333333 | 0 |  |  |
| all | micro_continuation_state | mixed_microstructure | 6 | 15.107500085513792 | 8.1708240312155 | 0.8333333333333334 | 0.16666666666666666 | 0 |  |  |
| all | micro_continuation_state | micro_sparse_observation | 9 | 13.848445093977027 | 13.362375131239098 | 0.6666666666666666 | 0.2222222222222222 | 0 |  |  |
| all | micro_continuation_state | micro_missing | 1591 | 5.682538023845083 | 2.6799118667005297 | 0.5417976115650535 | 0.3966059082338152 | 0 |  |  |
| all | micro_continuation_state | fragile_breakout | 9 | 2.7302389996821157 | 1.47610339159052 | 0.5555555555555556 | 0.4444444444444444 | 0 |  |  |
| recent_oos | combined_quality_micro_state |  | 1 | 71.46296690195348 | 71.46296690195348 | 1.0 | 0.0 | 0 |  | strong_content_clean_micro |
| recent_oos | combined_quality_micro_state |  | 77 | 10.931832297318122 | 4.80385673640806 | 0.5844155844155844 | 0.33766233766233766 | 0 |  | strong_content_unconfirmed_micro |
| recent_oos | combined_quality_micro_state |  | 151 | 7.064169566617622 | 1.8214647940131699 | 0.5298013245033113 | 0.40397350993377484 | 0 |  | mixed_or_missing |
| recent_oos | combined_quality_micro_state |  | 101 | 6.009742719749037 | -0.17250082547124 | 0.49504950495049505 | 0.42574257425742573 | 0 |  | risk_reversal_content |
| recent_oos | combined_quality_micro_state |  | 2 | -2.376413493153326 | -2.376413493153326 | 0.5 | 0.5 | 0 |  | weak_content_fragile_micro |
| recent_oos | content_quality_tier_task645 |  | 78 | 11.707872484557038 | 5.287557624796675 | 0.5897435897435898 | 0.3333333333333333 | 0 | strong_contract_quality |  |
| recent_oos | content_quality_tier_task645 |  | 36 | 11.436849983339496 | 4.033947581201275 | 0.5555555555555556 | 0.3888888888888889 | 0 | weak_presence_only_quality |  |
| recent_oos | content_quality_tier_task645 |  | 101 | 6.009742719749037 | -0.17250082547124 | 0.49504950495049505 | 0.42574257425742573 | 0 | risk_or_reversal_candidate |  |
| recent_oos | content_quality_tier_task645 |  | 117 | 5.5573519501942945 | 1.1496941101549 | 0.5213675213675214 | 0.41025641025641024 | 0 | moderate_content_quality |  |
| recent_oos | micro_continuation_state | real_continuation | 2 | 37.53875853549371 | 37.53875853549371 | 1.0 | 0.0 | 0 |  |  |
| recent_oos | micro_continuation_state | micro_sparse_observation | 1 | 30.983700959578808 | 30.983700959578808 | 1.0 | 0.0 | 0 |  |  |
| recent_oos | micro_continuation_state | fragile_breakout | 4 | 13.305508070151683 | 12.725750489073965 | 0.75 | 0.25 | 0 |  |  |
| recent_oos | micro_continuation_state | micro_missing | 324 | 7.4700033396315035 | 1.4208187419263651 | 0.5246913580246914 | 0.4012345679012346 | 0 |  |  |
| recent_oos | micro_continuation_state | mixed_microstructure | 1 | 2.57051371127601 | 2.57051371127601 | 1.0 | 0.0 | 0 |  |  |
| train_design | combined_quality_micro_state |  | 103 | 9.807686532253504 | -0.48389346262863003 | 0.49514563106796117 | 0.4854368932038835 | 0 |  | risk_reversal_content |
| train_design | combined_quality_micro_state |  | 335 | 8.531436471006167 | 7.561949442511071 | 0.608955223880597 | 0.3283582089552239 | 0 |  | mixed_or_missing |
| train_design | combined_quality_micro_state |  | 2 | 1.3258202067503388 | 1.3258202067503388 | 0.5 | 0.5 | 0 |  | strong_content_clean_micro |
| train_design | combined_quality_micro_state |  | 193 | -3.363826009160171 | -9.69579184850631 | 0.3626943005181347 | 0.6062176165803109 | 0 |  | strong_content_unconfirmed_micro |
| train_design | combined_quality_micro_state |  | 1 | -24.68691683575241 | -24.68691683575241 | 0.0 | 1.0 | 0 |  | weak_content_fragile_micro |
| train_design | content_quality_tier_task645 |  | 103 | 9.807686532253504 | -0.48389346262863003 | 0.49514563106796117 | 0.4854368932038835 | 0 | risk_or_reversal_candidate |  |
| train_design | content_quality_tier_task645 |  | 331 | 8.777514967120505 | 7.96959338633553 | 0.6163141993957704 | 0.3202416918429003 | 0 | moderate_content_quality |  |
| train_design | content_quality_tier_task645 |  | 1 | -1.73530767889181 | -1.73530767889181 | 0.0 | 0.0 | 0 | compound_contract_supply_quality |  |
| train_design | content_quality_tier_task645 |  | 194 | -3.3238735653377343 | -9.74034187637102 | 0.36597938144329895 | 0.6082474226804123 | 0 | strong_contract_quality |  |
| train_design | content_quality_tier_task645 |  | 5 | -14.402630633114772 | -13.69144380018319 | 0.0 | 1.0 | 0 | weak_presence_only_quality |  |
| train_design | micro_continuation_state | micro_sparse_observation | 4 | 13.516937290128716 | 11.152220730364009 | 0.5 | 0.5 | 0 |  |  |
| train_design | micro_continuation_state | micro_missing | 622 | 5.167455589447365 | 1.72674314216535 | 0.5176848874598071 | 0.43569131832797425 | 0 |  |  |
| train_design | micro_continuation_state | mixed_microstructure | 2 | 0.07815101636087507 | 0.07815101636087507 | 0.5 | 0.5 | 0 |  |  |
| train_design | micro_continuation_state | real_continuation | 3 | -5.37918114010934 | -18.789183833828698 | 0.3333333333333333 | 0.6666666666666666 | 0 |  |  |
| train_design | micro_continuation_state | fragile_breakout | 3 | -18.424883330052765 | -23.56201688879607 | 0.0 | 1.0 | 0 |  |  |
| validation | combined_quality_micro_state |  | 1 | 32.85587632744386 | 32.85587632744386 | 1.0 | 0.0 | 0 |  | strong_content_clean_micro |
| validation | combined_quality_micro_state |  | 2 | 13.312384353345305 | 13.312384353345305 | 1.0 | 0.0 | 0 |  | weak_content_fragile_micro |
| validation | combined_quality_micro_state |  | 37 | 6.6129012014781425 | 2.71655298712838 | 0.5945945945945946 | 0.32432432432432434 | 0 |  | strong_content_unconfirmed_micro |
| validation | combined_quality_micro_state |  | 485 | 6.223428432172221 | 4.42225296230822 | 0.6 | 0.3237113402061856 | 0 |  | mixed_or_missing |
| validation | combined_quality_micro_state |  | 130 | 2.0841703361325004 | -2.116480907204415 | 0.4846153846153846 | 0.46923076923076923 | 0 |  | risk_reversal_content |
| validation | content_quality_tier_task645 |  | 38 | 7.30350581005619 | 3.061310559162405 | 0.6052631578947368 | 0.3157894736842105 | 0 | strong_contract_quality |  |
| validation | content_quality_tier_task645 |  | 451 | 6.611057756358983 | 4.9167993767965195 | 0.6119733924611973 | 0.31042128603104213 | 0 | moderate_content_quality |  |
| validation | content_quality_tier_task645 |  | 130 | 2.0841703361325004 | -2.116480907204415 | 0.4846153846153846 | 0.46923076923076923 | 0 | risk_or_reversal_candidate |  |
| validation | content_quality_tier_task645 |  | 36 | 1.7611252831198883 | -1.02012637167675 | 0.4722222222222222 | 0.4722222222222222 | 0 | weak_presence_only_quality |  |
| validation | micro_continuation_state | real_continuation | 1 | 32.85587632744386 | 32.85587632744386 | 1.0 | 0.0 | 0 |  |  |
| validation | micro_continuation_state | mixed_microstructure | 3 | 29.306061589695 | 31.778770580220538 | 1.0 | 0.0 | 0 |  |  |
| validation | micro_continuation_state | fragile_breakout | 2 | 13.312384353345305 | 13.312384353345305 | 1.0 | 0.0 | 0 |  |  |
| validation | micro_continuation_state | micro_sparse_observation | 4 | 9.89613893142489 | 10.639459315129379 | 0.75 | 0.0 | 0 |  |  |
| validation | micro_continuation_state | micro_missing | 645 | 5.281363623659936 | 3.7037093102548497 | 0.5736434108527132 | 0.35658914728682173 | 0 |  |  |

### Content x Microstructure Interaction

| split_name | feature_group | content_quality_tier_task645 | micro_continuation_state | row_count | avg_return_pct | median_return_pct | win_rate | entry_reduce_failure_rate | label_used_for_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | content_quality_tier_task645|micro_continuation_state | risk_or_reversal_candidate | micro_sparse_observation | 3 | 33.652921686280315 | 30.983700959578808 | 1.0 | 0.0 | 0 |
| all | content_quality_tier_task645|micro_continuation_state | risk_or_reversal_candidate | fragile_breakout | 2 | 28.987429633456692 | 28.987429633456692 | 1.0 | 0.0 | 0 |
| all | content_quality_tier_task645|micro_continuation_state | strong_contract_quality | real_continuation | 4 | 26.742620910724508 | 29.191161598650844 | 0.75 | 0.25 | 0 |
| all | content_quality_tier_task645|micro_continuation_state | moderate_content_quality | mixed_microstructure | 4 | 24.92470379338435 | 21.779700492336467 | 1.0 | 0.0 | 0 |
| all | content_quality_tier_task645|micro_continuation_state | moderate_content_quality | micro_sparse_observation | 4 | 7.913050953684943 | 10.639459315129379 | 0.75 | 0.25 | 0 |
| all | content_quality_tier_task645|micro_continuation_state | moderate_content_quality | micro_missing | 885 | 7.262607706631006 | 5.36829093141333 | 0.6 | 0.327683615819209 | 0 |
| all | content_quality_tier_task645|micro_continuation_state | risk_or_reversal_candidate | micro_missing | 328 | 5.260883221704878 | -1.297246268797045 | 0.4817073170731707 | 0.4695121951219512 | 0 |
| all | content_quality_tier_task645|micro_continuation_state | weak_presence_only_quality | micro_missing | 77 | 5.235246187363167 | -1.67801142987156 | 0.4805194805194805 | 0.4675324675324675 | 0 |
| all | content_quality_tier_task645|micro_continuation_state | risk_or_reversal_candidate | real_continuation | 1 | 3.61455016903395 | 3.61455016903395 | 1.0 | 0.0 | 0 |
| all | content_quality_tier_task645|micro_continuation_state | strong_contract_quality | micro_missing | 300 | 1.621872767006046 | -3.58828501362341 | 0.4533333333333333 | 0.5033333333333333 | 0 |
| all | content_quality_tier_task645|micro_continuation_state | moderate_content_quality | fragile_breakout | 5 | -0.5629950230736902 | 1.47610339159052 | 0.6 | 0.4 | 0 |
| all | content_quality_tier_task645|micro_continuation_state | compound_contract_supply_quality | micro_missing | 1 | -1.73530767889181 | -1.73530767889181 | 0.0 | 0.0 | 0 |
| all | content_quality_tier_task645|micro_continuation_state | strong_contract_quality | micro_sparse_observation | 2 | -3.987481513893745 | -3.987481513893745 | 0.0 | 0.5 | 0 |
| all | content_quality_tier_task645|micro_continuation_state | strong_contract_quality | mixed_microstructure | 2 | -4.52690733022732 | -4.52690733022732 | 0.5 | 0.5 | 0 |
| all | content_quality_tier_task645|micro_continuation_state | strong_contract_quality | fragile_breakout | 2 | -15.293866577202945 | -15.293866577202945 | 0.0 | 1.0 | 0 |
| all | content_quality_tier_task645|micro_continuation_state | moderate_content_quality | real_continuation | 1 | -18.789183833828698 | -18.789183833828698 | 0.0 | 1.0 | 0 |
| recent_oos | content_quality_tier_task645|micro_continuation_state | strong_contract_quality | real_continuation | 1 | 71.46296690195348 | 71.46296690195348 | 1.0 | 0.0 | 0 |
| recent_oos | content_quality_tier_task645|micro_continuation_state | risk_or_reversal_candidate | micro_sparse_observation | 1 | 30.983700959578808 | 30.983700959578808 | 1.0 | 0.0 | 0 |
| recent_oos | content_quality_tier_task645|micro_continuation_state | risk_or_reversal_candidate | fragile_breakout | 2 | 28.987429633456692 | 28.987429633456692 | 1.0 | 0.0 | 0 |
| recent_oos | content_quality_tier_task645|micro_continuation_state | weak_presence_only_quality | micro_missing | 36 | 11.436849983339496 | 4.033947581201275 | 0.5555555555555556 | 0.3888888888888889 | 0 |
| recent_oos | content_quality_tier_task645|micro_continuation_state | strong_contract_quality | micro_missing | 76 | 11.041849647134468 | 5.287557624796675 | 0.5789473684210527 | 0.34210526315789475 | 0 |
| recent_oos | content_quality_tier_task645|micro_continuation_state | moderate_content_quality | micro_missing | 115 | 5.695330479643819 | 1.1496941101549 | 0.5217391304347826 | 0.40869565217391307 | 0 |
| recent_oos | content_quality_tier_task645|micro_continuation_state | risk_or_reversal_candidate | micro_missing | 97 | 5.303205198960068 | -0.42690939613477 | 0.4742268041237113 | 0.44329896907216493 | 0 |
| recent_oos | content_quality_tier_task645|micro_continuation_state | risk_or_reversal_candidate | real_continuation | 1 | 3.61455016903395 | 3.61455016903395 | 1.0 | 0.0 | 0 |
| recent_oos | content_quality_tier_task645|micro_continuation_state | strong_contract_quality | mixed_microstructure | 1 | 2.57051371127601 | 2.57051371127601 | 1.0 | 0.0 | 0 |
| recent_oos | content_quality_tier_task645|micro_continuation_state | moderate_content_quality | fragile_breakout | 2 | -2.376413493153326 | -2.376413493153326 | 0.5 | 0.5 | 0 |
| validation | content_quality_tier_task645|micro_continuation_state | strong_contract_quality | real_continuation | 1 | 32.85587632744386 | 32.85587632744386 | 1.0 | 0.0 | 0 |
| validation | content_quality_tier_task645|micro_continuation_state | moderate_content_quality | mixed_microstructure | 3 | 29.306061589695 | 31.778770580220538 | 1.0 | 0.0 | 0 |
| validation | content_quality_tier_task645|micro_continuation_state | moderate_content_quality | micro_sparse_observation | 3 | 13.764177214262164 | 13.362375131239098 | 1.0 | 0.0 | 0 |
| validation | content_quality_tier_task645|micro_continuation_state | moderate_content_quality | fragile_breakout | 2 | 13.312384353345305 | 13.312384353345305 | 1.0 | 0.0 | 0 |
| validation | content_quality_tier_task645|micro_continuation_state | strong_contract_quality | micro_missing | 36 | 6.8440366769938406 | 3.061310559162405 | 0.6111111111111112 | 0.3333333333333333 | 0 |
| validation | content_quality_tier_task645|micro_continuation_state | moderate_content_quality | micro_missing | 443 | 6.378671699772774 | 4.42225296230822 | 0.6049661399548533 | 0.3160270880361174 | 0 |
| validation | content_quality_tier_task645|micro_continuation_state | risk_or_reversal_candidate | micro_missing | 130 | 2.0841703361325004 | -2.116480907204415 | 0.4846153846153846 | 0.46923076923076923 | 0 |
| validation | content_quality_tier_task645|micro_continuation_state | weak_presence_only_quality | micro_missing | 36 | 1.7611252831198883 | -1.02012637167675 | 0.4722222222222222 | 0.4722222222222222 | 0 |
| validation | content_quality_tier_task645|micro_continuation_state | strong_contract_quality | micro_sparse_observation | 1 | -1.7079759170869302 | -1.7079759170869302 | 0.0 | 0.0 | 0 |

### Account Grid

| split_name | entry_action | sizing_policy | round_trip_cost_bps | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | avg_net_return_pct | win_rate | entry_reduce_failure_rate | max_drawdown_pct | qqq_final_capital_usd | beats_qqq_flag | label_used_in_assignment_flag | presence_only_signal_used_flag | missing_microstructure_used_as_negative_flag | symbol_blacklist_used_flag | theme_blacklist_used_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | base | micro_fragile_reduce | 50 | 1621 | 54 | 7670.988361869871 | 667.0988361869871 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -23.36667063415372 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| all | fragile_weak_delay_confirm | micro_fragile_reduce | 50 | 1621 | 54 | 7670.988361869871 | 667.0988361869871 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -23.36667063415372 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| all | fragile_weak_delay_confirm | equal | 50 | 1621 | 54 | 7639.620310821464 | 663.9620310821465 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -23.755747663170702 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| all | base | equal | 50 | 1621 | 54 | 7639.620310821464 | 663.9620310821465 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -23.755747663170702 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| all | fragile_weak_delay_confirm | combined_quality_micro | 50 | 1621 | 54 | 5652.228115965281 | 465.2228115965281 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -21.595495609281024 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| all | base | combined_quality_micro | 50 | 1621 | 54 | 5652.228115965281 | 465.2228115965281 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -21.595495609281024 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| all | base | content_quality_soft | 50 | 1621 | 54 | 5281.441926672834 | 428.1441926672834 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -21.926789918280278 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |
| all | fragile_weak_delay_confirm | content_quality_soft | 50 | 1621 | 54 | 5281.441926672834 | 428.1441926672834 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | -21.926789918280278 | 1606.8278306897957 | 1 | 0 | 0 | 0 | 0 | 0 |

### OOS Grid

| split_name | entry_action | sizing_policy | round_trip_cost_bps | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | avg_net_return_pct | win_rate | entry_reduce_failure_rate | max_drawdown_pct | qqq_final_capital_usd | beats_qqq_flag | label_used_in_assignment_flag | presence_only_signal_used_flag | missing_microstructure_used_as_negative_flag | symbol_blacklist_used_flag | theme_blacklist_used_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| recent_oos | base | content_quality_soft | 50 | 332 | 10 | 1586.8806898437726 | 58.68806898437726 | 25.78265294363888 | 0.5 | 0.1 | -0.8706085134816854 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| recent_oos | fragile_weak_delay_confirm | content_quality_soft | 50 | 332 | 10 | 1586.8806898437726 | 58.68806898437726 | 25.78265294363888 | 0.5 | 0.1 | -0.8706085134816854 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| recent_oos | base | combined_quality_micro | 50 | 332 | 10 | 1559.3511774402173 | 55.93511774402173 | 25.78265294363888 | 0.5 | 0.1 | -0.8413683997520294 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| recent_oos | fragile_weak_delay_confirm | combined_quality_micro | 50 | 332 | 10 | 1559.3511774402173 | 55.93511774402173 | 25.78265294363888 | 0.5 | 0.1 | -0.8413683997520294 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| recent_oos | base | equal | 50 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | 25.78265294363888 | 0.5 | 0.1 | -0.811391994497368 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| recent_oos | base | micro_fragile_reduce | 50 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | 25.78265294363888 | 0.5 | 0.1 | -0.811391994497368 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| recent_oos | fragile_weak_delay_confirm | equal | 50 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | 25.78265294363888 | 0.5 | 0.1 | -0.811391994497368 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| recent_oos | fragile_weak_delay_confirm | micro_fragile_reduce | 50 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | 25.78265294363888 | 0.5 | 0.1 | -0.811391994497368 | 1124.192829329964 | 1 | 0 | 0 | 0 | 0 | 0 |
| validation | base | content_quality_soft | 50 | 655 | 15 | 1085.1527480840869 | 8.51527480840868 | 2.5122605564289224 | 0.5333333333333333 | 0.4 | -6.442056384306383 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |
| validation | fragile_weak_delay_confirm | content_quality_soft | 50 | 655 | 15 | 1085.1527480840869 | 8.51527480840868 | 2.5122605564289224 | 0.5333333333333333 | 0.4 | -6.442056384306383 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |
| validation | base | combined_quality_micro | 50 | 655 | 15 | 1080.496843342796 | 8.049684334279593 | 2.5122605564289224 | 0.5333333333333333 | 0.4 | -6.362545168448119 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |
| validation | fragile_weak_delay_confirm | combined_quality_micro | 50 | 655 | 15 | 1080.496843342796 | 8.049684334279593 | 2.5122605564289224 | 0.5333333333333333 | 0.4 | -6.362545168448119 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |
| validation | base | equal | 50 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | 2.5122605564289224 | 0.5333333333333333 | 0.4 | -7.363321689343804 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |
| validation | base | micro_fragile_reduce | 50 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | 2.5122605564289224 | 0.5333333333333333 | 0.4 | -7.363321689343804 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |
| validation | fragile_weak_delay_confirm | equal | 50 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | 2.5122605564289224 | 0.5333333333333333 | 0.4 | -7.363321689343804 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |
| validation | fragile_weak_delay_confirm | micro_fragile_reduce | 50 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | 2.5122605564289224 | 0.5333333333333333 | 0.4 | -7.363321689343804 | 1049.908329847512 | 1 | 0 | 0 | 0 | 0 | 0 |

### Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| gpt_design_captured | 1 | captured=1 | GPT review packet must be captured as review-only input |
| task639_baseline_reproduced | 1 | task645_base=$7639.62; task639=$7639.62 | Task645 base/equal must reproduce Task639 account result |
| feature_candidate_beats_task639_return | 1 | best=$7670.99; task639=$7639.62 | best feature-linked candidate must exceed Task639 |
| feature_candidate_reduces_task639_drawdown | 1 | best_dd=-23.37%; task639_dd=-23.76% | best feature-linked candidate must reduce drawdown severity |
| same_config_validation_recent_beat_qqq | 1 | validation=$1069.23/QQQ $1049.91; recent=$1531.90/QQQ $1124.19 | same config must beat QQQ in validation and recent OOS |
| microstructure_coverage_sufficient_for_micro_rule | 0 | best_uses_micro=1; quote_rate=0.019; trade_rate=0.005 | microstructure-linked account rule needs at least 20% quote-row and 10% trade-row coverage |
| no_shortcut_or_missing_as_negative | 1 | no labels/blacklists; missing_microstructure_used_as_negative=0 | missing sources must be reported, not treated as bearish |
| trading_promotion | 0 | feature validation only; historical sources are not live-ready | live-source readiness and paper-shadow replay required |

## No-Background Decision-Maker Report

- 이번 작업은 바로 매매 룰을 바꾼 작업이 아닙니다.
- 먼저 돌파가 진짜인지, 뉴스가 얼마나 강한지 더 세부적으로 숫자화했습니다.
- trade microstructure는 아직 커버리지가 낮아서 없는 구간을 나쁘게 처리하지 않았습니다.
- 이 결과가 Task639보다 수익과 낙폭을 동시에 개선하지 못하면 전략 승격은 금지입니다.

## Artifact Manifest

- `task_645_gpt_design_packet.txt`
- `task_645_gpt_design_response.md`
- `task_645_microstructure_content_feature_panel.csv`
- `task_645_feature_diagnostics.csv`
- `task_645_content_microstructure_interaction_panel.csv`
- `task_645_account_grid.csv`
- `task_645_oos_grid.csv`
- `task_645_source_audit.csv`
- `task_645_pass_fail_matrix.csv`
- `task_645_decision.csv`
- `task_645_microstructure_coverage_audit.csv`
- `task_645_content_source_audit.csv`
- `artifact_manifest.csv`
