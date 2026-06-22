# Task3331-Task3340 Full Source Default Acceleration

## Decision Summary

- Verdict: `full_source_provider_endpoint_groupby_default_promoted_to_auto_polars`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: full-source normalized panel rows 4,588,915; groupby result rows 4; AUTO selected Polars; runtime 1439.3681 ms vs pandas 22746.9235 ms; speedup 15.803409x; fixed pandas reference hash matched.
- What changed: the next 500k+ source-panel strict-gate aggregate by `provider,endpoint_name` is validated as an AUTO default accelerator candidate, and strict-gate CSV aggregate helpers now read only the group columns plus `strict_gate_pass`.
- Next action: promote only one additional source/backtest panel at a time when it clears pandas parity, reference hash equality, and minimum 2x speedup.

## Quant Expert Report

### Data Source And Source Readiness

No new raw source was acquired.

Existing local artifact used:

- `data/artifacts/task_2251_2280_plus8000_full_source_acquisition/task2253_normalized_sources.csv`

This task does not claim source coverage is complete.

### Exact Join Keys

No inferred matching was used.

Promoted groupby:

- Panel: Task2251 full-source normalized sources
- Keys: `provider`, `endpoint_name`
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

Before this task, the strict-gate CSV aggregate helpers read full CSV payloads even when only group columns and `strict_gate_pass` were required.

After this task, the same helper path reads only the columns required for the aggregate. The full-source `provider,endpoint_name` aggregate uses `BackendAccelerationEngine.AUTO`, selects Polars, passes pandas parity, writes a pandas reference output, and matches the fixed reference hash.

### Cost/Slippage Stress

Not applicable. No trading-cost model changed.

### Remaining Blockers

- This default promotion applies only to the named full-source normalized aggregate.
- It does not prove catalog speed improvement.
- It does not change live-source readiness or strategy acceptance.
- Future default promotions need their own real-panel speedup and parity artifacts.

## No-Background Decision-Maker Report

Conclusion first: a second large source-panel groupby now clears the default acceleration gate.

The selected panel is the 4,588,915-row full-source normalized source panel from Task2251.

AUTO chose Polars, matched pandas output hash exactly, matched the fixed reference hash, and ran 15.803409x faster in the validator.

This is backend acceleration only. It does not approve trading, deployment, paper orders, live orders, or real capital.

## Artifact Manifest

- Inputs:
  - `data/artifacts/task_2251_2280_plus8000_full_source_acquisition/task2253_normalized_sources.csv`
  - `src/infra/external_tools.py`
- Outputs:
  - `data/artifacts/task_3331_3340_full_source_default_acceleration/benchmark_result.csv`
  - `data/artifacts/task_3331_3340_full_source_default_acceleration/acceptance_checks.csv`
  - `data/artifacts/task_3331_3340_full_source_default_acceleration/decision.csv`
  - `data/artifacts/task_3331_3340_full_source_default_acceleration/default_outputs/full_source_provider_endpoint_auto_default.csv`
  - `data/artifacts/task_3331_3340_full_source_default_acceleration/pandas_reference/full_source_provider_endpoint_pandas_reference.csv`
  - `docs/reports/task_3331_3340_full_source_default_acceleration/task_3331_3340_full_source_default_acceleration.md`
  - `docs/reports/task_3331_3340_full_source_default_acceleration/task_3340_decision.csv`
- Row counts:
  - Source rows: 4,588,915
  - Result rows: 4
- Source hashes:
  - AUTO output hash: `4bb6ebb8838f1e3ad2e07ec3edb83a5ce507f012e646fa0f036559f6d317f2a1`
  - Pandas reference hash: `4bb6ebb8838f1e3ad2e07ec3edb83a5ce507f012e646fa0f036559f6d317f2a1`
- Validation commands:
  - `python scripts/trader_brain_3331_3340_full_source_default_acceleration_validate.py`
  - `python -m unittest tests.test_backend_accelerators`
  - `python scripts/task_registry_validate.py`

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
