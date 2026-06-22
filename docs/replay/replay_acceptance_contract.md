# T602-0 Replay Acceptance Contract

Last updated: 2026-06-03

## Decision

This contract fixes the minimum replay acceptance definition for paper trading.

Paper trading is not strategy validation until replay can reproduce runtime decisions, order attempts, broker-truth fills, and position lifecycle outcomes using exact IDs only.

This is a design contract only. It does not implement replay logic.

## Ownership

| Field | Value |
|---|---|
| Task | T602-0 |
| Owner | 동승 |
| Team | Replay & Simulation |
| Reviewer | 필수 / 중훈 |
| Priority | P0 |
| Program blocker | `P0_EXACT_REPLAY` |
| Strategy status | `NOT_ACCEPTED` |

## Match Surfaces

Replay acceptance has four required match surfaces:

```text
Decision Match
Order Match
Fill Match
Position Match
```

Each surface is evaluated independently. A pass in one surface cannot hide failure in another surface.

## Match Definitions

### Decision Match

Replay must reproduce runtime decision records using exact `decision_id`.

Required comparison:

| Runtime Field | Replay Field | Rule |
|---|---|---|
| `decision_id` | `decision_id` | exact match |
| `symbol` | `symbol` | exact match |
| `side` | `side` | exact match |
| `quantity` | `quantity` | exact numeric match after canonical normalization |
| `limit_price` | `limit_price` | exact or tolerance-defined match; tolerance must be recorded |
| `reason_code` | `reason_code` | exact match |
| `source_snapshot_id` | `source_snapshot_id` | exact match |

### Order Match

Replay must account for order attempts linked to decisions.

Required comparison:

| Runtime Field | Replay Field | Rule |
|---|---|---|
| `decision_id` | `decision_id` | exact match |
| `order_id` | `order_id` | exact broker/order ID when ordered |
| `order_status` | `order_status` | exact state or explicitly explained terminal mapping |
| `symbol` | `symbol` | exact match |
| `side` | `side` | exact match |
| `quantity` | `quantity` | exact numeric match |

### Fill Match

Replay must account for broker-truth fills only.

Required comparison:

| Runtime Field | Replay Field | Rule |
|---|---|---|
| `order_id` | `order_id` | exact match |
| `fill_id` | `fill_id` | exact match |
| `filled_qty` | `filled_qty` | exact numeric match |
| `filled_avg_price` | `filled_avg_price` | exact or tolerance-defined match; tolerance must be recorded |
| `fill_time` | `fill_time` | exact timestamp or documented broker timestamp normalization |

### Position Match

Replay must reproduce position lifecycle state from exact fills.

Required comparison:

| Runtime Field | Replay Field | Rule |
|---|---|---|
| `position_id` | `position_id` | exact lifecycle ID |
| `symbol` | `symbol` | exact match |
| `open_qty` | `open_qty` | exact numeric match |
| `realized_pnl` | `realized_pnl` | exact for closed positions |
| `state` | `state` | exact state: `NEW`, `OPEN`, `PARTIAL_EXIT`, `CLOSED` |

## Required Diff Table

Table or report artifact:

```text
replay_diff.csv
```

Required fields:

```text
decision_id
runtime_value
replay_value
diff_reason
```

Recommended additional fields:

```text
surface
field_name
order_id
fill_id
position_id
severity
```

## PASS / FAIL Criteria

| Status | Requirement |
|---|---|
| `PASS` | decision, order, fill, and position match rates are each `>= 99%` |
| `REVIEW` | any match rate is `>= 95%` and `< 99%`, and every mismatch has `diff_reason` |
| `FAIL` | any match rate is `< 95%` or any material mismatch lacks `diff_reason` |

Program-level `ACCEPTANCE_REVIEW` requires `PASS`, not `REVIEW`.

## Immediate FAIL Conditions

- decision mismatch unexplained.
- order/fill linked by symbol/date/price/time proximity.
- missing fill treated as non-event without audit.
- proxy PnL used as realized PnL.
- old pilot rows included without explicit inclusion/exclusion policy.
- replay uses labels, future outcomes, or post-close information to rebuild assignment.

## Old Pilot Row Policy

Rows outside the current controlled paper window must be excluded unless explicitly included in a separate audit segment.

If included, they must be labeled:

```text
historical_pilot_non_promotable
```

They cannot improve acceptance metrics.

## Acceptance

T602-0 passes when this contract is approved.

Implementation acceptance for T602-1 requires:

- `paper_replay_acceptance_report.md`
- `replay_diff.csv`
- `replay_validation.md`
- match rates for all four surfaces
- explicit accounting for fills, skips, exclusions, quarantined rows, and limit-versus-fill differences

## Validation Placeholder

Design-stage validation:

```powershell
python validate_readiness_registry.py
python scripts/operating_closeout_validate.py
```

Implementation-stage validation must be added in T602-1.
