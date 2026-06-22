# Task640 Leverage ETF Drawdown Upgrade

## Decision Summary

- Verdict: `PASS_COMBO_RETURN_UP_DRAWDOWN_DOWN_RESEARCH_CANDIDATE_NOT_ACCEPTED`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Task639 baseline: $7639.62, max drawdown -23.76%
- Best exclusion: `symbol:MDB` -> $8482.25, DD -23.76%
- Best leveraged ETF overlay: `long_3x_theme_proxy` weight 0.30 -> $3777.95, DD -26.41%
- Best drawdown throttle: `size_reduce` -> $7217.35, DD -23.76%
- Best combo: `symbol:MDB` + threshold -5.0% / multiplier 0.75 -> $7692.60, DD -23.63%

## Quant Expert Report

Task640 tested four direct ways to increase return and reduce drawdown over Task639: single theme/symbol exclusion, leveraged ETF theme overlays, realized drawdown throttles, and exclusion-plus-throttle combos. The acceptance bar was strict: a candidate must beat Task639 final capital and have a less severe max drawdown.

### Source Audit

| task_id | source_rule | base_source_trade_count | task639_same_rule_pass_candidate_count | leveraged_etf_symbols_available | leveraged_etf_available_count | leveraged_overlay_configs | leveraged_overlay_min_price_coverage_rate | label_used_in_assignment_flag | presence_field_used_for_assignment_flag | gpt_or_plugin_used_as_source_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Task640 | Task639 best same-rule candidate | 1621 | 21 | LABU,QLD,SOXL,SSO,TQQQ,UPRO | 6 | 10 | 0.7937888198757764 | 0 | 0 | 0 |

### Top Exclusion Tests

| policy | target_type | target_value | source_trade_count | accepted_trade_count | final_capital_usd | max_drawdown_pct | entry_reduce_failure_rate | final_delta_vs_task639_usd | drawdown_delta_vs_task639_pct_point | return_up_drawdown_down_pass_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| exclude_one | symbol | MDB | 1596 | 54 | 8482.251607715529 | -23.755747663170702 | 0.35185185185185186 | 842.6312968940638 | 0.0 | 0 |
| exclude_one | symbol | NOC | 1600 | 53 | 8402.82592020914 | -23.755747663170702 | 0.32075471698113206 | 763.2056093876745 | 0.0 | 0 |
| exclude_one | symbol | ASML | 1589 | 54 | 8061.794913807896 | -23.755747663170702 | 0.37037037037037035 | 422.1746029864307 | 0.0 | 0 |
| exclude_one | symbol | PLTR | 1587 | 53 | 8039.052847618057 | -23.755747663170702 | 0.33962264150943394 | 399.4325367965921 | 0.0 | 0 |
| exclude_one | symbol | ETN | 1601 | 54 | 7915.1952634513045 | -23.755747663170702 | 0.3888888888888889 | 275.5749526298396 | 0.0 | 0 |
| none | none | none | 1621 | 54 | 7639.620310821465 | -23.755747663170702 | 0.37037037037037035 | 0.0 | 0.0 | 0 |
| exclude_one | theme | cybersecurity | 1459 | 54 | 7639.620310821465 | -23.755747663170702 | 0.37037037037037035 | 0.0 | 0.0 | 0 |
| exclude_one | theme | ev_autonomy_mobility | 1532 | 54 | 7639.620310821465 | -23.755747663170702 | 0.37037037037037035 | 0.0 | 0.0 | 0 |
| exclude_one | symbol | VRT | 1580 | 54 | 7639.620310821465 | -23.755747663170702 | 0.37037037037037035 | 0.0 | 0.0 | 0 |
| exclude_one | symbol | PWR | 1580 | 54 | 7639.620310821465 | -23.755747663170702 | 0.37037037037037035 | 0.0 | 0.0 | 0 |
| exclude_one | symbol | TER | 1582 | 54 | 7639.620310821465 | -23.755747663170702 | 0.37037037037037035 | 0.0 | 0.0 | 0 |
| exclude_one | symbol | TSM | 1582 | 54 | 7639.620310821465 | -23.755747663170702 | 0.37037037037037035 | 0.0 | 0.0 | 0 |

### Top Leveraged ETF Overlay Tests

| overlay_name | overlay_weight | mapped_trade_count | priced_trade_count | price_coverage_rate | source_trade_count | accepted_trade_count | final_capital_usd | max_drawdown_pct | entry_reduce_failure_rate | final_delta_vs_task639_usd | drawdown_delta_vs_task639_pct_point | return_up_drawdown_down_pass_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| long_3x_theme_proxy | 0.3 | 805 | 644 | 0.8 | 644 | 42 | 3777.949707430741 | -26.405584036687777 | 0.4523809523809524 | -3861.670603390724 | -2.6498363735170756 | 0 |
| long_3x_theme_proxy | 0.5 | 805 | 644 | 0.8 | 644 | 42 | 3748.8692098227366 | -27.8342003857747 | 0.4523809523809524 | -3890.7511009987284 | -4.078452722603998 | 0 |
| long_3x_theme_proxy | 0.2 | 805 | 644 | 0.8 | 644 | 42 | 3734.5879805625996 | -25.65109489692089 | 0.4523809523809524 | -3905.0323302588654 | -1.8953472337501864 | 0 |
| long_3x_theme_proxy | 0.1 | 805 | 644 | 0.8 | 644 | 42 | 3652.934099740639 | -24.873328062046596 | 0.4523809523809524 | -3986.686211080826 | -1.1175803988758943 | 0 |
| long_2x_theme_proxy | 0.1 | 805 | 639 | 0.7937888198757764 | 639 | 39 | 3217.2342816625246 | -23.3070124167713 | 0.46153846153846156 | -4422.386029158941 | 0.44873524639940143 | 0 |
| long_3x_theme_proxy | 1.0 | 805 | 644 | 0.8 | 644 | 42 | 3043.3916228837816 | -33.57248274128521 | 0.4523809523809524 | -4596.228687937683 | -9.816735078114505 | 0 |
| long_2x_theme_proxy | 0.2 | 805 | 639 | 0.7937888198757764 | 639 | 39 | 2999.9535028877954 | -22.49395498353717 | 0.46153846153846156 | -4639.66680793367 | 1.2617926796335333 | 0 |
| long_2x_theme_proxy | 0.3 | 805 | 639 | 0.7937888198757764 | 639 | 39 | 2783.1967751999773 | -21.631496000238613 | 0.46153846153846156 | -4856.423535621488 | 2.124251662932089 | 0 |
| long_2x_theme_proxy | 0.5 | 805 | 639 | 0.7937888198757764 | 639 | 39 | 2354.439025869558 | -19.739436040790416 | 0.46153846153846156 | -5285.1812849519065 | 4.016311622380286 | 0 |
| long_2x_theme_proxy | 1.0 | 805 | 639 | 0.7937888198757764 | 639 | 39 | 1350.0619969501763 | -16.739646042045543 | 0.46153846153846156 | -6289.558313871288 | 7.016101621125159 | 0 |

### Top Drawdown Throttle Tests

| policy | drawdown_threshold_pct | position_multiplier | cooldown_days | accepted_trade_count | final_capital_usd | max_drawdown_pct | entry_reduce_failure_rate | final_delta_vs_task639_usd | drawdown_delta_vs_task639_pct_point | return_up_drawdown_down_pass_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| size_reduce | -15.0 | 0.75 | 0 | 54 | 7217.352399261596 | -23.755747663170702 | 0.35185185185185186 | -422.2679115598694 | 0.0 | 0 |
| size_reduce | -10.0 | 0.75 | 0 | 54 | 6951.2552867712775 | -24.055690902159775 | 0.35185185185185186 | -688.3650240501875 | -0.2999432389890728 | 0 |
| size_reduce | -5.0 | 0.75 | 0 | 54 | 6766.773095912819 | -23.627756955860914 | 0.35185185185185186 | -872.8472149086456 | 0.12799070730978812 | 0 |
| size_reduce | -15.0 | 0.5 | 0 | 54 | 6750.352422183694 | -23.755747663170702 | 0.35185185185185186 | -889.2678886377707 | 0.0 | 0 |
| size_reduce | -10.0 | 0.5 | 0 | 54 | 6025.126578894095 | -24.369902459285342 | 0.35185185185185186 | -1614.4937319273704 | -0.6141547961146401 | 0 |
| size_reduce | -5.0 | 0.5 | 0 | 54 | 5715.086579856482 | -23.51609476412658 | 0.35185185185185186 | -1924.533730964983 | 0.23965289904412046 | 0 |
| size_reduce | -15.0 | 0.25 | 0 | 54 | 5649.495608537098 | -23.755747663170702 | 0.35185185185185186 | -1990.1247022843672 | 0.0 | 0 |
| size_reduce | -5.0 | 0.25 | 0 | 54 | 4482.746875600223 | -23.421954598368732 | 0.35185185185185186 | -3156.8734352212423 | 0.33379306480197 | 0 |
| size_reduce | -10.0 | 0.25 | 0 | 54 | 4412.338721574046 | -24.6994252576485 | 0.35185185185185186 | -3227.281589247419 | -0.9436775944777978 | 0 |
| cooldown_skip | -15.0 | 0.0 | 5 | 25 | 4022.90017232689 | -23.755747663170702 | 0.4 | -3616.720138494575 | 0.0 | 0 |
| cooldown_skip | -15.0 | 0.0 | 10 | 25 | 4022.90017232689 | -23.755747663170702 | 0.4 | -3616.720138494575 | 0.0 | 0 |
| cooldown_skip | -15.0 | 0.0 | 20 | 25 | 4022.90017232689 | -23.755747663170702 | 0.4 | -3616.720138494575 | 0.0 | 0 |

### Top Exclusion Plus Throttle Combo Tests

| target_type | target_value | drawdown_threshold_pct | position_multiplier | cooldown_days | accepted_trade_count | final_capital_usd | max_drawdown_pct | entry_reduce_failure_rate | final_delta_vs_task639_usd | drawdown_delta_vs_task639_pct_point | return_up_drawdown_down_pass_flag | single_name_exclusion_overfit_risk_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| symbol | MDB | -5.0 | 0.75 | 0 | 54 | 7692.603156894304 | -23.627756955860914 | 0.3333333333333333 | 52.98284607283949 | 0.12799070730978812 | 1 | 1 |
| symbol | MDB | -20.0 | 0.75 | 0 | 54 | 8320.667215505113 | -23.755747663170702 | 0.3333333333333333 | 681.0469046836479 | 0.0 | 0 | 1 |
| symbol | NOC | -20.0 | 0.75 | 0 | 53 | 8276.526655639598 | -23.755747663170702 | 0.32075471698113206 | 636.9063448181332 | 0.0 | 0 | 1 |
| symbol | MDB | -20.0 | 0.5 | 0 | 54 | 8159.082823294685 | -23.755747663170702 | 0.3333333333333333 | 519.4625124732202 | 0.0 | 0 | 1 |
| symbol | NOC | -20.0 | 0.5 | 0 | 53 | 8150.227391070054 | -23.755747663170702 | 0.32075471698113206 | 510.6070802485892 | 0.0 | 0 | 1 |
| symbol | NOC | -20.0 | 0.25 | 0 | 53 | 8023.92812650052 | -23.755747663170702 | 0.32075471698113206 | 384.30781567905524 | 0.0 | 0 | 1 |
| symbol | MDB | -15.0 | 0.75 | 0 | 54 | 8013.129777376186 | -23.755747663170702 | 0.3333333333333333 | 373.50946655472126 | 0.0 | 0 | 1 |
| symbol | MDB | -20.0 | 0.25 | 0 | 54 | 7997.498431084264 | -23.755747663170702 | 0.3333333333333333 | 357.8781202627988 | 0.0 | 0 | 1 |
| symbol | MDB | -10.0 | 0.75 | 0 | 54 | 7888.643454682429 | -24.055690902159775 | 0.3333333333333333 | 249.0231438609644 | -0.2999432389890728 | 0 | 1 |
| symbol | PLTR | -20.0 | 0.75 | 0 | 53 | 7885.878609038137 | -23.755747663170702 | 0.32075471698113206 | 246.2582982166723 | 0.0 | 0 | 1 |
| symbol | NOC | -15.0 | 0.75 | 0 | 53 | 7865.490400528214 | -23.755747663170702 | 0.32075471698113206 | 225.87008970674924 | 0.0 | 0 | 1 |
| symbol | ASML | -20.0 | 0.75 | 0 | 54 | 7811.015422448088 | -23.755747663170702 | 0.35185185185185186 | 171.39511162662347 | 0.0 | 0 | 1 |

## No-Background Decision-Maker Report

- Leveraged ETFs did not help this rule. They lowered return and made drawdown worse or not better.
- Removing one bad-looking theme or symbol also did not produce a clean return-up and drawdown-down improvement.
- Drawdown throttles can reduce some damage, but they cut too much upside.
- One combo did improve both: exclude `MDB`, then cut new position size to 75% after realized drawdown passes -5%.
- This is not accepted because single-name exclusion can be curve-fit. Next step is to prove why that name should be excluded with pre-entry source/content evidence or reject it.

## Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| task639_baseline_reproduced | 1 | $7639.62, dd=-23.76% | Task639 reported baseline must be reproduced |
| leveraged_etf_data_available | 1 | LABU,QLD,SOXL,SSO,TQQQ,UPRO | leveraged ETF daily data must exist for overlay test |
| exclusion_filter_improves_task639 | 0 | best=symbol:MDB $8482.25, dd=-23.76% | final capital above Task639 and drawdown less severe |
| leveraged_etf_improves_task639 | 0 | best=long_3x_theme_proxy w=0.30 $3777.95, dd=-26.41% | final capital above Task639 and drawdown less severe |
| drawdown_throttle_improves_task639 | 0 | best=size_reduce $7217.35, dd=-23.76% | final capital above Task639 and drawdown less severe |
| exclusion_plus_throttle_improves_task639 | 1 | best=symbol:MDB thr=-5.0 mult=0.75 $7692.60, dd=-23.63% | final capital above Task639 and drawdown less severe |
| combo_overfit_risk_block | 0 | combo uses single symbol/theme exclusion | single-name or single-theme exclusions require fresh OOS and causal pre-entry rule before acceptance |
| any_return_up_drawdown_down_upgrade_found | 1 | any_pass=1 | at least one tested upgrade must improve both return and drawdown |
| trading_promotion | 0 | research rejection or candidate only | requires live-readable rule lock, source latency audit, and paper-shadow replay |

## Artifact Manifest

- `task_640_task639_baseline_recheck.csv`
- `task_640_exclusion_filter_grid.csv`
- `task_640_leverage_etf_overlay_grid.csv`
- `task_640_drawdown_throttle_grid.csv`
- `task_640_exclusion_throttle_combo_grid.csv`
- `task_640_source_audit.csv`
- `task_640_pass_fail_matrix.csv`
- `task_640_decision.csv`
- `task_640_gpt_review_packet.txt`
- `task_640_gpt_review_response.md`
- `artifact_manifest.csv`
