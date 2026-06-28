# L2 Runtime Context Policy

## Decision

`runtime_context` is mandatory on every L2 primitive batch and fact. It is the hard boundary that prevents historical research artifacts, backtest evidence, live intraday diagnostics, and operator replay diagnostics from being mixed.

## Context Semantics

| Context | Meaning | L3 Use |
|---|---|---|
| `HISTORICAL_RESEARCH` | Ingested research artifacts or historical panels. | Research-only L3 interpretation. |
| `BACKTEST_RESEARCH` | Backtest-generated primitive facts with controlled replay lineage. | Backtest-only L3 interpretation. |
| `LIVE_INTRADAY_DIAGNOSTIC` | Source-time-safe live/runtime diagnostic facts. | Diagnostic L3 only. No order intent. |
| `OPERATOR_REPLAY_DIAGNOSTIC` | Operator-triggered replay of source-time-safe facts. | Diagnostic replay only. |

## Gate Rules

- A primitive batch has exactly one `runtime_context`.
- A primitive fact must use the same context as its batch.
- A historical artifact batch cannot contain live/runtime evidence.
- A live diagnostic batch cannot contain `historical_artifact` rows.
- Stale, missing, blocked, or unknown freshness is a blocker, not negative evidence.
- `diagnostic_only` remains `1` until a separate governance task changes readiness.

## Non-Promotion Rules

This policy does not grant strategy acceptance, paper trading readiness, deployment readiness, broker mutation, paper order intent, live order intent, or microstructure feature-builder permission.

## Live Runtime Canonical Path

The current live runtime L2 path is:

```text
market_bars_5m / indicator_snapshots
-> l2_runtime_source_receipts
-> l2_primitive_batches
-> l2_primitive_facts
-> src.brain.l2_to_meaning_adapter.load_canonical_l2_meaning_inputs()
```

`src/app/task_089_market_data_signal_refresh.py` writes canonical live diagnostic L2 rows after it writes the runtime indicator snapshot. The runtime decision layer remains diagnostic and is not promoted to strategy acceptance by this wiring.
