# Task3126 External Tool Isolated Install Pilot

## Decision Summary

- Verdict: `external_tool_isolated_install_pilot_completed_diagnostic_only`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: created an isolated venv install pilot for `edgartools` and `Pandera`, ran an offline SEC local-parse compatibility check, ran a Pandera validator attempt, and benchmarked DuckDB/Polars on larger local panels.
- What did not change: no root dependency manifest, raw source download, source acquisition, replay, selector change, sizing change, paper order, live order, acceptance, or deployment state changed.
- Key metrics:
  - Install rows: 2.
  - Installed tools: 2.
  - Pandera decision: `adopt`.
  - Edgartools decision: `defer`.
  - Large benchmark rows: 6.
  - Local query adoption candidates: 3.
- Next action: promote only tools with `decision=adopt` to a separate opt-in wrapper task; keep all others deferred or blocked.

## Quant Expert Report

### Isolated Install Lock

| tool_name | install_status | version | import_available | import_name_used | license |
| --- | --- | --- | --- | --- | --- |
| edgartools | installed | 5.36.0 | 1 | edgar | Development Status :: 4 - Beta;Intended Audience :: Developers;Intended Audience :: Financial and Insurance Industry;Intended Audience :: Science/Research;License :: OSI Approved :: MIT License;Programming Language :: Python;Programming Language :: Python :: 3.10;Programming Language :: Python :: 3. |
| pandera | installed | 0.32.0 | 1 | pandera | MIT License  Copyright (c) 2018 Niels Bantilan  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:  The above copyrigh |

The install was isolated under `.cache/task_3126_external_tool_venv/`. No root dependency manifest was created.

### Edgartools SEC Local Fixture Check

| tool_name | install_status | comparison_status | sample_row_count | local_parser_found | row_level_match_rows | adoption_decision | decision_reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| edgartools | installed | local_parser_candidates_found_not_executed_no_safe_constructor | 10 | 1 | 0 | defer | local_parser_candidates_found_not_executed_no_safe_constructor |

`edgartools` was not allowed to download SEC data. It could only qualify if a safe offline local-file parser was proven against existing raw documents.

### Pandera Validator Pilot

| tool_name | install_status | schema_status | row_count | pandera_row_count | imperative_validator_pass | pandera_validator_pass | pandera_failure_cases |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pandera | installed | schema_checks_executed | 138049 | 138049 | 1 | 1 | 0 |

| tool_name | diff_status | row_count_match | false_fail_detected | adoption_decision | decision_reason |
| --- | --- | --- | --- | --- | --- |
| pandera | matched | 1 | 0 | adopt | schema_matches_existing_validator |

The validator target is the existing SEC normalized packet panel. The schema checks timestamps, source/hash identity, missing-as-negative flags, and outcome-assignment flags.

### DuckDB/Polars Large Panel Benchmark

| query_id | engine | runtime_ms | source_row_count | result_row_count | join_key_null_count | row_count_match_pandas | aggregate_checksum_match_pandas | strict_gate_pass_total_match_pandas | adoption_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sec_symbol_event_family_agg | pandas | 3147.2319 | 138049 | 1294 | 0 | 1 | 1 | 1 | 0 |
| sec_symbol_event_family_agg | duckdb | 3630.7828 | 138049 | 1294 | 0 | 1 | 1 | 1 | 0 |
| sec_symbol_event_family_agg | polars | 371.0838 | 138049 | 1294 | 0 | 1 | 1 | 1 | 1 |
| liquidity_provider_series_agg | pandas | 12350.1617 | 768841 | 38 | 0 | 1 | 1 | 1 | 0 |
| liquidity_provider_series_agg | duckdb | 4770.785 | 768841 | 38 | 0 | 1 | 1 | 1 | 1 |
| liquidity_provider_series_agg | polars | 475.6024 | 768841 | 38 | 0 | 1 | 1 | 1 | 1 |

The benchmark compares pandas, DuckDB, and Polars on existing local SEC and liquidity/rates panels. Results that differ from pandas are not adoption candidates.

### Adoption Decision Matrix

| tool_name | decision | reason | allowed_next_layer |
| --- | --- | --- | --- |
| edgartools | defer | local_parser_candidates_found_not_executed_no_safe_constructor | none_until_offline_local_parse_is_proven |
| pandera | adopt | schema_matches_existing_validator | optional_validator_schema_candidate |
| duckdb | adopt | large_panel_adoption_candidates=1 | local_artifact_query_helper_candidate |
| polars | adopt | large_panel_adoption_candidates=2 | local_artifact_query_helper_candidate |
| dlt | defer | deferred_not_in_task3126 | none_until_source_receipt_task |
| github_mcp_read_only | defer | connector_not_invoked_in_task3126 | none_until_read_only_monitoring_task |

### Acceptance Checks

| check_name | pass | detail |
| --- | --- | --- |
| status_unchanged | 1 | Strategy/deployment/real-capital statuses remain unchanged. |
| no_orders | 1 | No paper or live orders are created. |
| no_replay_or_source_acquisition | 1 | No replay or source acquisition is performed. |
| root_dependency_manifest_absent | 1 | No root Python dependency manifest was created. |
| install_lock_present | 1 | edgartools and pandera install rows are recorded. |
| edgartools_no_trading_connection | 1 | edgartools is not connected to selector/sizing/replay. |
| pandera_validation_recorded | 1 | Pandera validation result is recorded even if blocked. |
| large_panel_benchmark_exact_or_rejected | 1 | DuckDB/Polars available rows match pandas on row/key/checksum metrics. |
| decisions_cover_all_tools | 1 | All planned tools have an adopt/defer/reject/blocked decision. |

No output from this task is connected to selector, sizing, replay, paper runtime, live orders, strategy acceptance, or deployment readiness.

## No-Background Decision-Maker Report

Conclusion first: this task decides which external tools deserve a next wrapper step, not trading use.

`Pandera` can move forward only if its isolated schema result matches the existing validator. `edgartools` cannot move forward unless it proves offline local SEC document parsing without hiding raw identity. DuckDB/Polars can move forward only where a large-panel benchmark exactly matches pandas and is faster.

This does not change strategy acceptance. This does not change deployment readiness. This does not permit real capital.

## Artifact Manifest

- Inputs:
  - `C:/Users/minjo/OneDrive/바탕 화면/외국주식 퀀트트레이딩/data/artifacts/task_2541_2560_sec_financing_dilution_acquisition/task2545_normalized_sec_financing_dilution_packets.csv`
  - `C:/Users/minjo/OneDrive/바탕 화면/외국주식 퀀트트레이딩/data/artifacts/task_2561_2580_liquidity_rates_regime_acquisition/task2565_normalized_liquidity_rates_packets.csv`
- Outputs:
  - `docs/reports/task_3126_external_tool_isolated_install_pilot/task_3126_external_tool_isolated_install_pilot.md`
  - `docs/reports/task_3126_external_tool_isolated_install_pilot/task_3126_decision.csv`
  - `data/artifacts/task_3126_external_tool_isolated_install_pilot/`
- Row counts:
  - Tool install lock: 2
  - Edgartools comparison summary rows: 1
  - Pandera validation rows: 1
  - Large benchmark rows: 6
  - Adoption decision rows: 6
- Validation commands:
  - `python scripts/trader_brain_3126_external_tool_isolated_install_pilot_validate.py`
  - `python scripts/task_registry_validate.py`
- Source hashes:
  - SEC panel: `1cc0ba60ca78ec615ff3b1ce57af0d43ac04f3ba548e4da8ec9d7bc0712e07e2`
  - Liquidity/rates panel: `59e8ee997132715335e02e1ba71a932598bba026719905851c1c09d25659f297`

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
