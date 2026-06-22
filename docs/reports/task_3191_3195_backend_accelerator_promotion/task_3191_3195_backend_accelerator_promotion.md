# Task3191-Task3195 Backend Accelerator Promotion

## Decision Summary

- Verdict: Polars and DuckDB were promoted from diagnostic-only helpers into a core backend acceleration layer.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: synthetic fixture rows 4096, Polars correctness parity 1, DuckDB correctness parity 1, auto-selected accelerator 1.
- What changed: added `src/infra/accelerators.py`, package exports, package-health tests, and validator artifacts.
- Next action: migrate one real pandas bottleneck behind `strict_gate_aggregate_accelerated()` only after row/key/value parity is locked for that path.

## Quant Expert Report

### Data Source And Source Readiness

No market, broker, SEC, news, or source panel data was acquired.

Validation used a synthetic strict-gate fixture generated under:

`data/artifacts/task_3191_3195_backend_accelerator_promotion/accelerator_strict_gate_fixture.csv`

### Exact Join Keys

No symbol/date/price/time matching was performed.

The synthetic aggregate groups by:

- `symbol`
- `event_family`

### Leakage Audit

The accelerator layer computes equivalent aggregate results only.

It does not:

- rank trades
- size positions
- run replay
- create paper order intent
- create live order intent
- mutate broker or runtime state
- change acceptance status

### Split/OOS Metrics

Not applicable. No replay, backtest, split/OOS, PnL, MDD, cost, or slippage result was produced.

### Failure Decomposition

Before this task, Polars and DuckDB lived as optional diagnostic helpers under `src/infra/external_tools.py`.

This task adds a core-facing wrapper:

`strict_gate_aggregate_accelerated(panel, group_cols, engine="auto")`

Selection order:

```text
Polars -> DuckDB -> pandas fallback
```

Non-pandas engines must match pandas row counts, null counts, strict-gate totals, and aggregate checksum before they are accepted.

### Cost/Slippage Stress

Not applicable. No trading cost model changed.

### Remaining Blockers

- This is acceleration infrastructure only.
- No existing strategy path has been migrated yet.
- Each future migration must prove pandas parity on the real target path before becoming the default.

## No-Background Decision-Maker Report

Polars and DuckDB are now allowed as core backend acceleration engines.

They are not allowed to change trading judgment.

The engine can use them to compute the same result faster, then fall back to pandas if dependencies or parity fail.

This does not make the strategy accepted or deployable.

## Artifact Manifest

See `artifact_manifest.csv`.

