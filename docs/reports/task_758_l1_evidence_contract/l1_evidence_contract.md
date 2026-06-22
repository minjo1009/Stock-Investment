# L1 Evidence Contract

## Purpose

L1 preserves source evidence and context for the Trader Brain without promoting source text into trade decisions.

The contract is intentionally small. It captures enough source identity, timing, trace, directness, novelty, contamination, and uncertainty for L2/L3 review. It does not require perfect denominators or complete external comparators at L1.

## Layer Boundary

Allowed:

- Preserve source identity and trace.
- Preserve raw or excerpt evidence spans.
- Classify source family and route circuit.
- Mark directness, novelty, contamination, and uncertainty.
- State allowed and forbidden fact families.
- Require downstream interaction edges for context-only sources.

Forbidden:

- Buy, sell, hold, rank, sizing, allocation, or backtest eligibility.
- Outcome, future return, or price rescue fields.
- Missing field to negative label conversion.
- Source-family blanket block.
- Generic 8-K agreement text to operating claim without classification and transmission evidence.

## Required Fields

| Field | Required | Meaning |
| --- | --- | --- |
| `evidence_id` | yes | Stable L1 evidence packet id. |
| `source_event_id` | yes | Original source event id or accession-derived event id. |
| `issuer_symbol` | yes | Ticker or issuer symbol attached by upstream source event. |
| `lifecycle_id` | when available | Candidate lifecycle link; blank is allowed but must remain uncertainty. |
| `source_form_family` | yes | Normalized source family such as `form4_insider`, `financing_8k`, or `generic_8k`. |
| `route_circuit` | yes | Source-specific circuit used by the router. |
| `source_route_state` | yes | Route state from the source router. |
| `source_event_ts` | yes | Source event timestamp if available. |
| `filed_ts` | when available | Filing or publication timestamp. |
| `observed_ts` | when available | Timestamp when the system observed the source. |
| `as_of_state` | yes | `as_of_known`, `timestamp_incomplete`, or `source_gap`. |
| `source_url` | when available | Public source URL or filing URL. |
| `accession_or_document_id` | when available | SEC accession, document id, or source-native id. |
| `raw_text_path` | when available | Path to raw text if retained outside small Git artifacts. |
| `evidence_span` | when available | Small source excerpt or parsed span used for review. |
| `evidence_span_status` | yes | `span_present`, `raw_path_only`, `metadata_only`, or `missing_source_trace`. |
| `source_directness_state` | yes | `direct_operating`, `financing_context`, `insider_context`, `ownership_context`, `macro_context`, `generic_classifier_context`, `context_only`, or `source_gap`. |
| `novelty_state` | yes | `new_event`, `amendment_update`, `stale_snapshot`, `duplicate_possible`, or `unknown_novelty`. |
| `contamination_state` | yes | `clean_source_trace`, `boilerplate_possible`, `mixed_context`, `gpt_review_only`, or `source_trace_gap`. |
| `uncertainty_state` | yes | Explicit uncertainty such as `terms_incomplete`, `holding_denominator_missing`, `company_link_weak`, or `classifier_needed`. |
| `allowed_fact_families` | yes | Pipe-delimited fact families L2 may extract. |
| `forbidden_fact_families` | yes | Pipe-delimited fact families L2 must not infer from this source. |
| `context_retention_state` | yes | `retained_direct_evidence`, `retained_context_only`, or `retained_source_gap_review`. |
| `downstream_edge_required_flag` | yes | `1` when context needs L3/L4 interaction before use. |
| `source_is_discarded_flag` | yes | Must be `0` for retained evidence. |
| `backtest_eligible_flag` | yes | Must be `0` at L1. |
| `outcome_used_for_assignment_flag` | yes | Must be `0` at L1. |

## Good-Enough Interpretation Rules

### Insider Form 4

Good enough:

- Role is visible or inferable from filing text.
- Transaction type is visible: open-market buy, open-market sale, option/award, tax/admin, or plan/automatic.
- Timing and source trace are present.

Do not over-require:

- Full holdings denominator.
- Full compensation context.
- Complete multi-year insider history.

Policy:

- Non-plan insider selling may be negative context when role, sale type, and plan status are visible.
- Missing holdings denominator is uncertainty, not a negative label.
- Form 4 cannot create an operating catalyst by itself.

### Financing 8-K

Good enough:

- Financing type or instrument is visible.
- Use-of-proceeds, liquidity, maturity, dilution, covenant, or refinance language is visible when available.

Policy:

- Growth funding, survival funding, dilution overhang, and refinancing context can be retained.
- Missing exact pro-forma dilution is uncertainty, not a discard reason.
- Financing context must interact downstream with growth, liquidity, dilution, or runway facts.

### Generic 8-K

Good enough:

- Item number, agreement family, or classifier state is visible.
- Operating transmission evidence is separated from agreement boilerplate.

Policy:

- Agreement wording alone is context, not operating support.
- Governance, compensation, severance, financing, and M&A boilerplate remain retained context.
- Operating use requires later classification and transmission evidence.

### 13D/G And Ownership

Good enough:

- Active/passive filing state, ownership percent, amendment status, or control-intent language is visible.

Policy:

- 13D active/control language can route to special-situation review.
- 13G/passive ownership can route to sponsorship, float, or crowding context.
- Missing full holder history is uncertainty, not a negative label.

### 13F

Good enough:

- Manager, period, or reported position value is visible.

Policy:

- 13F is stale by design and should be retained as positioning context.
- It cannot create a fresh catalyst without additional same-as-of evidence.

### Macro, Policy, And Geopolitics

Good enough:

- Policy, budget, supply-chain, regulatory, or geopolitical theme is visible.
- Company link or theme link is stated separately.

Policy:

- Theme context is retained even when single-name link is weak.
- Weak company link is uncertainty, not a negative label.
- Single-name operating claims require downstream company-specific linkage.

## Downstream Interaction

L1 produces evidence packets only.

L2 may extract source-local primitive facts from allowed fields.
L3 may interpret economic meaning with explicit uncertainty.
L4 may build typed relation edges such as reinforcement, offset, prerequisite, blocker, confidence cap, or context-only attachment.
L5 and backtest gates remain unavailable from L1 output alone.

## Research-Only Status

This contract does not change strategy acceptance, deployment readiness, or real-capital permission.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
