# Task3143 External Tool Typed Contract

## Decision Summary

- Verdict: `external_tool_typed_contract_completed_diagnostic_only`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: added typed dataclass result contracts to `src/infra/external_tools.py` and verified parity with the existing dict/tuple API.
- What did not change: no source acquisition, replay, selector, sizing, paper order, live order, root dependency manifest, acceptance, or deployment state changed.
- Key metrics: typed contracts 5, parity rows 4, parity pass rows 4.

## Quant Expert Report

### Typed Contracts

| contract_name | contract_type | purpose | trading_decision_allowed |
| --- | --- | --- | --- |
| ToolStatus | dataclass | optional_dependency_status_without_import_side_effect | 0 |
| AggregateMetrics | dataclass | stable_local_artifact_query_metrics | 0 |
| AggregateResult | dataclass | metrics_plus_rows_for_audit_outputs | 0 |
| SchemaValidationResult | dataclass | stable_schema_validation_payload | 0 |
| MetricComparison | dataclass | stable_pandas_parity_comparison | 0 |

### Typed Parity

| case_id | tool_name | legacy_status | typed_status | legacy_row_count | typed_row_count | parity_pass | comparison_pass |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TYPED3143-PANDERA-SEC | pandera | schema_checks_executed | schema_checks_executed | 138049 | 138049 | 1 |  |
| TYPED3143-POLARS-SEC | polars | core_accelerator | available | 138049 | 138049 | 1 | 1 |
| TYPED3143-POLARS-LIQ | polars | core_accelerator | available | 768841 | 768841 | 1 | 1 |
| TYPED3143-DUCKDB-LIQ | duckdb | core_accelerator | available | 768841 | 768841 | 1 | 1 |

### Acceptance Checks

| check_name | pass | detail |
| --- | --- | --- |
| typed_contracts_present | 1 | All typed dataclass contracts are recorded. |
| typed_legacy_parity | 1 | Typed wrappers match legacy wrapper outputs. |
| typed_query_comparison_pass | 1 | Typed aggregate comparisons pass pandas parity. |
| trading_decision_disabled | 1 | Typed contracts do not allow trading decisions. |
| status_unchanged | 1 | Strategy/deployment/real-capital statuses remain unchanged. |

No output from this task is connected to selector, sizing, replay, paper runtime, live orders, strategy acceptance, or deployment readiness.

## No-Background Decision-Maker Report

Conclusion first: the common infra module now has stable typed result contracts.

This makes later migration safer because callers can use explicit result objects instead of loose dictionaries. The module remains diagnostic-only.

## Artifact Manifest

- Inputs:
  - `C:/Users/minjo/OneDrive/바탕 화면/외국주식 퀀트트레이딩/data/artifacts/task_2541_2560_sec_financing_dilution_acquisition/task2545_normalized_sec_financing_dilution_packets.csv`
  - `C:/Users/minjo/OneDrive/바탕 화면/외국주식 퀀트트레이딩/data/artifacts/task_2561_2580_liquidity_rates_regime_acquisition/task2565_normalized_liquidity_rates_packets.csv`
- Outputs:
  - `src/infra/external_tools.py`
  - `docs/reports/task_3143_external_tool_typed_contract/task_3143_external_tool_typed_contract.md`
  - `data/artifacts/task_3143_external_tool_typed_contract/`
- Validation commands:
  - `python scripts/trader_brain_3143_external_tool_typed_contract_validate.py`
  - `python scripts/task_registry_validate.py`
- Source hashes:
  - SEC panel: `1cc0ba60ca78ec615ff3b1ce57af0d43ac04f3ba548e4da8ec9d7bc0712e07e2`
  - Liquidity/rates panel: `59e8ee997132715335e02e1ba71a932598bba026719905851c1c09d25659f297`

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
