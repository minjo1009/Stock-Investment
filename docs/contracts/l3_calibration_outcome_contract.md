# L3 Calibration Outcome Contract

## Purpose

This contract defines how L3 static confidence can be evaluated against later
outcomes without turning L3 into a trading signal. Calibration is evaluation
only. It does not grant strategy acceptance, deployment readiness, paper
trading, live trading, broker mutation, BUY/SELL signals, rank, sizing, or
order intent.

## Required Boundary

L3 calibration rows must be built only through explicit keys:

- `meaning_id`
- `l2_primitive_id`
- `source_receipt_id`
- another manifest-backed `outcome_bridge_key`

Symbol/date/price/time proximity matching is forbidden. If a row cannot be
linked through an explicit key, it remains missing or blocked. Missing labels
are never converted to negatives.

Before an outcome row is produced, a bridge row may be recorded through:

```text
src/brain/l3/calibration_bridge.py
```

Allowed bridge methods are direct meaning id, direct L2 primitive id, direct
source receipt id, or another manifest-backed exact key. Inferred bridge rows
are rejected.

## Canonical Table

The canonical table is:

```text
l3_calibration_outcomes
```

Implemented by:

```text
src/brain/l3/calibration_contracts.py
src/brain/l3/calibration_builder.py
src/brain/l3/calibration_store.py
```

## Required Fields

Identity and lineage:

- `calibration_row_id`
- `meaning_id`
- `evidence_edge_id`
- `l2_primitive_id`
- `source_receipt_id`
- `symbol`
- `entity_id`
- `asof_ts`
- `event_time`
- `source_ts`
- `available_to_brain_ts`
- `runtime_context`
- `source_time_certified`
- `freshness_status`

L3 interpretation:

- `event_type`
- `economic_dimension`
- `direction`
- `confidence_raw_band`
- `confidence_static_weight`

Outcome:

- `split_name`
- `outcome_source_table`
- `outcome_bridge_key`
- `lifecycle_id`
- `continuation_id`
- `outcome_start_ts`
- `outcome_end_ts`
- `outcome_horizon`
- `outcome_metric`
- `outcome_value`
- `outcome_label`
- `label_source`

Safety flags:

- `inferred_matching_used_flag`
- `label_used_in_assignment_flag`
- `outcome_used_in_assignment_flag`
- `missing_label_flag`
- `diagnostic_only`
- `trade_output_flag`
- `score_output_flag`
- `order_intent_flag`

## Hard Validation Rules

- `inferred_matching_used_flag` must be `0`.
- `label_used_in_assignment_flag` must be `0`.
- `outcome_used_in_assignment_flag` must be `0`.
- `diagnostic_only` must be `1`.
- `trade_output_flag`, `score_output_flag`, and `order_intent_flag` must be `0`.
- Non-missing rows require an explicit `outcome_bridge_key`.
- Non-missing rows require an outcome window and `outcome_value`.
- Missing rows must use `outcome_label = MISSING`.

## Audit Buckets

Calibration audit buckets group rows by:

```text
event_type
economic_dimension
direction
confidence_raw_band
split_name
```

They report:

- `sample_size`
- `positive_count`
- `negative_count`
- `neutral_count`
- `missing_count`
- `observed_positive_rate`
- `average_static_weight`
- `brier_score`
- `calibration_error`
- `calibration_status`
- `calibrated_probability`

`calibrated_probability` is available only when `calibration_status =
CALIBRATED`. Otherwise it remains `None`.

## Current Limitation

Existing canonical source-event artifacts expose an exact
`source_event_id -> lifecycle_id -> outcome` path. That path is allowed because
it uses explicit keys and produces diagnostic source-event calibration rows.

Task742-specific empirical calibration still requires a Task742 packet to
lifecycle/outcome bridge artifact. The system must not fill that gap with
symbol/date/price/time proximity or inferred matching.
