# Same-Timestamp Slot Contract

## Purpose

This contract defines the Task768 future input boundary for same-timestamp slot comparison.

It compares only review quality among candidate bundles that share the same exact timestamp cohort. It does not create a trade action, global rank, slot score, actual size, allocation, portfolio optimizer output, backtest permission, deployment readiness, strategy acceptance, or real-capital permission.

## Layer Boundary

Allowed:

- Consume L4 candidate thesis bundles when upstream ids and timestamps are explicit.
- Compare only candidates inside the same `cohort_id`.
- Use review-only bundle quality dimensions such as trace completeness, thesis clarity, relation coherence, confirmation burden, contradiction load, invalidation visibility, modifier context, weakest layer, and uncertainty state.
- Emit only research review states such as `comparable_review_ready`, `comparable_but_capped`, `review_needed`, `not_comparable`, `source_gap`, or `timestamp_blocked`.
- Preserve disqualifiers and uncertainty without converting missing labels into negatives.

Forbidden:

- No global top5 rank.
- No local or global rank output.
- No slot score or numeric quality score.
- No buy, sell, hold, order, fill, trade permission, or backtest eligibility.
- No actual sizing, allocation, budget, exposure target, or portfolio optimizer.
- No future PnL, future return, future price, realized outcome, win/loss, winner, loser, target label, or post-event field.
- No inferred lifecycle matching.
- No symbol/date/price/time proximity fallback matching.
- No missing source, label, or context converted to a negative.

## Required Object Fields

| Field | Required | Meaning |
| --- | --- | --- |
| `slot_input_id` | yes | Stable id derived from `candidate_bundle_id`, `cohort_id`, exact `entry_ts`, exact `asof_ts`, and contract version. Must not include outcome, return, price reaction, or backtest result. |
| `cohort_id` | yes | Same timestamp comparison group id. Minimum derivation: `split_name` plus exact normalized `entry_ts` plus contract version. It is not a global universe id. |
| `entry_ts` | yes | Exact timestamp used to define same-timestamp comparability. Candidates with different `entry_ts` are not comparable. |
| `asof_ts` | yes | Latest information timestamp allowed for the candidate. It must be less than or equal to the comparison as-of boundary and must not include future outcome information. |
| `candidate_bundle_id` | yes | Upstream L4 bundle id. It must already exist; Task768 does not infer or create bundle identity. |
| `bundle_trace_ids` | yes | Pipe-delimited explicit ids to evidence, primitive fact, meaning object, relation edge, modifier, confirmation, contradiction, and invalidation records when present. |
| `bundle_state` | yes | One of `review_ready`, `capped`, `context_only`, `not_ready`, or `source_gap`. |
| `comparable_candidate_set` | yes | Explicit list or count of bundle ids in the same `cohort_id`. It cannot be created by symbol/date/price/time proximity. |
| `comparison_scope` | yes | Must be `same_entry_ts_cohort_only`. |
| `source_readiness_state` | yes | One of `complete`, `capped`, `timestamp_incomplete`, `stale_context`, or `source_gap`. |
| `relation_quality_state` | yes | One of `coherent`, `mixed`, `contradicted`, `confirmation_required`, `blocked`, or `not_ready`. |
| `modifier_context_state` | yes | One of `supportive`, `hostile`, `rotating`, `extended`, `accepted`, `rejected`, `unclear`, or `none`. |
| `weakest_layer` | yes | Blocking or weakest layer among `L1_Evidence`, `L2_PrimitiveFact`, `L3_MeaningObject`, `L3_RelationEdge`, `L4_CandidateBundle`, `L5_SlotInput`, or `none`. |
| `uncertainty_state` | yes | One of `low`, `capped`, `unclear`, `review_needed`, `source_gap`, `timestamp_blocked`, or `not_comparable`. |
| `slot_review_state` | yes | Research-only output state: `comparable_review_ready`, `comparable_but_capped`, `review_needed`, `not_comparable`, `source_gap`, or `timestamp_blocked`. |
| `disqualifiers` | yes | Pipe-delimited reasons that block comparison or downstream review. Use `none` only when no disqualifier is present. |
| `forbidden_outputs` | yes | Must include `buy_sell`, `rank`, `score`, `slot_score`, `global_top5`, `actual_sizing`, `allocation`, `portfolio_optimizer`, `backtest_eligibility`, `future_pnl`, `trade_permission`, `deployment_readiness`, and `real_capital`. |

## Cohort Identity

`cohort_id` is the only allowed grouping unit for slot comparison.

Minimum form:

```text
cohort::<split_name>::<normalized_entry_ts>::task768_v1
```

Rules:

- `entry_ts` must match exactly after canonical timestamp normalization.
- `asof_ts` must be explicit and no later than the comparison boundary.
- `cohort_id` must not include future return, price move, realized outcome, or selection result.
- A single-symbol cohort is allowed, but it remains review-only and cannot create a trade.
- Candidates outside the exact cohort are not comparable.

## Comparable Candidates

A candidate is comparable only when all conditions hold:

- `candidate_bundle_id` is explicit.
- `cohort_id` is explicit.
- `entry_ts` exactly matches the cohort timestamp.
- `asof_ts` is explicit and as-of safe.
- the bundle has upstream trace ids or explicit source-gap state.
- the bundle state is not `source_gap`, `not_ready`, or `context_only` unless the comparison purpose is repair or context review.
- the requested output is research review state only.

If any condition fails, the output must be `not_comparable`, `source_gap`, `timestamp_blocked`, or `review_needed`.

## Required Bundle Inputs

Future Task768 implementations may consume only these L4 bundle inputs:

- `candidate_bundle_id`
- `thesis_summary`
- `evidence_trace_ids`
- `primitive_fact_ids`
- `meaning_object_ids`
- `relation_edge_ids`
- `modifier_ids`
- `confirmation_needs`
- `contradiction_states`
- `invalidation_links`
- `weakest_layer`
- `missing_context`
- `uncertainty_flags`
- `bundle_state`
- `entry_ts`
- `asof_ts`

Task768 may not create missing L4 fields from price reaction, future outcome, symbol proximity, date proximity, or lifecycle inference.

## Allowed Comparison Dimensions

Allowed dimensions are categorical and explanatory:

| Dimension | Allowed states | Meaning |
| --- | --- | --- |
| source readiness | `complete`, `capped`, `timestamp_incomplete`, `stale_context`, `source_gap` | Whether upstream source trace is usable. |
| trace completeness | `complete`, `partial`, `missing_required`, `source_gap` | Whether required upstream ids are present. |
| thesis clarity | `clear`, `partial`, `ambiguous`, `not_ready` | Whether the bundle explains the reviewed thesis. |
| relation coherence | `coherent`, `mixed`, `contradicted`, `confirmation_required`, `blocked`, `not_ready` | Whether relation edges are reviewable. |
| contradiction load | `none`, `explicit_low`, `explicit_medium`, `explicit_high`, `blocked` | Whether contradictions are visible and bounded. |
| confirmation burden | `none`, `low`, `medium`, `high`, `blocking` | How much confirmation is required. |
| invalidation visibility | `explicit`, `partial`, `missing`, `not_applicable` | Whether failure conditions are known. |
| modifier context | `supportive`, `hostile`, `rotating`, `extended`, `accepted`, `rejected`, `unclear`, `none` | Task765-style context attached to the bundle. |
| weakest layer | `L1_Evidence`, `L2_PrimitiveFact`, `L3_MeaningObject`, `L3_RelationEdge`, `L4_CandidateBundle`, `L5_SlotInput`, `none` | Where review is weakest. |
| uncertainty | `low`, `capped`, `unclear`, `review_needed`, `source_gap`, `timestamp_blocked`, `not_comparable` | Whether uncertainty blocks stronger review. |

No allowed dimension may be converted into a numeric score, rank, size, selection, or trade action.

## Disqualifiers

The slot input must be disqualified from comparison or reduced to repair review when any of these occur:

- exact `entry_ts` mismatch
- missing or future-contaminated `asof_ts`
- missing `cohort_id`
- missing `candidate_bundle_id`
- missing required bundle trace without explicit source-gap state
- `source_gap`, `context_only`, or `not_ready` bundle state for a non-repair comparison
- inferred lifecycle matching
- symbol/date/price/time proximity fallback matching
- future PnL, future return, future price, realized outcome, win/loss, or target label present
- requested output includes buy/sell, rank, score, slot score, actual sizing, allocation, optimizer, trade permission, or backtest eligibility

## Uncertainty Handling

Uncertainty is preserved, not hidden.

- Missing raw source is `source_gap`.
- Missing timestamp is `timestamp_incomplete` or `timestamp_blocked`.
- Stale context is `stale_context`.
- Ambiguous relation or modifier state is `unclear` or `review_needed`.
- Missing label is not a negative.
- Missing comparison peer is not a reason to create a global rank.
- Price strength cannot rescue weak or missing evidence.

## Forbidden Outputs

Task768 output is a future input contract only. It must not emit:

- buy, sell, hold, or trade permission
- global top5 rank
- any rank
- score or slot score
- actual sizing, allocation, or exposure budget
- portfolio optimizer output
- order or fill instruction
- backtest eligibility
- future PnL or realized outcome label
- deployment readiness
- strategy acceptance
- real-capital permission

## Research-Only Status

This contract does not change strategy acceptance, deployment readiness, or real-capital permission.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
