# Task741 Economic Denominator Meaning Layer

## Decision Summary

- Verdict: `ECONOMIC_DENOMINATOR_MEANING_LAYER_CONDITIONALLY_CLOSED_WITH_BLOCKERS`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Backtest permission: `FAIL`
- Economic packets: 3443
- Missing source blockers: 8117
- Meaning states: 10
- Layer status: `CONDITIONALLY_CLOSED_WITH_EXPLICIT_JOIN_BLOCKERS`

## Quant Expert Report

Task741 attaches available economic denominators and comparators to Task740 source-semantic resolver outputs. It uses local SEC companyfacts and daily price sources when they are as-of valid, and emits explicit blockers for missing free float, prior holder percent, exact insider history, consensus, prior guidance, and margin bridge sources.

### Quality Metrics

| metric | value | unit |
| --- | --- | --- |
| packet_coverage_count | 3443.0 | count |
| task722_event_detail_join_rate | 1.0 | ratio |
| sec_companyfacts_join_rate | 1.0 | ratio |
| daily_price_join_rate | 1.0 | ratio |
| market_cap_proxy_attach_rate | 0.383387 | ratio |
| revenue_baseline_attach_rate | 0.998838 | ratio |
| cash_debt_attach_rate | 0.998838 | ratio |
| ownership_percent_attach_rate | 0.071159 | ratio |
| financing_principal_attach_rate | 0.383387 | ratio |
| missing_blocker_emit_rate | 2.357537 | ratio |
| future_data_violation_count | 0.0 | count |
| trade_output_violation_count | 0.0 | count |

### Meaning Distribution

| source_circuit | meaning_state | row_count | backtest_eligible_count |
| --- | --- | --- | --- |
| form4_insider_behavior | insider_transaction_size_attached_source_only | 1376 | 0 |
| ownership_float_structure | ownership_market_cap_context_attached | 622 | 0 |
| ownership_float_structure | ownership_float_denominator_blocked | 621 | 0 |
| form4_insider_behavior | insider_transaction_size_market_cap_context | 534 | 0 |
| activist_control | ownership_percent_source_attached | 235 | 0 |
| financial_results_guidance | revenue_baseline_attached | 26 | 0 |
| ownership_float_structure | ownership_percent_source_attached | 10 | 0 |
| form4_insider_behavior | insider_context_denominator_blocked | 6 | 0 |
| generic_8k_classifier | generic_8k_non_operating_route_confirmed | 5 | 0 |
| financial_results_guidance | financial_result_source_only_context | 4 | 0 |
| credit_financing | financing_principal_market_cap_context | 4 | 0 |

### Source Availability

| availability_flag | true_count | packet_count | true_rate |
| --- | --- | --- | --- |
| has_cash_fact | 3439 | 3443 | 0.998838 |
| has_consensus_estimates | 0 | 3443 | 0.0 |
| has_daily_price | 3443 | 3443 | 1.0 |
| has_debt_fact | 2055 | 3443 | 0.596863 |
| has_event_date | 3443 | 3443 | 1.0 |
| has_exact_insider_history | 0 | 3443 | 0.0 |
| has_free_float | 0 | 3443 | 0.0 |
| has_market_cap_proxy | 1320 | 3443 | 0.383387 |
| has_prior_guidance_database | 0 | 3443 | 0.0 |
| has_public_float_fact | 3412 | 3443 | 0.990996 |
| has_raw_text_path | 3443 | 3443 | 1.0 |
| has_revenue_fact | 3439 | 3443 | 0.998838 |
| has_sec_companyfacts | 3443 | 3443 | 1.0 |
| has_shares_outstanding_fact | 1320 | 3443 | 0.383387 |
| has_task722_event_detail | 3443 | 3443 | 1.0 |
| has_task740_primitive | 3443 | 3443 | 1.0 |
| has_tradable_after_dt | 3443 | 3443 | 1.0 |

### Blocker Summary

| blocker_state | source_circuit | row_count | backtest_eligible_count |
| --- | --- | --- | --- |
| exact_person_history_missing | form4_insider_behavior | 1916 | 0 |
| insider_total_holdings_missing | form4_insider_behavior | 1916 | 0 |
| prior_holder_percent_missing | ownership_float_structure | 1253 | 0 |
| free_float_missing | ownership_float_structure | 1253 | 0 |
| ownership_percent_missing | ownership_float_structure | 1243 | 0 |
| prior_holder_percent_missing | activist_control | 235 | 0 |
| free_float_missing | activist_control | 235 | 0 |
| consensus_estimates_missing | financial_results_guidance | 30 | 0 |
| prior_guidance_database_missing | financial_results_guidance | 30 | 0 |
| ownership_after_missing | form4_insider_behavior | 6 | 0 |

### Guardrail

| gate | pass_flag | observed | expected |
| --- | --- | --- | --- |
| no_forbidden_columns_created | 1 | checked | no forbidden output columns |
| no_future_denominator_or_price | 1 | rows=0 | 0 |
| missing_is_blocker_not_negative | 1 | rows=0 | 0 |
| no_bullish_bearish_financing | 1 | rows=0 | 0 |
| generic_8k_item101_not_operating_supported | 1 | rows=0 | 0 |
| no_trade_score_backtest_outputs | 1 | rows=0 | 0 |
| all_packets_trace_identity | 1 | rows=0 | 0 |

### GPT Review

| review_scope | status | summary | applied_to_code_flag | gpt_is_source_of_truth_flag |
| --- | --- | --- | --- | --- |
| overall_brain_strategy_review | EXISTING_TAB_CAPTURED | Institutional GPT review passed Task741 as an economic denominator/comparator meaning layer that attaches available local denominators and emits explicit missing-source blockers without trading, scoring, ranking, or backtest promotion. | 1 | 0 |
| circuit_detail_review | EXISTING_TAB_CAPTURED | GPT required Form4 transaction size context, ownership/13D/13G percent and float blockers, financing principal versus market/cash/debt context, financial results baseline and expectation blockers, and generic 8-K route guardrails. | 1 | 0 |

## No-Background Decision-Maker Report

The economic meaning layer is conditionally closed. Local denominators such as SEC companyfacts, public float USD, shares outstanding, cash, debt, revenue, and daily price are attached when available. Missing higher-grade sources remain explicit blockers, not negative signals.

## Artifact Manifest

- `task741_economic_meaning_packets.csv/jsonl`
- `task741_missing_source_blockers.csv/jsonl`
- `task741_quality_metrics.csv`
- `task741_meaning_distribution.csv`
- `task741_source_availability_summary.csv`
- `task741_blocker_summary.csv`
- `task741_coverage_report.csv`
- `task741_guardrail.csv`
- `task741_gpt_review_summary.csv`
- `task_741_decision.csv`
- `task_741_pass_fail_matrix.csv`

## Pass Fail Matrix

| gate | pass_flag | observed | expected |
| --- | --- | --- | --- |
| all_task740_resolvers_have_packets | 1 | resolvers=3443, packets=3443 | equal |
| coverage_report_created | 1 | all_task740_resolvers_have_economic_meaning_packet | all covered |
| quality_metrics_created | 1 | rows=12 | >=10 |
| missing_source_blockers_emitted | 1 | rows=8117 | >0 |
| guardrail_all_pass | 1 | min=1 | 1 |
| backtest_permission | 0 | FAIL | economic meaning packets review only |
