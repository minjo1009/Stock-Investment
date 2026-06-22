# T601-0 Candidate Funnel Contract

Last updated: 2026-06-03

## Decision

This contract fixes the minimum candidate funnel schema required before candidate selection work can proceed.

Current state:

```text
230 candidates
24 fills
```

The problem is not candidate generation. The problem is that candidate generation, ranking, eligibility, cooldown, skip, order, fill, and close states are not governed as one auditable funnel.

This is a design contract only. It does not implement candidate ranking or execution logic.

## Ownership

| Field | Value |
|---|---|
| Task | T601-0 |
| Owner | 성원 |
| Team | Candidate Funnel Research |
| Reviewer | 필수 / 중훈 |
| Priority | P0 |
| Program blocker | `P0_CANDIDATE_FUNNEL` |
| Strategy status | `NOT_ACCEPTED` |

## Required SQL Artifact

Schema file:

```text
docs/candidate_funnel/candidate_funnel_events.sql
```

Required table:

```sql
candidate_funnel_events
```

## Required Fields

```text
candidate_id
symbol
generated_time
rank_score
eligibility
cooldown_reason
skip_reason
order_id
fill_id
```

Additional exact-lineage fields required for audit:

```text
stage
source_snapshot_id
decision_id
created_at
```

## Funnel Stages

```text
GENERATED
RANKED
ELIGIBLE
ORDERED
FILLED
CLOSED
```

## Stage Definitions

| Stage | Meaning | Required Fields |
|---|---|---|
| `GENERATED` | Runtime logic produced a candidate | `candidate_id`, `symbol`, `generated_time`, `decision_id`, `source_snapshot_id` |
| `RANKED` | Candidate received a comparable rank score | `rank_score` |
| `ELIGIBLE` | Candidate passed portfolio/risk/cooldown checks | `eligibility` |
| `ORDERED` | Candidate became an order attempt | `order_id` |
| `FILLED` | Broker-truth fill exists | `fill_id` |
| `CLOSED` | Candidate's resulting position is closed | linked lifecycle row through exact order/fill IDs |

## Allowed Stage Order

```text
GENERATED -> RANKED -> ELIGIBLE -> ORDERED -> FILLED -> CLOSED
```

A candidate may stop at any stage with a `skip_reason`, but it must not skip forward without exact evidence.

Forbidden:

- `GENERATED -> ORDERED` without `RANKED` and `ELIGIBLE`.
- `ORDERED -> FILLED` without exact `order_id` and `fill_id`.
- `FILLED -> CLOSED` without exact lifecycle evidence.
- selecting candidates by symbol/date/price/time proximity.

## Eligibility Semantics

| Eligibility | Meaning |
|---|---|
| `ELIGIBLE` | Can proceed to order consideration |
| `INELIGIBLE_RISK` | Blocked by risk/exposure rules |
| `INELIGIBLE_COOLDOWN` | Blocked by symbol/session cooldown |
| `INELIGIBLE_DUPLICATE` | Blocked as duplicate candidate |
| `INELIGIBLE_SOURCE` | Blocked by missing or stale source |
| `INELIGIBLE_UNKNOWN` | Blocked because required evidence is missing |

Missing data must become `INELIGIBLE_UNKNOWN` or `INELIGIBLE_SOURCE`, not a silent pass.

## Required Metrics

| Metric | Definition |
|---|---|
| `candidate_to_order_ratio` | ordered candidates / generated candidates |
| `candidate_to_fill_ratio` | filled candidates / generated candidates |
| `top_symbol_concentration` | top symbol fills / total fills |
| `cooldown_rate` | cooldown-blocked candidates / generated candidates |

## Acceptance

T601-0 passes when the SQL schema and this contract are approved.

Implementation acceptance for T601-1 requires:

- candidate explanation available for 100% of candidates that reach `ORDERED`.
- top 3 symbols fill concentration below 50%.
- every skipped candidate has a `skip_reason`.
- every fill links to exact `order_id` and `fill_id`.

## Fail Conditions

- single symbol concentration above 80%.
- candidate ordered without rank evidence.
- candidate ordered while cooldown block is active.
- missing source inferred as eligible.
- `order_id` or `fill_id` inferred by proximity.

## Validation Placeholder

Design-stage validation:

```powershell
python validate_readiness_registry.py
python scripts/operating_closeout_validate.py
```

Implementation-stage validation must be added in T601-1.
