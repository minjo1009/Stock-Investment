# Task3127 External Tool Opt-In Wrapper Pilot

## Decision Summary

- Verdict: `external_tool_opt_in_wrapper_pilot_completed_diagnostic_only`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: promoted only Task3126 adopted infrastructure candidates into task-scoped opt-in wrappers for validation and local artifact querying.
- What did not change: no root dependency manifest, raw source download, source acquisition, replay, selector change, sizing change, paper order, live order, acceptance, or deployment state changed.
- Key metrics:
  - Wrapper contracts: 7.
  - Executed wrappers: 4.
  - Wrapper candidates: 4.
  - Deferred wrappers: 3.
- Next action: move only `Pandera` and exact/faster local query wrappers into a narrow reusable helper task; keep `edgartools`, `dlt`, and GitHub MCP deferred.

## Quant Expert Report

### Wrapper Contracts

| wrapper_id | tool_name | wrapper_status | allowed_layers | forbidden_layers | writes_only_under_task_artifacts |
| --- | --- | --- | --- | --- | --- |
| WRAP3127-PANDERA-SEC-SCHEMA | pandera | enabled | data_validation|resolver_qa | selector|sizing|replay|paper_order|live_order|acceptance|deployment | 1 |
| WRAP3127-POLARS-SEC-AGG | polars | enabled | local_artifact_query|audit_benchmark | selector|sizing|replay|paper_order|live_order|acceptance|deployment | 1 |
| WRAP3127-POLARS-LIQUIDITY-AGG | polars | enabled | local_artifact_query|audit_benchmark | selector|sizing|replay|paper_order|live_order|acceptance|deployment | 1 |
| WRAP3127-DUCKDB-LIQUIDITY-AGG | duckdb | enabled | local_artifact_query|audit_benchmark | selector|sizing|replay|paper_order|live_order|acceptance|deployment | 1 |
| WRAP3127-EDGARTOOLS-OFFLINE-SEC | edgartools | deferred | none_until_offline_local_parse_is_proven | selector|sizing|replay|paper_order|live_order|acceptance|deployment | 1 |
| WRAP3127-DLT-RECEIPT | dlt | deferred | none_until_source_receipt_task | selector|sizing|replay|paper_order|live_order|acceptance|deployment | 1 |
| WRAP3127-GITHUB-MCP-READONLY | github_mcp_read_only | deferred | none_until_read_only_monitoring_task | source_truth|selector|sizing|replay|paper_order|live_order|acceptance|deployment | 1 |

### Pandera Schema Wrapper

| wrapper_id | wrapper_status | schema_status | row_count | pandera_validator_pass | decision | reason |
| --- | --- | --- | --- | --- | --- | --- |
| WRAP3127-PANDERA-SEC-SCHEMA | executed | schema_checks_executed | 138049 | 1 | wrapper_candidate | schema_passed_in_opt_in_wrapper |

### Local Query Wrappers

| wrapper_id | query_id | engine | wrapper_status | pandas_runtime_ms | wrapper_runtime_ms | source_row_count | result_row_count | aggregate_checksum_match_pandas | faster_than_pandas | decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WRAP3127-POLARS-SEC-AGG | sec_symbol_event_family_agg | polars | executed | 2130.3458 | 236.7916 | 138049 | 1294 | 1 | 1 | wrapper_candidate |
| WRAP3127-POLARS-LIQUIDITY-AGG | liquidity_provider_series_agg | polars | executed | 13194.4239 | 397.5859 | 768841 | 38 | 1 | 1 | wrapper_candidate |
| WRAP3127-DUCKDB-LIQUIDITY-AGG | liquidity_provider_series_agg | duckdb | executed | 13194.4239 | 3817.8115 | 768841 | 38 | 1 | 1 | wrapper_candidate |

### Wrapper Decision Matrix

| tool_name | wrapper_decision | candidate_wrapper_count | reason | allowed_next_layer |
| --- | --- | --- | --- | --- |
| pandera | adopt_wrapper_candidate | 1 | schema_passed_in_opt_in_wrapper | task_scoped_validator_wrapper_only |
| polars | adopt_wrapper_candidate | 2 | candidate_count=2;mismatch_count=0 | task_scoped_local_artifact_query_wrapper_only |
| duckdb | adopt_wrapper_candidate | 1 | candidate_count=1;mismatch_count=0 | task_scoped_local_artifact_query_wrapper_only |
| edgartools | defer | 0 | deferred_until_offline_local_sec_parse_is_proven | none |
| dlt | defer | 0 | deferred_until_source_receipt_task | none |
| github_mcp_read_only | defer | 0 | deferred_until_read_only_monitoring_task | none |

### Acceptance Checks

| check_name | pass | detail |
| --- | --- | --- |
| status_unchanged | 1 | Strategy/deployment/real-capital statuses remain unchanged. |
| no_orders | 1 | No paper or live orders are created. |
| no_replay_or_source_acquisition | 1 | No replay or source acquisition is performed. |
| root_dependency_manifest_absent | 1 | No root Python dependency manifest was created. |
| wrapper_contracts_present | 1 | All enabled and deferred wrapper contracts are recorded. |
| pandera_wrapper_passed | 1 | Pandera opt-in wrapper passed. |
| query_wrappers_exact | 1 | Executed local query wrappers match pandas. |
| wrapper_candidates_present | 1 | At least one local query wrapper candidate exists. |
| deferred_tools_not_executed | 1 | Deferred tools were not executed. |
| decisions_cover_all_tools | 1 | All planned tools have wrapper decisions. |

No output from this task is connected to selector, sizing, replay, paper runtime, live orders, strategy acceptance, or deployment readiness.

## No-Background Decision-Maker Report

Conclusion first: we now have real wrapper candidates, but still only for infrastructure.

`Pandera` is useful as a schema validator wrapper. `Polars` is useful for local artifact query acceleration. `DuckDB` remains useful where its exact result is faster than pandas. `edgartools` is still not ready because offline local SEC parsing has not been proven.

This does not change strategy acceptance. This does not change deployment readiness. This does not permit real capital.

## Artifact Manifest

- Inputs:
  - `C:/Users/minjo/OneDrive/바탕 화면/외국주식 퀀트트레이딩/data/artifacts/task_3126_external_tool_isolated_install_pilot/adoption_decision_matrix.csv`
  - `C:/Users/minjo/OneDrive/바탕 화면/외국주식 퀀트트레이딩/data/artifacts/task_2541_2560_sec_financing_dilution_acquisition/task2545_normalized_sec_financing_dilution_packets.csv`
  - `C:/Users/minjo/OneDrive/바탕 화면/외국주식 퀀트트레이딩/data/artifacts/task_2561_2580_liquidity_rates_regime_acquisition/task2565_normalized_liquidity_rates_packets.csv`
- Outputs:
  - `docs/reports/task_3127_external_tool_opt_in_wrapper_pilot/task_3127_external_tool_opt_in_wrapper_pilot.md`
  - `docs/reports/task_3127_external_tool_opt_in_wrapper_pilot/task_3127_decision.csv`
  - `data/artifacts/task_3127_external_tool_opt_in_wrapper_pilot/`
- Row counts:
  - Wrapper contracts: 7
  - Pandera wrapper rows: 1
  - Local query wrapper rows: 3
  - Wrapper decision rows: 6
- Validation commands:
  - `python scripts/trader_brain_3127_external_tool_opt_in_wrapper_pilot_validate.py`
  - `python scripts/task_registry_validate.py`
- Source hashes:
  - Task3126 decisions: `0d6f4012c2bfd99b300f80d77915aba301a0527ecb0bd1d82618e14151dd4afc`
  - SEC panel: `1cc0ba60ca78ec615ff3b1ce57af0d43ac04f3ba548e4da8ec9d7bc0712e07e2`
  - Liquidity/rates panel: `59e8ee997132715335e02e1ba71a932598bba026719905851c1c09d25659f297`

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
