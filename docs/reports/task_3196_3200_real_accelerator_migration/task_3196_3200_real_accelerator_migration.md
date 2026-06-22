# Task3196-Task3200 Real Accelerator Migration

## Decision Summary

- Verdict: one real local artifact aggregate path was migrated behind `strict_gate_aggregate_accelerated()`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: migrated aggregate paths 3, reference matches 3, pandas correctness parity rows 3, shared pandas baseline cache added for repeated large-panel checks.
- What changed: `scripts/trader_brain_3141_external_tool_helper_contract.py` now routes Polars/DuckDB strict-gate aggregate work through the core backend accelerator API.
- Next action: migrate the next real pandas bottleneck only after the same reference-hash and pandas-correctness checks are available.

## Quant Expert Report

### Data Source And Source Readiness

No new raw source was acquired.

Existing local artifact panels used:

- `data/artifacts/task_2541_2560_sec_financing_dilution_acquisition/task2545_normalized_sec_financing_dilution_packets.csv`
- `data/artifacts/task_2561_2580_liquidity_rates_regime_acquisition/task2565_normalized_liquidity_rates_packets.csv`

### Exact Join Keys

No symbol/date/price/time fallback matching was performed.

Aggregate keys:

- SEC panel: `symbol`, `event_family`
- Liquidity/rates panel: `provider`, `series_id`

### Leakage Audit

The migrated path aggregates `strict_gate_pass` counts only.

It does not:

- assign labels
- rank trades
- size positions
- run replay
- create paper or live order intent
- mutate runtime or broker state
- change acceptance or deployment status

### Split/OOS Metrics

Not applicable. No replay, backtest, split/OOS, PnL, MDD, cost, or slippage metric was produced.

### Failure Decomposition

Before this task, the Task3141 helper replay path called low-level pandas/Polars/DuckDB aggregate helpers directly.

After this task, the Polars/DuckDB aggregate path is routed through:

`src.infra.accelerators.strict_gate_aggregate_accelerated`

The validator checks:

- migrated script uses the core accelerator API
- direct pandas strict-gate aggregate call was removed from the migrated script
- real outputs match Task3127 reference hashes
- real outputs match pandas correctness parity
- repeated large-panel checks can reuse the same pandas baseline instead of rereading the panel for every candidate engine

### Cost/Slippage Stress

Not applicable. No trading-cost model changed.

### Remaining Blockers

- This is backend acceleration only.
- No strategy or runtime trading path has been accelerated yet.
- Future migrations need their own parity/reference checks.

## No-Background Decision-Maker Report

The first real pandas-adjacent bottleneck has moved behind the core accelerator wrapper.

This used real local artifacts, not a synthetic fixture.

The result matched old reference outputs and pandas correctness checks.

This still does not approve strategy or deployment.

## Artifact Manifest

See `artifact_manifest.csv`.
