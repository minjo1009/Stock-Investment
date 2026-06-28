# L2 Code Complexity Audit

## Decision Summary

- Verdict: staged extraction is required; no large runner rewrite was performed in this task.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- What changed: a new `src/l2` canonical contract, builders, store, and validators were added so future runner changes can call L2 instead of embedding L2 semantics in runtime loops.
- Next action: wire runtime acquisition and registered loops to write canonical L2 batches after L1 receipt/freshness evidence is available.

## Quant Expert Report

### Local File Size Audit

| File | Local line count | Local nonblank line count | Responsibility observed |
|---|---:|---:|---|
| `tools/db/run_source_acquisition_once.py` | 37 | 37 | L0 source acquisition runner wrapper. |
| `tools/db/run_registered_loop_once.py` | 4 | 4 | Registered loop wrapper. |
| `src/app/task_089_market_data_signal_refresh.py` | 882 | 882 | Market ticks/bars, indicator snapshots, runtime candidate-local fields, and reports. |
| `src/app/task_584_runtime_strategy_decision_gate.py` | 475 | 475 | Runtime decision table, candidate selection, no-trade decomposition, and task report. |
| `src/backtest/pragmatic_economic_meaning_layer.py` | missing | missing | Mentioned in attachment but absent in this local workspace. |
| `src/backtest/build_task742_pragmatic_economic_meaning_layer.py` | missing | missing | Mentioned in attachment but absent in this local workspace. |

### Extraction Plan

- Move canonical primitive contracts to `src/l2/contracts.py`.
- Keep runtime contexts and allowed status vocabulary in `src/l2/runtime_context.py` and `src/l2/freshness.py`.
- Move source-local market bar primitive construction to `src/l2/builders/market_bar_primitives.py`.
- Move source-local indicator primitive construction to `src/l2/builders/indicator_primitives.py`.
- Add source family placeholders for news, SEC, macro, and microstructure without enabling their feature builders.
- Keep existing `task_089` and `task_584` behavior unchanged until a separate wiring task can add L1 receipt ids to the runner path.

### Preserved Behavior

- Existing runner behavior remains diagnostic-only.
- Existing runtime decision logic is not promoted to L2.
- L2 indicator primitives strip score, action, side, entry, selected-for-portfolio, and candidate-rank fields from primitive payloads.
- No broker mutation, paper order, live order, BUY/SELL signal, or deployment claim was introduced.

## No-Background Decision-Maker Report

L2 now has a formal place in the codebase. The current trading system is still not accepted and not deployment-ready. This work makes future evidence safer to interpret by forcing every primitive to say where it came from, when it was available, whether it was fresh, and whether it is historical or live diagnostic evidence.

## Artifact Manifest

See `artifact_manifest.csv`.
