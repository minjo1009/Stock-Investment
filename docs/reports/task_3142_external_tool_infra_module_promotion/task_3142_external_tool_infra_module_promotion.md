# Task3142 External Tool Infra Module Promotion

## Decision Summary

- Verdict: `external_tool_infra_module_promotion_completed_diagnostic_only`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: promoted `Pandera`, Polars, and DuckDB helper behavior into `src/infra/external_tools.py` as diagnostic-only optional infrastructure helpers.
- What did not change: no root dependency manifest, source acquisition, replay, selector change, sizing change, paper order, live order, acceptance, or deployment state changed.
- Key metrics:
  - Module contracts: 6.
  - Module replay rows: 4.
  - Module candidates: 4.
  - Reference matches: 4.
- Next action: harden the module in 2-3 more passes: typed result contracts, failure-mode tests, then limited script migration.

## Quant Expert Report

### Module Contracts

| module_path | tool_name | dependency_status | dependency_mode | allowed_layers | forbidden_layers | trading_decision_allowed |
| --- | --- | --- | --- | --- | --- | --- |
| src/infra/external_tools.py | pandera | dependency_missing | optional_import_or_task3126_venv | data_validation|resolver_qa | selector|sizing|replay|paper_order|live_order|acceptance|deployment | 0 |
| src/infra/external_tools.py | polars | available | optional_import | local_artifact_query|audit_benchmark | selector|sizing|replay|paper_order|live_order|acceptance|deployment | 0 |
| src/infra/external_tools.py | duckdb | available | optional_import | local_artifact_query|audit_benchmark | selector|sizing|replay|paper_order|live_order|acceptance|deployment | 0 |
| src/infra/external_tools.py | edgartools | dependency_missing | deferred | none_until_offline_local_parse_is_proven | selector|sizing|replay|paper_order|live_order|acceptance|deployment | 0 |
| src/infra/external_tools.py | dlt | dependency_missing | deferred | none_until_source_receipt_task | selector|sizing|replay|paper_order|live_order|acceptance|deployment | 0 |
| src/infra/external_tools.py | github_mcp_read_only | deferred_connector_not_invoked | deferred_connector_not_invoked | none_until_read_only_monitoring_task | selector|sizing|replay|paper_order|live_order|acceptance|deployment | 0 |

### Module Replay Results

| module_function | tool_name | source_wrapper_id | source_row_count | result_row_count | reference_match | module_candidate |
| --- | --- | --- | --- | --- | --- | --- |
| validate_sec_panel_schema_with_pandera_venv | pandera | WRAP3127-PANDERA-SEC-SCHEMA |  |  | 1 | 1 |
| strict_gate_aggregate_accelerated | polars | WRAP3127-POLARS-SEC-AGG | 138049 | 1294 | 1 | 1 |
| strict_gate_aggregate_accelerated | polars | WRAP3127-POLARS-LIQUIDITY-AGG | 768841 | 38 | 1 | 1 |
| strict_gate_aggregate_accelerated | duckdb | WRAP3127-DUCKDB-LIQUIDITY-AGG | 768841 | 38 | 1 | 1 |

### Reference Diff

| module_function | source_wrapper_id | diff_status | reference_match |
| --- | --- | --- | --- |
| validate_sec_panel_schema_with_pandera_venv | WRAP3127-PANDERA-SEC-SCHEMA | matched | 1 |
| strict_gate_aggregate_accelerated | WRAP3127-POLARS-SEC-AGG | matched | 1 |
| strict_gate_aggregate_accelerated | WRAP3127-POLARS-LIQUIDITY-AGG | matched | 1 |
| strict_gate_aggregate_accelerated | WRAP3127-DUCKDB-LIQUIDITY-AGG | matched | 1 |

### Module Decision Matrix

| tool_name | module_decision | candidate_function_count | mismatch_count | allowed_next_layer |
| --- | --- | --- | --- | --- |
| pandera | promote_common_infra_candidate | 1 | 0 | src_infra_external_tools_diagnostic_only |
| polars | promote_common_infra_candidate | 2 | 0 | src_infra_external_tools_diagnostic_only |
| duckdb | promote_common_infra_candidate | 1 | 0 | src_infra_external_tools_diagnostic_only |
| edgartools | defer | 0 | 0 | none |
| dlt | defer | 0 | 0 | none |
| github_mcp_read_only | defer | 0 | 0 | none |

### Acceptance Checks

| check_name | pass | detail |
| --- | --- | --- |
| status_unchanged | 1 | Strategy/deployment/real-capital statuses remain unchanged. |
| no_orders | 1 | No paper or live orders are created. |
| no_replay_or_source_acquisition | 1 | No replay or source acquisition is performed. |
| root_dependency_manifest_absent | 1 | No root Python dependency manifest was created. |
| module_contracts_present | 1 | All module contracts are recorded. |
| module_reference_replay_match | 1 | Module outputs match Task3141 references. |
| module_candidates_present | 1 | Pandera, Polars, and DuckDB module candidates exist. |
| deferred_tools_not_promoted | 1 | Deferred tools remain deferred. |
| trading_decision_disabled | 1 | No tool is allowed to make trading decisions. |

No output from this task is connected to selector, sizing, replay, paper runtime, live orders, strategy acceptance, or deployment readiness.

## No-Background Decision-Maker Report

Conclusion first: the useful external-tool infra helpers are now in a common module.

`Pandera`, Polars, and DuckDB are available only as diagnostic infrastructure helpers. They validate panels and query local artifacts. They do not rank trades, size positions, trigger replay, or create orders.

This does not change strategy acceptance. This does not change deployment readiness. This does not permit real capital.

## Artifact Manifest

- Inputs:
  - `C:/Users/minjo/OneDrive/바탕 화면/외국주식 퀀트트레이딩/data/artifacts/task_3141_external_tool_helper_contract/helper_replay_result.csv`
  - `C:/Users/minjo/OneDrive/바탕 화면/외국주식 퀀트트레이딩/data/artifacts/task_2541_2560_sec_financing_dilution_acquisition/task2545_normalized_sec_financing_dilution_packets.csv`
  - `C:/Users/minjo/OneDrive/바탕 화면/외국주식 퀀트트레이딩/data/artifacts/task_2561_2580_liquidity_rates_regime_acquisition/task2565_normalized_liquidity_rates_packets.csv`
- Outputs:
  - `src/infra/external_tools.py`
  - `docs/reports/task_3142_external_tool_infra_module_promotion/task_3142_external_tool_infra_module_promotion.md`
  - `docs/reports/task_3142_external_tool_infra_module_promotion/task_3142_decision.csv`
  - `data/artifacts/task_3142_external_tool_infra_module_promotion/`
- Row counts:
  - Module contracts: 6
  - Module replay rows: 4
  - Module diff rows: 4
  - Module decision rows: 6
- Validation commands:
  - `python scripts/trader_brain_3142_external_tool_infra_module_promotion_validate.py`
  - `python scripts/task_registry_validate.py`
- Source hashes:
  - Task3141 helper replay: `448ff5c59d6888a57dd0f54180259775f3dd5c00fc4caf6181322dd916328deb`
  - SEC panel: `1cc0ba60ca78ec615ff3b1ce57af0d43ac04f3ba548e4da8ec9d7bc0712e07e2`
  - Liquidity/rates panel: `59e8ee997132715335e02e1ba71a932598bba026719905851c1c09d25659f297`

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
