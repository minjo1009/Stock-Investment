# Primitive Gate Repair Contract

## Purpose

This contract defines the minimal Task729 primitive fact gate repair target. It is research-only. It allows Task729 to consume explicit Task761 adapter gate input instead of keeping `primitive_fact_gate_pass = 0` fixed.

This contract does not create trade actions, assignment, score, rank, sizing, PnL, outcome labels, backtest eligibility, deployment readiness, or real-capital permission.

## Input Fields

### Required Minimal Field

| Field | Required | Meaning |
| --- | --- | --- |
| `primitive_fact_adapter_gate_state` | yes for repaired behavior | Explicit gate state from the Task761 adapter. |

### Recommended Trace Fields

| Field | Required | Meaning |
| --- | --- | --- |
| `adapter_packet_id` | when available | Stable adapter packet id. |
| `lifecycle_id` | when available | Lifecycle link supplied upstream; do not infer if missing. |
| `source_event_id` | when available | Source event identity. |
| `primitive_id` | when available | Primitive fact identity. |
| `source_trace` | when available | Source trace or compact trace reference. |
| `adapter_source_task` | when available | Upstream task that emitted the adapter gate, usually Task742 or Task761-derived adapter output. |
| `adapter_source_packet_id` | when available | Stable upstream packet id used for gate audit. |
| `adapter_gate_reason` | when available | Short reason explaining why the adapter emitted pass, cap, context_only, not_ready, or source_gap. |
| `evidence_trace_json` | when available | Structured evidence trail. |
| `relation_ready_tier` | when available | Task742 readiness tier. |
| `confidence_band` | when available | Task742 confidence band. |
| `hard_blocker_flags` | when available | Explicit hard blockers. |
| `needed_confirmation` | when available | Confirmation still required. |
| `adapter_relation_permission` | when available | Adapter permission for relation review, context attachment, or block. |

The repaired Task729 code should not infer missing lifecycle, source, primitive, or gate identity through symbol/date/price/time proximity.

## Gate State Enum

Allowed values:

- `pass`
- `cap`
- `context_only`
- `not_ready`
- `source_gap`

Normalization rules:

- Trim whitespace.
- Lowercase the value.
- If missing, blank, null, or outside the enum, normalize to `not_ready`.
- Do not normalize unknown values to `pass`.
- Do not use market price, return, slot state, or outcome fields to normalize the gate.

## Mapping To Task729 Internal Relation States

| Gate state | `primitive_fact_gate_pass_flag` | Relation state mapping | Dominance rule |
| --- | ---: | --- | --- |
| `pass` | `1` | Preserve source-backed L2/L3 relation review and permit directional relation interpretation when existing edge rules allow it. | Existing blockers, invalidations, and confidence caps still dominate. |
| `cap` | `0` | Map to confidence-cap, confirmation-needed, invalidation, or hard-blocker review state. | Cap cannot be overridden by positive direction hint. |
| `context_only` | `0` | Map to context attachment only. | Cannot create directional relation edge. |
| `not_ready` | `0` | Map to primitive repair-needed or `RESEARCH_ONLY_NEEDS_PRIMITIVE_FACTS`. | Cannot be rescued by price acceptance. |
| `source_gap` | `0` | Map to source-gap repair or source-gap blocker. | Must dominate over price, slot, and direction hints. |

Recommended visible output:

- Keep existing `primitive_fact_gate_pass_flag`.
- Add `primitive_fact_gate_state` if implementation tests need traceability.

Required constant outputs:

- `interaction_engine_assignment_allowed_flag = 0`
- `backtest_eligible_flag = 0`
- `real_capital_status = FORBIDDEN`

## Default Behavior If Missing

If `primitive_fact_adapter_gate_state` is missing from the input row:

```text
primitive_fact_gate_state = not_ready
primitive_fact_gate_pass_flag = 0
```

This default preserves the current conservative behavior without keeping the hard-coded gate permanently closed for valid adapter packets.

## Guardrails

- No gate state may create backtest eligibility by itself.
- No gate state may create buy, sell, hold, rank, score, sizing, allocation, PnL, return, win/loss, or outcome labels.
- `pass` is not strategy acceptance.
- `pass` is not deployment readiness.
- `pass` is not real-capital permission.
- `cap`, `context_only`, `not_ready`, and `source_gap` cannot become directional edges through price behavior.
- Missing labels are never negatives.
- Missing raw sources are reported as gaps, not approximated.
- Labels/outcomes are evaluation-only and must not enter assignment logic.
- Direction hints are review metadata, not trade instructions.
- Existing source-gap, blocker, invalidation, and confidence-cap edge priority remains authoritative.

## Code-Touch Boundary

Later implementation may change only this gate path in `src/backtest/five_layer_interaction_engine.py`:

- `resolve_candidate()`
- `final_actionability()`
- A small helper near `state()` for gate normalization.

Later implementation must not rewrite:

- `evaluate_interaction_frame()`
- `evaluate_candidate_edges()`
- `l1_l2_evidence_gate()`
- `l1_l2_source_economic_contradiction()`
- `l2_l3_thesis_confirmation()`
- `l2_l5_thesis_invalidation()`
- `l3_l4_slot_adjustment()`
- `l4_l5_budget_interaction()`
- `all_layer_final_gate()`
- `positive_economic()`
- `is_stale_or_reaffirmed()`
- `make_edge()`

The builder and historical artifact generation should remain untouched unless a separate parent task explicitly scopes them.

## Test Expectations

Focused tests for the later implementation should cover:

1. Missing `primitive_fact_adapter_gate_state` defaults to `not_ready` and flag `0`.
2. Invalid gate state defaults to `not_ready` and flag `0`.
3. `pass` sets `primitive_fact_gate_pass_flag = 1` while `backtest_eligible_flag` remains `0`.
4. `cap` leaves the pass flag `0` and preserves confidence-cap, blocker, or invalidation dominance.
5. `context_only` leaves the pass flag `0` and cannot create directional relation output.
6. `source_gap` leaves the pass flag `0` and cannot be rescued by price acceptance.
7. Hard blocker flags prevent a positive direction hint from becoming a pass.
8. Final actionability text remains research-only and does not imply actual approval.

## Acceptance Examples

| Example | Minimal row condition | Expected output |
| --- | --- | --- |
| Directional pass | `primitive_fact_adapter_gate_state=pass`, direct source trace, primitive id, high/medium confidence, no hard blocker. | Primitive flag `1`; review-only relation readiness; no backtest eligibility. |
| Structural cap | `primitive_fact_adapter_gate_state=cap`, structural mixed ownership/control meaning. | Primitive flag `0`; confidence cap or modifier review. |
| Context-only | `primitive_fact_adapter_gate_state=context_only`, filing or insider context without source-backed directional path. | Primitive flag `0`; context attachment only. |
| Not-ready | `primitive_fact_adapter_gate_state=not_ready` or missing field. | Primitive flag `0`; needs primitive facts. |
| Source-gap | `primitive_fact_adapter_gate_state=source_gap`, missing source trace or primitive id. | Primitive flag `0`; source-gap blocked or repair-needed. |
| Hard-blocker cap/block | `primitive_fact_adapter_gate_state=cap`, hard blocker or financing overhang present. | Primitive flag `0`; blocker/invalidation remains dominant. |

## Validation Authority

This is diagnostic/research contract validation only.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
