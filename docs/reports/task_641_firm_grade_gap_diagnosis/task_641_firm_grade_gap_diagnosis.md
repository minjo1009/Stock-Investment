# Task641 Firm-Grade Gap Diagnosis

## Decision Summary

- Verdict: `DIAGNOSE_FIRM_GRADE_GAPS_BEFORE_MORE_ALPHA_SEARCH`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Task639 baseline: $7639.62, max drawdown -23.76%
- Accepted trades: 54/1621
- Median holding days: 85.4
- Top priority gap: `entry_quality_confirmation_missing`

## Quant Expert Report

Task641 is a diagnosis task. It does not add a new trading rule. It identifies what must be improved before chasing more alpha.

### Baseline

| task_id | source_rule | source_trade_count | accepted_trade_count | skipped_due_capacity_count | capacity_acceptance_rate | final_capital_usd | task639_reported_final_capital_usd | max_drawdown_pct | task639_reported_max_drawdown_pct | avg_net_return_pct | win_rate | entry_reduce_failure_rate | median_holding_days | large_loss_trade_count | microstructure_available_rate | label_used_in_assignment_flag | presence_field_used_for_assignment_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Task641 | Task639 positive_contract_customer OR content_supply_demand / delay1d / existing_exit / equal_max5 / 50bp | 1621 | 54 | 1567 | 0.033312769895126465 | 7639.620310821465 | 7639.620310821465 | -23.755747663170702 | -23.755747663170705 | 26.43398519539194 | 0.5740740740740741 | 0.37037037037037035 | 85.42708333333333 | 13 | 0.0 | 0 | 0 |

### Capacity Sensitivity

| max_positions | accepted_trade_count | final_capital_usd | max_drawdown_pct | avg_net_return_pct | entry_reduce_failure_rate | skipped_due_capacity_count |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | 32 | 9241.054375518084 | -27.32862330647954 | 30.336327650196115 | 0.375 | 1589 |
| 5 | 54 | 7639.620310821465 | -23.755747663170702 | 26.43398519539194 | 0.37037037037037035 | 1567 |
| 7 | 74 | 6313.194382728866 | -27.72007287304862 | 24.138996268720785 | 0.36486486486486486 | 1547 |
| 10 | 101 | 4709.128540580766 | -21.974285991321562 | 19.612655315806006 | 0.37623762376237624 | 1520 |
| 15 | 145 | 2857.0602779357696 | -26.280400810259074 | 13.275627861551767 | 0.38620689655172413 | 1476 |
| 20 | 181 | 2514.5859698287477 | -23.09473828908932 | 12.03988573812494 | 0.3812154696132597 | 1440 |
| 30 | 248 | 2288.258567652686 | -21.763409140496336 | 11.618500379837261 | 0.375 | 1373 |
| 50 | 385 | 1768.916454578474 | -20.940688632124406 | 8.650681869593434 | 0.4155844155844156 | 1236 |

### Signal Tier Diagnostics

| scope | signal_tier | trade_count | avg_net_return_pct | win_rate | large_loss_rate |
| --- | --- | --- | --- | --- | --- |
| source_all | both_contract_and_supply | 646 | 4.165005145863546 | 0.5108359133126935 | 0.3157894736842105 |
| source_all | contract_only | 90 | 4.535039608120902 | 0.45555555555555555 | 0.34444444444444444 |
| source_all | supply_only | 885 | 6.173243067020239 | 0.5627118644067797 | 0.280225988700565 |
| accepted_max5 | both_contract_and_supply | 19 | 19.800483109044002 | 0.5789473684210527 | 0.3684210526315789 |
| accepted_max5 | contract_only | 7 | 46.04527131771897 | 0.8571428571428571 | 0.0 |
| accepted_max5 | supply_only | 28 | 26.03246865197486 | 0.6071428571428571 | 0.21428571428571427 |

### Drawdown Damage

| dimension | bucket | accepted_trade_count | avg_net_return_pct | worst_trade_return_pct | large_loss_count | loss_trade_count |
| --- | --- | --- | --- | --- | --- | --- |
| timing_state | opening_drive | 41 | 25.678712725531422 | -26.97397380304668 | 9 | 14 |
| split_name | train_design | 30 | 39.99494235090527 | -26.97397380304668 | 8 | 10 |
| theme_id | data_devops_software | 9 | 8.669124998129963 | -26.97397380304668 | 4 | 5 |
| split_name | validation | 14 | 3.9676470440566507 | -25.89604274338907 | 4 | 6 |
| symbol | DDOG | 4 | -2.9545385179633286 | -26.97397380304668 | 3 | 3 |
| symbol | ASTS | 11 | 49.19420903460677 | -26.427844603207628 | 3 | 4 |
| theme_id | aerospace_defense_space | 16 | 66.74517714076721 | -26.427844603207628 | 3 | 4 |
| theme_id | cloud_ai_platforms | 4 | -21.647365502117 | -25.89604274338907 | 3 | 4 |
| timing_state | midday_continuation | 11 | 13.041089157105354 | -25.227870877505236 | 3 | 5 |
| symbol | AMZN | 3 | -20.231139755026305 | -25.540961396692442 | 2 | 3 |
| symbol | AMGN | 4 | -9.494701258437644 | -11.52907895315929 | 2 | 4 |
| theme_id | biotech_glp1_healthcare | 4 | -9.494701258437644 | -11.52907895315929 | 2 | 4 |
| timing_state | late_day_confirmation | 2 | 115.57799903810877 | -26.427844603207628 | 1 | 1 |
| symbol | CRM | 1 | -25.89604274338907 | -25.89604274338907 | 1 | 1 |
| symbol | AMD | 5 | 13.508729017878935 | -16.856345575196073 | 1 | 1 |
| theme_id | ai_semiconductors | 8 | 16.776993691823105 | -16.856345575196073 | 1 | 1 |
| symbol | PLTR | 1 | -14.29981817543989 | -14.29981817543989 | 1 | 1 |
| split_name | recent_oos | 10 | 17.203987140721377 | -11.52907895315929 | 1 | 4 |
| symbol | EMR | 1 | -9.76544717195588 | -9.76544717195588 | 0 | 1 |
| theme_id | industrial_automation_robotics | 6 | 18.048384508542345 | -9.76544717195588 | 0 | 1 |

### Dimension Diagnostics

| dimension | bucket | accepted_trade_count | avg_net_return_pct | large_loss_rate |
| --- | --- | --- | --- | --- |
| broad_market_stress | (-inf, 25.0] | 9 | 4.6936577535696715 | 0.2222222222222222 |
| broad_market_stress | (25.0, 35.0] | 22 | 30.43636838610754 | 0.22727272727272727 |
| broad_market_stress | (35.0, 45.0] | 13 | 40.50404376973845 | 0.3076923076923077 |
| broad_market_stress | (45.0, inf] | 10 | 18.903960726807206 | 0.2 |
| intraday_entry_state_v4 | intraday_breakout_acceptance | 54 | 26.43398519539194 | 0.24074074074074073 |
| microstructure_state_v4 | microstructure_not_available | 54 | 26.43398519539194 | 0.24074074074074073 |
| multi_day_market_state_v4 | constructive_risk_on | 54 | 26.43398519539194 | 0.24074074074074073 |
| range_pos | (-inf, 0.85] | 2 | 55.539455917245064 | 0.0 |
| range_pos | (0.85, 0.95] | 27 | 22.021331743481817 | 0.2962962962962963 |
| range_pos | (0.95, 0.99] | 18 | 39.53468218212514 | 0.1111111111111111 |
| range_pos | (0.99, inf] | 7 | 1.4508646234875824 | 0.42857142857142855 |
| theme_rank_prev | (-inf, 2.0] | 31 | 36.42212380426279 | 0.1935483870967742 |
| theme_rank_prev | (2.0, 5.0] | 20 | 14.167751634923073 | 0.3 |
| theme_rank_prev | (5.0, 10.0] | 3 | 4.998109973518941 | 0.3333333333333333 |
| theme_regime_state_v4 | narrow_theme_leader | 1 | 3.40718929389442 | 0.0 |
| theme_regime_state_v4 | persistent_theme_leader | 24 | 30.95335965012664 | 0.20833333333333334 |
| theme_regime_state_v4 | theme_participation | 29 | 23.487840677732105 | 0.27586206896551724 |
| volume_ratio_prev | (-inf, 1.0] | 25 | 34.51370849062394 | 0.4 |
| volume_ratio_prev | (1.0, 1.5] | 21 | 18.164902619502918 | 0.09523809523809523 |
| volume_ratio_prev | (1.5, 2.0] | 6 | 25.06419803470785 | 0.0 |
| volume_ratio_prev | (2.0, inf] | 2 | 16.372172533879027 | 0.5 |

### Firm-Grade Gap Matrix

| priority | gap | evidence | why_it_matters | next_test | acceptance_bar |
| --- | --- | --- | --- | --- | --- |
| 1 | entry_quality_confirmation_missing | All accepted trades share broad intraday_breakout_acceptance; no VWAP/opening-range/relative-strength confirmation has been locked for Task639. | May remove large loss trades before capital is committed. | Task641A: same Task639 signal plus pre-entry VWAP/opening-range/theme-RS/volume confirmation. | Beat Task639 final capital and max drawdown with same rule in validation and recent OOS. |
| 2 | risk_normalized_sizing_missing | Equal max5 sizes high-vol and low-vol names the same; large loss count is 13. | A few high-vol losers can drive most drawdown even when signal is good. | Task641B: ATR/gap/volatility-bucket sizing with fixed max gross exposure. | Lower max drawdown without reducing validation and recent OOS QQQ edge. |
| 3 | signal_strength_tiering_underused | both_contract_and_supply/accepted_max5: n=19, avg=19.80%; contract_only/accepted_max5: n=7, avg=46.05%; supply_only/accepted_max5: n=28, avg=26.03% | The OR rule treats different economic evidence strength as the same bet. | Task641C: both features full size, single-feature normal or confirmation-required size. | Tiered sizing improves return/DD and does not rely on symbol identity. |
| 4 | capital_turnover_and_exit_policy_underdeveloped | Only 54/1621 trades accepted; median hold 85.4 days; cap3 final $9241.05 with worse DD, cap10 final $4709.13 with lower DD. | The strategy may be using capital inefficiently; current exit wins by long winners but blocks many candidates. | Task641D: profit-lock/trailing/partial exit and capital recycling only after entry-quality and risk sizing. | Higher capital turnover with no validation/recent OOS degradation. |
| 5 | microstructure_source_gap | Accepted-trade microstructure availability rate is 0.00%. | Cannot distinguish real continuation from thin/fragile breakout at execution time. | Task641E: source-ready microstructure fields before live or paper-shadow promotion. | Live-readable fields with timestamp provenance; no inferred lifecycle matching. |
| 6 | damage_cluster_causality_missing | data_devops_software: large_loss=4, avg=8.67%; aerospace_defense_space: large_loss=3, avg=66.75%; cloud_ai_platforms: large_loss=3, avg=-21.65% | Single-symbol exclusions are overfit unless converted to causal pre-entry rules. | Task641F: explain worst accepted losses by source relevance, price reaction, volatility, and entry tape. | No single-name blacklist; only general rules surviving split/OOS. |

## No-Background Decision-Maker Report

- The main missing piece is not leveraged ETF exposure.
- The biggest missing pieces are entry quality, volatility-aware sizing, signal strength tiering, and capital turnover.
- Current Task639 uses only 54 of 1,621 candidate trades because capital is locked for a long time.
- Single-name exclusions are not acceptable until converted into causal pre-entry rules.
- Next tests should keep the Task639 signal fixed and improve execution/risk around it.

## Artifact Manifest

- `task_641_task639_baseline_diagnostic.csv`
- `task_641_task639_accepted_trades.csv`
- `task_641_capacity_sensitivity.csv`
- `task_641_signal_tier_diagnostics.csv`
- `task_641_drawdown_damage_table.csv`
- `task_641_dimension_diagnostics.csv`
- `task_641_firm_grade_gap_matrix.csv`
- `task_641_decision.csv`
- `task_641_gpt_review_packet.txt`
- `task_641_gpt_review_response.md`
- `artifact_manifest.csv`
