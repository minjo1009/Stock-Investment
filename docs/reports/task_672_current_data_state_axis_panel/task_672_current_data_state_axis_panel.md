# Task672 Current Data State Axis Panel

## Decision Summary

- Verdict: `CURRENT_DATA_STATE_AXIS_PANEL_BUILT_NO_TRADING_PROMOTION`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Candidate rows: `1621`
- Task639: `$7639.62`, MDD `-23.76%`.
- Active relation cap3: `$10887.47`, MDD `-30.52%`.
- What changed: current-data-only state axes are now implemented and audited.
- Next action: design a predeclared action matrix from these axes, then test split/OOS and MDD gates.

## Quant Expert Report

Task672 implements the Task671 state decomposition with currently available entry-time data only. It does not use quote/trade/NBBO/microstructure data and does not create a new trading action.

### Data Source and Join Keys

- Source: Task659 panel rebuilt through Task661 mechanism state panel and Task668 replay functions.
- Join keys for replay annotation: `lifecycle_id`, `entry_ts`.
- Assignment leakage controls: return, label, future price, missing source, symbol blacklist, theme blacklist, and microstructure flags are audited as zero-use inputs.

### Account Comparison

| comparison_type | candidate_name | label | split_name | final_capital_usd | max_drawdown_pct | accepted_trade_count | qqq_final_capital_usd | beats_qqq_flag | promotion_allowed_flag | comment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| account_result | baseline_task639 | Task639 baseline | all | 7639.620310821465 | -23.755747663170702 | 54 | 1606.8278306897957 | 1 | 0 | reference comparison only |
| account_result | baseline_task639 | Task639 baseline | validation | 1069.2312936091898 | -7.363321689343804 | 15 | 1049.908329847512 | 1 | 0 | reference comparison only |
| account_result | baseline_task639 | Task639 baseline | recent_oos | 1531.9029143138666 | -0.811391994497368 | 10 | 1124.192829329964 | 1 | 0 | reference comparison only |
| account_result | active_relation_cap3_reference | Active relation cap3 reference | all | 10887.474713480713 | -30.524857842425657 | 51 | 1606.8278306897957 | 1 | 0 | reference comparison only |
| account_result | active_relation_cap3_reference | Active relation cap3 reference | validation | 1327.5223368015004 | -5.866934869678831 | 13 | 1049.908329847512 | 1 | 0 | reference comparison only |
| account_result | active_relation_cap3_reference | Active relation cap3 reference | recent_oos | 1541.4394915288256 | -1.0957772237519925 | 10 | 1124.192829329964 | 1 | 0 | reference comparison only |
| account_result | relation_priority_playbook_lite_sizing | Task668 lite sizing | all | 10183.615927393126 | -28.61213359654865 | 51 | 1606.8278306897957 | 1 | 0 | reference comparison only |
| account_result | relation_priority_playbook_lite_sizing | Task668 lite sizing | validation | 1298.0005109893289 | -5.866934869678831 | 13 | 1049.908329847512 | 1 | 0 | reference comparison only |
| account_result | relation_priority_playbook_lite_sizing | Task668 lite sizing | recent_oos | 1541.4394915288256 | -1.0957772237519925 | 10 | 1124.192829329964 | 1 | 0 | reference comparison only |
| account_result | playbook_dynamic_cap | Task668 dynamic cap | all | 5173.940688581928 | -18.758042531894326 | 46 | 1606.8278306897957 | 1 | 0 | reference comparison only |
| account_result | playbook_dynamic_cap | Task668 dynamic cap | validation | 1038.3854696195574 | -6.578720639095326 | 14 | 1049.908329847512 | 0 | 0 | reference comparison only |
| account_result | playbook_dynamic_cap | Task668 dynamic cap | recent_oos | 1667.2809903209381 | -3.525899653039477 | 11 | 1124.192829329964 | 1 | 0 | reference comparison only |

### Active Relation Cap3 Axis Exposure

| candidate_name | axis | axis_value | accepted_trade_count | avg_return_costed_pct | win_rate | entry_reduce_failure_rate | promotion_allowed_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| active_relation_cap3_reference | company_catalyst_state | hard_company_catalyst | 19 | 32.3039653389094 | 0.6842105263157895 | 0.2631578947368421 | 0 |
| active_relation_cap3_reference | company_catalyst_state | multi_dimension_high_quality_catalyst | 16 | 19.87680387069425 | 0.5625 | 0.4375 | 0 |
| active_relation_cap3_reference | company_catalyst_state | multi_signal_medium_catalyst | 15 | 53.1080098279743 | 0.6666666666666666 | 0.3333333333333333 | 0 |
| active_relation_cap3_reference | company_catalyst_state | weak_or_single_dimension_catalyst | 1 | 10.287363195607108 | 1.0 | 0.0 | 0 |
| active_relation_cap3_reference | macro_market_state | market_mixed | 33 | 38.829957161528895 | 0.696969696969697 | 0.30303030303030304 | 0 |
| active_relation_cap3_reference | macro_market_state | market_stress | 17 | 24.69377411490339 | 0.5294117647058824 | 0.4117647058823529 | 0 |
| active_relation_cap3_reference | macro_market_state | market_supportive | 1 | 37.52896770179718 | 1.0 | 0.0 | 0 |
| active_relation_cap3_reference | portfolio_capacity_state | slot_competition_low | 34 | 46.470814330771006 | 0.7058823529411765 | 0.29411764705882354 | 0 |
| active_relation_cap3_reference | portfolio_capacity_state | slot_competition_very_high | 11 | 0.8772976144599702 | 0.36363636363636365 | 0.5454545454545454 | 0 |
| active_relation_cap3_reference | portfolio_capacity_state | slot_competition_high | 6 | 24.842292163389036 | 0.8333333333333334 | 0.16666666666666666 | 0 |
| active_relation_cap3_reference | price_chart_acceptance_state | price_confirmed_basic | 33 | 21.797642933349476 | 0.6060606060606061 | 0.36363636363636365 | 0 |
| active_relation_cap3_reference | price_chart_acceptance_state | price_confirmed_but_extended | 15 | 38.24098680544985 | 0.7333333333333333 | 0.26666666666666666 | 0 |
| active_relation_cap3_reference | price_chart_acceptance_state | price_fragile_or_unconfirmed | 3 | 148.5915650344425 | 0.6666666666666666 | 0.3333333333333333 | 0 |
| active_relation_cap3_reference | proxy_risk_context | proxy_neutral | 25 | 36.50054514523282 | 0.72 | 0.28 | 0 |
| active_relation_cap3_reference | proxy_risk_context | extension_proxy | 12 | 56.237002898605304 | 0.75 | 0.25 | 0 |
| active_relation_cap3_reference | proxy_risk_context | market_stress_proxy | 8 | 9.40861883841672 | 0.375 | 0.5 | 0 |
| active_relation_cap3_reference | proxy_risk_context | stress_plus_extension_proxy | 4 | 27.34547102092379 | 0.75 | 0.25 | 0 |
| active_relation_cap3_reference | proxy_risk_context | high_liquidity_momentum_proxy | 2 | -16.64839210975252 | 0.0 | 1.0 | 0 |
| active_relation_cap3_reference | rates_dollar_credit_liquidity_state | driver_neutral_or_mixed | 17 | 80.76400510839427 | 0.7058823529411765 | 0.29411764705882354 | 0 |
| active_relation_cap3_reference | rates_dollar_credit_liquidity_state | multi_driver_support | 10 | 18.87411001122313 | 0.7 | 0.3 | 0 |
| active_relation_cap3_reference | rates_dollar_credit_liquidity_state | credit_support | 9 | 7.09533196655497 | 0.5555555555555556 | 0.4444444444444444 | 0 |
| active_relation_cap3_reference | rates_dollar_credit_liquidity_state | liquidity_support | 8 | -6.456342896082207 | 0.25 | 0.625 | 0 |
| active_relation_cap3_reference | rates_dollar_credit_liquidity_state | multi_driver_pressure_exposed | 3 | 26.506818661018343 | 1.0 | 0.0 | 0 |
| active_relation_cap3_reference | rates_dollar_credit_liquidity_state | rates_pressure_offset_by_support | 2 | 15.108173335029385 | 1.0 | 0.0 | 0 |
| active_relation_cap3_reference | rates_dollar_credit_liquidity_state | dollar_support | 1 | 48.50959509181497 | 1.0 | 0.0 | 0 |
| active_relation_cap3_reference | rates_dollar_credit_liquidity_state | liquidity_pressure_offset_by_support | 1 | 6.528884755408369 | 1.0 | 0.0 | 0 |
| active_relation_cap3_reference | relation_transmission_state | relation_reinforcing | 19 | 15.748810205695445 | 0.631578947368421 | 0.3157894736842105 | 0 |
| active_relation_cap3_reference | relation_transmission_state | company_positive_confirmation_needed | 14 | 56.33790415895008 | 0.7142857142857143 | 0.2857142857142857 | 0 |
| active_relation_cap3_reference | relation_transmission_state | company_price_confirmed_macro_secondary | 8 | 72.28676717955706 | 0.625 | 0.375 | 0 |
| active_relation_cap3_reference | relation_transmission_state | relation_offsetting | 5 | 7.154696577069878 | 0.6 | 0.4 | 0 |
| active_relation_cap3_reference | relation_transmission_state | relation_sparse_research_only | 5 | 7.3372083060575255 | 0.6 | 0.4 | 0 |
| active_relation_cap3_reference | source_integrity_state | company_certified_macro_provisional | 51 | 34.092386548737416 | 0.6470588235294118 | 0.3333333333333333 | 0 |
| active_relation_cap3_reference | theme_leadership_state | theme_participating | 27 | 33.84844494665746 | 0.5925925925925926 | 0.37037037037037035 | 0 |
| active_relation_cap3_reference | theme_leadership_state | theme_leadership_fading | 16 | 21.970110779476173 | 0.625 | 0.375 | 0 |
| active_relation_cap3_reference | theme_leadership_state | theme_leadership_expanding | 4 | 30.18641106634956 | 1.0 | 0.0 | 0 |
| active_relation_cap3_reference | theme_leadership_state | narrow_leadership | 2 | 148.81295552164278 | 1.0 | 0.0 | 0 |
| active_relation_cap3_reference | theme_leadership_state | persistent_broad_theme_leader | 2 | 27.45518632277713 | 0.5 | 0.5 | 0 |

### MDD Axis Exposure

| candidate_name | axis | axis_value | mdd_peak_ts | mdd_trough_ts | max_drawdown_pct | active_trade_count | avg_return_costed_pct | negative_mdd_exposure_flag | promotion_allowed_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| active_relation_cap3_reference | company_catalyst_state | multi_dimension_high_quality_catalyst | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 6 | 10.364351241658722 | 0 | 0 |
| active_relation_cap3_reference | company_catalyst_state | hard_company_catalyst | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 5 | 4.9094260785718715 | 0 | 0 |
| active_relation_cap3_reference | company_catalyst_state | multi_signal_medium_catalyst | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 4 | -13.0465922605981 | 1 | 0 |
| active_relation_cap3_reference | macro_market_state | market_mixed | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 10 | 0.29264401870293805 | 0 | 0 |
| active_relation_cap3_reference | macro_market_state | market_stress | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 5 | 6.3240857226779825 | 0 | 0 |
| active_relation_cap3_reference | portfolio_capacity_state | slot_competition_low | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 9 | -0.553418744280988 | 1 | 0 |
| active_relation_cap3_reference | portfolio_capacity_state | slot_competition_very_high | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 5 | 9.916799474693557 | 0 | 0 |
| active_relation_cap3_reference | portfolio_capacity_state | slot_competition_high | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 1 | -10.0563598745196 | 1 | 0 |
| active_relation_cap3_reference | price_chart_acceptance_state | price_confirmed_basic | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 12 | 0.004943509999700188 | 0 | 0 |
| active_relation_cap3_reference | price_chart_acceptance_state | price_confirmed_but_extended | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 2 | 28.453905520865774 | 0 | 0 |
| active_relation_cap3_reference | price_chart_acceptance_state | price_fragile_or_unconfirmed | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 1 | -22.42026436130865 | 1 | 0 |
| active_relation_cap3_reference | proxy_risk_context | proxy_neutral | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 8 | 6.614038288168173 | 0 | 0 |
| active_relation_cap3_reference | proxy_risk_context | market_stress_proxy | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 3 | -13.992154775717527 | 1 | 0 |
| active_relation_cap3_reference | proxy_risk_context | high_liquidity_momentum_proxy | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 2 | -16.64839210975252 | 1 | 0 |
| active_relation_cap3_reference | proxy_risk_context | extension_proxy | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 1 | -26.97397380304668 | 1 | 0 |
| active_relation_cap3_reference | proxy_risk_context | stress_plus_extension_proxy | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 1 | 83.88178484477822 | 0 | 0 |
| active_relation_cap3_reference | rates_dollar_credit_liquidity_state | driver_neutral_or_mixed | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 4 | 13.52892004092362 | 0 | 0 |
| active_relation_cap3_reference | rates_dollar_credit_liquidity_state | liquidity_support | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 4 | -18.58307210654833 | 1 | 0 |
| active_relation_cap3_reference | rates_dollar_credit_liquidity_state | credit_support | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 2 | 13.214976999711524 | 0 | 0 |
| active_relation_cap3_reference | rates_dollar_credit_liquidity_state | multi_driver_support | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 2 | -18.885862363898326 | 1 | 0 |
| active_relation_cap3_reference | rates_dollar_credit_liquidity_state | rates_pressure_offset_by_support | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 2 | 15.108173335029385 | 0 | 0 |
| active_relation_cap3_reference | rates_dollar_credit_liquidity_state | multi_driver_pressure_exposed | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 1 | 35.888901121232955 | 0 | 0 |
| active_relation_cap3_reference | relation_transmission_state | relation_reinforcing | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 5 | -6.123643082981395 | 1 | 0 |
| active_relation_cap3_reference | relation_transmission_state | company_positive_confirmation_needed | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 3 | -9.922034893694581 | 1 | 0 |
| active_relation_cap3_reference | relation_transmission_state | relation_offsetting | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 3 | 2.5736983732513985 | 0 | 0 |
| active_relation_cap3_reference | relation_transmission_state | company_price_confirmed_macro_secondary | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 2 | 36.87072850836575 | 0 | 0 |
| active_relation_cap3_reference | relation_transmission_state | relation_sparse_research_only | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 2 | 6.734318379962153 | 0 | 0 |
| active_relation_cap3_reference | source_integrity_state | company_certified_macro_provisional | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 15 | 2.303124586694618 | 0 | 0 |
| active_relation_cap3_reference | theme_leadership_state | theme_participating | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 7 | -10.78196014036095 | 1 | 0 |
| active_relation_cap3_reference | theme_leadership_state | theme_leadership_fading | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 4 | 10.41919712197738 | 0 | 0 |
| active_relation_cap3_reference | theme_leadership_state | theme_leadership_expanding | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 3 | 26.38051740659546 | 0 | 0 |
| active_relation_cap3_reference | theme_leadership_state | persistent_broad_theme_leader | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | 1 | -10.79775092474997 | 1 | 0 |

### Capacity Context

| context_type | entry_ts | portfolio_capacity_state | candidate_count | max_same_theme_count | max_same_relation_count | accepted_count | blocked_count | allocation_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_timestamp | 2026-03-23 14:30:00+00:00 | slot_competition_low | 2 | 2 | 2 |  |  |  |
| candidate_timestamp | 2026-04-20 14:30:00+00:00 | slot_competition_high | 8 | 5 | 6 |  |  |  |
| candidate_timestamp | 2026-04-22 14:30:00+00:00 | slot_competition_high | 6 | 3 | 5 |  |  |  |
| candidate_timestamp | 2026-04-23 14:30:00+00:00 | slot_competition_high | 7 | 4 | 5 |  |  |  |
| candidate_timestamp | 2026-04-24 14:30:00+00:00 | slot_competition_very_high | 18 | 6 | 10 |  |  |  |
| candidate_timestamp | 2026-04-27 14:30:00+00:00 | slot_competition_very_high | 12 | 5 | 11 |  |  |  |
| candidate_timestamp | 2026-04-29 14:30:00+00:00 | slot_competition_high | 7 | 3 | 5 |  |  |  |
| candidate_timestamp | 2026-05-06 14:30:00+00:00 | slot_competition_low | 2 | 2 | 2 |  |  |  |
| candidate_timestamp | 2026-05-08 14:30:00+00:00 | slot_competition_very_high | 21 | 5 | 10 |  |  |  |
| candidate_timestamp | 2026-05-11 14:30:00+00:00 | slot_competition_very_high | 12 | 5 | 6 |  |  |  |
| candidate_timestamp | 2026-05-13 14:30:00+00:00 | slot_competition_very_high | 20 | 6 | 8 |  |  |  |
| candidate_timestamp | 2026-05-14 14:30:00+00:00 | slot_competition_very_high | 13 | 5 | 6 |  |  |  |
| candidate_timestamp | 2026-05-15 14:30:00+00:00 | slot_competition_very_high | 12 | 6 | 8 |  |  |  |
| candidate_timestamp | 2026-05-18 14:30:00+00:00 | slot_competition_very_high | 19 | 7 | 18 |  |  |  |
| candidate_timestamp | 2026-05-28 14:30:00+00:00 | slot_competition_low | 1 | 1 | 1 |  |  |  |
| candidate_timestamp | 2026-05-29 14:30:00+00:00 | slot_competition_low | 1 | 1 | 1 |  |  |  |
| candidate_timestamp | 2026-06-01 14:30:00+00:00 | slot_competition_low | 1 | 1 | 1 |  |  |  |
| active_relation_cap3_allocation |  |  | 51 |  |  | 51 | 0 | accepted |
| active_relation_cap3_allocation |  |  | 36 |  |  | 0 | 36 | active_relation_playbook_cap |
| active_relation_cap3_allocation |  |  | 1534 |  |  | 0 | 1534 | max_positions_full |

### Sparse Cell Report

| macro_market_state | rates_dollar_credit_liquidity_state | theme_leadership_state | company_catalyst_state | price_chart_acceptance_state | relation_transmission_state | portfolio_capacity_state | candidate_count | split_name | promotion_allowed_flag | recommended_use |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| market_mixed | credit_support | persistent_broad_theme_leader | hard_company_catalyst | price_confirmed_basic | company_price_confirmed_macro_secondary | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | persistent_broad_theme_leader | hard_company_catalyst | price_confirmed_but_extended | relation_reinforcing | slot_competition_low | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | persistent_broad_theme_leader | hard_company_catalyst | price_fragile_or_unconfirmed | company_price_confirmed_macro_secondary | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | persistent_broad_theme_leader | multi_dimension_high_quality_catalyst | price_accepted_needs_confirmation | relation_reinforcing | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | persistent_broad_theme_leader | multi_dimension_high_quality_catalyst | price_confirmed_basic | company_price_confirmed_macro_secondary | slot_competition_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | persistent_broad_theme_leader | multi_dimension_high_quality_catalyst | price_confirmed_basic | relation_reinforcing | slot_competition_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | persistent_broad_theme_leader | multi_dimension_high_quality_catalyst | price_confirmed_basic | relation_sparse_research_only | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | persistent_broad_theme_leader | multi_dimension_high_quality_catalyst | price_confirmed_but_extended | relation_reinforcing | slot_competition_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | persistent_broad_theme_leader | multi_dimension_high_quality_catalyst | price_fragile_or_unconfirmed | company_price_confirmed_macro_secondary | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | persistent_broad_theme_leader | multi_signal_medium_catalyst | price_fragile_or_unconfirmed | company_positive_confirmation_needed | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | persistent_broad_theme_leader | weak_or_single_dimension_catalyst | price_confirmed_but_extended | company_positive_confirmation_needed | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | theme_leadership_expanding | hard_company_catalyst | price_accepted_needs_confirmation | relation_reinforcing | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | theme_leadership_expanding | hard_company_catalyst | price_confirmed_basic | relation_reinforcing | same_relation_crowded | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | theme_leadership_expanding | hard_company_catalyst | price_confirmed_basic | relation_sparse_research_only | slot_competition_low | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | theme_leadership_expanding | hard_company_catalyst | price_confirmed_but_extended | relation_reinforcing | slot_competition_low | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | theme_leadership_expanding | hard_company_catalyst | price_confirmed_but_extended | relation_reinforcing | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | theme_leadership_fading | hard_company_catalyst | price_confirmed_basic | company_price_confirmed_macro_secondary | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | theme_leadership_fading | hard_company_catalyst | price_confirmed_but_extended | relation_reinforcing | slot_competition_low | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | theme_leadership_fading | multi_dimension_high_quality_catalyst | price_confirmed_basic | relation_sparse_research_only | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | theme_participating | hard_company_catalyst | price_confirmed_basic | relation_reinforcing | slot_competition_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | theme_participating | hard_company_catalyst | price_fragile_or_unconfirmed | relation_sparse_research_only | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | theme_participating | multi_dimension_high_quality_catalyst | price_accepted_needs_confirmation | relation_reinforcing | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | theme_participating | multi_dimension_high_quality_catalyst | price_confirmed_but_extended | relation_offsetting | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | theme_participating | multi_dimension_high_quality_catalyst | price_confirmed_but_extended | relation_reinforcing | slot_competition_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | theme_participating | multi_dimension_high_quality_catalyst | price_fragile_or_unconfirmed | relation_reinforcing | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | theme_participating | multi_signal_medium_catalyst | price_accepted_needs_confirmation | company_positive_confirmation_needed | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | credit_support | theme_participating | multi_signal_medium_catalyst | price_confirmed_but_extended | relation_sparse_research_only | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | dollar_pressure_offset_by_support | theme_participating | hard_company_catalyst | price_confirmed_basic | relation_reinforcing | slot_competition_low | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | dollar_pressure_offset_by_support | theme_participating | multi_dimension_high_quality_catalyst | price_fragile_or_unconfirmed | relation_reinforcing | same_relation_crowded | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | dollar_support | theme_leadership_fading | multi_signal_medium_catalyst | price_confirmed_basic | company_positive_confirmation_needed | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | dollar_support | theme_participating | hard_company_catalyst | price_confirmed_basic | relation_reinforcing | slot_competition_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | dollar_support | theme_participating | hard_company_catalyst | price_confirmed_basic | relation_reinforcing | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | dollar_support | theme_participating | multi_signal_medium_catalyst | price_confirmed_basic | company_positive_confirmation_needed | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | driver_neutral_or_mixed | narrow_leadership | hard_company_catalyst | price_confirmed_basic | company_price_confirmed_macro_secondary | slot_competition_low | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | driver_neutral_or_mixed | narrow_leadership | multi_dimension_high_quality_catalyst | price_confirmed_but_extended | company_price_confirmed_macro_secondary | slot_competition_low | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | driver_neutral_or_mixed | persistent_broad_theme_leader | hard_company_catalyst | price_confirmed_basic | company_price_confirmed_macro_secondary | slot_competition_low | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | driver_neutral_or_mixed | persistent_broad_theme_leader | hard_company_catalyst | price_confirmed_but_extended | company_price_confirmed_macro_secondary | slot_competition_very_high | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | driver_neutral_or_mixed | persistent_broad_theme_leader | multi_dimension_high_quality_catalyst | price_confirmed_basic | company_price_confirmed_macro_secondary | same_relation_crowded | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | driver_neutral_or_mixed | persistent_broad_theme_leader | multi_dimension_high_quality_catalyst | price_confirmed_basic | company_price_confirmed_macro_secondary | slot_competition_low | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |
| market_mixed | driver_neutral_or_mixed | persistent_broad_theme_leader | multi_dimension_high_quality_catalyst | price_confirmed_but_extended | company_price_confirmed_macro_secondary | same_relation_crowded | 1 | all | 0 | diagnostic_only_until_cell_has_enough_split_oos_support |

### Forbidden Input Audit

| check_name | violation_count | pass_flag | required_value |
| --- | --- | --- | --- |
| return_used_in_assignment_flag | 0 | 1 | 0 violations |
| label_used_in_assignment_flag_task661 | 0 | 1 | 0 violations |
| microstructure_used_in_assignment | 0 | 1 | 0 violations |
| missing_source_used_as_signal | 0 | 1 | 0 violations |
| symbol_blacklist_used | 0 | 1 | 0 violations |
| theme_blacklist_used | 0 | 1 | 0 violations |
| future_price_used_in_assignment | 0 | 1 | 0 violations |

## No-Background Decision-Maker Report

상태를 더 잘게 쪼개는 코드는 구현됐습니다.

아직 새 매매 룰은 아닙니다. 지금은 어떤 상태가 돈을 벌고, 어떤 상태가 낙폭을 만드는지 보는 진단판입니다.

미시구조 데이터는 아직 수집 중이라 쓰지 않았습니다. 차트 데이터를 미시구조처럼 속여 쓰지도 않았습니다.

다음은 이 상태축으로 선제 룰을 정하고, 그 룰이 OOS와 낙폭에서 살아남는지 검증해야 합니다.

## Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| state_axis_panel_built | 1 | rows=1621 | candidate-level current-data state panel exists |
| all_8_axes_present | 1 | axes=8 | 8 implementable axes |
| microstructure_not_used | 1 | SOURCE_PENDING_NOT_USED | microstructure assignment flag zero |
| forbidden_input_audit_clean | 1 | violations=0 | 0 forbidden-input violations |
| axis_value_performance_built | 1 | rows=125 | axis diagnostics exist |
| active_cap3_axis_exposure_built | 1 | rows=37 | active cap3 axis exposure exists |
| mdd_axis_exposure_built | 1 | rows=32 | MDD window axis exposure exists |
| capacity_context_built | 1 | rows=218 | slot/capacity context exists |
| sparse_cell_report_built | 1 | rows=764 | sparse cells identified |
| comparison_summary_built | 1 | rows=22 | Task639 active cap3 Task668 comparison exists |
| trading_action_allowed | 0 | diagnostic decomposition only | predeclared action mapping and OOS gates required |
| real_capital_allowed | 0 | FORBIDDEN | accepted strategy plus live-source readiness |

## Artifact Manifest

- `task672_state_axis_panel.csv`
- `task672_axis_value_performance.csv`
- `task672_active_relation_cap3_axis_exposure.csv`
- `task672_mdd_axis_exposure_report.csv`
- `task672_capacity_context_report.csv`
- `task672_sparse_cell_report.csv`
- `task672_forbidden_input_audit.csv`
- `task672_comparison_summary.csv`
- `task672_candidate_grid_reference.csv`
- `task_672_decision.csv`
- `task_672_pass_fail_matrix.csv`
- `artifact_manifest.csv`
