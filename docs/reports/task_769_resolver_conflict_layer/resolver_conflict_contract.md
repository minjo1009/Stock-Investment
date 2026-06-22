# Resolver Conflict Contract

## Purpose

Task769 defines the research-only resolver and conflict layer for the Task756 Trader Brain program.

The resolver receives explicit upstream evidence, primitive, meaning, relation, modifier, compound, bundle, and slot-review inputs. It converts missing fields, weak sources, timestamp problems, relation blockers, invalidation, and modifier disagreement into bounded next-action states.

It resolves to a review or repair class. It does not resolve to a trade, rank, score, size, slot, backtest eligibility, deployment readiness, strategy acceptance, or real-capital permission.

## Boundary

Allowed:

- Preserve upstream source and provenance gaps.
- Detect conflicts between primitive facts, meaning objects, relation edges, modifiers, compound states, candidate bundles, and same-timestamp slot inputs.
- Emit research-only output states: `source_gap`, `timestamp_blocked`, `not_comparable`, `repair_needed`, `review_needed`, `context_only`, or `ready_for_gate_review`.
- Escalate to the owning research layer when a source, primitive, meaning, relation, modifier, bundle, timestamp, or comparability repair is needed.
- Keep missing labels, missing denominators, missing comparators, and missing raw sources as explicit uncertainty or repair states.

Forbidden:

- No code promotion.
- No future data.
- No future prices, returns, PnL, win/loss labels, target labels, or realized outcomes.
- No GPT-only resolution.
- No silent default pass.
- No buy, sell, hold, rank, score, sizing, allocation, slot priority, portfolio budget, order, fill, trade permission, backtest eligibility, deployment readiness, strategy acceptance, or real-capital permission.
- No inferred lifecycle matching.
- No symbol/date/price/time proximity fallback matching.
- No missing-to-negative conversion.
- No price, regime, sector, theme, or supportive modifier rescue of `source_gap`, `context_only`, `not_ready`, blocker, cap, timestamp, or comparability failures.

## Required Inputs

The resolver may consume only explicit upstream ids and review fields. Missing inputs must be reported as gaps instead of inferred.

| Input family | Required fields when available | Use |
| --- | --- | --- |
| L1 Evidence | `evidence_id`, `source_event_id`, `raw_source_available_flag`, `source_trace_state`, `source_family`, `asof_ts` | Determine source availability and trace state. |
| L2 PrimitiveFact | `primitive_fact_id`, `source_event_id`, `fact_family`, `fact_type`, `fact_value`, `review_state`, `join_blocker_state`, `missing_required_context`, `as_of_state` | Detect primitive missing or primitive blocker states. |
| L3 MeaningObject | `meaning_object_id`, `primitive_fact_id`, `meaning_state`, `confidence_band`, `ambiguity`, `soft_blockers`, `hard_blockers`, `needed_confirmation`, `relation_ready_tier`, `invalidation_clue` | Detect meaning conflicts, blockers, caps, and confirmation needs. |
| L3 RelationEdge | `edge_id`, `source_node`, `target_node`, `relation_type`, `preconditions`, `confidence_cap`, `primitive_gate_state`, `allowed_effect`, `invalidation_link` | Detect relation blockers, prerequisites, confidence caps, and invalidation. |
| Modifier | `modifier_id`, `modifier_family`, `state`, `asof_state`, `relation_effect`, `confidence_cap`, `invalidation_link`, `allowed_effect` | Detect modifier disagreement, rejected context, and cap states. |
| CompoundState | `compound_state`, `blocking_trace_ids`, `cap_trace_ids`, `confirmation_trace_ids`, `invalidation_trace_ids`, `source_trace_ids` | Preserve Task766 state precedence and unresolved blockers. |
| CandidateBundle | `candidate_bundle_id`, `evidence_trace`, `primitive_facts`, `meaning_objects`, `relation_edges`, `modifiers`, `compound_state`, `confirmation_needed`, `contradictions`, `invalidation_conditions`, `weakest_layer`, `unresolved_gaps` | Detect bundle-level unresolved gaps and conflict evidence. |
| SlotInput | `slot_input_id`, `cohort_id`, `entry_ts`, `asof_ts`, `candidate_bundle_id`, `comparison_scope`, `source_readiness_state`, `relation_quality_state`, `uncertainty_state`, `slot_review_state`, `disqualifiers` | Detect exact timestamp comparability and slot-review blockers. |

## Conflict States

The resolver catalog is stored in `conflict_state_catalog.csv`. The canonical conflict state set is:

- `source_gap`
- `primitive_missing`
- `meaning_conflict`
- `modifier_conflict`
- `relation_blocker`
- `invalidation_present`
- `timestamp_blocked`
- `not_comparable`
- `review_needed`
- `repair_needed`
- `context_only`
- `ready_for_gate_review`

Conflict states describe what the resolver found. Resolution outputs describe what the next action is.

## Resolution Outputs

Allowed resolver outputs:

| Output state | Meaning |
| --- | --- |
| `source_gap` | Required raw source, source trace, or upstream id is missing. Source repair or source review is required. |
| `timestamp_blocked` | Required as-of, event, filing, entry, or cohort timestamp is missing, inconsistent, or future-contaminated. |
| `not_comparable` | Exact cohort, bundle, timestamp, or explicit identity requirements are absent for same-timestamp comparison. |
| `repair_needed` | Contract shape, required fields, provenance, contamination, or missing primitive inputs must be repaired before review. |
| `review_needed` | Source-backed conflict, blocker, cap, contradiction, modifier disagreement, or invalidation needs owner review. |
| `context_only` | Evidence may be retained as explanatory context but cannot move into directional relation or gate review. |
| `ready_for_gate_review` | Explicit source, primitive, meaning, relation, modifier, timestamp, and conflict checks are present with no unresolved blocker. This is research-only gate-review readiness. |

Forbidden resolver outputs:

```text
buy_sell
rank
score
sizing
allocation
slot_priority
portfolio_budget
order
fill
trade_permission
backtest_eligibility
deployment_readiness
strategy_acceptance
real_capital
future_return
pnl
win_loss
outcome_label
inferred_lifecycle_match
symbol_date_price_time_fallback_match
```

## Precedence Rules

The resolver must apply the highest-priority active condition first:

1. Future-contaminated input, outcome input, GPT-only support, or forbidden output request -> `repair_needed`.
2. Missing raw source, source trace, or required upstream id -> `source_gap`.
3. Missing, unsafe, stale, inconsistent, or future-contaminated as-of boundary -> `timestamp_blocked`.
4. Missing exact cohort, exact timestamp, or explicit bundle identity for comparison -> `not_comparable`.
5. Missing required primitive fields or primitive gate not ready -> `repair_needed`.
6. Explicit relation blocker or hard blocker -> `review_needed`.
7. Explicit invalidation -> `review_needed`.
8. Meaning conflict, modifier conflict, contradiction, cap, or confirmation need -> `review_needed`.
9. Context-only source, primitive, meaning, compound, bundle, or slot state -> `context_only`.
10. No unresolved source, primitive, meaning, relation, modifier, timestamp, comparability, blocker, cap, contradiction, or invalidation issue -> `ready_for_gate_review`.

Unknown or unrecognized states must resolve to `repair_needed`. They must not default to pass.

## Provenance Requirements

Every resolver output must preserve:

- `resolver_packet_id`
- `contract_version`
- `input_artifact_refs`
- explicit upstream ids used
- conflict states observed
- selected output state
- dominant blocker or repair reason
- as-of timestamp fields supplied by upstream artifacts
- source trace state
- owner escalation target
- forbidden output audit flags

The resolver must also record:

- `inferred_matching_used = NO`
- `future_data_used = NO`
- `gpt_only_resolution_used = NO`
- `silent_default_pass_used = NO`
- `missing_to_negative_used = NO`

If any of those values would be `YES`, the packet must emit `repair_needed` and block `ready_for_gate_review`.

## Escalation Rules

| Condition | Escalation target | Required action |
| --- | --- | --- |
| Raw source or source trace missing | Data & Market Microstructure | Restore source trace or mark source gap explicitly. |
| Primitive fields missing | Data & Market Microstructure | Repair L2 extraction or carry `primitive_missing`. |
| Meaning ambiguity or contradiction | Regime Research | Review meaning state, blockers, confidence cap, and confirmation need. |
| Relation blocker or invalidation | Regime Research + Backtest & Simulation Infra | Review relation edge, preconditions, and invalidation trace. |
| Modifier disagreement | Regime Research | Review modifier family, state, as-of boundary, and allowed effect. |
| Compound or bundle conflict | Research Governance | Preserve weakest layer, contradiction, unresolved gap, and next action. |
| Timestamp or cohort failure | Backtest & Simulation Infra | Repair exact timestamp, as-of boundary, or cohort identity without fallback matching. |
| Forbidden output requested | Research Governance | Reject requested output and emit `repair_needed`. |
| GPT-only support detected | Research Governance | Reject as source-of-truth and request source-backed repair. |

## Forbidden Shortcuts

- Do not infer lifecycle id.
- Do not join by approximate symbol, date, price, or time.
- Do not use future price reaction to resolve conflict.
- Do not convert missing denominator, missing comparator, missing label, or missing context into a negative.
- Do not convert supportive regime, sector, theme, or price acceptance into readiness when upstream source or primitive state is blocked.
- Do not treat `ready_for_gate_review` as backtest eligibility.
- Do not treat test success as strategy acceptance.

## Validation Authority

Task769 validation is diagnostic/research contract validation only.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
