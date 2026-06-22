# Task2291-2310 Plus8000 Feature Full-Universe Backtest

## Decision Summary

- Verdict: `plus8000_feature_full_universe_backtest_complete_diagnostic_only`.
- Brain version: `latest_brain_plus8000_feature_proxy_full_universe_v1`.
- Candidate pool: 3100 rows.
- Selection allowed after L5/gates: 206 rows.
- +8000 non-gap feature rows: 2983.
- Best policy: `plus8000_feature_full_top2_v1`.
- Best final equity: 1930.2839.
- Best CAGR: 0.13591.
- Best MDD: -0.492756.
- Same-trade sizing only: `0`.
- Strict raw/as-of complete: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task runs the user-authorized diagnostic replay using the +8000-level feature/proxy panel across the full 3,100-candidate pool. It is not a strict raw/as-of-complete replay. Missing feature sources are neutral, not negative. Scheduled returns are used only after assignment for diagnostic PnL audit.

Replay results:

- `plus8000_feature_full_top2_v1`: final 1930.2839, CAGR 0.13591, MDD -0.492756, trades 112, beats QQQ 1, joint 0.
- `plus8000_feature_full_top3_v1`: final 1806.7071, CAGR 0.121441, MDD -0.407414, trades 153, beats QQQ 0, joint 0.
- `plus8000_feature_full_top5_v1`: final 1584.2922, CAGR 0.093255, MDD -0.311747, trades 192, beats QQQ 0, joint 0.
- `plus8000_feature_full_top10_v1`: final 1281.8088, CAGR 0.049283, MDD -0.178545, trades 206, beats QQQ 0, joint 0.

Source and proxy coverage:

- `feature_schema_parity`: covered 3100/3100, ratio 1.0, policy `feature_proxy_available_missing_neutral_not_strict_raw_complete`.
- `api_proxy_not_source_gap`: covered 2983/3100, ratio 0.962258, policy `feature_proxy_available_missing_neutral_not_strict_raw_complete`.
- `financial_statement_proxy`: covered 2827/3100, ratio 0.911935, policy `feature_proxy_available_missing_neutral_not_strict_raw_complete`.
- `earnings_surprise_proxy`: covered 154/3100, ratio 0.049677, policy `feature_proxy_available_missing_neutral_not_strict_raw_complete`.
- `rating_proxy`: covered 214/3100, ratio 0.069032, policy `feature_proxy_available_missing_neutral_not_strict_raw_complete`.
- `strict_raw_asof_replay_gate_reference_only`: covered 63/3100, ratio 0.020323, policy `reference_only_not_used_for_feature_proxy_backtest`.

Comparison:

- `qqq_buy_hold_benchmark` (benchmark): final 1847.0265, CAGR 0.126318, MDD , trades .
- `task1717_bad_trade_gate_top3_full_universe` (full_universe_prior): final 3525.2985, CAGR 0.276522, MDD -0.32335, trades 160.
- `task2151_api_loop3_guarded_risk_cap_top2` (selected_116_sizing_only): final 8468.6867, CAGR 0.512794, MDD -0.339808, trades 116.
- `task2191_api_dd_guard_winner_preserve_top2` (selected_116_sizing_only): final 8011.1549, CAGR 0.496601, MDD -0.280843, trades 116.
- `plus8000_feature_full_top2_v1` (plus8000_feature_full_universe_replay): final 1930.2839, CAGR 0.13591, MDD -0.492756, trades 112.
- `plus8000_feature_full_top3_v1` (plus8000_feature_full_universe_replay): final 1806.7071, CAGR 0.121441, MDD -0.407414, trades 153.
- `plus8000_feature_full_top5_v1` (plus8000_feature_full_universe_replay): final 1584.2922, CAGR 0.093255, MDD -0.311747, trades 192.
- `plus8000_feature_full_top10_v1` (plus8000_feature_full_universe_replay): final 1281.8088, CAGR 0.049283, MDD -0.178545, trades 206.

Worst selected trades:

- `plus8000_feature_full_top10_v1` CALX 2021-12-31: pnl -40.6446, return -0.37326425, guard `winner_preserved_under_drawdown_guard`.
- `plus8000_feature_full_top10_v1` AA 2022-05-31: pnl -28.1699, return -0.2635036, guard `no_drawdown_guard`.
- `plus8000_feature_full_top10_v1` CC 2022-05-31: pnl -27.6782, return -0.25890405, guard `no_drawdown_guard`.
- `plus8000_feature_full_top10_v1` AA 2022-03-31: pnl -27.6637, return -0.24891751, guard `no_drawdown_guard`.
- `plus8000_feature_full_top10_v1` CC 2022-08-31: pnl -25.9652, return -0.27119649, guard `winner_preserved_under_drawdown_guard`.
- `plus8000_feature_full_top10_v1` AMBA 2025-01-31: pnl -22.4342, return -0.20129615, guard `no_drawdown_guard`.
- `plus8000_feature_full_top10_v1` ACAD 2025-08-31: pnl -19.8025, return -0.1713266, guard `no_drawdown_guard`.
- `plus8000_feature_full_top10_v1` AOS 2021-08-31: pnl -18.18, return -0.16220368, guard `no_drawdown_guard`.
- `plus8000_feature_full_top10_v1` ALV 2024-05-31: pnl -18.1514, return -0.16332321, guard `no_drawdown_guard`.
- `plus8000_feature_full_top10_v1` ALGM 2023-03-31: pnl -17.9509, return -0.2566364, guard `portfolio_soft_drawdown_cap`.
- `plus8000_feature_full_top10_v1` CCRN 2022-11-30: pnl -17.6288, return -0.25940636, guard `portfolio_soft_drawdown_cap`.
- `plus8000_feature_full_top10_v1` CBT 2022-05-31: pnl -16.9262, return -0.15832846, guard `no_drawdown_guard`.

## No-Background Decision-Maker Report

Conclusion first: this is the fairer comparison to the +8000 selected-trade experiment because the same feature/proxy level is now applied to the full 3,100-candidate pool. It still does not prove deployment readiness because strict raw/as-of completeness is not solved.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2291_2310_plus8000_feature_full_universe_backtest/`.
- Validator: `python scripts/trader_brain_2291_2310_plus8000_feature_full_universe_backtest_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
