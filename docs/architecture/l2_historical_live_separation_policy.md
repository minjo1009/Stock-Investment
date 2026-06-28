# L2 Historical Live Separation Policy

## Problem

Historical research packets and live intraday evidence can look similar once they become CSV rows or database rows. L2 must make their source context explicit before L3 economic meaning consumes them.

## Required Flow

Historical artifact flow:

```text
Task740/Task741/Task742 artifact
-> artifact receipt/hash
-> l2_primitive_facts with runtime_context=HISTORICAL_RESEARCH
-> L3 historical research input
```

Live diagnostic flow:

```text
L0/L1 source receipt and freshness evidence
-> closed/source-time-certified primitive builder
-> l2_primitive_facts with runtime_context=LIVE_INTRADAY_DIAGNOSTIC
-> L3 diagnostic input
```

## Forbidden Flow

```text
Task CSV artifact -> LIVE_INTRADAY_DIAGNOSTIC L3 input
```

## Enforcement

- `scripts/ingest_task740_task741_artifacts_to_l2.py` ingests historical artifacts only as `HISTORICAL_RESEARCH`.
- `scripts/validate_l2_historical_live_separation.py` fails mixed historical/live batches.
- `scripts/validate_l3_inputs_are_l2_canonical.py` fails live L3 rows backed by direct historical artifacts.
- `scripts/validate_l2_no_trade_outputs.py` confirms L2 emits no trade, score, or order-intent outputs and preserves current readiness boundaries.
