# Task2201-2230 Latest Brain Full-Universe Replay

## Decision Summary

- Verdict: `latest_brain_full_universe_replay_complete_diagnostic_only`.
- Brain version: `latest_brain_full_universe_v1`.
- Candidate pool: 3100 rows.
- Selection allowed after L5/gates: 206 rows.
- API exact coverage: 217 rows; missing rows are neutral, not negative.
- Best new policy: `latest_brain_full_top3_dd_guard_v1`.
- Best final equity: 1749.2956.
- Best CAGR: 0.114445.
- Best MDD: -0.452625.
- Same-trade sizing only: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task freezes the latest usable L0-L5 brain into `latest_brain_full_universe_v1` and applies it to the 3,100-row canonical candidate pool. It reselects trades from the full pool instead of applying sizing to the previous 116 selected trades. Scheduled returns are used only after assignment for diagnostic PnL audit.

Replay results:

- `latest_brain_full_top3_v1`: final 1697.7196, CAGR 0.108001, MDD -0.481275, trades 153, beats QQQ 0, joint 0.
- `latest_brain_full_top5_v1`: final 1596.7433, CAGR 0.094914, MDD -0.311512, trades 192, beats QQQ 0, joint 0.
- `latest_brain_full_top10_v1`: final 1286.3089, CAGR 0.049996, MDD -0.17761, trades 206, beats QQQ 0, joint 0.
- `latest_brain_full_top3_dd_guard_v1`: final 1749.2956, CAGR 0.114445, MDD -0.452625, trades 153, beats QQQ 0, joint 0.
- `latest_brain_full_top5_dd_guard_v1`: final 1592.551, CAGR 0.094357, MDD -0.307999, trades 192, beats QQQ 0, joint 0.

Source family coverage:

- `sec_candidate_filings`: covered 3006/3100, missing 94, policy `covered_positive_only_missing_neutral`.
- `sec_survival`: covered 2754/3100, missing 346, policy `covered_positive_only_missing_neutral`.
- `ir_ceo_exhibit`: covered 2771/3100, missing 329, policy `covered_positive_only_missing_neutral`.
- `contract_exhibit`: covered 2850/3100, missing 250, policy `covered_positive_only_missing_neutral`.
- `price_gate`: covered 3100/3100, missing 0, policy `covered_positive_only_missing_neutral`.
- `analyst_pit`: covered 0/3100, missing 3100, policy `covered_positive_only_missing_neutral`.
- `api_hardened_overlay`: covered 217/3100, missing 2883, policy `exact_api_rows_only_missing_neutral_no_penalty`.

Comparison:

- `qqq_buy_hold_benchmark` (benchmark): final 1847.0265, CAGR 0.126318, MDD , trades .
- `task1717_bad_trade_gate_top3_full_universe` (full_universe_prior): final 3525.2985, CAGR 0.276522, MDD -0.32335, trades 160.
- `task2151_api_loop3_guarded_risk_cap_top2` (selected_116_sizing_only): final 8468.6867, CAGR 0.512794, MDD -0.339808, trades 116.
- `task2191_api_dd_guard_winner_preserve_top2` (selected_116_sizing_only): final 8011.1549, CAGR 0.496601, MDD -0.280843, trades 116.
- `latest_brain_full_top3_v1` (full_universe_latest_brain_replay): final 1697.7196, CAGR 0.108001, MDD -0.481275, trades 153.
- `latest_brain_full_top5_v1` (full_universe_latest_brain_replay): final 1596.7433, CAGR 0.094914, MDD -0.311512, trades 192.
- `latest_brain_full_top10_v1` (full_universe_latest_brain_replay): final 1286.3089, CAGR 0.049996, MDD -0.17761, trades 206.
- `latest_brain_full_top3_dd_guard_v1` (full_universe_latest_brain_replay): final 1749.2956, CAGR 0.114445, MDD -0.452625, trades 153.
- `latest_brain_full_top5_dd_guard_v1` (full_universe_latest_brain_replay): final 1592.551, CAGR 0.094357, MDD -0.307999, trades 192.

Worst selected trades:

- `latest_brain_full_top10_v1` CALX 2021-12-31: pnl -40.5546, return -0.37326425, guard `no_drawdown_guard`.
- `latest_brain_full_top10_v1` AA 2022-05-31: pnl -28.1384, return -0.2635036, guard `no_drawdown_guard`.
- `latest_brain_full_top10_v1` CC 2022-05-31: pnl -27.6472, return -0.25890405, guard `no_drawdown_guard`.
- `latest_brain_full_top10_v1` AA 2022-03-31: pnl -27.6002, return -0.24891751, guard `no_drawdown_guard`.
- `latest_brain_full_top10_v1` CC 2022-08-31: pnl -25.9948, return -0.27119649, guard `no_drawdown_guard`.
- `latest_brain_full_top10_v1` ALGM 2023-03-31: pnl -25.6, return -0.2566364, guard `no_drawdown_guard`.
- `latest_brain_full_top10_v1` CCRN 2022-11-30: pnl -25.3296, return -0.25940636, guard `no_drawdown_guard`.
- `latest_brain_full_top10_v1` AMBA 2025-01-31: pnl -22.5992, return -0.20129615, guard `no_drawdown_guard`.
- `latest_brain_full_top10_v1` ACAD 2025-08-31: pnl -19.863, return -0.1713266, guard `no_drawdown_guard`.
- `latest_brain_full_top10_v1` ALV 2024-05-31: pnl -18.2404, return -0.16332321, guard `no_drawdown_guard`.

## No-Background Decision-Maker Report

Conclusion first: this is no longer the same 116 trades with different sizing. The brain picked again from the 3,100-candidate pool. The result should therefore be read as a harder and more realistic diagnostic than the previous selected-trade sizing replay.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2201_2230_latest_brain_full_universe_replay/`.
- Skill installed for repeated acquisition: `C:/Users/minjo/.codex/skills/trader-brain-source-acquisition`.
- Validator: `python scripts/trader_brain_2201_2230_latest_brain_full_universe_replay_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
