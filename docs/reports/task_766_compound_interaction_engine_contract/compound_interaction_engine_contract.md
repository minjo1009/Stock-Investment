# Compound Interaction Engine Contract

## Purpose

Task766 defines the research-only compound interaction contract for the Trader Brain program.

The compound engine combines explicit upstream `PrimitiveFact`, `MeaningObject`, `RelationEdge`, and `Modifier` packets into one explanatory output field:

```text
compound_state
```

The output explains review state only. It is not a score engine, ranking engine, sizing engine, slot engine, backtest gate, buy/sell model, or deployment gate.

## Inputs

### PrimitiveFact

Required when available from Task759:

- `primitive_fact_id`
- `evidence_id`
- `source_event_id`
- `issuer_symbol`
- `source_form_family`
- `source_circuit`
- `as_of_ts`
- `as_of_state`
- `source_trace_state`
- `raw_source_available_flag`
- `fact_family`
- `fact_type`
- `fact_value`
- `extraction_confidence`
- `uncertainty_flags`
- `missing_required_context`
- `join_blocker_state`
- `review_state`
- `directional_signal_created_flag`
- `rank_created_flag`
- `sizing_created_flag`
- `backtest_eligible_flag`
- `outcome_used_for_assignment_flag`

Use rules:

- Primitive facts are source-local facts only.
- Extraction confidence is source extraction confidence, not trade confidence.
- Missing primitive facts create uncertainty, `not_ready`, or `source_gap`; they are not negative labels.

### MeaningObject

Required when available from Task760:

- `meaning_object_id`
- `source_event_id`
- `evidence_id`
- `primitive_fact_id`
- `source_form_family`
- `source_circuit`
- `meaning_state`
- `economic_direction_hint`
- `confidence_band`
- `ambiguity`
- `soft_blockers`
- `hard_blockers`
- `needed_confirmation`
- `relation_ready_tier`
- `relation_ready_reason`
- `invalidation_clue`
- `forbidden_effects`

Use rules:

- Direction hints are review metadata only.
- `relation_ready_tier=directional` is not backtest eligibility.
- `context_only` and `not_ready` cannot be converted to directional states by price, macro, regime, sector, or theme support.

### RelationEdge

Required when available from Task763:

- `edge_id`
- `source_node`
- `target_node`
- `relation_type`
- `preconditions`
- `confidence_cap`
- `evidence_trace`
- `primitive_gate_state`
- `meaning_state`
- `modifier_inputs`
- `invalidation_link`
- `allowed_effect`
- `forbidden_effects`

Allowed `relation_type` values:

- `reinforcing`
- `offsetting`
- `prerequisite`
- `blocker`
- `sizing_modifier`
- `confidence_cap`
- `invalidation`

Use rules:

- `sizing_modifier` means review-only cap or exposure context. It does not mean actual position sizing.
- Relation edges explain interaction effects; they do not emit actions.
- Blocker, cap, prerequisite, and invalidation edges dominate reinforcing edges when their preconditions are explicit.

### Modifier

Required when available from Task765:

- `modifier_id`
- `modifier_family`
- `state`
- `source_inputs`
- `asof_state`
- `applies_to_layer`
- `relation_effect`
- `confidence_cap`
- `invalidation_link`
- `allowed_effect`
- `forbidden_effects`

Allowed modifier families:

- `market_regime`
- `sector_leadership`
- `theme_rotation`
- `price_acceptance`
- `extension_risk`
- `exposure_cluster`

Use rules:

- Modifiers attach to source-backed meaning or existing relation review only.
- Modifiers may reinforce, cap, block, require confirmation, attach context, or link invalidation.
- Modifiers must not accumulate numerically.
- Supportive modifiers cannot rescue `source_gap`, `context_only`, `not_ready`, blocker, cap, or invalidation states.
- Macro, policy, sector, regime, theme, or price support cannot rescue missing raw source or primitive trace.

## Output Contract

The compound engine emits `compound_state` only as its decision-like output.

Allowed supporting audit fields may be carried only for provenance:

- `compound_state_reason`
- `dominant_relation_type`
- `dominant_rule_family`
- `blocking_trace_ids`
- `cap_trace_ids`
- `confirmation_trace_ids`
- `invalidation_trace_ids`
- `source_trace_ids`
- `contract_version`

These audit fields are not scores, ranks, decisions, or eligibility flags.

## Compound State Enum

| `compound_state` | Meaning |
| --- | --- |
| `source_gap_blocked` | Source trace, raw source, primitive id, adapter id, or required provenance is missing. |
| `hard_blocked` | Explicit source-backed blocker prevents relation use. |
| `invalidated` | Explicit invalidation edge or modifier invalidates the relation path. |
| `not_ready` | Required primitive, meaning, precondition, timestamp, or confirmation is unavailable. |
| `context_only` | Evidence is retained context but cannot create directional relation review. |
| `confidence_capped` | Source, primitive, meaning, denominator, modifier, or relation cap limits interpretation. |
| `confirmation_required` | Prerequisite exists and must be satisfied before stronger relation use. |
| `contradictory` | Source-backed offsetting relation creates unresolved contradiction. |
| `reinforced_review` | Source-backed meaning and relation/modifier support align after higher-priority blockers are absent. |
| `review_ready` | Required source, primitive, meaning, relation, and modifier prerequisites are present with no blocker, cap, contradiction, or invalidation. |

`review_ready` is still research-only. It is not buy/sell, rank, sizing, slot selection, backtest eligibility, deployment readiness, or real-capital permission.

## State Precedence

The engine must resolve states by highest-priority condition first:

1. `source_gap_blocked`
2. `hard_blocked`
3. `invalidated`
4. `not_ready`
5. `context_only`
6. `confidence_capped`
7. `confirmation_required`
8. `contradictory`
9. `reinforced_review`
10. `review_ready`

Precedence rules:

- `source_gap` dominates every modifier, relation, and price state.
- `hard_blocked` dominates reinforcing relations and supportive modifiers.
- `invalidated` dominates reinforcement even when the primitive gate is `pass`.
- `not_ready` cannot become ready through price acceptance, macro support, sector leadership, or theme rotation.
- `context_only` can attach context only.
- `confidence_capped` can be preserved or tightened but not converted to pass by positive direction hints.
- `confirmation_required` stays pending until the explicit prerequisite is present.
- Reinforcing states are used only after higher-priority blockers, caps, prerequisites, contradictions, and invalidations are absent.

## Handling Rule Families

### Blocker

Blockers emit `hard_blocked` unless the blocker is specifically a missing source trace, in which case emit `source_gap_blocked`.

Blockers cannot be overridden by:

- supportive modifier
- price acceptance
- sector leadership
- broad market regime
- macro or policy tailwind
- positive economic direction hint

### Cap

Caps emit `confidence_capped`.

Caps may be tightened by hostile, extended, unclear, or rejected modifiers. Caps may not be relaxed by supportive modifiers unless a later explicit source-backed repair packet removes the cap.

The engine must not sum caps or convert cap count into a score.

### Prerequisite

Prerequisites emit `confirmation_required` until the explicit required condition is present.

Prerequisites may include:

- company-specific macro transmission
- customer identity or duration
- use-of-proceeds and dilution bridge
- price acceptance after source-backed meaning
- sector/theme confirmation
- invalidation trace

Missing prerequisites are not negative labels.

### Reinforcing

Reinforcing emits `reinforced_review` only when:

- primitive gate is `pass`
- source trace is not `source_gap`
- relation-ready tier is not `context_only` or `not_ready`
- no higher-priority blocker, cap, prerequisite, contradiction, or invalidation is active
- modifier support, if present, attaches to existing source-backed meaning

Reinforcement is explanatory. It is not a score, rank, buy/sell recommendation, slot, sizing, or backtest gate.

### Sizing Modifier

`sizing_modifier` is a legacy relation type name with a restricted Task766 meaning:

```text
review_only_cap_modifier
```

It can record exposure, cluster, concentration, extension, or budget-review context. It must never output actual size, allocation, capital budget, order quantity, slot weight, or risk budget approval.

## Provenance Requirements

Every `compound_state` must preserve enough trace to audit why the state was emitted:

- source evidence trace
- primitive fact trace
- meaning object trace
- relation edge ids
- modifier ids
- primitive gate state
- as-of timestamp fields supplied upstream
- dominant blocker, cap, prerequisite, contradiction, or invalidation trace where applicable

Forbidden provenance behavior:

- Do not infer lifecycle id when missing.
- Do not match rows by symbol/date/price/time proximity.
- Do not approximate unavailable raw sources.
- Do not use labels, outcomes, future returns, or future prices for state assignment.

## Forbidden Outputs

The compound engine must never emit:

- score
- single total score
- numeric accumulated modifier value
- rank
- buy/sell/hold
- long/short
- slot decision
- actual position sizing
- allocation
- capital budget
- order instruction
- fill expectation
- backtest eligibility
- deployment readiness
- real-capital permission
- future return
- PnL
- win/loss
- outcome label
- inferred lifecycle match
- symbol/date/price/time fallback match

Explicit forbidden shortcuts:

- No price equals meaning.
- No macro rescue of `source_gap`.
- No sector, theme, regime, or price rescue of `context_only` or `not_ready`.
- No supportive modifier rescue of a blocker.
- No modifier numeric accumulation.
- No `sizing_modifier` as actual sizing.

## Validation Authority

Task766 validation is diagnostic and research-only.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
