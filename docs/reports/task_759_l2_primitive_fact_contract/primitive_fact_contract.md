# PrimitiveFact Contract

## Purpose

`PrimitiveFact` is the L2 object for source-local factual extraction in the Task756 Trader Brain program.

It receives retained L1 evidence and emits factual, non-directional rows that later layers can review. It does not emit economic meaning, relation edges, candidates, ranks, sizing, orders, or backtest eligibility.

## Boundary

Allowed:

- Preserve source-local facts visible in an evidence span or raw source reference.
- Normalize factual values when the source text supports normalization.
- Preserve extraction uncertainty and unresolved joins.
- Preserve good-enough facts without requiring every possible denominator.
- Feed Task760 and Task762 as research-only inputs.

Forbidden:

- Buy, sell, hold, rank, sizing, allocation, portfolio, order, or backtest eligibility.
- Economic promotion inside primitive extraction.
- Missing fact to negative conversion.
- Inferred lifecycle matching.
- Symbol/date/price/time proximity fallback matching.
- Unavailable raw source approximation.
- Source text, GPT notes, labels, outcomes, or future prices used for assignment logic.

## Required Object Fields

| Field | Required | Meaning |
| --- | --- | --- |
| `primitive_fact_id` | yes | Stable L2 id, preferably derived from evidence id, fact family, fact type, span reference, and extractor version. |
| `evidence_id` | yes | L1 evidence packet id. |
| `source_event_id` | yes | Original source event id or accession-derived event id. |
| `issuer_symbol` | yes | Issuer symbol supplied by L1/upstream. |
| `lifecycle_id` | when available | Existing upstream lifecycle id. Blank is allowed and remains uncertainty. |
| `source_form_family` | yes | Normalized L1 source family. |
| `source_circuit` | yes | Route/circuit that produced the evidence packet. |
| `source_url` | when available | Public filing, source URL, or source-native link. |
| `accession_or_document_id` | when available | SEC accession, document id, or source-native id. |
| `raw_text_path` | when available | Raw source path when retained outside small artifacts. |
| `source_hash` | when available | Hash of raw or normalized source text used for traceability. |
| `source_event_ts` | yes | Event timestamp from L1/upstream if available. |
| `filed_ts` | when available | Filing or publication timestamp. |
| `observed_ts` | when available | System observation timestamp. |
| `as_of_ts` | yes | Timestamp the primitive fact is allowed to know as of. |
| `as_of_state` | yes | `as_of_known`, `timestamp_incomplete`, or `source_gap`. |
| `extraction_span` | when available | Minimal evidence span used for extraction. |
| `extraction_span_start` | when available | Character or token start offset if available. |
| `extraction_span_end` | when available | Character or token end offset if available. |
| `evidence_reference_id` | yes | Span id, raw path id, accession pointer, or metadata pointer. |
| `extractor_name` | yes | Extractor or process that created the primitive. |
| `extractor_version` | yes | Version, task id, commit id, or stable local identifier. |
| `extraction_method` | yes | `regex`, `parser`, `structured_field`, `manual_review`, or `hybrid_review`. |
| `extraction_confidence` | yes | Numeric 0.0-1.0 confidence for the extraction, not for trading direction. |
| `confidence_reason` | yes | Short reason such as `explicit_amount_and_counterparty` or `raw_path_only_terms_incomplete`. |
| `source_trace_state` | yes | `raw_source_available`, `span_only`, `metadata_only`, or `source_gap`. |
| `raw_source_available_flag` | yes | `1` when raw source is available to inspect, else `0`. |
| `source_circuit_state` | yes | Circuit state such as `direct_operating_fact`, `financing_context_fact`, `insider_context_fact`, `ownership_context_fact`, `macro_context_fact`, or `generic_classifier_fact`. |
| `fact_family` | yes | Broad family from `primitive_fact_catalog.csv`. |
| `fact_type` | yes | Specific non-directional fact type. |
| `fact_value` | yes | Source-local value as extracted. Use `present` for presence facts. |
| `fact_unit` | when applicable | Unit such as `usd`, `shares`, `percent`, `months`, `text`, or `state`. |
| `fact_value_normalized` | when applicable | Normalized value only when source-supported. |
| `fact_period` | when available | Period or duration referred to by the source. |
| `counterparty_or_actor` | when available | Customer, insider, holder, lender, agency, policy actor, or supplier named by source. |
| `uncertainty_flags` | yes | Pipe-delimited uncertainty flags. Use `none` only when no known uncertainty remains. |
| `missing_required_context` | yes | Explicit missing context such as `holding_denominator_missing`, `prior_guidance_missing`, `raw_source_missing`, or `none`. |
| `join_blocker_state` | yes | `no_join_needed`, `denominator_join_needed`, `comparator_join_needed`, `timing_join_needed`, `economic_join_needed`, or `source_gap`. |
| `review_state` | yes | `fact_ready_for_meaning_review`, `context_only`, `not_ready`, or `source_gap_review`. |
| `directional_signal_created_flag` | yes | Must be `0`. |
| `rank_created_flag` | yes | Must be `0`. |
| `sizing_created_flag` | yes | Must be `0`. |
| `backtest_eligible_flag` | yes | Must be `0`. |
| `outcome_used_for_assignment_flag` | yes | Must be `0`. |
| `downstream_forbidden_effects` | yes | Pipe-delimited forbidden effects: `buy_sell`, `rank`, `sizing`, `allocation`, `backtest_eligibility`, `outcome_assignment`. |

## Fact Value Rules

Fact values must be source-local:

- Amounts can be normalized only when the amount and unit are visible.
- Durations can be normalized only when the period is visible.
- Presence facts use `present`; absence from the source is not a negative fact.
- Guidance facts may identify `raise`, `reaffirm`, `cut`, or `soft` language, but may not assign bullish/bearish direction.
- Form4 facts may identify transaction code, role, plan language, shares, and ownership-after fields, but may not infer motive.
- Ownership facts may identify active/passive/control language and ownership percent, but may not infer accumulation intent unless the text states control intent.
- Macro/policy facts may identify policy, budget, tariff, regulation, or geopolitical context, but may not claim single-name operating impact without downstream linkage.

## Uncertainty Rules

Use explicit uncertainty instead of blocking every row:

- `raw_source_missing`
- `span_only_no_raw`
- `timestamp_incomplete`
- `counterparty_not_named`
- `amount_not_stated`
- `duration_not_stated`
- `prior_guidance_missing`
- `holding_denominator_missing`
- `float_denominator_missing`
- `consensus_missing`
- `company_link_weak`
- `generic_8k_classifier_needed`
- `financing_terms_incomplete`
- `macro_transmission_unclear`

Missing context must not become a negative label. It may only create `uncertainty_flags`, `missing_required_context`, `join_blocker_state`, or `review_state`.

## Handoff Rules

Task760 may use `fact_family`, `fact_type`, `fact_value`, `extraction_confidence`, and uncertainty fields to create review-only economic meaning. Task760 must preserve ambiguity and cannot create trade instructions.

Task762 may use `review_state`, `source_trace_state`, `join_blocker_state`, `extraction_confidence`, and forbidden effect flags to define primitive gate states. A gate state can route review, cap confidence, or mark context-only; it cannot create backtest eligibility by itself.

## Research-Only Status

This contract does not change strategy acceptance, deployment readiness, or real-capital permission.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
