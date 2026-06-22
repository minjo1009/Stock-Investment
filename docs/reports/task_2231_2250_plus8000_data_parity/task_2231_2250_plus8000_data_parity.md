# Task2231-2250 Plus8000 Data Parity

## Decision Summary

- Verdict: `plus8000_data_parity_failed_replay_blocked`.
- Candidate rows: 3100.
- Plus8000 parity rows: 0.
- Plus8000 parity ratio: 0.0.
- Feature schema rows: 3100.
- Any raw source rows: 863.
- Replay allowed: `0`.
- Replay blocker: `same_standard_plus8000_data_not_attached_to_full_3100_pool`.
- Missing acquisition queue rows: 1577.
- Reference +8000 policy: `api_dd_guard_soft_boost_cap_top2_v1`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task does not run a replay. It first checks whether the data level used in the +8000 selected-trade sizing test is attached to the full 3,100-candidate pool under the same feature contract.

Contract:

- `task2124_l1_api_proxy_features`: source rows 377, exact keys 217, role `L1_api_proxy_features_used_before_plus8000_sizing`.
- `task2162_decision_asof_coverage`: source rows 377, exact keys 217, role `API_source_packet_coverage_used_for_hardened_L2`.
- `task2163_l2_api_semantics_hardened`: source rows 377, exact keys 217, role `hardened_L2_API_semantics`.
- `task2171_l4_api_score_cards_hardened`: source rows 377, exact keys 217, role `hardened_L4_API_adjusted_rank`.
- `task2172_l5_api_decisions_hardened`: source rows 377, exact keys 217, role `hardened_L5_API_budget_decision`.

Coverage:

- `exact_task2124_feature_match`: 217/3100 (0.07), pass 0.
- `exact_task2162_2172_hardened_match`: 217/3100 (0.07), pass 0.
- `symbol_raw_endpoint_parity`: 76/3100 (0.024516), pass 0.
- `asof_raw_endpoint_parity`: 0/3100 (0.0), pass 0.
- `plus8000_data_parity_pass`: 0/3100 (0.0), pass 0.
- `symbol_endpoint_stock_filings`: 863/3100 (0.278387), pass 0.
- `symbol_endpoint_stock_recommendation`: 863/3100 (0.278387), pass 0.
- `symbol_endpoint_earnings_history`: 230/3100 (0.074194), pass 0.
- `symbol_endpoint_income_statement`: 76/3100 (0.024516), pass 0.
- `symbol_endpoint_balance_sheet`: 76/3100 (0.024516), pass 0.
- `symbol_endpoint_cash_flow`: 76/3100 (0.024516), pass 0.
- `asof_endpoint_stock_filings`: 312/3100 (0.100645), pass 0.
- `asof_endpoint_stock_recommendation`: 0/3100 (0.0), pass 0.
- `asof_endpoint_earnings_history`: 230/3100 (0.074194), pass 0.
- `asof_endpoint_income_statement`: 18/3100 (0.005806), pass 0.
- `asof_endpoint_balance_sheet`: 18/3100 (0.005806), pass 0.
- `asof_endpoint_cash_flow`: 18/3100 (0.005806), pass 0.

Recomputed full-candidate feature schema:

- `feature_schema_parity_pass`: 3100/3100 (1.0).
- `raw_source_present_for_any_contract_endpoint`: 863/3100 (0.278387).
- `api_proxy_state::api_proxy_mixed_or_light`: 429/3100 (0.138387).
- `api_proxy_state::api_proxy_risk_or_weak_quality`: 6/3100 (0.001935).
- `api_proxy_state::api_proxy_source_gap_neutral`: 2631/3100 (0.84871).
- `api_proxy_state::api_proxy_supportive`: 34/3100 (0.010968).

## No-Background Decision-Maker Report

Conclusion first: the +8000 feature schema can be generated for 3,100 rows, but raw source parity is still weak. Therefore a fair full-universe replay under raw-source parity is blocked until the user explicitly authorizes proxy-schema parity replay.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2231_2250_plus8000_data_parity/`.
- Validator: `python scripts/trader_brain_2231_2250_plus8000_data_parity_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
