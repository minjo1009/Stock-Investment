# Modifier Contracts

## Purpose

Task765 defines a research-only Modifier object for market regime, sector leadership, theme rotation, price acceptance, extension risk, and exposure cluster context.

A modifier attaches to source-backed L2/L3 meaning or an existing relation-review packet. It cannot create a candidate by itself.

## Layer Boundary

Allowed:

- Reinforce existing L2/L3 meaning when source and primitive gates already permit relation review.
- Cap confidence when context is hostile, extended, crowded, uncertain, or rotating without confirmation.
- Block relation use when a required modifier state is rejected or source/as-of integrity fails.
- Require confirmation before stronger relation use.
- Attach context to the relation packet.
- Link a modifier to an invalidation path.

Forbidden:

- Buy, sell, hold, rank, score, sizing, allocation, candidate creation, portfolio budget, order, fill, backtest eligibility, deployment readiness, or real-capital permission.
- Regime-only, sector-only, theme-only, or price-only candidate creation.
- Price equals meaning.
- Future return, PnL, win/loss, outcome, or label fields.
- Inferred lifecycle matching.
- Symbol/date/price/time proximity fallback matching.
- Missing labels treated as negatives.
- Rescue of `source_gap`, `context_only`, or `not_ready` primitive states.

## Required Object Fields

| Field | Required | Meaning |
| --- | --- | --- |
| `modifier_id` | yes | Stable modifier id derived from explicit upstream ids, modifier family, state, as-of timestamp, and contract version. |
| `modifier_family` | yes | One of `market_regime`, `sector_leadership`, `theme_rotation`, `price_acceptance`, `extension_risk`, or `exposure_cluster`. |
| `state` | yes | One of `supportive`, `hostile`, `rotating`, `extended`, `accepted`, `rejected`, or `unclear`. |
| `source_inputs` | yes | Pipe-delimited explicit upstream fields or artifact ids used to assign the state. Must not include future returns or outcomes. |
| `asof_state` | yes | `as_of_known`, `timestamp_incomplete`, `source_gap`, or `stale_context`. |
| `applies_to_layer` | yes | Target review layer such as `L2xL3`, `L3xL4`, `L4xL5`, or `relation_edge`. |
| `relation_effect` | yes | One of `reinforcing`, `offsetting`, `prerequisite`, `blocker`, `confidence_cap`, or `invalidation`. |
| `confidence_cap` | yes | `none`, `low`, `medium`, `high`, or `block`. This is a review confidence cap, not position sizing. |
| `invalidation_link` | yes | Explicit invalidation path id, condition text, or `none`. Must identify what would weaken or block the modifier. |
| `allowed_effect` | yes | Pipe-delimited research-only effects from the allowed effect catalog below. |
| `forbidden_effects` | yes | Must include `buy_sell`, `rank_score`, `sizing_allocation`, `candidate_creation`, `backtest_eligibility`, `deployment_readiness`, `real_capital`, and `outcome_assignment`. |

## Modifier Families

| Modifier family | Purpose | Main distinction |
| --- | --- | --- |
| `market_regime` | Broad tape, macro/liquidity/risk appetite context. | Good market or bad market is broad participation context, not sector rotation. |
| `sector_leadership` | Whether the issuer's sector is leading, fading, or unclear. | Sector leadership can support or cap a source-backed thesis, but cannot create one. |
| `theme_rotation` | Whether theme participation is expanding, fading, rotating, or unclear. | Theme rotation is flow/participation context, not the same as broad market regime. |
| `price_acceptance` | Whether market price has accepted, rejected, or not confirmed the source-backed meaning. | Price acceptance confirms or questions meaning; price is not meaning. |
| `extension_risk` | Whether price/context is stretched enough to cap confidence or require absorption. | Extension is a cap or confirmation need, not a bullish signal. |
| `exposure_cluster` | Same-theme, same-relation, or same-timestamp concentration context. | Cluster exposure can cap relation review but cannot size a position. |

## Allowed Effect Catalog

| Allowed effect | Meaning |
| --- | --- |
| `reinforce_existing_meaning` | Existing L2/L3 meaning and modifier context align. |
| `cap_confidence` | Relation review remains possible but confidence is capped. |
| `block_relation_use` | Modifier state blocks relation use until repaired or invalidation clears. |
| `require_confirmation` | More current confirmation is required before stronger relation use. |
| `attach_context_only` | Modifier is explanatory context only. |
| `link_invalidation` | Modifier provides an explicit invalidation or failure condition. |

## State Semantics

| State | Default relation effect | Default confidence cap | Meaning |
| --- | --- | --- | --- |
| `supportive` | `reinforcing` | `none` | Context supports already-source-backed L2/L3 meaning. |
| `hostile` | `offsetting` | `medium` | Context works against the meaning or demands a lower-confidence review state. |
| `rotating` | `prerequisite` | `medium` | Participation is moving; sector/theme confirmation is needed before stronger use. |
| `extended` | `confidence_cap` | `high` | Price/context is stretched; absorption or reset is required. |
| `accepted` | `reinforcing` | `none` | Price or participation confirms an existing meaning without creating meaning. |
| `rejected` | `blocker` | `block` | Price, participation, or source/as-of context rejects the modifier path. |
| `unclear` | `prerequisite` | `medium` | Context is ambiguous and must remain confirmation-needed or context-only. |

## Primitive Gate Interaction

Modifier behavior is subordinate to L2/L3 source and primitive gates.

| Primitive gate state | Modifier behavior |
| --- | --- |
| `pass` | Modifier may reinforce, cap, block, require confirmation, or attach context. |
| `cap` | Modifier may preserve or tighten the cap; it may not convert cap to pass. |
| `context_only` | Modifier may attach context only; it may not create a directional relation edge. |
| `not_ready` | Modifier may note missing confirmation only; it may not rescue the packet. |
| `source_gap` | Modifier is blocked for directional relation use; price, regime, sector, or theme cannot rescue it. |

## As-Of And Source Rules

- Use only current as-of-safe source inputs supplied by upstream artifacts.
- Do not infer lifecycle links when missing.
- Do not match by symbol/date/price/time proximity.
- Do not use price moves to fill missing primitive facts.
- Do not treat missing leadership, missing price acceptance, or missing labels as negative evidence.
- Report raw source and timestamp gaps as `source_gap`, `timestamp_incomplete`, `stale_context`, or `unclear`.

## Research-Only Status

This contract does not change strategy acceptance, deployment readiness, or real-capital permission.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
