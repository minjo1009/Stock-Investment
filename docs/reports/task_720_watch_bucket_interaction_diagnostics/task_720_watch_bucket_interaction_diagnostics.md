# Task720 Watch Bucket Interaction Diagnostics

## Decision Summary

- Verdict: WATCH_BUCKET_INTERACTION_DIAGNOSTICS_BUILT_RESEARCH_ONLY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Conclusion: do not add a new brain layer first; strengthen interaction logic between existing layers.
- Next action: Manually review the three interaction packets before any backtest promotion.

## Quant Expert Report

- Scope: 345 watch candidates across the three priority buckets.
- Inputs: Task713 evidence, Task714 economic transmission, Task715 market pricing, Task716 slot context, and Task719 confirmation contracts.
- Institutional context:
  - Fed FSR 2026: valuation, borrowing, leverage, and funding risks can amplify stress.
  - IMF GFSR 2026: risk sentiment, financial conditions, leverage, and flow channels can move together.
  - NBER cash-flow news: cash-flow evidence and price reaction must be evaluated jointly.
  - NBER macro news reaction: conflicting signals can produce both overreaction and underreaction.
- Implementation: cashflow, financing, price absorption, slot competition, and invalidation axes are linked into a diagnostic interaction state.
- No action output is produced.

## No-Background Decision-Maker Report

- This does not buy anything.
- The issue is not another brain layer yet.
- The issue is whether company evidence, financing risk, price absorption, and slot quality agree or fight each other.
- The next human review should inspect financing use-of-proceeds, slot superiority, and company evidence price absorption packets.

## Artifact Manifest

- Outputs: task720_watch_bucket_interaction_panel.csv, task720_institutional_context_pack.csv, task720_bucket_interaction_matrix.csv, task720_human_review_queue.csv, task720_eval_guardrail.csv, task720_leakage_guardrail.csv, task720_governance_audit.csv, task_720_decision.csv, task_720_pass_fail_matrix.csv.
- Row counts: task720_watch_bucket_interaction_panel.csv=345; task720_institutional_context_pack.csv=4; task720_bucket_interaction_matrix.csv=5; task720_human_review_queue.csv=345; task720_eval_guardrail.csv=5; task720_leakage_guardrail.csv=8; task720_governance_audit.csv=9; task_720_decision.csv=1; task_720_pass_fail_matrix.csv=9.
- Validation command: `python -m unittest tests.test_task720_watch_bucket_interaction_diagnostics`.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| scope_target_345 | PRIMARY_PASS | 1 | rows=345 | 345 |
| target_subtype_count_3 | PRIMARY_PASS | 1 | subtypes=3 | 3 |
| interaction_matrix_present | PRIMARY_PASS | 1 | rows=5 | >0 |
| human_review_queue_complete | PRIMARY_PASS | 1 | rows=345 | 345 |
| eval_guardrail_present | PRIMARY_PASS | 1 | 0 | 0 |
| leakage_all_pass | PRIMARY_PASS | 1 | min=1 | 1 |
| governance_all_pass | PRIMARY_PASS | 1 | min=1 | 1 |
| strategy_not_accepted | PRIMARY_PASS | 1 | NOT_ACCEPTED | NOT_ACCEPTED |
| real_capital_forbidden | PRIMARY_PASS | 1 | FORBIDDEN | FORBIDDEN |
