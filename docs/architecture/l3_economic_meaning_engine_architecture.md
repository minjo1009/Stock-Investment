# L3 Economic Meaning Engine Architecture

## Scope

L3 converts source-time certified L2 primitive facts into review-only economic
meaning, evidence edges, and relation graph summaries. It is an interpretation
layer, not a trading layer.

## Role

The target path is:

```text
L2PrimitiveFact
-> L3EconomicMeaningV2
-> L3EvidenceEdge
-> L3RelationGraph
```

The legacy compatibility path is:

```text
Task742 row
-> EconomicMeaning
-> MeaningRelationEdge
```

The legacy path remains conservative and all-or-nothing for compatibility with
the historical Task3351-3370 review reports. New diagnostic graph scoring lives
under `src/brain/l3`.

## L3 May Emit

- Economic direction: `SUPPORTIVE`, `RISK`, `MIXED`, `NEUTRAL`, `UNKNOWN`.
- Confidence components: raw band, static weight, calibration status, optional calibrated probability.
- Source reliability score.
- Event prior score.
- Freshness decay score.
- Evidence completeness score.
- Contradiction flags.
- Critical blocker flags and noncritical gap flags.
- Evidence-edge graph scores: support, risk, context, blocker, coverage, net direction.
- Review-only relation graph state.

## L3 Must Not Emit

- BUY or SELL.
- Ranking.
- Position sizing.
- Order intent.
- Paper trading eligibility.
- Live trading permission.
- Broker mutation.
- Strategy acceptance.
- Deployment readiness.

## Confidence Contract

Static confidence is not empirical probability.

Current static weights are diagnostic weights:

```text
high -> 0.85
medium -> 0.60
low -> 0.35
insufficient/unknown -> 0.00
```

The official L3 v2 contract separates:

```text
raw_band
static_weight
calibrated_probability
calibration_status
calibration_version
sample_size
brier_score
calibration_error
```

`calibrated_probability` remains `None` unless `calibration_status` is
`CALIBRATED`. Static weights must not be displayed as historical hit rates or
success probabilities.

## Calibration Contract

L3 calibration uses `l3_calibration_outcomes` and
`l3_calibration_audit_buckets`. Rows must be built through explicit bridge keys
only: `meaning_id`, `l2_primitive_id`, `source_receipt_id`, or another
manifest-backed `outcome_bridge_key`.

Symbol/date/price/time proximity matching is forbidden. Missing labels are not
negatives. Labels and outcomes are evaluation-only and must not enter assignment
logic.

The detailed contract is:

```text
docs/contracts/l3_calibration_outcome_contract.md
```

## Evidence Edge Contract

Each L3 meaning can produce one L3 evidence edge. Edges carry component scores:

```text
edge_weight =
  confidence_static_weight
  * source_reliability_score
  * event_prior_score
  * freshness_decay_score
  * evidence_completeness_score
  * (1.0 - contradiction_penalty)
```

This is diagnostic scoring only. It is not a signal, rank, sizing input, or
order intent.

## Critical Blockers And Noncritical Gaps

L3 v2 distinguishes critical blockers from noncritical gaps.

Critical examples:

- `MISSING_RAW_SOURCE`
- `MISSING_L2_PRIMITIVE`
- `MISSING_ASOF_TIMESTAMP`
- live-context `STALE_SOURCE`
- live-context missing freshness certification

Noncritical examples:

- `MISSING_CONFIRMATION`
- `MISSING_COMPARATOR`
- `MISSING_DENOMINATOR`
- `DISCOVERY_ONLY_SOURCE`
- historical-context stale source

A noncritical gap does not block the whole graph. A critical blocker sets
`graph_state = BLOCKED_CRITICAL`.

## Relation Graph States

L3 v2 graph states are review states only:

- `SUPPORT_DOMINANT_REVIEW`
- `RISK_DOMINANT_REVIEW`
- `MIXED_REVIEW`
- `CONTEXT_ONLY`
- `BLOCKED_CRITICAL`
- `INSUFFICIENT_EVIDENCE`

`SUPPORT_DOMINANT_REVIEW` is not a buy signal. `RISK_DOMINANT_REVIEW` is not a
sell signal.

## Legacy Compatibility

`src/brain/meaning_adapter.py` and `src/brain/relation_adapter.py` preserve a
legacy Task742 review-only adapter contract. Legacy relation behavior remains:
one `not_ready` meaning blocks the whole legacy relation edge. That behavior is
kept for historical report compatibility and is not the new L3 v2 graph model.

## Runtime Boundary

Runtime L3 should consume canonical L2 primitive facts through:

```text
src/brain/l2_to_meaning_adapter.py
src/brain/l3/adapters/l2_primitive_adapter.py
```

Task742 CSV or row input is historical research only and must not be treated as
live source-time certified primitive input.
