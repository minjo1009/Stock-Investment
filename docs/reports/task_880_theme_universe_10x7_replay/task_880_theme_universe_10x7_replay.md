# Task880 Theme Universe 10x7 Controlled Replay

## Decision Summary

- Verdict: executed.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Universe: `10 themes x 7 symbols`, 70 rows and 70 unique symbols.
- Benchmark data: QQQ included separately.
- Initial capital: `$1,000`.
- Theme universe result: `$1,000 -> $944.73`.
- QQQ same-window result: `$1,000 -> $966.74`.
- QQQ long-term reference: `$1,000 -> $2,406.19`.
- Next action: decompose weak themes and define whether theme selection or trade-spec mapping should be tightened.

## Quant Expert Report

Data source and readiness:

- Source universe: `data/raw/theme_universe_10x7.csv`.
- Theme count: 10.
- Symbols per theme: 7.
- Unique universe symbols: 70.
- Data symbols acquired: 71 including QQQ benchmark.
- Daily acquisition: 71/71 ok.
- Intraday 15m acquisition: 71/71 ok.
- Canonical daily: 71/71 ok.
- Canonical 15m: 71/71 ok.
- Corporate actions: 71/71 ok.

Exact keys:

- `universe_id`
- `theme`
- `symbol`
- `role`
- `theme_universe_asof_ts`
- `tradable_after_ts`

Leakage audit:

- Entry is the next daily adjusted close after the minimum Task836 adapter bundle as-of timestamp.
- Exit is the latest certified daily bar.
- Symbols come only from `theme_universe_10x7.csv`.
- No future return, label, score, rank, or price proximity fallback is used.
- QQQ is included only as benchmark data, not as a theme-universe member.

Replay result:

| Metric | Result |
| --- | ---: |
| Theme universe final capital | `$944.73` |
| Theme universe return | `-5.527092%` |
| QQQ same-window final capital | `$966.74` |
| QQQ same-window return | `-3.326357%` |
| QQQ long-term final capital | `$2,406.19` |
| QQQ long-term return | `140.619018%` |

By-theme diagnostic ranking:

| Theme | Return |
| --- | ---: |
| biotech_glp1_healthcare | `4.948885%` |
| industrial_automation_robotics | `1.870377%` |
| aerospace_defense_space | `-3.828122%` |
| power_grid_electrification | `-4.373982%` |
| ai_semiconductors | `-5.032516%` |
| crypto_fintech | `-5.203962%` |
| ev_autonomy_mobility | `-6.907768%` |
| cybersecurity | `-10.522410%` |
| cloud_ai_platforms | `-12.287764%` |
| data_devops_software | `-13.933664%` |

Remaining blockers:

- This is not split/OOS validation.
- Costs and slippage are not applied.
- Equal-weight theme-universe replay is a diagnostic baseline, not a final strategy.
- Candidate-bundle-to-theme mapping remains a separate decision.
- Result does not change strategy acceptance, deployment readiness, or real-capital permission.

## No-Background Decision-Maker Report

The correct 10-theme, 7-symbol universe was used this time. All 70 symbols were acquired and replayed, with QQQ added only as the benchmark. The diagnostic theme basket lost money and underperformed QQQ over the same short replay window. This says the data and replay path now works at the intended universe size, but the policy is not good enough.

## Artifact Manifest

- Script: `scripts/trader_brain_880_theme_universe_10x7_replay.py`.
- Validator: `scripts/trader_brain_880_theme_universe_10x7_validate.py`.
- Raw downloads: `data/raw/yfinance/task_880_theme_universe_10x7/`.
- Data artifacts: `data/artifacts/task_880_theme_universe_10x7_replay/`.
- Universe contract: `data/artifacts/task_880_theme_universe_10x7_replay/theme_universe_10x7_contract.csv`.
- Daily audit: `data/artifacts/task_880_theme_universe_10x7_replay/full_data_acquisition_audit.csv`.
- Intraday audit: `data/artifacts/task_880_theme_universe_10x7_replay/intraday_acquisition_audit.csv`.
- Trade specs: `data/artifacts/task_880_theme_universe_10x7_replay/controlled_trade_specs.csv`.
- Replay trades: `data/artifacts/task_880_theme_universe_10x7_replay/controlled_replay_trades.csv`.
- Replay summary: `data/artifacts/task_880_theme_universe_10x7_replay/controlled_replay_summary.csv`.
- By-theme summary: `data/artifacts/task_880_theme_universe_10x7_replay/controlled_replay_by_theme.csv`.
- Validation command: `python scripts/trader_brain_880_theme_universe_10x7_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
