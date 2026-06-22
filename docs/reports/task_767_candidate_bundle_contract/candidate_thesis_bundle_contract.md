# Candidate Thesis Bundle Contract

## Purpose

`CandidateThesisBundle` is the L4 explanatory object in the Task756 Trader Brain program.

It collects source-backed L1 evidence, L2 primitive facts, L3 meaning objects, relation edges, modifiers, and compound interaction state into a review packet. The packet explains why a thesis exists, what still needs confirmation, what contradicts it, what would invalidate it, and which layer is weakest.

It is not a trade candidate. It is not a slot priority. It cannot emit buy, sell, hold, rank, score, sizing, allocation, portfolio budget, order, fill, backtest eligibility, deployment readiness, or real-capital permission.

## Layer Boundary

Allowed:

- Preserve the evidence trail behind a possible thesis.
- Summarize source-backed thesis logic in plain language.
- Show confirmations needed before stronger review.
- Show contradictions and invalidation conditions.
- Identify the weakest layer and unresolved gaps.
- Carry modifiers and compound state as explanatory context.
- Emit review-only forbidden-output flags.

Forbidden:

- Buy, sell, hold, rank, score, sizing, allocation, slot priority, portfolio budget, order, fill, or backtest eligibility.
- Hidden rank, hidden score, hidden priority, or implied slot readiness.
- Future returns, outcomes, PnL, win/loss labels, or post-event price behavior in bundle creation.
- Inferred lifecycle matching.
- Symbol/date/price/time proximity fallback matching.
- Missing context treated as rejection or negative evidence.
- Price acceptance used to rescue `source_gap`, `context_only`, or `not_ready` upstream states.

## Required Bundle Fields

| Field | Required | Meaning |
| --- | --- | --- |
| `bundle_id` | yes | Stable L4 id derived from explicit upstream ids and contract version. It must not use return, PnL, label, rank, or price reaction. |
| `lifecycle_id` | optional | Upstream lifecycle id if supplied. Blank remains uncertainty and must not be inferred. |
| `symbol` | yes | Source-attached issuer symbol for audit and display. It is not a fallback matching key. |
| `asof_ts` | yes | Timestamp the bundle is allowed to know as of. |
| `evidence_trace` | yes | Structured L1 trace including evidence ids, source event ids, raw/span references, source trace state, and as-of state. |
| `primitive_facts` | yes | Explicit L2 primitive fact ids and review states. Empty means `source_gap` or `not_ready`, not negative evidence. |
| `meaning_objects` | yes | Explicit L3 meaning object ids, meaning states, confidence bands, ambiguity, blockers, and needed confirmations. |
| `relation_edges` | yes | Explicit Task763-style edge ids and relation effects. Absence is a review gap, not a rejection. |
| `modifiers` | yes | Explicit Task765-style modifier ids and effects. Use `none` only when reviewed and absent. |
| `compound_state` | when supplied | Upstream compound interaction state. If Task766 output is unavailable, record `compound_state_unavailable` in unresolved gaps. |
| `thesis_statement` | yes | Human-readable source-backed thesis explanation. It cannot contain trade instructions. |
| `confirmation_needed` | yes | Conditions or evidence needed before stronger relation or later gate review. |
| `contradictions` | yes | Source-backed conflicts, offsetting edges, blockers, modifier disagreement, or `none_visible`. Missing data is not a contradiction by itself. |
| `invalidation_conditions` | yes | Conditions that would weaken or falsify the thesis. Must be as-of-safe or explicitly future-monitoring, not outcome labels. |
| `weakest_layer` | yes | One of the allowed weakest-layer values below. |
| `unresolved_gaps` | yes | Missing source, primitive, meaning, relation, modifier, compound, timestamp, denominator, or confirmation gaps. |
| `forbidden_outputs` | yes | Must include all forbidden outputs listed below. |

## Allowed Values

### Weakest Layer

- `none_visible`
- `L1_source_evidence`
- `L2_primitive_fact`
- `L3_meaning_object`
- `L3_relation_edge`
- `modifier_context`
- `compound_state`
- `L4_bundle_coherence`
- `asof_trace`
- `source_gap`
- `not_ready`

`none_visible` only means no weakest layer is visible from the current packet. It does not mean trade readiness.

### Confirmation Needed

Use pipe-delimited values such as:

- `none_visible`
- `raw_source_review`
- `timestamp_repair`
- `primitive_fact_repair`
- `denominator_needed`
- `operating_catalyst_confirmation`
- `source_circuit_classification`
- `relation_edge_review`
- `modifier_confirmation`
- `compound_state_needed`
- `invalidation_trace_needed`

### Contradictions

Use pipe-delimited values such as:

- `none_visible`
- `meaning_modifier_conflict`
- `reinforcing_offsetting_conflict`
- `source_trace_conflict`
- `primitive_meaning_conflict`
- `dilution_growth_funding_conflict`
- `price_acceptance_rejection_conflict`
- `regime_or_sector_hostile`
- `hard_blocker_present`

Missing context alone must be listed in `unresolved_gaps`, not as a contradiction.

### Invalidation Conditions

Use source-backed or review-monitoring conditions such as:

- `growth_use_not_confirmed`
- `operating_catalyst_missing`
- `dilution_terms_worse_than_trace`
- `guidance_reaffirmation_absent`
- `source_trace_retracted_or_corrected`
- `modifier_rejected`
- `price_acceptance_fails_after_asof_review`
- `compound_conflict_unresolved`
- `raw_source_unavailable`

Invalidation conditions must not use future return, PnL, win/loss, or backtest outcome labels.

## Forbidden Outputs

Every bundle must carry:

```text
forbidden_outputs = buy_sell|rank|score|sizing|allocation|slot_priority|portfolio_budget|order|fill|backtest_eligibility|deployment_readiness|real_capital|outcome_assignment|future_return_assignment
```

Recommended constant flags:

```text
buy_sell_signal_created_flag = 0
rank_created_flag = 0
score_created_flag = 0
sizing_created_flag = 0
slot_priority_created_flag = 0
backtest_eligible_flag = 0
outcome_used_for_assignment_flag = 0
real_capital_status = FORBIDDEN
```

## Construction Rules

1. Build the bundle only from explicit upstream ids and traces.
2. Preserve upstream `source_gap`, `context_only`, `not_ready`, hard blocker, confidence cap, and invalidation states.
3. Use `symbol` for display and audit only.
4. Use `asof_ts` to state the knowledge boundary.
5. Record missing upstream context in `unresolved_gaps`.
6. Record contradictory source-backed states in `contradictions`.
7. Record the most limiting visible layer in `weakest_layer`.
8. Record what would falsify or weaken the thesis in `invalidation_conditions`.
9. Do not create readiness, slot priority, or backtest eligibility from thesis coherence.

## Minimal Example

```text
bundle_id: bundle:L4:example:v1
lifecycle_id: L123
symbol: EXAMPLE
asof_ts: 2024-01-02T14:30:00Z
evidence_trace: evidence_id=E1;source_event_id=S1;source_trace_state=raw_source_available
primitive_facts: primitive_fact_id=P1;review_state=fact_ready_for_meaning_review
meaning_objects: meaning_object_id=M1;meaning_state=financing_growth_funding_size_known;confidence_band=medium
relation_edges: edge_id=R1;relation_type=prerequisite;allowed_effect=confirmation_required
modifiers: modifier_id=MOD1;modifier_family=price_acceptance;state=unclear;allowed_effect=require_confirmation
compound_state: compound_state_unavailable
thesis_statement: Source-backed financing may support growth use, but operating catalyst and price acceptance remain unconfirmed.
confirmation_needed: operating_catalyst_confirmation|modifier_confirmation|compound_state_needed
contradictions: dilution_growth_funding_conflict
invalidation_conditions: growth_use_not_confirmed|dilution_terms_worse_than_trace
weakest_layer: compound_state
unresolved_gaps: compound_state_unavailable|operating_catalyst_confirmation_needed
forbidden_outputs: buy_sell|rank|score|sizing|allocation|slot_priority|portfolio_budget|order|fill|backtest_eligibility|deployment_readiness|real_capital|outcome_assignment|future_return_assignment
```

## Validation Authority

This is diagnostic/research contract validation only.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
