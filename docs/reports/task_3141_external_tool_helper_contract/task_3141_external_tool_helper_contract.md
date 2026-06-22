# Task3141 External Tool Helper Contract

## Decision Summary

- Verdict: `external_tool_helper_contract_completed_diagnostic_only`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: extracted Task3127 wrapper behavior into task-scoped helper functions and replayed the helper outputs against Task3127 reference artifacts.
- What did not change: no root dependency manifest, `src/` promotion, source acquisition, replay, selector change, sizing change, paper order, live order, acceptance, or deployment state changed.
- Key metrics:
  - Helper contracts: 6.
  - Helper replay rows: 4.
  - Helper candidates: 4.
  - Reference matches: 4.
- Next action: only after owner approval, move these task-scoped helpers into a small reusable infrastructure module; keep trading brain disconnected.

## Quant Expert Report

### Helper Contracts

| helper_id | tool_name | helper_status | allowed_layers | forbidden_layers | dependency_mode | promoted_to_src |
| --- | --- | --- | --- | --- | --- | --- |
| HELP3141-PANDERA-SEC-SCHEMA | pandera | enabled | data_validation|resolver_qa | selector|sizing|replay|paper_order|live_order|acceptance|deployment | task3126_isolated_venv | 0 |
| HELP3141-POLARS-LOCAL-AGG | polars | enabled | local_artifact_query|audit_benchmark | selector|sizing|replay|paper_order|live_order|acceptance|deployment | current_environment_import | 0 |
| HELP3141-DUCKDB-LOCAL-AGG | duckdb | enabled | local_artifact_query|audit_benchmark | selector|sizing|replay|paper_order|live_order|acceptance|deployment | current_environment_import | 0 |
| HELP3141-EDGARTOOLS-OFFLINE-SEC | edgartools | deferred | none_until_offline_local_parse_is_proven | selector|sizing|replay|paper_order|live_order|acceptance|deployment | deferred | 0 |
| HELP3141-DLT-RECEIPT | dlt | deferred | none_until_source_receipt_task | selector|sizing|replay|paper_order|live_order|acceptance|deployment | deferred | 0 |
| HELP3141-GITHUB-MCP-READONLY | github_mcp_read_only | deferred | none_until_read_only_monitoring_task | source_truth|selector|sizing|replay|paper_order|live_order|acceptance|deployment | deferred | 0 |

### Helper Replay Results

| helper_id | tool_name | source_wrapper_id | query_id | helper_status | source_row_count | result_row_count | reference_match | decision | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HELP3141-PANDERA-SEC-SCHEMA | pandera | WRAP3127-PANDERA-SEC-SCHEMA |  | executed |  |  | 1 | helper_candidate | schema_checks_executed |
| HELP3141-POLARS-LOCAL-AGG | polars | WRAP3127-POLARS-SEC-AGG | sec_symbol_event_family_agg | executed | 138049 | 1294 | 1 | helper_candidate | matches_task3127_reference |
| HELP3141-POLARS-LOCAL-AGG | polars | WRAP3127-POLARS-LIQUIDITY-AGG | liquidity_provider_series_agg | executed | 768841 | 38 | 1 | helper_candidate | matches_task3127_reference |
| HELP3141-DUCKDB-LOCAL-AGG | duckdb | WRAP3127-DUCKDB-LIQUIDITY-AGG | liquidity_provider_series_agg | executed | 768841 | 38 | 1 | helper_candidate | matches_task3127_reference |

### Reference Diff

| helper_id | source_wrapper_id | diff_status | reference_match |
| --- | --- | --- | --- |
| HELP3141-PANDERA-SEC-SCHEMA | WRAP3127-PANDERA-SEC-SCHEMA | matched | 1 |
| HELP3141-POLARS-LOCAL-AGG | WRAP3127-POLARS-SEC-AGG | matched | 1 |
| HELP3141-POLARS-LOCAL-AGG | WRAP3127-POLARS-LIQUIDITY-AGG | matched | 1 |
| HELP3141-DUCKDB-LOCAL-AGG | WRAP3127-DUCKDB-LIQUIDITY-AGG | matched | 1 |

### Helper Decision Matrix

| tool_name | helper_decision | candidate_helper_count | mismatch_count | allowed_next_layer |
| --- | --- | --- | --- | --- |
| pandera | promote_task_scoped_helper_candidate | 1 | 0 | task_scoped_helper_only_no_src_promotion |
| polars | promote_task_scoped_helper_candidate | 2 | 0 | task_scoped_helper_only_no_src_promotion |
| duckdb | promote_task_scoped_helper_candidate | 1 | 0 | task_scoped_helper_only_no_src_promotion |
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
| no_src_promotion | 1 | Helpers remain task-scoped under scripts. |
| helper_contracts_present | 1 | All helper contracts are recorded. |
| helper_reference_replay_match | 1 | Helper outputs match Task3127 reference outputs. |
| helper_candidates_present | 1 | Pandera, Polars, and DuckDB helper candidates exist. |
| deferred_tools_not_promoted | 1 | Deferred tools remain deferred. |

No output from this task is connected to selector, sizing, replay, paper runtime, live orders, strategy acceptance, or deployment readiness.

## No-Background Decision-Maker Report

Conclusion first: the useful external tools are now organized as task-scoped infrastructure helpers, not trading logic.

`Pandera`, `Polars`, and `DuckDB` reproduced the Task3127 wrapper outputs. This makes them reasonable helper candidates for validation and local artifact querying. `edgartools`, `dlt`, and GitHub MCP remain deferred.

This does not change strategy acceptance. This does not change deployment readiness. This does not permit real capital.

## Artifact Manifest

- Inputs:
  - `C:/Users/minjo/OneDrive/바탕 화면/외국주식 퀀트트레이딩/data/artifacts/task_3127_external_tool_opt_in_wrapper_pilot/wrapper_decision_matrix.csv`
  - `C:/Users/minjo/OneDrive/바탕 화면/외국주식 퀀트트레이딩/data/artifacts/task_3127_external_tool_opt_in_wrapper_pilot/local_query_wrapper_result.csv`
  - `C:/Users/minjo/OneDrive/바탕 화면/외국주식 퀀트트레이딩/data/artifacts/task_2541_2560_sec_financing_dilution_acquisition/task2545_normalized_sec_financing_dilution_packets.csv`
  - `C:/Users/minjo/OneDrive/바탕 화면/외국주식 퀀트트레이딩/data/artifacts/task_2561_2580_liquidity_rates_regime_acquisition/task2565_normalized_liquidity_rates_packets.csv`
- Outputs:
  - `docs/reports/task_3141_external_tool_helper_contract/task_3141_external_tool_helper_contract.md`
  - `docs/reports/task_3141_external_tool_helper_contract/task_3141_decision.csv`
  - `data/artifacts/task_3141_external_tool_helper_contract/`
- Row counts:
  - Helper contracts: 6
  - Helper replay rows: 4
  - Helper diff rows: 4
  - Helper decision rows: 6
- Validation commands:
  - `python scripts/trader_brain_3141_external_tool_helper_contract_validate.py`
  - `python scripts/task_registry_validate.py`
- Source hashes:
  - Task3127 wrapper decisions: `c75269f8ceef7e5a056196084aecf82203056e1a87826606371625f475f29952`
  - Task3127 query wrappers: `c41fed453b03a9218efa61ec814f98a693a4d953386be9c5e336c196637fe9ed`
  - SEC panel: `1cc0ba60ca78ec615ff3b1ce57af0d43ac04f3ba548e4da8ec9d7bc0712e07e2`
  - Liquidity/rates panel: `59e8ee997132715335e02e1ba71a932598bba026719905851c1c09d25659f297`

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
