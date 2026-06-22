# Task3221-Task3280 Backend Acceleration Program

## Decision Summary

- Verdict: `backend_acceleration_program_structure_and_parity_completed`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: generic grouped accelerator API added, 3 catalog groupby helpers migrated behind the API, 1 backtest core grouped metric migrated behind the API, and Task3142/Task3143 source-panel aggregate paths routed through `strict_gate_aggregate_accelerated()` with current-code regeneration evidence.
- What changed: `src/infra/accelerators.py` now exposes `grouped_numeric_aggregate_accelerated()` with count-non-null, mean, and sum support; catalog/backtest/source-panel lanes use core accelerator wrappers instead of direct pandas or low-level Polars/DuckDB groupby calls.
- Next action: profile a larger real source-panel or backtest artifact and add only the next high-confidence groupby migration after pandas parity is available.

## Quant Expert Report

### Data Source And Source Readiness

No new raw source was acquired.

Existing local artifacts reused:

- Task3142 module replay artifacts.
- Task3143 typed parity artifacts.
- Task3196-Task3200 real accelerator migration artifacts.

This task does not claim source coverage is complete.

### Exact Join Keys

No symbol/date/price/time fallback matching was performed.

Accelerated grouping keys:

- Catalog lane: configured catalog group columns and derived matrix/composite keys.
- Backtest core lane: caller-provided `grouped_lifecycle_quality()` keys with `dropna=False`.
- Source-panel lane: SEC `symbol,event_family` and liquidity/rates `provider,series_id`.

### Leakage Audit

The accelerated paths compute aggregates only.

They do not:

- assign labels
- rank trades
- size positions
- run replay
- create paper or live order intent
- mutate runtime or broker state
- change acceptance or deployment status

### Split/OOS Metrics

Not applicable. No replay, backtest run, split/OOS, PnL, MDD, cost, or slippage metric was produced.

### Failure Decomposition

Before this task, grouped catalog/backtest metrics and Task3142/Task3143 source-panel checks had separate pandas or low-level helper paths.

After this task:

- grouped numeric aggregations share one backend API
- strict-gate source panel aggregations route through the core strict-gate accelerator
- Polars/DuckDB results are accepted only when the relevant validator proves pandas parity
- catalog full-build validation remains slow, so focused function-level parity is the active validator for this lane

### Cost/Slippage Stress

Not applicable. No trading-cost model changed.

### Remaining Blockers

- This is backend acceleration and operating discipline only.
- It does not make any strategy accepted or deployment-ready.
- Catalog runtime currently selects the pandas engine through the accelerator API because repeated in-memory Polars conversion was slower for full catalog tests.
- Future performance work should benchmark larger real panels before changing default engine selection for catalog builds.

## No-Background Decision-Maker Report

Conclusion first: the backend now has a reusable grouped aggregation accelerator.

The project can keep moving pandas groupby bottlenecks behind one governed API instead of rewriting every script separately.

This improves the operating loop. It does not approve trading, deployment, paper orders, live orders, or real capital.

The next practical step is one more real large-panel migration with a timing comparison and pandas parity. Catalog groupby now has governed API routing, but its default engine remains pandas because full catalog validation showed repeated in-memory conversion is not yet a proven speed win.

## Artifact Manifest

- Inputs:
  - `src/infra/accelerators.py`
  - `scripts/build_trader_terminal_catalog.py`
  - `src/backtest/core/metrics.py`
  - `scripts/trader_brain_3142_external_tool_infra_module_promotion.py`
  - `scripts/trader_brain_3143_external_tool_typed_contract.py`
- Outputs:
  - `data/artifacts/task_3221_3280_backend_acceleration_program/candidate_inventory.csv`
  - `data/artifacts/task_3221_3280_backend_acceleration_program/catalog_acceleration_result.csv`
  - `data/artifacts/task_3221_3280_backend_acceleration_program/backtest_core_metrics_acceleration_result.csv`
  - `data/artifacts/task_3221_3280_backend_acceleration_program/source_panel_acceleration_result.csv`
  - `data/artifacts/task_3221_3280_backend_acceleration_program/source_panel_regeneration_commands.csv`
  - `data/artifacts/task_3221_3280_backend_acceleration_program/program_validation_commands.csv`
  - `data/artifacts/task_3221_3280_backend_acceleration_program/artifact_manifest.csv`
  - `docs/reports/task_3221_3280_backend_acceleration_program/task_3221_3280_backend_acceleration_program.md`
  - `docs/reports/task_3221_3280_backend_acceleration_program/task_3280_decision.csv`
- Validation commands:
  - `python -m unittest tests.test_backend_accelerators`
  - `python -m unittest tests.test_backtest_core_metrics_accelerated`
  - `python scripts/trader_brain_3231_3245_catalog_acceleration_validate.py`
  - `python scripts/trader_brain_3246_3260_backtest_core_metrics_acceleration_validate.py`
  - `python scripts/trader_brain_3261_3270_source_panel_acceleration_validate.py`
  - `python scripts/trader_brain_3221_3280_backend_acceleration_program_validate.py`
  - `python scripts/task_registry_validate.py`
  - `python scripts/operating_closeout_validate.py`
  - `python scripts/governance_completion_audit.py`

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
