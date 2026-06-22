# Typed Relation Edge Schema

## Purpose

`RelationEdge` is the Task763 L3 relation-edge object for the Task756 Trader Brain program.

It connects two typed review nodes and explains whether their relationship is reinforcing, offsetting, prerequisite, blocker, sizing modifier, confidence cap, or invalidation.

It is research-only. It cannot emit buy/sell, rank, score, sizing, allocation, assignment, backtest eligibility, deployment readiness, or real-capital permission.

## Boundary

Allowed:

- Consume Task759 `PrimitiveFact` trace fields.
- Consume Task760 `MeaningObject` review fields.
- Consume Task762 `primitive_gate_state`.
- Preserve explicit preconditions, confidence caps, modifier inputs, invalidation links, and evidence traces.
- Explain relation review effects such as `review_allowed`, `context_attachment`, `confidence_capped`, `confirmation_required`, `blocked`, or `invalidation_trace_required`.

Forbidden:

- No code promotion.
- No strategy claim.
- No buy/sell/rank/score/sizing/backtest eligibility.
- No future returns, outcomes, PnL, win/loss, or labels in edge creation.
- No inferred lifecycle matching.
- No symbol/date/price/time fallback matching.
- No missing source/context to negative conversion.
- No giant brittle if/else tree.

## Required Object Fields

| Field | Required | Meaning |
| --- | --- | --- |
| `edge_id` | yes | Stable edge id derived from source node id, target node id, relation type, evidence trace id, and schema version. It must not use outcome, return, price reaction, or backtest result. |
| `source_node` | yes | Typed source node object. Minimum fields: `node_id`, `node_layer`, `node_type`, `node_state`, `source_task`. |
| `target_node` | yes | Typed target node object. Minimum fields: `node_id`, `node_layer`, `node_type`, `node_state`, `source_task`. |
| `relation_type` | yes | One of `reinforcing`, `offsetting`, `prerequisite`, `blocker`, `sizing_modifier`, `confidence_cap`, or `invalidation`. |
| `preconditions` | yes | Explicit source-backed conditions that must be true before the edge can be reviewed. Missing preconditions remain missing or not-ready; they are not negative labels. |
| `confidence_cap` | yes | Confidence limit for the edge: `none`, `low`, `medium`, `high`, or a structured cap reason. A cap limits interpretation only; it is not a score. |
| `evidence_trace` | yes | Structured trace to L1/L2/L3 inputs. Minimum fields: `evidence_id`, `source_event_id`, `primitive_fact_id`, `meaning_object_id`, `adapter_packet_id`, `source_trace_state`, `as_of_ts`. |
| `primitive_gate_state` | yes | Task762 gate state: `pass`, `cap`, `context_only`, `not_ready`, or `source_gap`. |
| `meaning_state` | yes | Task760 pragmatic meaning state or documented extension. It remains review metadata and cannot create a trade instruction. |
| `modifier_inputs` | yes | Structured modifier packet for regime, sector, price acceptance, ownership, dilution, cluster, or confirmation context. Empty is allowed as `none`. |
| `invalidation_link` | yes | Explicit clue or condition that weakens or falsifies the relation. Use `invalidation_trace_required` if not yet known. |
| `allowed_effect` | yes | Research-only effect such as `relation_review_allowed`, `context_attachment_allowed`, `modifier_review_allowed`, `confidence_capped`, `confirmation_required`, `blocked`, or `invalidation_trace_required`. |
| `forbidden_effects` | yes | Must include `buy_sell`, `rank`, `score`, `sizing`, `allocation`, `assignment`, `backtest_eligibility`, `deployment_readiness`, `real_capital`, and `outcome_assignment`. |

## Source Node And Target Node Shape

Minimum typed node shape:

```text
node_id
node_layer
node_type
node_state
source_task
trace_ref
as_of_ts
```

Allowed `node_layer` values:

- `L1_Evidence`
- `L2_PrimitiveFact`
- `L3_MeaningObject`
- `L3_RelationEdge`
- `L4_CandidateBundle`
- `L5_RiskReview`
- `Modifier`

Task763 should normally create edges among L2, L3, modifier, and invalidation review nodes. L4/L5 references are allowed only as review targets and cannot create candidate assignment, rank, size, or backtest eligibility.

## Relation Type Semantics

| Relation type | Meaning | Allowed effect | Forbidden promotion |
| --- | --- | --- | --- |
| `reinforcing` | Source and target states support the same review thesis. | May mark relation review as coherent or promising. | Cannot create buy/sell, rank, score, sizing, or backtest eligibility. |
| `offsetting` | Source and target states conflict or reduce each other. | May reduce confidence or require review. | Cannot become a negative label or sell signal. |
| `prerequisite` | Target review depends on a source-backed condition. | May require confirmation before stronger relation use. | Cannot infer readiness from price, slot, or outcome. |
| `blocker` | Explicit source-backed condition blocks relation promotion. | May block relation review or require repair. | Cannot convert missing context into a negative label. |
| `sizing_modifier` | Risk or exposure context describes a review-only cap reason. | May record a cap reason for later review. | Cannot emit actual size, allocation, or budget approval. |
| `confidence_cap` | Evidence, trace, ambiguity, or denominator gap limits confidence. | May cap confidence band or require confirmation. | Cannot become pass because direction hint is positive. |
| `invalidation` | Explicit condition would weaken or falsify the relation. | May attach invalidation trace. | Cannot use future outcome or return as the invalidation source. |

## Task759 Consumption

Task763 consumes Task759 only through explicit primitive fields:

- `primitive_fact_id`
- `evidence_id`
- `source_event_id`
- `issuer_symbol`
- `source_form_family`
- `source_circuit`
- `as_of_ts`
- `source_trace_state`
- `fact_family`
- `fact_type`
- `fact_value`
- `extraction_confidence`
- `uncertainty_flags`
- `missing_required_context`
- `join_blocker_state`
- `review_state`

Allowed use:

- Populate `evidence_trace`.
- Populate typed L2 `source_node` or `target_node`.
- Populate `preconditions`, `confidence_cap`, or `modifier_inputs`.

Forbidden use:

- Do not turn primitive facts into economic meaning inside Task763.
- Do not treat missing primitive context as a negative fact.
- Do not derive edge readiness from symbol/date/price/time proximity.

## Task760 Consumption

Task763 consumes Task760 only through explicit meaning fields:

- `meaning_object_id`
- `primitive_fact_id`
- `meaning_state`
- `economic_direction_hint`
- `confidence_band`
- `ambiguity`
- `soft_blockers`
- `hard_blockers`
- `needed_confirmation`
- `relation_ready_tier`
- `invalidation_clue`
- `forbidden_effects`

Allowed use:

- Populate L3 typed nodes.
- Populate `meaning_state`.
- Convert `hard_blockers`, `soft_blockers`, and `needed_confirmation` into relation preconditions, caps, blockers, or invalidation links.
- Preserve `economic_direction_hint` as review metadata only.

Forbidden use:

- Do not convert direction hints into trade instructions.
- Do not convert confidence bands into scores or ranks.
- Do not treat `relation_ready_tier=directional` as backtest eligibility.

## Task762 Consumption

Task763 consumes Task762 through `primitive_gate_state`.

Gate behavior:

- `pass`: permits source-backed relation review when all other edge preconditions allow it.
- `cap`: requires confidence cap, modifier, confirmation, or invalidation review.
- `context_only`: allows context attachment only.
- `not_ready`: blocks relation edge creation except repair or needs-review edge.
- `source_gap`: blocks relation review and preserves source-gap repair state.

`pass` only means primitive review can proceed. It does not create buy/sell, rank, score, sizing, assignment, backtest eligibility, deployment readiness, or real-capital permission.

## Edge Creation Stop Rules

Create a relation edge only when:

- both nodes have explicit ids or source-gap state is the edge subject;
- the relation type is in the catalog;
- `evidence_trace` is populated from upstream ids or explicitly says `source_gap`;
- `primitive_gate_state` is present or normalized to `not_ready`;
- `allowed_effect` is research-only;
- all forbidden effect flags remain active.

Do not create a relation edge when:

- the only link is shared symbol, date, price, timestamp, or proximity;
- the only support is a future price move, return, PnL, or outcome label;
- the source node is missing and there is no explicit source-gap repair edge;
- the edge would require enumerating an unbounded world-state if/else tree.

## Example Edge Packet

```text
edge_id: edge:meaning_growth_funding:price_acceptance:confidence_cap:v1
source_node: {node_layer=L3_MeaningObject, node_type=financing_meaning, node_state=financing_growth_funding_size_known, source_task=Task760}
target_node: {node_layer=Modifier, node_type=price_acceptance, node_state=accepted_or_building, source_task=Task765_future}
relation_type: prerequisite
preconditions: operating_catalyst_alignment; price_acceptance_after_result
confidence_cap: medium_until_confirmation
evidence_trace: evidence_id, source_event_id, primitive_fact_id, meaning_object_id, adapter_packet_id, as_of_ts
primitive_gate_state: pass
meaning_state: financing_growth_funding_size_known
modifier_inputs: price_acceptance=building; dilution_overhang=none_visible
invalidation_link: invalid_if_growth_use_not_confirmed
allowed_effect: confirmation_required
forbidden_effects: buy_sell|rank|score|sizing|allocation|assignment|backtest_eligibility|deployment_readiness|real_capital|outcome_assignment
```

## Research-Only Status

This schema does not change strategy acceptance, deployment readiness, or real-capital permission.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
