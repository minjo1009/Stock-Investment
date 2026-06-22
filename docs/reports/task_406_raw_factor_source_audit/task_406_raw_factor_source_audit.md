# Task 406A - Raw Factor Source Audit

## Quant Expert Report
- Raw row provenance is deterministic and uses no inferred matching.
- Missing quote/spread/status/LULD/raw receive timestamp sources are explicitly reported as missing raw source.

## No-Background Decision-Maker Report
- The local raw data is usable for OHLCV-based factors.
- It is not deployment-grade for quote/spread/status factors yet.

## Decision
task_406a_verdict,evaluation_status,raw_bar_count,symbol_count,available_exact_factor_count,missing_raw_source_factor_count,non_regular_session_bar_count,quote_spread_status_missing_flag,inferred_matching_used_flag,deployment_claim_flag,strategy_acceptance_status
COMPLETE_PASS,RAW_FACTOR_SOURCE_AUDIT_DIAGNOSTIC,3788967,159,8,13,1298129,1,0,0,RAW_SOURCE_LIMITED_DIAGNOSTIC_ONLY