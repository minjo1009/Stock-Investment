# Task691 Slot Leader and Contender Review

## Decision Summary

- Verdict: SLOT_LEADER_CONTENDER_REVIEW_BUILT_NO_TRADING_PROMOTION.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Key metrics: leaders 28, contenders 407, cohort reviews 210.
- What changed: slot leaders and contenders now have review paths before any allocation backtest.
- Next action: Inspect leader review statuses and contender confirmation paths, then define only reviewed allocation candidates.

## Quant Expert Report

### Data source and source readiness

Inputs are Task689 quality panels and Task690 same-timestamp slot competition outputs. No new raw source is added.

### Exact join keys

- `lifecycle_id` joins leader/contender rows to interpretation, edge, and weak-layer audits.
- `cohort_id` keeps review inside same timestamp and split.

### Leakage audit

- No PnL, win/loss, simulated exit, or future price columns are included.
- This task does not run a backtest and does not promote a trading rule.

### Confirmation rulebook

| confirmation_type | applies_when | must_confirm | promotion_effect |
| --- | --- | --- | --- |
| price_absorption_confirmation | priced-in gap, extension risk, or low margin versus next peer | price remains accepted without immediate fade; no full-slot promotion from headline alone | contender may become review-ready, not auto-buy |
| source_packet_confirmation | customer quality, contract value, margin bridge, or surprise is weak | source text supports economic value, counterparty quality, repeatability, and expectation surprise | economic interpretation gap can be downgraded |
| sector_blocker_clearance | sector blocker or blocker-limited state exists | funding, duration, policy, commodity, or credit blocker is absent or improving | candidate can move from cap-limited/delayed to contender review |
| peer_margin_confirmation | candidate is rank 1-3 but margin is small | candidate has clear same-timestamp superiority versus peers after quality penalties | candidate can become slot leader candidate |
| incumbent_replay_confirmation | active exposure proxy hurdle remains unresolved | deterministic portfolio replay identifies incumbent and opportunity cost without proximity matching | replacement decision can be audited against actual incumbent |

### Leader review summary

| leader_review_status | leader_verdict | leader_count |
| --- | --- | --- |
| leader_low_absolute_score | leader_label_but_not_allocation_ready | 5 |
| leader_priced_in_review_needed | leader_needs_specific_confirmation | 4 |
| leader_source_packet_needed | leader_needs_specific_confirmation | 19 |

### Contender confirmation summary

| required_confirmation_type | contender_review_bucket | contender_count |
| --- | --- | --- |
| peer_margin_confirmation | same_cohort_margin_review | 114 |
| price_absorption_confirmation | price_acceptance_review | 293 |

### Cohort review summary

| cohort_review_state | cohort_count |
| --- | --- |
| blocker_limited_cohort | 14 |
| contender_only_no_clear_leader | 168 |
| leader_only_cohort | 7 |
| leader_plus_contenders | 21 |

### Split/OOS metrics

Not applicable. This task is not a return test.

### Failure decomposition

- Leaders are not automatically clean. They can be thin, low-score, priced-in, or source-packet dependent.
- Contenders need explicit confirmation before promotion.
- Incumbent replacement remains unresolved until deterministic portfolio replay supplies actual incumbent identity.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Review leader statuses and remove weak leaders from allocation candidates.
- Convert contender confirmation paths into pre-backtest eligibility rules.
- Add deterministic incumbent replay before true replacement logic.

## No-Background Decision-Maker Report

- What happened: 28 leaders and 407 contenders were split into review buckets.
- Why it matters: this prevents "leader" from meaning automatic buy.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: approve which review buckets can enter the next allocation test.

## Artifact Manifest

- Inputs: Task689 quality panels, Task690 slot competition outputs.
- Outputs: confirmation rulebook, leader review, contender confirmation map, cohort review summary, integrity audit, decision, pass/fail, manifest.
- Row counts: leaders 28, contenders 407, cohorts 210.
- Validation commands: `python src/backtest/build_task691_slot_leader_contender_review.py`; `python -m unittest tests.test_task691_slot_leader_contender_review`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| leader_and_contender_counts_match_task690 | PRIMARY_PASS | 1 | leaders=28; contenders=407 | Task690 slot leader and contender counts must match |
| leader_review_decomposed | PRIMARY_PASS | 1 | leader_statuses=3 | leaders should split into multiple review states |
| contender_confirmation_decomposed | PRIMARY_PASS | 1 | confirmation_types=2 | contenders should split into data-supported confirmation paths |
| cohort_review_present | PRIMARY_PASS | 1 | cohort_review=210; cohorts=210 | one cohort review row per cohort |
| no_outcome_columns_in_review_outputs | PRIMARY_PASS | 1 | none | PnL/outcome columns excluded |
| no_strategy_promotion | PRIMARY_PASS | 1 | no PnL simulation or allocation rule promotion was run | leader/contender review only |
