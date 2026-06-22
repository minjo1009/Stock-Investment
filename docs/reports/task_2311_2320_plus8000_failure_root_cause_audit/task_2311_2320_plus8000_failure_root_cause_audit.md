# Task2311-2320 Plus8000 Failure Root Cause Audit

## Decision Summary

- Verdict: `root_cause_not_same_experiment_plus_selector_and_sizing_path_break`.
- Current Task2291 top2: final 1930.2839, CAGR 0.13591, MDD -0.492756.
- Reference Task2151 +8000: final 8011.1549, CAGR 0.496601, MDD -0.280843.
- Common trade count: 85.
- Primary cause: Task2291 did not exact-replay the +8000 selector/sizing stack; it ran a new full-universe selector and different capital path..
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Experiment metrics:

- `Task1717_full_universe_prior` / `bad_trade_gate_top3_v1`: final 3525.2985, CAGR 0.276522, MDD -0.32335, trades 160.
- `Task1717_full_universe_prior` / `bad_trade_gate_top5_v1`: final 2638.334, CAGR 0.206812, MDD -0.286708, trades 217.
- `Task2151_selected_trade_plus8000` / `api_loop3_filings_quality_top2_v1`: final 8397.7405, CAGR 0.51033, MDD -0.339808, trades 116.
- `Task2151_selected_trade_plus8000` / `api_loop3_source_gap_neutral_top2_v1`: final 8397.7405, CAGR 0.51033, MDD -0.339808, trades 116.
- `Task2151_selected_trade_plus8000` / `api_loop3_guarded_risk_cap_top2_v1`: final 8468.6867, CAGR 0.512794, MDD -0.339808, trades 116.
- `Task2191_selected_trade_dd_guard` / `api_dd_guard_soft_boost_cap_top2_v1`: final 8079.7165, CAGR 0.499074, MDD -0.327669, trades 116.
- `Task2191_selected_trade_dd_guard` / `api_dd_guard_stress_neutral_top2_v1`: final 8060.7699, CAGR 0.498392, MDD -0.316043, trades 116.
- `Task2191_selected_trade_dd_guard` / `api_dd_guard_winner_preserve_top2_v1`: final 8011.1549, CAGR 0.496601, MDD -0.280843, trades 116.
- `Task2291_full_universe_proxy` / `plus8000_feature_full_top2_v1`: final 1930.2839, CAGR 0.13591, MDD -0.492756, trades 112.
- `Task2291_full_universe_proxy` / `plus8000_feature_full_top3_v1`: final 1806.7071, CAGR 0.121441, MDD -0.407414, trades 153.
- `Task2291_full_universe_proxy` / `plus8000_feature_full_top5_v1`: final 1584.2922, CAGR 0.093255, MDD -0.311747, trades 192.
- `Task2291_full_universe_proxy` / `plus8000_feature_full_top10_v1`: final 1281.8088, CAGR 0.049283, MDD -0.178545, trades 206.

Root-cause ranking:

- 1. `not_same_experiment`: Task2151/2191 use SOURCE_POLICY winner_defense_budget_top5_v1 selected-trade universe; Task2291 reselects from 3100 using Task2201-style full replay plus proxy adjustment.
- 2. `exact_sizing_engine_not_reused`: Common Task2191-overlap trades: current pnl 971.5025 vs Task2191 pnl 6460.9339; capital path, cap multiplier, and exit/return path differ materially.
- 3. `bad_trades_ranked_good_before_sizing`: 25/25 worst top2 losses were marked eligible/top3 payoff and ordinary_pass collapse.
- 4. `broad_proxy_not_selection_power`: Feature proxy coverage is broad, but earnings_surprise_proxy and rating_proxy coverage are sparse; supportive/mixed proxy states did not distinguish near-term losers.
- 5. `concentration_amplifies_selector_errors`: Task2291 top2 final 1930.2839 MDD -0.492756 vs Task2151 final 8468.6867 MDD -0.339808.

Data coverage interpretation:

- `feature_schema_parity`: 3100/3100 (1.0) - broad_but_low_specificity_proxy.
- `api_proxy_not_source_gap`: 2983/3100 (0.962258) - broad_but_low_specificity_proxy.
- `financial_statement_proxy`: 2827/3100 (0.911935) - broad_but_low_specificity_proxy.
- `earnings_surprise_proxy`: 154/3100 (0.049677) - selection_power_sparse.
- `rating_proxy`: 214/3100 (0.069032) - selection_power_sparse.
- `strict_raw_asof_replay_gate_reference_only`: 63/3100 (0.020323) - selection_power_sparse.

Worst top2 selection failures:

- CALX 2021-12-31: rank 2, pnl -224.8633, payoff `top3_payoff_candidate`, collapse `ordinary_pass`, proxy `api_proxy_mixed_or_light`.
- CC 2022-05-31: rank 1, pnl -132.9709, payoff `top3_payoff_candidate`, collapse `ordinary_pass`, proxy `api_proxy_mixed_or_light`.
- AMBA 2025-01-31: rank 2, pnl -122.6675, payoff `eligible_payoff_candidate`, collapse `ordinary_pass`, proxy `api_proxy_supportive`.
- CC 2022-08-31: rank 1, pnl -110.5353, payoff `top3_payoff_candidate`, collapse `ordinary_pass`, proxy `api_proxy_mixed_or_light`.
- AOS 2021-08-31: rank 2, pnl -107.0148, payoff `top3_payoff_candidate`, collapse `ordinary_pass`, proxy `api_proxy_mixed_or_light`.
- ALV 2024-05-31: rank 2, pnl -97.1884, payoff `top3_payoff_candidate`, collapse `ordinary_pass`, proxy `api_proxy_mixed_or_light`.
- ANET 2024-03-31: rank 1, pnl -89.9513, payoff `top3_payoff_candidate`, collapse `ordinary_pass`, proxy `api_proxy_supportive`.
- CBT 2022-05-31: rank 2, pnl -81.3161, payoff `top3_payoff_candidate`, collapse `ordinary_pass`, proxy `api_proxy_mixed_or_light`.
- AMZN 2025-01-31: rank 1, pnl -56.3906, payoff `top3_payoff_candidate`, collapse `ordinary_pass`, proxy `api_proxy_supportive`.
- AZTA 2021-11-30: rank 1, pnl -54.1789, payoff `top3_payoff_candidate`, collapse `ordinary_pass`, proxy `api_proxy_supportive`.
- CDNA 2024-11-30: rank 1, pnl -52.5266, payoff `top3_payoff_candidate`, collapse `ordinary_pass`, proxy `api_proxy_mixed_or_light`.
- BNY 2021-08-31: rank 1, pnl -41.703, payoff `top3_payoff_candidate`, collapse `ordinary_pass`, proxy `api_proxy_supportive`.

## No-Background Decision-Maker Report

Conclusion first: the +8000 result and the new full-universe replay are not the same experiment. The old result proved that a prefiltered winner-defense basket plus aggressive sizing could compound well. The new result tested a different full-universe selector and a different capital path. Therefore the failure is not explained by data volume alone; it is a stack mismatch plus unresolved selector weakness.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2311_2320_plus8000_failure_root_cause_audit/`.
- Validator: `python scripts/trader_brain_2311_2320_plus8000_failure_root_cause_audit_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
