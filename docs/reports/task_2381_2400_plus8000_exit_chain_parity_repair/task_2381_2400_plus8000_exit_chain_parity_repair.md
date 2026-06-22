# Task2381-2400 Plus8000 Exit Chain Parity Repair

## Decision Summary

- Verdict: `plus8000_exit_chain_parity_repaired_diagnostic_only`.
- Full universe candidate rows: 3100.
- Repaired exit source rows: 3100.
- Selected 116 parity diff rows: 0.
- Price gap rows: 0.
- Scheduled fallback rows: 0.
- Same selected trades only: `0`.
- Generic Task2361 exit replaced: `1`.
- Best policy: `exit_chain_repaired_soft_boost_cap_top2_v1`.
- Best final equity: 6537.58.
- Best CAGR: 0.4388.
- Best MDD: -0.282109.
- Joint target met: `1`.
- Strict raw/as-of complete: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task repairs the Task2361 mistake by copying original +8000 exit-chain source rows wherever Task1788/Task1704/Task1668 source truth exists. The selected 116 +8000 trades must match the original chain exactly before the full-universe replay is considered reviewable. Non-original full-universe rows use an extended Task1668 `decide_action` path and are clearly tagged by extension method.

Replay results:

- `exit_chain_repaired_soft_boost_cap_top2_v1`: final 6537.58, CAGR 0.4388, MDD -0.282109, trades 124.
- `exit_chain_repaired_stress_neutral_top2_v1`: final 6297.7805, CAGR 0.42842, MDD -0.269595, trades 124.
- `exit_chain_repaired_winner_preserve_top2_v1`: final 6095.1082, CAGR 0.419395, MDD -0.252561, trades 124.

Coverage:

- `full_universe_candidate_rows`: 3100/3100 (1.0).
- `repaired_exit_source_rows`: 3100/3100 (1.0).
- `price_gap_rows`: 0/3100 (0.0).
- `scheduled_fallback_rows`: 0/3100 (0.0).
- `selected_116_parity_rows`: 116/116 (1.0).
- `selected_116_parity_diff_rows`: 0/116 (0.0).
- `extension_method_copied_original_task1792_1704_1668_source`: 215/3100 (0.069355).
- `extension_method_task1668_decide_action_extended`: 2885/3100 (0.930645).

Comparison:

- `qqq_buy_hold_benchmark` (benchmark): final 1847.0265, CAGR 0.126318, MDD , trades .
- `api_dd_guard_soft_boost_cap_top2_v1` (original_plus8000_selected_trade): final 8079.7165, CAGR 0.499074, MDD -0.327669, trades 116.
- `api_dd_guard_stress_neutral_top2_v1` (original_plus8000_selected_trade): final 8060.7699, CAGR 0.498392, MDD -0.316043, trades 116.
- `api_dd_guard_winner_preserve_top2_v1` (original_plus8000_selected_trade): final 8011.1549, CAGR 0.496601, MDD -0.280843, trades 116.
- `plus8000_brain_newdata_soft_boost_cap_top2_v1` (plus8000_brain_existing_universe_newdata): final 7876.4302, CAGR 0.49169, MDD -0.328559, trades 116.
- `plus8000_brain_newdata_stress_neutral_top2_v1` (plus8000_brain_existing_universe_newdata): final 7886.7314, CAGR 0.492068, MDD -0.316043, trades 116.
- `plus8000_brain_newdata_winner_preserve_top2_v1` (plus8000_brain_existing_universe_newdata): final 7776.9153, CAGR 0.48802, MDD -0.280843, trades 116.
- `plus8000_full_scheduled_uniform_soft_boost_cap_top2_v1` (prior_full_universe_partial_actual_or_scheduled): final 3622.5377, CAGR 0.28327, MDD -0.425479, trades 124.
- `plus8000_full_scheduled_uniform_stress_neutral_top2_v1` (prior_full_universe_partial_actual_or_scheduled): final 3491.196, CAGR 0.27412, MDD -0.395642, trades 124.
- `plus8000_full_scheduled_uniform_winner_preserve_top2_v1` (prior_full_universe_partial_actual_or_scheduled): final 3234.0859, CAGR 0.255373, MDD -0.374111, trades 124.
- `plus8000_full_actual_else_scheduled_soft_boost_cap_top2_v1` (prior_full_universe_partial_actual_or_scheduled): final 5935.0135, CAGR 0.412093, MDD -0.280467, trades 124.
- `plus8000_full_actual_else_scheduled_stress_neutral_top2_v1` (prior_full_universe_partial_actual_or_scheduled): final 5209.8343, CAGR 0.376881, MDD -0.266827, trades 124.
- `plus8000_full_actual_else_scheduled_winner_preserve_top2_v1` (prior_full_universe_partial_actual_or_scheduled): final 4952.6662, CAGR 0.363442, MDD -0.250101, trades 124.
- `full_exit_quality_soft_boost_cap_top2_v1` (generic_full_exit_quality_wrong_chain): final 4051.3878, CAGR 0.311394, MDD -0.424046, trades 124.
- `full_exit_quality_stress_neutral_top2_v1` (generic_full_exit_quality_wrong_chain): final 3688.9428, CAGR 0.287795, MDD -0.40621, trades 124.
- `full_exit_quality_winner_preserve_top2_v1` (generic_full_exit_quality_wrong_chain): final 3484.4839, CAGR 0.273645, MDD -0.382287, trades 124.
- `exit_chain_repaired_soft_boost_cap_top2_v1` (repaired_plus8000_exit_chain_full_universe): final 6537.58, CAGR 0.4388, MDD -0.282109, trades 124.
- `exit_chain_repaired_stress_neutral_top2_v1` (repaired_plus8000_exit_chain_full_universe): final 6297.7805, CAGR 0.42842, MDD -0.269595, trades 124.
- `exit_chain_repaired_winner_preserve_top2_v1` (repaired_plus8000_exit_chain_full_universe): final 6095.1082, CAGR 0.419395, MDD -0.252561, trades 124.

Failure attribution:

- `runtime_action` / reduce: rows 24, pnl -915.7915, avg_return -0.029654.
- `symbol` / CC: rows 1, pnl -275.6931, avg_return -0.233724.
- `symbol` / CALX: rows 1, pnl -260.2256, avg_return -0.272039.
- `symbol` / AGX: rows 1, pnl -159.9436, avg_return -0.073424.
- `symbol` / BRZE: rows 2, pnl -157.9051, avg_return -0.078401.
- `symbol` / ASO: rows 1, pnl -155.4818, avg_return -0.199377.
- `symbol` / AOS: rows 2, pnl -131.0238, avg_return -0.056722.
- `symbol` / AZTA: rows 1, pnl -106.0413, avg_return -0.117.
- `symbol` / AVGO: rows 21, pnl -100.1462, avg_return 0.007854.
- `symbol` / CBT: rows 2, pnl -93.3232, avg_return -0.03734.
- `symbol` / AME: rows 1, pnl -68.971, avg_return -0.074202.
- `symbol` / ADM: rows 1, pnl -56.8211, avg_return -0.086651.
- `symbol` / AZO: rows 2, pnl -51.8043, avg_return -0.019812.
- `symbol` / ALKT: rows 1, pnl -46.7486, avg_return -0.038259.
- `symbol` / CE: rows 2, pnl -36.032, avg_return -0.023873.
- `symbol` / BMRN: rows 1, pnl -29.7219, avg_return -0.051664.
- `extension_method` / task1668_decide_action_extended: rows 18, pnl -27.5176, avg_return -0.000499.
- `symbol` / APH: rows 2, pnl -22.1679, avg_return -0.003867.
- `symbol` / AWK: rows 1, pnl -20.3413, avg_return -0.023638.
- `symbol` / ACN: rows 3, pnl -11.474, avg_return -0.0017.
- `symbol` / ADI: rows 5, pnl -5.778, avg_return -0.015121.
- `symbol` / AMP: rows 1, pnl -3.2383, avg_return -0.003525.
- `symbol` / CDNA: rows 1, pnl -1.6442, avg_return -0.00132.
- `symbol` / BLK: rows 3, pnl 6.1361, avg_return -0.000538.
- `symbol` / ACVA: rows 1, pnl 13.0771, avg_return 0.011498.
- `symbol` / CB: rows 2, pnl 24.0743, avg_return 0.010335.
- `symbol` / ADBE: rows 1, pnl 24.774, avg_return 0.059454.
- `symbol` / AIG: rows 1, pnl 27.4755, avg_return 0.045862.
- `symbol` / AMZN: rows 3, pnl 29.7276, avg_return 0.007075.
- `symbol` / BFH: rows 1, pnl 33.6235, avg_return 0.049387.
- `symbol` / AMBA: rows 1, pnl 35.2157, avg_return 0.067703.
- `symbol` / AEP: rows 1, pnl 35.3848, avg_return 0.028363.
- `symbol` / BNY: rows 1, pnl 64.3707, avg_return 0.146545.
- `symbol` / AXS: rows 1, pnl 77.105, avg_return 0.052521.
- `symbol` / AFG: rows 4, pnl 102.0472, avg_return 0.043749.
- `symbol` / ALNY: rows 1, pnl 122.8088, avg_return 0.108131.
- `symbol` / CAT: rows 2, pnl 125.3273, avg_return 0.081714.
- `symbol` / BRO: rows 1, pnl 125.8323, avg_return 0.097469.
- `symbol` / AMAT: rows 3, pnl 132.4955, avg_return 0.074484.
- `symbol` / ALGM: rows 1, pnl 144.0451, avg_return 0.128993.

## No-Background Decision-Maker Report

Conclusion first: the original +8000 selected-trade exit chain is now parity-locked before full-universe extension. This is still diagnostic because extension rows are replay outcome rows, not live-source readiness.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2381_2400_plus8000_exit_chain_parity_repair/`.
- Validator: `python scripts/trader_brain_2381_2400_plus8000_exit_chain_parity_repair_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
