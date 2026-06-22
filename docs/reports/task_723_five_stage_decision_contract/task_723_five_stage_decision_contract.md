# Task723 Five Stage Decision Contract

## Decision Summary

- Verdict: FIVE_STAGE_DECISION_CONTRACT_BUILT_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Key metrics: candidates 345, queue1 0, queue2 25, queue3 320.
- What changed: Task722 source-attached packets are converted into five linked object layers: evidence, interpretation, relation, bundle, and slot judgment.
- Next action: Queue1 is empty after source parser repair; repair queue2 semantic gaps and queue3 ownership/noise taxonomy before any eligibility rule or backtest.

## Quant Expert Report

### Data source and source readiness

Input is Task722 source-attached review packet panel. Task723 does not add a data source, infer lifecycle matches, or use missing evidence as a negative signal.

### Exact join keys

All objects retain `lifecycle_id`, `symbol`, `theme_id`, `entry_ts`, and `split_name`. Slot judgment uses same `split_name` plus same `entry_ts` cohort only.

### Leakage audit

Forbidden future outcome, return, winner, loser, top50, future price, post-event, backtest target, and selection result fields are blocked from all Task723 objects. No action output is produced.

### Five-stage contract

1. Evidence object: source facts, raw text path, evidence span, certification, source noise, and authority.
2. Economic interpretation object: cashflow, customer, backlog, guidance, margin, financing, novelty, priced-in, and economic path states.
3. Relation edge object: evidence-to-interpretation, interpretation-to-price, interpretation-to-slot, and source-noise-to-queue edges.
4. Candidate context bundle: object ids, weakest layer, missing evidence, bundle state, and manual review queue.
5. Slot judgment object: same-timestamp cohort, slot claim, hurdle, review state, and explanation.

### Split/OOS metrics

Not applicable. This task is not a backtest.

### Failure decomposition

Queue 1 is the first review target because it has source-supported cashflow evidence. Queue 2 checks parser or semantic gaps. Queue 3 is noise taxonomy QA only.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Queue 1 manual packet review is not complete.
- Queue 2 semantic enrichment is not complete.
- Slot judgment remains explanatory only, not allocation authority.

## No-Background Decision-Maker Report

- What happened: the five-step structure is now fixed in code and artifacts.
- Why it matters: each candidate can be inspected by weak layer before any trading rule is changed.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: if queue1 is empty after parser repair, fix remaining semantic/noise parser gaps before any backtest.

## Artifact Manifest

- Inputs: `docs\reports\task_722_source_attached_review_packets\task722_source_attached_packet_panel.csv`.
- Outputs: task723_stage_contract.csv, task723_evidence_objects.csv, task723_economic_interpretation_objects.csv, task723_relation_edge_objects.csv, task723_candidate_context_bundles.csv, task723_slot_judgment_objects.csv, task723_manual_review_queue.csv, task723_leakage_guardrail.csv, task723_governance_audit.csv, task_723_decision.csv, task_723_pass_fail_matrix.csv.
- Row counts: task723_stage_contract.csv=5; task723_evidence_objects.csv=345; task723_economic_interpretation_objects.csv=345; task723_relation_edge_objects.csv=1380; task723_candidate_context_bundles.csv=345; task723_slot_judgment_objects.csv=345; task723_manual_review_queue.csv=345; task723_leakage_guardrail.csv=6; task723_governance_audit.csv=10; task_723_decision.csv=1; task_723_pass_fail_matrix.csv=10.
- Validation command: `python -m unittest tests.test_task723_five_stage_decision_contract`.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| five_stage_artifacts_present | PRIMARY_PASS | 1 | all present | all present |
| one_object_per_candidate_except_edges | PRIMARY_PASS | 1 | matched | matched |
| relation_edges_four_per_candidate | PRIMARY_PASS | 1 | edges=1380 | 4 per candidate |
| weakest_layer_populated | PRIMARY_PASS | 1 | complete | complete |
| manual_review_queue_populated | PRIMARY_PASS | 1 | complete | complete |
| slot_judgment_cohort_only | PRIMARY_PASS | 1 | cohort_only=1 | cohort_only=1 |
| leakage_all_pass | PRIMARY_PASS | 1 | min=1 | 1 |
| governance_all_pass | PRIMARY_PASS | 1 | min=1 | 1 |
| strategy_not_accepted | PRIMARY_PASS | 1 | NOT_ACCEPTED | NOT_ACCEPTED |
| real_capital_forbidden | PRIMARY_PASS | 1 | FORBIDDEN | FORBIDDEN |
