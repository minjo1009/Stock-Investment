# Task2361-2380 Full Exit Quality Parity Backtest

## Decision Summary

- Verdict: `full_exit_quality_parity_backtest_complete_diagnostic_only`.
- Full universe candidate rows: 3100.
- Exit quality rows: 3100.
- Price gap rows: 0.
- Scheduled fallback rows: `0`.
- Same selected trades only: `0`.
- Selector brain preserved: `1`.
- Best policy: `full_exit_quality_soft_boost_cap_top2_v1`.
- Best final equity: 4051.3878.
- Best CAGR: 0.311394.
- Best MDD: -0.424046.
- Joint target met: `0`.
- Strict raw/as-of complete: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task removes the scheduled-return fallback from Task2341 for the full 3,100-candidate L5 universe. It generates Task1704-compatible entry/planned-exit/runtime-exit/reduce/hold return rows from cached daily price paths for every candidate with price coverage. The return rows are replay outcome only and are not used for assignment or ranking.

Replay results:

- `full_exit_quality_soft_boost_cap_top2_v1`: final 4051.3878, CAGR 0.311394, MDD -0.424046, trades 124.
- `full_exit_quality_stress_neutral_top2_v1`: final 3688.9428, CAGR 0.287795, MDD -0.40621, trades 124.
- `full_exit_quality_winner_preserve_top2_v1`: final 3484.4839, CAGR 0.273645, MDD -0.382287, trades 124.

Coverage:

- `l5_candidate_rows`: 3100/3100 (1.0).
- `exit_quality_packet_rows`: 3100/3100 (1.0).
- `return_source_rows`: 3100/3100 (1.0).
- `price_gap_rows`: 0/3100 (0.0).
- `runtime_action_exit`: 76/3100 (0.024516).
- `runtime_action_hold`: 2749/3100 (0.886774).
- `runtime_action_reduce`: 275/3100 (0.08871).

Comparison:

- `qqq_buy_hold_benchmark` (benchmark): final 1847.0265, CAGR 0.126318, MDD , trades .
- `api_dd_guard_soft_boost_cap_top2_v1` (original_plus8000_selected_trade): final 8079.7165, CAGR 0.499074, MDD -0.327669, trades 116.
- `api_dd_guard_stress_neutral_top2_v1` (original_plus8000_selected_trade): final 8060.7699, CAGR 0.498392, MDD -0.316043, trades 116.
- `api_dd_guard_winner_preserve_top2_v1` (original_plus8000_selected_trade): final 8011.1549, CAGR 0.496601, MDD -0.280843, trades 116.
- `plus8000_brain_newdata_soft_boost_cap_top2_v1` (plus8000_brain_existing_universe_newdata): final 7876.4302, CAGR 0.49169, MDD -0.328559, trades 116.
- `plus8000_brain_newdata_stress_neutral_top2_v1` (plus8000_brain_existing_universe_newdata): final 7886.7314, CAGR 0.492068, MDD -0.316043, trades 116.
- `plus8000_brain_newdata_winner_preserve_top2_v1` (plus8000_brain_existing_universe_newdata): final 7776.9153, CAGR 0.48802, MDD -0.280843, trades 116.
- `plus8000_full_scheduled_uniform_soft_boost_cap_top2_v1` (prior_full_universe_scheduled_or_partial_actual): final 3622.5377, CAGR 0.28327, MDD -0.425479, trades 124.
- `plus8000_full_scheduled_uniform_stress_neutral_top2_v1` (prior_full_universe_scheduled_or_partial_actual): final 3491.196, CAGR 0.27412, MDD -0.395642, trades 124.
- `plus8000_full_scheduled_uniform_winner_preserve_top2_v1` (prior_full_universe_scheduled_or_partial_actual): final 3234.0859, CAGR 0.255373, MDD -0.374111, trades 124.
- `plus8000_full_actual_else_scheduled_soft_boost_cap_top2_v1` (prior_full_universe_scheduled_or_partial_actual): final 5935.0135, CAGR 0.412093, MDD -0.280467, trades 124.
- `plus8000_full_actual_else_scheduled_stress_neutral_top2_v1` (prior_full_universe_scheduled_or_partial_actual): final 5209.8343, CAGR 0.376881, MDD -0.266827, trades 124.
- `plus8000_full_actual_else_scheduled_winner_preserve_top2_v1` (prior_full_universe_scheduled_or_partial_actual): final 4952.6662, CAGR 0.363442, MDD -0.250101, trades 124.
- `full_exit_quality_soft_boost_cap_top2_v1` (full_exit_quality_parity_full_universe): final 4051.3878, CAGR 0.311394, MDD -0.424046, trades 124.
- `full_exit_quality_stress_neutral_top2_v1` (full_exit_quality_parity_full_universe): final 3688.9428, CAGR 0.287795, MDD -0.40621, trades 124.
- `full_exit_quality_winner_preserve_top2_v1` (full_exit_quality_parity_full_universe): final 3484.4839, CAGR 0.273645, MDD -0.382287, trades 124.

Selection overlap:

- `full_exit_quality_winner_preserve_top2_v1`: common 98/116, added 26, removed 18.

Failure attribution:

- `selected_symbol_pnl` / CALX: rows 1, pnl -386.7399, avg_return -0.373264.
- `selected_symbol_pnl` / AOS: rows 2, pnl -152.7684, avg_return -0.061483.
- `selected_symbol_pnl` / CBT: rows 2, pnl -146.1481, avg_return -0.112627.
- `selected_symbol_pnl` / CC: rows 1, pnl -143.641, avg_return -0.258904.
- `selected_symbol_pnl` / ASO: rows 1, pnl -98.8955, avg_return -0.199377.
- `selected_symbol_pnl` / AGX: rows 1, pnl -87.196, avg_return -0.070414.
- `selected_symbol_pnl` / AZTA: rows 1, pnl -86.5269, avg_return -0.089522.
- `selected_symbol_pnl` / BRZE: rows 2, pnl -65.5753, avg_return -0.064431.
- `selected_symbol_pnl` / CE: rows 2, pnl -41.2155, avg_return -0.023873.
- `selected_symbol_pnl` / ADM: rows 1, pnl -37.6053, avg_return -0.086651.
- `selected_symbol_pnl` / ALKT: rows 1, pnl -25.2083, avg_return -0.038259.
- `selected_symbol_pnl` / AME: rows 1, pnl -22.0739, avg_return -0.040395.
- `selected_symbol_pnl` / BMRN: rows 1, pnl -19.6705, avg_return -0.051664.
- `selected_symbol_pnl` / AZO: rows 2, pnl -18.3633, avg_return -0.012509.
- `selected_symbol_pnl` / AWK: rows 1, pnl -11.9141, avg_return -0.023638.
- `selected_symbol_pnl` / AMZN: rows 3, pnl -9.7412, avg_return 0.003898.
- `selected_symbol_pnl` / AMP: rows 1, pnl -7.0237, avg_return -0.013353.
- `selected_symbol_pnl` / ACN: rows 3, pnl -6.2564, avg_return -0.0017.
- `selected_symbol_pnl` / ANET: rows 14, pnl -4.7091, avg_return 0.000569.
- `selected_symbol_pnl` / BLK: rows 3, pnl -3.6056, avg_return -0.002454.
- `selected_symbol_pnl` / APH: rows 2, pnl -0.6166, avg_return -0.003867.
- `selected_symbol_pnl` / ACVA: rows 1, pnl 5.6314, avg_return 0.011498.
- `selected_symbol_pnl` / CB: rows 2, pnl 14.4962, avg_return 0.007776.
- `selected_symbol_pnl` / AIG: rows 1, pnl 15.0715, avg_return 0.024645.
- `selected_symbol_pnl` / ADI: rows 5, pnl 20.8173, avg_return -0.005438.
- `selected_symbol_pnl` / AEP: rows 1, pnl 23.7618, avg_return 0.028363.
- `selected_symbol_pnl` / ADBE: rows 1, pnl 27.4581, avg_return 0.059454.
- `selected_symbol_pnl` / BFH: rows 1, pnl 33.9544, avg_return 0.049387.
- `selected_symbol_pnl` / AMBA: rows 1, pnl 35.2157, avg_return 0.067703.
- `selected_symbol_pnl` / CDNA: rows 1, pnl 41.3333, avg_return 0.059714.
- `selected_symbol_pnl` / ALNY: rows 1, pnl 42.1348, avg_return 0.06334.
- `selected_symbol_pnl` / AXS: rows 1, pnl 42.8445, avg_return 0.052521.
- `selected_symbol_pnl` / AFG: rows 4, pnl 65.6866, avg_return 0.033791.
- `selected_symbol_pnl` / ALGM: rows 1, pnl 67.6787, avg_return 0.142354.
- `selected_symbol_pnl` / CAT: rows 2, pnl 68.5357, avg_return 0.074669.
- `selected_symbol_pnl` / BRO: rows 1, pnl 68.7508, avg_return 0.097469.
- `selected_symbol_pnl` / BNY: rows 1, pnl 69.4298, avg_return 0.146545.
- `selected_symbol_pnl` / ALHC: rows 2, pnl 92.1282, avg_return 0.067204.
- `selected_symbol_pnl` / AYI: rows 2, pnl 98.8222, avg_return 0.059047.
- `selected_symbol_pnl` / AMD: rows 1, pnl 114.2002, avg_return 0.208059.

## No-Background Decision-Maker Report

Conclusion first: full exit-quality parity is now attached to the 3,100-candidate pool. This removes scheduled fallback rows from the replay source. The result is still diagnostic because the exit path uses post-decision market prices for replay outcome only, not strict live-source readiness.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2361_2380_full_exit_quality_parity_backtest/`.
- Validator: `python scripts/trader_brain_2361_2380_full_exit_quality_parity_backtest_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
