# Task1041-1080 Golden Extractor Replay

## Decision Summary

- Verdict: `diagnostic_golden_l1_l4_extractor_overlay_replay_complete`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Best diagnostic result: `golden_slot7_theme_cap3_v1`, 1000 -> 4732.81, CAGR 34.576215%, MDD -29.142740%, QQQ beat.
- Important limit: `historical_source_time_gap=1`. This is not acceptance evidence.
- What changed: Task1031-1040 golden logic was turned into extractor-contract rows, 200 stress inputs, a 3,689-row adapter feature panel, base slot replay, and risk-overlay replay.
- Next action: replace the golden logic overlay with real as-of external source extractors, then rerun the pre-registered policy.

## Quant Expert Report

### Data source and source readiness

- Golden input: `data/artifacts/task_1031_1040_l1_l4_golden_set`.
- Replay input: existing ready trade specs from `data/artifacts/task_921_930_controlled_adapter_gate/task929_controlled_trade_specs.csv`.
- Market data: existing Task880 canonical daily prices through the Task941 replay harness.
- Source-time status: `historical_source_time_gap=1`; the golden set is a logic contract, not a historical external source feed.

### Exact join keys

- Golden extractor: `case_id` links L1/L2/L3/L4.
- Adapter overlay: `trade_spec_id`, `adapter_input_id`, `candidate_bundle_id`, `decision_asof_ts`, `theme`, and `symbol`.
- Replay lineage: `trade_spec_id` connects feature panel, selection ledger, replay trades, and equity curves.

### Leakage audit

- Golden rows are not directly used as trade specs.
- Replay uses existing Task929 ready trade specs and existing Task941 price harness.
- Feature panel explicitly carries `historical_source_time_gap=1`.
- Forbidden inputs remain listed and blocked: `future_return`, `realized_return`, `pnl`, `post_entry_price_change`, `outcome_rank`, `exit_price`.
- Post-replay attribution is marked diagnostics-only and never selection input.

### Split/OOS metrics

Base golden replay:

| Slot cap | Final equity | CAGR % | MDD % | Beats QQQ | CAGR >= 30 | MDD >= -30 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 5532.69 | 38.651096 | -45.385923 | 1 | 1 | 0 |
| 5 | 4489.85 | 33.228160 | -44.662487 | 1 | 1 | 0 |
| 10 | 4559.25 | 33.619110 | -33.926246 | 1 | 1 | 0 |

Risk overlay replay:

| Variant | Slot cap | Max theme | Final equity | CAGR % | MDD % | Beats QQQ | CAGR >= 30 | MDD >= -30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| golden_slot7_theme_cap3_v1 | 7 | 3 | 4732.81 | 34.576215 | -29.142740 | 1 | 1 | 1 |
| golden_slot8_theme_cap4_v1 | 8 | 4 | 4391.31 | 32.664578 | -30.892465 | 1 | 1 | 0 |
| golden_slot8_theme_cap3_v1 | 8 | 3 | 4232.11 | 31.732044 | -31.253709 | 1 | 1 | 0 |
| golden_slot5_theme_cap2_v1 | 5 | 2 | 4059.85 | 30.690449 | -32.345327 | 1 | 1 | 0 |

### Failure decomposition

- Base golden replay found strong return but excessive drawdown.
- Risk overlay fixed the main concentration issue with slot 7 and max 3 open positions per theme.
- The result remains diagnostic because source-time evidence is not yet a real historical external source feed.

### Cost/slippage stress

- Reused Task941 assumptions: 5 bps entry slippage, 5 bps exit slippage, 10 bps round trip cost.
- No real broker execution or real capital path was touched.

### Remaining blockers

- Real as-of source extractors must replace the golden logic overlay.
- BLS source gap from Task1031-1040 must remain reported until repaired.
- This replay does not grant strategy acceptance, deployment readiness, or real-capital permission.

## No-Background Decision-Maker Report

What happened:

The brain was made to use the new L1-L4 golden logic and run a diagnostic backtest through the existing controlled replay harness.

Why it matters:

The prior best Task941 result was 1000 -> 2939.23, CAGR 22.87%, MDD -29.48%. The best new diagnostic risk-overlay result is 1000 -> 4732.81, CAGR 34.58%, MDD -29.14%.

Whether this changes capital/deployment readiness:

No. This is still diagnostic. Strategy remains `NOT_ACCEPTED`. Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`. Real capital remains `FORBIDDEN`.

Plain-language next step:

Keep the slot 7 / max 3 theme risk policy as the current diagnostic leader, but rebuild its input from real historical as-of sources before treating it as serious strategy evidence.

## Artifact Manifest

### Inputs

- `data/artifacts/task_1031_1040_l1_l4_golden_set`
- `data/artifacts/task_921_930_controlled_adapter_gate/task929_controlled_trade_specs.csv`
- `data/artifacts/task_941_950_slot_capped_selection_replay/task941_selection_feature_panel.csv`

### Outputs

- `data/artifacts/task_1041_1080_golden_extractor_replay/task1041_gpt_expert_plan_synthesis.csv`
- `data/artifacts/task_1041_1080_golden_extractor_replay/task1042_extractor_contract.csv`
- `data/artifacts/task_1041_1080_golden_extractor_replay/task1043_extractor_golden_match.csv`
- `data/artifacts/task_1041_1080_golden_extractor_replay/task1044_expanded_stress_input_set.csv`
- `data/artifacts/task_1041_1080_golden_extractor_replay/task1045_golden_brain_adapter_feature_panel.csv`
- `data/artifacts/task_1041_1080_golden_extractor_replay/task1050_golden_brain_backtest_summary.csv`
- `data/artifacts/task_1041_1080_golden_extractor_replay/task1055_golden_risk_overlay_summary.csv`
- `data/artifacts/task_1041_1080_golden_extractor_replay/task1080_golden_extractor_replay_closeout.csv`
- `data/artifacts/task_1041_1080_golden_extractor_replay/artifact_manifest.csv`

### Row Counts

- Expert reviewer roles: 10.
- Golden extractor cases: 20.
- Stress input rows: 200.
- Adapter feature rows: 3,689.
- Base replay variants: 3.
- Risk overlay variants: 8.

### Validation Commands

```text
python scripts/trader_brain_1041_1080_golden_extractor_replay.py
python scripts/trader_brain_1041_1080_golden_risk_overlay_replay.py
python scripts/task_artifact_manifest.py --task-dir data/artifacts/task_1041_1080_golden_extractor_replay
python scripts/trader_brain_1041_1080_golden_extractor_replay_validate.py
python -m unittest tests.test_trader_brain_1041_1080_golden_extractor_replay
python scripts/trader_brain_1031_1040_l1_l4_golden_set_validate.py
python scripts/trader_brain_941_950_slot_capped_selection_replay_validate.py
python scripts/task_registry_validate.py --registry tasks/task_registry.csv --root .
```

Validation authority: `RESEARCH_ONLY` / `DIAGNOSTIC_CONTROLLED_REPLAY_ONLY`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
