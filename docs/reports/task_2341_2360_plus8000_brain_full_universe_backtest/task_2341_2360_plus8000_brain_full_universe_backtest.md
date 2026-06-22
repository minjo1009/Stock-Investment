# Task2341-2360 Plus8000 Brain Full-Universe Backtest

## Decision Summary

- Verdict: `plus8000_brain_full_universe_backtest_complete_diagnostic_only`.
- Full universe candidate rows: 3100.
- L5 decision rows: 3100.
- Original candidate set only: `0`.
- Plus8000 brain structure preserved: `1`.
- Same replay capital path as +8000: `1`.
- Best policy: `plus8000_full_actual_else_scheduled_soft_boost_cap_top2_v1`.
- Best final equity: 5935.0135.
- Best CAGR: 0.412093.
- Best MDD: -0.280467.
- Joint target met: `1`.
- Strict raw/as-of complete: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task applies the +8000 brain structure to the full 3,100-candidate universe: pre-entry risk budget, winner defense, winner acceleration, Task2251 new-data API overlay, and Task2191 drawdown/sizing guard. It does not reuse only the old 116 trades. It includes two return-source policies: uniform scheduled returns for all candidates, and actual Task1788 returns where available with scheduled fallback for full-universe extension rows.

Replay results:

- `plus8000_full_scheduled_uniform_soft_boost_cap_top2_v1`: final 3622.5377, CAGR 0.28327, MDD -0.425479, trades 124.
- `plus8000_full_scheduled_uniform_stress_neutral_top2_v1`: final 3491.196, CAGR 0.27412, MDD -0.395642, trades 124.
- `plus8000_full_scheduled_uniform_winner_preserve_top2_v1`: final 3234.0859, CAGR 0.255373, MDD -0.374111, trades 124.
- `plus8000_full_actual_else_scheduled_soft_boost_cap_top2_v1`: final 5935.0135, CAGR 0.412093, MDD -0.280467, trades 124.
- `plus8000_full_actual_else_scheduled_stress_neutral_top2_v1`: final 5209.8343, CAGR 0.376881, MDD -0.266827, trades 124.
- `plus8000_full_actual_else_scheduled_winner_preserve_top2_v1`: final 4952.6662, CAGR 0.363442, MDD -0.250101, trades 124.

Comparison:

- `qqq_buy_hold_benchmark` (benchmark): final 1847.0265, CAGR 0.126318, MDD , trades .
- `api_dd_guard_soft_boost_cap_top2_v1` (original_plus8000_selected_trade): final 8079.7165, CAGR 0.499074, MDD -0.327669, trades 116.
- `api_dd_guard_stress_neutral_top2_v1` (original_plus8000_selected_trade): final 8060.7699, CAGR 0.498392, MDD -0.316043, trades 116.
- `api_dd_guard_winner_preserve_top2_v1` (original_plus8000_selected_trade): final 8011.1549, CAGR 0.496601, MDD -0.280843, trades 116.
- `plus8000_feature_full_top2_v1` (prior_wrong_full_universe_proxy): final 1930.2839, CAGR 0.13591, MDD -0.492756, trades 112.
- `plus8000_feature_full_top3_v1` (prior_wrong_full_universe_proxy): final 1806.7071, CAGR 0.121441, MDD -0.407414, trades 153.
- `plus8000_feature_full_top5_v1` (prior_wrong_full_universe_proxy): final 1584.2922, CAGR 0.093255, MDD -0.311747, trades 192.
- `plus8000_feature_full_top10_v1` (prior_wrong_full_universe_proxy): final 1281.8088, CAGR 0.049283, MDD -0.178545, trades 206.
- `plus8000_brain_newdata_soft_boost_cap_top2_v1` (plus8000_brain_existing_universe_newdata): final 7876.4302, CAGR 0.49169, MDD -0.328559, trades 116.
- `plus8000_brain_newdata_stress_neutral_top2_v1` (plus8000_brain_existing_universe_newdata): final 7886.7314, CAGR 0.492068, MDD -0.316043, trades 116.
- `plus8000_brain_newdata_winner_preserve_top2_v1` (plus8000_brain_existing_universe_newdata): final 7776.9153, CAGR 0.48802, MDD -0.280843, trades 116.
- `plus8000_full_scheduled_uniform_soft_boost_cap_top2_v1` (plus8000_brain_structure_full_universe): final 3622.5377, CAGR 0.28327, MDD -0.425479, trades 124.
- `plus8000_full_scheduled_uniform_stress_neutral_top2_v1` (plus8000_brain_structure_full_universe): final 3491.196, CAGR 0.27412, MDD -0.395642, trades 124.
- `plus8000_full_scheduled_uniform_winner_preserve_top2_v1` (plus8000_brain_structure_full_universe): final 3234.0859, CAGR 0.255373, MDD -0.374111, trades 124.
- `plus8000_full_actual_else_scheduled_soft_boost_cap_top2_v1` (plus8000_brain_structure_full_universe): final 5935.0135, CAGR 0.412093, MDD -0.280467, trades 124.
- `plus8000_full_actual_else_scheduled_stress_neutral_top2_v1` (plus8000_brain_structure_full_universe): final 5209.8343, CAGR 0.376881, MDD -0.266827, trades 124.
- `plus8000_full_actual_else_scheduled_winner_preserve_top2_v1` (plus8000_brain_structure_full_universe): final 4952.6662, CAGR 0.363442, MDD -0.250101, trades 124.

Coverage:

- `full_universe_candidate_rows`: 3100/3100 (1.0).
- `l5_decision_rows`: 3100/3100 (1.0).
- `api_proxy_supportive_rows`: 1250/3100 (0.403226).
- `api_proxy_source_gap_rows`: 117/3100 (0.037742).
- `return_source_task1509_scheduled_uniform`: 5985/6200 (0.965323).
- `return_source_task1788_actual_exit_available`: 215/6200 (0.034677).

Selection overlap:

- `api_dd_guard_soft_boost_cap_top2_v1` -> `plus8000_full_actual_else_scheduled_soft_boost_cap_top2_v1`: common 98/116 old, added 26, removed 18.
- `api_dd_guard_stress_neutral_top2_v1` -> `plus8000_full_actual_else_scheduled_stress_neutral_top2_v1`: common 98/116 old, added 26, removed 18.
- `api_dd_guard_winner_preserve_top2_v1` -> `plus8000_full_actual_else_scheduled_winner_preserve_top2_v1`: common 98/116 old, added 26, removed 18.

## No-Background Decision-Maker Report

Conclusion first: this is the requested shape: +8000 brain structure, new data, full universe. It remains diagnostic because strict raw/as-of completeness is not solved and full-universe extension still uses generated bridge rows for stages that originally existed only on the 377-row +8000 candidate set.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2341_2360_plus8000_brain_full_universe_backtest/`.
- Validator: `python scripts/trader_brain_2341_2360_plus8000_brain_full_universe_backtest_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
