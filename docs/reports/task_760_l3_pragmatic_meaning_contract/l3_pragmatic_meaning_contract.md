# L3 Pragmatic Meaning Contract

## Purpose

L3 converts source-local primitive facts into practical economic meaning for review. It does not convert meaning into a trade, rank, score, size, assignment, backtest gate, or capital permission.

The contract is intentionally pragmatic. It allows good-enough interpretation from current retained evidence and primitives while keeping uncertainty explicit.

## Layer Boundary

Allowed:

- Interpret source-local primitives into a review meaning state.
- Preserve source circuit, primitive references, evidence trace, confidence, ambiguity, and confirmation needs.
- Emit direction hints as review metadata only.
- Mark relation readiness as `directional`, `structural_mixed`, `context_only`, or `not_ready`.
- Preserve missing context as uncertainty or blocker state.
- Emit invalidation clues for later relation review.

Forbidden:

- Buy, sell, hold, rank, score, sizing, allocation, candidate assignment, backtest eligibility, or real-capital permission.
- Outcome, return, PnL, win/loss, future price, or label fields.
- Inferred lifecycle matching.
- Symbol/date/price/time proximity fallback matching.
- Missing context to negative conversion.
- Direction hint as trade instruction.
- Price rescue of weak or missing source evidence.

## MeaningObject Required Fields

| Field | Required | Meaning |
| --- | --- | --- |
| `meaning_object_id` | yes | Stable L3 object id. |
| `lifecycle_id` | when available | Upstream lifecycle id. Blank remains uncertainty and cannot be inferred by proximity. |
| `source_event_id` | yes | Source event id from L1/L2 trace. |
| `evidence_id` | when available | L1 evidence packet id. |
| `issuer_symbol` | yes | Source-attached symbol only. Not a matching fallback key. |
| `event_date` | when available | Source event date from upstream evidence. |
| `tradable_after_dt` | when available | As-of-safe review timestamp from upstream evidence. |
| `primitive_fact_id` | when available | L2 primitive id. Missing id creates uncertainty or source-gap handling. |
| `primitive_source_task` | yes | Current source of primitive trace such as `Task740` or future `Task759`. |
| `primitive_rule_id` | when available | Rule id that extracted the primitive fact. |
| `primitive_fact_family` | yes | Source-local fact family such as financing, guidance, Form4, ownership, margin, demand, supply, contract, or macro policy. |
| `primitive_as_of_ts` | when available | Timestamp used for as-of safety. |
| `primitive_evidence_span_ref` | when available | Evidence span, raw path, or source trace reference. |
| `primitive_extraction_confidence` | yes | Extraction confidence from L2 or `unknown` when not provided. |
| `source_form_family` | yes | Normalized source family. |
| `source_circuit` | yes | Source circuit used for interpretation. |
| `meaning_state` | yes | Good-enough economic meaning state from `meaning_taxonomy.csv` or a documented circuit extension. |
| `economic_direction_hint` | yes | `positive`, `negative`, `neutral`, `mixed`, or `unknown`. Review metadata only. |
| `confidence_band` | yes | `high`, `medium`, `low`, or `insufficient`. |
| `ambiguity` | yes | Pipe-delimited ambiguity flags or blank. |
| `soft_blockers` | yes | Missing or weak context that limits confidence but does not force hard rejection. |
| `hard_blockers` | yes | Source, primitive, as-of, or trace failures that block relation readiness. |
| `needed_confirmation` | yes | Confirmation needed before stronger relation use. |
| `relation_ready_tier` | yes | `directional`, `structural_mixed`, `context_only`, or `not_ready`. |
| `relation_ready_reason` | yes | Human-readable reason for the tier. |
| `invalidation_clue` | yes | What would weaken or invalidate the meaning. |
| `forbidden_effects` | yes | Must include `buy_sell`, `score_rank`, `sizing`, `assignment`, `backtest_ready`, `real_capital`, and `outcome_label`. |
| `direction_hint_trade_instruction_flag` | yes | Must be `0`. |
| `assignment_allowed_flag` | yes | Must be `0`. |
| `score_output_flag` | yes | Must be `0`. |
| `backtest_eligible_flag` | yes | Must be `0`. |
| `outcome_used_for_assignment_flag` | yes | Must be `0`. |

## Direction Hint Semantics

`economic_direction_hint` is a review label for economic interpretation, not an action.

Allowed meanings:

- `positive`: Source-local facts suggest favorable economic transmission.
- `negative`: Source-local facts suggest unfavorable economic transmission.
- `neutral`: Source-local facts are context with no directional pressure.
- `mixed`: Source-local facts can reinforce and constrain at the same time.
- `unknown`: Current facts do not support a direction.

Forbidden meanings:

- Buy or sell recommendation.
- Ranking or score.
- Position sizing.
- Backtest eligibility.
- Assignment eligibility.

## Relation-Ready Tiers

| Tier | Meaning | Allowed downstream use | Forbidden downstream use |
| --- | --- | --- | --- |
| `directional` | Positive or negative meaning has medium/high confidence and no hard blocker. | May feed Task761 relation-edge review and Task762 gate design. | Cannot become buy/sell/rank/sizing/backtest eligibility. |
| `structural_mixed` | Mixed meaning has medium/high confidence and no hard blocker. | May feed modifier, cap, or special-situation relation review. | Cannot become a directional edge by itself. |
| `context_only` | Context is useful but not directional. | May attach context to a relation packet. | Cannot create a directional relation edge. |
| `not_ready` | Meaning lacks sufficient trace, confidence, or relation readiness. | May create repair, source-gap, or review-needed state. | Cannot create relation edge, assignment, or backtest gate. |

## Good-Enough Interpretation Rule

L3 should not demand every possible denominator before preserving practical meaning. It should use current data only and carry missing pieces as explicit uncertainty.

Examples:

- Growth financing can be positive review metadata when amount and growth use are visible, even if exact market-cap scale is missing.
- Survival funding or refinancing can be mixed review metadata when liquidity or refinance language is visible.
- Dilution overhang can be negative review metadata when convertible, warrant, ATM, shelf, or dilution language is visible.
- Planned Form 4 sales remain context rather than automatic negative meaning.
- Non-plan insider sales can be negative context when transaction type and plan status are visible.
- Passive ownership is context. Active/control language is structural mixed.
- Macro/policy evidence is context unless company-specific transmission is visible.

## Task759 Primitive Consumption

Task760 accepts future Task759 primitives through explicit primitive fields only. If Task759 is unavailable, current Task740 primitive trace may be used as the primitive reference source, with `primitive_source_task = Task740`.

Required behavior:

- Do not infer missing primitive facts from price behavior.
- Do not infer lifecycle links from symbol/date/price/time proximity.
- Do not treat missing L2 fields as negative facts.
- Do not convert extraction confidence into trade confidence.

## Task761 And Task762 Handoff

Task760 may feed Task761/762 with:

- identity and trace fields
- `meaning_state`
- `economic_direction_hint`
- `confidence_band`
- `relation_ready_tier`
- `ambiguity`
- `soft_blockers`
- `hard_blockers`
- `needed_confirmation`
- `invalidation_clue`

Task761 may adapt these into relation-engine review fields. Task762 may design primitive gate states from explicit source and primitive readiness. Neither task may use L3 meaning to create buy/sell/rank/sizing/backtest eligibility.

## Required Guardrail Values

```text
direction_hint_trade_instruction_flag = 0
assignment_allowed_flag = 0
score_output_flag = 0
backtest_eligible_flag = 0
outcome_used_for_assignment_flag = 0
real_capital = FORBIDDEN
```

## Research-Only Status

This contract does not change strategy acceptance, deployment readiness, or real-capital permission.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
