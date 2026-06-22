# Task724 Queue Deep Dive Review

## Decision Summary

- Verdict: QUEUE_DEEP_DIVE_REVIEW_BUILT_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Key metrics: queue1 0, queue2 25, queue3 320.
- What changed: Task723 manual review queues are decomposed into institutional review subtypes with raw text, evidence span, contamination, and parser-gap diagnostics.
- Next action: Queue1 is empty after parser repair; repair queue2 parser-miss versus true-empty cases and queue3 taxonomy exceptions before any backtest.

## Quant Expert Report

### Data source and source readiness

Inputs are Task722 source-attached packet panel and Task723 manual review queue. Task724 reads raw text files referenced by Task722 when available and does not infer new lifecycle matches.

### Exact join keys

Task724 joins Task723 to Task722 by `lifecycle_id` only after Task723 already preserved `symbol`, `theme_id`, `entry_ts`, and `split_name`.

### Leakage audit

Forbidden outcome, return, winner, loser, future price, top50, post-event, backtest target, selection result, and costed return fields are blocked. Manual subtypes are review-only and cannot create buy, sell, sizing, or allocation instructions.

### Queue subtype summary

| review_queue | manual_subtype | candidate_count | raw_text_available_count | economic_terms_found_count | financing_terms_found_count | ownership_terms_found_count |
| --- | --- | --- | --- | --- | --- | --- |
| queue_2_semantic_enrichment_review | true_semantic_empty_ownership_filing | 24 | 24 | 4 | 24 | 24 |
| queue_2_semantic_enrichment_review | parser_miss_policy_or_sector_transmission | 1 | 1 | 0 | 1 | 1 |
| queue_3_noise_taxonomy_qa | pure_form4_insider_noise | 198 | 198 | 198 | 198 | 198 |
| queue_3_noise_taxonomy_qa | pure_ownership_13g_13d_noise | 96 | 96 | 89 | 88 | 96 |
| queue_3_noise_taxonomy_qa | ownership_noise_with_company_anchor | 20 | 20 | 20 | 20 | 20 |
| queue_3_noise_taxonomy_qa | insider_noise_with_material_context | 3 | 3 | 3 | 3 | 0 |
| queue_3_noise_taxonomy_qa | noise_taxonomy_misclassified | 3 | 3 | 3 | 0 | 0 |

### Split/OOS metrics

Not applicable. This task is not a backtest.

### Failure decomposition

- Queue 1 is not clean. It is mostly cashflow-flagged but company-specific causality is not established and financing/ownership/generic filing contamination must be separated.
- Queue 2 is a parser-miss versus true-empty filing problem.
- Queue 3 should stay shallow QA unless a company anchor is found.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Queue 1 manual subtype decisions remain pending.
- Queue 2 parser-miss versus true-empty decisions remain pending.
- Queue 3 company-anchor mixed suspects are QA-only until manually confirmed.

## No-Background Decision-Maker Report

- What happened: 1/2/3순위를 더 잘게 깠습니다.
- Why it matters: 1순위도 깨끗한 호재가 아니라 오염된 후보일 수 있다는 점이 보입니다.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: parser repair after this task can reduce queue1 to zero; then remaining queue2/queue3 parser gaps must be fixed before backtest.

## Artifact Manifest

- Inputs: `docs\reports\task_722_source_attached_review_packets\task722_source_attached_packet_panel.csv`, `docs\reports\task_723_five_stage_decision_contract\task723_manual_review_queue.csv`.
- Outputs: task724_queue_deep_dive_panel.csv, task724_queue_summary.csv, task724_subtype_summary.csv, task724_queue1_cashflow_packets.csv, task724_queue2_semantic_gap_packets.csv, task724_queue3_noise_qa_packets.csv, task724_manual_review_sample_packets.csv, task724_institutional_review_protocol.csv, task724_leakage_guardrail.csv, task724_governance_audit.csv, task_724_decision.csv, task_724_pass_fail_matrix.csv.
- Row counts: task724_queue_deep_dive_panel.csv=345; task724_queue_summary.csv=2; task724_subtype_summary.csv=7; task724_queue1_cashflow_packets.csv=0; task724_queue2_semantic_gap_packets.csv=25; task724_queue3_noise_qa_packets.csv=320; task724_manual_review_sample_packets.csv=27; task724_institutional_review_protocol.csv=3; task724_leakage_guardrail.csv=4; task724_governance_audit.csv=10; task_724_decision.csv=1; task_724_pass_fail_matrix.csv=10.
- Validation command: `python -m unittest tests.test_task724_queue_deep_dive_review`.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| all_345_subtyped | PRIMARY_PASS | 1 | rows=345 | 345 with subtype |
| queue1_decomposed_or_empty | PRIMARY_PASS | 1 | rows=0; subtypes=0 | empty or >=1 subtype |
| queue2_decomposed | PRIMARY_PASS | 1 | subtypes=2 | >=1 |
| queue3_decomposed | PRIMARY_PASS | 1 | rows=320; subtypes=5 | >0 and >=2 |
| queue_summary_present | PRIMARY_PASS | 1 | rows=2 | >=2; queue1 may be empty after parser repair |
| subtype_summary_present | PRIMARY_PASS | 1 | rows=7 | >0 |
| leakage_all_pass | PRIMARY_PASS | 1 | min=1 | 1 |
| governance_all_pass | PRIMARY_PASS | 1 | min=1 | 1 |
| strategy_not_accepted | PRIMARY_PASS | 1 | NOT_ACCEPTED | NOT_ACCEPTED |
| real_capital_forbidden | PRIMARY_PASS | 1 | FORBIDDEN | FORBIDDEN |
