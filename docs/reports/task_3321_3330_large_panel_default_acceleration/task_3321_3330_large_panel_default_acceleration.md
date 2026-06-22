# Task3321-Task3330 Large Panel Default Acceleration

## Decision Summary

- Verdict: `large_panel_liquidity_groupby_default_promoted_to_auto_polars`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: liquidity/rates panel rows 768,841; groupby result rows 38; AUTO selected Polars; runtime 228.3562 ms vs pandas 4491.6106 ms; speedup 19.669317x; Task3127 reference hash matched.
- What changed: the real liquidity/rates `provider,series_id` strict-gate aggregate path now uses `BackendAccelerationEngine.AUTO` in Task3142/Task3143 source-panel scripts, letting the core backend accelerator choose Polars by default after pandas parity.
- Next action: profile the next large-panel groupby only if it has a pandas parity validator and a minimum 2x speedup threshold.

## Quant Expert Report

### Data Source And Source Readiness

No new raw source was acquired.

Existing local artifact used:

- `data/artifacts/task_2561_2580_liquidity_rates_regime_acquisition/task2565_normalized_liquidity_rates_packets.csv`

This task does not claim source coverage is complete.

### Exact Join Keys

No inferred matching was used.

Promoted groupby:

- Panel: liquidity/rates
- Keys: `provider`, `series_id`
- Aggregate: strict-gate packet count and pass count

### Leakage Audit

The promoted path aggregates existing strict-gate rows only.

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

Before this task, the liquidity/rates source-panel replay used an explicit Polars request in Task3142/Task3143.

After this task, that real large-panel groupby uses `BackendAccelerationEngine.AUTO`. The core accelerator selects Polars by default, verifies pandas parity, preserves the Task3127 reference hash, and records the measured speedup.

### Cost/Slippage Stress

Not applicable. No trading-cost model changed.

### Remaining Blockers

- This default promotion applies only to the named liquidity/rates groupby.
- It does not prove catalog speed improvement.
- Future default promotions need their own real-panel speedup and parity artifacts.

## No-Background Decision-Maker Report

Conclusion first: one real large-panel groupby now defaults to the faster accelerator path.

The selected path is the 768,841-row liquidity/rates aggregate by `provider,series_id`.

AUTO chose Polars, matched pandas/reference output, and ran about 19.67x faster in the validator.

This is backend acceleration only. It does not approve trading, deployment, paper orders, live orders, or real capital.

## Artifact Manifest

- Inputs:
  - `data/artifacts/task_2561_2580_liquidity_rates_regime_acquisition/task2565_normalized_liquidity_rates_packets.csv`
  - `data/artifacts/task_3127_external_tool_opt_in_wrapper_pilot/local_query_wrapper_result.csv`
  - `scripts/trader_brain_3142_external_tool_infra_module_promotion.py`
  - `scripts/trader_brain_3143_external_tool_typed_contract.py`
- Outputs:
  - `data/artifacts/task_3321_3330_large_panel_default_acceleration/benchmark_result.csv`
  - `data/artifacts/task_3321_3330_large_panel_default_acceleration/acceptance_checks.csv`
  - `data/artifacts/task_3321_3330_large_panel_default_acceleration/decision.csv`
  - `data/artifacts/task_3321_3330_large_panel_default_acceleration/default_outputs/liquidity_provider_series_auto_default.csv`
  - `docs/reports/task_3321_3330_large_panel_default_acceleration/task_3321_3330_large_panel_default_acceleration.md`
  - `docs/reports/task_3321_3330_large_panel_default_acceleration/task_3330_decision.csv`
- Validation commands:
  - `python scripts/trader_brain_3321_3330_large_panel_default_acceleration_validate.py`
  - `python scripts/trader_brain_3142_external_tool_infra_module_promotion.py`
  - `python scripts/trader_brain_3143_external_tool_typed_contract.py`
  - `python scripts/trader_brain_3142_external_tool_infra_module_promotion_validate.py`
  - `python scripts/trader_brain_3143_external_tool_typed_contract_validate.py`
  - `python scripts/trader_brain_3196_3200_real_accelerator_migration_validate.py`
  - `python scripts/task_registry_validate.py`

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
