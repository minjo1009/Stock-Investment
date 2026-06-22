# Task1081-1100 SEC As-Of Source Replay

## Decision Summary

- Verdict: `sec_companyfacts_asof_source_replay_complete_diagnostic_only`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: the golden overlay was replaced with real SEC companyfacts source-time features for the 3,689 ready trade specs.
- Source-time result: 3,689 / 3,689 rows passed SEC `available_to_brain_ts <= decision_asof_ts`.
- Best return result: `sec_slot3_theme_cap1_v1`, 1000 -> 14620.85, CAGR 66.934114%, MDD -34.456351%.
- Best balanced CAGR>=30 result: `sec_slot8_theme_cap3_v1`, 1000 -> 5795.68, CAGR 39.886597%, MDD -32.123917%.
- Important limit: SEC source-time gap is closed for this scope, but `non_sec_source_gap=1`.
- Next action: add non-SEC as-of sources such as transcripts, press releases, macro/policy releases, and theme news before acceptance claims.

## Quant Expert Report

### Data source and source readiness

- Source scope: `sec_companyfacts_only`.
- Input L1 source: `data/artifacts/task_907_916_sec_l1_l5_pipeline/task908_l1_sec_companyfacts_evidence.csv`.
- Input L3 source: `data/artifacts/task_907_916_sec_l1_l5_pipeline/task913_l3_relation_snapshots.csv`.
- Input L4 source: `data/artifacts/task_907_916_sec_l1_l5_pipeline/task914_l4_candidate_bundles.csv`.
- Trade specs: `data/artifacts/task_921_930_controlled_adapter_gate/task929_controlled_trade_specs.csv`.
- SEC L1 rows: 618.
- SEC L3 snapshot keys: 4,041.
- Adapter feature rows: 3,689.

### Exact join keys

- `decision_asof_ts + symbol + theme` links SEC relation snapshots and candidate bundles to ready trade specs.
- `trade_spec_id` links source-time audit, adapter feature panel, selection ledger, trades, equity curves, and replay summaries.
- SEC source-time eligibility uses `available_to_brain_ts <= decision_asof_ts`.

### Leakage audit

- Future SEC rows used: 0.
- Source-time pass rows: 3,689 / 3,689.
- Forbidden inputs remain blocked: `future_return`, `realized_return`, `pnl`, `post_entry_price_change`, `outcome_rank`, `exit_price`.
- Post-replay attribution is diagnostics-only and never selection input.

### Split/OOS metrics

Best high-return variant:

| Variant | Final equity | CAGR % | MDD % | Beats QQQ | CAGR >= 30 | MDD >= -30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| sec_slot3_theme_cap1_v1 | 14620.85 | 66.934114 | -34.456351 | 1 | 1 | 0 |

Best balanced CAGR>=30 variant:

| Variant | Final equity | CAGR % | MDD % | Beats QQQ | CAGR >= 30 | MDD >= -30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| sec_slot8_theme_cap3_v1 | 5795.68 | 39.886597 | -32.123917 | 1 | 1 | 0 |

### Failure decomposition

- SEC-only source-time evidence preserved high return potential.
- SEC-only evidence did not keep MDD inside the -30% target.
- Drawdown pause variants reduced drawdown but killed return, so they are not the current leader.
- The missing layer is likely non-SEC event evidence and regime/price-context timing, not SEC source-time itself.

### Cost/slippage stress

- Reused Task941 assumptions: 5 bps entry slippage, 5 bps exit slippage, 10 bps round trip cost.
- No real broker execution or real capital path was touched.

### Remaining blockers

- Non-SEC as-of source families remain open: earnings transcripts, press releases, macro/policy releases, theme news, and price reaction context.
- Strategy remains diagnostic-only despite high CAGR.

## No-Background Decision-Maker Report

What happened:

We replaced the fake/golden overlay with real SEC as-of source features. The system only used SEC facts available before each decision timestamp.

Why it matters:

The strong return did not disappear. That is a good sign. But MDD is still too high, so the source-time question is partly solved, not fully solved.

Whether this changes capital/deployment readiness:

No. Strategy remains `NOT_ACCEPTED`. Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`. Real capital remains `FORBIDDEN`.

Plain-language next step:

Keep SEC as-of source extraction, then add non-SEC as-of sources so the brain can avoid bad drawdown periods without losing the structural winners.

## Artifact Manifest

### Outputs

- `data/artifacts/task_1081_1100_sec_asof_source_replay/task1081_sec_source_time_audit.csv`
- `data/artifacts/task_1081_1100_sec_asof_source_replay/task1082_sec_asof_adapter_feature_panel.csv`
- `data/artifacts/task_1081_1100_sec_asof_source_replay/task1083_sec_asof_selection_ledger.csv`
- `data/artifacts/task_1081_1100_sec_asof_source_replay/task1084_sec_asof_replay_trades.csv`
- `data/artifacts/task_1081_1100_sec_asof_source_replay/task1085_sec_asof_equity_curves.csv`
- `data/artifacts/task_1081_1100_sec_asof_source_replay/task1086_sec_asof_backtest_summary.csv`
- `data/artifacts/task_1081_1100_sec_asof_source_replay/task1087_sec_asof_attribution.csv`
- `data/artifacts/task_1081_1100_sec_asof_source_replay/task1100_sec_asof_source_replay_closeout.csv`
- `data/artifacts/task_1081_1100_sec_asof_source_replay/artifact_manifest.csv`

### Validation Commands

```text
python scripts/trader_brain_1081_1100_sec_asof_source_replay.py
python scripts/task_artifact_manifest.py --task-dir data/artifacts/task_1081_1100_sec_asof_source_replay
python scripts/trader_brain_1081_1100_sec_asof_source_replay_validate.py
python -m unittest tests.test_trader_brain_1081_1100_sec_asof_source_replay
python scripts/trader_brain_1041_1080_golden_extractor_replay_validate.py
python scripts/task_registry_validate.py --registry tasks/task_registry.csv --root .
```

Validation authority: `DIAGNOSTIC_SEC_ASOF_SOURCE_REPLAY_ONLY`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
