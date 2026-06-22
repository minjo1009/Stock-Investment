# Task1101-1110 Winner Concentration Audit

## Decision Summary

- Verdict: `winner_basket_concentration_confirmed`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Audited variant: `sec_slot3_theme_cap1_v1`.
- Key finding: 6 of 70 universe symbols were selected, and top 3 symbols generated 96.275391% of total PnL.
- What changed: Task1081-1100's best SEC as-of source replay was decomposed by symbol concentration, score stability, and universe PIT readiness.
- Next action: repair PIT universe evidence and add dynamic non-SEC event timing before treating the result as strategy skill.

## Quant Expert Report

### Data source and source readiness

- Inputs:
  - `data/artifacts/task_1081_1100_sec_asof_source_replay/task1083_sec_asof_selection_ledger.csv`
  - `data/artifacts/task_1081_1100_sec_asof_source_replay/task1084_sec_asof_replay_trades.csv`
  - `data/artifacts/task_1081_1100_sec_asof_source_replay/task1082_sec_asof_adapter_feature_panel.csv`
  - `data/raw/theme_universe_10x7.csv`
- The audited result remains diagnostic-only.

### Exact join keys

- `policy_variant_id=sec_slot3_theme_cap1_v1`.
- `symbol` links selected trades to PnL contribution and score stability.
- `trade_spec_id` links selection ledger to replay trades.

### Leakage audit

- This audit did not create new trades.
- It evaluates already generated Task1081-1100 diagnostic replay outputs.
- Universe PIT audit found no point-in-time columns in `theme_universe_10x7.csv`.

### Concentration metrics

| Metric | Value |
| --- | ---: |
| Closed trades | 135 |
| Selected symbols | 6 |
| Universe symbols | 70 |
| Selected symbol share | 8.571429% |
| Top 3 symbols | ASTS;VRT;ARM |
| Top 3 PnL share | 96.275391% |
| Top 5 symbols | ASTS;VRT;ARM;AVGO;PH |
| Top 3 spent share | 84.349912% |
| PnL HHI | 0.332847 |
| Spent HHI | 0.248111 |

### Symbol contribution

| Symbol | Trades | PnL share % | Return on spent % |
| --- | ---: | ---: | ---: |
| ASTS | 23 | 43.265138 | 13.216106 |
| VRT | 33 | 31.804900 | 8.673606 |
| ARM | 15 | 21.205354 | 6.875028 |
| AVGO | 30 | 2.471573 | 2.817437 |
| PH | 27 | 1.445454 | 1.970352 |
| BA | 7 | -0.192418 | -0.772270 |

### Failure decomposition

- The high return did not come from broad market-wide intelligence.
- It came from repeated reinvestment into a narrow set of winners.
- All 6 selected symbols had a static score when selected.
- 3 selected symbols had static score across the full feature period.
- The universe is static and lacks PIT membership columns, so universe hindsight bias is still open.

### Cost/slippage stress

- No new cost/slippage stress was run.
- This audit only decomposes Task1081-1100 replay output.

### Remaining blockers

- PIT universe reconstruction.
- Dynamic non-SEC source timing.
- Re-entry justification beyond static SEC score.
- Winner concentration guard or explicit structural-winner hold model.

## No-Background Decision-Maker Report

What happened:

We checked whether the very strong result was broad trading skill or narrow winner concentration.

Why it matters:

The strong result is real inside the current diagnostic replay, but it is mostly explained by repeated exposure to ASTS, VRT, and ARM.

Whether this changes capital/deployment readiness:

No. Strategy remains `NOT_ACCEPTED`. Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`. Real capital remains `FORBIDDEN`.

Plain-language next step:

Do not celebrate the 66.93% CAGR as strategy proof. First rebuild point-in-time universe membership and add dynamic event timing.

## Artifact Manifest

### Outputs

- `data/artifacts/task_1101_1110_winner_concentration_audit/task1101_winner_concentration_summary.csv`
- `data/artifacts/task_1101_1110_winner_concentration_audit/task1102_symbol_pnl_contribution.csv`
- `data/artifacts/task_1101_1110_winner_concentration_audit/task1103_selected_score_stability.csv`
- `data/artifacts/task_1101_1110_winner_concentration_audit/task1104_full_feature_score_stability.csv`
- `data/artifacts/task_1101_1110_winner_concentration_audit/task1105_universe_pit_audit.csv`
- `data/artifacts/task_1101_1110_winner_concentration_audit/task1110_winner_concentration_closeout.csv`
- `data/artifacts/task_1101_1110_winner_concentration_audit/artifact_manifest.csv`

### Validation Commands

```text
python scripts/trader_brain_1101_1110_winner_concentration_audit.py
python scripts/task_artifact_manifest.py --task-dir data/artifacts/task_1101_1110_winner_concentration_audit
python scripts/trader_brain_1101_1110_winner_concentration_audit_validate.py
python -m unittest tests.test_trader_brain_1101_1110_winner_concentration_audit
python scripts/trader_brain_1081_1100_sec_asof_source_replay_validate.py
python scripts/task_registry_validate.py --registry tasks/task_registry.csv --root .
```

Validation authority: `DIAGNOSTIC_WINNER_CONCENTRATION_AUDIT_ONLY`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
