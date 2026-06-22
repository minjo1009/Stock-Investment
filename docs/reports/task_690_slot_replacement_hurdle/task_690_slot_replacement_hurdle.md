# Task690 Same-Timestamp Slot Replacement Hurdle

## Decision Summary

- Verdict: SAME_TIMESTAMP_SLOT_REPLACEMENT_HURDLE_BUILT_NO_TRADING_PROMOTION.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Key metrics: candidates 1621, slot-hurdle candidates 1451, cohorts 210, hurdle states 4.
- What changed: slot claim is now explained inside same-timestamp cohorts only.
- Next action: Review slot leaders and contenders by cohort before any allocation backtest.

## Quant Expert Report

### Data source and source readiness

Inputs are Task688 bundle/slot explanations and Task689 interpretation/edge/weak-layer panels. No new raw source is added.

### Exact join keys

- `lifecycle_id` joins all candidate-level panels.
- `cohort_id = split_name + entry_ts`.
- `cohort_rank` is valid only inside `cohort_id`.

### Leakage audit

- No PnL, win/loss, simulated exit, or future price columns are included.
- This task does not run a backtest and does not promote a trading rule.
- Existing holdings are not inferred; active exposure is marked as proxy only.

### Slot replacement rulebook

| rule_id | purpose | required_inputs | decision_effect | forbidden_shortcut |
| --- | --- | --- | --- | --- |
| same_timestamp_only | Prevent global Top5 leakage and compare only candidates competing at the same entry timestamp. | entry_ts\|split_name\|same-entry peer set | cohort_rank can be used only inside the same entry_ts and split. | No global priority rank or future outcome rank. |
| clear_superiority_margin | New slot claimant must be meaningfully better than peers, not merely slightly higher. | claim_score minus cohort_median and next peer score | Leader becomes clear only when margin to median is >= 3 and no blocker exists. | Do not admit a candidate because it is rank 1 by a tiny score gap. |
| blocker_overrides_rank | Sector blocker beats attractive headline score. | sector_specific_blocker_flag\|weakest_layer | Candidate becomes blocker_limited even if cohort_rank is high. | Do not use a blocker candidate as a full-slot replacement. |
| quality_before_capacity | Capacity pressure is not enough; candidate must have quality evidence. | interpretation quality\|edge quality\|bundle readiness | Low quality candidates stay confirmation/research even when cohort is small. | Do not fill empty slots with weak evidence. |
| active_exposure_proxy_only | Existing holdings are not reconstructed here, so active exposure is a proxy, not an incumbent identity. | active_theme_count\|active_relation_count\|active_driver_count where available | Produces unresolved incumbent hurdle when peer comparison is insufficient. | No inferred incumbent symbol/date/price matching. |

### Hurdle state summary

| replacement_hurdle_state | slot_claim_tier | candidate_count |
| --- | --- | --- |
| clear_same_timestamp_superiority | slot_leader | 28 |
| cohort_contender_needs_confirmation | slot_contender | 407 |
| quality_gap_no_slot_claim | research_only_or_no_claim | 1098 |
| sector_blocker_limited | cap_limited_or_delayed | 88 |

### Slot claim tier summary

| slot_claim_tier | candidate_count |
| --- | --- |
| cap_limited_or_delayed | 88 |
| research_only_or_no_claim | 1098 |
| slot_contender | 407 |
| slot_leader | 28 |

### Hurdle decomposition

| scope | replacement_hurdle_state | candidate_count | avg_cohort_size | avg_slot_claim_score | leader_count | contender_count | research_or_no_claim_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all_candidates | clear_same_timestamp_superiority | 28 | 11.0000 | 9.5000 | 28 | 0 | 0 |
| all_candidates | cohort_contender_needs_confirmation | 407 | 10.4079 | 8.9275 | 0 | 407 | 0 |
| all_candidates | quality_gap_no_slot_claim | 1098 | 17.9262 | 6.4649 | 0 | 0 | 1098 |
| all_candidates | sector_blocker_limited | 88 | 17.1818 | -44.8750 | 0 | 0 | 0 |
| slot_hurdle_required | clear_same_timestamp_superiority | 19 | 14.9474 | 10.6579 | 19 | 0 | 0 |
| slot_hurdle_required | cohort_contender_needs_confirmation | 288 | 13.8681 | 10.0590 | 0 | 288 | 0 |
| slot_hurdle_required | quality_gap_no_slot_claim | 1075 | 18.2474 | 6.6260 | 0 | 0 | 1075 |
| slot_hurdle_required | sector_blocker_limited | 69 | 21.4348 | -43.6304 | 0 | 0 | 0 |

### Split/OOS metrics

Not applicable. This task is not a return test.

### Failure decomposition

- Many candidates still require slot replacement proof rather than automatic entry.
- High rank inside a cohort is not enough when sector blockers or quality gaps exist.
- Single-candidate cohorts with active exposure pressure remain unresolved because incumbent identities are not reconstructed here.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Review slot leaders/contenders with source packets.
- Add actual active holding identity only through deterministic portfolio replay, not proximity matching.
- Then convert only reviewed slot states into a backtest candidate.

## No-Background Decision-Maker Report

- What happened: slot competition is now peer-relative, not global.
- Why it matters: a candidate must prove it deserves a scarce slot at that timestamp.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: inspect leaders and contenders before changing allocation.

## Artifact Manifest

- Inputs: Task688 bundle/slot objects, Task689 interpretation/edge/weak-layer panels.
- Outputs: slot replacement rulebook, cohort competition panel, slot claim explanation v2, hurdle decomposition, integrity audit, decision, pass/fail, manifest.
- Row counts: competition 1621, explanation 1621, decomposition 8.
- Validation commands: `python src/backtest/build_task690_slot_replacement_hurdle.py`; `python -m unittest tests.test_task690_slot_replacement_hurdle`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| competition_panel_present | PRIMARY_PASS | 1 | competition=1621; explanations=1621 | one explanation per competition row |
| same_timestamp_rank_scope_only | PRIMARY_PASS | 1 | {'same_entry_ts_split_only': 1621} | no global ranking scope |
| slot_hurdle_decomposed | PRIMARY_PASS | 1 | hurdle_states=4 | slot hurdle candidates should split into multiple states |
| no_outcome_columns_in_slot_outputs | PRIMARY_PASS | 1 | none | PnL/outcome columns excluded |
| no_strategy_promotion | PRIMARY_PASS | 1 | no PnL simulation or allocation rule promotion was run | slot hurdle explanation only |
