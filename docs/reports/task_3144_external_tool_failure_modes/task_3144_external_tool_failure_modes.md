# Task3144 External Tool Failure Modes

## Decision Summary

- Verdict: `external_tool_failure_modes_completed_diagnostic_only`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: hardened `src/infra/external_tools.py` so malformed local artifact inputs return structured failure statuses instead of uncaught crashes.
- What did not change: no source acquisition, replay, selector, sizing, paper order, live order, root dependency manifest, acceptance, or deployment state changed.
- Key metrics: bad fixtures 3, failure cases 8, pass rows 8.

## Quant Expert Report

### Bad Fixtures

| fixture_name | path | sha256 |
| --- | --- | --- |
| missing_join_key | C:/Users/minjo/OneDrive/바탕 화면/외국주식 퀀트트레이딩/data/artifacts/task_3144_external_tool_failure_modes/bad_fixtures/missing_join_key.csv | 365b8b1142819ac2db4f97a026060f904057dbfd1e4a85a7ffd21c233dd79921 |
| missing_strict_gate | C:/Users/minjo/OneDrive/바탕 화면/외국주식 퀀트트레이딩/data/artifacts/task_3144_external_tool_failure_modes/bad_fixtures/missing_strict_gate.csv | 022d9ff85aa7bb14aa4e642dfe1c207c17cab7ea7cb6d8acfbc31cab54f1a230 |
| bad_sec_schema | C:/Users/minjo/OneDrive/바탕 화면/외국주식 퀀트트레이딩/data/artifacts/task_3144_external_tool_failure_modes/bad_fixtures/bad_sec_schema.csv | 77c8bc135a6ba97943ccaa5bbcc386707935662b156a041bceab289a6bb91219 |

### Failure Cases

| case_id | tool_name | fixture_name | expected_status | actual_status | failure_mode_pass |
| --- | --- | --- | --- | --- | --- |
| FAIL3144-PANDAS-missing_join_key | pandas | missing_join_key | invalid_input | invalid_input | 1 |
| FAIL3144-PANDAS-missing_strict_gate | pandas | missing_strict_gate | invalid_input | invalid_input | 1 |
| FAIL3144-POLARS-missing_join_key | polars | missing_join_key | invalid_input | invalid_input | 1 |
| FAIL3144-POLARS-missing_strict_gate | polars | missing_strict_gate | invalid_input | invalid_input | 1 |
| FAIL3144-DUCKDB-missing_join_key | duckdb | missing_join_key | invalid_input | invalid_input | 1 |
| FAIL3144-DUCKDB-missing_strict_gate | duckdb | missing_strict_gate | invalid_input | invalid_input | 1 |
| FAIL3144-PANDERA-bad_sec_schema | pandera | bad_sec_schema | schema_execution_failed | schema_execution_failed | 1 |
| FAIL3144-DEPENDENCY-MISSING | definitely_missing_external_tool_for_task3144 | none | dependency_missing | dependency_missing | 1 |

### Acceptance Checks

| check_name | pass | detail |
| --- | --- | --- |
| failure_cases_present | 1 | All failure cases are recorded. |
| failure_modes_pass | 1 | All bad inputs close as expected statuses. |
| no_traceback_escape | 1 | All failure cases returned structured status. |
| status_unchanged | 1 | Strategy/deployment/real-capital statuses remain unchanged. |

No output from this task is connected to selector, sizing, replay, paper runtime, live orders, strategy acceptance, or deployment readiness.

## No-Background Decision-Maker Report

Conclusion first: bad inputs now fail closed with structured statuses.

Malformed query panels return `invalid_input`, bad Pandera schema returns `schema_execution_failed`, and missing tools return `dependency_missing`.

## Artifact Manifest

- Outputs:
  - `docs/reports/task_3144_external_tool_failure_modes/task_3144_external_tool_failure_modes.md`
  - `data/artifacts/task_3144_external_tool_failure_modes/`
- Validation commands:
  - `python scripts/trader_brain_3144_external_tool_failure_modes_validate.py`
  - `python scripts/task_registry_validate.py`

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
